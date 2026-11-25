"""Evolutionary search, generation 4 (G4-1, G4-2, G4-3, E2), as pre-registered in
EVOLUTION_GEN4_PREREG_2026-11-25.md (commit 9be1008).
python3 -I evolution_gen4.py   (mpmath; G4-2 uses the exact arithmetic of exact_forms.py; exits with status 1 if any
pre-registered check fails)
"""
import importlib.util
import itertools
import os
import random
from fractions import Fraction as Fr

from mpmath import mp, mpf, gamma, pi, sin, quad, nstr, exp, fabs

mp.dps = 50


def sigma(term):
    """sigma(beta pi^s prod Gamma(a)^n_a) = s + sum n_a a (mod 1); term = (list of (a, n_a), s), a and s Fractions.
    Algebraic factors beta do not enter."""
    gammas, s = term
    return (s + sum(n * a for a, n in gammas)) % 1


def value(term, alg=1):
    gammas, s = term
    v = mpf(alg) * pi ** (mpf(s.numerator) / s.denominator)
    for a, n in gammas:
        v *= gamma(mpf(a.numerator) / a.denominator) ** n
    return v


def relation_ok(lhs, rhs, alg, tol=mpf(10) ** -40):
    """For a relation LHS = alg * RHS: (holds numerically, preserves sigma)."""
    l, r = value(lhs), value(rhs, alg)
    return abs(l - r) <= tol * abs(l), sigma(lhs) == sigma(rhs)


FIFTHS = {1: (1, 0, 0), 2: (0, 1, 0), 3: (0, -1, 1), 4: (-1, 0, 1)}    # Gamma(j/5) as (e1, e2, pi) modulo Qbar^x


