#!/usr/bin/env python3
"""Shared helpers for the frontier records (build_frontier_certificates.py, verify_frontier_scoped.py).

A frontier record is the JSON file the strict gate (verify_frontier_closeout.py) reads for one of its eight items,
plus a TeX sidecar. Every record carries:

  scope_category          VERIFIED | CONDITIONAL | OPEN | NEGATIVE
                            VERIFIED     the strict gate's criterion for the item holds, from computations in the run
                            CONDITIONAL  the result is computed in the run and holds under the listed hypotheses
                            OPEN         the item is not established; open_items says what is missing
                            NEGATIVE     the computation refutes the claimed result; findings says how
  status                  the strict gate's status string only when scope_category is VERIFIED
  fully_certified         true only when scope_category is VERIFIED
  computed_by             the script that wrote the record
  inputs                  [{path, sha256, role}] of every file the record was computed from or compared with
  source_workflow_run_id  $GITHUB_RUN_ID of the run that wrote it ("local" outside GitHub Actions)
  payload_hash            sha256 of the canonical JSON without payload_hash (same as the strict gate)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCOPES = ("VERIFIED", "CONDITIONAL", "OPEN", "NEGATIVE")
SCHEMA = "UGCT_FRONTIER_RECORD_V2"

# item -> (certificate, sidecar, strict status); the same table as verify_frontier_closeout.REQUIRED
ITEMS = {
    "pfaffian": ("data_room/data/pfaffian_normalization_certificate.json",
                 "data_room/proofs/pfaffian_local_reduction_theorem.tex", "VERIFIED_ABSOLUTE_PFAFFIAN_NORMALIZATION"),
    "uplift": ("data_room/data/uplift_hessian_certificate.json",
               "data_room/proofs/uplift_positive_hessian_theorem.tex", "VERIFIED_UPLIFT_STABILITY"),
    "cosmological_constant": ("data_room/data/cosmological_constant_error_budget.json",
                              "data_room/proofs/cosmological_constant_interval_theorem.tex",
                              "VERIFIED_COSMOLOGICAL_CONSTANT_INTERVAL_PAYLOAD"),
    "prime_race": ("data_room/data/prime_race_density_certificate.json",
                   "data_room/proofs/prime_race_density_theorem.tex", "VERIFIED_PRIME_RACE_DENSITY"),
    "ym_mass_gap_import": ("data_room/data/ym_mass_gap_import_certificate.json",
                           "data_room/proofs/ym_mass_gap_import_theorem.tex", "VERIFIED_YM_MASS_GAP_COMPANION_IMPORT"),
    "proton_cp": ("data_room/data/proton_cp_lattice_certificate.json",
                  "data_room/proofs/proton_cp_lattice_extraction_theorem.tex", "VERIFIED_PROTON_CP_LATTICE_QCD"),
    "hadamard_divisor": ("data_room/data/hadamard_divisor_certificate.json",
                         "data_room/proofs/hadamard_divisor_identification_theorem.tex",
                         "VERIFIED_HADAMARD_DIVISOR_IDENTIFICATION"),
    "y4_tensor": ("data_room/data/y4_tensor_manifest.json", "data_room/proofs/y4_tensor_reproduction_theorem.tex",
                  "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED"),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(obj: dict) -> str:
    """Same canonical hash as data_room/scripts/verify_frontier_closeout.py."""
    tmp = dict(obj)
    tmp.pop("payload_hash", None)
    return hashlib.sha256(json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_info(env: dict) -> dict:
    return {"source_workflow_run_id": str(env.get("GITHUB_RUN_ID") or "local"),
            "source_workflow_run_attempt": str(env.get("GITHUB_RUN_ATTEMPT") or ""),
            "source_commit": str(env.get("GITHUB_SHA") or ""),
            "source_repository": str(env.get("GITHUB_REPOSITORY") or "")}


def input_entry(root: Path, rel: str, role: str) -> dict:
    return {"path": rel, "sha256": sha256_file(root / rel), "role": role}


def finalize(record: dict) -> dict:
    if record.get("scope_category") not in SCOPES:
        raise ValueError(f"scope_category must be one of {SCOPES}, not {record.get('scope_category')!r}")
    record["fully_certified"] = record["scope_category"] == "VERIFIED"
    record["payload_hash"] = canonical_hash(record)
    return record


def tex_escape(s) -> str:
    out = []
    for ch in str(s):
        out.append({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}", "<": r"\textless{}",
                    ">": r"\textgreater{}", "|": r"\textbar{}"}.get(ch, ch))
    return "".join(out)


def tex_sci(x: float, digits: int = 2) -> str:
    """A float in TeX scientific notation, e.g. 1.1\\times10^{-5}."""
    m, e = f"{x:.{digits - 1}e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.10g}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + "; ".join(f"{k}: {fmt(x)}" for k, x in v.items()) + "}"
    return str(v)


def record_tex(record: dict, title: str, summary: list[str], extra: list[str] | None = None) -> str:
    """TeX sidecar for a record: summary prose (already TeX), then every field of the record that a reader checks."""
    lines = [r"\section*{" + title + "}",
             f"This file is generated by \\texttt{{{tex_escape(record['computed_by'])}}} in run "
             f"{tex_escape(record.get('source_workflow_run_id'))}. "
             + ("It is a record, not a theorem." if record["scope_category"] != "VERIFIED" else ""),
             "",
             f"Scope: \\texttt{{{record['scope_category']}}}. Status: \\texttt{{{tex_escape(record['status'])}}}.",
             ""] + summary + [""]
    if record.get("inputs"):
        lines += [r"\paragraph{Inputs.}", r"\begin{itemize}"]
        lines += [f"\\item \\texttt{{{tex_escape(i['path'])}}} ({tex_escape(i['role'])}), SHA-256 "
                  f"\\texttt{{{i['sha256'][:16]}}}\\ldots" for i in record["inputs"]]
        lines.append(r"\end{itemize}")
    for key, head in (("hypotheses", "Hypotheses"), ("findings", "Findings"), ("open_items", "Open items")):
        if record.get(key):
            lines += [r"\paragraph{" + head + ".}", r"\begin{enumerate}"]
            lines += [f"\\item {tex_escape(x)}" for x in record[key]]
            lines.append(r"\end{enumerate}")
    if record.get("checks"):
        lines += [r"\paragraph{Checks in this run.}", r"\begin{itemize}"]
        lines += [f"\\item {tex_escape(k)}: {tex_escape(fmt(v))}" for k, v in record["checks"].items()]
        lines.append(r"\end{itemize}")
    if extra:
        lines += [""] + extra
    return "\n".join(lines) + "\n"


def write(root: Path, item: str, record: dict, tex: str) -> None:
    cert, proof, _ = ITEMS[item]
    (root / cert).parent.mkdir(parents=True, exist_ok=True)
    (root / proof).parent.mkdir(parents=True, exist_ok=True)
    (root / cert).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (root / proof).write_text(tex)
