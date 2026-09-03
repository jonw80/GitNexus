#!/usr/bin/env python3
"""Full 313k-fiber Draw-pullback contraction on component 10. NO bucket writes."""
import os, sys, json, time, math, gc, itertools

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ.setdefault('V174_INPUT', '/workspace/v174-payload/extract')
os.environ.setdefault('V174_OUT', '/tmp/v174-out')
os.environ.setdefault('V174_CACHE', '/tmp/v174-cache')
os.environ.setdefault('V174_COMPONENT', os.environ.get('V174_COMPONENT','10'))

import numpy as np

def rss_mb():
    try:
        return int(open('/proc/self/status').read().split('VmRSS:')[1].split()[0]) // 1024
    except Exception:
        return -1

print('RSS_START_MB', rss_mb(), flush=True)
print('EXEC_REDUCER', flush=True)
t_exec = time.time()
_red = os.environ.get('V174_REDUCER', '/workspace/v174-extract/run_external_norm_generic.py')
_src = open(_red).read().replace("if __name__=='__main__':main()", "")
G = {'__name__': 'ren', '__file__': _red}
exec(compile(_src, 'patched.py', 'exec'), G)
print('EXEC_DONE sec', time.time() - t_exec, 'RSS_MB', rss_mb(), flush=True)

group_W_fibers = G['group_W_fibers']
branch_tensor = G['branch_tensor']
canonicalize_key_tensor = G['canonicalize_key_tensor']
key_trans_info = G['key_trans_info']
branches = G['branches']
degree = G['degree']
valid_key = G['valid_key']
gvl = G['gvl']
slabels = G['slabels']
local_matrix = G['local_matrix']
direct_basis_sorted = G['direct_basis_sorted']
fixed_basis_sorted = G['fixed_basis_sorted']
cg_maps = G['cg_maps']
wilson_a = G['wilson_a']

PAPER_RDW = 324.957029045596114
PAPER_XLOG = -1228.86890836319450
BETA = 13.55
N_PROBE_TARGET = None  # all fibers
N_PROBE_MIN = 10**12
TIMEBOX_SEC = 10**12
RSS_LIMIT_MB = 8 * 1024  # 8 GiB

def logc_from_states(S48):
    pq = S48.reshape(-1, 24, 2).astype(np.int16)
    pmax = int(pq[:, :, 0].max()); qmax = int(pq[:, :, 1].max())
    table = np.zeros((pmax + 1, qmax + 1), dtype=np.float64)
    for p in range(pmax + 1):
        for q in range(qmax + 1):
            if p == 0 and q == 0:
                continue
            table[p, q] = math.log(float(wilson_a(BETA, int(p), int(q))))
    return table[pq[:, :, 0], pq[:, :, 1]].sum(axis=1)

print('LOAD_CROSSING', flush=True)
comp = int(os.environ['V174_COMPONENT'])
cross_path = os.environ.get('V174_CROSSING', f'/workspace/v174-run/out/crossing_component{comp}.npz')
print('COMPONENT', comp, 'CROSSING', cross_path, flush=True)
z = np.load(cross_path)
K = np.ascontiguousarray(z['states56'])
R = np.asarray(z['R'], np.float64)
W = np.asarray(z['W'], np.float64)
n = int(K.shape[0])
logc = logc_from_states(K[:, :48])
print('CROSSING n', n, 'G', float(W @ W), 'RSS_MB', rss_mb(), flush=True)

# Populate FIXED_LABELS from crossing keys (matches original crossing() for deg 10-13 tuples).
print('FIXED_LABELS_FROM_CROSSING', flush=True)
t_fl = time.time()
seen48 = set()
n_added = 0
for row in K:
    k48 = row[:48].tobytes()
    if k48 in seen48:
        continue
    seen48.add(k48)
    key = tuple((int(row[2 * i]), int(row[2 * i + 1])) for i in range(24))
    for labs in gvl(key):
        sl = slabels(labs)
        if sl not in G['FIXED_LABELS']:
            G['FIXED_LABELS'].add(sl)
            n_added += 1
print('FIXED_LABELS unique_k48', len(seen48), 'newly_added', n_added,
      'total', len(G['FIXED_LABELS']), 'sec', time.time() - t_fl, 'RSS_MB', rss_mb(), flush=True)

print('GROUP_W_FIBERS', flush=True)
t_grp = time.time()
fibers, wnorm = group_W_fibers(K, W)
t_grp = time.time() - t_grp
n_fibers = len(fibers)
print('GROUP_DONE n_fibers', n_fibers, 'wnorm', wnorm, 'sec', t_grp, 'RSS_MB', rss_mb(), flush=True)

# 56-byte lookup into crossing arrays
print('BUILD_LOOKUP', flush=True)
t_lu = time.time()
idx56 = {K[i].tobytes(): i for i in range(n)}
logc_by_k48 = {}
for i in range(n):
    k48 = K[i, :48].tobytes()
    if k48 not in logc_by_k48:
        logc_by_k48[k48] = float(logc[i])
