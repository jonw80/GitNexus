"""Evolutionary search, generation 3 (G3-1, G3-2, G3-3, E), as pre-registered in
EVOLUTION_GEN3_PREREG_2026-11-25.md (commit 465bbf0).
python3 -I evolution_gen3.py   (mpmath, numpy, cypari2; E reuses the lattice of ../block_lattice.py)
"""
import itertools
import os
from collections import Counter
from mpmath import mp, mpf, pi, gamma, sin, sqrt, quad, exp, inf, tan, findpoly, nstr

def certificate_failures(cert, n_blocks):
    """Part E pass criterion (pre-registration 465bbf0): on every block, for the dual form and the block form,
    no vector lies below the exact minimum, at least one minimal pair exists, and the minimal norms are exact."""
    bad = [] if sum(cert.values()) == n_blocks else [f"{sum(cert.values())} of {n_blocks} blocks certified"]
    for key, count in cert.items():
        for name, (below, pairs, exact) in zip(("dual", "block"), key):
            if below or pairs < 1 or not exact:
                bad.append(f"{count} block(s), {name} form: {below} vectors below, {pairs} minimal pairs, exact {exact}")
    return bad


def finish(failures, mu, m):
    """Exit with status 1 if any pre-registered check failed; print the certificate only if all passed."""
    if failures:
        print("FAILED:", "; ".join(failures))
        raise SystemExit(1)
    print(f"      certified: every nonzero charge has Q >= (2/125) tan 72 = {mu:.7f}; alpha^-1 <= {1 / mu:.4f};"
          f" block minimum 10 tan 72 = {m:.4f}")


mp.dps = 50
L = pi * gamma(mpf(1) / 5) ** 3 / gamma(mpf(2) / 5)
G = lambda k: gamma(mpf(k) / 5)

# G3-1: Laplace factor of the affine chart
P_omega = G(1) ** 3 * G(3) * G(4) / gamma(2)                       # period of the (1,1,1,3,4) block
N_Y = 3 * sqrt(5) * G(1)
print("G3-1  N_Y - 15 sqrt5 Gamma(6/5)          =", nstr(N_Y - 15 * sqrt(5) * gamma(mpf(6) / 5), 5))
print("      Law 1 - N_Y P(omega_Y)/(12 pi)      =", nstr(L - N_Y * P_omega / (12 * pi), 5))
E4 = 1
for a in (1, 1, 1, 3):                                              # Int_{R+^4} e^(-sum x^5) x_4^2 d^4x, by quadrature
    E4 *= quad(lambda x: exp(-x ** 5) * x ** (a - 1), [0, 1, inf])
print("      Law 1 - sin(2pi/5) 5^4 E4(1,1,1,3)  =", nstr(L - sin(2 * pi / 5) * 5 ** 4 * E4, 5))
multisets = list(itertools.combinations_with_replacement(range(1, 5), 4))
vals = sorted((float(5 ** 4 * sin(2 * pi / 5) * G(a[0]) * G(a[1]) * G(a[2]) * G(a[3]) / 5 ** 4), a) for a in multisets)
print(f"      affine-chart characters a' (multisets): {len(multisets)}; hyperplanes 5, placements 4;"
      f" (1,1,1,3) is input, not output: rank {[v[1] for v in vals].index((1, 1, 1, 3)) + 1} of {len(vals)} by value")

# G3-2: tt* normalization; content vectors in (Gamma(1/5), Gamma(2/5), pi) modulo algebraic numbers
content = {1: (1, 0, -0.5), 2: (0, 1, -0.5), 3: (0, -1, 0.5), 4: (-1, 0, 0.5)}   # sqrt(g_k) = Gamma(k/5) pi^(-1/2) x alg
law1 = (3, -1, 1)
realized = {}
for n in range(1, 9):
    sols = [m for m in itertools.combinations_with_replacement(range(1, 5), n)
            if tuple(sum(content[k][j] for k in m) for j in (0, 1)) == law1[:2]]
    realized[n] = (len(sols), sum(1 for m in sols if sum(m) % 5 == 0), sols[:3])
for n, (c, cproj, ex) in realized.items():
    print(f"G3-2  n = {n}: states with Law 1's Gamma-content: {c} (Gepner-projected: {cproj})" + (f", e.g. {ex}" if c else ""))
g = lambda k: sin(k * pi / 5) * G(k) ** 2 / pi                       # g_k = 1/alpha_k^2 (Leaf-Herrmann A.11), up to scale
r = L / (pi ** 2 * sqrt(g(1) ** 3 * g(3)))
print("      Law 1 / (pi^2 sqrt(g_1^3 g_3)) =", nstr(r, 20), " minimal polynomial:", findpoly(r, 8, maxcoeff=10 ** 6))
for k in (1, 2, 3, 4):                                               # (i) tt*-normalized thimble central charge
    zk = abs((mp.e ** (2j * pi * k / 5) - 1) * G(k) / 5) / sqrt(g(k))
    print(f"      k = {k}: |orthonormal thimble charge|/sqrt(pi) - (2/5) sqrt(sin(k pi/5)) = "
          f"{nstr(zk / sqrt(pi) - 2 * sqrt(sin(k * pi / 5)) / 5, 5)}   (algebraic: no Gamma left)")
grades = {sum(a) % 5 for a in itertools.product(range(1, 5), repeat=5) if sum(a) % 5 == 0}
print(f"      grades of all projected 5-copy normalizations: {grades}")

