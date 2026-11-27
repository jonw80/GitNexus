"""Unit test of the scan E chance estimate in alpha_exactness_tests.py (hit_chance), without running the scan.
The chance must use the same fixed +-sigma hit test as the scan itself.
python3 -I test_alpha_exactness_checks.py   (exits 1 on a failed test)
"""
import ast
import os
import random
from bisect import bisect_left
from math import log as flog

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "alpha_exactness_tests.py")
tree = ast.parse(open(path).read())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "hit_chance"]
assert funcs, "hit_chance missing from alpha_exactness_tests.py"
ns = {"flog": flog}
exec(compile(ast.Module(body=funcs, type_ignores=[]), path, "exec"), ns)
hit_chance = ns["hit_chance"]

d, s = 1.0, 1e-3                                  # target scale and absolute tolerance
lo, hi = d / 2, 2 * d
span = flog(hi / lo)

# one value far from d: the window is [v - s, v + s], not the relative window v/(1 -+ s/d)
v = 1.9
c, n = hit_chance([v], s, lo, hi)
assert n == 1 and abs(c - flog((v + s) / (v - s)) / span) < 1e-12
r = s / d
assert abs(c - flog((1 + r) / (1 - r)) / span) > 0.1 * c           # the relative window gives a different answer

# overlapping windows are merged, separate ones add
c2, _ = hit_chance([1.0, 1.0005], s, lo, hi)
assert abs(c2 - flog((1.0005 + s) / (1.0 - s)) / span) < 1e-12
c3, _ = hit_chance([0.8, 1.2], s, lo, hi)
assert abs(c3 - (flog(0.801 / 0.799) + flog(1.201 / 1.199)) / span) < 1e-12

# clipping at the ends of the target range, and values outside it
c4, n4 = hit_chance([lo, 3.0, 0.1], s, lo, hi)
assert n4 == 1 and abs(c4 - flog((lo + s) / lo) / span) < 1e-12

# agreement with the direct hit test |v - t| <= s for log-uniform random targets
rng = random.Random(7)
vals = sorted(rng.uniform(0.3, 2.5) for _ in range(300))
c5, _ = hit_chance(vals, s, lo, hi)
hits, N = 0, 200000
for _ in range(N):
    t = lo * (hi / lo) ** rng.random()
    i = bisect_left(vals, t - s)
    hits += i < len(vals) and vals[i] <= t + s
mc = hits / N
assert abs(c5 - mc) < 4 * (mc * (1 - mc) / N) ** 0.5 + 1e-3, (c5, mc)

print("alpha exactness checks: all tests passed")
