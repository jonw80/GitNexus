#!/usr/bin/env python3
"""Extract the standard A4/SU(5) Tate model data from IntersectionNumbers.m.

Mathics is not reliable enough to run the full pushforward algorithm from the
public Mathematica package, but it can usually evaluate the simple structural
functions:

  generators[{a,4}], hypersurface[{a,4}], divisors[{a,4}]

This script writes those three expressions to JSON so the native Sage backend can
perform the actual pushforward/intersection computation without relying on
Mathics' implementation of Limit/Fold/Monitor/Subscript internals.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

DATA = Path("data")
REPORTS = Path("reports")
SOURCES = Path("sources")
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
PKG = SOURCES / "IntersectionNumbers.m"
OUT = DATA / "intersectionnumbers_a4_model.json"
REPORT = REPORTS / "intersectionnumbers_a4_model_extract_report.json"

MATHICS_SPEC = "mathics3<10"
SETUPTOOLS_SPEC = "setuptools<81"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def write(obj):
    REPORT.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps(obj, indent=2, sort_keys=True))

def install_mathics():
    cmds = [[sys.executable, "-m", "pip", "install", "--no-input", SETUPTOOLS_SPEC, MATHICS_SPEC]]
    sage = shutil.which("sage")
    if sage:
        cmds.append([sage, "-pip", "install", "--no-input", SETUPTOOLS_SPEC, MATHICS_SPEC])
    errors = []
    for cmd in cmds:
        try:
            subprocess.check_call(cmd)
            return None
        except Exception as exc:
            errors.append({"command": cmd, "error": str(exc)})
    return errors

def import_session():
    try:
        import pkg_resources  # noqa: F401
        from mathics.session import MathicsSession
        return MathicsSession, None
    except Exception as first:
        errors = install_mathics()
        try:
            import pkg_resources  # noqa: F401
            from mathics.session import MathicsSession
            return MathicsSession, None
        except Exception as second:
            return None, {"initial": str(first), "install_errors": errors, "post_install": str(second)}

def as_string(x):
    s = str(x)
    if hasattr(x, "to_python"):
        try:
            y = x.to_python()
            if isinstance(y, str):
                return y
        except Exception:
            pass
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

if not PKG.exists():
    write({"status": "A4_MODEL_EXTRACT_NOT_RUN", "reason": "sources/IntersectionNumbers.m missing"})
    raise SystemExit(0)

MathicsSession, err = import_session()
if MathicsSession is None:
    write({"status": "A4_MODEL_EXTRACT_NOT_RUN", "reason": "Mathics import failed", "error": err})
    raise SystemExit(0)

try:
    session = MathicsSession()
except Exception as exc:
    write({"status": "A4_MODEL_EXTRACT_NOT_RUN", "reason": "MathicsSession startup failed", "error": repr(exc)})
    raise SystemExit(0)

def ev(code):
    return session.evaluate(code)

def evs(expr):
    # Try qualified package symbols first, then unqualified symbols.
    for candidate in [expr, expr.replace("IntersectionNumbers`", "")]:
        try:
            val = ev(f"ToString[InputForm[{candidate}]]")
            return as_string(val)
        except Exception:
            continue
    raise RuntimeError(f"Could not evaluate {expr}")

workdir = Path.cwd().resolve().as_posix()
pkg = PKG.resolve().as_posix()
try:
    ev(f'SetDirectory["{workdir}"]; Get["{pkg}"];')
    generators = evs("IntersectionNumbers`generators[{a,4}]")
    hypersurface = evs("IntersectionNumbers`hypersurface[{a,4}]")
    divisors = evs("IntersectionNumbers`divisors[{a,4}]")
    cartan_len = evs("Length[IntersectionNumbers`divisors[{a,4}]]")
except Exception as exc:
    write({
        "status": "A4_MODEL_EXTRACT_FAILED",
        "reason": "Package loaded but A4 structural functions could not be evaluated",
        "error": str(exc),
        "package_sha256": sha256_file(PKG)
    })
    raise SystemExit(0)

out = {
    "schema_version": "INTERSECTIONNUMBERS_A4_MODEL_V1",
    "status": "INTERSECTIONNUMBERS_A4_MODEL_EXTRACTED",
    "algebra_rank": "A4 / SU(5)",
    "generators_inputform": generators,
    "hypersurface_inputform": hypersurface,
    "divisors_inputform": divisors,
    "cartan_length": cartan_len,
    "source_package": "Jefferson-Turner IntersectionNumbers.m, arXiv:2206.11527 ancillary",
    "source_package_sha256": sha256_file(PKG),
    "extracted_by": "extract_intersectionnumbers_a4_model.py"
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
write({
    "status": "INTERSECTIONNUMBERS_A4_MODEL_EXTRACTED",
    "output": str(OUT),
    "cartan_length": cartan_len,
    "package_sha256": sha256_file(PKG),
    "generators_preview": generators[:500],
    "hypersurface": hypersurface,
    "divisors": divisors
})
