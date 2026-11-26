#!/usr/bin/env python3
"""Independent computation of the Y4 intersection tensor and chi(Y4), in exact rational arithmetic.

This file shares no code with native_pushforward_core.py or run_chow_tensor.sage. It works directly from:
- the theorems of Esole-Jefferson-Kang, arXiv:1703.00905 (ledger M7);
- Aluffi's Chern class formula for blowups along complete intersections;
- the published blowup sequence of the Jefferson-Turner IntersectionNumbers package for the SU(5) (A4) Tate
  tuning: generators[{a,4}], hypersurface[{a,4}], divisors[{a,4}] in IntersectionNumbers.m.

Geometry:
  base       B3 = P(O + K_S) over S = dP8; the GUT divisor is the section R with R|_R = K_S, so R(R - K_S) = 0;
             c1(S) = 3h - e1 - ... - e8, K_S^2 = 1, c2(S) = 11 points.
  ambient    X0 = P(O + L^2 + L^3) over B3 with L = c1(B3) = 2R + 2 c1(S); z, x, y have classes H, H + 2L, H + 3L,
             so H (H + 2L)(H + 3L) = 0.
  blowups    (x, y, s | E1), (y1, E1 | E2), (x1, E2 | E3), (y2, E3 | E4), with center classes
             {H+2L, H+3L, R}, {H+3L-E1, E1}, {H+2L-E1, E2}, {H+3L-E1-E2, E3}.
  Y4         proper transform of the Tate hypersurface, class 3H + 6L - 2E1 - E2 - E3 - E4 (multiplicity 2 along the
             first center: y^2 and a1 x y are the lowest-order terms).
  divisors   zero section Z = H/3 on Y4; Cartan divisors (package order) C1 = E1-E2, C2 = E3-E4, C3 = E4, C4 = E2-E3;
             pullbacks R, h, e1..e8 of base divisors.

Pushforwards:
  blowup     f_* (a E^k) = a for k = 0, and a (-1)^(d-1) (Z_1 ... Z_d) h_(k-d)(Z_1, ..., Z_d) for k >= 1
             (EJK Theorem 1.8 summed in closed form; h_m is the complete homogeneous symmetric polynomial);
  bundle     pi_* H^k = h_(k-2)(0, -2L, -3L) = (-L)^(k-2) (3^(k-1) - 2^(k-1));
  base       int R^3 = K_S^2 = 1, int R^2 a = K_S.a, int R a b = a.b on S, int a b c = 0.

Checks (the script exits 1 if one fails):
  1. the pushforward reproduces int_{Bl_pt P^3} E^3 = 1 and int H^2 = 1 on the P^2 bundle;
  2. the smooth Weierstrass model gives chi = 12 int c1 c2 + 360 int c1^3 (= 3168 for this B3);
  3. Calabi-Yau: c1(X4) - [Y] restricts to zero on Y4 (tested against every triple of basis divisors);
  4. zero section: Z^2 = -c1(B3) Z on Y4;
  5. fibral divisors D0 = R - E1, C1..C4 satisfy D_a D_b h h = -(affine A4 Cartan matrix)_ab int_B3 R h h;
  6. chi(Y4) equals the published SU(5) formula of EJK arXiv:1703.00905 Table 9 (with L = c1) and is divisible by 6;
  7. Todd genus (3 int c2^2 - chi)/720 = 2, and Riemann-Roch integrality D^4 + c2.D^2 = 0 mod 24 for the basis
     divisors, their pairwise sums and 300 random integral combinations (this tests every tensor entry mod 24);
  8. the triple-Cartan sector, pushed to the base as x S^2 + y S L, equals the Intriligator-Morrison-Seiberg
     5d prepotential of SU(5) with n_5 = S(8L - 5S), n_10 = SL, 1 - g = (SL - S^2)/2 in exactly one Coulomb chamber.

Run:  python3 ugct_sage_y4/independent_y4_pushforward.py [output.json]
"""
from __future__ import annotations

import itertools
import json
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

