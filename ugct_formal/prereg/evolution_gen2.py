"""Evolutionary search, generation 2 (A, B), as pre-registered in EVOLUTION_GEN2_PREREG_2026-11-25.md (d32fca8)."""
import itertools
from mpmath import mp, mpf, quad, gamma, exp, inf
mp.dps = 30
# A: the exponential period I(a, c) = Int_0^inf e^(-c x^5) x^(a-1) dx scales as c^(-a/5): weight -a/5, grade a.
for a in (1, 2, 3, 4, 5, 6):
    r = quad(lambda x: exp(-2 * x ** 5) * x ** (a - 1), [0, 1, inf]) / quad(lambda x: exp(-x ** 5) * x ** (a - 1), [0, 1, inf])
    print(f"A  a = {a}: I(a,2)/I(a,1) = {mp.nstr(r, 15)}, 2^(-a/5) = {mp.nstr(mpf(2) ** (-mpf(a) / 5), 15)}")
bad = [n for n in itertools.product(range(-4, 5), repeat=4)
       if ((sum(k * m for k, m in zip((1, 2, 3, 4), n)) % 5 == 0) != (sum(k * m for k, m in zip((1, 2, 3, 4), n)) / 5).is_integer())]
print(f"A  monomials |n_k| <= 4 where (grade 0) and (integral weight) disagree: {len(bad)} of {9 ** 4}")
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
