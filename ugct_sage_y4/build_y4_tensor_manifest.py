#!/usr/bin/env python3
"""Build data_room/data/y4_tensor_manifest.json from the Y4 tensors that this workflow run computed.

Two computations of the same tensor run in the workflow:
- independent_y4_pushforward.py computes every degree-four intersection number, chi(Y4) and c2(Y4) in exact rational
  arithmetic from the published blowup sequence (Esole-Jefferson-Kang pushforward), shares no code with the Sage
  pipeline, and runs its own checks (published EJK Euler characteristic formula, Todd genus 2, Riemann-Roch
  integrality, Calabi-Yau condition, zero-section relation, affine A4 Cartan matrix, and the 5d IMS prepotential
  for the triple-Cartan sector). It writes ugct_sage_y4/data/y4_independent_tensor.json.
- the Sage pipeline (native_pushforward_core.py for the higher-Cartan sector, rules for the rest, exported by
  run_chow_tensor.sage) writes ugct_sage_y4/data/y4_intersection_ring_full.json and the run summary.

The manifest is filled only from this run's outputs and the GitHub run id. Every count and hash is recomputed here.

The tensor counts as FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED only if all three of these hold:
  1. the Sage tensor was exported in this run and its counts are consistent;
  2. the independent computation ran in this run and every one of its checks passed;
  3. the two tensors agree value by value on every degree-four monomial in the basis.
Otherwise the status is Y4_TENSOR_COMPUTED_NOT_INDEPENDENTLY_VERIFIED, and the reasons are listed in open_items.

Until 2026-11-26 the rule was instead: the resolved ambient Chow input declares itself complete, and an
IntersectionNumbers run (Wolfram or Mathics) reproduces the native higher-Cartan table. Neither cross-check could
run (no wolframscript; Mathics fails on the package), and the native table was all zeros because of three
convention errors (see native_pushforward_core.py). The certified values no longer come from the Chow input, so its
status and the IntersectionNumbers runs are still recorded but no longer decide the status.

The script exits 1 only when this run's outputs are missing or inconsistent.
Run from the repository root:  python3 ugct_sage_y4/build_y4_tensor_manifest.py
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

TENSOR = "ugct_sage_y4/data/y4_intersection_ring_full.json"
SUMMARY = "ugct_sage_y4/reports/sage_run_summary.json"
INDEPENDENT = "ugct_sage_y4/data/y4_independent_tensor.json"
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
INDEPENDENT_OK = "INDEPENDENT_TENSOR_COMPUTED"


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
    """Value-by-value comparison of an IntersectionNumbers higher-Cartan table with the native Sage table (recorded only).

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
        return out
    keys = sorted(set(nv) | set(fv))
    mism = [k for k in keys if k not in nv or k not in fv or exact(nv[k]) is None or exact(nv[k]) != exact(fv[k])]
    out["mismatch_count"] = len(mism)
    out["mismatch_sample"] = mism[:10]
    out["passed"] = required > 0 and len(nv) >= required and len(fv) >= required and not mism
    return out


def canonical_entries(basis, entries) -> tuple[dict, list]:
    """Re-key a tensor by basis order and drop zeros; returns (entries, keys that are not degree-four monomials)."""
    order = {n: i for i, n in enumerate(basis)}
    out, bad = {}, []
    for k, v in entries.items():
        parts = str(k).split(",")
        q = exact(v)
        if len(parts) != 4 or any(p not in order for p in parts) or q is None:
            bad.append(k)
            continue
        if q:
            out[",".join(sorted(parts, key=order.get))] = q
    return out, bad


