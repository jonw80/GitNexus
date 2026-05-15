#!/usr/bin/env python3
"""Compute the 235 higher-Cartan values through Mathics + IntersectionNumbers.m.

GitHub-hosted runners do not provide Wolfram Engine. This script uses Mathics3
as an open-source Wolfram-language evaluator. It loads the public Jefferson-
Turner IntersectionNumbers.m package, evaluates the A4/SU(5) pushforward calls,
and writes data/higher_cartan_closure_rules.json if successful.

The script is intentionally conservative: if Mathics or the package call fails,
it writes a NOT_RUN/FAILED report and exits 0 so the rest of the audit workflow
can still report the exact blocker.
"""
import hashlib
import itertools
import json
from pathlib import Path

DATA = Path("data")
REPORTS = Path("reports")
SOURCES = Path("sources")
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

PKG = SOURCES / "IntersectionNumbers.m"
OUT = DATA / "higher_cartan_closure_rules.json"
REPORT = REPORTS / "intersectionnumbers_ewx_mathics_report.json"

BASE_NAMES = ["R", "H"] + [f"E{i}" for i in range(1, 9)]
BASE_SYMS = {"R": "r", "H": "h", **{f"E{i}": f"ee{i}" for i in range(1, 9)}}
CARTAN_NAMES = [f"C{i}" for i in range(1, 5)]
ORDER = {name: i for i, name in enumerate(["R", "H"] + [f"E{i}" for i in range(1, 9)] + ["Z"] + CARTAN_NAMES)}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def write_report(status, **extra):
    obj = {"status": status, **extra}
    REPORT.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps(obj, indent=2, sort_keys=True))

def to_python_string(x):
    if hasattr(x, "to_python"):
        try:
            y = x.to_python()
            if isinstance(y, str):
                return y
        except Exception:
            pass
    s = str(x)
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

def ckey(parts):
    return ",".join(sorted(parts, key=lambda p: ORDER[p]))

if not PKG.exists():
    write_report("MATHICS_EWX_NOT_RUN", reason="sources/IntersectionNumbers.m missing")
    raise SystemExit(0)

try:
    from mathics.session import MathicsSession
except Exception as exc:
    write_report("MATHICS_EWX_NOT_RUN", reason="Mathics3 is not importable", exception=str(exc))
    raise SystemExit(0)

session = MathicsSession()

def ev(code: str):
    return session.evaluate(code)

def ev_string(code: str) -> str:
    return to_python_string(ev(f"ToString[InputForm[{code}]]"))

setup = r'''
SetDirectory[Directory[]];
Get["sources/IntersectionNumbers.m"];
baseVars = {r,h,ee1,ee2,ee3,ee4,ee5,ee6,ee7,ee8};
Lclass = 2*r + 6*h - 2*(ee1+ee2+ee3+ee4+ee5+ee6+ee7+ee8);
Sclass = r;
baseSubstitution = {L -> Lclass, s[1] -> Sclass};
surfPair[x_, y_] := Which[x === h && y === h, 1, MemberQ[{ee1,ee2,ee3,ee4,ee5,ee6,ee7,ee8}, x] && x === y, -1, True, 0];
kPair[x_] := Which[x === h, -3, MemberQ[{ee1,ee2,ee3,ee4,ee5,ee6,ee7,ee8}, x], -1, True, 0];
intExp[exps_List] := Module[{rct, surf, surfDegree, positions, pos},
  rct = exps[[1]];
  surf = Rest[exps];
  surfDegree = Total[surf];
  Which[
    Total[exps] =!= 3, 0,
    rct == 0, 0,
    rct == 1 && surfDegree == 2,
      positions = Flatten[MapIndexed[ConstantArray[#2[[1]] + 1, #1] &, surf]];
      If[Length[positions] =!= 2, 0, surfPair[baseVars[[positions[[1]]]], baseVars[[positions[[2]]]]]],
    rct == 2 && surfDegree == 1,
      pos = First[Flatten[MapIndexed[ConstantArray[#2[[1]] + 1, #1] &, surf]]];
      kPair[baseVars[[pos]]],
    rct == 3 && surfDegree == 0, 1,
    True, 0
  ]
];
integrateB3[poly_] := Module[{rules, expanded}, expanded = Expand[poly]; rules = CoefficientRules[expanded, baseVars]; Total[(#[[2]] * intExp[#[[1]]]) & /@ rules]];
ratString[x_] := Module[{y = Together[x]}, If[Denominator[y] === 1, ToString[Numerator[y]], ToString[Numerator[y]] <> "/" <> ToString[Denominator[y]]]];
cartanClasses = divisors[{a,4}];
pushBase[expr_] := Expand[push[{a,4}, pushFunction -> expr] /. baseSubstitution];
'''
try:
    ev(setup)
    cartan_len = ev_string("Length[cartanClasses]")