# variables: L, R, h, e1..e8, H, E1..E4
NAMES = ["L", "R", "h"] + [f"e{i}" for i in range(1, 9)] + ["H", "E1", "E2", "E3", "E4"]
IDX = {n: i for i, n in enumerate(NAMES)}
NV = len(NAMES)
BASE_VARS = ["L", "R", "h"] + [f"e{i}" for i in range(1, 9)]


# ---------------------------------------------------------------- polynomials: dict exponent-tuple -> Fraction

def var(name, c=1):
    e = [0] * NV
    e[IDX[name]] = 1
    return {tuple(e): Fraction(c)}


def const(c):
    return {(0,) * NV: Fraction(c)}


def add(*ps):
    out = {}
    for p in ps:
        for m, c in p.items():
            v = out.get(m, 0) + c
            if v:
                out[m] = v
            else:
                out.pop(m, None)
    return out


def scale(p, c):
    c = Fraction(c)
    return {m: v * c for m, v in p.items()} if c else {}


def mul(p, q, maxdeg=None):
    out = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(a + b for a, b in zip(m1, m2))
            if maxdeg is not None and sum(m) > maxdeg:
                continue
            v = out.get(m, 0) + c1 * c2
            if v:
                out[m] = v
            else:
                out.pop(m, None)
    return out


def power(p, k, maxdeg=None):
    out = const(1)
    for _ in range(k):
        out = mul(out, p, maxdeg)
    return out


def lin(**coeffs):
    return add(*[var(n, c) for n, c in coeffs.items()])


def h_complete(zs, m):
    """Complete homogeneous symmetric polynomial h_m of the polynomials zs."""
    if m < 0:
        return {}
    if m == 0:
        return const(1)
    if len(zs) == 1:
        return power(zs[0], m)
    return add(*[mul(power(zs[-1], i), h_complete(zs[:-1], m - i)) for i in range(m + 1)])


def series_inverse_one_plus(x, maxdeg):
    """(1 + x)^-1 truncated at total degree maxdeg; x has no constant term."""
    out, term = const(1), const(1)
    for _ in range(maxdeg):
        term = scale(mul(term, x, maxdeg), -1)
        out = add(out, term)
    return out


# ---------------------------------------------------------------- geometry

C1S = add(var("h", 3), *[var(f"e{i}", -1) for i in range(1, 9)])          # c1(dP8)
L_EXPANDED = add(var("R", 2), scale(C1S, 2))                                 # c1(B3) = 2R + 2 c1(S)
H, Lv = var("H"), var("L")
E = {k: var(f"E{k}") for k in range(1, 5)}
CENTERS = {
    1: [lin(H=1, L=2), lin(H=1, L=3), var("R")],
    2: [lin(H=1, L=3, E1=-1), E[1]],
    3: [lin(H=1, L=2, E1=-1), E[2]],
    4: [lin(H=1, L=3, E1=-1, E2=-1), E[3]],
}
HYPERSURFACE = lin(H=3, L=6, E1=-2, E2=-1, E3=-1, E4=-1)
CARTAN = {"C1": lin(E1=1, E2=-1), "C2": lin(E3=1, E4=-1), "C3": lin(E4=1), "C4": lin(E2=1, E3=-1)}
AFFINE = lin(R=1, E1=-1)                                                      # D0 = S - E1
DIV = {"R": var("R"), "H": var("h"), **{f"E{i}": var(f"e{i}") for i in range(1, 9)},
       "Z": scale(H, Fraction(1, 3)), **CARTAN}
BASIS = ["R", "H"] + [f"E{i}" for i in range(1, 9)] + ["Z", "C1", "C2", "C3", "C4"]
ORD = {n: i for i, n in enumerate(BASIS)}


@lru_cache(maxsize=None)
def push_blowup_monomial(stage, mono):
    k = mono[IDX[f"E{stage}"]]
    rest = list(mono)
    rest[IDX[f"E{stage}"]] = 0
    coef = {tuple(rest): Fraction(1)}
    if k == 0:
        return coef
    zs = CENTERS[stage]
    d = len(zs)
    prod = const(1)
    for z in zs:
        prod = mul(prod, z)
    return mul(coef, scale(mul(prod, h_complete(zs, k - d)), (-1) ** (d - 1)))


