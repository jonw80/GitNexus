#!/usr/bin/env python3
"""Unit tests of build_y4_tensor_manifest.py on planted run outputs, checked with the frontier gate's own functions.
The planted cross-check outputs have the shapes the real producers write: native_pushforward_core.py,
run_intersectionnumbers_ewx.wls and run_intersectionnumbers_ewx_mathics.py all write
data/higher_cartan_closure_rules.json (exact_values, computed_by) plus their own report.
Run from the repository root:  python3 ugct_sage_y4/test_build_y4_tensor_manifest.py   (exits 1 on a failed test)
"""
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
NATIVE_VALUES = {"C1,C1,C1,C1": "-8", "C1,C1,C1,C2": "3", "C1,C2,C3,R": "-3/2", "C2,C2,C2,H": "0", "C4,C4,C4,C4": "12"}
NATIVE = {"computed_by": "native_pushforward_core.py", "exact_values": NATIVE_VALUES, "required_value_count": 5,
          "value_count": 5, "status": "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED"}
WOLFRAM_OK = {"status": "INTERSECTIONNUMBERS_EWX_EXACT_VALUES_EXPORTED", "value_count": 5}
MATHICS_OK = {"status": "MATHICS_EWX_EXACT_VALUES_EXPORTED", "value_count": 5}
WOLFRAM_NONE = {"status": "WOLFRAMSCRIPT_NOT_AVAILABLE"}
MATHICS_FAIL = {"status": "MATHICS_EWX_EXACT_VALUES_FAILED", "computed_count": 0, "error_count": 20}


def table(producer, values):
    return {"computed_by": producer, "exact_values": values, "value_count": len(values),
            "status": "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED"}


def plant(root, chow_status="RESOLVED_AMBIENT_CHOW_MANUAL_TRANSCRIPTION_PARTIAL", final=None, native=NATIVE,
          wolfram=WOLFRAM_NONE, mathics=MATHICS_FAIL, summary_nonzero=None, tensor_entries=None, with_summary=True):
    basis = ["A", "B", "C"]
    entries = tensor_entries if tensor_entries is not None else {"A,A,B,C": 2, "A,B,B,C": "-1", "A,B,C,C": 0}
    n_nonzero = sum(1 for v in entries.values() if str(v) != "0")
    files = {
        bm.TENSOR: {"basis": basis, "quadruple_intersections": entries, "resolution_chamber": "test",
                    "checks": {"chi_Y4": 1056}},
        bm.CHOW_INPUT: {"status": chow_status},
        bm.EXC_RULES: {"status": "EXCEPTIONAL_SECTOR_VERIFIED", "rules": {"A,A,A,A": 0, "B,B,B,B": "0", "C,C,C,C": 3}},
        bm.HC_RULES: final if final is not None else native,
        bm.WOLFRAM: wolfram,
        bm.MATHICS: mathics,
    }
    if native is not None:
        files[bm.HC_NATIVE] = native
    if with_summary:
        files[bm.SUMMARY] = {"status": "SAGE_DEGREE4_TENSOR_EXPORTED", "full_tensor_status": bm.VERIFIED,
                             "full_chamber_specific_tensor_verified": True,
                             "nonzero_exported": n_nonzero if summary_nonzero is None else summary_nonzero,
                             "total_symmetric_multisets_degree4": comb(6, 4), "zero_multisets": comb(6, 4) - n_nonzero}
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


# 1. today's situation: partial Chow input, the table is the native one, both cross-checks failed
m, tex, fails = build()
assert m["status"] == bm.NOT_VERIFIED and m["fully_certified"] is False and m["full_chamber_specific_tensor_verified"] is False
assert m["nonzero_quadruple_intersections"] == 2 and m["total_degree4_monomials"] == 15
assert m["source_workflow_run_id"] == "123" and m["source_commit"] == "abc123" and len(m["artifact_sha256"]) == 64
assert len(m["open_items"]) == 2 and "native_pushforward_core.py" in m["open_items"][1]
assert m["cross_checks"]["table_comparison"]["independent_producer"] is None
assert "chi_Y4" in m["typed_values_not_used"] and "1056" not in json.dumps({k: v for k, v in m.items() if k != "typed_values_not_used"})
assert m["payload_hash"] == gate.canonical_hash(m) and len(tex.encode()) > 500
assert any("status mismatch" in f for f in fails) and "tensor verified flag required" in fails, fails

# 2. complete input; Wolfram's IntersectionNumbers run replaced the table with the same values -> verified, gate passes
same = dict(NATIVE_VALUES, **{"C1,C2,C3,R": "-1.5"})          # equal as exact rationals
m, tex, fails = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", same), wolfram=WOLFRAM_OK)
assert m["status"] == bm.VERIFIED and m["open_items"] == [] and fails == [], (m["open_items"], fails)
assert m["cross_checks"]["table_comparison"]["mismatch_count"] == 0
m, tex, fails = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx_mathics.py", NATIVE_VALUES),
                      mathics=MATHICS_OK)
assert m["status"] == bm.VERIFIED and fails == []

# 3. a disagreeing, incomplete or unconfirmed independent table does not verify
wrong = dict(NATIVE_VALUES, **{"C4,C4,C4,C4": "11"})
m, _, _ = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", wrong), wolfram=WOLFRAM_OK)
assert m["status"] == bm.NOT_VERIFIED and m["cross_checks"]["table_comparison"]["mismatch_count"] == 1
short = {k: v for k, v in NATIVE_VALUES.items() if k != "C4,C4,C4,C4"}
m, _, _ = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", short), wolfram=WOLFRAM_OK)
assert m["status"] == bm.NOT_VERIFIED
m, _, _ = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", NATIVE_VALUES), wolfram=WOLFRAM_NONE)
assert m["status"] == bm.NOT_VERIFIED and "report says" in m["open_items"][0]
m, _, _ = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", NATIVE_VALUES), wolfram=WOLFRAM_OK,
                native=None)
assert m["status"] == bm.NOT_VERIFIED and "was not kept" in m["open_items"][0]

# 4. a matching table with incomplete Chow input still does not verify
m, _, _ = build(final=table("run_intersectionnumbers_ewx.wls", NATIVE_VALUES), wolfram=WOLFRAM_OK)
assert m["status"] == bm.NOT_VERIFIED and len(m["open_items"]) == 1

# 5. missing or inconsistent run outputs stop the build
expect_error(with_summary=False)
expect_error(summary_nonzero=7)
expect_error(tensor_entries={"A,A,B,D": 1})

# 6. a tampered manifest fails the gate's hash check
m, tex, _ = build(chow_status=bm.CHOW_COMPLETE, final=table("run_intersectionnumbers_ewx.wls", NATIVE_VALUES), wolfram=WOLFRAM_OK)
m["nonzero_quadruple_intersections"] = 1847
with tempfile.TemporaryDirectory() as d:
    assert "payload_hash mismatch" in gate_failures(m, tex, Path(d))

print("Y4 manifest builder: all tests passed")
