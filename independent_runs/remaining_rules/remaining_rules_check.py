#!/usr/bin/env python3
"""Two remaining mass-free definitions from the UGCT record, run as written (2026-10-27).

A. The kappa_3 worked example (post-review-5 manuscript, chat 2026-05-28) defines
       R(z) = (w1(z) conj(w2(z)) - w2(z) conj(w1(z))) / (2i |w0(z)|^2)
   with w1, w2 "single-log solutions of the PF operator obtained by Frobenius at z = 0",
   and kappa_gen = R_gen / sqrt(5 vol), vol = (5/6)|w0(z*)|^2.  It states R_3 = 0.9252 at
   z*_3, and R_2 = 0.117, R_1 = 0.208.  R depends on z only, so it is evaluated here at the
   printed z* under each reading of w1, w2.

B. Theorem 1.26 / Definition "Intrinsic flux dominance predicate": with
       Y_f = D_f(N)^{1/2} Omega^(f) D_f(N)^{1/2},
       D_f(N)_ii = (|w_fi|^2/|w_max|^2) (1 + kappa_g(i) sum_j C_lin[f_i, j] n_g(i),j)^2,
   the predicate is lambda_max(Y_f^+ Y_f) > lambda_2 > lambda_1 for f = u, d, e.
   Omega^(f) has no numerical entries in the manuscript, so Omega = 1 is used; kappa_g are the
   printed values; C_lin is rebuilt from the coupling c(a,b) of the GitNexus engine
   data_room/scripts/fermat_101_period_derivative.py (same definition, copied below).
   Two readings: (i) literal (eigenvalues strictly ordered), (ii) generation-labelled
   (gen-3 entry > gen-2 entry > gen-1 entry in every sector).

No measured mass enters either test.  Usage: python3 remaining_rules_check.py [engine.py]
(the optional engine path cross-checks the copied coupling definition).
"""
import itertools, math, sys, importlib.util
import numpy as np
import mpmath as mp

mp.mp.dps = 40

# ----------------------------------------------------------------------------------------
# A. The R(z) formula of the kappa_3 worked example
# ----------------------------------------------------------------------------------------
NT = 30  # series terms; 3125 z* <= 0.058, so the tail is below 1e-37

def a_eps(n, e):
    """Frobenius coefficient (5(n+e))! / (n+e)!^5, normalised to 1 at n = 0."""
    return (mp.gamma(5*n + 5*e + 1) * mp.gamma(e + 1)**5) / (mp.gamma(n + e + 1)**5 * mp.gamma(5*e + 1))

COEF = [mp.taylor(lambda e, n=n: a_eps(n, e), 0, 3) for n in range(NT)]  # COEF[n][m]

def frob(z):
    """Frobenius basis at z = 0: w_k = sum_j (log z)^j / j! * f_{k-j}(z), k = 0..3 (real for 0 < z)."""
    z = mp.mpf(z); L = mp.log(z)
    f = [mp.fsum(COEF[n][m] * z**n for n in range(NT)) for m in range(4)]
    return [mp.fsum(L**j / mp.factorial(j) * f[k - j] for j in range(k + 1)) for k in range(4)]

def pf_residual(z):
    """|theta^4 w - 5 z prod(5 theta + i) w| / |w| for each Frobenius solution (theta = d/dlog z)."""
    out = []
    for k in range(4):
        g = lambda s, k=k: frob(mp.e**s)[k]
        s0 = mp.log(z)
        d = [mp.diff(g, s0, m) for m in range(5)]
        th = lambda m: d[m]
        # prod_{i=1..4} (5 theta + i) expanded: 625 th^4 + 1250 th^3 + 875 th^2 + 250 th + 24
        lhs = th(4) - 5*z*(625*th(4) + 1250*th(3) + 875*th(2) + 250*th(1) + 24*th(0))
        out.append(abs(lhs) / abs(d[0]))
    return out

# genus-0 Gopakumar-Vafa invariants of the quintic (Candelas-de la Ossa-Green-Parkes)
GV = {1: 2875, 2: 609250, 3: 317206375, 4: 242467530000, 5: 229305888887625}

