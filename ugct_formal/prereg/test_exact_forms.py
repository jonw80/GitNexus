"""Unit tests of exact_forms.py: field arithmetic in Q(zeta_20) and the exact minimum certificate.
python3 -I test_exact_forms.py   (exits 1 on a failed test)
"""
import importlib.util
import os
from fractions import Fraction

spec = importlib.util.spec_from_file_location(
    "exact_forms", os.path.join(os.path.dirname(os.path.abspath(__file__)), "exact_forms.py"))
xf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xf)
F, certify_min, to_F = xf.F, xf.certify_min, xf.to_F

# field identities
x = F.x(1)
assert F.x(20) == 1 and F.x(10) == -1 and xf.I_ * xf.I_ == -1 and F.x(4) == xf.ZETA5
a = F([3, -1, 0, Fraction(2, 7), 5, 0, 1, -2])
assert a * a.inv() == 1 and (a + a.conj()).conj() == a + a.conj()
t = xf.TAN72.interval(40)
assert t.a > 0 and abs(float(t.mid) - 3.0776835371752534) < 1e-15   # tan 72 deg = sqrt(5 + 2 sqrt5)
assert (xf.TAN72 * xf.TAN72 - 5) * (xf.TAN72 * xf.TAN72 - 5) == 20

def diag(*d):
    return [[F.const(0) if i != j else (d[i] if isinstance(d[i], F) else F.const(d[i])) for j in range(len(d))]
            for i in range(len(d))]

# 1. a minimum 1e-13 below the claimed bound is caught (a relative tolerance of 1e-12 would accept it)
eps = Fraction(1, 10 ** 13)
below, equal, _ = certify_min(diag(1 - eps, 2, 2, 2), F.const(1))
assert (below, equal) == (1, 0)
assert abs(float(1 - eps) / 1 - 1) < 1e-12                    # what a float tolerance test would have called exact

# 2. the search reaches the bound even when the minimal vector has large coordinates:
#    G = U^T diag(3,1,3,3) U with U = [[1,7,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]; the only minimal pair is +-(-7,1,0,0)
U = [[1, 7, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
D = [3, 1, 3, 3]
G = [[sum(U[k][i] * D[k] * U[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
below, equal, radii = certify_min(to_F(G), F.const(1))
assert (below, equal) == (0, 1) and radii[0] >= 7
assert all(max(abs(c) for c in v) <= 4 for v in [(-7, 1, 0, 0)]) is False   # a box of radius 4 would miss it

# 3. exact equality at an irrational bound, and strict inequality just above it
mu = xf.TAN72 * Fraction(2, 125)
assert certify_min(diag(mu, mu, 1, 1), mu)[:2] == (0, 2)
assert certify_min(diag(mu, mu, 1, 1), mu + Fraction(1, 10 ** 30))[:2] == (2, 0)

# 4. forms that are not positive definite or not symmetric are rejected
for bad in (diag(1, -1, 1, 1), [[F.const(v) for v in row] for row in ([1, 1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])]):
    try:
        certify_min(bad, F.const(1))
        raise AssertionError("an invalid form was accepted")
    except ValueError:
        pass
print("exact_forms: all tests pass")