def push_blowup(stage, p):
    return add(*[scale(push_blowup_monomial(stage, m), c) for m, c in p.items()])


@lru_cache(maxsize=None)
def push_bundle_monomial(mono):
    k = mono[IDX["H"]]
    if k < 2:
        return {}
    rest = list(mono)
    rest[IDX["H"]] = 0
    return scale(mul({tuple(rest): Fraction(1)}, power(scale(Lv, -1), k - 2)), 3 ** (k - 1) - 2 ** (k - 1))


def push_bundle(p):
    return add(*[scale(push_bundle_monomial(m), c) for m, c in p.items()])


def dp8_pair(a, b):
    if a == "h" and b == "h":
        return 1
    if a == b:
        return -1
    return 0


@lru_cache(maxsize=None)
def integrate_base_monomial(mono):
    """int_B3 of a degree-3 monomial in L, R, h, e_i (L expanded as 2R + 2 c1(S))."""
    if any(mono[IDX[n]] for n in NAMES if n not in BASE_VARS):
        raise ValueError("ambient variable left after pushforward")
    if sum(mono) != 3:
        return Fraction(0)
    nl = mono[IDX["L"]]
    rest = list(mono)
    rest[IDX["L"]] = 0
    p = mul({tuple(rest): Fraction(1)}, power(L_EXPANDED, nl))
    total = Fraction(0)
    for m, c in p.items():
        r = m[IDX["R"]]
        others = [n for n in ["h"] + [f"e{i}" for i in range(1, 9)] for _ in range(m[IDX[n]])]
        if r == 3:
            val = 1
        elif r == 2:                                   # K_S . a = -c1(S) . a
            a = others[0]
            val = -3 if a == "h" else -1
        elif r == 1:
            val = dp8_pair(*others)
        else:
            val = 0
        total += c * val
    return total


def integrate_base(p):
    return sum((c * integrate_base_monomial(m) for m, c in p.items()), Fraction(0))


def integrate_ambient(p, stages=(4, 3, 2, 1)):
    for s in stages:
        p = push_blowup(s, p)
    return integrate_base(push_bundle(p))


def on_y(*divs):
    p = HYPERSURFACE
    for d in divs:
        p = mul(p, d)
    return integrate_ambient(p)


def push_to_base(p):
    for s in (4, 3, 2, 1):
        p = push_blowup(s, p)
    return push_bundle(p)


def base_coefficients(p, names):
    """Coefficients of the given base monomials (e.g. ["R,R", "R,L"]) in a pushed-forward class; also returns
    whatever other monomials occur, which must be empty for a class built from S and L only."""
    want = {}
    for n in names:
        e = [0] * NV
        for v in n.split(","):
            e[IDX[v]] += 1
        want[tuple(e)] = n
    coeffs = {n: Fraction(0) for n in names}
    other = {}
    for m, c in p.items():
        if m in want:
            coeffs[want[m]] = c
        else:
            other[m] = c
    return coeffs, other


# ---------------------------------------------------------------- 5d prepotential check of the triple-Cartan sector
#
# For a base divisor alpha, D_a D_b D_c pi^*alpha = int_B pi_*([Y] D_a D_b D_c) . alpha and pi_*([Y] D_a D_b D_c) =
# x_abc S^2 + y_abc S L.  On a Calabi-Yau threefold these are the triple intersection numbers that match the
# Intriligator-Morrison-Seiberg prepotential of 5d SU(5) with g adjoints, n_5 fundamentals and n_10 antisymmetrics:
#   int J^3 = -6 F_IMS,  F_IMS = (1/12)[(1-g) sum_roots |a.phi|^3 - n_5 sum_{w in 5} |w.phi|^3 - n_10 sum_{w in 10} |w.phi|^3],
# with 1-g = (S.L - S^2)/2, n_5 = S.(8L - 5S), n_10 = S.L for the SU(5) Tate model.  Collecting the S^2 and S.L
# parts gives, in the Coulomb chamber of the resolution,
#   x(phi) = A/4 - 5B/2,   y(phi) = -A/4 + 4B + C/2,
# where A, B, C are the three |.|^3 sums.  The check finds the chamber (sign pattern of the 5 and 10 weights) and
# overall orientation in which this holds at every sample point; the polynomials are cubic, so agreement at more
# than 20 generic points in one chamber is an identity there.

