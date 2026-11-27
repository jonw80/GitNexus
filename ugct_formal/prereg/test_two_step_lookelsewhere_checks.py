"""Unit test of hits() in two_step_lookelsewhere.py on planted families, without running the scan.
Every base that some correction can reach must be counted.
python3 -I test_two_step_lookelsewhere_checks.py   (exits 1 on a failed test)
"""
import ast
import os

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "two_step_lookelsewhere.py")
tree = ast.parse(open(path).read())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "hits"]
assert funcs, "hits missing from two_step_lookelsewhere.py"
ns = {"np": np}
exec(compile(ast.Module(body=funcs, type_ignores=[]), path, "exec"), ns)
hits = ns["hits"]

t, sig = 137.035999, 1e-6
# base 136.0 is 0.76% below t; the correction 1.035999 reaches it, so the pair counts
G = np.array([100.0, 136.0, 137.5])
corr = np.array([0.001, 0.464001, 1.035999])
assert hits(t, (1,), G, corr, sig) == 1
assert hits(t, (1, -1), G, corr, sig) == 2                     # 137.5 - 0.464001 = t as well
assert hits(t + 3 * sig, (1,), G, corr, sig) == 0             # outside the window


def brute(t, signs, G, corr, sig):
    return sum(any(abs(g + s * c - t) <= sig for c in corr) for g in G for s in signs)


rng = np.random.default_rng(3)
for _ in range(200):
    G = np.sort(rng.uniform(120, 150, 40))
    corr = np.sort(rng.uniform(1e-4, 5.0, 30))
    tt = float(rng.uniform(125, 145))
    # plant one exact pair, with either sign
    g0, c0 = G[int(rng.integers(40))], corr[int(rng.integers(30))]
    tt = g0 + c0 if rng.random() < 0.5 else g0 - c0
    s = 1e-9
    for signs in ((1,), (1, -1)):
        assert hits(tt, signs, G, corr, s) == brute(tt, signs, G, corr, s), (tt, signs)

print("two-step look-elsewhere checks: all tests passed")
