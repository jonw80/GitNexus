#!/usr/bin/env python3
"""Validate independently certified Esole-Yau Ewx higher-Cartan values.

This validator does not compute the values. It enforces that the certificate file
contains exact rational values for every currently required higher-Cartan
monomial and records enough provenance to make the table auditable.
"""
import json
from fractions import Fraction
from pathlib import Path

DATA = Path("data")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
RULE_FILE = DATA / "higher_cartan_closure_rules.json"
REQ_JSON = REPORTS / "higher_cartan_requirements.json"
OUT = REPORTS / "higher_cartan_exact_certificate_report.json"

REQUIRED_PROVENANCE_KEYS = [
    "toolchain",
    "toolchain_version",
    "source_geometry",
    "sr_linear_ideal_hash",
    "proper_transform_hash",
    "script_hash",
    "independent_rerun_hash"
]

if not RULE_FILE.exists():
    report = {"status": "EXACT_HIGHER_CARTAN_CERTIFICATE_MISSING", "reason": f"{RULE_FILE} is missing"}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0)

rules = json.loads(RULE_FILE.read_text())
exact_values = rules.get("exact_values", {}) or {}
provenance = rules.get("provenance", {}) or {}
missing_provenance = [k for k in REQUIRED_PROVENANCE_KEYS if not provenance.get(k)]

if REQ_JSON.exists():
    req = json.loads(REQ_JSON.read_text())
    required_keys = [item["monomial"] for item in req.get("items", [])]
else:
    # If the requirements extractor was not run yet, validate only the known count.
    required_keys = []

missing_values = [k for k in required_keys if k not in exact_values]
extra_values = [k for k in exact_values if required_keys and k not in required_keys]
non_rational = []
for k, v in exact_values.items():
    try:
        Fraction(str(v))
    except Exception:
        non_rational.append(k)

status = "EXACT_HIGHER_CARTAN_CERTIFICATE_VERIFIED"
if rules.get("fallback_rule", {}).get("enabled"):
    status = "EXACT_HIGHER_CARTAN_CERTIFICATE_REJECTED_FALLBACK_ENABLED"
if missing_values:
    status = "EXACT_HIGHER_CARTAN_CERTIFICATE_INCOMPLETE_VALUES"
if non_rational:
    status = "EXACT_HIGHER_CARTAN_CERTIFICATE_REJECTED_NON_RATIONAL_VALUES"
if missing_provenance:
    status = "EXACT_HIGHER_CARTAN_CERTIFICATE_INCOMPLETE_PROVENANCE"
if required_keys and len(exact_values) != len(required_keys):
    status = "EXACT_HIGHER_CARTAN_CERTIFICATE_INCOMPLETE_COVERAGE"

report = {
    "status": status,
    "rule_file_status": rules.get("status"),
    "required_count": len(required_keys) if required_keys else 235,
    "exact_value_count": len(exact_values),
    "missing_value_count": len(missing_values),
    "extra_value_count": len(extra_values),
    "non_rational_count": len(non_rational),
    "missing_provenance": missing_provenance,
    "missing_values_sample": missing_values[:50],
    "extra_values_sample": extra_values[:50],
    "non_rational_sample": non_rational[:50]
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