# G3-3: Laplace scale fixed by an SL(2,Z) fixed point
for gs in (mpf(1), 2 / sqrt(3)):
    lap = quad(lambda t: exp(-t / gs) * t ** (mpf(6) / 5 - 1), [0, 1, inf])
    print(f"G3-3  g_s = {nstr(gs, 8)}: Laplace integral / Gamma(6/5) = {nstr(lap / gamma(mpf(6) / 5), 12)} = g_s^(6/5)")
print("      ratio of the two fixed-point values:", nstr((2 / sqrt(3)) ** (mpf(6) / 5), 8))

# Pre-registered claims of G3-1 to G3-3, checked before part E redefines names such as L and r;
# the script exits with status 1 at the end if any check fails.
fail_g3 = []
for name, res in (("N_Y = 15 sqrt5 Gamma(6/5)", N_Y - 15 * sqrt(5) * gamma(mpf(6) / 5)),
                  ("Law 1 = N_Y P(omega_Y)/(12 pi)", L - N_Y * P_omega / (12 * pi)),
                  ("Law 1 = sin(2pi/5) 5^4 E4", L - sin(2 * pi / 5) * 5 ** 4 * E4),
                  ("5 r^4 - 20 r^2 - 16 = 0", 5 * r ** 4 - 20 * r ** 2 - 16)):
    fail_g3 += [] if abs(res) < mpf(10) ** -40 else [f"{name}: residual {nstr(res, 5)}"]
for k in (1, 2, 3, 4):
    zk = abs((mp.e ** (2j * pi * k / 5) - 1) * G(k) / 5) / sqrt(g(k))
    fail_g3 += [] if abs(zk / sqrt(pi) - 2 * sqrt(sin(k * pi / 5)) / 5) < mpf(10) ** -40 else [f"thimble charge k = {k} not Gamma-free"]
fail_g3 += [] if realized[5][0] == 0 else ["a 5-factor state has Law 1's Gamma-content"]
fail_g3 += [] if realized[4][0] == 1 else [f"{realized[4][0]} 4-factor states, not 1"]
fail_g3 += [f"{c} projected {n}-factor states" for n, (_, c, _) in realized.items() if c]
fail_g3 += [] if grades == {0} else [f"projected grades {grades}"]
for gs in (mpf(1), 2 / sqrt(3)):
    lap = quad(lambda t: exp(-t / gs) * t ** (mpf(6) / 5 - 1), [0, 1, inf]) / gamma(mpf(6) / 5)
    fail_g3 += [] if abs(lap - gs ** (mpf(6) / 5)) < mpf(10) ** -30 else [f"Laplace integral at g_s = {nstr(gs, 8)}"]

# E: Fincke-Pohst certificate of the magnitude no-go on all 51 blocks
import numpy as np
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evolution_gen1.py")).read()
exec(src.split("orbits, seen = [], set()")[0])
mu_exact, m_exact = float(mpf(2) / 125 * tan(2 * pi / 5)), float(10 * tan(2 * pi / 5))
orbits, seen = [], set()
for b in itertools.product(range(1, 5), repeat=4):
    if sum(b) % 5 and b not in seen:
        seen.update(tuple((t * x) % 5 for x in b) for t in range(1, 5))
        orbits.append(b)
cert, definite = Counter(), []
for a in orbits:
    B = block_basis(a)
    E = B.T @ S @ B
    Ei = np.linalg.inv(E.astype(float))
    M1 = Ei @ (B.T @ S @ T[0] @ B)
    eig = [((t * a[0]) % 5, t) for t in range(1, 5)]
    C = np.zeros((4, 4), dtype=complex)
    for e, t in eig:
        Pt = np.eye(4, dtype=complex)
        for e2, _ in eig:
            if e2 != e:
                Pt = Pt @ (M1 - z ** e2 * np.eye(4)) / (z ** e - z ** e2)
        C += weil(tuple([(-t * sum(a)) % 5] + [(t * x) % 5 for x in a])) * Pt
    Gq = E @ C.real
    Gq = (Gq + Gq.T) / 2
    Gq = Gq if np.linalg.eigvalsh(Gq).min() > 0 else -Gq
    definite.append(bool(np.linalg.eigvalsh(Gq).min() > 0))
    Gd = Ei @ Gq @ Ei.T
    out = []
    for M, exact in ((Gd, mu_exact), (Gq, m_exact)):         # flag 2 widens the bound by a relative slack ~1e-9
        Mp = pari.matrix(4, 4, [float(x) for x in M.flatten()])
        below = int(pari.qfminim(Mp, exact * (1 - 1e-6), 0, 2)[0])
        at = pari.qfminim(Mp, exact * (1 + 1e-6), 100, 2)
        V = np.array([[float(at[2][i, j]) for j in range(at[2].ncols())] for i in range(4)])
        err = max((abs(float(v @ M @ v) / exact - 1) for v in V.T), default=float("inf"))
        out.append((below, int(at[0]) // 2, err < 1e-12))
    cert[tuple(out)] += 1
print(f"E     certificate over {len(orbits)} blocks: ((vectors below exact(1-1e-6), minimal pairs, norms = exact to 1e-12) for dual, block): {dict(cert)}")
# Part E's pass criterion, then the verdict on every check (status 1 if any failed).
fail = certificate_failures(cert, 51) + ([] if len(orbits) == 51 else [f"{len(orbits)} blocks, not 51"])
fail += [] if all(definite) else [f"{definite.count(False)} blocks with an indefinite Hodge form"]
finish(fail_g3 + fail, mu_exact, m_exact)
