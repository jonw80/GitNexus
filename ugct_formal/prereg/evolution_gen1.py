"""Evolutionary search, generation 1 (A, B, C), as pre-registered in EVOLUTION_GEN1_PREREG_2026-11-25.md (71621b8).
python3 -I evolution_gen1.py   (numpy, cypari2; reuses the lattice of ../block_lattice.py)
"""
import itertools
import os
import numpy as np

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "block_lattice.py")).read()
exec(src.split("pari(\"Kz = polcyclo(5, z)\")")[0])           # S, T, P, cols, pari, I256, checks on H_3(X5, Z)
z = np.exp(2j * np.pi / 5)


def block_basis(a):
    inv = pow(a[0], -1, 5)
    gens = [tuple((-a[k] * inv) % 5 if i == 0 else int(i == k) for i in range(4)) for k in (1, 2, 3)]
    Tg = lambda g: reduce(lambda x, y: x @ y, [np.linalg.matrix_power(T[k], g[k]) for k in range(4)])
    Kn = cols(pari.matkerint(P(np.vstack([S @ (Tg(g) - I256) for g in gens]))), 256)
    G = Kn.T @ S @ Kn
    U, V, D = pari.matsnf(P(G), 1)
    keep = [i for i in range(G.shape[0]) if int(D[i][i]) != 0]
    return Kn @ cols(V, G.shape[0])[:, keep]


def weil(full):                                  # Weil operator value i^(p-q) of a full character (a0..a4)
    s = sum(x % 5 for x in full) // 5            # <a> in {1,2,3,4}; Hodge type (4-s, s-1)
    return 1j ** (5 - 2 * s)


def minimum(Gram, R=4):
    best = np.inf
    red = np.array(pari.qflllgram(pari.matrix(4, 4, [float(x) for x in Gram.flatten()])).mattranspose().tolist(), dtype=float).T \
        if False else None
    for v in itertools.product(range(-R, R + 1), repeat=4):
        if any(v):
            x = np.array(v, dtype=float)
            best = min(best, x @ Gram @ x)
    return best


orbits, seen = [], set()
for b in itertools.product(range(1, 5), repeat=4):
    if sum(b) % 5 and b not in seen:
        orb = [tuple((t * x) % 5 for x in b) for t in range(1, 5)]
        seen.update(orb)
        orbits.append(b)
print(f"character blocks: {len(orbits)}")

rows, signs = [], set()
for a in orbits:
    B = block_basis(a)
    E = B.T @ S @ B
    Ei = np.linalg.inv(E.astype(float))
    M1 = Ei @ (B.T @ S @ T[0] @ B)                                   # T1 on the block, in the basis B
    eig = [((t * a[0]) % 5, t) for t in range(1, 5)]                  # T1 acts on line t*a by zeta^(t a1)
    C = np.zeros((4, 4), dtype=complex)
    for e, t in eig:
        Pt = np.eye(4, dtype=complex)
        for e2, _ in eig:
            if e2 != e:
                Pt = Pt @ (M1 - z ** e2 * np.eye(4)) / (z ** e - z ** e2)
        full = tuple([(-t * sum(a)) % 5] + [(t * x) % 5 for x in a])
        C += weil(full) * Pt
    assert np.abs(C.imag).max() < 1e-9
    Gq = E @ C.real
    Gq = (Gq + Gq.T) / 2
    ev = np.linalg.eigvalsh(Gq)
    sign = 1 if ev.min() > 0 else -1 if ev.max() < 0 else 0
    signs.add(sign)
    Gq = sign * Gq
    Gd = Ei @ Gq @ Ei.T                                             # Q on the dual lattice
    full1 = tuple([(-sum(a)) % 5] + list(a))
    types = "".join("(3,0)(2,1)(1,2)(0,3)".split(")")[sum(x * t % 5 for x in full1 + ()) // 5 - 1] + ")" for t in (1, 2, 3, 4)) \
        if False else ""
    rows.append((full1, round(abs(np.linalg.det(E))), minimum(Gq), minimum(Gd), sign))

print(f"raw sign of <g, C g> on every block: {signs} (one value = consistent Hodge assignment)")
rows.sort(key=lambda r: r[3])
for full1, detE, mb, mub, sg in rows[:6]:
    print(f"  block {full1}: det E = {detE}, m_b = {mb:.6f}, mu_b = {mub:.6f}")
mu_min, m_min = min(r[3] for r in rows), min(r[2] for r in rows)
print(f"A  bounds on the Weil systole: {mu_min:.6f} <= min Q <= {m_min:.6f}")
print(f"   weakest coupling of any charge of X5: {1 / m_min:.4f} <= alpha^-1_max <= {1 / mu_min:.4f}"
      f"   (target 137.035999177): {'possible' if 1 / mu_min >= 137.035999177 else 'excluded'}")
m1 = [r for r in rows if r[0] == (1, 1, 1, 1, 1)][0]
print(f"B  (1,1,1,1,1) block with its principal form: min Q = {m1[2] / 25:.6f} -> alpha^-1 = {25 / m1[2]:.6f}")

# C: grade of every squared chiral structure constant of the k = 3 N = 2 minimal model
grades = set()
for l1, l2 in itertools.product(range(4), repeat=2):
    l3 = l1 + l2
    if l3 <= 3:
        expo = {}
        for x, s in ((1, 1), (l3 + 1, 1), (l1 + 1, -1), (l2 + 1, -1)):   # gamma(x/5) = Gamma(x/5)/Gamma(1-x/5)
            expo[x] = expo.get(x, 0) + s
            expo[5 - x] = expo.get(5 - x, 0) - s
        grades.add(sum(k * n for k, n in expo.items()) % 5)
print(f"C  grades of all squared chiral structure constants (l1 + l2 = l3 <= 3): {grades}")