A4_CARTAN = [[2, -1, 0, 0], [-1, 2, -1, 0], [0, -1, 2, -1], [0, 0, -1, 2]]
A4_CARTAN_INV = [[Fraction(v, 5) for v in row] for row in [[4, 3, 2, 1], [3, 6, 4, 2], [2, 4, 6, 3], [1, 2, 3, 4]]]
FUND_WEIGHTS = [[Fraction(v, 5) for v in row] for row in
                [[4, 3, 2, 1], [-1, 3, 2, 1], [-1, -2, 2, 1], [-1, -2, -3, 1], [-1, -2, -3, -4]]]


def weight_dot(q, a):
    return sum(qi * ai for qi, ai in zip(q, a))


def prepotential_check(chain, samples=400, seed=20261126):
    """chain: the Cartan divisor names in Dynkin order (from the computed adjacency)."""
    import random
    rng = random.Random(seed)
    x, y = {}, {}
    leftovers = []
    for tri in itertools.combinations_with_replacement(range(4), 3):
        p = mul(mul(mul(HYPERSURFACE, CARTAN[chain[tri[0]]]), CARTAN[chain[tri[1]]]), CARTAN[chain[tri[2]]])
        coeffs, other = base_coefficients(push_to_base(p), ["R,R", "R,L"])
        if other:
            leftovers.append(tri)
        x[tri], y[tri] = coeffs["R,R"], coeffs["R,L"]

    def geometric(phi):
        gx = gy = Fraction(0)
        for tri in x:
            mult = len(set(itertools.permutations(tri)))
            prod = phi[tri[0]] * phi[tri[1]] * phi[tri[2]]
            gx += mult * x[tri] * prod
            gy += mult * y[tri] * prod
        return gx, gy

    tens = [[FUND_WEIGHTS[i][k] + FUND_WEIGHTS[j][k] for k in range(4)] for i in range(5) for j in range(i + 1, 5)]
    roots = [[FUND_WEIGHTS[i][k] - FUND_WEIGHTS[j][k] for k in range(4)] for i in range(5) for j in range(i + 1, 5)]
    chambers = {}
    for _ in range(samples):
        a = [Fraction(rng.randint(1, 60), rng.randint(1, 13)) for _ in range(4)]     # alpha_b . phi > 0
        phi = [sum(A4_CARTAN_INV[i][j] * a[j] for j in range(4)) for i in range(4)]
        w5 = [weight_dot(q, a) for q in FUND_WEIGHTS]
        w10 = [weight_dot(q, a) for q in tens]
        if any(v == 0 for v in w5 + w10):
            continue
        signs = ("".join("+" if v > 0 else "-" for v in w5), "".join("+" if v > 0 else "-" for v in w10))
        big_a = 2 * sum(weight_dot(q, a) ** 3 for q in roots)
        big_b = sum(abs(v) ** 3 for v in w5)
        big_c = sum(abs(v) ** 3 for v in w10)
        gx, gy = geometric(phi)
        ims_x, ims_y = big_a / 4 - 5 * big_b / 2, -big_a / 4 + 4 * big_b + big_c / 2
        st = chambers.setdefault(signs, {"points": 0, "match_plus": 0, "match_minus": 0})
        st["points"] += 1
        st["match_plus"] += (gx, gy) == (ims_x, ims_y)
        st["match_minus"] += (gx, gy) == (-ims_x, -ims_y)
    matched = [(s, st) for s, st in chambers.items()
               if st["points"] > 20 and (st["match_plus"] == st["points"] or st["match_minus"] == st["points"])]
    return {
        "chain": chain,
        "x_coefficients_S2": {",".join(chain[i] for i in t): frac_str(v) for t, v in x.items()},
        "y_coefficients_SL": {",".join(chain[i] for i in t): frac_str(v) for t, v in y.items()},
        "non_S_classes_left": len(leftovers),
        "chambers_sampled": {f"5:{s[0]} 10:{s[1]}": st for s, st in chambers.items()},
        "matched_chambers": [f"5:{s[0]} 10:{s[1]}" for s, _ in matched],
        "orientation": ("J^3 = -6F" if matched and matched[0][1]["match_plus"] else "J^3 = +6F") if matched else None,
        "passed": len(matched) == 1 and not leftovers,
    }