def compare_tensors(basis, sage_entries, ind_basis, ind_entries) -> dict:
    """Value-by-value comparison of the two tensors over every degree-four monomial of the basis."""
    total = comb(len(basis) + 3, 4)
    out = {"monomials_compared": 0, "mismatch_count": None, "mismatch_sample": [], "passed": False}
    if list(ind_basis or []) != list(basis):
        out["basis_differs"] = {"sage": basis, "independent": ind_basis}
        return out
    a, bad_a = canonical_entries(basis, sage_entries)
    b, bad_b = canonical_entries(basis, ind_entries)
    if bad_a or bad_b:
        out["malformed_keys"] = (bad_a + bad_b)[:10]
        return out
    mism = []
    for quad in itertools.combinations_with_replacement(basis, 4):
        k = ",".join(quad)
        if a.get(k, 0) != b.get(k, 0):
            mism.append({"monomial": k, "sage": str(a.get(k, 0)), "independent": str(b.get(k, 0))})
    out.update(monomials_compared=total, mismatch_count=len(mism), mismatch_sample=mism[:10], passed=not mism)
    return out


def independent_failures(ind) -> list[str]:
    """Reasons the independent computation cannot be used; empty when it ran and every check passed."""
    if not isinstance(ind, dict):
        return [f"The independent computation did not run in this run ({INDEPENDENT} is missing)."]
    out = []
    if ind.get("status") != INDEPENDENT_OK:
        out.append(f"The independent computation reports {ind.get('status')}, not {INDEPENDENT_OK}.")
    if ind.get("failures"):
        out.append(f"The independent computation lists failed checks: {ind['failures'][:3]}.")
    ch = ind.get("checks") if isinstance(ind.get("checks"), dict) else {}
    prepot = ch.get("prepotential_triple_cartan") if isinstance(ch.get("prepotential_triple_cartan"), dict) else {}
    required = {
        "chi matches the published EJK SU(5) formula": ch.get("chi_matches_published_formula") is True,
        "Todd genus 2": str(ch.get("todd_genus")) == "2",
        "Riemann-Roch integrality": ch.get("riemann_roch_failures") == 0 and (ch.get("riemann_roch_divisors_tested") or 0) > 0,
        "Calabi-Yau condition": ch.get("calabi_yau_condition") is True,
        "zero-section relation": ch.get("zero_section_relation") is True,
        "IMS prepotential of the triple-Cartan sector": prepot.get("passed") is True,
    }
    missing = [name for name, ok in required.items() if not ok]
    if missing:
        out.append(f"The independent computation does not record these checks as passed: {', '.join(missing)}.")
    if not isinstance(ind.get("quadruple_intersections"), dict) or not isinstance(ind.get("basis"), list):
        out.append("The independent computation has no basis or no quadruple_intersections table.")
    return out


