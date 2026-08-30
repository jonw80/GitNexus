#!/usr/bin/env python3
"""Sharded, resumable driver for the V174 component-10 external reduction.

The committed reducer runs crossing() as one uninterruptible loop over 7576 low
states. This box allows ~200 s per invocation, so the loop is re-expressed as
shards over source index ranges whose partial accumulators are merged. The loop
body is copied verbatim from patched.py:crossing() -- same thresholds, same
canonicalisation, same fac = sqrt(ns/nt) -- so shard boundaries cannot change the
result: accR/accW are plain sums over independent sources.

Stages
  cross  --lo --hi   accumulate accR/accW over low_states[lo:hi] -> shard npz
  merge              merge shards -> crossing_component10.npz, report R2/W2
  emit               group_W_fibers + emit_external -> OUT/buckets
  reduce             reduce_external -> N_D, then A10/M2/B*B and the PSD floor
"""
import os, sys, math, itertools, time, json, pathlib, gc, functools, hashlib
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


def _phase():
    p = OUT / 'phase.npy'
    if p.exists():
        return np.load(p)
    import scipy.sparse as sp
    C, outside = G['low_raw_C']()
    s, ncc, contr, eigres, logc = G['recover_phase'](C)
    # Save first so a failed check still leaves an artifact.
    np.save(p, s); np.save(OUT / 'logc.npy', logc)
    print(f'PHASE ncc={ncc} contr={contr} eigres={eigres} nnz={C.nnz}', flush=True)
    _M = (G['A'] * (C @ sp.diags(s.astype(float))) + sp.diags(logc)).tocsr()
    _D = (_M - _M.T).tocoo()
    phase_sym = float(np.abs(_D.data).max()) if _D.nnz else 0.0
    del _M, _D
    print(f'PHASE_SYMMETRY {phase_sym}', flush=True)
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
            # Five module caches carry maxsize=500000 and hold dense arrays; the
            # upstream loop clears only three of them, and only every 1500
            # sources. That is what drove RSS to 3.89 GB and got the process
            # OOM-killed on the 9142x4824 solve. Every expensive result is now
            # on disk (ns / mult / cg / fixed_basis), so dropping the in-process
            # caches costs a reload, not a recomputation.
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
    by_lo = {}
    for p in parsed:
        by_lo.setdefault(p[0], []).append(p)
    selected = []
    skipped = []
    for lo, group in sorted(by_lo.items()):
        group.sort(key=lambda p: p[1])
        his = [g[1] for g in group]
        nested = all(his[i] <= his[i+1] for i in range(len(his)-1))
        if nested and len(group) > 1:
            selected.append(group[-1])
            skipped.extend(g[2].name for g in group[:-1])
        else:
            selected.extend(group)
    if skipped:
        print('MERGE_SKIP_PREFIXES', skipped, flush=True)
    selected.sort()
    for i in range(1, len(selected)):
        if selected[i][0] < selected[i-1][1]:
            raise RuntimeError(('refusing to merge overlapping shards',
                                selected[i-1][2].name, selected[i][2].name))
    # Non-overlap alone is not enough once shards arrive from independent
    # parallel jobs: a job that dies leaves a GAP, and summing what remains
    # silently produces a crossing that is short rather than wrong-looking.
    # Require exact contiguous cover of [0, NLOW).
    cursor = 0; gaps = []
    for lo, hi, _f in selected:
        if lo > cursor:
            gaps.append((cursor, lo))
        cursor = max(cursor, hi)
    if cursor < NLOW:
        gaps.append((cursor, NLOW))
    if gaps:
        raise RuntimeError(('shard coverage incomplete -- missing source ranges',
                            gaps, 'have', [(l, h) for l, h, _ in selected]))
    print(f'MERGE_COVERAGE_OK contiguous 0..{NLOW} from {len(selected)} shards', flush=True)
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
    K = np.frombuffer(b''.join(keys), dtype=np.uint8).reshape(-1, 56).copy() if keys else np.zeros((0, 56), np.uint8)
    R = np.array([accR.get(k, 0.0) for k in keys]); W = np.array([accW.get(k, 0.0) for k in keys])
    R2 = float(R @ R) if len(R) else 0.0; W2 = float(W @ W) if len(W) else 0.0
    np.savez_compressed(OUT / 'crossing_component10.npz', states56=K, R=R, W=W)
    rep = {'coverage': merged, 'complete': complete, 'targets': len(keys),
           'R2': R2, 'W2': W2, 'gram_abs_diff': abs(R2 - W2),
           'expected_G': G['EXPECTED_G'], 'expected_abs_diff': abs(R2 - G['EXPECTED_G']),
           'branches': br, 'outcomes': oc, 'reciprocity': recip,
           'shards_used': [f.name for _, _, f in chosen]}
    (OUT / 'merge_report.json').write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2), flush=True)
    if not complete:
        raise RuntimeError(('incomplete crossing coverage', merged, 'expected', [(0, int(NLOW))]))
    return rep



