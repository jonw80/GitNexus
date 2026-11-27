"""Dictionary of numbers that X_5 determines, for the Law 1 accuracy scans (X5_ACCURACY_PREREG_2026-11-25.md).

Each entry is a number fixed by the Fermat quintic X_5, its Gepner / Landau-Ginzburg point, its mirror family,
or its arithmetic, with its source. Values are computed to 60 digits.

Every entry that can be recomputed from X_5's defining data is recomputed here:
- the Chern numbers;
- the Gopakumar-Vafa numbers, via the Picard-Fuchs periods and the mirror map, in exact rational arithmetic;
- the character count and the Galois blocks;
- the conifold newform, identified by counting points over F_p;
- the L-values, checked with PARI (functional equations, closed forms);
- the Law 1 identities.

The run exits with status 1 if any check fails. Two entries, L (Law 1) and N_Y (postulate P8), are flagged:
they are UGCT's own formulas, not consequences of X_5.

Run: python3 -I x5_dictionary.py   (needs mpmath and cypari2)
"""
import sys
from fractions import Fraction as Fr
from itertools import combinations, product
from math import factorial

import numpy as np
from mpmath import mp, mpf, gamma, pi, sqrt, sin, cot, tan, zeta, log, nstr

DPS = 60
mp.dps = DPS


# ---------------------------------------------------------------- exact checks from X_5's defining data

def chern_numbers():
    """c(X) = (1+H)^5/(1+5H) truncated at H^3, with H^3 = 5. Returns (c2.H, chi)."""
    num = [Fr(1), Fr(5), Fr(10), Fr(10)]                        # (1+H)^5 up to H^3
    den = [Fr((-5) ** k) for k in range(4)]                     # 1/(1+5H)
    c = [sum(num[i] * den[k - i] for i in range(k + 1)) for k in range(4)]
    assert c[1] == 0, "c1 must vanish"
    return c[2] * 5, c[3] * 5


def h21_from_monomials():
    """Quintic monomials in 5 variables minus dim GL(5): C(9,4) - 25."""
    return factorial(9) // (factorial(4) * factorial(5)) - 25


def characters():
    """Characters a in {1..4}^5 with sum = 0 mod 5 (the eigenlines of H^3(X_5)), and their Galois orbits."""
    chars = [a for a in product(range(1, 5), repeat=5) if sum(a) % 5 == 0]
    orbits = {min(tuple((t * x) % 5 for x in a) for t in range(1, 5)) for a in chars}
    return len(chars), len(orbits)


def _mul(a, b, n):
    return [sum(a[i] * b[k - i] for i in range(k + 1)) for k in range(n)]


def _inv(a, n):
    out = [Fr(1) / a[0]] + [Fr(0)] * (n - 1)
    for k in range(1, n):
        out[k] = -sum(a[i] * out[k - i] for i in range(1, k + 1)) / a[0]
    return out


def _exp(a, n):
    """exp of a series with a[0] = 0."""
    assert a[0] == 0
    out, term = [Fr(1)] + [Fr(0)] * (n - 1), [Fr(1)] + [Fr(0)] * (n - 1)
    for k in range(1, n):
        term = [x / k for x in _mul(term, a, n)]
        out = [x + y for x, y in zip(out, term)]
    return out


def _compose(g, z, n):
    """g(z(q)) for a series z with z[0] = 0."""
    out, power = [Fr(0)] * n, [Fr(1)] + [Fr(0)] * (n - 1)
    for k in range(n):
        out = [x + g[k] * y for x, y in zip(out, power)]
        power = _mul(power, z, n)
    return out


