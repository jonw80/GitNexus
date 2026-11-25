"""Exact arithmetic in Q(zeta_20) and an exact minimum certificate for positive definite forms over its real
subfield. Used by evolution_gen3.py (part E, ledger T14); tested by test_exact_forms.py.

Elements are polynomials of degree < 8 in x = zeta_20 = e^(i pi/10) with rational coefficients, reduced modulo
Phi_20(x) = x^8 - x^6 + x^4 - x^2 + 1, so zeta_5 = x^4 and i = x^5. Equality is exact (the representation is
canonical). The sign of a nonzero real element is decided with interval arithmetic (mpmath.iv), refining the
precision until the enclosure excludes 0; no floating-point comparison decides any claim.
"""
import itertools
from fractions import Fraction
from math import isqrt

import mpmath
from mpmath import iv

UNITS = (1, 3, 7, 9, 11, 13, 17, 19)                 # (Z/20)^x, the Galois group of Q(zeta_20)


class F:
    __slots__ = ("c",)

    def __init__(self, c):
        self.c = tuple(Fraction(v) for v in c)
        assert len(self.c) == 8

    @staticmethod
    def const(q):
        return F([q] + [0] * 7)

    @staticmethod
    def x(k):
        p = [Fraction(0)] * (k % 20 + 1)
        p[k % 20] = Fraction(1)
        return F(_reduce(p))

    def __add__(self, o):
        o = _lift(o)
        return F([a + b for a, b in zip(self.c, o.c)])

    __radd__ = __add__

    def __neg__(self):
        return F([-a for a in self.c])

    def __sub__(self, o):
        return self + (-_lift(o))

    def __rsub__(self, o):
        return _lift(o) - self

    def __mul__(self, o):
        if isinstance(o, (int, Fraction)):
            return F([a * o for a in self.c])
        p = [Fraction(0)] * 15
        for i, a in enumerate(self.c):
            if a:
                for j, b in enumerate(o.c):
                    if b:
                        p[i + j] += a * b
        return F(_reduce(p))

    __rmul__ = __mul__

    def __eq__(self, o):
        return self.c == _lift(o).c

    def __hash__(self):
        return hash(self.c)

    def is_zero(self):
        return not any(self.c)

    def galois(self, k):                              # x -> x^k
        out = F.const(0)
        for j, a in enumerate(self.c):
            if a:
                out = out + F.x(j * k) * a
        return out

    def conj(self):
        return self.galois(19)

    def inv(self):
        assert not self.is_zero(), "inverse of 0"
        num = F.const(1)
        for k in UNITS[1:]:
            num = num * self.galois(k)
        norm = self * num
        assert all(v == 0 for v in norm.c[1:]), "norm is not rational"
        return num * (1 / norm.c[0])

    def __truediv__(self, o):
        return self * _lift(o).inv()

    def interval(self, dps):
        """Rigorous enclosure of a real element: Re(sum c_k x^k) = sum c_k cos(k pi/10)."""
        assert self.conj() == self, "element is not real"
        iv.dps = dps
        s = iv.mpf(0)
        for k, a in enumerate(self.c):
            if a:
                s += iv.mpf(a.numerator) / iv.mpf(a.denominator) * iv.cos(iv.pi * k / 10)
        return s

    def sign(self):
        if self.is_zero():
            return 0
        for dps in (30, 60, 120, 240, 480):
            s = self.interval(dps)
            if s.a > 0:
                return 1
            if s.b < 0:
                return -1
        raise ArithmeticError("sign undecided at 480 digits")


def _lift(o):
    return o if isinstance(o, F) else F.const(o)


def _reduce(p):
    p = list(p) + [Fraction(0)] * max(0, 8 - len(p))
    for d in range(len(p) - 1, 7, -1):                # x^d = x^(d-2) - x^(d-4) + x^(d-6) - x^(d-8) mod Phi_20
        a = p[d]
        if a:
            p[d] = Fraction(0)
            p[d - 2] += a
            p[d - 4] -= a
            p[d - 6] += a
            p[d - 8] -= a
    return p[:8]


ZETA5 = F.x(4)
I_ = F.x(5)
TAN72 = (F.x(4) - F.x(16)) / (F.x(5) * (F.x(4) + F.x(16)))      # sin(2pi/5)/cos(2pi/5)


def matmul(A, B):
    return [[sum((A[i][k] * B[k][j] for k in range(len(B))), F.const(0)) for j in range(len(B[0]))]
            for i in range(len(A))]


def transpose(A):
    return [list(r) for r in zip(*A)]


def identity(n):
    return [[F.const(int(i == j)) for j in range(n)] for i in range(n)]


def to_F(M):
    return [[F.const(Fraction(int(v)) if not isinstance(v, Fraction) else v) for v in row] for row in M]


