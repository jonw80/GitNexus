"""Operations O1-O3, exactly as pre-registered in EXACT_COUPLINGS_PREREG_2026-11-24b.md (commit 9c7d521).
python3 -I exact_couplings_tests.py   (mpmath, numpy)
"""
import itertools
from fractions import Fraction
import numpy as np
from mpmath import mp, mpf, mpc, sqrt, sin, pi, gamma, matrix, log

mp.dps = 40
A_OBS, SIG = mpf("137.035999177"), mpf("0.000000021")            # CODATA 2022

# ---- O1: tau of the (1,1,1,3,4) block (T7 model = X5's block by T11), exact forms from the T7 script
s72, s144, r5 = sin(2 * pi / 5), sin(4 * pi / 5), sqrt(5)
t00 = mpc((71 + 7 * r5) / 44, (18 * s72 - s144) / 11)
t01 = mpc((79 + 5 * r5) / 44, (5 * s72 + 4 * s144) / 11)
t11 = mpc((29 + r5) / 22, (2 * s72 + 6 * s144) / 11)
X = matrix([[t00.real, t01.real], [t01.real, t11.real]])
Y = matrix([[t00.imag, t01.imag], [t01.imag, t11.imag]])
Yi = Y ** -1
print(f"tau00 = {mp.nstr(t00, 12)}, tau01 = {mp.nstr(t01, 12)}, tau11 = {mp.nstr(t11, 12)}  (T7 script: 1.96937445097+1.50283927646j, ...)")


def Q(c, d):
    u = [c[0] * X[0, j] + c[1] * X[1, j] + d[j] for j in range(2)]
    w = [c[0] * Y[0, j] + c[1] * Y[1, j] for j in range(2)]
    return sum(u[i] * Yi[i, j] * u[j] for i in range(2) for j in range(2)) + sum(c[i] * Y[i, j] * c[j] for i in range(2) for j in range(2))


vals = []
R = range(-7, 8)
for c0, c1, d0, d1 in itertools.product(R, R, R, R):
    if (c0, c1, d0, d1) != (0, 0, 0, 0):
        vals.append((Q((c0, c1), (d0, d1)), (c0, c1, d0, d1)))
vals.sort(key=lambda t: t[0])
lam1, v1 = vals[0]
lam2, v2 = next((q, v) for q, v in vals if np.linalg.matrix_rank(np.array([v1, v])) == 2)
G = [[Q(*[(e[0], e[1]), (e[2], e[3])]) for e in [tuple(int(i == k) for i in range(4))]][0] for k in range(4)]
print(f"successive minima of the invariant form: lambda1 = {mp.nstr(lam1, 15)} at {v1}, lambda2 = {mp.nstr(lam2, 15)} at {v2}")
print(f"{'candidate':<22}{'alpha^-1':>22}   {'distance from CODATA 2022':>26}")
for N in (Fraction(1, 25), Fraction(1), Fraction(25)):
    for name, lam in (("1/lambda1", lam1), ("1/lambda2", lam2)):
        a = mpf(N.numerator) / N.denominator / lam
        print(f"{'N = ' + str(N) + ', ' + name:<22}{mp.nstr(a, 15):>22}   {mp.nstr((a - A_OBS) / SIG, 4):>20} sigma")

# ---- O2: precision limit for the family G
lg1, lg2, lpi, lr5 = (float(log(gamma(mpf(1) / 5))), float(log(gamma(mpf(2) / 5))), float(log(pi)), float(log(sqrt(5))))
coefs = sorted({Fraction(p, q) for p in range(1, 11) for q in range(1, 11)})
lc = np.array([np.log(c.numerator / c.denominator) for c in coefs])
e6 = np.arange(-6, 7)
A, B, C, E = np.meshgrid(e6, e6, e6, np.array([0, 1]), indexing="ij")
base = (A * lpi + B * lg1 + C * lg2 + E * lr5).ravel()
allv = (base[:, None] + lc[None, :]).ravel()
target = float(log(A_OBS))
size = allv.size
w_sig, w_law1, w_wide = float(SIG / A_OBS), 1.236e-7, 0.01
n_sig = int(np.sum(np.abs(allv - target) <= w_sig))
n_law1 = int(np.sum(np.abs(allv - target) <= w_law1))
n_wide = int(np.sum(np.abs(allv - target) <= w_wide))
dens = n_wide / (2 * w_wide)                                   # members per unit of log near 137
print(f"O2  family size {size:,}; within +-1 sigma (0.15 ppb): {n_sig}; within +-0.124 ppm: {n_law1}")
print(f"    density near 137: {dens:,.0f} per unit log -> expected by chance: {dens * 2 * w_sig:.2e} within 1 sigma,"
      f" {dens * 2 * w_law1:.2f} within 0.124 ppm")

# ---- O3: the alpha^2/pi candidate against individual measurements
L = pi * gamma(mpf(1) / 5) ** 3 / gamma(mpf(2) / 5)
x = L
for _ in range(60):
    x = L + 1 / (x ** 2 * pi)
print(f"O3  alpha^-1 = L + alpha^2/pi = {mp.nstr(x, 13)}")
for name, val, err in (("CODATA 2022", "137.035999177", "0.000000021"), ("Rb 2020", "137.035999206", "0.000000011"),
                       ("Cs 2018", "137.035999046", "0.000000027")):
    print(f"    vs {name:<12} {val}({err[-2:]}): {mp.nstr((x - mpf(val)) / mpf(err), 3)} sigma")
