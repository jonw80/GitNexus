# Export exact Esole-Yau Ewx higher-Cartan values from a complete resolved presentation.
# Runs under SageMath.
#
# Input:
#   data/ewx_resolved_presentation_input.json
#
# Output:
#   data/higher_cartan_closure_rules.json
#   reports/ewx_resolved_presentation_export_report.json

import itertools
import json
from fractions import Fraction
from pathlib import Path
from sage.all import PolynomialRing, QQ

DATA = Path("data")
REPORTS = Path("reports")
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
INP = DATA / "ewx_resolved_presentation_input.json"
OUT = DATA / "higher_cartan_closure_rules.json"
REPORT = REPORTS / "ewx_resolved_presentation_export_report.json"

BASE = ["R", "H"] + [f"E{i}" for i in range(1, 9)]
CARTAN = [f"C{i}" for i in range(1, 5)]
ORDER = {d: i for i, d in enumerate(BASE + ["Z"] + CARTAN)}
REQ_PROV = ["toolchain", "toolchain_version", "source_geometry", "sr_linear_ideal_hash", "proper_transform_hash", "script_hash", "independent_rerun_hash"]

def ckey(parts):
    return ",".join(sorted(parts, key=lambda x: ORDER.get(x, 999)))

def required_keys():
    keys = []
    for d in BASE:
        for c in itertools.combinations_with_replacement(CARTAN, 3):
            keys.append(ckey([d] + list(c)))
    for c in itertools.combinations_with_replacement(CARTAN, 4):
        keys.append(ckey(list(c)))
    return keys

def fail(reason, extra=None):
    report = {"status": "EWX_RESOLVED_PRESENTATION_EXPORT_NOT_RUN", "reason": reason, "required_count": 235}
    if extra:
        report.update(extra)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0)

def sage_eval(expr, names):
    return eval(expr, {"__builtins__": {}}, names)

def integrate(poly, top_values, names):
    total = Fraction(0)
    for exp, coeff in poly.dict().items():
        parts = []
        for var, power in zip(names["__varlist__"], exp):
            parts.extend([var] * int(power))
        key = "*".join(parts) if parts else "1"
        if key not in top_values:
            raise KeyError("No top integration value for normal-form monomial %s" % key)
        total += Fraction(str(coeff)) * Fraction(str(top_values[key]))
    return total

if not INP.exists():
    fail("Missing input file", {"missing_file": str(INP)})

inp = json.loads(INP.read_text())
if inp.get("status") != "RESOLVED_EWX_PRESENTATION_VERIFIED":
    fail("Input status is not RESOLVED_EWX_PRESENTATION_VERIFIED", {"actual_status": inp.get("status")})

missing = [k for k in ["variables", "quotient_ideal_generators", "divisor_lifts", "integration_functional", "provenance"] if k not in inp]
if missing:
    fail("Input lacks required keys", {"missing_keys": missing})
prov = inp.get("provenance", {})
missing_prov = [k for k in REQ_PROV if not prov.get(k)]
if missing_prov:
    fail("Missing provenance fields", {"missing_provenance": missing_prov})

variables = inp["variables"]
if not variables:
    fail("No polynomial variables supplied")
R = PolynomialRing(QQ, variables, order="degrevlex")
names = {str(v): g for v, g in zip(variables, R.gens())}
names["ONE"] = R(1)
names["__varlist__"] = variables

lifts = inp["divisor_lifts"]
missing_lifts = [d for d in BASE + CARTAN if d not in lifts]
if missing_lifts:
    fail("Missing divisor lifts", {"missing_lifts": missing_lifts})

ideal_exprs = inp.get("quotient_ideal_generators", [])
if not ideal_exprs:
    fail("No quotient ideal generators supplied")
try:
    ideal = R.ideal([sage_eval(expr, names) for expr in ideal_exprs])
    gb = ideal.groebner_basis()
except Exception as exc:
    fail("Could not build quotient ideal/Groebner basis", {"exception": str(exc)})

top_values = inp.get("integration_functional", {}).get("top_monomial_values", {})
if not top_values:
    fail("No top_monomial_values supplied")

values = {}
errors = {}
for key in required_keys():
    try:
        poly = names["ONE"]
        for d in key.split(","):
            poly *= sage_eval(lifts[d], names)
        normal = poly.reduce(gb)
        val = integrate(normal, top_values, names)
        values[key] = int(val) if val.denominator == 1 else str(val)
    except Exception as exc:
        errors[key] = str(exc)

if errors:
    report = {"status": "EWX_RESOLVED_PRESENTATION_EXPORT_INCOMPLETE", "computed_count": len(values), "error_count": len(errors), "error_sample": dict(list(errors.items())[:50])}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0)

out = {
    "schema_version": "UGCT_HIGHER_CARTAN_CLOSURE_RULES_V3",
    "status": "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED",
    "resolution_chamber": "Esole-Yau Ewx",
    "exact_values": values,
    "fallback_rule": {"enabled": False, "name": "NO_FALLBACK_FOR_CERTIFICATION"},
    "provenance": prov,
    "computed_by": "export_higher_cartan_from_resolved_presentation.sage",
    "value_count": len(values)
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
report = {"status": "EWX_RESOLVED_PRESENTATION_EXPORT_COMPLETED", "computed_count": len(values), "output": str(OUT), "provenance": prov}
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
