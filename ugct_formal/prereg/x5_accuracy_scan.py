"""Scans A and B of X5_ACCURACY_PREREG_2026-11-25.md: can numbers that X_5 determines make Law 1 accurate?

Scan A: compare the gap delta = alpha^-1 - Law 1 with D^e alpha^k pi^m, where:
        - D is in the X_5 dictionary, e = +-1, k = 0..4, m = -3..3;
        - a hit is within 1 sigma of delta;
        - the reference family is D = 1.
Scan B: compare alpha^-1 itself with pi^m D1^p1 D2^p2 D3^p3, where:
        - at most three distinct dictionary numbers are used, p in {+-1, +-2, +-3}, m = -3..3;
        - a hit is within 2 sigma.
Null models: the same families against random targets (log-uniform), with the same relative window.
Every hit is recomputed at 50 digits, and each window count must equal the number of verified hits.
The run exits with status 1 if a consistency check fails.

Run: python3 -I x5_accuracy_scan.py   (needs numpy, mpmath, cypari2)
"""
import importlib.util
import os
import sys
from itertools import combinations

import numpy as np
from mpmath import mp, mpf, pi, log, nstr

ALPHA_INV = mpf("137.035999177")      # CODATA 2022
SIGMA = mpf("2.1e-8")
EXPS = np.array([-3, -2, -1, 1, 2, 3])
PI_EXPS = np.arange(-3, 4)
LPI = float(log(pi))
SLACK = 1e-9                          # float pre-selection margin in log space; every candidate is decided at 50 digits


def rel_window(r):
    """log offsets of the relative window [t (1 - r), t (1 + r)]."""
    return float(log(1 - r)), float(log(1 + r))


def window_hits(sorted_vals, log_targets, lo_off, hi_off):
    """Number of sorted log values in [log t + lo_off, log t + hi_off], for each target."""
    lo = np.searchsorted(sorted_vals, log_targets + lo_off, side="left")
    hi = np.searchsorted(sorted_vals, log_targets + hi_off, side="right")
    return hi - lo


# ---------------------------------------------------------------- family A

def family_a(logd, log_alpha):
    """log values and labels (i, e, k, m) of D_i^e alpha^k pi^m; i = -1 is the reference D = 1."""
    vals, labs = [], []
    for i in range(-1, len(logd)):
        for e in ((1,) if i < 0 else (1, -1)):
            for k in range(5):
                for m in PI_EXPS:
                    vals.append((0.0 if i < 0 else e * logd[i]) + k * log_alpha + m * LPI)
                    labs.append((i, e, k, int(m)))
    return np.array(vals), labs


def scan_a(entries, alpha, target, sigma):
    """Verified hits |D^e alpha^k pi^m - target| <= sigma, and the float window count of the X_5 forms."""
    logd = [float(log(e["value"])) for e in entries]
    va, la = family_a(logd, float(log(alpha)))
    is_ref = np.array([lab[0] < 0 for lab in la])
    lo, hi = rel_window(sigma / target)
    lt = float(log(target))
    hits = []
    for idx in np.nonzero((va >= lt + lo - SLACK) & (va <= lt + hi + SLACK))[0]:
        i, e, k, m = la[idx]
        D = mpf(1) if i < 0 else entries[i]["value"] ** e
        val = D * alpha ** k * pi ** m
        if abs(val - target) <= sigma:
            hits.append((i, e, k, m, val))
    count = int(window_hits(np.sort(va[~is_ref]), np.array([lt]), lo, hi)[0])
    return hits, count, va, is_ref


# ---------------------------------------------------------------- family B

