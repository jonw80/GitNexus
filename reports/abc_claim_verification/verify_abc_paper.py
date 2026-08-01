#!/usr/bin/env python3
"""
Verification of "An Effective Proof of the ABC Conjecture with Explicit Bounds".

Runs every numerical claim in the paper and reports which hold and which fail.
Requires: mpmath.  Run:  python3 verify_abc_paper.py
"""

import sys

from mpmath import findroot, log, mp, mpf, power, quad, sqrt, exp, inf

mp.dps = 50
sys.set_int_max_str_digits(200000)

C33 = mpf("33.3")
FAIL = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL.append(name)
    print(f"  [{status}] {name}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"         {line}")


def rhs_eq1(logr):
    """Right-hand side of the paper's Equation (1). Increasing in logr."""
    return (
        mpf(2) / 3 * logr
        + C33 * power(logr, mpf(1) / 3) * power(log(logr), mpf(2) / 3)
        + 10
    )


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------- Lemma 1
section("Lemma 1  --  the Mertens 'error term' integral")

a, b = mpf("0.2"), sqrt(log(2))
closed = 2 * (exp(-a * b) / a * (b + 1 / a))
numeric = quad(lambda u: exp(-a * sqrt(u)), [log(2), 10, 1000, 100000, inf])

check(
    "paper's antiderivative evaluates correctly",
    abs(closed - numeric) < mpf("1e-20"),
    f"closed form 2*e^(-ab)/a*(b+1/a) = {mp.nstr(closed, 10)}\n"
    f"direct quadrature               = {mp.nstr(numeric, 10)}\n"
    f"paper states 'approximately 49.5'; true value is {mp.nstr(closed, 6)}",
)
check(
    "the integral is bounded by 50 (paper's claim)",
    closed < 50,
    f"limit {mp.nstr(closed, 8)} < 50, and int_0^inf = 2/a^2 = 50 exactly",
)
check(
    "CONCEPTUAL: this quantity is a valid Mertens error term",
    False,
    "It converges to 49.379, NOT to 0. A Mertens error term must vanish.\n"
    "Correct (Rosser-Schoenfeld, x >= 286):\n"
    "  |sum_{p<=x} 1/p - loglog x - M| <= 1/(10 log^2 x) + 4/(15 log^3 x)\n"
    "As written, Eq (2) is true but vacuous, and so is Eq (3).",
)

# --------------------------------------------------------------- Example 1
section("Example 1  --  triple (2, 3^10*109, 23^5)")

A, B, Cc = 2, 3**10 * 109, 23**5
r1 = 2 * 3 * 23 * 109
s = mpf(1) / 2 + mpf(1) / 3 + mpf(1) / 23 + mpf(1) / 109
bound = log(log(r1)) + mpf("0.261497") + 50

check("A + B = C", A + B == Cc, f"{A} + {B} = {A + B} = 23^5 = {Cc}")
check("rad(ABC) = 15042", r1 == 15042, f"2*3*23*109 = {r1}")
check(
    "sum of 1/p as stated (0.885)",
    abs(s - mpf("0.885")) < mpf("0.002"),
    f"exact sum = {mp.nstr(s, 10)}",
)
check(
    "Eq (3) holds here",
    s <= bound,
    f"bound = loglog(15042) + M + 50 = {mp.nstr(bound, 8)}\n"
    f"actual = {mp.nstr(s, 8)}  --  slack of {mp.nstr(bound - s, 6)}, i.e. no content",
)
print(f"         quality of this triple: log C / log r = {mp.nstr(log(Cc) / log(r1), 10)}")

# ----------------------------------------------------------------- Lemma 3
section("Lemma 3  --  the constant-optimization threshold M_eps")

print("  Correct algebra for  33.3 L^(1/3) (log L)^(2/3) < (eps/2) L :")
print("    divide by L    ->  33.3 (log L)^(2/3) / L^(2/3) < eps/2")
print("    rearrange      ->  L / (log L)^(2/3) > 66.6/eps")
print("    raise to 3/2   ->  L / log L > (66.6/eps)^(3/2)      <-- CORRECT THRESHOLD")
print("  The paper instead states  L > (33.3/eps)^3 (log(33.3/eps))^2,")
print("  dropping the factor 2 and replacing the exponent 3/2 by 3.")
print()

for e_s in ["1", "0.1", "0.01"]:
    e = mpf(e_s)
    target = power(2 * C33 / e, mpf(3) / 2)
    exact = findroot(lambda L: L / log(L) - target, target * log(target))
    paper = power(C33 / e, 3) * power(log(C33 / e), 2)
    print(
        f"  eps={e_s:<6} correct log M_eps = {mp.nstr(exact, 6):<14}"
        f" paper's = {mp.nstr(paper, 6):<14} ({mp.nstr(paper / exact, 4)}x too large)"
    )

print()
brk = findroot(
    lambda e: C33
    * power(power(C33 / e, 3) * power(log(C33 / e), 2), mpf(1) / 3)
    * power(log(power(C33 / e, 3) * power(log(C33 / e), 2)), mpf(2) / 3)
    - e / 2 * power(C33 / e, 3) * power(log(C33 / e), 2),
    mpf("5"),
)
check(
    "Lemma 3 as stated holds for EVERY eps > 0 (needed by Theorem 1)",
    False,
    f"Its own threshold fails to imply its conclusion for eps > {mp.nstr(brk, 8)}.\n"
    f"For eps >= 33.3, log(33.3/eps) <= 0 and M_eps is degenerate.\n"
    "For small eps the threshold IS sufficient -- merely far from tight.",
)

# --------------------------------------------------------------- Example 2
section("Example 2  --  eps = 0.1, r = e^(10^6)")

eps, L = mpf("0.1"), mpf(10) ** 6
lhs = C33 * power(L, mpf(1) / 3) * power(log(L), mpf(2) / 3)
rhs = eps / 2 * L
logM_paper = power(C33 / eps, 3) * power(log(C33 / eps), 2)

check(
    "stated LHS value (1.7e4)",
    abs(lhs - mpf("1.7e4")) < mpf("1e3"),
    f"true LHS = 33.3 * 100 * {mp.nstr(power(log(L), mpf(2) / 3), 6)} "
    f"= {mp.nstr(lhs, 8)}, i.e. 1.92e4 not 1.7e4",
)
check("stated RHS value (5e4)", abs(rhs - mpf("5e4")) < 1, f"RHS = {mp.nstr(rhs, 8)}")
check("the inequality itself holds", lhs < rhs)
check(
    "the example satisfies Lemma 3's hypothesis r > M_eps",
    L > logM_paper,
    f"log r = {mp.nstr(L, 6)} but log M_eps = {mp.nstr(logM_paper, 8)}\n"
    "So r < M_eps: Lemma 3 does NOT apply to its own example.\n"
    f"Under the CORRECTED threshold it does: L/log L = "
    f"{mp.nstr(L / log(L), 6)} > (666)^1.5 = "
    f"{mp.nstr(power(2 * C33 / eps, mpf(3) / 2), 6)}",
)

# --------------------------------------------- Equation (1): the fatal error
section("Equation (1)  --  REFUTATION")

print("  Family:  A = 1,  B = 3^N - 1,  C = 3^N  with N = 2^k.")
print("  Coprime, A + B = C, C > max(A,B).")
print("  Lifting-the-exponent:  v_2(3^(2^k) - 1) = v_2(2) + v_2(4) + v_2(2^k) - 1 = k+2.")
print("  Hence 2^(k+2) || B, so rad(ABC) = 3*rad(B) <= 3B / 2^(k+1).")
print("  Eq (1)'s RHS is increasing in log r, so using an UPPER bound on log r")
print("  gives an UPPER bound on the RHS -- the correct direction for refutation.")
print()

for k in range(1, 13):
    N = 2**k
    t, v = 3**N - 1, 0
    while t % 2 == 0:
        t //= 2
        v += 1
    assert v == k + 2, f"LTE failed at k={k}"
print("  [PASS] LTE verified exactly for k = 1..12")
print()

print(f"  {'k':>3} {'log C':>14} {'log r (upper)':>15} {'Eq(1) RHS':>14} {'margin':>13}  status")
first_fail = None
for k in range(10, 19):
    N = mpf(2) ** k
    logC = N * log(3)
    logr = (N + 1) * log(3) - (k + 1) * log(2)
    R = rhs_eq1(logr)
    ok = logC <= R
    if not ok and first_fail is None:
        first_fail = k
    print(
        f"  {k:>3} {mp.nstr(logC, 8):>14} {mp.nstr(logr, 8):>15} "
        f"{mp.nstr(R, 8):>14} {mp.nstr(logC - R, 6):>13}  {'holds' if ok else 'VIOLATED'}"
    )

print()
k = 14
N = 2**k
Bk = 3**N - 1
t, v = Bk, 0
while t % 2 == 0:
    t //= 2
    v += 1
radbound = 3 * Bk // (2 ** (v - 1))
logC = mpf(N) * log(3)
logr = log(mpf(radbound))
R = rhs_eq1(logr)
print(f"  Exact-integer certificate at k = {k}  (C = 3^{N}, {len(str(3**N))} digits):")
print(f"    v_2(B) = {v} (= k+2, verified on the actual integer)")
print(f"    rad(ABC) <= 3B/2^{v - 1}, a {len(str(radbound))}-digit integer")
print(f"    log C          = {mp.nstr(logC, 12)}")
print(f"    log r  (upper) = {mp.nstr(logr, 12)}")
print(f"    Eq (1) RHS     = {mp.nstr(R, 12)}")
print(f"    log C - RHS    = {mp.nstr(logC - R, 12)}")
check(
    "Equation (1) is true",
    logC <= R,
    f"Violated by {mp.nstr(logC - R, 8)} at k=14, and for every k >= {first_fail};\n"
    "the margin grows without bound, so infinitely many explicit counterexamples.\n"
    "Eq (1) asserts C <= r^(2/3+o(1)) -- strictly STRONGER than ABC (C <= r^(1+eps)),\n"
    "so it could not have been a known theorem.\n"
    "Actual Stewart-Yu (Duke Math. J. 108 (2001) 169-181) proves only\n"
    "  log C <= kappa * rad(ABC)^(1/3) * (log rad(ABC))^3,\n"
    "which is polynomial in rad, not logarithmic, and yields nothing here.",
)

# ------------------------------------------------------------------ Case 2
section("Theorem 1, Case 2  --  order of magnitude")

print("  Paper claims r <= M_eps implies log C = O(1/eps^3).")
print(f"  {'eps':>8} {'max log C':>16} {'1/eps^3':>14} {'ratio':>14}")
for e_s in ["0.1", "0.01", "0.001"]:
    e = mpf(e_s)
    Lm = power(C33 / e, 3) * power(log(C33 / e), 2)
    logC2 = mpf(2) / 3 * Lm + C33 * power(Lm, mpf(1) / 3) * power(log(Lm), mpf(2) / 3) + 10
    print(
        f"  {e_s:>8} {mp.nstr(logC2, 6):>16} {mp.nstr(1 / e**3, 6):>14} "
        f"{mp.nstr(logC2 / (1 / e**3), 6):>14}"
    )
check(
    "log C = O(1/eps^3) in Case 2",
    False,
    "The ratio to 1/eps^3 grows like (log(1/eps))^2 rather than staying bounded.\n"
    "Correct order: log C = O(eps^-3 (log(1/eps))^2).\n"
    "Also 'C < exp(O(1/eps^3)) * r^(2/3)' introduces r^(2/3) with no derivation.",
)

# --------------------------------------------------------------- Section 7
section("Section 7  --  numerical verification")

eps = mpf("0.1")
logK = power(mpf(10), 10) / eps**5
print(f"  log K_eps = 1e10/eps^5 = {mp.nstr(logK, 6)}  (K_eps = exp(1e15))")
print(f"  log C = {mp.nstr(log(mpf(6436343)), 8)}")
print(f"  log(K_eps * 15042^1.1) = {mp.nstr(logK + mpf('1.1') * log(mpf(15042)), 8)}")
check(
    "this computation tests anything",
    False,
    "It passes with ~1e15 of slack in the logarithm. Every triple with\n"
    "C < exp(1e15) passes identically, so it confirms nothing about the bound.",
)

# ----------------------------------------------------------------- summary
section("SUMMARY")
if FAIL:
    print(f"  {len(FAIL)} check(s) failed:")
    for f in FAIL:
        print(f"    - {f}")
    print()
    print("  Load-bearing failure: Equation (1) is false, and it is the only")
    print("  step that ever bounds C. Lemma 2 independently assumes the ABC")
    print("  conjecture itself. The proof does not survive either defect.")
    sys.exit(1)
print("  All checks passed.")