cross48 = seen48  # all unique 48-byte crossing keys
print('LOOKUP n56', len(idx56), 'n48', len(cross48), 'sec', time.time() - t_lu, 'RSS_MB', rss_mb(), flush=True)

# Decide probe count from remaining time
elapsed_setup = t_grp  # grouping is the big known cost; import already done
# remaining for the loop
n_probe = n_fibers
print('FULL_PLAN n_probe', n_probe, 'n_fibers', n_fibers, flush=True)

acc = {
    'npz_W_Z': 0.0,       # sum W[k56]*Z  if k56 in crossing npz
    'npz_logCW_Z': 0.0,   # sum (logC*W)[k56]*Z
    'npz_R_Z': 0.0,
    'npz_logCR_Z': 0.0,
    'fiber_F_Z': 0.0,     # sum_ck <F_ck, Zc>  (W-fiber inner product)
    'fiber_logC_F_Z': 0.0,
    'hits_npz': 0,
    'hits_fiber': 0,
    'nz_emitted': 0,
    'branches': 0,
    'transitions': 0,
    'discard_low': 0,
    'skipped_not_crossing48': 0,
    'shape_mismatch': 0,
}

t_loop = time.time()
deadline = t_loop + max(30.0, TIMEBOX_SEC - t_grp - 30.0)
ii = 0
stopped_reason = 'completed_n_probe'
n_done = 0

for k48, F in fibers.items():
    ii += 1
    if ii > n_probe:
        break
    now = time.time()
    if ii > N_PROBE_MIN and now > deadline:
        stopped_reason = 'timebox_after_500'
        break
    if rss_mb() > RSS_LIMIT_MB:
        stopped_reason = 'rss_limit'
        break

    a = list(k48)
    key = tuple((a[2 * i], a[2 * i + 1]) for i in range(24))
    _, nks, _, _, _ = key_trans_info(k48)
    for pidx in range(24):
        for ar in (1, -1):
            for nk in branches(key, pidx, ar):
                dg = degree(nk)
                if not valid_key(nk):
                    continue
                if dg < 10:
                    acc['discard_low'] += 1
                    continue
                if dg > 17:
                    raise RuntimeError(('degree>17', dg))
                acc['branches'] += 1
                k48_nk = bytes(x for r in nk for x in r)
                ck_pre, nkt_pre, _, _, _ = key_trans_info(k48_nk)
                if ck_pre not in cross48:
                    acc['skipped_not_crossing48'] += 1
                    continue
                Z = branch_tensor(key, F, pidx, ar, nk)
                if not np.any(np.abs(Z) > 1e-15):
                    continue
                ck, Zc, nkt = canonicalize_key_tensor(nk, Z)
                Zc = np.asarray(Zc, dtype=np.float64) * math.sqrt(nks / nkt)
                acc['transitions'] += 1

                Ft = fibers.get(ck)
                if Ft is not None:
                    if Ft.shape == Zc.shape:
                        ip = float(np.vdot(Ft, Zc).real)
                        acc['fiber_F_Z'] += ip
                        acc['fiber_logC_F_Z'] += logc_by_k48.get(ck, 0.0) * ip
                        acc['hits_fiber'] += 1
                    else:
                        acc['shape_mismatch'] += 1

                nz = np.argwhere(np.abs(Zc) > 1e-15)
                acc['nz_emitted'] += int(len(nz))
                for ix in nz:
                    vb = bytes(int(x) for x in ix)
                    k56 = ck + vb
                    j = idx56.get(k56)
                    if j is None:
                        continue
                    v = float(Zc[tuple(ix)])
                    acc['npz_W_Z'] += W[j] * v
                    acc['npz_logCW_Z'] += logc[j] * W[j] * v
                    acc['npz_R_Z'] += R[j] * v
                    acc['npz_logCR_Z'] += logc[j] * R[j] * v
                    acc['hits_npz'] += 1

    n_done = ii
    if ii % 100 == 0 or ii == 1:
        print('FULL', ii, '/', n_probe, 'hits_npz', acc['hits_npz'], 'hits_fiber', acc['hits_fiber'],
              'npz_W_Z', acc['npz_W_Z'], 'fiber_F_Z', acc['fiber_F_Z'],
              'sec', time.time() - t_loop, 'RSS_MB', rss_mb(), flush=True)
        local_matrix.cache_clear(); direct_basis_sorted.cache_clear()
        fixed_basis_sorted.cache_clear(); cg_maps.cache_clear()
        branches.cache_clear(); valid_key.cache_clear(); gc.collect()
        if ii % 2000 == 0:
            with open(os.environ.get('V174_CONTRACT_CKPT', f'/workspace/v174-run/contraction_component{comp}.ckpt.json'),'w') as f:
                json.dump({'n_done': ii, 'acc': acc, 'loop_seconds': time.time()-t_loop, 'rss_mb': rss_mb()}, f, indent=2, default=str)

t_loop = time.time() - t_loop
if n_done == 0:
    n_done = max(0, ii if ii <= n_probe else n_probe)