# ---------------------------------------------------------------- Chern classes

def chern_base():
    c_s = add(const(1), C1S, scale(mul(var("h"), var("h")), 11))           # c(S), c2(S) = 11 points = 11 h^2
    rp = add(var("R"), C1S)                                                 # the other section R' = R - K_S
    return mul(mul(c_s, add(const(1), var("R"))), add(const(1), rp))


def chern_x0():
    c = chern_base()
    for shift in (const(0), scale(Lv, 2), scale(Lv, 3)):
        c = mul(c, add(const(1), H, shift), 5)
    return c


def chern_after_blowups(c, upto=4):
    for s in range(1, upto + 1):
        e = E[s]
        c = mul(c, add(const(1), e), 5)
        for z in CENTERS[s]:
            c = mul(c, add(const(1), z, scale(e, -1)), 5)
            c = mul(c, series_inverse_one_plus(z, 5), 5)
    return c


def degree_part(p, d):
    return {m: c for m, c in p.items() if sum(m) == d}


def euler_characteristic(c_ambient, y_class, stages):
    cy = mul(c_ambient, series_inverse_one_plus(y_class, 5), 5)
    return integrate_ambient(mul(y_class, degree_part(cy, 4)), stages)


def chern_y_part(c_ambient, y_class, k):
    """c_k(TY) as an ambient class (to be multiplied by [Y] and integrated)."""
    return degree_part(mul(c_ambient, series_inverse_one_plus(y_class, 5), 5), k)


def quartic_form(tensor, n):
    """D^4 for D = sum n_i B_i, from the symmetric tensor keyed by sorted basis names."""
    total = Fraction(0)
    for quad in itertools.combinations_with_replacement(range(len(BASIS)), 4):
        v = tensor.get(key([BASIS[i] for i in quad]))
        if not v:
            continue
        mult = len(set(itertools.permutations(quad)))
        total += mult * Fraction(v) * n[quad[0]] * n[quad[1]] * n[quad[2]] * n[quad[3]]
    return total


def quadratic_form(pairing, n):
    total = Fraction(0)
    for pair in itertools.combinations_with_replacement(range(len(BASIS)), 2):
        v = pairing.get(key([BASIS[i] for i in pair]))
        if not v:
            continue
        mult = 1 if pair[0] == pair[1] else 2
        total += mult * Fraction(v) * n[pair[0]] * n[pair[1]]
    return total


def riemann_roch_failures(tensor, c2_pairing, trials=300, seed=7):
    """On a Calabi-Yau fourfold chi(O(D)) = (D^4 + c2.D^2)/24 + chi(O_Y), so D^4 + c2.D^2 = 0 mod 24 for every
    integral divisor D.  Tested on the basis divisors, their pairwise sums and random integral combinations."""
    import random
    rng = random.Random(seed)
    vectors = []
    nb = len(BASIS)
    for i in range(nb):
        vectors.append([1 if j == i else 0 for j in range(nb)])
        for k in range(i + 1, nb):
            vectors.append([1 if j in (i, k) else 0 for j in range(nb)])
    vectors += [[rng.randint(-3, 3) for _ in range(nb)] for _ in range(trials)]
    bad = []
    for n in vectors:
        v = quartic_form(tensor, n) + quadratic_form(c2_pairing, n)
        if v.denominator != 1 or v.numerator % 24:
            bad.append({"D": {BASIS[i]: n[i] for i in range(nb) if n[i]}, "D4_plus_c2D2": frac_str(v)})
    return len(vectors), bad


