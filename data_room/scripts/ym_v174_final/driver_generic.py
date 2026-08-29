#!/usr/bin/env python3
"""Sharded, resumable driver for V174 external reduction (generic component).

Non-destructive copy of driver.py. Honors V174_COMPONENT. Does not invent A{N}
or expected_G. If overlapping lo=0 checkpoints exist, merge uses only the single
full-coverage shard (cross_0_{NLOW}.npz), matching the certified component-10
pipeline which would otherwise double-count nested prefixes.
"""
import os, sys, math, itertools, time, json, pathlib, gc
import numpy as np

os.environ.setdefault('V174_INPUT', '/tmp/v174b/payload')
os.environ.setdefault('V174_OUT', '/tmp/v174b/out')
os.environ.setdefault('V174_CACHE', '/tmp/v174b/cache')
SHARD = pathlib.Path(os.environ.get('V174_SHARDS', '/tmp/v174b/shards'))
SHARD.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, os.environ['V174_INPUT'])

_src = open(os.environ.get('V174_REDUCER', '/tmp/v174b/patched3.py')).read().replace("if __name__=='__main__':main()", "")
G = {'__name__': 'ren', '__file__': '/tmp/v174b/patched3.py'}
exec(compile(_src, 'patched.py', 'exec'), G)

OUT = G['OUT']
NLOW = G['NLOW']; psi = G['psi']; A = G['A']
COMP = int(G.get('COMP', os.environ.get('V174_COMPONENT', '10')))


def _phase():
    p = OUT / 'phase.npy'
    stats_path = OUT / 'phase_stats.json'
    if p.exists():
        if stats_path.exists():
            st = json.loads(stats_path.read_text())
            print(f"PHASE ncc={st.get('ncc')} contr={st.get('contr')} eigres={st.get('eigres')} phase_sym={st.get('phase_sym')} (cached)", flush=True)
        return np.load(p)
    import scipy.sparse as sp
    C, outside = G['low_raw_C']()
    s, ncc, contr, eigres, logc = G['recover_phase'](C)
    np.save(p, s); np.save(OUT / 'logc.npy', logc)
    print(f'PHASE ncc={ncc} contr={contr} eigres={eigres} nnz={C.nnz}', flush=True)
    _M = (G['A'] * (C @ sp.diags(s.astype(float))) + sp.diags(logc)).tocsr()
    _D = (_M - _M.T).tocoo()
    phase_sym = float(np.abs(_D.data).max()) if _D.nnz else 0.0
    del _M, _D
    print(f'PHASE_SYMMETRY {phase_sym}', flush=True)
    st = {'ncc': int(ncc), 'contr': int(contr), 'eigres': float(eigres),
          'phase_sym': phase_sym, 'nnz': int(C.nnz), 'outside': int(outside)}
    stats_path.write_text(json.dumps(st, indent=2))
    if ncc != 1 or contr != 0 or phase_sym > 1e-8:
        raise RuntimeError(('phase check failed', ncc, contr, phase_sym))
    del C; gc.collect()
    return s


def _save(accR, accW, lo, i, br, oc, recip):
    keys = sorted(set(accR) | set(accW))
    K = np.frombuffer(b''.join(keys), dtype=np.uint8).reshape(-1,56).copy() if keys else np.zeros((0,56),np.uint8)
    tmp = SHARD / f'.tmp_{lo}_{i}.npz'
    np.savez_compressed(tmp, K=K,
                        R=np.array([accR.get(k,0.0) for k in keys]),
                        W=np.array([accW.get(k,0.0) for k in keys]),
                        meta=np.array([br, oc, recip, i], dtype=float))
    os.replace(tmp, SHARD / f'cross_{lo}_{i}.npz')
    print(f'CKPT lo={lo} through={i} targets={len(keys)}', flush=True)


def next_lo():
    best = 0
    for f in SHARD.glob('cross_*.npz'):
        a = int(f.stem.split('_')[1]); b = int(f.stem.split('_')[2])
        if a <= best: best = max(best, b)
    return best


