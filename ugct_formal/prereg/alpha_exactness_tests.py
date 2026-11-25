"""Law 1 exactness tests A-E, exactly as pre-registered in ALPHA_EXACTNESS_PREREG_2026-11-24.md
(GitNexus commit 3a0560b, 2026-11-24T22:59:16-05:00; this file is in the same folder).  python3 -I alpha_exactness_tests.py

Corrections are evaluated with alpha_L = 1/L, the geometric value, so no measured alpha enters a
prediction (G2); the measured value is used only in the comparison.
"""
from fractions import Fraction
from math import log as flog
from mpmath import mp, mpf, gamma, pi, quad, log, sqrt

mp.dps = 40
L = pi * gamma(mpf(1) / 5) ** 3 / gamma(mpf(2) / 5)
A_OBS, SIG = mpf("137.035999177"), mpf("0.000000021")      # CODATA 2022
d_obs = A_OBS - L
aL = 1 / L
show = lambda d: f"{mp.nstr(d, 6):>12}   {mp.nstr((d - d_obs) / SIG, 4):>10} sigma"
print(f"L = {mp.nstr(L, 15)};  delta_obs = {mp.nstr(d_obs, 6)} +- {mp.nstr(SIG, 2)}")
print(f"{'reading':<58}{'delta':>12}   {'delta - delta_obs':>16}")

# A: Law 1 is alpha(0).
print(f"{'A  alpha(0) itself':<58}{show(mpf(0))}")

# B: MS-bar coupling at mu = m_e, electron-only theory, two loops: alpha(0) = [1 - 15 (a/4pi)^2] ahat(m_e).
dB = 15 * aL / (16 * pi ** 2)
print(f"{'B  MS-bar alpha at mu = m_e (two loops)':<58}{show(dB)}")

# C: one-loop on-shell running coupling at fixed spacelike Q (leptons e, mu, tau).
m_e, m_mu, m_tau = mpf("0.51099895000e-3"), mpf("0.1056583755"), mpf("1.77686")   # GeV
M_PL = mpf("1.22091e19")                                                               # GeV, node I1


def dC(Q):
    return sum(2 / pi * quad(lambda x: x * (1 - x) * log(1 + x * (1 - x) * Q ** 2 / m ** 2), [0, mp.mpf(1) / 2, 1])
               for m in (m_e, m_mu, m_tau))


for name, Q in [("Q = alpha m_e (Bohr momentum)", aL * m_e), ("Q = m_e", m_e), ("Q = m_mu", m_mu),
                ("Q = M_Pl (leptons only; the '19 decades' argument)", M_PL)]:
    print(f"{'C  ' + name:<58}{show(dC(Q))}")

# D: structural.  L/pi = Gamma(1/5)^3 Gamma(2/5)^-1.  Rohrlich (K1): pi^k prod Gamma(j/5)^m_j algebraic only if
# m_1 = m_4 and m_2 = m_3.  Here (m_1, m_2, m_3, m_4) = (3, -1, 0, 0), grade 3*1 - 1*2 = 1.
m = (3, -1, 0, 0)
print(f"D  L/pi exponents {m}: m1 = m4? {m[0] == m[3]}; m2 = m3? {m[1] == m[2]}; grade {(1*m[0] + 2*m[1] + 3*m[2] + 4*m[3]) % 5}"
      " -> not algebraic if K1 holds (Lean T9), so Law 1 is not 4 pi x an algebraic number")

# E: scan of (p/q) alpha^k pi^m.
coefs = sorted({Fraction(p, q) for p in range(1, 11) for q in range(1, 11)})
forms = [(c, k, mm, mpf(c.numerator) / c.denominator * aL ** k * pi ** mm)
         for c in coefs for k in (1, 2, 3) for mm in range(-3, 4)]
hits = [(c, k, mm, v) for c, k, mm, v in forms if abs(v - d_obs) <= SIG]
print(f"E  family size {len(forms)}; terms within 1 sigma: {len(hits)}")
for c, k, mm, v in hits:
    print(f"     ({c}) alpha^{k} pi^{mm} = {mp.nstr(v, 8)}   {mp.nstr((v - d_obs) / SIG, 3)} sigma")
r = float(SIG / d_obs)                                  # relative window
lo, hi = float(d_obs) / 2, float(d_obs) * 2
ivs = sorted((max(flog(float(v) / (1 + r)), flog(lo)), min(flog(float(v) / (1 - r)), flog(hi)))
             for *_, v in forms if lo / (1 + r) < float(v) < hi / (1 - r))
covered, cur = 0.0, None
for a, b in ivs:
    if cur is None or a > cur[1]:
        if cur:
            covered += cur[1] - cur[0]
        cur = [a, b]
    else:
        cur[1] = max(cur[1], b)
if cur:
    covered += cur[1] - cur[0]
print(f"   chance that a random target in [delta_obs/2, 2 delta_obs] has >= 1 hit: {covered / flog(4):.3f}"
      f" ({len(ivs)} family values in that range)")

# The alpha^2/pi reading solved self-consistently: alpha^-1 = L + alpha^2/pi.
x = L
for _ in range(50):
    x = L + 1 / (x ** 2 * pi)
print(f"   alpha^-1 = L + alpha^2/pi solved: {mp.nstr(x, 13)}  vs CODATA 2022 {A_OBS} -> {mp.nstr((x - A_OBS) / SIG, 3)} sigma;"
      f"  equivalent scale sqrt(15) alpha m_e = {mp.nstr(sqrt(15) * aL * m_e * 1e6, 4)} keV")