def build(root: Path, env: dict) -> tuple[dict, str]:
    tensor = load(root, TENSOR, True)
    summary = load(root, SUMMARY, True)
    ind = load(root, INDEPENDENT, False)
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

    open_items = independent_failures(ind)
    ind_ok = not open_items
    ind_entries = (ind or {}).get("quadruple_intersections") if isinstance((ind or {}).get("quadruple_intersections"), dict) else {}
    tensor_comparison = compare_tensors(basis, entries, (ind or {}).get("basis"), ind_entries) if ind_entries else \
        {"monomials_compared": 0, "mismatch_count": None, "mismatch_sample": [], "passed": False}
    if isinstance(ind, dict) and not tensor_comparison["passed"]:
        if "basis_differs" in tensor_comparison:
            open_items.append("The two computations use different bases, so they cannot be compared.")
        elif "malformed_keys" in tensor_comparison:
            open_items.append(f"Malformed tensor keys: {tensor_comparison['malformed_keys']}.")
        elif tensor_comparison["mismatch_count"]:
            open_items.append(f"The Sage tensor and the independent tensor differ on {tensor_comparison['mismatch_count']} of "
                              f"{tensor_comparison['monomials_compared']} monomials, e.g. "
                              f"{[m['monomial'] for m in tensor_comparison['mismatch_sample'][:5]]}.")
        elif not ind_entries:
            pass                                                     # already reported by independent_failures
    verified = not open_items

    comparison = compare_tables(native, hc, {"wolfram": wolfram, "mathics": mathics})
    exc_rules = exc.get("rules") if isinstance(exc.get("rules"), dict) else {}
    exc_zero = sum(1 for v in exc_rules.values() if str(v) in ("0", "0/1"))
    chow_status = str(chow.get("status", "MISSING"))

    if ind_ok:
        certified_file, certified_entries = INDEPENDENT, canonical_entries(ind["basis"], ind_entries)[0]
    else:
        certified_file, certified_entries = TENSOR, nonzero
    files = [TENSOR, SUMMARY, INDEPENDENT, CHOW_INPUT, EXC_RULES, HC_RULES, HC_NATIVE, WOLFRAM, MATHICS]
    present = [(rel, sha256_file(root / rel)) for rel in files if (root / rel).exists()]
    bundle = hashlib.sha256("".join(f"{rel}:{h}\n" for rel, h in sorted(present)).encode()).hexdigest()

    typed = {}
    sage_chi = (tensor.get("checks") or {}).get("chi_Y4") if isinstance(tensor.get("checks"), dict) else None
    if sage_chi is not None:
        typed["chi_Y4"] = (f"{sage_chi} in the Sage tensor file's checks is a constant written by run_chow_tensor.sage, "
                           "not computed from the tensor; it is not used here")

    ind_checks = (ind or {}).get("checks") if isinstance((ind or {}).get("checks"), dict) else {}
    chi = (ind or {}).get("chi_Y4") if ind_ok else None
    manifest = {
        "schema_version": "UGCT_Y4_TENSOR_MANIFEST_FROM_RUN_V2",
        "status": VERIFIED if verified else NOT_VERIFIED,
        "fully_certified": verified,
        "full_chamber_specific_tensor_verified": verified,
        "nonzero_quadruple_intersections": len(certified_entries),
        "total_degree4_monomials": total,
        "basis": basis,
        "resolution_chamber": tensor.get("resolution_chamber"),
        "chi_Y4": chi,
        "d3_tadpole_chi_over_24": (ind or {}).get("d3_tadpole_chi_over_24") if ind_ok else None,
        "int_c2_squared": (ind or {}).get("int_c2_squared") if ind_ok else None,
        "source_workflow_run_id": str(env.get("GITHUB_RUN_ID") or "local"),
        "source_workflow_run_attempt": str(env.get("GITHUB_RUN_ATTEMPT") or ""),
        "source_commit": str(env.get("GITHUB_SHA") or ""),
        "source_repository": str(env.get("GITHUB_REPOSITORY") or ""),
        "tensor_file": certified_file,
        "tensor_file_sha256": sha256_file(root / certified_file),
        "sage_tensor_file_sha256": sha256_file(root / TENSOR),
        "sage_tensor_nonzero": len(nonzero),
        "artifact_sha256": bundle,
        "artifact_sha256_definition": "sha256 of the sorted lines 'path:sha256' of the run outputs and inputs listed in files",
        "files": dict(present),
        "independent_computation": {
            "status": (ind or {}).get("status", "MISSING"),
            "method": (ind or {}).get("method"),
            "nonzero_count": (ind or {}).get("nonzero_count"),
            "checks": {k: ind_checks.get(k) for k in (
                "chi_from_published_EJK_formula", "chi_matches_published_formula", "todd_genus",
                "riemann_roch_divisors_tested", "riemann_roch_failures", "calabi_yau_condition", "zero_section_relation",
                "dynkin_adjacency", "prepotential_triple_cartan", "smooth_weierstrass_chi")},
            "failures": (ind or {}).get("failures"),
        },
        "tensor_comparison": tensor_comparison,
        "recorded_not_required": {
            "chow_input_status": chow_status,
            "exceptional_rules": {"status": exc.get("status"), "rule_count": len(exc_rules), "zero_values": exc_zero},
            "higher_cartan_rules": {"status": hc.get("status"), "computed_by": hc.get("computed_by"),
                                    "value_count": hc.get("value_count")},
            "wolfram": {"status": (wolfram or {}).get("status", "MISSING")},
            "mathics": {"status": (mathics or {}).get("status", "MISSING"), "computed_count": (mathics or {}).get("computed_count"),
                        "error_count": (mathics or {}).get("error_count")},
            "intersectionnumbers_table_comparison": comparison,
        },
        "sage_run_reported": {"status": summary.get("status"), "full_tensor_status": summary.get("full_tensor_status"),
                              "full_chamber_specific_tensor_verified": summary.get("full_chamber_specific_tensor_verified")},
        "typed_values_not_used": typed,
        "verification_rule": "verified only if the Sage tensor was exported consistently in this run, the independent exact "
                             "pushforward ran in this run with every check passed, and the two tensors agree on every "
                             "degree-four monomial",
        "open_items": open_items,
    }
    manifest["payload_hash"] = canonical_hash(manifest)

    def tt(s):
        return str(s).replace("_", chr(92) + "_")

    lines = [
        r"\section*{Y4 tensor reproduction record}",
        "This file is generated by \\texttt{ugct\\_sage\\_y4/build\\_y4\\_tensor\\_manifest.py} from the outputs of one "
        "workflow run. It records what that run computed and how the two computations compare. It is a record, not a theorem.",
        r"\begin{itemize}",
        f"\\item Run {manifest['source_workflow_run_id']} (attempt {manifest['source_workflow_run_attempt'] or 'n/a'}), "
        f"commit \\texttt{{{manifest['source_commit'][:12] or 'n/a'}}}.",
        f"\\item Basis of {len(basis)} divisor classes; {total} degree-four monomials; "
        f"{len(certified_entries)} nonzero quadruple intersections in \\texttt{{{tt(certified_file)}}}.",
        f"\\item Certified tensor file SHA-256 \\texttt{{{manifest['tensor_file_sha256']}}}.",
        f"\\item Independent exact computation: \\texttt{{{tt(manifest['independent_computation']['status'])}}}; "
        f"$\\chi(Y_4) = {chi if chi is not None else 'n/a'}$ "
        f"(published EJK SU(5) formula: {ind_checks.get('chi_from_published_EJK_formula', 'n/a')}); "
        f"Todd genus {ind_checks.get('todd_genus', 'n/a')}; Riemann--Roch integrality failures "
        f"{ind_checks.get('riemann_roch_failures', 'n/a')} of {ind_checks.get('riemann_roch_divisors_tested', 'n/a')}; "
        f"IMS prepotential check of the triple-Cartan sector: "
        f"{'passed' if (ind_checks.get('prepotential_triple_cartan') or {}).get('passed') else 'not passed'}.",
        f"\\item Sage tensor against the independent tensor: "
        f"{'agree on all ' + str(tensor_comparison['monomials_compared']) + ' monomials' if tensor_comparison['passed'] else 'not in agreement'}"
        f"{'' if tensor_comparison['passed'] or tensor_comparison['mismatch_count'] is None else ' (' + str(tensor_comparison['mismatch_count']) + ' monomials differ)'}.",
        f"\\item Recorded, not required: resolved ambient Chow input status \\texttt{{{tt(chow_status)}}}; "
        f"Wolfram \\texttt{{{tt((wolfram or {}).get('status', 'MISSING'))}}}; Mathics \\texttt{{{tt((mathics or {}).get('status', 'MISSING'))}}}.",
        f"\\item Status: \\texttt{{{tt(manifest['status'])}}}.",
        r"\end{itemize}",
    ]
    if open_items:
        lines.append(r"Open items:")
        lines.append(r"\begin{enumerate}")
        lines += [f"\\item {tt(item)}" for item in open_items]
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
                                               "chi_Y4", "source_workflow_run_id", "tensor_file_sha256", "open_items")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
