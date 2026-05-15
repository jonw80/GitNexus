#!/usr/bin/env python3
"""Extract the remaining higher-Cartan intersection requirements.

Reads data/esole_yau_exceptional_reduction_rules.json after the Chow reducer runs
and writes exact residual ledgers for the unresolved exceptional sector.
"""
import csv
import json
from pathlib import Path

DATA = Path("data")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
RULES = DATA / "esole_yau_exceptional_reduction_rules.json"
OUT_JSON = REPORTS / "higher_cartan_requirements.json"
OUT_CSV = REPORTS / "higher_cartan_requirements.csv"
OUT_MD = REPORTS / "higher_cartan_requirements.md"

CARTAN = {"C1", "C2", "C3", "C4"}
BASE = {"R", "H"} | {f"E{i}" for i in range(1, 9)}
ZERO = {"Z"}

def classify(parts):
    cart = [p for p in parts if p in CARTAN]
    base = [p for p in parts if p in BASE]
    zero = [p for p in parts if p in ZERO]
    if len(parts) != 4:
        return "not_degree_four"
    if len(cart) == 3 and len(base) == 1:
        return "base_triple_cartan"
    if len(cart) == 4:
        return "quadruple_cartan"
    if len(cart) == 2 and len(base) == 1 and len(zero) == 1:
        return "base_zero_pair_cartan"
    if len(cart) == 2 and len(base) == 2:
        return "base_pair_cartan"
    return "other_exceptional_residual"

if not RULES.exists():
    report = {
        "status": "NO_RULE_FILE",
        "reason": f"{RULES} does not exist yet"
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True))
    OUT_MD.write_text("# Higher-Cartan requirements\n\nNo rule file exists yet.\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0)

obj = json.loads(RULES.read_text())
required = obj.get("required_rules", {}) or {}
rows = []
counts = {}
for key in sorted(required):
    parts = [p.strip() for p in key.split(",") if p.strip()]
    cls = classify(parts)
    counts[cls] = counts.get(cls, 0) + 1
    rows.append({
        "monomial": key,
        "classification": cls,
        "cartan_count": sum(1 for p in parts if p in CARTAN),
        "base_count": sum(1 for p in parts if p in BASE),
        "zero_count": sum(1 for p in parts if p in ZERO),
        "required_value": required[key]
    })

report = {
    "status": "HIGHER_CARTAN_REQUIREMENTS_EXTRACTED" if rows else "NO_REMAINING_HIGHER_CARTAN_REQUIREMENTS",
    "source_rule_file_status": obj.get("status"),
    "source_rule_count": obj.get("rule_count"),
    "source_required_rule_count": obj.get("required_rule_count"),
    "remaining_count": len(rows),
    "classification_counts": counts,
    "items": rows
}
OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True))
with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["monomial", "classification", "cartan_count", "base_count", "zero_count", "required_value"])
    w.writeheader()
    w.writerows(rows)

lines = ["# Higher-Cartan residual requirements", "", f"Status: `{report['status']}`", f"Remaining count: `{len(rows)}`", "", "## Classification counts", ""]
for k, v in sorted(counts.items()):
    lines.append(f"- `{k}`: `{v}`")
lines.extend(["", "## First 100 requirements", ""])
for row in rows[:100]:
    lines.append(f"- `{row['monomial']}` — `{row['classification']}`")
OUT_MD.write_text("\n".join(lines) + "\n")
print(json.dumps({k: report[k] for k in ["status", "remaining_count", "classification_counts"]}, indent=2, sort_keys=True))
