#!/usr/bin/env python3
"""Build data_room/data/y4_tensor_manifest.json from the Y4 tensor that this workflow run computed.

The manifest is filled only from this run's outputs:
- the tensor file, ugct_sage_y4/data/y4_intersection_ring_full.json;
- the Sage run summary, ugct_sage_y4/reports/sage_run_summary.json (written only by run_chow_tensor.sage);
- the inputs and cross-check reports listed below;
- the GitHub run id.

Every count and hash is recomputed here. Nothing is typed in.

The tensor counts as FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED only if all three of these hold:
  1. the tensor was exported in this run and its counts are consistent;
  2. the resolved ambient Chow input declares itself complete (RESOLVED_AMBIENT_CHOW_DATA_VERIFIED,
     the status the input file itself requires for full acceptance);
  3. an independent cross-check reproduced the higher-Cartan values: the table in this run was written by an
     IntersectionNumbers run (Wolfram or Mathics), and it agrees value by value with the native Sage table,
     which the workflow keeps in ugct_sage_y4/data/higher_cartan_native_values.json before the optional runs
     (all three producers write the same file).
Otherwise the status is Y4_TENSOR_COMPUTED_NOT_INDEPENDENTLY_VERIFIED, and the reasons are listed in open_items.

The script exits 1 only when this run's outputs are missing or inconsistent.
Run from the repository root:  python3 ugct_sage_y4/build_y4_tensor_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

TENSOR = "ugct_sage_y4/data/y4_intersection_ring_full.json"
SUMMARY = "ugct_sage_y4/reports/sage_run_summary.json"
CHOW_INPUT = "ugct_sage_y4/data/esole_yau_ewx_resolved_ambient_chow.json"
EXC_RULES = "ugct_sage_y4/data/esole_yau_exceptional_reduction_rules.json"
HC_RULES = "ugct_sage_y4/data/higher_cartan_closure_rules.json"
HC_NATIVE = "ugct_sage_y4/data/higher_cartan_native_values.json"
CROSS_PRODUCERS = {"run_intersectionnumbers_ewx.wls": "wolfram", "run_intersectionnumbers_ewx_mathics.py": "mathics"}
PRODUCER_OK = {"wolfram": "INTERSECTIONNUMBERS_EWX_EXACT_VALUES_EXPORTED", "mathics": "MATHICS_EWX_EXACT_VALUES_EXPORTED"}
WOLFRAM = "ugct_sage_y4/reports/intersectionnumbers_ewx_run_report.json"
MATHICS = "ugct_sage_y4/reports/intersectionnumbers_ewx_mathics_report.json"
OUT_JSON = "data_room/data/y4_tensor_manifest.json"
OUT_TEX = "data_room/proofs/y4_tensor_reproduction_theorem.tex"
VERIFIED = "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED"
NOT_VERIFIED = "Y4_TENSOR_COMPUTED_NOT_INDEPENDENTLY_VERIFIED"
CHOW_COMPLETE = "RESOLVED_AMBIENT_CHOW_DATA_VERIFIED"


class RunOutputError(Exception):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(obj: dict) -> str:
    """Same canonical hash as data_room/scripts/verify_frontier_closeout.py."""
    tmp = dict(obj)
    tmp.pop("payload_hash", None)
    return hashlib.sha256(json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(root: Path, rel: str, required: bool):
    path = root / rel
    if not path.exists():
        if required:
            raise RunOutputError(f"missing run output {rel}")
        return None
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise RunOutputError(f"unreadable {rel}: {exc}")


def exact(v):
    try:
        return Fraction(str(v).replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def compare_tables(native, final, reports=None) -> dict:
    """Value-by-value comparison of an IntersectionNumbers higher-Cartan table with the native Sage table.

    reports maps "wolfram"/"mathics" to that run's report; the producer's report must say it exported the values.
    """
    nv = (native or {}).get("exact_values") if isinstance(native, dict) else None
    fv = (final or {}).get("exact_values") if isinstance(final, dict) else None
    nv = nv if isinstance(nv, dict) else {}
    fv = fv if isinstance(fv, dict) else {}
    producer = CROSS_PRODUCERS.get(str((final or {}).get("computed_by")))
    try:
        required = int((native or {}).get("required_value_count") or len(nv))
    except (TypeError, ValueError):
        required = len(nv)
    out = {"independent_producer": producer, "native_value_count": len(nv), "independent_value_count": len(fv) if producer else 0,
           "required_value_count": required, "mismatch_count": None, "mismatch_sample": [], "passed": False}
    if producer is None or not nv:
        return out
    status = ((reports or {}).get(producer) or {}).get("status")
    out["producer_report_status"] = status
    if status != PRODUCER_OK[producer]:
        out["mismatch_count"] = None
        return out
    keys = sorted(set(nv) | set(fv))
    mism = [k for k in keys if k not in nv or k not in fv or exact(nv[k]) is None or exact(nv[k]) != exact(fv[k])]
    out["mismatch_count"] = len(mism)
    out["mismatch_sample"] = mism[:10]
    out["passed"] = required > 0 and len(nv) >= required and len(fv) >= required and not mism
    return out


def build(root: Path, env: dict) -> tuple[dict, str]:
    tensor = load(root, TENSOR, True)
    summary = load(root, SUMMARY, True)
    chow = load(root, CHOW_INPUT, False) or {}
    exc = load(root, EXC_RULES, False) or {}
    hc = load(root, HC_RULES, False) or {}
    native = load(root, HC_NATIVE, False)
    wolfram = load(root, WOLFRAM, False)
    mathics = load(root, MATHICS, False)

    basis = tensor.get("basis")
    entries = tensor.get("quadruple_intersections")
    if not isinstance(basis, list) or not basis or not isinstance(entries, dict):
        raise RunOutputError("tensor file has no basis or no quadruple_intersections table")
    nonzero = {k: v for k, v in entries.items() if str(v) not in ("0", "0/1")}
    total = comb(len(basis) + 3, 4)
    problems = []
    if summary.get("nonzero_exported") != len(nonzero):
        problems.append(f"summary nonzero_exported {summary.get('nonzero_exported')} != {len(nonzero)} entries in the tensor file")
    if summary.get("total_symmetric_multisets_degree4") not in (None, total):
        problems.append(f"summary multiset count {summary.get('total_symmetric_multisets_degree4')} != C({len(basis)}+3, 4) = {total}")
    zero = summary.get("zero_multisets")
    if zero is not None and zero + len(nonzero) != total:
        problems.append(f"zero {zero} + nonzero {len(nonzero)} != {total}")
    bad_keys = [k for k in nonzero if len(k.split(",")) != 4 or any(x not in basis for x in k.split(","))]
    if bad_keys:
        problems.append(f"{len(bad_keys)} tensor keys are not degree-four monomials in the basis, e.g. {bad_keys[:3]}")
    if problems:
        raise RunOutputError("; ".join(problems))

    comparison = compare_tables(native, hc, {"wolfram": wolfram, "mathics": mathics})
    exc_rules = exc.get("rules") if isinstance(exc.get("rules"), dict) else {}
    exc_zero = sum(1 for v in exc_rules.values() if str(v) in ("0", "0/1"))
    chow_status = str(chow.get("status", "MISSING"))

    open_items = []
    if chow_status != CHOW_COMPLETE:
        open_items.append(f"The resolved ambient Chow input is not complete: its status is {chow_status}, "
                          f"and the input file requires {CHOW_COMPLETE} for full acceptance.")
    if not comparison["passed"]:
        if comparison["independent_producer"] is None:
            open_items.append("No independent cross-check reproduced the values: the higher-Cartan table in this run was "
                              f"written by {hc.get('computed_by', 'MISSING')}, and the IntersectionNumbers runs report "
                              f"Wolfram {(wolfram or {}).get('status', 'MISSING')} and Mathics "
                              f"{(mathics or {}).get('status', 'MISSING')} "
                              f"(computed {(mathics or {}).get('computed_count', 'n/a')}, errors {(mathics or {}).get('error_count', 'n/a')}).")
        elif not comparison["native_value_count"]:
            open_items.append("The IntersectionNumbers table cannot be compared: the native Sage table was not kept "
                              f"({HC_NATIVE} is missing or empty).")
        elif comparison.get("producer_report_status") != PRODUCER_OK[comparison["independent_producer"]]:
            open_items.append(f"The higher-Cartan table names {comparison['independent_producer']} as its producer, but that "
                              f"run's report says {comparison.get('producer_report_status')}, not "
                              f"{PRODUCER_OK[comparison['independent_producer']]}.")
        else:
            open_items.append(f"The IntersectionNumbers table ({comparison['independent_producer']}) does not reproduce the native "
                              f"Sage table: {comparison['mismatch_count']} keys differ or are missing (native "
                              f"{comparison['native_value_count']} values, IntersectionNumbers "
                              f"{comparison['independent_value_count']}, {comparison['required_value_count']} required).")
    verified = not open_items

    files = [TENSOR, SUMMARY, CHOW_INPUT, EXC_RULES, HC_RULES, HC_NATIVE, WOLFRAM, MATHICS]
    present = [(rel, sha256_file(root / rel)) for rel in files if (root / rel).exists()]
    bundle = hashlib.sha256("".join(f"{rel}:{h}\n" for rel, h in sorted(present)).encode()).hexdigest()

    typed = {}
    if isinstance(tensor.get("checks"), dict) and "chi_Y4" in tensor["checks"]:
        typed["chi_Y4"] = (f"{tensor['checks']['chi_Y4']} in the tensor file's checks is a constant written by "
                           "run_chow_tensor.sage, not computed from the tensor (ledger T5 computes 3048 or 1098 for the "
                           "stated construction); it is not used here")

    manifest = {
        "schema_version": "UGCT_Y4_TENSOR_MANIFEST_FROM_RUN_V1",
        "status": VERIFIED if verified else NOT_VERIFIED,
        "fully_certified": verified,
        "full_chamber_specific_tensor_verified": verified,
        "nonzero_quadruple_intersections": len(nonzero),
        "total_degree4_monomials": total,
        "basis": basis,
        "resolution_chamber": tensor.get("resolution_chamber"),
        "source_workflow_run_id": str(env.get("GITHUB_RUN_ID") or "local"),
        "source_workflow_run_attempt": str(env.get("GITHUB_RUN_ATTEMPT") or ""),
        "source_commit": str(env.get("GITHUB_SHA") or ""),
        "source_repository": str(env.get("GITHUB_REPOSITORY") or ""),
        "tensor_file": TENSOR,
        "tensor_file_sha256": sha256_file(root / TENSOR),
        "artifact_sha256": bundle,
        "artifact_sha256_definition": "sha256 of the sorted lines 'path:sha256' of the run outputs and inputs listed in files",
        "files": dict(present),
        "inputs": {
            "chow_input_status": chow_status,
            "exceptional_rules": {"status": exc.get("status"), "rule_count": len(exc_rules), "zero_values": exc_zero},
            "higher_cartan_rules": {"status": hc.get("status"), "computed_by": hc.get("computed_by"),
                                    "value_count": hc.get("value_count"),
                                    "required_value_count": comparison["required_value_count"]},
        },
        "cross_checks": {
            "wolfram": {"status": (wolfram or {}).get("status", "MISSING")},
            "mathics": {"status": (mathics or {}).get("status", "MISSING"), "computed_count": (mathics or {}).get("computed_count"),
                        "error_count": (mathics or {}).get("error_count")},
            "table_comparison": comparison,
        },
        "sage_run_reported": {"status": summary.get("status"), "full_tensor_status": summary.get("full_tensor_status"),
                              "full_chamber_specific_tensor_verified": summary.get("full_chamber_specific_tensor_verified")},
        "typed_values_not_used": typed,
        "verification_rule": "verified only if the tensor was exported consistently in this run, the Chow input declares "
                             f"{CHOW_COMPLETE}, and an IntersectionNumbers table agrees value by value with the native Sage table",
        "open_items": open_items,
    }
    manifest["payload_hash"] = canonical_hash(manifest)

    lines = [
        r"\section*{Y4 tensor reproduction record}",
        "This file is generated by \\texttt{ugct\\_sage\\_y4/build\\_y4\\_tensor\\_manifest.py} from the outputs of one "
        "workflow run. It records what that run computed. It is a record, not a theorem.",
        r"\begin{itemize}",
        f"\\item Run {manifest['source_workflow_run_id']} (attempt {manifest['source_workflow_run_attempt'] or 'n/a'}), "
        f"commit \\texttt{{{manifest['source_commit'][:12] or 'n/a'}}}.",
        f"\\item Basis of {len(basis)} divisor classes; {total} degree-four monomials; "
        f"{len(nonzero)} nonzero quadruple intersections.",
        f"\\item Tensor file SHA-256 \\texttt{{{manifest['tensor_file_sha256']}}}.",
        f"\\item Resolved ambient Chow input status: \\texttt{{{chow_status.replace('_', chr(92) + '_')}}}.",
        f"\\item Exceptional rules: {len(exc_rules)}, of which {exc_zero} are zero.",
        f"\\item Independent cross-check (IntersectionNumbers table against the native Sage table): "
        f"{'agrees' if comparison['passed'] else 'not established'}.",
        f"\\item Status: \\texttt{{{manifest['status'].replace('_', chr(92) + '_')}}}.",
        r"\end{itemize}",
    ]
    if open_items:
        lines.append(r"Open items:")
        lines.append(r"\begin{enumerate}")
        lines += [f"\\item {item.replace('_', chr(92) + '_')}" for item in open_items]
        lines.append(r"\end{enumerate}")
    return manifest, "\n".join(lines) + "\n"


def main() -> int:
    root = Path.cwd()
    try:
        manifest, tex = build(root, dict(os.environ))
    except RunOutputError as exc:
        print(f"FAILED: {exc}")
        return 1
    (root / OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_TEX).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_JSON).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (root / OUT_TEX).write_text(tex)
    print(json.dumps({k: manifest[k] for k in ("status", "nonzero_quadruple_intersections", "total_degree4_monomials",
                                               "source_workflow_run_id", "tensor_file_sha256", "open_items")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