# ---------------------------------------------------------------- run

def key(names):
    return ",".join(sorted(names, key=lambda n: ORD[n]))


def frac_str(q):
    q = Fraction(q)
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def h_numeric(zs, m):
    if m < 0:
        return Fraction(0)
    if m == 0:
        return Fraction(1)
    if len(zs) == 1:
        return Fraction(zs[0]) ** m
    return sum((Fraction(zs[-1]) ** i * h_numeric(zs[:-1], m - i) for i in range(m + 1)), Fraction(0))


def ejk_lagrange_sum(zs, k):
    """EJK Theorem 1.8 as stated: sum_l Z_l^k prod_{m != l} Z_m / (Z_m - Z_l), evaluated at numbers."""
    zs = [Fraction(z) for z in zs]
    total = Fraction(0)
    for l, zl in enumerate(zs):
        term = zl ** k
        for m, zm in enumerate(zs):
            if m != l:
                term *= zm / (zm - zl)
        total += term
    return total


def closed_form_numeric(zs, k):
    if k == 0:
        return Fraction(1)
    prod = Fraction(1)
    for z in zs:
        prod *= Fraction(z)
    return (-1) ** (len(zs) - 1) * prod * h_numeric(zs, k - len(zs))


def sanity_failures():
    failures = []
    for zs in ([2, 5], [3, -7], [2, 5, 11], [-3, 4, 9]):
        for k in range(0, 8):
            if ejk_lagrange_sum(zs, k) != closed_form_numeric(zs, k):
                failures.append(f"closed form != EJK sum for Z={zs}, k={k}")
    expected = {2: const(1), 3: scale(Lv, -5), 4: scale(power(Lv, 2), 19), 5: scale(power(Lv, 3), -65)}
    for k, want in expected.items():
        if push_bundle(power(H, k)) != want:
            failures.append(f"pi_* H^{k}")
    if push_bundle(mul(mul(H, add(H, scale(Lv, 2))), add(H, scale(Lv, 3)))):
        failures.append("projective bundle relation H(H+2L)(H+3L) does not push forward to zero")
    base = {"R,R,R": 1, "R,R,h": -3, "R,R,e1": -1, "R,h,h": 1, "R,e1,e1": -1, "R,h,e1": 0, "h,h,e1": 0}
    for names, want in base.items():
        p = const(1)
        for n in names.split(","):
            p = mul(p, var(n))
        if integrate_base(p) != want:
            failures.append(f"int_B3 {names} != {want}")
    return failures


