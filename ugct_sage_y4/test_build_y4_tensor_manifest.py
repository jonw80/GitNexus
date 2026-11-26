#!/usr/bin/env python3
"""Unit tests of build_y4_tensor_manifest.py on planted run outputs, checked with the frontier gate's own functions.

The planted outputs have the shapes the real producers write: run_chow_tensor.sage writes the Sage tensor and run
summary; independent_y4_pushforward.py writes data/y4_independent_tensor.json (status, failures, basis,
quadruple_intersections, chi_Y4, checks); native_pushforward_core.py and the IntersectionNumbers runs write
data/higher_cartan_closure_rules.json plus their own reports (recorded only).
Run from the repository root:  python3 ugct_sage_y4/test_build_y4_tensor_manifest.py   (exits 1 on a failed test)
"""
import copy
import importlib.util
import json
import tempfile
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bm = load(REPO / "ugct_sage_y4" / "build_y4_tensor_manifest.py", "build_y4_tensor_manifest")
gate = load(REPO / "data_room" / "scripts" / "verify_frontier_closeout.py", "verify_frontier_closeout")
ENV = {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "abc123", "GITHUB_REPOSITORY": "o/r"}
BASIS = ["A", "B", "C"]
SAGE_ENTRIES = {"A,A,B,C": 2, "A,B,B,C": "-1", "A,B,C,C": 0, "C,C,C,C": "-8"}
IND_ENTRIES = {"A,A,B,C": "2", "A,B,B,C": "-1", "C,C,C,C": "-8"}
PASSING_CHECKS = {"chi_from_published_EJK_formula": "3048", "chi_matches_published_formula": True, "todd_genus": "2",
                  "riemann_roch_divisors_tested": 420, "riemann_roch_failures": 0, "calabi_yau_condition": True,
                  "zero_section_relation": True, "prepotential_triple_cartan": {"passed": True}}
IND = {"status": bm.INDEPENDENT_OK, "failures": [], "basis": BASIS, "quadruple_intersections": IND_ENTRIES,
       "chi_Y4": "3048", "d3_tadpole_chi_over_24": "127", "int_c2_squared": "1496", "nonzero_count": 3,
       "method": "test", "checks": PASSING_CHECKS}
NATIVE = {"computed_by": "native_pushforward_core.py", "exact_values": {"C,C,C,C": "-8"}, "required_value_count": 1,
          "value_count": 1, "status": "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED"}
WOLFRAM_NONE = {"status": "WOLFRAMSCRIPT_NOT_AVAILABLE"}
MATHICS_FAIL = {"status": "MATHICS_EWX_EXACT_VALUES_FAILED", "computed_count": 0, "error_count": 20}
PARTIAL_CHOW = "RESOLVED_AMBIENT_CHOW_MANUAL_TRANSCRIPTION_PARTIAL"


def plant(root, sage_entries=None, ind=IND, chow_status=PARTIAL_CHOW, summary_nonzero=None, with_summary=True,
          sage_checks=None, summary_extra=None, hc_rules=None, cross=None, wolfram=None):
    entries = SAGE_ENTRIES if sage_entries is None else sage_entries
    n_nonzero = sum(1 for v in entries.values() if str(v) != "0")
    files = {
        bm.TENSOR: {"basis": BASIS, "quadruple_intersections": entries, "resolution_chamber": "test",
                    "checks": sage_checks if sage_checks is not None else {"chi_Y4": None}},
        bm.CHOW_INPUT: {"status": chow_status},
        bm.EXC_RULES: {"status": "EXCEPTIONAL_SECTOR_VERIFIED", "rules": {"A,A,A,A": 0, "C,C,C,C": -8}},
        bm.HC_RULES: hc_rules if hc_rules is not None else NATIVE,
        bm.HC_NATIVE: NATIVE,
        bm.WOLFRAM: wolfram if wolfram is not None else WOLFRAM_NONE,
        bm.MATHICS: MATHICS_FAIL,
    }
    if ind is not None:
        files[bm.INDEPENDENT] = ind
    if cross is not None:
        files[bm.HC_CROSS] = cross
    if with_summary:
        files[bm.SUMMARY] = {"status": "SAGE_DEGREE4_TENSOR_EXPORTED", "full_tensor_status": bm.VERIFIED,
                             "full_chamber_specific_tensor_verified": True,
                             "nonzero_exported": n_nonzero if summary_nonzero is None else summary_nonzero,
                             "total_symmetric_multisets_degree4": comb(6, 4), "zero_multisets": comb(6, 4) - n_nonzero,
                             "full_chamber_specific_tensor_executed_with_fallback": False,
                             "exceptional_rule_file": {"declares_exceptional_sector_executed_with_fallback": False,
                                                       "reduction_stats": {"higher_cartan_fallback_terms": 0}}}
        files[bm.SUMMARY].update(summary_extra or {})
    for rel, obj in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj))


def gate_failures(manifest, tex, root):
    proof = root / "proof.tex"
    proof.write_text(tex)
    fail = []
    gate.check_common("y4_tensor", manifest, proof, gate.REQUIRED["y4_tensor"][2], fail)
    gate.check_item("y4_tensor", manifest, fail)
    return fail


def build(**kw):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        plant(root, **kw)
        m, tex = bm.build(root, ENV)
        return m, tex, gate_failures(m, tex, root)


def expect_error(**kw):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        plant(root, **kw)
        try:
            bm.build(root, ENV)
        except bm.RunOutputError:
            return
        raise AssertionError(f"inconsistent run outputs accepted: {kw}")