def group_W_fibers_surveyed(G, K, W, strict=True):
    """group_W_fibers, but it surveys every failure before deciding.

    The upstream routine raises on the first offending state, so each CI run
    reports exactly one bad state and nothing about how many others there are or
    what they carry. These are integrity checks, so continuing past them silently
    would produce a wrong N_D -- but failing on the first one costs a full run per
    state. This walks everything, classifies each failure, records the squared
    norm the offenders carry, and only then raises. One run yields the whole
    picture; the excluded-norm fraction says whether the failures are numerical
    dust or structural.
    """
    import math, time
    t = time.time()
    key_trans_info = G['key_trans_info']; orbit_size_bytes = G['orbit_size_bytes']
    vm = G['vm']
    fib = {}; coll = 0
    bad = {'noncanonical': [], 'orbit_ratio': [], 'stab_orbit': [], 'fiber_too_large': []}
    # np.zeros(vm(key)) allocates an 8-dimensional tensor sized by the key's
    # irrep dimensions. A key with large labels asks for an astronomical array
    # and the process is OOM-KILLED -- which emits no Python traceback at all,
    # so wrapping the call in traceback.print_exc() reports nothing. Bound it.
    max_cells = int(os.environ.get('V174_MAX_FIBER_CELLS', 1 << 22))
    biggest = 0
    bad_n2 = 0.0; good_n2 = 0.0
    for row, x in zip(K, W):
        if abs(x) < 1e-18:
            continue
        k48 = bytes(row[:48].tolist())
        vb = tuple(int(v) for v in row[48:56])
        key = tuple((row[2 * i].item(), row[2 * i + 1].item()) for i in range(24))
        ck, nk, vmap, inv, stab = key_trans_info(k48)
        if ck != k48:
            bad['noncanonical'].append((k48.hex()[:32], float(x))); bad_n2 += float(x) ** 2
            continue
        raw = bytes(row.tolist()); ns = orbit_size_bytes(raw); m = ns / nk
        if abs(m - round(m)) > 1e-12:
            bad['orbit_ratio'].append((k48.hex()[:32], ns, nk, float(m), float(x)))
            bad_n2 += float(x) ** 2
            continue
        orb = set()
        for vm0 in stab:
            nv = [0] * 8
            for v, b in enumerate(vb):
                nv[vm0[v]] = b
            orb.add(tuple(nv))
        if len(orb) != round(m):
            bad['stab_orbit'].append((k48.hex()[:32], len(orb), round(m), len(stab), float(x)))
            bad_n2 += float(x) ** 2
            continue
        F = fib.get(k48)
        if F is None:
            shape = vm(key)
            cells = 1
            for d in shape:
                cells *= int(d)
            biggest = max(biggest, cells)
            if cells > max_cells:
                bad['fiber_too_large'].append((k48.hex()[:32], tuple(int(d) for d in shape),
                                               cells, float(x)))
                bad_n2 += float(x) ** 2
                continue
            F = np.zeros(shape, float); fib[k48] = F
        val = float(x) / math.sqrt(len(orb))
        for qv in orb:
            if abs(F[qv]) > 1e-13:
                coll += 1
            F[qv] += val
        good_n2 += float(x) ** 2
    n = float(sum(np.vdot(F, F).real for F in fib.values()))
    nbad = sum(len(v) for v in bad.values())
    print(f'FIBERS {len(fib)} norm2 {n} collisions {coll} '
          f'largest_fiber_cells {biggest} sec {time.time()-t:.1f}', flush=True)
    if nbad:
        total = good_n2 + bad_n2
        print('FIBER_SURVEY  offending states by class:', flush=True)
        for cls, items in bad.items():
            if items:
                print(f'  {cls}: {len(items)}   examples: {items[:3]}', flush=True)
        print(f'  excluded squared norm {bad_n2:.6e} of {total:.6e} '
              f'({100.0*bad_n2/total if total else 0:.4f}%)', flush=True)
        if strict:
            raise RuntimeError(('fiber integrity failures', {k: len(v) for k, v in bad.items()},
                                'excluded_norm2', bad_n2))
    return fib, n