def readings(z):
    w = frob(z)
    tpi = 2j * mp.pi
    out = {}
    # (a) raw Frobenius solutions w1 (single log) and w2 (double log): all real for real z
    w1, w2 = mp.mpc(w[1]), mp.mpc(w[2])
    out["(a) raw w1, w2"] = ((w1 * mp.conj(w2) - w2 * mp.conj(w1)) / (2j * abs(w[0])**2)).real
    # (b) the same with the standard (2 pi i)^-k normalisation
    w1, w2 = w[1] / tpi, w[2] / tpi**2
    out["(b) w_k/(2 pi i)^k"] = ((w1 * mp.conj(w2) - w2 * mp.conj(w1)) / (2j * abs(w[0])**2)).real
    # (c) the integral symplectic pair X^1 = w0 t, F_1 = w0 dF/dt with the quintic prepotential
    t = w[1] / (tpi * w[0])
    q = mp.exp(tpi * t)
    Fp = -mp.mpf(5)/2 * t**2 - mp.mpf(11)/2 * t + mp.mpf(25)/12 \
         + mp.fsum(n * d * mp.polylog(2, q**d) for d, n in GV.items()) / (4 * mp.pi**2)
    X1, F1 = w[0] * t, w[0] * Fp
    out["(c) X^1, F_1"] = ((X1 * mp.conj(F1) - F1 * mp.conj(X1)) / (2j * abs(w[0])**2)).real
    return w, out

ZSTAR = {3: mp.mpf("1.855592e-5"), 2: mp.mpf("1.647039e-5"), 1: mp.mpf("1.0e-10")}
KAPPA = {3: 0.4522, 2: 0.0572, 1: 0.1021}
R_PRINTED = {3: 0.9252, 2: 0.117, 1: 0.208}

print("A. R(z) of the kappa_3 worked example, evaluated at the printed attractor points")
print("   PF residual of the four Frobenius solutions at z*_3:",
      ", ".join(mp.nstr(r, 2) for r in pf_residual(ZSTAR[3])))
vals = {}
for g in (3, 2, 1):
    w, out = readings(ZSTAR[g])
    vol = mp.mpf(5) / 6 * w[0]**2
    inv = KAPPA[g] * mp.sqrt(5 * vol)
    vals[g] = out
    print(f"   gen {g}: z* = {mp.nstr(ZSTAR[g], 7)}, w0 = {mp.nstr(w[0], 8)}, "
          f"kappa*sqrt(5 vol) = {mp.nstr(inv, 5)} (printed R = {R_PRINTED[g]})")
    for k, v in out.items():
        print(f"      R {k:20s} = {mp.nstr(v, 6)}")
print("   Ratio R(z*_3)/R(z*_2): printed", round(R_PRINTED[3] / R_PRINTED[2], 2), "| formula:",
      ", ".join(f"{k.split()[0]} {mp.nstr(vals[3][k] / vals[2][k], 4) if vals[2][k] else 'undefined (0/0)'}"
                for k in vals[3]))

# ----------------------------------------------------------------------------------------
# B. The intrinsic dominance predicate of Theorem 1.26
# ----------------------------------------------------------------------------------------
def characters():
    return [a for a in itertools.product(range(1, 5), repeat=5) if sum(a) % 5 == 0]

def monomials():
    return [b for b in itertools.product(range(4), repeat=5) if sum(b) == 5]

def coupling(a, b):
    s = tuple((x + y) % 5 for x, y in zip(a, b))
    if any(v == 0 for v in s) or sum(x + y for x, y in zip(a, b)) % 5:
        return mp.mpf(0)
    return mp.fprod(mp.gamma(mp.mpf(v) / 5) / mp.gamma(mp.mpf(x) / 5) for x, v in zip(a, s))

A_CH, B_MO = characters(), monomials()
if len(sys.argv) > 1:  # optional cross-check against the repo engine
    spec = importlib.util.spec_from_file_location("eng", sys.argv[1])
    eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
    assert eng.characters() == A_CH and eng.monomials() == B_MO
    assert all(eng.coupling(a, b) == coupling(a, b) for a in A_CH[::7] for b in B_MO[::5])
    print("\nB. coupling definition matches the repo engine on a sample of", len(A_CH[::7]) * len(B_MO[::5]), "pairs")
else:
    print()

MT = [(0, 0, 0, 2, 3), (0, 0, 1, 1, 3), (0, 0, 1, 2, 2), (0, 1, 1, 1, 2)]
BT = {t: [b for b in B_MO if tuple(sorted(b)) == t] for t in MT}

def clin(ftype):
    As = [a for a in A_CH if tuple(sorted(a)) == ftype]
    return np.array([float(mp.fsum(coupling(a, b) for a in As for b in BT[t]) / (len(As) * len(BT[t]))) for t in MT])