def stage_cross(lo, hi, budget=170.0):
    s = _phase(); phi = s.astype(float) * psi
    low_states = G['low_states']; branches = G['branches']; degree = G['degree']
    valid_key = G['valid_key']; gvl = G['gvl']; slabels = G['slabels']
    FIXED = G['FIXED_LABELS']; tchoices = G['transition_choices']
    enc = G['encode_state']; canon = G['canon_state_bytes']; osb = G['orbit_size_bytes']
    accR = {}; accW = {}; branches_n = outcomes = 0; recip = 0.0
    t0 = time.time(); i = lo
    while i < hi:
        key, vb = low_states[i]
        ns = osb(enc(key, vb))
        for pidx in range(24):
            for ar in (1, -1):
                for nk in branches(key, pidx, ar):
                    dg = degree(nk)
                    if dg < 10 or dg > 13 or not valid_key(nk): continue
                    branches_n += 1
                    for labs in gvl(nk): FIXED.add(slabels(labs))
                    tc = tchoices(key, nk, pidx, ar, vb, True, True, True)
                    if tc is None: continue
                    aff, pf, pr, choices = tc; base = list(vb)
                    for comb in itertools.product(*choices):
                        vf = pf; vr = pr; tvb = base.copy()
                        for v, (bb, xf, xr) in zip(aff, comb):
                            tvb[v] = bb; vf *= xf; vr *= xr
                        if abs(vf) <= 1e-13 and abs(vr) <= 1e-13: continue
                        rb = canon(enc(nk, tuple(tvb))); nt = osb(rb)
                        fac = math.sqrt(ns / nt)
                        if abs(vf) > 1e-13: accR[rb] = accR.get(rb, 0.0) + A * fac * vf * phi[i]
                        if abs(vr) > 1e-13: accW[rb] = accW.get(rb, 0.0) + A * fac * vr * psi[i]
                        if abs(vf) > 1e-13 and abs(vr) > 1e-13:
                            recip = max(recip, abs(abs(vf / vr) - 1.0))
                        outcomes += 1
        i += 1
        if (i - lo) % 250 == 0:
            print(f'  CROSS {i}/{hi} targets {len(accR)} sec {time.time()-t0:.0f}', flush=True)
            G['local_matrix'].cache_clear(); G['fixed_basis_sorted'].cache_clear()
            G['cg_maps'].cache_clear(); gc.collect()
        if (i - lo) % 200 == 0 and i > lo:
            _save(accR, accW, lo, i, branches_n, outcomes, recip)
            for _n, _f in list(G.items()):
                cc = getattr(_f, 'cache_clear', None)
                if cc is not None:
                    try: cc()
                    except Exception: pass
            gc.collect()
            try:
                _rss = int(open('/proc/self/status').read().split('VmRSS:')[1].split()[0]) // 1024
                print(f'  RSS {_rss} MB after clear', flush=True)
            except Exception: pass
        if time.time() - t0 > budget:
            break
    _save(accR, accW, lo, i, branches_n, outcomes, recip)
    keys = sorted(set(accR) | set(accW))
    print(f'SHARD_DONE lo={lo} reached={i} of {hi}  targets={len(keys)} '
          f'sec={time.time()-t0:.0f}', flush=True)
    return i


def _select_shards():
    """Prefer a single full-coverage shard; never sum nested lo=0 prefixes."""
    files = list(SHARD.glob('cross_*.npz'))
    parsed = []
    for f in files:
        parts = f.stem.split('_')
        lo = int(parts[1]); hi = int(parts[2])
        parsed.append((lo, hi, f))
    if not parsed:
        raise RuntimeError('no cross_*.npz shards')
    full = [p for p in parsed if p[0] == 0 and p[1] == NLOW]
    if full:
        chosen = max(full, key=lambda p: p[1])
        skipped = [p[2].name for p in parsed if p[2] != chosen[2]]
        if skipped:
            print('MERGE_SKIP_OVERLAPPING', skipped, 'using', chosen[2].name, flush=True)
        return [chosen]
    # Nested prefixes from a common lo: take the longest hi only.
    by_lo = {}
    for p in parsed:
        by_lo.setdefault(p[0], []).append(p)
    selected = []
    skipped = []
    for lo, group in sorted(by_lo.items()):
        group.sort(key=lambda p: p[1])
        # if they are nested prefixes, keep only max hi
        his = [g[1] for g in group]
        nested = all(his[i] <= his[i+1] for i in range(len(his)-1))
        if nested and len(group) > 1:
            selected.append(group[-1])
            skipped.extend(g[2].name for g in group[:-1])
        else:
            selected.extend(group)
    if skipped:
        print('MERGE_SKIP_PREFIXES', skipped, flush=True)
    # Overlap check across different lo: refuse double-count
    selected.sort()
    for i in range(1, len(selected)):
        if selected[i][0] < selected[i-1][1]:
            raise RuntimeError(('refusing to merge overlapping shards',
                                selected[i-1][2].name, selected[i][2].name))
    return selected


def stage_merge():
    accR = {}; accW = {}; br = oc = 0; recip = 0.0
    chosen = _select_shards()
    cov = []
    for lo, hi, f in chosen:
        z = np.load(f)
        hi_meta = int(z['meta'][3])
        cov.append((lo, hi_meta))
        for row, r, w in zip(z['K'], z['R'], z['W']):
            k = bytes(row.tolist())
            if r: accR[k] = accR.get(k, 0.0) + float(r)
            if w: accW[k] = accW.get(k, 0.0) + float(w)
        br += int(z['meta'][0]); oc += int(z['meta'][1]); recip = max(recip, float(z['meta'][2]))
    cov.sort(); merged = []
    for a, b in cov:
        if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else: merged.append((a, b))
    complete = merged == [(0, NLOW)]
    keys = sorted(set(accR) | set(accW))
    K = np.frombuffer(b''.join(keys), dtype=np.uint8).reshape(-1, 56).copy()
    R = np.array([accR.get(k, 0.0) for k in keys]); W = np.array([accW.get(k, 0.0) for k in keys])
    R2 = float(R @ R); W2 = float(W @ W)
    np.savez_compressed(OUT / f'crossing_component{COMP}.npz', states56=K, R=R, W=W)
    EG = G.get('EXPECTED_G')
    rep = {'coverage': merged, 'complete': complete, 'targets': len(keys),
           'R2': R2, 'W2': W2, 'gram_abs_diff': abs(R2 - W2),
           'expected_G': EG,
           'expected_abs_diff': (abs(R2 - EG) if EG is not None else None),
           'expected_G_skipped': EG is None,
           'branches': br, 'outcomes': oc, 'reciprocity': recip,
           'shards_used': [f.name for _,_,f in chosen],
           'component': COMP}
    (OUT / 'merge_report.json').write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2), flush=True)
    return rep


