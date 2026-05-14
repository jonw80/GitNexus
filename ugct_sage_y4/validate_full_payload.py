#!/usr/bin/env python3
"""Strict UGCT full-payload validator.

This script is intentionally conservative. It only authorizes FULL_PAYLOAD_VERIFIED
when the repository contains a complete chamber-specific Y4 tensor and all declared
external/interval/proof certificates with no placeholder/blocker markers.
"""
import json, os, re, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

BLOCKER_PATTERNS = re.compile(r"BLOCKED|UNSUPPORTED|PENDING|PLACEHOLDER|TO_BE_FIXED|EXTERNAL_REQUIRED|NOT_SUPPLIED|schema_complete|external", re.I)

required = {
    "data/y4_intersection_ring_full.json": ["status", "basis", "quadruple_intersections", "checks"],
    "data/flux_scan.csv": None,
    "data/pf_basis.json": ["status"],
    "data/symplectic_pairing.json": ["status"],
    "data/attractor_intervals.json": ["status"],
    "data/axio_dilaton_interval.json": ["status", "tau_interval", "g_s_interval"],
    "data/instanton_divisors.json": ["status", "divisors"],
    "data/hidden_sector_ranks.json": ["status", "ranks"],
    "data/pfaffian_prefactors.json": ["status", "prefactors"],
    "data/racetrack_superpotential.json": ["status", "terms"],
    "data/string_loop_coefficients.json": ["status", "coefficients"],
    "data/kahler_stabilization_certificate.json": ["status", "interval_box", "krawczyk_certificate"],
    "data/uplift_source.json": ["status", "mechanism"],
    "data/warp_factor_certificate.json": ["status", "warp_factor_interval"],
    "data/uplift_backreaction_certificate.json": ["status", "backreaction_bound"],
    "data/cosmological_constant_error_budget.json": ["status", "rho_lambda_interval"],
    "data/cp_trace_anomaly_certificate.json": ["status", "c_p_interval", "scheme"],
    "data/prime_race_density_interval.json": ["status", "delta_interval"],
    "proofs/global_arithmetic_id_certificate.tex": None,
    "proofs/determinant_normalization.tex": None,
    "proofs/hadamard_divisor_equivalence.tex": None,
}

missing = []
schema_fail = []
placeholder_fail = []
hashes = {}

for rel, keys in required.items():
    p = ROOT / rel
    if not p.exists():
        missing.append(rel)
        continue
    data = p.read_bytes()
    hashes[rel] = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8", errors="ignore")
    if BLOCKER_PATTERNS.search(text):
        placeholder_fail.append(rel)
    if keys is not None:
        try:
            obj = json.loads(text)
        except Exception as e:
            schema_fail.append({"file": rel, "reason": f"not_json: {e}"})
            continue
        for k in keys:
            if k not in obj:
                schema_fail.append({"file": rel, "reason": f"missing_key:{k}"})

# Extra acceptance checks for the full Y4 tensor if present.
y4_checks = []
y4_path = ROOT / "data/y4_intersection_ring_full.json"
if y4_path.exists():
    try:
        y4 = json.loads(y4_path.read_text())
        checks = y4.get("checks", {})
        q = y4.get("quadruple_intersections", {})
        if y4.get("status") != "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED":
            y4_checks.append("status_not_FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED")
        if checks.get("A4_cartan") is not True:
            y4_checks.append("A4_cartan_check_not_true")
        if checks.get("chi_Y4") != 1056:
            y4_checks.append("chi_Y4_not_1056")
        if checks.get("tadpole") != 44:
            y4_checks.append("tadpole_not_44")
        if not isinstance(q, dict) or len(q) == 0:
            y4_checks.append("quadruple_intersections_empty")
    except Exception as e:
        y4_checks.append(f"y4_parse_error:{e}")

status = "FULL_PAYLOAD_VERIFIED" if not (missing or schema_fail or placeholder_fail or y4_checks) else "FULL_PAYLOAD_NOT_VERIFIED"
report = {
    "status": status,
    "missing_count": len(missing),
    "schema_fail_count": len(schema_fail),
    "placeholder_fail_count": len(placeholder_fail),
    "y4_check_fail_count": len(y4_checks),
    "missing": missing,
    "schema_fail": schema_fail,
    "placeholder_fail": placeholder_fail,
    "y4_check_fail": y4_checks,
    "sha256": hashes,
}
(REPORTS / "full_payload_validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps({k: report[k] for k in ["status","missing_count","schema_fail_count","placeholder_fail_count","y4_check_fail_count","missing"]}, indent=2, sort_keys=True))
# Do not fail the GitHub job; the report itself controls manuscript upgrade.