def gopakumar_vafa(n=4):
    """n_1 .. n_{n-1} of the quintic from its Picard-Fuchs periods, in exact rational arithmetic.

    w0 = sum (5k)!/(k!)^5 z^k; w1 = w0 log z + sum (5k)!/(k!)^5 5(H_5k - H_k) z^k; q = z exp(w1~/w0);
    Y_ttt = 5 / ((1 - 5^5 z) w0^2 (dlog q/dlog z)^3) = 5 + sum_d n_d d^3 q^d/(1 - q^d).
    """
    a = [Fr(factorial(5 * k), factorial(k) ** 5) for k in range(n)]
    harm = lambda m: sum(Fr(1, j) for j in range(1, m + 1))
    b = [a[k] * 5 * (harm(5 * k) - harm(k)) for k in range(n)]
    ratio = _mul(b, _inv(a, n), n)                              # w1~/w0, ratio[0] = 0
    g = _exp(ratio, n)                                          # q = z g(z)
    dlog = [Fr(1)] + [k * ratio[k] for k in range(1, n)]        # dlog q/dlog z
    y_z = _inv(_mul(_mul([Fr(1), Fr(-3125)] + [Fr(0)] * (n - 2), _mul(a, a, n), n),
                    _mul(dlog, _mul(dlog, dlog, n), n), n), n)
    y_z = [5 * x for x in y_z]
    # invert q = z g(z): z = q h(q), by fixed-point iteration (z_0 = q)
    zq = [Fr(0), Fr(1)] + [Fr(0)] * (n - 2)
    for _ in range(n):
        zq = [Fr(0)] + _inv(_compose(g, zq, n), n)[: n - 1]
    y_q = _compose(y_z, zq, n)
    assert y_q[0] == 5, "Y_ttt must start at the degree 5"
    nd = {}
    for d in range(1, n):
        c = y_q[d] - sum(nd[e] * e ** 3 for e in nd if d % e == 0)
        assert c % (d ** 3) == 0
        nd[d] = c // d ** 3
    return [int(nd[d]) for d in range(1, n)]


def fit_forms(counts, forms):
    """Forms f with #X_1(F_p) = 1 + p + p^2 + p^3 + e p - a_p(f) for one integer e at every counted prime.

    Only the Z5^3-invariant part of H^3 contributes at the primes p != 1 mod 5. Returns [(a_2, e)].
    """
    fits = []
    for c in forms:
        e = {Fr(counts[p] - (1 + p + p * p + p ** 3) + c[p], p) for p in counts}
        if len(e) == 1 and next(iter(e)).denominator == 1:
            fits.append((c[2], int(next(iter(e)))))
    return fits


def dwork_point_count(p, psi=1):
    """# of points of x1^5 + .. + x5^5 - 5 psi x1..x5 = 0 in P^4(F_p)."""
    x = np.arange(p, dtype=np.int64)
    x5 = (x ** 5) % p
    total = 0
    for a, b in product(range(p), repeat=2):
        s = (x5[a] + x5[b] + x5[:, None, None] + x5[None, :, None] + x5[None, None, :]) % p
        pr = (5 * psi * a * b * x[:, None, None] * x[None, :, None] * x[None, None, :]) % p
        total += int(np.count_nonzero((s - pr) % p == 0))
    return (total - 1) // (p - 1)


# ---------------------------------------------------------------- PARI quantities

def pari_values():
    import cypari2
    pari = cypari2.Pari()
    pari.allocatemem(10 ** 9)
    pari.set_real_precision(DPS + 20)
    conv = lambda z: mpf(str(z).replace(" E", "e"))
    out = {}
    # weight-4 newforms of level 25 with rational coefficients
    pari("mf = mfinit([25, 4], 0); B = mfeigenbasis(mf)")
    nb = int(pari("#B"))
    forms = []
    for j in range(1, nb + 1):
        coefs = [int(c) for c in pari(f"mfcoefs(B[{j}], 30)")]
        forms.append(coefs)
    out["forms"] = forms
    j = 1 + next(i for i, c in enumerate(forms) if c[2] == 1)
    pari(f"Lf = lfunmf(mf, B[{j}])")
    out["f_feq_bits"] = int(pari("lfuncheckfeq(Lf)"))
    out["f_root"] = int(pari("lfunrootres(Lf)[3]"))
    for s in (1, 2, 3):
        out[f"L(f,{s})"] = conv(pari(f"lfun(Lf, {s})"))
    # genus-2 curve y^2 + y = x^5, whose H^1 twisted by one is the Fermat motive M2 (claude/lm2_check.py)
    pari("Lc = lfungenus2([x^5, 1])")
    out["c_feq_bits"] = int(pari("lfuncheckfeq(Lc)"))
    out["L(M2,2)"] = conv(pari("lfun(Lc, 1)"))
    # Dedekind zeta of Q(sqrt5) and L(s, (5/.)) at s = 2
    out["zetaK(2)"] = conv(pari("lfun(lfuncreate(x^2 - x - 1), 2)"))
    out["L(2,chi5)"] = conv(pari("lfun(lfuncreate(5), 2)"))
    return out


# ---------------------------------------------------------------- the dictionary