def stage_emit():
    z = np.load(OUT / f'crossing_component{COMP}.npz')
    K, W = z['states56'], z['W']
    fibers, wnorm = G['group_W_fibers'](K, W)
    print('fiber norm', wnorm, flush=True)
    emit = G['emit_external'](fibers, 128)
    emit = dict(emit)
    emit['fiber_norm'] = float(wnorm)
    emit['component'] = COMP
    (OUT / 'emit_report.json').write_text(json.dumps(emit, indent=2))
    print(json.dumps(emit, indent=2), flush=True)


def stage_reduce():
    ND, red = G['reduce_external'](128)
    z = np.load(OUT / f'crossing_component{COMP}.npz')
    R = z['R']; W = z['W']
    Gm = float(R @ R); W2 = float(W @ W)
    XLOG = -1228.86890836319450; LOGNORM = 2929.1760467826693
    A_N = G.get('EXPECTED_A')
    EG = G.get('EXPECTED_G')
    note_missing = []
    if A_N is None:
        M2 = None; B2 = None; floor = None; floor_sat = None; psd = None
        note_missing.append(
            f'A{COMP} absent from constants.json; skipped M2/B*B/floor. '
            'XLOG/LOGNORM remain hardcoded as in the original reducer but were not applied. '
            'No A value was invented. Certified A exists only for component 10.'
        )
    else:
        M2 = float((A * A * float(ND) + 2 * A * XLOG + LOGNORM) / Gm)
        B2 = M2 - A_N * A_N
        floor = 517.05823521403812592
        floor_sat = bool(float(ND) >= floor)
        psd = bool(B2 >= -1e-10)
    if EG is None:
        note_missing.append(
            'expected_G_consistent absent; skipped expected-G check. '
            'The older four-channel crossing G diagonal is stale under V174 and was not reused.'
        )
    nd_ld = red.get('N_D_longdouble', str(ND))
    phase_st = {}
    pp = OUT / 'phase_stats.json'
    if pp.exists():
        phase_st = json.loads(pp.read_text())
    emit_st = {}
    ep = OUT / 'emit_report.json'
    if ep.exists():
        emit_st = json.loads(ep.read_text())
    merge_st = {}
    mp = OUT / 'merge_report.json'
    if mp.exists():
        merge_st = json.loads(mp.read_text())
    out = {
        'schema': 'GZYM_V174_EXTERNAL_GENERIC_V1',
        'component': COMP,
        'a': float(A),
        'lambda_crit': float(G['LAM']),
        'N_D': float(ND),
        'N_D_longdouble': nd_ld,
        'G': Gm,
        'G_reverse': W2,
        'gram_abs_diff': abs(Gm - W2),
        'expected_G': EG,
        'A': A_N,
        'M2': M2,
        'B_star_B': B2,
        'preregistered_floor': floor,
        'floor_satisfied': floor_sat,
        'psd': psd,
        'constants_notes': note_missing,
        'checks': {
            'low_phase_components': phase_st.get('ncc'),
            'low_phase_contradictions': phase_st.get('contr'),
            'low_eigen_residual_l2': phase_st.get('eigres'),
            'phase_sym': phase_st.get('phase_sym'),
            'low_raw_nnz': phase_st.get('nnz'),
            'crossing_self_adjoint_pass': bool(abs(Gm - W2) <= 1e-8),
            'crossing_expected_skipped': EG is None,
            'A_M2_B2_floor_skipped': A_N is None,
            'B_psd': psd,
        },
        'inputs': {
            'q_norm2': float(psi @ psi),
            'v3_component_count': int(NLOW),
        },
        'merge': {k: merge_st[k] for k in merge_st if k != 'coverage' or True},
        'emit': {k: emit_st[k] for k in emit_st if k != 'records_per_bucket'},
        'reduce': red,
        'XLOG_hardcoded': XLOG,
        'LOGNORM_hardcoded': LOGNORM,
        'XLOG_LOGNORM_applied': A_N is not None,
    }
    # drop huge records_per_bucket from emit copy already handled
    (OUT / f'a{COMP}_B{COMP}_component{COMP}.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2), flush=True)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'cross':
        lo = int(sys.argv[2]); hi = int(sys.argv[3])
        b = float(sys.argv[4]) if len(sys.argv) > 4 else 170.0
        stage_cross(lo, hi, b)
    elif cmd == 'merge': stage_merge()
    elif cmd == 'emit': stage_emit()
    elif cmd == 'reduce': stage_reduce()