scale = (n_done / n_fibers) if n_fibers else float('nan')

def scaled(x):
    return (x / scale) if scale else float('nan')

def rel_err(val, paper):
    return abs(val - paper) / abs(paper) if paper else float('nan')

result = {
    'n_states': n,
    'n_fibers': n_fibers,
    'wnorm': float(wnorm),
    'group_seconds': t_grp,
    'n_probe': n_done,
    'n_probe_target': N_PROBE_TARGET,
    'stopped_reason': stopped_reason,
    'loop_seconds': t_loop,
    'rss_mb_end': rss_mb(),
    'scale_factor': scale,
    'accumulators': acc,
    'npz_56byte_lookup': {
        'probe_RDW': acc['npz_W_Z'],
        'probe_XLOG': acc['npz_logCW_Z'],
        'scaled_RDW': scaled(acc['npz_W_Z']),
        'scaled_XLOG': scaled(acc['npz_logCW_Z']),
        'probe_RDW_rawR': acc['npz_R_Z'],
        'probe_XLOG_rawR': acc['npz_logCR_Z'],
        'scaled_RDW_rawR': scaled(acc['npz_R_Z']),
        'scaled_XLOG_rawR': scaled(acc['npz_logCR_Z']),
        'hits': acc['hits_npz'],
    },
    'fiber_inner_product': {
        'probe_RDW': acc['fiber_F_Z'],
        'probe_XLOG': acc['fiber_logC_F_Z'],
        'scaled_RDW': scaled(acc['fiber_F_Z']),
        'scaled_XLOG': scaled(acc['fiber_logC_F_Z']),
        'hits': acc['hits_fiber'],
        'note': 'sum_ck <F_W(ck), Zc> when emitted canonical key is a W-fiber; logC is per 48-byte key',
    },
    'paper': {'R_DW': PAPER_RDW, 'XLOG': PAPER_XLOG},
}
for tag, block in (('npz_56byte_lookup', result['npz_56byte_lookup']),
                   ('fiber_inner_product', result['fiber_inner_product'])):
    block['rel_err_RDW'] = rel_err(block['scaled_RDW'], PAPER_RDW)
    block['rel_err_XLOG'] = rel_err(block['scaled_XLOG'], PAPER_XLOG)
    block['few_percent_RDW'] = bool(block['rel_err_RDW'] < 0.05)
    block['few_percent_XLOG'] = bool(block['rel_err_XLOG'] < 0.05)

print('PROBE_RESULT', json.dumps(result, indent=2, default=str), flush=True)
a = 4.516666666666667
G = float(W @ W)
WlogW = float(np.dot(W*W, logc))
LOGNORM = float(np.dot(W*logc, W*logc))
RDW = float(acc['npz_W_Z'])
XLOG = float(acc['npz_logCW_Z'])
A10 = (a*RDW + WlogW)/G
cert = {
    'schema': 'GZYM_V174_A_CONTRACTION_FULL_V1',
    'component': comp,
    'n_states': n,
    'n_fibers': n_fibers,
    'n_done': n_done,
    'stopped_reason': stopped_reason,
    'group_seconds': t_grp,
    'loop_seconds': t_loop,
    'G': G,
    'a': a,
    'RDW': RDW,
    'XLOG': XLOG,
    'W_logC_W': WlogW,
    'LOGNORM': LOGNORM,
    'A': A10,
    'paper': {
        'RDW': PAPER_RDW,
        'XLOG': PAPER_XLOG,
        'W_logC_W': -770.2405251831079,
        'LOGNORM': 2929.1760467826693,
        'A10': 3.40729224466442823,
        'G_fresh': 204.7027392787848,
    },
    'rel_err_RDW': abs(RDW-PAPER_RDW)/abs(PAPER_RDW),
    'rel_err_XLOG': abs(XLOG-PAPER_XLOG)/abs(PAPER_XLOG),
    'rel_err_A': abs(A10-3.40729224466442823)/3.40729224466442823,
    'fiber_F_Z': acc['fiber_F_Z'],
    'accumulators': acc,
    'rss_mb_end': rss_mb(),
    'lookup': 'W',
}
outp = os.environ.get('V174_CONTRACT_OUT', f'/workspace/v174-run/contraction_component{comp}.json')
with open(outp, 'w') as f:
    json.dump(cert, f, indent=2, default=str)
    f.write('\n')
print('CERT', json.dumps({k:cert[k] for k in ('RDW','XLOG','A','rel_err_RDW','rel_err_XLOG','rel_err_A','n_done','n_fibers')}, indent=2), flush=True)
print('WROTE', outp, 'RSS_MB', rss_mb(), flush=True)
# checkpoint last accumulators
with open(os.environ.get('V174_CONTRACT_CKPT', f'/workspace/v174-run/contraction_component{comp}.ckpt.json'),'w') as f:
    json.dump({'n_done': n_done, 'acc': acc, 'loop_seconds': t_loop}, f, indent=2, default=str)