def build():
    """Returns (entries, failures). entries: list of dicts with name, value (mpf), source, flag."""
    fails = []

    def check(ok, what):
        if not ok:
            fails.append(what)

    c2h, chi = chern_numbers()
    check(c2h == 50 and chi == -200, f"Chern numbers {c2h}, {chi}")
    h11, h21 = 1, h21_from_monomials()
    check(h21 == 101 and chi == 2 * (h11 - h21), f"h21 = {h21}")
    b3 = 2 + 2 * h21
    nchar, norb = characters()
    check(nchar == 204 == b3 and norb == 51, f"characters {nchar}, orbits {norb}")
    gv = gopakumar_vafa(4)
    check(gv == [2875, 609250, 317206375], f"GV {gv}")
    f1_k = (3 + h11 - Fr(chi, 12)) / 2
    f1_z = (1 + Fr(c2h, 12)) / 2
    check(f1_k == Fr(31, 3) and f1_z == Fr(31, 12), f"F1 coefficients {f1_k}, {f1_z}")
    aut = 5 ** 4 * factorial(5)

    g1, g2, g3, g4 = (gamma(mpf(k) / 5) for k in range(1, 5))
    phi = (1 + sqrt(5)) / 2
    t72 = tan(2 * pi / 5)
    kappa = sqrt(g3 ** 3 * g1 / (g2 ** 3 * g4))
    gam = lambda x: gamma(x) / gamma(1 - x)
    g_wp = 25 * (gam(mpf(2) / 5) / gam(mpf(1) / 5)) ** 5
    check(nstr(g_wp, 10) == "0.1922564546" and nstr(kappa ** 5, 11) == "1.55531899", "M9 values")
    check(abs(sin(2 * pi / 5) / sin(pi / 5) - phi) < mpf(10) ** (-DPS + 5), "quantum dimension phi")
    L = pi * g1 ** 3 / g2
    NY = 3 * sqrt(5) * g1
    Pw = g1 ** 3 * g3 * g4
    check(abs(NY * Pw / (12 * pi) - L) < mpf(10) ** (-DPS + 5), "Law 1 = N_Y P(omega_Y)/(12 pi)")
    check(abs(g1 * g2 * g3 * g4 - 4 * pi ** 2 / sqrt(5)) < mpf(10) ** (-DPS + 5), "Gamma product")
    xi = 100 * zeta(3) / (2 * pi) ** 3
    check(abs(xi - abs(chi) * zeta(3) / (2 * (2 * pi) ** 3)) < mpf(10) ** (-DPS + 5), "xi")

    pv = pari_values()
    forms = pv["forms"]
    check(len(forms) == 3 and sorted(c[2] for c in forms) == [-1, 1, 4], f"newforms {[c[:4] for c in forms]}")
    # identify the conifold form by point counts at the primes p != 1 mod 5
    counts = {p: dwork_point_count(p) for p in (2, 3, 7, 13, 17)}
    fits = fit_forms(counts, forms)
    check(len(fits) == 1 and fits[0][0] == 1, f"point counts {counts}; fitting forms (a2, e): {fits}")
    check(pv["f_feq_bits"] < -150 and pv["c_feq_bits"] < -150, "functional equations")
    eps = pv["f_root"]
    check(abs(pv["L(f,1)"] - eps * 25 / (2 * pi ** 2) * pv["L(f,3)"]) < mpf(10) ** (-40), "L(f,1) vs L(f,3)")
    lm2 = g1 ** 3 * g2 / (2 * pi * mpf(5) ** (mpf(9) / 4) * sqrt(phi))
    check(abs(pv["L(M2,2)"] - lm2) < mpf(10) ** (-40), "L(M2,2) closed form")
    zk = 2 * pi ** 4 / (75 * sqrt(5))
    l2 = 4 * pi ** 2 / (25 * sqrt(5))
    check(abs(pv["zetaK(2)"] - zk) < mpf(10) ** (-40) and abs(pv["L(2,chi5)"] - l2) < mpf(10) ** (-40),
          "zeta_K(2), L(2,chi_5)")

    E = []

    def add(name, value, source, flag=""):
        E.append({"name": name, "value": mpf(value), "source": source, "flag": flag})

    add("5", 5, "degree H^3")
    add("3", 3, "complex dimension; c-hat of the Gepner model")
    add("50", c2h, "c2.H (computed)")
    add("200", -chi, "|chi| (computed)")
    add("100", -chi // 2, "|chi|/2, net generations")
    add("101", h21, "h^{2,1} (computed)")
    add("204", b3, "b_3 = number of characters (computed)")
    add("25/12", mpf(25) / 12, "c2.H/24")
    add("5/6", mpf(5) / 6, "H^3/6")
    add("25/3", mpf(25) / 3, "|chi|/24")
    add("31/3", mpf(31) / 3, "BCOV F1: coefficient of K, (3 + h11 - chi/12)/2 (computed)")
    add("31/12", mpf(31) / 12, "BCOV F1: exponent of z, (1 + c2.H/12)/2 (computed)")
    add("2875", gv[0], "n_1 (computed from the periods)")
    add("609250", gv[1], "n_2 (computed from the periods)")
    add("317206375", gv[2], "n_3 (computed from the periods)")
    add("3125", 3125, "conifold point z = 5^-5")
    add("75000", aut, "order of Aut(X_5) = 5^4 5!")
    add("51", norb, "Galois blocks of H_3 (computed)")
    add("phi", phi, "golden ratio = quantum dimension of the k = 3 minimal model (checked)")
    add("9/5", mpf(9) / 5, "central charge 3k/(k+2) of the k = 3 minimal model")
    add("sin(pi/5)", sin(pi / 5), "Fermat/Gepner trigonometry")
    add("sin(2pi/5)", sin(2 * pi / 5), "Fermat/Gepner trigonometry")
    add("tan72", t72, "tan 72 deg")
    add("(2/5)tan72", 2 * t72 / 5, "T13 block coupling minimum")
    add("(2/125)tan72", 2 * t72 / 125, "T14 Hodge-norm coupling minimum")
    add("cot(pi/5)/2", cot(pi / 5) / 2, "Im t at the Landau-Ginzburg point (Candelas et al. 1991)")
    add("G(1/5)", g1, "Gamma(1/5)")
    add("G(2/5)", g2, "Gamma(2/5)")
    add("G(3/5)", g3, "Gamma(3/5)")
    add("G(4/5)", g4, "Gamma(4/5)")
    add("G(1/5)^5", g1 ** 5, "holomorphic period of type (1,1,1,1,1), up to algebraic factors")
    add("P(omega_Y)", Pw, "Gamma(1/5)^3 Gamma(3/5) Gamma(4/5) = 5 omega(1,1,1,3,4)")
    add("kappa", kappa, "M5: normalized Yukawa unit (Distler-Greene)")
    add("kappa^5", kappa ** 5, "M9: normalized Yukawa of the Dwork deformation")
    add("g_psipsibar", g_wp, "M9: Weil-Petersson metric at the Fermat point")
    add("L(M2,2)", pv["L(M2,2)"], "L-value of the Fermat motive M2 = H^1(y^2+y=x^5)(-1) (PARI; closed form checked)")
    add("N_Y", NY, "P8 hypercharge normalization", "UGCT postulate")
    add("L", L, "Law 1", "UGCT formula")
    add("xi", xi, "|chi| zeta(3)/(2 (2 pi)^3): alpha'^3 term of the Kaehler potential (Gamma class)")
    add("L(f,1)", pv["L(f,1)"], "conifold newform f in S_4(Gamma_0(25)), a_2 = 1 (identified by point counts)")
    add("L(f,2)", pv["L(f,2)"], "conifold newform, central value")
    add("L(f,3)", pv["L(f,3)"], "conifold newform")
    add("log(phi)", log(phi), "regulator of Q(sqrt5)")
    add("zetaK(2)", pv["zetaK(2)"], "Dedekind zeta of Q(sqrt5) at 2 = 2 pi^4/(75 sqrt5) (checked)")
    add("L(2,chi5)", pv["L(2,chi5)"], "L(2, (5/.)) = 4 pi^2/(25 sqrt5) (checked)")
    add("125", 125, "|disc Q(zeta_5)|")
    add("25", 25, "level of the conifold newform")
    report = {"counts": counts, "fits": fits, "forms": [c[:13] for c in forms], "gv": gv, "root": eps,
              "feq": (pv["f_feq_bits"], pv["c_feq_bits"])}
    return E, fails, report


if __name__ == "__main__":
    entries, failures, rep = build()
    print(f"newforms of S_4(Gamma_0(25)), a_0..a_12: {rep['forms']}")
    print(f"#X_(psi=1)(F_p): {rep['counts']}; forms fitting #X = 1+p+p^2+p^3+e p - a_p (a_2, e): {rep['fits']}")
    print(f"GV from the periods: {rep['gv']}; L(f,s) root number {rep['root']}; feq bits {rep['feq']}")
    print(f"{len(entries)} entries:")
    for e in entries:
        print(f"  {e['name']:>14} = {nstr(e['value'], 25):>32}   {e['source']}{'  [' + e['flag'] + ']' if e['flag'] else ''}")
    if failures:
        print("FAILED:", *failures, sep="\n  ")
        sys.exit(1)
    print("all dictionary checks passed")
