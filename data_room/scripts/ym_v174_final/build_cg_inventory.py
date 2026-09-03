#!/usr/bin/env python3
"""Split the V174 reduction into a memory-heavy phase and a portable one.

The wall is not the reduction. It is a handful of intertwiner solves inside it.
Measured on the component-10 payload, the largest is 9142x4824, whose dgesdd
allocation is ~2.0 GiB (U 0.33, Vh 0.17, workspace ~7n^2 = 1.21, M 0.33) before
any interpreter overhead -- it OOM-killed a 3.9 GiB container even with the
accumulators empty. The crossing itself, once those solves are cached, runs at
600 sources in 24 s and needs almost nothing.

So do the expensive part ONCE, on a machine that has the memory, and pin the
result as an artifact:

    phase 1  build_cg_inventory.py --build     needs ~8 GiB, run once
    phase 2  driver.py cross/merge/emit/reduce needs ~1 GiB, runs anywhere

Phase 1 walks the crossing purely for its side effects, discarding accR/accW so
the accumulators never compete with LAPACK for memory, and writes every solve to
disk. Phase 2 restores that inventory and never opens a large SVD again.

This also removes a reproducibility problem that exists today independently of
memory. `robust_null_space` falls back from gesdd to gesvd whenever gesdd raises
LinAlgError, and whether gesdd converges is version- and platform-dependent. So
which driver produces a given intertwiner basis is not currently fixed across
machines. Pinning the inventory by hash makes the whole computation
deterministic: every later run consumes exactly the bases the pinned run
produced, whichever driver produced them.

    --build      populate the cache by walking the crossing, discarding results
    --manifest   hash every cache entry into cg_inventory_manifest.json
    --verify     check a restored cache against a manifest before reducing
"""
import argparse, hashlib, json, os, pathlib, sys, time

CACHE = pathlib.Path(os.environ.get('V174_CACHE', '/tmp/v174b/cache'))
SUBDIRS = ('ns', 'cg', 'fixed_basis', 'direct_basis', 'mult')


def _load_module():
    # the reducer resolves v135_engine relative to its input dir
    inp = os.environ.get('V174_INPUT', '/tmp/v174b/payload')
    if inp not in sys.path:
        sys.path.insert(0, inp)
    src = open(os.environ.get('V174_REDUCER', '/tmp/v174b/patched3.py')).read()
    src = src.replace("if __name__=='__main__':main()", "")
    g = {'__name__': 'ren', '__file__': 'reducer.py'}
    exec(compile(src, 'reducer.py', 'exec'), g)
    return g


def build(budget):
    """Walk the crossing for side effects only; never retain accR/accW."""
    import numpy as np, gc, math, itertools
    G = _load_module()
    p = G['OUT'] / 'phase.npy'
    if p.exists():
        s = np.load(p)
    else:
        C, _ = G['low_raw_C']()
        s, ncc, contr, eigres, logc = G['recover_phase'](C)
        np.save(p, s); del C; gc.collect()
    phi = s.astype(float) * G['psi']
    low_states = G['low_states']; NLOW = G['NLOW']
    t0 = time.time(); solved0 = len(list((CACHE / 'ns').glob('*.npy')))
    for i in range(NLOW):
        key, vb = low_states[i]
        for pidx in range(24):
            for ar in (1, -1):
                for nk in G['branches'](key, pidx, ar):
                    dg = G['degree'](nk)
                    if dg < 10 or dg > 13 or not G['valid_key'](nk):
                        continue
                    for labs in G['gvl'](nk):
                        G['FIXED_LABELS'].add(G['slabels'](labs))
                    # forces every CG solve this transition needs, then drops it
                    G['transition_choices'](key, nk, pidx, ar, vb, True, True, True)
        if i % 50 == 0:
            for _f in G.values():
                cc = getattr(_f, 'cache_clear', None)
                if cc is not None:
                    try: cc()
                    except Exception: pass
            gc.collect()
            n = len(list((CACHE / 'ns').glob('*.npy')))
            print(f'  INV source {i}/{NLOW}  solves {n} (+{n-solved0})  '
                  f'{time.time()-t0:.0f}s', flush=True)
        if time.time() - t0 > budget:
            print(f'INV_PAUSED at source {i}', flush=True); return i
    print('INV_COMPLETE', flush=True); return NLOW


def manifest(out):
    m = {'schema': 'V174_CG_INVENTORY_V1', 'entries': {}, 'counts': {}}
    total = 0
    for sub in SUBDIRS:
        d = CACHE / sub
        if not d.is_dir():
            continue
        files = sorted(p.name for p in d.iterdir() if p.is_file())
        m['counts'][sub] = len(files)
        h = hashlib.sha256()
        for name in files:
            b = (d / name).read_bytes(); total += len(b)
            h.update(name.encode()); h.update(hashlib.sha256(b).digest())
        m['entries'][sub] = h.hexdigest()
    m['total_bytes'] = total
    m['inventory_sha256'] = hashlib.sha256(
        json.dumps(m['entries'], sort_keys=True).encode()).hexdigest()
    pathlib.Path(out).write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2))
    return m


def verify(path):
    want = json.loads(pathlib.Path(path).read_text())
    got = {}
    for sub in SUBDIRS:
        d = CACHE / sub
        files = sorted(p.name for p in d.iterdir() if p.is_file()) if d.is_dir() else []
        h = hashlib.sha256()
        for name in files:
            h.update(name.encode()); h.update(hashlib.sha256((d / name).read_bytes()).digest())
        got[sub] = h.hexdigest()
    ok = got == want['entries']
    for sub in SUBDIRS:
        mark = 'ok  ' if got.get(sub) == want['entries'].get(sub) else 'FAIL'
        print(f'  {mark} {sub}: {want["counts"].get(sub, 0)} entries')
    print('INVENTORY_VERIFIED' if ok else 'INVENTORY_MISMATCH')
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--budget', type=float, default=1e9)
    ap.add_argument('--manifest', type=str)
    ap.add_argument('--verify', type=str)
    a = ap.parse_args()
    if a.build: build(a.budget)
    if a.manifest: manifest(a.manifest)
    if a.verify: sys.exit(verify(a.verify))
