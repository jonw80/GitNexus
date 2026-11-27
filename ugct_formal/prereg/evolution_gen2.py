"""Evolutionary search, generation 2 (A, B), as pre-registered in EVOLUTION_GEN2_PREREG_2026-11-25.md (d32fca8).
python3 -I evolution_gen2.py   (mpmath; exits with status 1 if any pre-registered check fails)
"""
import itertools
from mpmath import mp, mpf, quad, gamma, exp, inf, log, nint
def mismatches(weights, R=4, tol=mpf(10) ** -20):
    """Number of monomials prod Gamma(k/5)^(n_k), |n_k| <= R, on which 'grade 0' (sum k n_k = 0 mod 5) and
    'integral scale weight' (sum n_k w_k an integer, with the weights w_k given) disagree."""
    bad = 0
    for n in itertools.product(range(-R, R + 1), repeat=4):
        wt = sum(m * weights[k] for k, m in zip((1, 2, 3, 4), n))
        bad += (abs(wt - nint(wt)) < tol) != (sum(k * m for k, m in zip((1, 2, 3, 4), n)) % 5 == 0)
    return bad


mp.dps = 30
# A: the exponential period I(a, c) = Int_0^inf e^(-c x^5) x^(a-1) dx scales as c^(-a/5): weight -a/5, grade a.
for a in (1, 2, 3, 4, 5, 6):
    r = quad(lambda x: exp(-2 * x ** 5) * x ** (a - 1), [0, 1, inf]) / quad(lambda x: exp(-x ** 5) * x ** (a - 1), [0, 1, inf])
    print(f"A  a = {a}: I(a,2)/I(a,1) = {mp.nstr(r, 15)}, 2^(-a/5) = {mp.nstr(mpf(2) ** (-mpf(a) / 5), 15)}")
# The scale weight of each Gamma(k/5) is measured from its integral, I(k, 2)/I(k, 1) = 2^w_k, independently of
# the grade sum k n_k (mod 5); the two are then compared on every monomial with |n_k| <= 4.
w = {k: log(quad(lambda x: exp(-2 * x ** 5) * x ** (k - 1), [0, 1, inf])
            / quad(lambda x: exp(-x ** 5) * x ** (k - 1), [0, 1, inf])) / log(2) for k in (1, 2, 3, 4)}
print("A  measured weights w_k of Gamma(k/5):", {k: mp.nstr(v, 12) for k, v in w.items()})
bad = mismatches(w)
print(f"A  monomials |n_k| <= 4 where (grade 0) and (integral measured weight) disagree: {bad} of {9 ** 4}")
# B: torus characters of the Principia's assignment N_Y * omega_Y
omega_Y = (1, 1, 1, 3, 4)
diag = lambda v: len(set(v)) == 1
chars = [tuple(x + (j == i) for j, x in enumerate(omega_Y)) for i in range(5) if omega_Y[i] == 1]
print(f"B  characters of the three terms of N_Y omega_Y: {chars}; any presentation-invariant: {any(diag(c) for c in chars)}")
neutral = 0
for k in (1, 2, 3):
    for combo in itertools.combinations_with_replacement([a for a in itertools.product(range(1, 5), repeat=5) if sum(a) % 5 == 0], k):
        tot = [sum(c[i] for c in combo) for i in range(5)]
        if diag(tot):
            neutral += 1
            assert sum(sum(c) for c in combo) % 5 == 0          # every product of periods has grade 0
print(f"B  torus-neutral products of 1-3 Fermat periods: {neutral}; all grade 0, so none equals Law 1 (grade 1, T3)")

# Every pre-registered claim is checked; exit status 1 if any fails.
fail = [] if bad == 0 else [f"{bad} monomials where grade and measured weight disagree"]
fail += [] if all(abs(w[k] + mpf(k) / 5) < mpf(10) ** -20 for k in w) else ["a measured weight differs from -k/5"]
fail += [] if not any(diag(c) for c in chars) else ["a placement of N_Y omega_Y is presentation-invariant"]
fail += [] if neutral == 4904 else [f"{neutral} torus-neutral products, not 4904"]
if fail:
    print("FAILED:", "; ".join(fail))
    raise SystemExit(1)
