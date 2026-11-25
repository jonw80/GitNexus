"""Unit test of evolution_gen2.py's weight-versus-grade comparison, without running its computations.
python3 -I test_evolution_gen2_checks.py   (exits 1 on a failed test)
"""
import ast
import itertools
import os
from fractions import Fraction

from mpmath import mp, mpf, nint

mp.dps = 30                                   # the precision evolution_gen2.py uses

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evolution_gen2.py")
tree = ast.parse(open(path).read())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "mismatches"]
assert funcs, "mismatches() missing from evolution_gen2.py"
ns = {"itertools": itertools, "mpf": mpf, "nint": nint}
exec(compile(ast.Module(body=funcs, type_ignores=[]), path, "exec"), ns)
mismatches = ns["mismatches"]

true = {k: mpf(-k) / 5 for k in (1, 2, 3, 4)}
assert mismatches(true) == 0                                            # weight -k/5: no disagreement
swapped = {1: mpf(-2) / 5, 2: mpf(-1) / 5, 3: mpf(-3) / 5, 4: mpf(-4) / 5}
assert mismatches(swapped) > 0                                          # a wrong weight assignment is detected
assert mismatches({k: mpf(-k) / 4 for k in (1, 2, 3, 4)}) > 0           # a wrong scaling law is detected
assert mismatches({k: v + mpf(10) ** -12 for k, v in true.items()}) > 0  # a tiny error in a weight is detected
print("evolution_gen2 check logic: all tests pass")
