#!/usr/bin/env python3
"""Strict UGCT full-payload validator.

Corrected mode: if data/full_payload_manifest_v7.json is present, validate the
uploaded data-room manifest instead of treating the repo's transient data/
folder as empty. This distinguishes:
  (1) missing payload files, from
  (2) present but not certificate-grade payload files.
"""
import json, re, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

MANIFEST = ROOT / "data" / "full_payload_manifest_v7.json"
CERTIFIED_OK = re.compile(r"FULL|VERIFIED|concrete_matrix_provided|schema_complete$|proof_file_present", re.I)
BLOCKER = re.compile(r"PARTIAL|CANDIDATE|EXTERNAL|HPC|STILL_REQUIRED|NO_FULL_TORIC_FAN|NOT_GVW_CERTIFIED|schema_complete_.*external|conditional", re.I)

if MANIFEST.exists():
    manifest = json.loads(MANIFEST.read_text())
    entries = manifest.get("entries", [])
    missing = [e for e in entries if not e.get("present_in_uploaded_data_room")]
    certificate_grade = []
    conditional = []
    blockers = []
    for e in entries:
        status = str(e.get("status") or e.get("y4_completion_status") or "")
        path = e.get("path", "")
        record = {"path": path, "status": status, "size_bytes": e.get("size_bytes")}
        if path == "data/prime_race_density_certificate.json" or "CONDITIONAL" in status.upper():
            conditional.append(record)
        elif BLOCKER.search(status) or e.get("contains_external_markers"):
            blockers.append(record)
        elif CERTIFIED_OK.search(status):
            certificate_grade.append(record)
        else:
            blockers.append(record | {"reason": "unrecognized_status"})

    # Y4 special check: the data room has a tensor-like object, but its own
    # status says it is partial without full toric fan / resolved chamber.
    y4_entries = [e for e in entries if e.get("path") == "data/y4_intersection_ring.json"]
    y4_status = y4_entries[0].get("y4_completion_status") if y4_entries else "MISSING"
    y4_full_verified = y4_status == "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED"

    status = "FULL_PAYLOAD_VERIFIED" if not missing and not blockers and y4_full_verified else "DATA_ROOM_PRESENT__FULL_PAYLOAD_NOT_VERIFIED"
    report = {
        "status": status,
        "mode": "uploaded_data_room_manifest_v7",
        "source_zip": manifest.get("source_zip"),
        "total_entries": len(entries),
        "missing_count": len(missing),
        "certificate_grade_count": len(certificate_grade),
        "conditional_count": len(conditional),
        "blocker_count": len(blockers),
        "y4_full_verified": y4_full_verified,
        "y4_completion_status": y4_status,
        "missing": missing,
        "certificate_grade": certificate_grade,
        "conditional": conditional,
        "blockers": blockers,
        "sha256_manifest": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
    }
else:
    report = {
        "status": "NO_DATA_ROOM_MANIFEST_FOUND",
        "mode": "repo_local_strict",
        "missing_count": 1,
        "missing": ["data/full_payload_manifest_v7.json"],
    }

(REPORTS / "full_payload_validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps({k: report[k] for k in ["status","mode","total_entries","missing_count","certificate_grade_count","conditional_count","blocker_count","y4_full_verified"] if k in report}, indent=2, sort_keys=True))