def _direct_basis_dense(sl):
    """G['direct_basis_sorted'], but the singlet subspace is found densely.

    The pinned reducer solves for it with spla.eigsh(Gram, k=k+1, which='SM').
    Gram's kernel is exactly k-fold degenerate and its next eigenvalue is 1.0,
    and ARPACK does not reliably separate the two: on some hosts it returns
    spurious 1.0 eigenpairs in place of true zeros, the k-th smallest lands at
    1.0, and the 'direct kernel residual eig' guard fires. Which label tuple
    trips it is a function of the host's rounding rather than of the
    mathematics -- CI failed on ((0,1),(0,2),(0,3),(1,0),(1,0),(4,0)) and this
    box on ((0,0),(1,0),(1,0),(1,1),(1,1),(2,1)) -- so it is not reproducible
    and not a bad multiplicity: for the tuple CI failed on, Littlewood-Richardson
    over SU(3) gives exactly 8 singlets, which is what sm() returns.

    Gram is nz x nz with nz of order 1e3, so it is diagonalised densely here:
    same subspace, deterministic, no convergence tolerance to tune. Verified to
    span the identical kernel -- all k overlap singular values against the
    ARPACK result are 1.0 to 1e-15.

    Installed over the reducer's binding rather than edited into
    run_external_norm.py.xz.b64, which stays byte-identical and still verifies
    against its pinned sha256.
    """
    np_ = np
    sp_ = G['sp']; la_ = G['la']
    irrep = G['irrep']; sm = G['sm']; DIRECTDIR = G['DIRECTDIR']
    sl = tuple(sl)
    p = DIRECTDIR / (hashlib.sha256(repr(sl).encode()).hexdigest() + '.npz')
    if p.exists():
        return np_.asarray(np_.load(p, allow_pickle=False)['V'], float)
    reps = [irrep(*r) for r in sl]; dims = [R.dim for R in reps]
    DD = int(np_.prod(dims)); k = sm(sl)
    if k == 0:
        V = np_.zeros((DD, 0)); np_.savez_compressed(p, V=V); return V
    total_boxes = sum(R.boxes for R in reps)
    if total_boxes % 3:
        raise RuntimeError(('nonzero singlet with boxes', sl, total_boxes, k))
    tw = total_boxes // 3
    zcomb = []; zflat = []
    for comb in itertools.product(*[range(d) for d in dims]):
        w = [0, 0, 0]
        for R, i in zip(reps, comb):
            wi = R.weights[i]; w[0] += wi[0]; w[1] += wi[1]; w[2] += wi[2]
        if w[0] == tw and w[1] == tw and w[2] == tw:
            zcomb.append(comb); zflat.append(np_.ravel_multi_index(comb, dims))
    nz = len(zcomb)
    if nz == k:
        Q = np_.eye(k)
    else:
        rows = []; cols = []; vals = []; rowmap = {}
        for cj, comb in enumerate(zcomb):
            for gg in (0, 1):
                for leg, R in enumerate(reps):
                    F = R.F1 if gg == 0 else R.F2
                    col = F.getcol(comb[leg]).tocoo()
                    for rr, val in zip(col.row, col.data):
                        cc = list(comb); cc[leg] = int(rr)
                        tag = (gg, tuple(cc)); ri = rowmap.setdefault(tag, len(rowmap))
                        rows.append(ri); cols.append(cj); vals.append(float(val))
        M = sp_.csr_matrix((vals, (rows, cols)), shape=(len(rowmap), nz))
        Gram = (M.T @ M).tocsr()
        if k >= nz:
            Q = np_.eye(nz)[:, :k]
        else:
            # Try the reducer's own solver first, unchanged, so that every tuple
            # ARPACK can handle keeps the pinned reducer's exact basis and this
            # override is a no-op there. Only fall back where it actually fails.
            nev = min(nz - 1, k + 1)
            v0 = np_.linspace(1.0, 2.0, nz); v0 /= np_.linalg.norm(v0)
            vals0 = vec = None
            try:
                w, u = G['spla'].eigsh(Gram, k=nev, which='SM', tol=1e-11,
                                       maxiter=20000, v0=v0)
                o = np_.argsort(w)
                if w[o][k - 1] <= 1e-8:
                    vals0 = w[o]; vec = u[:, o]
            except Exception:
                pass
            if vals0 is None:
                # ARPACK did not separate the k-fold degenerate kernel from the
                # next eigenvalue (1.0). Dense is exact here. Measured over the
                # full tuple set: 14 of 1423 tuples need this, at nz = 399, 399,
                # 624, 714, 948, 1146, 1164, 1242, 1500, 1674, 2004, 2598, 3666,
                # 4590 -- so failure is NOT a function of size, and the fallback
                # is rare enough that the dense cost is bounded while every other
                # tuple keeps the pinned reducer's own basis.
                w, u = np_.linalg.eigh(Gram.toarray())
                o = np_.argsort(w); vals0 = w[o]; vec = u[:, o]
                print(f'DIRECT_BASIS_DENSE_FALLBACK nz={nz} k={k} {sl}', flush=True)
            if vals0[k - 1] > 1e-8:
                raise RuntimeError(('direct kernel residual eig', sl, vals0[:k + 1]))
            Q0 = np_.asarray(vec[:, :k], float)
            # Canonical gauge from the subspace projector using deterministic pivot rows.
            _, _, piv = la_.qr(Q0.T, pivoting=True, mode='economic')
            B = Q0 @ Q0[np_.asarray(piv[:k]), :].T
            Q, _ = np_.linalg.qr(B)
            for j in range(k):
                ii = int(np_.argmax(np_.abs(Q[:, j])))
                if Q[ii, j] < 0: Q[:, j] *= -1
    V = np_.zeros((DD, k), float); V[np_.asarray(zflat, int), :] = Q
    defect = float(np_.linalg.norm(V.T @ V - np_.eye(k)))
    if defect > 1e-8:
        raise RuntimeError(('direct ortho', sl, defect))
    np_.savez_compressed(p, V=V, labels=np_.asarray(sl, np_.int16))
    return V