def family_b_size(n):
    return 7 * (1 + 6 * n + 36 * n * (n - 1) // 2 + 216 * n * (n - 1) * (n - 2) // 6)


def family_b_core(logd):
    """Core log values sum_i p_i log D_i over subsets of size 0..3, with a decoder."""
    n = len(logd)
    d = np.asarray(logd, dtype=float)
    blocks = [np.zeros(1), (d[:, None] * EXPS[None, :]).ravel()]
    pairs = np.array(list(combinations(range(n), 2)), dtype=np.int64).reshape(-1, 2)
    triples = np.array(list(combinations(range(n), 3)), dtype=np.int64).reshape(-1, 3)
    blocks.append((d[pairs[:, 0]][:, None, None] * EXPS[None, :, None]
                   + d[pairs[:, 1]][:, None, None] * EXPS[None, None, :]).ravel())
    blocks.append((d[triples[:, 0]][:, None, None, None] * EXPS[None, :, None, None]
                   + d[triples[:, 1]][:, None, None, None] * EXPS[None, None, :, None]
                   + d[triples[:, 2]][:, None, None, None] * EXPS[None, None, None, :]).ravel())
    starts = np.cumsum([0] + [len(b) for b in blocks])

    def decode(c):
        """core index -> tuple of (dictionary index, exponent)."""
        c = int(c)
        if c < starts[1]:
            return ()
        if c < starts[2]:
            c -= starts[1]
            return ((c // 6, int(EXPS[c % 6])),)
        if c < starts[3]:
            c -= starts[2]
            i, j = pairs[c // 36]
            return ((int(i), int(EXPS[(c // 6) % 6])), (int(j), int(EXPS[c % 6])))
        c -= starts[3]
        i, j, k = triples[c // 216]
        return ((int(i), int(EXPS[(c // 36) % 6])), (int(j), int(EXPS[(c // 6) % 6])),
                (int(k), int(EXPS[c % 6])))

    return np.concatenate(blocks), decode


def family_b(core):
    """Full family: core + m log pi. Flat index f -> core index f // 7 and m = PI_EXPS[f % 7]."""
    return (core[:, None] + LPI * PI_EXPS[None, :]).ravel()


def value_b(entries, combo, m):
    v = pi ** int(m)
    for i, p in combo:
        v *= entries[i]["value"] ** p
    return v


def label_b(entries, combo, m):
    parts = ([f"pi^{m}"] if m else []) + [f"{entries[i]['name']}^{p}" for i, p in combo]
    return " * ".join(parts) if parts else "1"


def scan_b(entries, vb, decode, target, tol):
    """Verified hits |form - target| <= tol: (number of verified forms, distinct (label, value) list)."""
    lt = float(log(target))
    lo, hi = rel_window(tol / target)
    n_ok, distinct, seen = 0, [], set()
    for f in np.nonzero((vb >= lt + lo - SLACK) & (vb <= lt + hi + SLACK))[0]:
        combo, m = decode(f // 7), int(PI_EXPS[f % 7])
        val = value_b(entries, combo, m)
        if abs(val - target) <= tol:
            n_ok += 1
            key = nstr(val, 30)
            if key not in seen:
                seen.add(key)
                distinct.append((label_b(entries, combo, m), val))
    return n_ok, distinct


# ---------------------------------------------------------------- main run

def main():
    mp.dps = 50
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("x5_dictionary", os.path.join(here, "x5_dictionary.py"))
    xd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(xd)
    entries, fails, _ = xd.build()
    mp.dps = 50
    if fails:
        print("dictionary checks FAILED:", fails)
        sys.exit(1)
    problems = []
    names = [e["name"] for e in entries]
    L = next(e["value"] for e in entries if e["name"] == "L")
    delta = ALPHA_INV - L
    alpha = 1 / ALPHA_INV
    rng = np.random.default_rng(20261125)
    print(f"dictionary: {len(entries)} numbers; delta = {nstr(delta, 8)} +- {nstr(SIGMA, 2)} "
          f"(relative {nstr(SIGMA / delta, 3)})")

    # ---- Scan A
    hits, count, va, is_ref = scan_a(entries, alpha, delta, SIGMA)
    print(f"\nScan A: {np.count_nonzero(~is_ref)} X_5 forms + {np.count_nonzero(is_ref)} reference forms (D = 1)")
    for i, e, k, m, val in hits:
        D = mpf(1) if i < 0 else entries[i]["value"] ** e
        pred = L + D * (1 / L) ** k * pi ** m                # alpha -> 1/Law 1: no measured input
        lab = "1 (reference)" if i < 0 else f"{names[i]}^{e}"
        print(f"  hit: {lab} * alpha^{k} * pi^{m} = {nstr(val, 10)} ({nstr((val - delta) / SIGMA, 3)} sigma); "
              f"with alpha -> 1/L: alpha^-1 = {nstr(pred, 14)} ({nstr((pred - ALPHA_INV) / SIGMA, 3)} sigma)")
    n_x5 = sum(1 for h in hits if h[0] >= 0)
    print(f"  X_5 hits: {n_x5}; reference hits: {len(hits) - n_x5}")
    if count != n_x5:
        problems.append(f"Scan A: window count {count} != verified X_5 hits {n_x5}")
    lo, hi = rel_window(SIGMA / delta)
    T = float(log(delta)) + rng.uniform(-1, 1, 100000) * float(log(10))
    p_x5 = np.mean(window_hits(np.sort(va[~is_ref]), T, lo, hi) > 0)
    p_ref = np.mean(window_hits(np.sort(va[is_ref]), T, lo, hi) > 0)
    print(f"  null (100,000 targets log-uniform in [delta/10, 10 delta]): P(hit) = {p_x5:.4f} for the X_5 forms, "
          f"{p_ref:.4f} for the reference forms")

    # ---- Scan B
    core, decode = family_b_core([float(log(e["value"])) for e in entries])
    vb = family_b(core)
    del core
    if len(vb) != family_b_size(len(entries)):
        problems.append(f"Scan B: family size {len(vb)} != {family_b_size(len(entries))}")
    print(f"\nScan B: {len(vb):,} forms (products of up to three dictionary numbers, exponents +-1..3, pi^-3..3)")
    t0 = float(log(ALPHA_INV))
    n_ok, distinct = scan_b(entries, vb, decode, ALPHA_INV, 2 * SIGMA)
    for lab, val in distinct:
        print(f"  hit: {lab} = {nstr(val, 15)} ({nstr((val - ALPHA_INV) / SIGMA, 3)} sigma)")
    print(f"  forms within 2 sigma: {n_ok} ({len(distinct)} distinct values)")
    near = np.argpartition(np.abs(vb - t0), 60)[:60]
    near = near[np.argsort(np.abs(vb[near] - t0))]
    print("  closest distinct values:")
    seen, shown = set(), 0
    for f in near:
        combo, m = decode(f // 7), int(PI_EXPS[f % 7])
        val = value_b(entries, combo, m)
        if nstr(val, 30) in seen:
            continue
        seen.add(nstr(val, 30))
        print(f"    {label_b(entries, combo, m):<58} = {nstr(val, 15)} ({nstr((val - ALPHA_INV) / SIGMA, 4)} sigma)")
        shown += 1
        if shown == 8:
            break
    sb = np.sort(vb)
    loB, hiB = rel_window(2 * SIGMA / ALPHA_INV)
    real_b = int(window_hits(sb, np.array([t0]), loB, hiB)[0])
    if real_b != n_ok:
        problems.append(f"Scan B: window count {real_b} != verified hits {n_ok}")
    TB = t0 + rng.uniform(-1, 1, 100000) * float(log(1.5))
    pB = np.mean(window_hits(sb, TB, loB, hiB) > 0)
    print(f"  null (100,000 targets log-uniform in [alpha^-1/1.5, 1.5 alpha^-1]): P(hit within 2 sigma) = {pB:.5f}")
    # secondary: how often does a random target get a form as close as Law 1 is to alpha^-1?
    off1 = abs(L - ALPHA_INV) * (1 + mpf("1e-6"))
    n1, d1 = scan_b(entries, vb, decode, ALPHA_INV, off1)
    lo1, hi1 = rel_window(off1 / ALPHA_INV)
    p1 = np.mean(window_hits(sb, TB, lo1, hi1) > 0)
    law1_in = any(abs(val - L) < mpf(10) ** -40 for _, val in d1)
    print(f"  secondary: distinct values at least as close to alpha^-1 as Law 1 ({nstr(off1 / ALPHA_INV * 1e9, 4)} ppb): "
          f"{len(d1)}, Law 1 among them: {law1_in}; random targets with such a form: {p1:.4f}")
    for lab, val in d1:
        print(f"    {lab} = {nstr(val, 15)} ({nstr((val - ALPHA_INV) / SIGMA, 4)} sigma)")
    if not law1_in:
        problems.append("Law 1 not found in family B")
    if int(window_hits(sb, np.array([t0]), lo1, hi1)[0]) != n1:
        problems.append("secondary: window count != verified count")

    if problems:
        print("FAILED:", *problems, sep="\n  ")
        sys.exit(1)
    print("\nconsistency checks passed")


if __name__ == "__main__":
    main()
