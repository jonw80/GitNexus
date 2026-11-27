#!/usr/bin/env python3
"""Scoped frontier gate: every frontier record says what it establishes and was computed in this run.

For each of the eight items of the strict gate (verify_frontier_closeout.py) the record must
  1. exist, parse, and carry a payload_hash equal to its canonical hash;
  2. name a scope category: VERIFIED, CONDITIONAL, OPEN or NEGATIVE (frontier_records.py);
  3. be written by one of the record builders (computed_by);
  4. list its inputs with SHA-256 hashes that match the files on disk now;
  5. carry this run's identifier (GITHUB_RUN_ID) when run inside GitHub Actions, so a committed or stale record fails;
  6. be VERIFIED exactly when it passes the strict gate's checks for its item; otherwise fully_certified is false and
     the status is not the strict status;
  7. CONDITIONAL: list hypotheses and results; OPEN: list open_items; NEGATIVE: list findings;
  8. have a TeX sidecar that states its scope category and status;
  9. if it records a dependency on another item, record that item's current status and scope.

The gate passes when every record is honest in this sense, whatever its scope. It reports the strict tally (how many
items meet the strict criterion) beside it; verify_frontier_closeout.py is unchanged and can still be run as a
blocking gate. Writes data_room/data/frontier_scoped_report.json. Exits 1 if any record fails.

Run from the repository root:  python3 data_room/scripts/verify_frontier_scoped.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frontier_records as fr  # noqa: E402

REPORT = "data_room/data/frontier_scoped_report.json"
BUILDERS = ("data_room/scripts/build_frontier_certificates.py", "data_room/scripts/build_ym_import_record.py",
            "ugct_sage_y4/build_y4_tensor_manifest.py")
REQUIRED_LIST = {"CONDITIONAL": ("hypotheses",), "OPEN": ("open_items",), "NEGATIVE": ("findings",)}


def strict_gate():
    spec = importlib.util.spec_from_file_location("verify_frontier_closeout", HERE / "verify_frontier_closeout.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table_mismatch(gate) -> list[str]:
    """The item table here must be the strict gate's table."""
    out = []
    for name, (cert, proof, status) in gate.REQUIRED.items():
        mine = fr.ITEMS.get(name)
        theirs = (str(cert.relative_to(gate.REPO)), str(proof.relative_to(gate.REPO)), status)
        if mine != theirs:
            out.append(f"{name}: frontier_records.ITEMS {mine} != strict gate {theirs}")
    if set(fr.ITEMS) != set(gate.REQUIRED):
        out.append(f"item sets differ: {sorted(set(fr.ITEMS) ^ set(gate.REQUIRED))}")
    return out


def strict_failures(gate, name: str, obj: dict, proof: Path, status: str) -> list[str]:
    fail = []
    try:
        gate.check_common(name, obj, proof, status, fail)
        gate.check_item(name, obj, fail)
    except Exception as exc:                      # a malformed field the strict gate does not expect
        fail.append(f"strict check raised {type(exc).__name__}: {exc}")
    return fail