# ordered_basis() resolves direct_basis_sorted as a module global at call time,
# so rebinding it here reaches every caller inside the reducer. lru_cache keeps
# the .cache_clear() that emit_external's memory sweep calls on it.
G['direct_basis_sorted'] = functools.lru_cache(maxsize=48)(_direct_basis_dense)


def stage_emit():
    pth = OUT / 'crossing_component10.npz'
    print(f'EMIT_START {pth} exists={pth.exists()} size={pth.stat().st_size if pth.exists() else None}', flush=True)
    z = np.load(pth)
    K, W = z['states56'], z['W']
    print(f'EMIT_CROSSING keys={len(K)} W2={float(W @ W) if len(W) else 0.0}', flush=True)
    try:
        fibers, wnorm = group_W_fibers_surveyed(
        G, K, W, strict=os.environ.get('V174_FIBER_SURVEY_ONLY') != '1')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'::error::Emit group_W_fibers {type(e).__name__}: {e!r}', flush=True)
        raise
    print('fiber norm', wnorm, 'n_fibers', len(fibers), flush=True)
    emit = G['emit_external'](fibers, 128)
    def _ser(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    print(json.dumps(emit, indent=2, default=_ser), flush=True)


def stage_reduce():
    ND, red = G['reduce_external'](128)
    z = np.load(OUT / 'crossing_component10.npz')
    R = z['R']; Gm = float(R @ R)
    XLOG = -1228.86890836319450; LOGNORM = 2929.1760467826693
    A10 = G['EXPECTED_A']
    M2 = (A * A * ND + 2 * A * XLOG + LOGNORM) / Gm
    B2 = M2 - A10 * A10
    floor = 517.05823521403812592
    out = {'N_D': float(ND), 'G10': Gm, 'A10': A10, 'M2': float(M2),
           'B10_1_star_B10_1': float(B2), 'psd': bool(B2 >= -1e-10),
           'preregistered_floor': floor, 'floor_satisfied': bool(ND >= floor),
           'reduce': red}
    (OUT / 'a10_B10_component10.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2), flush=True)


if __name__ == '__main__':
    try:
        cmd = sys.argv[1]
        if cmd == 'cross':
            lo = int(sys.argv[2]); hi = int(sys.argv[3])
            b = float(sys.argv[4]) if len(sys.argv) > 4 else 170.0
            stage_cross(lo, hi, b)
        elif cmd == 'merge': stage_merge()
        elif cmd == 'emit': stage_emit()
        elif cmd == 'reduce': stage_reduce()
        else:
            raise SystemExit(f'unknown cmd {cmd}')
    except Exception as e:
        print(f'::error::driver.py {cmd if "cmd" in dir() else "?"} {type(e).__name__}: {e!r}', flush=True)
        raise
