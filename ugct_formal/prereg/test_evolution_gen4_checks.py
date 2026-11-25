"""Unit test of evolution_gen4.py's check logic, without running its computations.
python3 -I test_evolution_gen4_checks.py   (exits 1 on a failed test)
"""
import ast
import importlib.util
import os
from fractions import Fraction as Fr

from mpmath import mp, mpf, gamma, pi, quad

mp.dps = 50
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("exact_forms", os.path.join(here, "exact_forms.py"))
xf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xf)
path = os.path.join(here, "evolution_gen4.py")
tree = ast.parse(open(path).read())
names = {"sigma", "value", "relation_ok", "gamma_content", "g_content", "beta_by_quadrature", "charpoly", "is_integral"}
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
assert {f.name for f in funcs} == names, "check functions missing from evolution_gen4.py"
fifths = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FIFTHS")
ns = {"mpf": mpf, "gamma": gamma, "pi": pi, "quad": quad, "Fr": Fr, "F": xf.F, "xf": xf}
exec(compile(ast.Module(body=[fifths] + funcs, type_ignores=[]), path, "exec"), ns)
sigma, relation_ok, gamma_content, g_content = ns["sigma"], ns["relation_ok"], ns["gamma_content"], ns["g_content"]

# sigma
assert sigma(([(Fr(1, 5), 3), (Fr(2, 5), -1)], Fr(1))) == Fr(1, 5)                       # Law 1
assert sigma(([(Fr(1, 7), 1), (Fr(3, 7), 1), (Fr(4, 7), -1)], Fr(0))) == 0               # a Beta value
# a correct Gauss multiplication (m = 2) passes; the same with the wrong power of pi fails both tests
x, m = Fr(1, 10), 2
alg = mpf(2) ** (mpf(m - 1) / 2) * mpf(m) ** (mpf(1) / 2 - m * mpf(x.numerator) / x.denominator)
lhs = ([(x, 1), (x + Fr(1, 2), 1)], Fr(0))
assert relation_ok(lhs, ([(m * x, 1)], Fr(1, 2)), alg) == (True, True)
assert relation_ok(lhs, ([(m * x, 1)], Fr(1)), alg) == (False, False)
# Gamma-content
assert gamma_content(Fr(-4, 5)) == (1, 0, 0) and gamma_content(Fr(3, 5)) == (0, -1, 1)
assert gamma_content(Fr(0)) == "pole" and gamma_content(Fr(1, 3)) is None
assert g_content(Fr(1), Fr(1), Fr(12, 5)) == (1, -1, 1)                                   # one-loop bubble, d = 12/5
assert g_content(Fr(1), Fr(1), Fr(2)) == "divergent"
# the singular-endpoint Beta integral that defeated plain quadrature
al, be = mpf(1) / 11, mpf(10) / 11
assert abs(ns["beta_by_quadrature"](al, be) - gamma(al) * gamma(be) / gamma(al + be)) < mpf(10) ** -40
plain = quad(lambda u: u ** (al - 1) * (1 - u) ** (be - 1), [0, 0.5, 1])
assert abs(plain - gamma(al) * gamma(be) / gamma(al + be)) > mpf(10) ** -10               # the old check's failure
# integrality in Q(zeta_20)
F = xf.F
assert ns["is_integral"](F.x(4)) and ns["is_integral"](-(F.x(8)) - F.x(12))              # zeta_5, golden ratio
assert not ns["is_integral"](F.const(Fr(1, 2)))
print("evolution_gen4 check logic: all tests pass")
