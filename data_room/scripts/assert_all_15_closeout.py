#!/usr/bin/env python3
"""Strict closeout gate for the Principia 15-item payload.

This script distinguishes a generated payload from a mathematically closed
payload.  It writes data/ALL_15_CLOSEOUT_REPORT.json and exits nonzero unless
all non-frontier/non-conditional certificate records are genuinely verified.

The current policy is intentionally strict:
  - VERIFIED/CERTIFIED or fully_certified:true counts as closed.
  - READY_FOR, SPECIFIED, HPC, EXTERNAL, INHERITS, FRONTIER, CONTESTED, and
    CONDITIONAL do not count as closed.
  - Tier-3/frontier items must remain fully_certified:false unless a future
    theorem/computation genuinely changes their status.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

EXPECTED = {
    1: "flux_scan_summary.json",
    2: "pf_basis.json",
    3: "attractor_intervals.json",
    4: "axio_dilaton_interval.json",
    5: "instanton_divisors.json",
    6: "hidden_sector_ranks.json",
    7: "pfaffian_prefactors.json",
    8: "racetrack_superpotential.json",
    9: "string_loop_coefficients.json",
    10: "kahler_stabilization_certificate.json",
    11: "warp_factor_certificate.json",
    12: "uplift_backreaction_certificate.json",
    13: "cosmological_constant_error_budget.json",
    14: "cp_trace_anomaly_certificate.json",
    15: "global_arithmetic_id_certificate.json",
    16: "prime_race_density_certificate.json",
}

BAD_STATUS_TOKENS = (
    "READY_FOR",
    "SPECIFIED",
    "HPC",
    "EXTERNAL",
    "INHERITS",
    "FRONTIER",
    "CONTESTED",
    "CONDITIONAL",
    "OPEN",
)


def load(name: str) -> dict:
    p = DATA / name
    if not p.exists():
        return {"missing": True, "path": str(p)}
    try:
        obj = json.loads(p.read_text())
    except Exception as exc:
        return {"missing": True, "path": str(p), "error": str(exc)}
    obj["_file"] = name
    return obj


def classify(obj: dict) -> str:
    if obj.get("missing"):
        return "missing"
    status = str(obj.get("status", ""))
    tier = str(obj.get("tier", ""))
    if tier == "3" or obj.get("open_problem_flag") is True or "FRONTIER" in status or "CONTESTED" in status:
        return "frontier_not_closed"
    if "CONDITIONAL" in status or "conditional" in tier:
        return "conditional_not_unconditional"
    if any(tok in status for tok in BAD_STATUS_TOKENS):
        return "not_computed"
    if status.startswith("VERIFIED") or status.startswith("CERTIFIED") or obj.get("fully_certified") is True:
        return "closed"
    return "not_computed"


def main() -> int:
    records = []
    for cid, filename in EXPECTED.items():
        obj = load(filename)
        cls = classify(obj)
        records.append({
            "id": cid,
            "file": filename,
            "name": obj.get("name"),
            "tier": obj.get("tier"),
            "status": obj.get("status"),
            "fully_certified": obj.get("fully_certified"),
            "classification": cls,
            "closure_action": obj.get("closure_action"),
            "scope": obj.get("scope"),
        })

    closed = [r for r in records if r["classification"] == "closed"]
    not_closed = [r for r in records if r["classification"] != "closed"]
    report = {
        "schema_version": "UGCT_ALL_15_CLOSEOUT_V1",
        "status": "ALL_15_CLOSED" if not not_closed else "ALL_15_NOT_CLOSED",
        "closed_count": len(closed),
        "not_closed_count": len(not_closed),
        "closed_ids": [r["id"] for r in closed],
        "not_closed_ids": [r["id"] for r in not_closed],
        "honesty_rule": "The workflow must not report full Principia closure while any item remains READY, SPECIFIED, HPC/external, frontier, or conditional.",
        "records": records,
    }
    out = DATA / "ALL_15_CLOSEOUT_REPORT.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    if not_closed:
        raise SystemExit("ALL_15_NOT_CLOSED: see data_room/data/ALL_15_CLOSEOUT_REPORT.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
