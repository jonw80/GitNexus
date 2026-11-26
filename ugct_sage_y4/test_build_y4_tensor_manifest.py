#!/usr/bin/env python3
"""Unit tests of build_y4_tensor_manifest.py on planted run outputs, checked with the frontier gate's own functions.
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


def plant(root, chow_status="RESOLVED_AMBIENT_CHOW_MANUAL_TRANSCRIPTION_PARTIAL", mathics=None, summary_nonzero=None,
          tensor_entries=None, with_summary=True):
    basis = ["A", "B", "C"]
    entries = tensor_entries if tensor_entries is not None else {"A,A,B,C": 2, "A,B,B,C": "-1", "A,B,C,C": 0}
    n_nonzero = sum(1 for v in entries.values() if str(v) != "0")
    files = {
        bm.TENSOR: {"basis": basis, "quadruple_intersections": entries, "resolution_chamber": "test",
                    "checks": {"chi_Y4": 1056}},
        bm.CHOW_INPUT: {"status": chow_status},
        bm.EXC_RULES: {"status": "EXCEPTIONAL_SECTOR_VERIFIED", "rules": {"A,A,A,A": 0, "B,B,B,B": "0", "C,C,C,C": 3}},
        bm.HC_RULES: {"status": "X", "computed_by": "native", "value_count": 5, "required_value_count": 5},
        bm.WOLFRAM: {"status": "WOLFRAMSCRIPT_NOT_AVAILABLE"},
        bm.MATHICS: mathics if mathics is not None else {"status": "MATHICS_EWX_EXACT_VALUES_FAILED", "computed_count": 0,
                                                         "error_count": 20},
    }
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


def expect_error(**kw):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        plant(root, **kw)
        try:
            bm.build(root, ENV)
        except bm.RunOutputError:
            return
        raise AssertionError(f"inconsistent run outputs accepted: {kw}")


# 1. today's situation: partial Chow input, failed cross-checks -> recorded as computed, not verified; the gate rejects it
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    plant(root)
    m, tex = bm.build(root, ENV)
    assert m["status"] == bm.NOT_VERIFIED and m["fully_certified"] is False and m["full_chamber_specific_tensor_verified"] is False
    assert m["nonzero_quadruple_intersections"] == 2 and m["total_degree4_monomials"] == 15
    assert m["source_workflow_run_id"] == "123" and m["source_commit"] == "abc123"
    assert m["tensor_file_sha256"] == bm.sha256_file(root / bm.TENSOR) and len(m["artifact_sha256"]) == 64
    assert len(m["open_items"]) == 2 and m["inputs"]["exceptional_rules"]["zero_values"] == 2
    assert "chi_Y4" in m["typed_values_not_used"] and "1056" not in json.dumps({k: v for k, v in m.items() if k != "typed_values_not_used"})
    assert m["payload_hash"] == gate.canonical_hash(m)
    fails = gate_failures(m, tex, root)
    assert any("status mismatch" in f for f in fails) and "tensor verified flag required" in fails, fails
    assert len(tex.encode()) > 500

# 2. complete input and a passing independent cross-check -> verified, and the gate's Y4 checks all pass
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    plant(root, chow_status=bm.CHOW_COMPLETE,
          mathics={"status": "OK", "computed_count": 5, "error_count": 0, "mismatch_count": 0})
    m, tex = bm.build(root, ENV)
    assert m["status"] == bm.VERIFIED and m["open_items"] == []
    assert gate_failures(m, tex, root) == []

# 3. a cross-check that does not report mismatches, or computed too few values, does not count
for rep in ({"status": "OK", "computed_count": 5, "error_count": 0},
            {"status": "OK", "computed_count": 4, "error_count": 0, "mismatch_count": 0}):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        plant(root, chow_status=bm.CHOW_COMPLETE, mathics=rep)
        m, _ = bm.build(root, ENV)
        assert m["status"] == bm.NOT_VERIFIED, rep

# 4. missing or inconsistent run outputs stop the build
expect_error(with_summary=False)
expect_error(summary_nonzero=7)
expect_error(tensor_entries={"A,A,B,D": 1})

# 5. the tampered manifest fails the gate's hash check
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    plant(root, chow_status=bm.CHOW_COMPLETE, mathics={"status": "OK", "computed_count": 5, "error_count": 0, "mismatch_count": 0})
    m, tex = bm.build(root, ENV)
    m["nonzero_quadruple_intersections"] = 1847
    assert "payload_hash mismatch" in gate_failures(m, tex, root)

print("Y4 manifest builder: all tests passed")
