#!/usr/bin/env python3
"""
verify_proton_cp_anvil.py

Promotion verification for UGCT proton c_p Anvil lattice/HPC certificate
(Item 14 → PRESERVED_LATTICE_HPC_CERTIFICATE).

STATUS is PRESERVED_LATTICE_HPC_CERTIFICATE only if every required artifact
exists, has complete metadata, SHA256 manifests match, and no synthetic/
inferred-from-mass data is detected.

This script intentionally fails closed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REQUIRED_ARTIFACTS = [
    "anvil_job_metadata.json",
    "raw_correlators_manifest.json",
    "analysis_windows.json",
    "continuum_extrapolation.json",
    "finite_volume.json",
    "scale_setting.json",
    "trace_anomaly.json",
]

REQUIRED_KEYS = {
    "anvil_job_metadata.json": [
        "configuration_count", "ensemble_ids", "beta_values",
        "lattice_spacings", "volumes", "Nf", "random_seeds",
        "plaquette_means", "topological_charges", "acceptance_rates",
        "autocorrelation_lengths",
    ],
    "raw_correlators_manifest.json": [
        "SHA256", "file_sizes", "configuration_count", "ensemble_IDs",
        "correlator_files",
    ],
    "analysis_windows.json": [
        "fit_windows", "model_selection_rule", "chi2_dof",
        "AIC", "BIC", "selected_model",
    ],
    "continuum_extrapolation.json": [
        "lattice_spacings", "fit_forms", "continuum_limit",
        "systematic_uncertainty", "chi2",
    ],
    "finite_volume.json": [
        "volumes", "Delta_FV", "m_pi_L_values",
    ],
    "scale_setting.json": [
        "observable", "scale_value", "uncertainty_propagation",
    ],
    "trace_anomaly.json": [
        "central", "bootstrap", "systematics", "c_p_interval",
    ],
}

FORBIDDEN_INDICATORS = [
    "experimental_proton_mass",
    "back_solved",
    "symbolic_derivation",
    "synthetic_configuration",
    "inferred_from_mass",
    "target_mass_used",
    "pdg_proton_mass",
    "flag_lambda",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}


def check_artifact(name: str, base: Path) -> list[str]:
    issues: list[str] = []
    p = base / name
    if not p.exists():
        issues.append(f"MISSING: {name}")
        return issues
    data = load_json(p)
    if "_error" in data:
        issues.append(f"INVALID_JSON: {name} ({data['_error']})")
        return issues
    for key in REQUIRED_KEYS.get(name, []):
        if key not in data:
            issues.append(f"MISSING_KEY: {name}.{key}")
    text = json.dumps(data).lower()
    for bad in FORBIDDEN_INDICATORS:
        if bad in text:
            issues.append(f"FORBIDDEN_INDICATOR: {name} contains '{bad}'")
    return issues


def main() -> int:
    base = Path(__file__).resolve().parent
    all_issues: list[str] = []

    print("=== UGCT Anvil Proton c_p Verification ===")
    print(f"Working directory: {base}")
    print()

    for art in REQUIRED_ARTIFACTS:
        issues = check_artifact(art, base)
        if issues:
            all_issues.extend(issues)
            print(f"[FAIL] {art}")
            for i in issues:
                print(f"       {i}")
        else:
            print(f"[PASS] {art}")

    manifest_path = base / "raw_correlators_manifest.json"
    if manifest_path.exists():
        man = load_json(manifest_path)
        if "SHA256" in man and isinstance(man["SHA256"], dict):
            for fname, expected in man["SHA256"].items():
                fp = base / fname
                if fp.exists():
                    actual = sha256_file(fp)
                    if actual != expected:
                        all_issues.append(f"HASH_MISMATCH: {fname}")
                        print(f"[FAIL] HASH_MISMATCH: {fname}")
                else:
                    all_issues.append(f"MANIFEST_FILE_MISSING: {fname}")

    print()
    if all_issues:
        print("STATUS:")
        print("FAIL")
        print()
        print("Reasons:")
        for i in all_issues:
            print(f"  - {i}")
        print()
        print("Promotion to PRESERVED_LATTICE_HPC_CERTIFICATE denied.")
        print("Real SU(3) gauge ensembles, inversions, correlators, and")
        print("first-principles EMT matrix elements are required.")
        print("No synthetic or mass-inferred data permitted.")
        return 1

    print("STATUS:")
    print("PRESERVED_LATTICE_HPC_CERTIFICATE")
    print()
    print("All artifacts present, keys complete, no forbidden indicators.")
    print("Certificate may be promoted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