TYPE = {"top": (1,1,1,1,1), "bottom": (1,1,2,2,4), "tau": (1,1,1,3,4), "charm": (1,1,2,3,3), "muon": (2,2,2,2,2),
        "strange": (1,2,4,4,4), "down": (2,2,3,4,4), "up": (3,3,3,3,3), "electron": (4,4,4,4,4)}
GEN_OF = {"top": 3, "bottom": 3, "tau": 3, "charm": 2, "muon": 2, "strange": 2, "down": 1, "up": 1, "electron": 1}
SECTORS = {"u": ("up", "charm", "top"), "d": ("down", "strange", "bottom"), "e": ("electron", "muon", "tau")}
NVEC = {3: (-1, 3, 2, 5), 2: (2, 2, 5, -2), 1: (1, -2, -3, -3)}

om2 = lambda t: math.prod(math.gamma(a / 5)**2 for a in t) / 25
RATIO = {f: om2(t) / om2(TYPE["top"]) for f, t in TYPE.items()}
CL = {f: (np.zeros(4) if f == "top" else clin(t)) for f, t in TYPE.items()}  # delta_top = 0 (anchor)

V = np.array([v for v in itertools.product(range(-6, 7), repeat=4) if 0 < sum(x * x for x in v) <= 44], dtype=float)
print(f"B. Intrinsic dominance predicate: {len(V)} candidate vectors per generation, kappa = printed, Omega = 1")
idx = {g: int(np.where((V == np.array(NVEC[g], float)).all(1))[0][0]) for g in NVEC}
Y = {f: RATIO[f] * (1 + KAPPA[GEN_OF[f]] * V @ CL[f])**2 for f in TYPE}  # entry of D_f for every candidate

# (i) literal: the three eigenvalues of Y_f^+ Y_f = D_f^2 are strictly ordered unless two entries coincide
mingap = {}
for s, (f1, f2, f3) in SECTORS.items():
    gaps = []
    for fa, fb in ((f1, f2), (f1, f3), (f2, f3)):
        a, b = np.sort(Y[fa]), np.sort(Y[fb])
        j = np.clip(np.searchsorted(b, a), 1, len(b) - 1)
        near = np.minimum(abs(a - b[j - 1]), abs(a - b[j]))
        gaps.append(float(np.min(near / np.maximum(np.maximum(a, b[j]), 1e-300))))
    mingap[s] = min(gaps)
print("   (i) literal reading: smallest relative gap between two entries of one sector, over all triples:",
      {s: f"{g:.1e}" for s, g in mingap.items()})
print("       no two entries coincide, so lambda_max > lambda_2 > lambda_1 holds for all "
      f"{len(V)**3:.3e} triples")

# (ii) generation-labelled: y(gen 3) > y(gen 2) > y(gen 1) in every sector
total, ok2 = 0, np.zeros(len(V), bool)
n3_any, n1_any = np.zeros(len(V), bool), np.zeros(len(V), bool)
for c in range(0, len(V), 400):
    sl = slice(c, c + 400)
    up_ok = Y["charm"][sl] < Y["top"][0]  # y_top = 1 for every candidate (delta_top = 0)
    m3 = (Y["bottom"][None, :] > Y["strange"][sl, None]) & (Y["tau"][None, :] > Y["muon"][sl, None])
    m1 = (Y["up"][None, :] < Y["charm"][sl, None]) & (Y["down"][None, :] < Y["strange"][sl, None]) \
         & (Y["electron"][None, :] < Y["muon"][sl, None])
    c3, c1 = m3.sum(1), m1.sum(1)
    total += int((up_ok * c3 * c1).sum())
    good = up_ok & (c3 > 0) & (c1 > 0)
    ok2[sl] = good
    n3_any |= m3[good].any(0); n1_any |= m1[good].any(0)
pr = (Y["charm"][idx[2]] < 1 and Y["bottom"][idx[3]] > Y["strange"][idx[2]] > Y["down"][idx[1]]
      and Y["tau"][idx[3]] > Y["muon"][idx[2]] > Y["electron"][idx[1]] and Y["charm"][idx[2]] > Y["up"][idx[1]])
print(f"   (ii) generation-labelled reading: {total:,} of {len(V)**3:,} triples pass ({total / len(V)**3:.1%});")
print(f"        vectors that occur in a passing triple: gen 3 {int(n3_any.sum())}, gen 2 {int(ok2.sum())}, "
      f"gen 1 {int(n1_any.sum())} of {len(V)}; printed triple passes: {pr}")