def gamma_content(x):
    """Gamma(x) for x in (1/5)Z, modulo Qbar^x: content (e1, e2, pi-exponent) on (Gamma(1/5), Gamma(2/5), pi);
    'pole' at non-positive integers, None if x is not in (1/5)Z."""
    if x.denominator == 1:
        return "pole" if x <= 0 else (0, 0, 0)
    j = (x - (x.numerator // x.denominator)) * 5
    return FIFTHS[int(j)] if j.denominator == 1 else None


def g_content(a, b, d):
    """Content of the Chetyrkin-Tkachov function G(a,b;d); 'divergent' or 'zero' at poles of the Gammas."""
    num = [a + b - d / 2, d / 2 - a, d / 2 - b]
    den = [a, b, d - a - b]
    cn, cd = [gamma_content(x) for x in num], [gamma_content(x) for x in den]
    if "pole" in cn:
        return "divergent"
    if "pole" in cd:
        return "zero"
    if None in cn + cd:
        return None
    return tuple(sum(c[i] for c in cn) - sum(c[i] for c in cd) for i in range(3))


def verdict(failures):
    if failures:
        print("FAILED:", "; ".join(failures))
        raise SystemExit(1)
    print("all pre-registered checks pass")


fail = []
half = Fr(1, 2)

# G4-1: sigma is invariant under the Lang-Rohrlich relations
random.seed(20261125)
n_ok, n_inst = 0, 0
for _ in range(20000):
    kind = random.choice(("translation", "reflection", "multiplication"))
    q = random.randint(2, 60)
    if kind == "translation":
        x = Fr(random.randint(1, 3 * q), q)
        rel = (([(x + 1, 1)], Fr(0)), ([(x, 1)], Fr(0)), mpf(x.numerator) / x.denominator)
    elif kind == "reflection":
        x = Fr(random.randint(1, q - 1), q)
        rel = (([(x, 1), (1 - x, 1)], Fr(0)), ([], Fr(1)), 1 / sin(pi * x.numerator / x.denominator))
    else:
        m = random.randint(2, 12)
        x = Fr(random.randint(1, 2 * q), q)
        if (m * x).denominator == 1 and m * x <= 0:
            continue
        alg = mpf(2) ** (mpf(m - 1) / 2) * mpf(m) ** (half - m * mpf(x.numerator) / x.denominator)
        rel = (([(x + Fr(j, m), 1) for j in range(m)], Fr(0)), ([(m * x, 1)], Fr(m - 1, 2)), alg)
    num_ok, sig_ok = relation_ok(*rel)
    n_inst += 1
    n_ok += num_ok and sig_ok
print(f"G4-1  relation instances holding numerically (40 digits) with sigma preserved: {n_ok} of {n_inst}")
fail += [] if n_ok == n_inst else [f"{n_inst - n_ok} relation instances fail"]
dup = relation_ok(([(Fr(1, 10), 1), (Fr(6, 10), 1)], Fr(0)), ([(Fr(1, 5), 1)], half), mpf(2) ** (1 - mpf(2) / 10))
print(f"      duplication Gamma(1/10)Gamma(3/5) = 2^(4/5) sqrt(pi) Gamma(1/5): holds {dup[0]}, sigma preserved {dup[1]};"
      f" sigma(Gamma(1/10)Gamma(3/5)/sqrt(pi)) = {sigma(([(Fr(1, 10), 1), (Fr(3, 5), 1)], -half))}")
fail += [] if all(dup) and sigma(([(Fr(1, 10), 1), (Fr(3, 5), 1)], -half)) == Fr(1, 5) else ["duplication check"]
# Fermat periods of degree N: Int_0^1 t^(a-1) (1-t^N)^(b/N-1) dt = B(a/N, b/N)/N (u = t^N), checked by quadrature
# after u = v^(1/al) on [0, 1/2] and 1 - u = w^(1/be) on [1/2, 1], which remove the endpoint singularities; sigma(B) = 0


def beta_by_quadrature(al, be):
    h = mpf(1) / 2
    left = quad(lambda v: (1 - v ** (1 / al)) ** (be - 1), [0, h ** al]) / al
    right = quad(lambda w: (1 - w ** (1 / be)) ** (al - 1), [0, h ** be]) / be
    return left + right


fermat_bad = 0
for _ in range(60):
    N = random.randint(3, 12)
    a, b = random.randint(1, N - 1), random.randint(1, N - 1)
    integral = beta_by_quadrature(mpf(a) / N, mpf(b) / N) / N
    term = ([(Fr(a, N), 1), (Fr(b, N), 1), (Fr(a + b, N), -1)], Fr(0))
    fermat_bad += abs(integral - value(term) / N) > mpf(10) ** -40 * abs(integral) or sigma(term) != 0
print(f"      Fermat periods (degree 3-12) checked by quadrature, sigma = 0: {60 - fermat_bad} of 60")
fail += [] if fermat_bad == 0 else [f"{fermat_bad} Fermat period checks"]
laws = {
    "Law 1, pi Gamma(1/5)^3/Gamma(2/5)": ([(Fr(1, 5), 3), (Fr(2, 5), -1)], Fr(1)),
    "sin^2 theta_W, 25/(pi^2 Gamma(2/5)^3)": ([(Fr(2, 5), -3)], Fr(-2)),
    "lambda_H, Gamma(1/5) Gamma(2/5)/(25 pi)": ([(Fr(1, 5), 1), (Fr(2, 5), 1)], Fr(-1)),
    "v_0 factor Gamma(1/5)": ([(Fr(1, 5), 1)], Fr(0)),
    "V_cb factor Gamma(2/5)/Gamma(1/5)": ([(Fr(2, 5), 1), (Fr(1, 5), -1)], Fr(0)),
    "N_Y, 3 sqrt5 Gamma(1/5)": ([(Fr(1, 5), 1)], Fr(0)),
    "kappa^2 (M5)": ([(Fr(3, 5), 3), (Fr(1, 5), 1), (Fr(2, 5), -3), (Fr(4, 5), -1)], Fr(0)),
    "g_psipsibar(0) (M9)": ([(Fr(2, 5), 5), (Fr(3, 5), -5), (Fr(1, 5), -5), (Fr(4, 5), 5)], Fr(0)),
    "P(omega_Y) (T16)": ([(Fr(1, 5), 3), (Fr(3, 5), 1), (Fr(4, 5), 1)], Fr(0)),
}
expected = {"kappa^2 (M5)": 0, "g_psipsibar(0) (M9)": 0, "P(omega_Y) (T16)": 0}
for name, term in laws.items():
    print(f"E2    sigma-screen: {name}: sigma = {sigma(term)}" + ("  (period class)" if sigma(term) == 0 else "  (not a period)"))
fail += [] if sigma(laws["Law 1, pi Gamma(1/5)^3/Gamma(2/5)"]) == Fr(1, 5) else ["sigma(Law 1) != 1/5"]
fail += [f"{n}: sigma {sigma(t)}" for n, t in laws.items() if (sigma(t) == 0) != (n in expected)]

# G4-2: integral thimble lattice of W_4 = x1^5 + ... + x4^5, exact arithmetic in Q(zeta_20)
spec = importlib.util.spec_from_file_location(
    "exact_forms", os.path.join(os.path.dirname(os.path.abspath(__file__)), "exact_forms.py"))
xf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xf)
F = xf.F
s1 = (F.x(2) - F.x(18)) / (F.x(5) * 2)                   # sin(pi/5)
s2 = (F.x(4) - F.x(16)) / (F.x(5) * 2)                   # sin(2 pi/5)
zeta = F.x(4)
T = s2 * 625 / (s1 * s1 * s1 * s1 * 16)                  # Law 1 / (C |1 - zeta|^4)


def charpoly(y):
    """Characteristic polynomial of y over Q (product over the Galois conjugates), as Fractions, constant term first."""
    coeffs = [F.const(1)]
    for k in xf.UNITS:
        c = y.galois(k)
        new = [F.const(0)] * (len(coeffs) + 1)
        for i, a in enumerate(coeffs):
            new[i + 1] = new[i + 1] + a
            new[i] = new[i] - a * c
        coeffs = new
    assert all(not any(a.c[1:]) for a in coeffs), "characteristic polynomial is not rational"
    return [a.c[0] for a in coeffs]


def is_integral(y):
    return all(c.denominator == 1 for c in charpoly(y))


phi = -(zeta * zeta) - zeta * zeta * zeta                                   # golden ratio = -(zeta^2 + zeta^3)
m_star = phi * phi * (1 - zeta * zeta) * 125
norm_m = m_star * m_star.conj()
T2 = T * T
checks42 = {
    "|1 - zeta|^2 = 4 sin^2(pi/5)": (1 - zeta) * (1 - zeta).conj() == s1 * s1 * 4,
    "T^2 is not an algebraic integer": not is_integral(T2),
    "(2T)^2 is an algebraic integer": is_integral(T2 * 4),
    "|m*|^2 = (2T)^2 exactly": norm_m == T2 * 4,
    "m* lies in Z[zeta_5]": all(c.denominator == 1 for c in m_star.c),
    "T^2/n^2 not integral for n = 1..12": all(not is_integral(T2 * Fr(1, n * n)) for n in range(1, 13)),
}
print("G4-2  T^2 =", " ".join(f"{c}" for c in charpoly(T2)[:2]), "...  characteristic polynomial of T^2, first coefficients")
for name, ok in checks42.items():
    print(f"      {name}: {ok}")
    fail += [] if ok else [f"G4-2: {name}"]
L1 = pi * gamma(mpf(1) / 5) ** 3 / gamma(mpf(2) / 5)
C = gamma(mpf(1) / 5) ** 3 * gamma(mpf(3) / 5) / 625
z = exp(2j * pi / 5)
m_num = 125 * ((1 + mpf(5) ** 0.5) / 2) ** 2 * (1 - z ** 2)
Zstar = C * fabs(1 - z) ** 4 * fabs(m_num)
print(f"      |Z(gamma*)| = {nstr(Zstar, 20)};  2 Law 1 = {nstr(2 * L1, 20)};  difference {nstr(Zstar - 2 * L1, 3)}")
fail += [] if fabs(Zstar - 2 * L1) < mpf(10) ** -40 else ["G4-2: |Z(gamma*)| != 2 Law 1"]

# G4-3: nested massless insertions I_L(d) = prod_j G(1, j - (j-1) d/2; d), d = 4 - 2k/5
law1_content = (3, -1)
matches, table = [], {}
for k in range(1, 10):
    d = 4 - Fr(2 * k, 5)
    total, status = (0, 0, 0), "finite"
    for L in range(1, 7):
        g = g_content(Fr(1), L - (L - 1) * d / 2, d)
        if g in ("divergent", "zero", None):
            status = g if g else "outside fifths"
            table[(k, L)] = status
            break
        total = tuple(t + c for t, c in zip(total, g))
        table[(k, L)] = total[:2]
        if total[:2] == law1_content:
            matches.append((str(d), L))
print(f"G4-3  nested insertions in d = 4 - 2k/5 (k = 1..9, L <= 6) with Law 1's Gamma-content (3, -1): {matches}")
for k in range(1, 10):
    print(f"      d = {str(4 - Fr(2 * k, 5)):>5}: " + ", ".join(f"L{L} {table[(k, L)]}" for L in range(1, 7) if (k, L) in table))
sig_ok = all(Fr(L * k, 5) % 1 == (-L * (4 - Fr(2 * k, 5)) / 2) % 1 for k in range(1, 10) for L in range(1, 7))
fail += [] if sig_ok else ["G4-3: sigma(I_L) != L k/5"]
verdict(fail)
