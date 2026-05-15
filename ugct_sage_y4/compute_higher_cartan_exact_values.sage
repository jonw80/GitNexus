# UGCT exact higher-Cartan Ewx self-intersection computation harness
# Runs under SageMath.
#
# This file is intentionally strict. It computes/populates the final 235
# higher-Cartan values only from a complete resolved Esole-Yau Ewx ambient
# Chow presentation, not from fallback zero assignments.
#
# Required input:
#   data/esole_yau_ewx_resolved_ambient_chow.json
#
# It must contain an `exact_higher_cartan_computation` block with:
#   status: RESOLVED_EWX_HIGHER_CARTAN_INPUT_VERIFIED
#   variables: [...]
#   quotient_ideal_generators: [...]
#   divisor_lifts: {R,H,E1..E8,C1..C4: polynomial strings}
#   integration_functional.top_monomial_values: {...}
#   provenance: {toolchain, toolchain_version, source_geometry,
#                sr_linear_ideal_hash, proper_transform_hash,
#                script_hash, independent_rerun_hash}
#
# Output:
#   data/higher_cartan_closure_rules.json
#   reports/higher_cartan_exact_computation_report.json

import itertools
import json
from fractions import Fraction
from pathlib import Path

from sage.all import PolynomialRing, QQ

DATA = Path("data")
REPORTS = Path("reports")
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
CHOW = DATA / "esole_yau_ewx_resolved_ambient_chow.json"
OUT = DATA / "higher_cartan_closure_rules.json"
REPORT = REPORTS / "higher_cartan_exact_computation_report.json"

BASIS = ["R", "H"] + [f"E{i}" for i in range(1, 9)] + [f"C{i}" for i in range(1, 5)]
BASE = {"R", "H"} | {f"E{i}" for i in range(1, 9)}
CARTAN = {f"C{i}" for i in range(1, 5)}
ORDER = {d: i for i, d in enumerate(["R", "H"] + [f"E{i}" for i in range(1,9)] + ["Z"] + [f"C{i}" for i in range(1,5)])}
REQ_PROV = ["toolchain", "toolchain_version", "source_geometry", "sr_linear_ideal_hash", "proper_transform_hash", "script_hash", "independent_rerun_hash"]

def ckey(parts):
    return ",".join(sorted(parts, key=lambda x: ORDER.get(x, 999)))

def required_keys():
    keys = []
    for D in sorted(BASE, key=lambda x: ORDER[x]):
        for c in itertools.combinations_with_replacement(sorted(CARTAN, key=lambda x: ORDER[x]), 3):
            keys.append(ckey([D] + list(c)))
    for c in itertools.combinations_with_replacement(sorted(CARTAN, key=lambda x: ORDER[x]), 4):
        keys.append(ckey(list(c)))
    return keys

def fail(reason, extra=None):
    report = {
        "status": "EXACT_HIGHER_CARTAN_COMPUTATION_NOT_RUN",
        "reason": reason,
        "required_values": 235,
        "output": str(OUT)
    }
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
        mon = "*".join(parts) if parts else "1"
        if mon not in top_values:
            raise KeyError("No integration value for normal-form top monomial %s" % mon)
        total += Fraction(str(coeff)) * Fraction(str(top_values[mon]))
    return total

if not CHOW.exists():
    fail("Missing resolved ambient Chow input file", {"missing_file": str(CHOW)})

chow = json.loads(CHOW.read_text())
comp = chow.get("exact_higher_cartan_computation")
if not comp:
    fail("No exact_higher_cartan_computation block is present in the Chow input file.")
if comp.get("status") != "RESOLVED_EWX_HIGHER_CARTAN_INPUT_VERIFIED":
    fail("exact_higher_cartan_computation.status is not RESOLVED_EWX_HIGHER_CARTAN_INPUT_VERIFIED", {"actual_status": comp.get("status")})

missing = [k for k in ["variables", "quotient_ideal_generators", "divisor_lifts", "integration_functional", "provenance"] if k not in comp]
if missing:
    fail("exact_higher_cartan_computation lacks required keys", {"missing_keys": missing})
prov = comp.get("provenance", {})
missing_prov = [k for k in REQ_PROV if not prov.get(k)]
if missing_prov:
    fail("Exact computation provenance is incomplete", {"missing_provenance": missing_prov})

variables = comp["variables"]
if not variables:
    fail("No polynomial variables supplied")
R = PolynomialRing(QQ, variables, order="degrevlex")
names = {str(v): g for v, g in zip(variables, R.gens())}
names["ONE"] = R(1)
names["__varlist__"] = variables

lifts = comp["divisor_lifts"]
missing_lifts = [d for d in BASIS if d not in lifts]
if missing_lifts:
    fail("Missing divisor lifts for required basis divisors", {"missing_lifts": missing_lifts})

ideal_exprs = comp.get("quotient_ideal_generators", [])
if not ideal_exprs:
    fail("No quotient ideal generators supplied")
try:
    ideal = R.ideal([sage_eval(e, names) for e in ideal_exprs])
    gb = ideal.groebner_basis()
except Exception as exc:
    fail("Could not build Groebner basis", {"exception": str(exc)})

top_values = comp.get("integration_functional", {}).get("top_monomial_values", {})
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
    report = {
        "status": "EXACT_HIGHER_CARTAN_COMPUTATION_INCOMPLETE",
        "computed_count": len(values),
        "error_count": len(errors),
        "error_sample": dict(list(errors.items())[:50])
    }
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
    "computed_by": "compute_higher_cartan_exact_values.sage",
    "value_count": len(values)
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
report = {
    "status": "EXACT_HIGHER_CARTAN_COMPUTATION_COMPLETED",
    "computed_count": len(values),
    "output": str(OUT),
    "provenance": prov
}
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
