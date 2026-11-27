#!/usr/bin/env python3
"""Tests of build_ym_import_record.py, checked with the frontier gate's own functions.
Run from the repository root:  python3 data_room/scripts/test_build_ym_import_record.py   (exits 1 on a failed test)
"""
import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ym = load(REPO / "data_room" / "scripts" / "build_ym_import_record.py", "build_ym_import_record")
gate = load(REPO / "data_room" / "scripts" / "verify_frontier_closeout.py", "verify_frontier_closeout")
CURRENT = json.loads((REPO / ym.STATUS_FILE).read_text())


def all_proved(st):
    st = copy.deepcopy(st)
    for g in st["gates"].values():
        g["status"] = "proved"
    return st


def build(st, volume_bytes=None):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ym.STATUS_FILE).parent.mkdir(parents=True, exist_ok=True)
        if volume_bytes is not None:
            (root / "data_room/primary/ym/gzym.pdf").write_bytes(volume_bytes)
        (root / ym.STATUS_FILE).write_text(json.dumps(st))
        rec, tex = ym.build(root)
        proof = root / "proof.tex"
        proof.write_text(tex)
        fail = []
        gate.check_common("ym_mass_gap_import", rec, proof, gate.REQUIRED["ym_mass_gap_import"][2], fail)
        gate.check_item("ym_mass_gap_import", rec, fail)
        return rec, tex, fail


def expect_error(st):
    try:
        build(st)
    except ym.StatusFileError:
        return
    raise AssertionError("malformed status file accepted")


# 1. the recorded status (2026-11-26): two statements open and one lattice-only, so scope OPEN; every flag false, no
#    hash; the gate rejects it with reasons
rec, tex, fail = build(CURRENT)
assert rec["status"] == ym.OPEN and rec["scope_category"] == "OPEN" and rec["hypotheses"] == []
assert rec["fully_certified"] is False and rec["companion_volume_sha256"] is None
assert rec["computed_by"] == ym.COMPUTED_BY and rec["inputs"][0]["path"] == ym.STATUS_FILE
assert rec["source_workflow_run_id"] == "local" and "Scope: \\texttt{OPEN}" in tex
assert not any(rec[f] for _, f in ym.GATES), [rec[f] for _, f in ym.GATES]
assert {g["status"] for g in rec["gates"].values()} == {"conditional", "lattice_only", "open"}
assert len(rec["open_items"]) == 6 and rec["payload_hash"] == gate.canonical_hash(rec)
for need in ("status mismatch", "fully_certified must be true", "companion hash required",
             "os_axioms_verified must be true", "reflection_positivity_verified must be true",
             "rg_convergence_verified must be true", "spectral_gap_lower_bound_positive must be true"):
    assert any(need in f for f in fail), (need, fail)
assert len(tex.encode()) > 500 and "Theorem A.67.1" in tex and "lattice" in tex and "^" not in tex.replace(r"\^{}", "")

# 2. all four proved, volume committed, independent verification recorded -> verified, and the gate passes
good = all_proved(CURRENT)
good["companion_volume"]["file"] = "data_room/primary/ym/gzym.pdf"
good["independent_verification"] = [{"by": "referee", "scope": "all four statements", "evidence": "report"}]
rec, _, fail = build(good, volume_bytes=b"volume")
assert rec["status"] == ym.VERIFIED and rec["fully_certified"] and fail == [], (rec["open_items"], fail)
assert rec["scope_category"] == "VERIFIED" and rec["companion_volume_sha256"] == hashlib.sha256(b"volume").hexdigest()
assert [i["path"] for i in rec["inputs"]] == [ym.STATUS_FILE, "data_room/primary/ym/gzym.pdf"]

# 3. a statement short of proved: "conditional" -> scope CONDITIONAL with its assumptions as hypotheses;
#    "lattice_only" or "open" -> scope OPEN; no file, no verification or a hash mismatch -> CONDITIONAL on the volume
for name, flag in ym.GATES:
    for status, expect in (("conditional", ym.CONDITIONAL), ("lattice_only", ym.OPEN), ("open", ym.OPEN)):
        st = copy.deepcopy(good)
        st["gates"][name]["status"] = status
        rec = build(st, volume_bytes=b"volume")[0]
        assert rec["status"] == expect and rec["fully_certified"] is False, (name, status)
        if status == "conditional":
            assert rec["scope_category"] == "CONDITIONAL" and rec["hypotheses"][0].startswith(flag), rec["hypotheses"]
st = copy.deepcopy(good)
st["independent_verification"] = []
rec = build(st, volume_bytes=b"volume")[0]
assert rec["status"] == ym.CONDITIONAL and "companion volume's proofs" in rec["hypotheses"][-1]
assert build(good)[0]["status"] == ym.CONDITIONAL                                   # file named but not committed
st = copy.deepcopy(good)
st["companion_volume"]["sha256"] = "0" * 64
rec = build(st, volume_bytes=b"volume")[0]
assert rec["status"] == ym.CONDITIONAL and rec["companion_volume_sha256"] is None and "differs" in rec["open_items"][0]

# 4. malformed status files are refused
for bad in ({}, {"gates": {}}, {**CURRENT, "gates": {**CURRENT["gates"], "spectral_gap": {**CURRENT["gates"]["spectral_gap"], "status": "done"}}},
            {**CURRENT, "gates": {**CURRENT["gates"], "os_axioms": {**CURRENT["gates"]["os_axioms"], "references": []}}},
            {**CURRENT, "gates": {**CURRENT["gates"], "rg_convergence": {**CURRENT["gates"]["rg_convergence"], "flag": "rg_ok"}}}):
    expect_error(bad)

print("Yang-Mills import record builder: all tests passed")
