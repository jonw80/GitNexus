#!/usr/bin/env python3
"""Aggregate all certificate JSONs into data_room/data/INDEX.json with
tier, status, and reproduction command per item.
"""
import argparse, json, sys
from pathlib import Path

ITEMS = [
    ("1", "flux_scan_summary.json", 2, "scan_flux_lattice.py"),
    ("2", "pf_basis.json", 1, "compute_pf_basis.py"),
    ("3", "attractor_intervals.json", 1, "attractor_interval_solve.py"),
    ("4", "axio_dilaton_interval.json", 1, "axio_dilaton_solve.py"),
    ("5", "instanton_divisors.json", 1, "instanton_zero_modes.jl"),
    ("6", "hidden_sector_ranks.json", 1, "hidden_sector_scan.py"),
    ("7", "pfaffian_prefactors.json", 3, "pfaffian_zero_locus.jl"),
    ("8", "racetrack_superpotential.json", 2, "assemble_racetrack.py"),
    ("9", "string_loop_coefficients.json", 2, "string_loop_coefficients.py"),
    ("10", "kahler_stabilization_certificate.json", 1, "kahler_stabilize.py"),
    ("11", "warp_factor_certificate.json", 2, "warp_factor.py"),
    ("12", "uplift_backreaction_certificate.json", 3, "backreaction_static_check.py"),
    ("13", "cosmological_constant_error_budget.json", 2, "cosmo_const_budget.py"),
    ("14", "cp_trace_anomaly_certificate.json", 2, "cp_anomaly_from_flag.py"),
    ("15", "global_arithmetic_id_certificate.tex", 1, "(in proofs/, see manuscript)"),
    ("16", "prime_race_density_certificate.json", 2, "prime_race_delta.py"),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data_room/data"))
    ap.add_argument("--out", type=Path, default=Path("data_room/data/INDEX.json"))
    args = ap.parse_args()
    
    index = {"schema_version": "1.0", "items": []}
    for (item_id, filename, expected_tier, script) in ITEMS:
        path = args.data_dir / filename
        entry = {
            "item_id": item_id,
            "file": filename,
            "expected_tier": expected_tier,
            "reproduction_script": script,
        }
        if path.exists():
            try:
                with open(path) as f:
                    d = json.load(f) if filename.endswith(".json") else {}
                entry["status"] = d.get("status", "present")
                entry["tier_reported"] = d.get("tier", expected_tier)
                entry["fully_certified"] = d.get("fully_certified", None)
            except Exception as e:
                entry["status"] = f"error: {e}"
        else:
            entry["status"] = "absent"
        index["items"].append(entry)
    
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(index, f, indent=2)
    print(f"WROTE {args.out}")
    print(f"  {sum(1 for e in index['items'] if e['status']=='present')} / "
          f"{len(index['items'])} items present")
    return 0

if __name__ == "__main__":
    sys.exit(main())