def main(out_path=None):
    # 1. pushforward and base-integration sanity
    failures = sanity_failures()

    # 2. smooth Weierstrass chi
    c1 = L_EXPANDED
    c2b = degree_part(chern_base(), 2)
    c1c2 = integrate_base(mul(c1, c2b))
    c13 = integrate_base(power(c1, 3))
    chi_smooth = euler_characteristic(chern_x0(), lin(H=3, L=6), stages=())
    if chi_smooth != 12 * c1c2 + 360 * c13:
        failures.append(f"smooth chi {chi_smooth} != 12*{c1c2} + 360*{c13}")

    # resolved SU(5) model
    c_x4 = chern_after_blowups(chern_x0())
    chi = euler_characteristic(c_x4, HYPERSURFACE, stages=(4, 3, 2, 1))

    # 3. Calabi-Yau condition
    c1_x4 = degree_part(c_x4, 1)
    diff = add(c1_x4, scale(HYPERSURFACE, -1))
    cy_bad = []
    for trip in itertools.combinations_with_replacement(BASIS, 3):
        v = on_y(diff, *[DIV[n] for n in trip])
        if v:
            cy_bad.append((key(trip), frac_str(v)))
    if cy_bad:
        failures.append(f"Calabi-Yau condition fails on {len(cy_bad)} triples, e.g. {cy_bad[:3]}")

    # 4. zero section relation Z^2 = -c1(B3) Z
    zs_bad = []
    for pair in itertools.combinations_with_replacement(BASIS, 2):
        v = on_y(add(mul(DIV["Z"], DIV["Z"]), mul(Lv, DIV["Z"])), *[DIV[n] for n in pair])
        if v:
            zs_bad.append((key(pair), frac_str(v)))
    if zs_bad:
        failures.append(f"zero-section relation fails on {len(zs_bad)} pairs, e.g. {zs_bad[:3]}")

    # 5. affine Cartan matrix of the fibral divisors
    fib = {"D0": AFFINE, **CARTAN}
    norm = integrate_base(mul(mul(var("R"), var("h")), var("h")))            # int_B3 S h h = 1
    gram = {a: {b: -on_y(fib[a], fib[b], var("h"), var("h")) / norm for b in fib} for a in fib}
    adjacency = {a: sorted(b for b in fib if b != a and gram[a][b] == -1) for a in fib}
    affine_ok = all(gram[a][a] == 2 for a in fib) and all(len(adjacency[a]) == 2 for a in fib) \
        and all(gram[a][b] in (0, -1) for a in fib for b in fib if a != b)
    if not affine_ok:
        failures.append(f"fibral divisors do not give the affine A4 Cartan matrix: {gram}")

    # full tensor
    tensor = {}
    for quad in itertools.combinations_with_replacement(BASIS, 4):
        v = on_y(*[DIV[n] for n in quad])
        if v:
            tensor[key(quad)] = frac_str(v)
    higher_cartan = {}
    cs = ["C1", "C2", "C3", "C4"]
    for b in ["R", "H"] + [f"E{i}" for i in range(1, 9)]:
        for tri in itertools.combinations_with_replacement(cs, 3):
            k = key([b, *tri])
            higher_cartan[k] = tensor.get(k, "0")
    for quad in itertools.combinations_with_replacement(cs, 4):
        k = key(list(quad))
        higher_cartan[k] = tensor.get(k, "0")

    # 6. published Euler characteristic: EJK arXiv:1703.00905 Table 9, SU(5) row, with L = c1 (Calabi-Yau):
    #    chi = -72 c1 L^2 + 80 c1 L S - 30 c1 S^2 + 12 c2 L + 432 L^3 - 830 L^2 S + 555 L S^2 - 120 S^3
    S_ = var("R")
    def ib(*ps):
        q = const(1)
        for p_ in ps:
            q = mul(q, p_)
        return integrate_base(q)
    chi_ejk = (-72 * ib(c1, c1, c1) + 80 * ib(c1, c1, S_) - 30 * ib(c1, S_, S_) + 12 * ib(c2b, c1)
               + 432 * ib(c1, c1, c1) - 830 * ib(c1, c1, S_) + 555 * ib(c1, S_, S_) - 120 * ib(S_, S_, S_))
    if chi != chi_ejk:
        failures.append(f"chi {chi} differs from the EJK Table 9 SU(5) formula {chi_ejk}")
    if chi % 6:
        failures.append(f"chi {chi} is not divisible by 6")

    # 7. second Chern class, Todd genus and Riemann-Roch integrality of the whole tensor
    c2y = chern_y_part(c_x4, HYPERSURFACE, 2)
    c2_pairing = {}
    for pair in itertools.combinations_with_replacement(BASIS, 2):
        v = on_y(c2y, *[DIV[n] for n in pair])
        if v:
            c2_pairing[key(pair)] = frac_str(v)
    c2_squared = on_y(c2y, c2y)
    todd = (3 * c2_squared - chi) / 720
    if todd != 2:
        failures.append(f"Todd genus (3 c2^2 - c4)/720 = {todd}, expected 2 for a Calabi-Yau fourfold")
    rr_tested, rr_bad = riemann_roch_failures(tensor, c2_pairing)
    if rr_bad:
        failures.append(f"Riemann-Roch integrality fails for {len(rr_bad)} of {rr_tested} divisors, e.g. {rr_bad[:2]}")

    # 8. 5d prepotential (IMS) check of the triple-Cartan sector, in the Dynkin order found in check 5
    chain, prev, cur = [], "D0", adjacency["D0"][0] if adjacency.get("D0") else None
    while cur and cur != "D0" and len(chain) < 5:
        chain.append(cur)
        nxt = [b for b in adjacency[cur] if b != prev]
        prev, cur = cur, (nxt[0] if nxt else None)
    prepot = prepotential_check(chain) if len(chain) == 4 else {"passed": False, "chain": chain}
    if not prepot["passed"]:
        failures.append("triple-Cartan sector does not match the IMS prepotential in exactly one Coulomb chamber")

    result = {
        "schema_version": "UGCT_Y4_INDEPENDENT_EJK_PUSHFORWARD_V1",
        "computed_by": "independent_y4_pushforward.py",
        "status": "INDEPENDENT_TENSOR_COMPUTED" if not failures else "INDEPENDENT_COMPUTATION_CHECKS_FAILED",
        "method": "Esole-Jefferson-Kang pushforward (arXiv:1703.00905) in exact rational arithmetic; no shared code",
        "model": {
            "base": "B3 = P(O + K_S), S = dP8, GUT divisor R with R(R - K_S) = 0",
            "ambient": "P(O + L^2 + L^3), L = c1(B3) = 2R + 2c1(S)",
            "centers": ["H+2L, H+3L, R", "H+3L-E1, E1", "H+2L-E1, E2", "H+3L-E1-E2, E3"],
            "hypersurface": "3H + 6L - 2E1 - E2 - E3 - E4",
            "cartan_divisors": {"C1": "E1-E2", "C2": "E3-E4", "C3": "E4", "C4": "E2-E3"},
            "zero_section": "H/3",
            "source": "IntersectionNumbers.m generators[{a,4}], hypersurface[{a,4}], divisors[{a,4}]",
        },
        "basis": BASIS,
        "total_degree4_monomials": len(list(itertools.combinations_with_replacement(BASIS, 4))),
        "nonzero_count": len(tensor),
        "quadruple_intersections": tensor,
        "higher_cartan_values": higher_cartan,
        "higher_cartan_value_count": len(higher_cartan),
        "chi_Y4": frac_str(chi),
        "d3_tadpole_chi_over_24": frac_str(Fraction(chi) / 24),
        "int_c2_squared": frac_str(c2_squared),
        "c2_pairings": c2_pairing,
        "checks": {
            "smooth_weierstrass_chi": frac_str(chi_smooth), "int_c1c2_B3": frac_str(c1c2), "int_c1cubed_B3": frac_str(c13),
            "chi_from_published_EJK_formula": frac_str(chi_ejk),
            "chi_matches_published_formula": chi == chi_ejk,
            "todd_genus": frac_str(todd),
            "riemann_roch_divisors_tested": rr_tested, "riemann_roch_failures": len(rr_bad),
            "calabi_yau_condition": not cy_bad, "zero_section_relation": not zs_bad,
            "affine_cartan_matrix": {a: {b: frac_str(v) for b, v in row.items()} for a, row in gram.items()},
            "dynkin_adjacency": adjacency,
            "prepotential_triple_cartan": {k: prepot.get(k) for k in
                                           ("passed", "chain", "matched_chambers", "orientation", "non_S_classes_left")},
            "prepotential_coefficients": {k: prepot.get(k) for k in ("x_coefficients_S2", "y_coefficients_SL")},
        },
        "failures": failures,
    }
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "nonzero_count", "higher_cartan_value_count", "chi_Y4",
                                             "d3_tadpole_chi_over_24", "int_c2_squared", "failures")}, indent=2))
    print("checks:", json.dumps({k: v for k, v in result["checks"].items()
                                 if k not in ("affine_cartan_matrix", "prepotential_coefficients")}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
