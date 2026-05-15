#!/usr/bin/env python3
"""Fail the GitHub job if the UGCT Y4/full-payload math is not verified.

The validator scripts write detailed JSON reports but intentionally keep running
so artifacts are uploaded. This final gate makes the Actions job red whenever
UGCT math remains incomplete.
"""
import json
import sys
from pathlib import Path

REPORTS = Path("reports")
DATA = Path("data")

checks = []

def load(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as exc:
        return {"status": "UNREADABLE_JSON", "error": str(exc)}

sage = load(REPORTS / "sage_run_summary.json") or {}
y4 = load(DATA / "y4_intersection_ring_full.json") or {}
cert = load(REPORTS / "higher_cartan_exact_certificate_report.json") or {}
full = load(REPORTS / "full_payload_validation_report.json") or {}
mathics = load(REPORTS / "intersectionnumbers_ewx_mathics_report.json") or {}
wolfram = load(REPORTS / "intersectionnumbers_ewx_run_report.json") or {}

checks.append((
    "Y4 tensor full verification",
    y4.get("status") == "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED" or sage.get("full_tensor_status") == "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED",
    y4.get("status") or sage.get("full_tensor_status") or "missing"
))
checks.append((
    "Higher-Cartan exact certificate",
    cert.get("status") == "EXACT_HIGHER_CARTAN_CERTIFICATE_VERIFIED",
    cert.get("status") or "missing"
))
checks.append((
    "Full payload verification",
    full.get("status") == "FULL_PAYLOAD_VERIFIED",
    full.get("status") or "missing"
))

ok = all(c[1] for c in checks)
summary = {
    "status": "UGCT_MATH_VERIFIED" if ok else "UGCT_MATH_NOT_VERIFIED",
    "checks": [{"name": n, "ok": passed, "observed": observed} for n, passed, observed in checks],
    "mathics_status": mathics.get("status"),
    "wolfram_status": wolfram.get("status"),
    "guidance": "Artifacts were uploaded before this gate. Inspect reports/*.json, especially higher_cartan_exact_certificate_report.json and sage_run_summary.json."
}
print(json.dumps(summary, indent=2, sort_keys=True))
if not ok:
    sys.exit(1)