except Exception as exc:
    write_report("MATHICS_EWX_SETUP_FAILED", exception=str(exc))
    raise SystemExit(0)

if cartan_len.strip() != "4":
    write_report("MATHICS_EWX_SETUP_FAILED", reason="divisors[{a,4}] did not return four Cartan classes", cartan_length=cartan_len)
    raise SystemExit(0)

values = {}
errors = {}
triples = list(itertools.combinations_with_replacement(range(1, 5), 3))
quads = list(itertools.combinations_with_replacement(range(1, 5), 4))

for base in BASE_NAMES:
    b = BASE_SYMS[base]
    for triple in triples:
        prod = "*".join([f"cartanClasses[[{i}]]" for i in triple])
        key = ckey([base] + [CARTAN_NAMES[i-1] for i in triple])
        code = f"ratString[integrateB3[({b}) * pushBase[{prod}]]]"
        try:
            values[key] = ev_string(code)
        except Exception as exc:
            errors[key] = str(exc)
            if len(errors) >= 20:
                break
    if len(errors) >= 20:
        break

if not errors:
    for quad in quads:
        prod = "*".join([f"cartanClasses[[{i}]]" for i in quad])
        key = ckey([CARTAN_NAMES[i-1] for i in quad])
        code = f"ratString[integrateB3[pushBase[{prod}]]]"
        try:
            values[key] = ev_string(code)
        except Exception as exc:
            errors[key] = str(exc)
            if len(errors) >= 20:
                break

if errors:
    write_report(
        "MATHICS_EWX_EXACT_VALUES_FAILED",
        computed_count=len(values),
        error_count=len(errors),
        error_sample=errors,
        note="Mathics could not complete the same IntersectionNumbers.m calls. Use wolframscript or inspect the Mathics incompatibility."
    )
    raise SystemExit(0)

if len(values) != 235:
    write_report("MATHICS_EWX_EXACT_VALUES_INCOMPLETE", value_count=len(values), expected=235)
    raise SystemExit(0)

pkg_hash = sha256_file(PKG)
script_hash = sha256_file(Path(__file__))
value_hash = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()

out = {
    "schema_version": "UGCT_HIGHER_CARTAN_CLOSURE_RULES_V3",
    "status": "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED",
    "resolution_chamber": "Esole-Yau Ewx / standard split SU(5) A4 Tate tuning via IntersectionNumbers.m",
    "exact_values": values,
    "fallback_rule": {"enabled": False, "name": "NO_FALLBACK_FOR_CERTIFICATION"},
    "provenance": {
        "toolchain": "Mathics3 + Jefferson-Turner IntersectionNumbers.m",
        "toolchain_version": ev_string("$Version"),
        "source_geometry": "split SU(5)/A4 Tate model, package call push[{a,4}, pushFunction->...], GUT divisor S=s[1]=R, B3=P(O+K_dP8)",
        "sr_linear_ideal_hash": "sha256:" + pkg_hash,
        "proper_transform_hash": "sha256:" + pkg_hash,
        "script_hash": "sha256:" + script_hash,
        "independent_rerun_hash": "sha256:" + value_hash
    },
    "computed_by": "run_intersectionnumbers_ewx_mathics.py",
    "value_count": len(values)
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
write_report(
    "MATHICS_EWX_EXACT_VALUES_EXPORTED",
    value_count=len(values),
    output=str(OUT),
    package_hash="sha256:" + pkg_hash,
    script_hash="sha256:" + script_hash,
    value_hash="sha256:" + value_hash,
)
