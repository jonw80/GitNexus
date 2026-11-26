#!/usr/bin/env python3
"""Tests of independent_y4_pushforward.py: its sanity checks, its full run, and that its checks catch the errors
they are meant to catch (the old native conventions, zeroed higher-Cartan entries, a wrong Dynkin order).
Run from the repository root:  python3 ugct_sage_y4/test_independent_y4_pushforward.py   (exits 1 on a failed test)
"""
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("independent_y4_pushforward", REPO / "ugct_sage_y4" / "independent_y4_pushforward.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def clear_caches():
    for f in (m.push_blowup_monomial, m.push_bundle_monomial, m.integrate_base_monomial):
        f.cache_clear()


def run(path):
    with contextlib.redirect_stdout(io.StringIO()):
        code = m.main(str(path))
    return code, json.loads(Path(path).read_text())


# 1. sanity checks of the pushforward formulas and the base ring
assert m.sanity_failures() == [], m.sanity_failures()

# 2. the full computation
with tempfile.TemporaryDirectory() as d:
    code, r = run(Path(d) / "y4.json")
assert code == 0 and r["status"] == "INDEPENDENT_TENSOR_COMPUTED" and r["failures"] == [], r["failures"]
assert r["chi_Y4"] == "3048" and r["d3_tadpole_chi_over_24"] == "127" and r["int_c2_squared"] == "1496"
assert r["nonzero_count"] == 284 and r["total_degree4_monomials"] == 3060 and r["higher_cartan_value_count"] == 235
ch = r["checks"]
assert ch["chi_from_published_EJK_formula"] == "3048" and ch["smooth_weierstrass_chi"] == "3168" and ch["todd_genus"] == "2"
assert ch["riemann_roch_failures"] == 0 and ch["riemann_roch_divisors_tested"] == 420
assert ch["prepotential_triple_cartan"]["passed"] and ch["prepotential_triple_cartan"]["chain"] == ["C1", "C2", "C3", "C4"]
t = r["quadruple_intersections"]
assert t["H,H,C1,C1"] == "-2" and t["H,H,C1,C2"] == "1" and "H,H,C1,C3" not in t           # -Cartan matrix x int R h h
assert t["R,C1,C1,C1"] == "-4" and t["H,C1,C1,C1"] == "12" and t["C2,C2,C2,C2"] == "-14"
assert sum(1 for k in r["higher_cartan_values"].values() if k != "0") == 113
tensor, c2 = t, r["c2_pairings"]

# 3. the Riemann-Roch check catches a tensor whose higher-Cartan entries are zero (the Sage table before the fix)
zeroed = {k: v for k, v in tensor.items() if sum(p.startswith("C") for p in k.split(",")) < 3}
n, bad = m.riemann_roch_failures(zeroed, c2)
assert len(bad) > 100, len(bad)

# 4. the prepotential check fails for a wrong Dynkin order
assert m.prepotential_check(["C1", "C3", "C2", "C4"])["passed"] is False

# 5. the old native conventions (hypersurface 3H+6L-E1-E2-E3-E4, centers without H) fail the checks
saved = (m.HYPERSURFACE, dict(m.CENTERS))
try:
    m.HYPERSURFACE = m.lin(H=3, L=6, E1=-1, E2=-1, E3=-1, E4=-1)
    m.CENTERS.clear()
    m.CENTERS.update({1: [m.lin(L=2), m.lin(L=3), m.var("R")], 2: [m.lin(L=3, E1=-1), m.E[1]],
                      3: [m.lin(L=2, E1=-1), m.E[2]], 4: [m.lin(L=3, E1=-1, E2=-1), m.E[3]]})
    clear_caches()
    with tempfile.TemporaryDirectory() as d:
        code, r = run(Path(d) / "old.json")
    assert code == 1 and r["status"] == "INDEPENDENT_COMPUTATION_CHECKS_FAILED", r["status"]
    assert any("EJK" in f for f in r["failures"]) or any("Calabi-Yau" in f for f in r["failures"]), r["failures"]
finally:
    m.HYPERSURFACE = saved[0]
    m.CENTERS.clear()
    m.CENTERS.update(saved[1])
    clear_caches()

print("independent Y4 pushforward: all tests passed")
