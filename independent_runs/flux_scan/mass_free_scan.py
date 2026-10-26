#!/usr/bin/env python3
"""Mass-free flux selection, run exactly as the manuscript defines it.

Source of every definition (UGCT_Principia_strengthened_post_review 5.tex, Ch. "The Flux
Attractor and Explicit Integer Vectors", Definition "Flux-admissible attractor triple" and
Section "Full Hypergeometric Attractor Solve"; PICARD FUCHS full RESULTS.pdf, Step 4):

  * candidates   : n in Z^4 with 0 < sum n_i^2 <= 44            (clause i, tadpole)
  * superpotential W(z) = sum_mu n^mu omega_mu(z),
                   omega_mu(z) = omega_mu(0) * 4F3(a_1/5,..,a_4/5; 1,1,1; 3125 z)
  * attractor    : D_z W = 0 on the real physical branch 0 < z < 1/3125   (clauses ii, iii)
  * hierarchy    : 0 < Y_u < Y_c < Y_t, 0 < Y_d < Y_s < Y_b, 0 < Y_e < Y_mu < Y_tau  (clause iv)
No measured mass enters any clause.

Completions the text leaves implicit (each is reported as a separate variant, none is tuned):
  * index mu <-> period: monomial type b <-> character a = b + (1,1,1,1,1), the Griffiths
    residue correspondence for H^{2,1} of the Fermat quintic (types are the C_lin columns).
  * omega_mu(0) = (1/5) prod Gamma(a_i/5)  (the manuscript's Griffiths formula).
  * "a_1..a_4": the first four entries of the sorted character (as in the March/April code
    and in the repository's compute_pf_basis.py), or the last four (variant).
  * D_z: flat derivative dW/dz (the April 10 code), or D_z W = dW/dz + K_z W with the
    manuscript's K = -log vol, vol = (5/6)|omega_0|^2, omega_0 = sum (5n)!/(n!)^5 z^n.
  * Yukawa used in clause iv: Y_f = |omega_f(0) F_f(z*)|^2 eta_f with eta_f the manuscript's
    fixed RG factors (the hypergeometric deformation map of Step 4).
Usage: python3 mass_free_scan.py [--shard I --nshards N] [--out results.json]
"""
import argparse, itertools, json, math, sys, time
import numpy as np
from multiprocessing import Pool

MT = [(0, 0, 0, 2, 3), (0, 0, 1, 1, 3), (0, 0, 1, 2, 2), (0, 1, 1, 1, 2)]   # C_lin column order
PRINTED = {3: (-1, 3, 2, 5), 2: (2, 2, 5, -2), 1: (1, -2, -3, -3)}
PRINTED_Z = {3: 1.855592e-05, 2: 1.647039e-05, 1: 1.0e-10}                 # PICARD FUCHS full RESULTS.pdf
FERMION = {"t": (1, 1, 1, 1, 1), "b": (1, 1, 2, 2, 4), "tau": (1, 1, 1, 3, 4),
           "c": (1, 1, 2, 3, 3), "mu": (2, 2, 2, 2, 2), "s": (1, 2, 4, 4, 4),
           "d": (2, 2, 3, 4, 4), "u": (3, 3, 3, 3, 3), "e": (4, 4, 4, 4, 4)}
ETA = {"t": 2.14, "b": 4.52, "tau": 1.77, "c": 5.01, "mu": 1.77, "s": 5.31, "d": 5.09, "u": 4.51, "e": 1.77}
GEN_OF = {"t": 3, "b": 3, "tau": 3, "c": 2, "mu": 2, "s": 2, "u": 1, "d": 1, "e": 1}
CHAINS = [("u", "c", "t"), ("d", "s", "b"), ("e", "mu", "tau")]
XMAX = 0.99            # x = 3125 z; stay off the conifold x = 1
NTERMS = 12000


def omega_fermat(a):
    return math.prod(math.gamma(ai / 5) for ai in a) / 5


def params(a, variant):
    s = sorted(a)
    return [v / 5 for v in (s[:4] if variant == "first4" else s[1:])]


def hyp4f3(p, x):
    """4F3(p;1,1,1;x) and d/dx, vectorized over x (|x| <= 0.99), float64 series."""
    x = np.asarray(x, dtype=float)
    T = np.ones_like(x); F = np.ones_like(x); D = np.zeros_like(x)
    for n in range(NTERMS):
        r = (p[0] + n) * (p[1] + n) * (p[2] + n) * (p[3] + n) / (n + 1) ** 4
        T = T * x * r                       # term n+1
        F += T
        D += (n + 1) * T
        if n > 50 and np.max(np.abs(T)) < 1e-300:
            break
    return F, D / x