def ind_with(**changes):
    out = copy.deepcopy(IND)
    for k, v in changes.items():
        if k.startswith("check_"):
            out["checks"][k[len("check_"):]] = v
        else:
            out[k] = v
    return out


# 1. both computations agree and the independent checks pass -> verified, even with partial Chow input and no
#    IntersectionNumbers run (those are recorded, not required); the gate's own checks pass
m, tex, fails = build()
assert m["status"] == bm.VERIFIED and m["fully_certified"] is True and m["full_chamber_specific_tensor_verified"] is True, m["open_items"]
assert fails == [], fails
assert m["open_items"] == [] and m["tensor_comparison"]["monomials_compared"] == 15 and m["tensor_comparison"]["mismatch_count"] == 0
assert m["nonzero_quadruple_intersections"] == 3 and m["tensor_file"] == bm.INDEPENDENT and m["chi_Y4"] == "3048"
assert m["recorded_not_required"]["chow_input_status"] == PARTIAL_CHOW
assert m["source_workflow_run_id"] == "123" and m["source_commit"] == "abc123" and len(m["artifact_sha256"]) == 64
assert m["payload_hash"] == gate.canonical_hash(m) and len(tex.encode()) > 500

# 2. keys in another order and equal rationals written differently still agree
m, _, fails = build(sage_entries={"B,A,C,A": "4/2", "C,B,B,A": "-1.0", "C,C,C,C": -8})
assert m["status"] == bm.VERIFIED and fails == [], (m["open_items"], fails)

# 3. today's Sage tensor before the native fix: higher-Cartan entries all zero -> not verified, the difference is named
m, _, fails = build(sage_entries={"A,A,B,C": 2, "A,B,B,C": "-1", "C,C,C,C": 0})
assert m["status"] == bm.NOT_VERIFIED and m["tensor_comparison"]["mismatch_count"] == 1
assert m["tensor_comparison"]["mismatch_sample"][0] == {"monomial": "C,C,C,C", "sage": "0", "independent": "-8"}
assert "differ on 1 of 15 monomials" in m["open_items"][0] and "tensor verified flag required" in fails

# 4. the independent computation missing, failing a check, or reporting failures -> not verified
m, _, _ = build(ind=None)
assert m["status"] == bm.NOT_VERIFIED and "did not run" in m["open_items"][0] and m["tensor_file"] == bm.TENSOR
for bad in (ind_with(check_todd_genus="3"), ind_with(check_prepotential_triple_cartan={"passed": False}),
            ind_with(check_chi_matches_published_formula=False), ind_with(check_riemann_roch_failures=4),
            ind_with(check_riemann_roch_divisors_tested=0), ind_with(failures=["Calabi-Yau condition fails"]),
            ind_with(status="INDEPENDENT_COMPUTATION_CHECKS_FAILED")):
    m, _, _ = build(ind=bad)
    assert m["status"] == bm.NOT_VERIFIED and m["chi_Y4"] is None, bad

# 5. different bases cannot be compared
m, _, _ = build(ind=ind_with(basis=["A", "C", "B"]))
assert m["status"] == bm.NOT_VERIFIED and "different bases" in " ".join(m["open_items"])

# 6. a typed chi in the Sage file is recorded as not used and appears nowhere else
m, _, _ = build(sage_checks={"chi_Y4": 1056})
assert "chi_Y4" in m["typed_values_not_used"] and "1056" not in json.dumps({k: v for k, v in m.items() if k != "typed_values_not_used"})

# 7. a Sage tensor built with fallback values (or without the flag) is no cross-check, even if it agrees
for extra in ({"full_chamber_specific_tensor_executed_with_fallback": True},
              {"full_chamber_specific_tensor_executed_with_fallback": None},
              {"exceptional_rule_file": {"declares_exceptional_sector_executed_with_fallback": True}},
              {"exceptional_rule_file": {"reduction_stats": {"higher_cartan_fallback_terms": 3}}}):
    m, _, fails = build(summary_extra=extra)
    assert m["status"] == bm.NOT_VERIFIED and "fallback" in " ".join(m["open_items"]) and m["sage_fallback_reasons"], extra
    assert "tensor verified flag required" in fails

# 8. an IntersectionNumbers table saved right after its run is compared even after a later Sage step rewrote the
#    shared higher-Cartan file (recorded, not required)
WOLFRAM_TABLE = {"computed_by": "run_intersectionnumbers_ewx.wls", "exact_values": {"C,C,C,C": "-8"}, "value_count": 1}
SAGE_TABLE = {"computed_by": "export_higher_cartan_from_resolved_presentation.sage", "exact_values": {"C,C,C,C": "0"}}
m, _, _ = build(hc_rules=SAGE_TABLE, cross=WOLFRAM_TABLE,
                wolfram={"status": "INTERSECTIONNUMBERS_EWX_EXACT_VALUES_EXPORTED", "value_count": 1})
cmp_ = m["recorded_not_required"]["intersectionnumbers_table_comparison"]
assert cmp_["independent_producer"] == "wolfram" and cmp_["passed"] is True and m["status"] == bm.VERIFIED, cmp_
assert bm.HC_CROSS in m["files"]

# 9. missing or inconsistent Sage outputs stop the build
expect_error(with_summary=False)
expect_error(summary_nonzero=7)
expect_error(sage_entries={"A,A,B,D": 1})

# 10. a tampered manifest fails the gate's hash check
m, tex, _ = build()
m["nonzero_quadruple_intersections"] = 1847
with tempfile.TemporaryDirectory() as d:
    assert "payload_hash mismatch" in gate_failures(m, tex, Path(d))

print("Y4 manifest builder: all tests passed")
