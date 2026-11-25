"""Unit test of evolution_gen1.py's lattice minimum, without running its computations.
python3 -I test_evolution_gen1_checks.py   (exits 1 on a failed test)
"""
import ast
import itertools
import os

import numpy as np

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evolution_gen1.py")
tree = ast.parse(open(path).read())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "minimum"]
assert funcs, "minimum() missing from evolution_gen1.py"
ns = {"np": np, "itertools": itertools}
exec(compile(ast.Module(body=funcs, type_ignores=[]), path, "exec"), ns)
minimum = ns["minimum"]

# G = U^T diag(3,1,3,3) U, U = [[1,7,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]: the minimum 1 is attained only at
# +-(-7,1,0,0), outside the box [-4,4]^4, where the smallest value is 3
U = np.array([[1, 7, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
G = U.T @ np.diag([3.0, 1.0, 3.0, 3.0]) @ U
box4 = min(np.array(v) @ G @ np.array(v) for v in itertools.product(range(-4, 5), repeat=4) if any(v))
assert abs(box4 - 3) < 1e-12                              # what the old fixed box returned
assert abs(minimum(G) - 1) < 1e-12                        # the complete enumeration finds the true minimum
assert abs(minimum(np.eye(4) * 2.5) - 2.5) < 1e-12
print("evolution_gen1 minimum: all tests pass")