def check_record(gate, root: Path, env: dict, name: str) -> dict:
    cert_rel, proof_rel, strict_status = fr.ITEMS[name]
    cert, proof = root / cert_rel, root / proof_rel
    fail: list[str] = []
    rec = {"name": name, "certificate": cert_rel, "proof": proof_rel}
    if not cert.exists():
        return {**rec, "ok": False, "strict_ok": False, "failures": [f"missing {cert_rel}"]}
    try:
        obj = json.loads(cert.read_text())
    except Exception as exc:
        return {**rec, "ok": False, "strict_ok": False, "failures": [f"unreadable {cert_rel}: {exc}"]}
    scope, status = obj.get("scope_category"), obj.get("status")
    rec.update(scope_category=scope, status=status)

    if obj.get("payload_hash") != fr.canonical_hash(obj):
        fail.append("payload_hash does not match the canonical hash")
    if scope not in fr.SCOPES:
        fail.append(f"scope_category {scope!r} is not one of {fr.SCOPES}")
    if obj.get("computed_by") not in BUILDERS:
        fail.append(f"computed_by {obj.get('computed_by')!r} is not a record builder {BUILDERS}")
    elif not (root / obj["computed_by"]).exists():
        fail.append(f"computed_by {obj['computed_by']} does not exist")

    inputs = obj.get("inputs")
    if not isinstance(inputs, list):
        fail.append("inputs must be a list of {path, sha256, role}")
        inputs = []
    for i, entry in enumerate(inputs):
        if not isinstance(entry, dict) or not entry.get("path") or not entry.get("sha256"):
            fail.append(f"inputs[{i}] needs path and sha256")
            continue
        path = root / entry["path"]
        if not path.exists():
            fail.append(f"input {entry['path']} does not exist")
        elif fr.sha256_file(path) != entry["sha256"]:
            fail.append(f"input {entry['path']} changed after the record was written")

    run_id = env.get("GITHUB_RUN_ID")
    if run_id and str(obj.get("source_workflow_run_id")) != str(run_id):
        fail.append(f"source_workflow_run_id {obj.get('source_workflow_run_id')!r} is not this run ({run_id})")
    elif not obj.get("source_workflow_run_id"):
        fail.append("source_workflow_run_id missing")

    strict = strict_failures(gate, name, obj, proof, strict_status)
    strict_ok = not strict
    if scope == "VERIFIED" and not strict_ok:
        fail.append("scope VERIFIED but the strict checks fail: " + "; ".join(strict))
    if scope != "VERIFIED":
        if strict_ok:
            fail.append(f"the record passes the strict checks but its scope is {scope}")
        if obj.get("fully_certified") is not False:
            fail.append("fully_certified must be false unless the scope is VERIFIED")
        if status == strict_status:
            fail.append(f"status {status} is the strict status but the scope is {scope}")
    for key in REQUIRED_LIST.get(scope, ()):
        if not isinstance(obj.get(key), list) or not obj[key]:
            fail.append(f"scope {scope} needs a non-empty {key} list")
    if scope == "CONDITIONAL" and not obj.get("results"):
        fail.append("scope CONDITIONAL needs the computed results")

    dep = obj.get("dependency")
    if isinstance(dep, dict) and dep.get("item") in fr.ITEMS:
        try:
            upstream = json.loads((root / fr.ITEMS[dep["item"]][0]).read_text())
        except Exception:
            upstream = {}
        if (upstream.get("status"), upstream.get("scope_category")) != (dep.get("status"), dep.get("scope_category")):
            fail.append(f"dependency on {dep['item']} records {dep.get('status')}/{dep.get('scope_category')}, but that "
                        f"record is {upstream.get('status')}/{upstream.get('scope_category')}")

    if not proof.exists():
        fail.append(f"missing sidecar {proof_rel}")
    else:
        text = proof.read_text().replace("\\_", "_")
        if f"Scope: \\texttt{{{scope}}}" not in text:
            fail.append("the sidecar does not state the scope category")
        if not status or str(status) not in text:
            fail.append("the sidecar does not state the status")
    return {**rec, "ok": not fail, "strict_ok": strict_ok, "strict_failures": strict, "failures": fail}


def verify(root: Path, env: dict) -> dict:
    gate = strict_gate()
    problems = table_mismatch(gate)
    records = [check_record(gate, root, env, name) for name in fr.ITEMS]
    ok = not problems and all(r["ok"] for r in records)
    counts = {s: sum(1 for r in records if r.get("scope_category") == s) for s in fr.SCOPES}
    return {"schema_version": "UGCT_FRONTIER_SCOPED_REPORT_V1",
            "status": "FRONTIER_RECORDS_SCOPED_AND_COMPUTED_IN_RUN" if ok else "FRONTIER_RECORDS_NOT_VERIFIED",
            "strict_tally": f"{sum(r['strict_ok'] for r in records)}/{len(records)}",
            "scope_counts": counts, "table_problems": problems,
            "meaning": "ok means every record states its scope honestly and was computed in this run from hashed "
                       "inputs; only VERIFIED records meet the strict criterion",
            "records": records}


def main() -> int:
    root = Path.cwd()
    report = verify(root, dict(os.environ))
    (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "strict_tally": report["strict_tally"],
                      "scope_counts": report["scope_counts"], "table_problems": report["table_problems"],
                      "records": [{k: r.get(k) for k in ("name", "scope_category", "status", "strict_ok", "ok",
                                                         "failures")} for r in report["records"]]}, indent=2))
    return 0 if report["status"] == "FRONTIER_RECORDS_SCOPED_AND_COMPUTED_IN_RUN" else 1


if __name__ == "__main__":
    sys.exit(main())