def basis(x, variant):
    """Rows: omega_mu(0) F_mu, omega_mu(0) F_mu', for the four monomial types."""
    Fv, Dv = [], []
    for b in MT:
        a = tuple(bi + 1 for bi in b)
        F, D = hyp4f3(params(a, variant), x)
        w = omega_fermat(a)
        Fv.append(w * F); Dv.append(w * D)
    w0, dw0 = hyp4f3([0.2, 0.4, 0.6, 0.8], x)          # Dwork fundamental period
    return np.array(Fv), np.array(Dv), dw0 / w0           # K_x = -omega0'/omega0


def g_matrix(N, x, variant, equation, cache={}):
    key = (variant, equation, x.size, float(x[0]), float(x[-1]))
    if key not in cache:
        Fv, Dv, L = basis(x, variant)
        cache[key] = Dv if equation == "flat" else Dv - L * Fv
    return N @ cache[key]


def roots_on_grid(N, x, variant, equation):
    """Sign changes of D_xW along the grid -> linearly interpolated roots."""
    G = g_matrix(N, x, variant, equation)
    out = []
    for i in range(N.shape[0]):
        g = G[i]
        idx = np.nonzero(np.sign(g[:-1]) * np.sign(g[1:]) < 0)[0]
        rs = [float(x[k] - g[k] * (x[k + 1] - x[k]) / (g[k + 1] - g[k])) for k in idx]
        out.append(rs)
    return out


def refine(n, xlo, xhi, variant, equation):
    n = np.asarray(n, float)
    f = lambda xx: float(g_matrix(n[None, :], np.array([xx]), variant, equation, cache={})[0, 0])
    flo = f(xlo)
    for _ in range(60):
        xm = 0.5 * (xlo + xhi); fm = f(xm)
        if (fm < 0) == (flo < 0):
            xlo, flo = xm, fm
        else:
            xhi = xm
    return 0.5 * (xlo + xhi)


def yukawa(f, x, variant):
    F, _ = hyp4f3(params(FERMION[f], variant), np.array([x]))
    return (omega_fermat(FERMION[f]) * F[0]) ** 2 * ETA[f]


def candidates():
    return [v for v in itertools.product(range(-6, 7), repeat=4) if 0 < sum(c * c for c in v) <= 44]


def run_variant(args):
    variant, equation, branch, cand, ngrid = args
    if branch == "positive":
        x = np.logspace(-14, math.log10(XMAX), ngrid)
    else:
        x = -np.logspace(math.log10(XMAX), -14, ngrid)
    out = {}
    N = np.array(cand, float)
    for s in range(0, len(cand), 800):
        rr = roots_on_grid(N[s:s + 800], x, variant, equation)
        for v, r in zip(cand[s:s + 800], rr):
            if r:
                out[str(v)] = r
    return (variant, equation, branch), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default="mass_free_scan_results.json")
    ap.add_argument("--grid", type=int, default=6000)
    a = ap.parse_args()
    t0 = time.time()
    cand_all = candidates()
    cand = cand_all[a.shard::a.nshards]
    jobs = [(v, e, b, cand, a.grid) for v in ("first4", "last4") for e in ("flat", "kahler") for b in ("positive", "negative")]
    with Pool(a.procs) as pool:
        res = dict(pool.map(run_variant, jobs))
    report = {"n_candidates_total": len(cand_all), "shard": a.shard, "nshards": a.nshards, "grid": a.grid,
              "n_candidates_this_shard": len(cand), "variants": {}}
    for (v, e, b), roots in res.items():
        key = f"{v}|{e}|{b}"
        printed = {}
        for g, vec in PRINTED.items():
            if vec in cand:
                rs = roots.get(str(vec), [])
                printed[g] = {"vector": vec, "x_roots": rs, "z_roots": [r / 3125 for r in rs],
                              "printed_z": PRINTED_Z[g]}
        report["variants"][key] = {"n_with_root": len(roots), "roots": roots, "printed": printed}
    report["seconds"] = round(time.time() - t0, 1)
    json.dump(report, open(a.out, "w"))
    print(json.dumps({k: {"n_with_root": v["n_with_root"], "printed": v["printed"]} for k, v in report["variants"].items()}, indent=1))
    print("seconds", report["seconds"])


if __name__ == "__main__":
    main()
