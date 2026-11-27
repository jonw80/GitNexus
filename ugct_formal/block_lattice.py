#!/usr/bin/env python3
"""Integral lattice of the character blocks of H_3(X5, Z), from Pham's vanishing cycles.

F = {x1^5 + x2^5 + x3^5 + x4^5 = 1} is the affine chart x0 = 1 of the Fermat quintic X5 (up to x -> -x).
Pham (1965) and Sebastiani-Thom (1971): H_3(F, Z) is the tensor product of four copies of the reduced H_0 of
the 5th roots of unity (rank 256); the Seifert form is L = L1^(x4) and the intersection form S = L^T - L.
T_k (x_k -> zeta x_k) acts by the cyclic shift on factor k.  H_3(X5, Z) = H_3(F, Z) / radical(S): the tubes
over H_2 of the hyperplane section are exactly the radical (Gysin sequence, H_1 of the section = 0).

Checks (the run fails on any): S invariant under every T_k; L^-1 L^T = T_1 T_2 T_3 T_4 (Milnor monodromy);
rank S = 204; all 204 nonzero elementary divisors of S are 1 (H_3(X5) is unimodular: Poincare duality);
the radical is the monodromy-fixed part.

Block of a character a = (a1..a4) (a0 = -sum mod 5, all nonzero): the classes of H_3(X5, Z) fixed by
K_a = {g : sum a_k g_k = 0 mod 5}, i.e. lying in the span of the eigenlines t*a, t = 1..4.  For each block:
the elementary divisors of the restricted form, and its structure as a Z[zeta_5]-module, Lambda = Z[zeta] lam
with E(x, y) = Tr(c x ybar).  c/25 is compared with the principal model c_model = (1 + 2z + 2z^3)/5 used for
the gauge-kinetic matrix in ALPHA_NORMALIZATION_NOTE sec. 4 (ledger T7), up to units u ubar = phi^(2n).

Run: python3 -I block_lattice.py   (numpy, cypari2)
"""
import itertools
import sys
from functools import reduce

import numpy as np
import cypari2

pari = cypari2.Pari()
pari.allocatemem(2 * 10**9)
fails = []


def check(ok, what):
    if not ok:
        fails.append(what)
    return ok


T1 = np.zeros((4, 4), dtype=np.int64)            # basis e_j = p_j - p_{j+1} of reduced H_0(mu_5); p_j -> p_{j+1}
for j in range(3):
    T1[j + 1, j] = 1
T1[:, 3] = -1
L1 = -np.eye(4, dtype=np.int64)                  # Seifert form of z^5
for j in range(3):
    L1[j, j + 1] = 1
check((T1.T @ L1 @ T1 == L1).all(), "L1 shift-invariant")
check((np.rint(-np.linalg.inv(L1) @ L1.T) == T1).all(), "monodromy of z^5 is the shift")

kron = lambda *ms: reduce(np.kron, ms)
I4, I256 = np.eye(4, dtype=np.int64), np.eye(256, dtype=np.int64)
L = kron(L1, L1, L1, L1)
S = L.T - L
T = [kron(*[T1 if i == k else I4 for i in range(4)]) for k in range(4)]
h = T[0] @ T[1] @ T[2] @ T[3]
check((L @ h == L.T).all(), "Sebastiani-Thom: L^-1 L^T is the Milnor monodromy")
check(all((Tk.T @ S @ Tk == S).all() for Tk in T), "S invariant under every T_k")

P = lambda M: pari.matrix(M.shape[0], M.shape[1], [int(v) for v in M.flatten()])
cols = lambda M, n: np.array([[int(M[j][i]) for j in range(len(M))] for i in range(n)], dtype=np.int64)
Sp = P(S)
snf = [int(v) for v in pari.matsnf(Sp)]
rad = cols(pari.matkerint(Sp), 256)
nonzero = [v for v in snf if v]
print(f"H_3(F): rank 256; rank S = {len(nonzero)}; radical rank {rad.shape[1]}; nonzero elementary divisors: "
      f"{sorted(set(nonzero))} x {len(nonzero)}")