def inverse(A):
    """Gauss-Jordan over the field (exact)."""
    n = len(A)
    M = [list(A[i]) + identity(n)[i] for i in range(n)]
    for col in range(n):
        piv = next(r for r in range(col, n) if not M[r][col].is_zero())
        M[col], M[piv] = M[piv], M[col]
        p = M[col][col].inv()
        M[col] = [v * p for v in M[col]]
        for r in range(n):
            if r != col and not M[r][col].is_zero():
                f = M[r][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
    return [row[n:] for row in M]


def leading_minors(A):
    n = len(A)
    out = []
    for k in range(1, n + 1):
        M = [list(A[i][:k]) for i in range(k)]
        det = F.const(1)
        for col in range(k):
            piv = next((r for r in range(col, k) if not M[r][col].is_zero()), None)
            if piv is None:
                det = F.const(0)
                break
            if piv != col:
                M[col], M[piv] = M[piv], M[col]
                det = -det
            det = det * M[col][col]
            p = M[col][col].inv()
            for r in range(col + 1, k):
                f = M[r][col] * p
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
        out.append(det)
    return out


def is_positive_definite(A):
    return all(m.sign() > 0 for m in leading_minors(A))


def certify_min(G, m):
    """Exact count of the vector pairs +-v of Z^n with v^T G v < m and with v^T G v = m.

    Every v with v^T G v <= m satisfies v_i^2 <= m (G^-1)_ii (Cauchy-Schwarz), so the box with those radii,
    taken from rigorous upper bounds, contains all of them. Float values only discard vectors whose norm exceeds
    m by far more than any rounding error; every remaining vector is decided in exact arithmetic.
    Returns (pairs below m, pairs equal to m, box radii).
    """
    n = len(G)
    if not all(G[i][j] == G[j][i] for i in range(n) for j in range(n)):
        raise ValueError("form is not symmetric")
    if not is_positive_definite(G):
        raise ValueError("form is not positive definite")
    Gi = inverse(G)
    radii = []
    for i in range(n):
        ub = (m * Gi[i][i]).interval(40).b          # rigorous upper bound of m (G^-1)_ii
        radii.append(isqrt(int(mpmath.floor(ub))))   # = floor(sqrt(ub)) >= floor(sqrt(m (G^-1)_ii))
    Gf = [[float(G[i][j].interval(30).mid) for j in range(n)] for i in range(n)]
    mf = float(m.interval(30).mid)
    below = equal = 0
    for v in itertools.product(*[range(-r, r + 1) for r in radii]):
        nz = next((x for x in v if x), 0)
        if nz <= 0:                                  # one representative of each pair +-v, and v != 0
            continue
        terms = [v[i] * v[j] * Gf[i][j] for i in range(n) for j in range(n)]
        qf, scale = sum(terms), sum(abs(t) for t in terms) + abs(mf)
        if qf > mf + 1e-9 * scale:                   # rounding error is below 1e-14 * scale
            continue
        q = F.const(0)
        for i in range(n):
            for j in range(n):
                if v[i] and v[j]:
                    q = q + G[i][j] * (v[i] * v[j])
        s = (q - m).sign()
        below += s < 0
        equal += s == 0
    return below, equal, radii


def block_forms(B, S, T1, a):
    """Exact Hodge form Q on the block lattice (basis B) of character a, and on its dual lattice.

    E = B^T S B is the intersection form, M1 the action of the monodromy T1 on the block, C the Weil operator
    (i^(p-q) on the eigenline of character t a, as in evolution_gen1.py), Q = sign * E C. Checks exactly that
    M1 has order 5 with minimal polynomial Phi_5, that C is real, commutes with M1 and squares to -1, and that
    E C is symmetric. Returns (Q_block, Q_dual, sign).
    """
    Bi = [[int(v) for v in row] for row in B.T.tolist()]
    Sl = [[int(v) for v in row] for row in S.tolist()]
    Tl = [[int(v) for v in row] for row in T1.tolist()]
    BtS = [[sum(Bi[i][k] * Sl[k][j] for k in range(len(Sl)) if Sl[k][j]) for j in range(len(Sl))] for i in range(4)]
    E = [[sum(BtS[i][k] * int(B[k, j]) for k in range(len(Sl))) for j in range(4)] for i in range(4)]
    TB = [[sum(Tl[k][l] * int(B[l, j]) for l in range(len(Tl)) if Tl[k][l]) for j in range(4)] for k in range(len(Tl))]
    N1 = [[sum(BtS[i][k] * TB[k][j] for k in range(len(Sl))) for j in range(4)] for i in range(4)]
    EF = to_F(E)
    Ei = inverse(EF)
    M1 = matmul(Ei, to_F(N1))
    Id = identity(4)
    M2 = matmul(M1, M1)
    M3, M4 = matmul(M2, M1), matmul(M2, M2)
    phi5 = [[Id[i][j] + M1[i][j] + M2[i][j] + M3[i][j] + M4[i][j] for j in range(4)] for i in range(4)]
    assert all(v.is_zero() for row in phi5 for v in row), "M1 does not satisfy Phi_5"
    assert matmul(M4, M1) == Id, "M1 does not have order 5"
    eig = [((t * a[0]) % 5, t) for t in range(1, 5)]
    C = [[F.const(0)] * 4 for _ in range(4)]
    for e, t in eig:
        Pt = Id
        for e2, _ in eig:
            if e2 != e:
                shifted = [[M1[i][j] - _zpow(e2) * int(i == j) for j in range(4)] for i in range(4)]
                d = (_zpow(e) - _zpow(e2)).inv()
                Pt = [[v * d for v in row] for row in matmul(Pt, shifted)]
        full = tuple([(-t * sum(a)) % 5] + [(t * x) % 5 for x in a])
        s = sum(v % 5 for v in full) // 5
        w = I_ if s in (2, 4) else -I_                # i^(5 - 2s)
        C = [[C[i][j] + w * Pt[i][j] for j in range(4)] for i in range(4)]
    assert all(v.conj() == v for row in C for v in row), "Weil operator is not real"
    assert matmul(C, C) == [[-v for v in row] for row in Id], "C^2 != -1"
    assert matmul(C, M1) == matmul(M1, C), "C does not commute with M1"
    Q = matmul(EF, C)
    assert all(Q[i][j] == Q[j][i] for i in range(4) for j in range(4)), "E C is not symmetric"
    sign = 1 if Q[0][0].sign() > 0 else -1
    Q = [[v * sign for v in row] for row in Q]
    Qd = matmul(matmul(Ei, Q), transpose(Ei))
    return Q, Qd, sign


def _zpow(e):
    return F.x(4 * (e % 5))
