#!/usr/bin/env python3
"""Strict verifier for UGCT frontier closeout certificates.

This is an enforcement script, not a certificate generator.  It intentionally
fails until the repository contains real proof/computation artifacts for each
frontier item.  Its purpose is to prevent criterion-only, placeholder, mocked,
conditional, or frontier-labeled outputs from being reported as closed.

The script writes data_room/data/frontier_closeout_report.json and exits nonzero
when any item is missing, malformed, non-final, or mathematically fails its
machine-checkable pass condition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / "data"
PROOFS = ROOT / "proofs"
REPORT = DATA / "frontier_closeout_report.json"

FORBIDDEN_TEXT = (
    "placeholder",
    "todo",
    "tbd",
    "mock",
    "toy",
    "candidate",
    "pending",
    "frontier",
    "conditional",
    "ready_for",
    "specified_only",
    "not_full",
    "not_fully",
    "not certified",
    "not_certified",
    "open_problem",
    "research_frontier",
    "inherits_",
    "criterion_only",
)

REQUIRED = {
    "pfaffian": {
        "json": DATA / "pfaffian_normalization_certificate.json",
        "proof": PROOFS / "pfaffian_local_reduction_theorem.tex",
        "final_status": "VERIFIED_ABSOLUTE_PFAFFIAN_NORMALIZATION",
    },
    "uplift": {
        "json": DATA / "uplift_hessian_certificate.json",
        "proof": PROOFS / "uplift_positive_hessian_theorem.tex",
        "final_status": "VERIFIED_ANTI_D3_UPLIFT_STABILITY",
    },
    "cosmological_constant": {
        "json": DATA / "cosmological_constant_error_budget.json",
        "proof": PROOFS / "cosmological_constant_interval_theorem.tex",
        "final_status": "VERIFIED_COSMOLOGICAL_CONSTANT_INTERVAL_PAYLOAD",
    },
    "prime_race": {
        "json": DATA / "prime_race_density_certificate.json",
        "proof": PROOFS / "prime_race_unconditional_density_theorem.tex",
        "final_status": "VERIFIED_UNCONDITIONAL_PRIME_RACE_DENSITY",
    },
    "ym_mass_gap_import": {
        "json": DATA / "ym_mass_gap_import_certificate.json",
        "proof": PROOFS / "ym_mass_gap_import_theorem.tex",
        "final_status": "VERIFIED_YM_MASS_GAP_COMPANION_IMPORT",
    },
    "proton_cp": {
        "json": DATA / "proton_cp_lattice_certificate.json",
        "proof": PROOFS / "proton_cp_lattice_extraction_theorem.tex",
        "final_status": "VERIFIED_PROTON_CP_LATTICE_QCD",
    },
    "hadamard_divisor": {
        "json": DATA / "hadamard_divisor_certificate.json",
        "proof": PROOFS / "hadamard_divisor_identification_theorem.tex",
        "final_status": "VERIFIED_HADAMARD_DIVISOR_IDENTIFICATION",
    },
    "y4_tensor": {
        "json": DATA / "y4_tensor_manifest.json",
        "proof": PROOFS / "y4_tensor_reproduction_theorem.tex",
        "final_status": "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED",
    },
}


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"missing file: {path.relative_to(REPO)}"
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"invalid JSON in {path.relative_to(REPO)}: {exc}"
    if not isinstance(obj, dict):
        return None, f"top-level JSON is not an object: {path.relative_to(REPO)}"
    return obj, None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def flatten_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            out.append(str(key))
            out.extend(flatten_strings(value))
    elif isinstance(obj, list):
        for value in obj:
            out.extend(flatten_strings(value))
    return out


def require(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def number(obj: dict[str, Any], key: str, failures: list[str]) -> float:
    if key not in obj:
        failures.append(f"missing numeric field `{key}`")
        return math.nan
    try:
        value = float(obj[key])
    except Exception:
        failures.append(f"field `{key}` is not numeric")
        return math.nan
    if not math.isfinite(value):
        failures.append(f"field `{key}` is not finite")
    return value


def interval(obj: dict[str, Any], key: str, failures: list[str]) -> tuple[float, float]:
    value = obj.get(key)
    if isinstance(value, dict):
        lo = value.get("lower")
        hi = value.get("upper")
    elif isinstance(value, list) and len(value) == 2:
        lo, hi = value
    else:
        failures.append(f"field `{key}` is not a two-sided interval")
        return math.nan, math.nan
    try:
        lo_f, hi_f = float(lo), float(hi)
    except Exception:
        failures.append(f"field `{key}` has nonnumeric endpoints")
        return math.nan, math.nan
    require(math.isfinite(lo_f) and math.isfinite(hi_f), failures, f"field `{key}` endpoints must be finite")
    require(lo_f <= hi_f, failures, f"field `{key}` lower endpoint exceeds upper endpoint")
    return lo_f, hi_f


def base_certificate_checks(name: str, obj: dict[str, Any], proof_path: Path, expected_status: str, failures: list[str]) -> None:
    status = str(obj.get("status", ""))
    require(status == expected_status, failures, f"status `{status}` does not equal required final status `{expected_status}`")
    require(obj.get("fully_certified") is True, failures, "fully_certified must be true for strict closeout")
    require(str(obj.get("schema_version", "")).startswith("UGCT_"), failures, "schema_version must start with UGCT_")
    require(proof_path.exists(), failures, f"missing proof artifact: {proof_path.relative_to(REPO)}")
    if proof_path.exists():
        require(proof_path.stat().st_size > 500, failures, f"proof artifact too small to be substantive: {proof_path.relative_to(REPO)}")
    bad_hits = sorted({bad for s in flatten_strings(obj) for bad in FORBIDDEN_TEXT if bad in s.lower()})
    require(not bad_hits, failures, f"certificate contains non-final/placeholder language: {bad_hits}")
    expected_payload_hash = obj.get("payload_hash")
    if expected_payload_hash is not None:
        obj_copy = dict(obj)
        obj_copy.pop("payload_hash", None)
        actual = hashlib.sha256(json.dumps(obj_copy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(str(expected_payload_hash) == actual, failures, "payload_hash does not match canonical JSON without payload_hash field")


def check_pfaffian(obj: dict[str, Any], failures: list[str]) -> None:
    lo, hi = interval(obj, "pfaffian_interval", failures)
    require(lo > 0.0 and hi > 0.0, failures, "pfaffian_interval must be strictly positive")
    require(obj.get("zero_modes_removed") is True, failures, "zero_modes_removed must be true")
    require(obj.get("collar_independence_verified") is True, failures, "collar_independence_verified must be true")
    require(bool(obj.get("operator_domain")), failures, "operator_domain must be specified")
    require(bool(obj.get("determinant_line_convention")), failures, "determinant_line_convention must be specified")


def check_uplift(obj: dict[str, Any], failures: list[str]) -> None:
    lam = number(obj, "hessian_lambda_min_lower", failures)
    grad = number(obj, "gradient_norm_upper", failures)
    boundary = number(obj, "boundary_potential_gap_lower", failures)
    vlo, vhi = interval(obj, "V_phys_interval", failures)
    require(lam > 0.0, failures, "hessian_lambda_min_lower must be strictly positive")
    require(grad >= 0.0 and grad <= max(lam, 1.0) * 1e-8, failures, "gradient_norm_upper must be a certified near-critical residual")
    require(boundary > 0.0, failures, "boundary_potential_gap_lower must exclude runaways")
    require(vlo > 0.0 and vhi > 0.0, failures, "V_phys_interval must be strictly positive")
    require(obj.get("compact_window_verified") is True, failures, "compact_window_verified must be true")
    require(obj.get("backreaction_terms_included") is True, failures, "backreaction_terms_included must be true")


def check_cosmological_constant(obj: dict[str, Any], failures: list[str]) -> None:
    lo, hi = interval(obj, "rho_lambda_interval", failures)
    require(lo > 0.0 and hi > 0.0, failures, "rho_lambda_interval must be strictly positive")
    require(obj.get("depends_on_uplift_certificate") == "VERIFIED_ANTI_D3_UPLIFT_STABILITY", failures, "cosmological constant must depend on the verified uplift certificate")
    require(bool(obj.get("error_budget_terms")), failures, "error_budget_terms must be nonempty")
    require(obj.get("all_uncertainties_propagated") is True, failures, "all_uncertainties_propagated must be true")


def check_prime_race(obj: dict[str, Any], failures: list[str]) -> None:
    lo, hi = interval(obj, "density_delta_4_3_1_interval", failures)
    eps = number(obj, "epsilon_above_one_half", failures)
    require(lo > 0.5 and hi <= 1.0, failures, "density lower bound must be strictly greater than 1/2 and upper <= 1")
    require(eps > 0.0, failures, "epsilon_above_one_half must be positive")
    require(obj.get("grh_used") is False, failures, "grh_used must be false for unconditional closeout")
    require(obj.get("linear_independence_used") is False, failures, "linear_independence_used must be false for unconditional closeout")
    require(obj.get("spectral_identification_verified") is True, failures, "spectral_identification_verified must be true")
    require(obj.get("polymer_hypotheses_verified") is True, failures, "polymer_hypotheses_verified must be true")


def check_ym_import(obj: dict[str, Any], failures: list[str]) -> None:
    require(bool(obj.get("companion_volume_sha256")), failures, "companion_volume_sha256 is required")
    require(obj.get("os_axioms_verified") is True, failures, "os_axioms_verified must be true")
    require(obj.get("spectral_gap_lower_bound_positive") is True, failures, "spectral_gap_lower_bound_positive must be true")
    require(obj.get("reflection_positivity_verified") is True, failures, "reflection_positivity_verified must be true")
    require(obj.get("rg_convergence_verified") is True, failures, "rg_convergence_verified must be true")


def check_proton_cp(obj: dict[str, Any], failures: list[str]) -> None:
    cp_lo, cp_hi = interval(obj, "c_p_interval", failures)
    mp_lo, mp_hi = interval(obj, "m_p_interval", failures)
    require(cp_lo > 0.0 and cp_hi > 0.0, failures, "c_p_interval must be positive")
    require(mp_lo > 0.0 and mp_hi > 0.0, failures, "m_p_interval must be positive")
    require(obj.get("continuum_extrapolation_verified") is True, failures, "continuum_extrapolation_verified must be true")
    require(obj.get("finite_volume_error_bounded") is True, failures, "finite_volume_error_bounded must be true")
    require(obj.get("scale_setting_verified") is True, failures, "scale_setting_verified must be true")
    require(bool(obj.get("lattice_input_snapshot_sha256")), failures, "lattice_input_snapshot_sha256 is required")


def check_hadamard(obj: dict[str, Any], failures: list[str]) -> None:
    require(obj.get("xi_divisor_identified") is True, failures, "xi_divisor_identified must be true")
    require(obj.get("nonvanishing_factor_verified") is True, failures, "nonvanishing_factor_verified must be true")
    require(obj.get("no_spurious_zeros_verified") is True, failures, "no_spurious_zeros_verified must be true")
    require(obj.get("hurwitz_transfer_verified") is True, failures, "hurwitz_transfer_verified must be true")
    require(obj.get("h2_tail_graph_norm_verified") is True, failures, "h2_tail_graph_norm_verified must be true")
    require(obj.get("parity_gap_persistence_verified") is True, failures, "parity_gap_persistence_verified must be true")


def check_y4(obj: dict[str, Any], failures: list[str]) -> None:
    require(obj.get("full_chamber_specific_tensor_verified") is True, failures, "full_chamber_specific_tensor_verified must be true")
    require(int(obj.get("nonzero_quadruple_intersections", 0)) > 0, failures, "nonzero_quadruple_intersections must be positive")
    require(bool(obj.get("source_workflow_run_id")), failures, "source_workflow_run_id is required")
    require(bool(obj.get("artifact_sha256")), failures, "artifact_sha256 is required")
    require(bool(obj.get("tensor_file_sha256")), failures, "tensor_file_sha256 is required")


CHECKS = {
    "pfaffian": check_pfaffian,
    "uplift": check_uplift,
    "cosmological_constant": check_cosmological_constant,
    "prime_race": check_prime_race,
    "ym_mass_gap_import": check_ym_import,
    "proton_cp": check_proton_cp,
    "hadamard_divisor": check_hadamard,
    "y4_tensor": check_y4,
}


def verify_item(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    cert_path: Path = spec["json"]
    proof_path: Path = spec["proof"]
    obj, error = load_json(cert_path)
    if error:
        failures.append(error)
        obj = {}
    if obj:
        base_certificate_checks(name, obj, proof_path, spec["final_status"], failures)
        CHECKS[name](obj, failures)
    record = {
        "name": name,
        "certificate": str(cert_path.relative_to(REPO)),
        "proof": str(proof_path.relative_to(REPO)),
        "required_status": spec["final_status"],
        "ok": not failures,
        "failures": failures,
    }
    if cert_path.exists():
        record["certificate_sha256"] = sha256_file(cert_path)
    if proof_path.exists():
        record["proof_sha256"] = sha256_file(proof_path)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify strict UGCT frontier closeout certificates")
    parser.add_argument("--allow-proton-pending", action="store_true", help="permit proton_cp to fail while still failing all other frontier items")
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    records = [verify_item(name, spec) for name, spec in REQUIRED.items()]
    effective_records = [r for r in records if not (args.allow_proton_pending and r["name"] == "proton_cp")]
    ok = all(r["ok"] for r in effective_records)
    report = {
        "schema_version": "UGCT_FRONTIER_CLOSEOUT_REPORT_V1",
        "status": "FRONTIER_CLOSEOUT_VERIFIED" if ok else "FRONTIER_CLOSEOUT_NOT_VERIFIED",
        "strict": True,
        "allow_proton_pending": bool(args.allow_proton_pending),
        "honesty_rule": "No frontier item is closed by analogy, criterion-only text, placeholder data, conditional status, or mocked computation. Each accepted item must have a proof artifact, final-status JSON certificate, pass/fail fields, and hashable provenance.",
        "records": records,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