check(len(nonzero) == 204 and set(nonzero) == {1}, "H_3(X5, Z) unimodular of rank 204")
check(((h - I256) @ rad == 0).all(), "radical fixed by the monodromy")

pari("Kz = polcyclo(5, z)")
c_model = pari("Mod((1 + 2*z + 2*z^3)/5, Kz)")
TR = [[4 if (i - j) % 5 == 0 else -1 for i in range(4)] for j in range(5)]      # Tr(zeta^(i-j))


def block(a):
    inv = pow(a[0], -1, 5)
    gens = [tuple((-a[k] * inv) % 5 if i == 0 else int(i == k) for i in range(4)) for k in (1, 2, 3)]
    Tg = lambda g: reduce(lambda x, y: x @ y, [np.linalg.matrix_power(T[k], g[k]) for k in range(4)])
    M = np.vstack([S @ (Tg(g) - I256) for g in gens])
    Kn = cols(pari.matkerint(P(M)), 256)
    G = Kn.T @ S @ Kn
    U, V, D = pari.matsnf(P(G), 1)
    keep = [i for i in range(G.shape[0]) if int(D[i][i]) != 0]
    B = Kn @ cols(V, G.shape[0])[:, keep]                  # Z-basis of the block lattice (mod the radical)
    ed = sorted(abs(int(D[i][i])) for i in keep)
    gram = lambda v: np.array([[int((np.linalg.matrix_power(T[0], i) @ v) @ S @ (np.linalg.matrix_power(T[0], j) @ v))
                                for j in range(4)] for i in range(4)])
    detB = round(abs(np.linalg.det(B.T @ S @ B)))
    lam = next(B @ np.array(cf) for cf in itertools.product(range(-2, 3), repeat=4)
               if any(cf) and round(abs(np.linalg.det(gram(B @ np.array(cf))))) == detB)
    E = [int(lam @ S @ (np.linalg.matrix_power(T[0], j) @ lam)) for j in range(5)]
    sol = pari.matsolve(pari.matrix(4, 4, [x for row in TR[:4] for x in row]), pari.matrix(4, 1, E[:4]))
    c = pari(f"Mod({'+'.join(f'({sol[i, 0]})*z^{i}' for i in range(4))}, Kz)")
    consistent = sum(TR[4][i] * pari(sol[i, 0]) for i in range(4)) == E[4]
    imaginary = pari(f"(subst(lift({c}), z, z^4) + lift({c})) % Kz") == 0
    unit = [2 * n for n in range(-8, 9) if pari(f"{c}/25/{c_model}") == pari(f"Mod(-z^2-z^3, Kz)^{2 * n}")]
    return Kn.shape[1], ed, c, consistent and imaginary, pari(f"norm({c})"), unit


for a in [(1, 1, 3, 4), (1, 1, 1, 4), (1, 1, 1, 3), (1, 1, 1, 1)]:
    rank56, ed, c, ok, N, unit = block(a)
    full = f"({(-sum(a)) % 5},{','.join(map(str, a))})"
    print(f"block {full}: elementary divisors {ed}; c = {pari('lift')(c)}, N(c) = {N}; "
          f"c/25 = c_model * phi^{unit[0] if unit else '?'}")
    check(rank56 == 56, f"{full}: block kernel rank 4 + 52")
    check(ed == [25, 25, 25, 25], f"{full}: form = 25 x unimodular")
    check(ok and N == 3125, f"{full}: E = Tr(c x ybar) with cbar = -c, N(c) = 5^5")
    if a != (1, 1, 1, 1):
        check(len(unit) == 1, f"{full}: equals the principal model up to a unit")

if fails:
    print("FAILED:", "; ".join(fails))
    sys.exit(1)
print("all checks passed")
