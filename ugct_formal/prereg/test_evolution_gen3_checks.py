"""Unit test of the pass/fail logic of evolution_gen3.py, without running its computations.
python3 -I test_evolution_gen3_checks.py   (exits 1 on a failed test)
"""
import ast
import contextlib
import io
import os
from collections import Counter

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evolution_gen3.py")
tree = ast.parse(open(path).read())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("certificate_failures", "finish")]
assert {f.name for f in funcs} == {"certificate_failures", "finish"}, "check functions missing from evolution_gen3.py"
ns = {}
exec(compile(ast.Module(body=funcs, type_ignores=[]), path, "exec"), ns)
certificate_failures, finish = ns["certificate_failures"], ns["finish"]

ok = ((0, 5, True), (0, 5, True))
assert certificate_failures(Counter({ok: 51}), 51) == []
assert certificate_failures(Counter({ok: 50}), 51)                                      # a block missing
assert certificate_failures(Counter({ok: 50, ((1, 5, True), (0, 5, True)): 1}), 51)    # a dual vector below the bound
assert certificate_failures(Counter({ok: 50, ((0, 5, True), (0, 0, True)): 1}), 51)    # no minimal vector found
assert certificate_failures(Counter({ok: 50, ((0, 5, False), (0, 5, True)): 1}), 51)   # minimum not the exact value

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    try:
        finish(["a failed check"], 0.0492429, 30.7768)
        raise AssertionError("finish() returned although a check failed")
    except SystemExit as e:
        assert e.code == 1
assert "FAILED" in buf.getvalue() and "certified" not in buf.getvalue()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    finish([], 0.0492429, 30.7768)
assert "certified" in buf.getvalue()
print("evolution_gen3 check logic: all tests pass")
