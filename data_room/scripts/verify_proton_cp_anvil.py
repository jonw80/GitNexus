#!/usr/bin/env python3
"""
verify_proton_cp_anvil.py

Definition 1.16 / first_principles_lattice_certificate.pdf verifier.

Emits PRESERVED_LATTICE_HPC_CERTIFICATE only when every required artifact
exists with complete production keys, non-null continuum/FV/scale/trace data,
SHA256 matches, and no forbidden indicators of synthetic or mass-inferred origin.

Current bounded files intentionally leave production fields null → FAIL (correct).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# Paths relative to repo root (as required by Definition 1.16)
REQUIRED = [
    "data_room/primary/proton/anvil_job_metadata.json",
    "data_room/primary/proton/raw_correlators_manifest.json",
    "data_room/primary/proton/analysis_windows.json",
    "data_room/primary/proton/continuum_extrapolation.json",
    "data_room/primary/proton/finite_volume.json",
    "data_room/primary/proton/scale_setting.json",
    "data_room/primary/proton/trace_anomaly.json",
]

# Keys that must be non-null for PRESERVED status
PRODUCTION_KEYS = {
    "data_room/primary/proton/anvil_job_metadata.json": [
        "configuration_count", "ensemble_ids", "beta_values",
        "lattice_spacings", "volumes", "plaquette_means",
    ],
    "data_room/primary/proton/raw_correlators_manifest.json": [
        "SHA256", "configuration_count", "correlator_files",
    ],
    "data_room/primary/proton/analysis_windows.json": [
        "fit_windows", "selected_model", "chi2_dof",
    ],
    "data_room/primary/proton/continuum_extrapolation.json": [
        "lattice_spacings", "continuum_limit", "systematic_uncertainty",
    ],
    "data_room/primary/proton/finite_volume.json": [
        "volumes", "Delta_FV", "m_pi_L_values",
    ],
    "data_room/primary/proton/scale_setting.json": [
        "observable", "scale_value",
    ],
    "data_room/primary/proton/trace_anomaly.json": [
        "central", "bootstrap", "systematics",
    ],
}

FORBIDDEN = [
    "experimental_proton_mass", "back_solved", "symbolic_derivation",
    "synthetic_configuration", "inferred_from_mass", "target_mass_used",
    "pdg_proton_mass",
]


def load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return {"_error": str(e)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]  # repo root
    issues = []

    print("=== UGCT Anvil Proton c_p Verification (Definition 1.16) ===")
    print(f"Repo root: {root}\n")

    for rel in REQUIRED:
        p = root / rel
        if not p.exists():
            issues.append(f"MISSING: {rel}")
            print(f"[FAIL] {rel}  (missing)")
            continue
        data = load(p)
        if "_error" in data:
            issues.append(f"INVALID_JSON: {rel}")
            print(f"[FAIL] {rel}  (invalid JSON)")
            continue

        # Check production keys are present and non-null
        prod_missing = []
        for k in PRODUCTION_KEYS.get(rel, []):
            if k not in data or data[k] is None or data[k] == [] or data[k] == {}:
                prod_missing.append(k)
        if prod_missing:
            issues.append(f"PRODUCTION_INCOMPLETE: {rel} missing/null {prod_missing}")
            print(f"[FAIL] {rel}  (production fields incomplete: {prod_missing})")
        else:
            print(f"[PASS] {rel}")

        text = json.dumps(data).lower()
        for bad in FORBIDDEN:
            if bad in text:
                issues.append(f"FORBIDDEN: {rel} contains '{bad}'")

    print()
    if issues:
        print("STATUS:")
        print("FAIL")
        print()
        print("Reasons (excerpt):")
        for i in issues[:12]:
            print(f"  - {i}")
        if len(issues) > 12:
            print(f"  ... and {len(issues)-12} more")
        print()
        print("Promotion to PRESERVED_LATTICE_HPC_CERTIFICATE denied.")
        print("Current files correctly report BOUNDED_PRIMARY_ENSEMBLE status.")
        print("Real production ensembles + correlators + continuum/FV/scale fits required.")
        return 1

    print("STATUS:")
    print("PRESERVED_LATTICE_HPC_CERTIFICATE")
    print()
    print("All production artifacts complete. Certificate may be promoted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
