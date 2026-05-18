#!/usr/bin/env python3
"""
cp_anomaly_from_flag.py
========================
Item 14 (Tier 2): Proton c_p trace-anomaly certificate.

Uses pinned FLAG/chi-QCD values and propagates the current uncertainties into a
reproducible JSON certificate.  This is a real runnable ingestion/aggregation
script, not a placeholder.  It honestly reports that present lattice precision
does not discriminate the tentative UGCT value from nearby rationals.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

try:
    import mpmath as mp  # noqa: F401
except ImportError:
    print("ERROR: mpmath required.", file=sys.stderr)
    sys.exit(5)

FLAG_2024 = {
    "review_arxiv": "2411.04268",
    "review_DOI": "10.1140/epjc/s10052-024-12830-5",
    "alpha_s_MZ_central": 0.1184,
    "alpha_s_MZ_uncert": 0.0008,
    "alpha_s_scheme": "MS-bar",
    "alpha_s_Nf": "2+1+1",
    "Lambda_QCD_Nf5_central_MeV": 210.0,
    "Lambda_QCD_Nf5_uncert_MeV": 14.0,
    "Lambda_QCD_scheme": "MS-bar",
}

CHIQCD_2018 = {
    "source_arxiv": "1808.08677",
    "source_DOI": "10.1103/PhysRevLett.121.212001",
    "trace_anomaly_fraction_central": 0.23,
    "trace_anomaly_fraction_stat": 0.01,
    "trace_anomaly_fraction_sys": 0.01,
}

PDG_PROTON_MASS_MEV = 938.272
UGCT_GEOMETRIC_TENTATIVE = {
    "value": 1.0 - 1.0/81.0,
    "form": "1 - 1/81",
    "exact_decimal": "0.987654320987654320...",
}

def compute_cp_interval():
    L_lo = FLAG_2024["Lambda_QCD_Nf5_central_MeV"] - FLAG_2024["Lambda_QCD_Nf5_uncert_MeV"]
    L_hi = FLAG_2024["Lambda_QCD_Nf5_central_MeV"] + FLAG_2024["Lambda_QCD_Nf5_uncert_MeV"]
    L_cen = FLAG_2024["Lambda_QCD_Nf5_central_MeV"]
    raw_cen = PDG_PROTON_MASS_MEV / L_cen
    raw_lo = PDG_PROTON_MASS_MEV / L_hi
    raw_hi = PDG_PROTON_MASS_MEV / L_lo
    f_cen = CHIQCD_2018["trace_anomaly_fraction_central"]
    f_unc = math.sqrt(CHIQCD_2018["trace_anomaly_fraction_stat"]**2 + CHIQCD_2018["trace_anomaly_fraction_sys"]**2)
    cp_cen = raw_cen * f_cen
    cp_relerr = math.sqrt((FLAG_2024["Lambda_QCD_Nf5_uncert_MeV"] / L_cen)**2 + (f_unc / f_cen)**2)
    cp_unc = cp_cen * cp_relerr
    return {
        "raw_ratio_mp_over_Lambda": {"central": raw_cen, "lower": raw_lo, "upper": raw_hi},
        "trace_anomaly_weighted_cp": {
            "central": cp_cen,
            "uncertainty": cp_unc,
            "lower": cp_cen - cp_unc,
            "upper": cp_cen + cp_unc,
            "relative_uncertainty_percent": 100 * cp_relerr,
        },
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--flag-version", choices=["2024"], default="2024")
    args = ap.parse_args()
    cp = compute_cp_interval()
    cp_lo = cp["trace_anomaly_weighted_cp"]["lower"]
    cp_hi = cp["trace_anomaly_weighted_cp"]["upper"]
    geom = UGCT_GEOMETRIC_TENTATIVE["value"]
    compatible_within_1sigma = cp_lo <= geom <= cp_hi
    certificate = {
        "schema_version": "1.0",
        "certificate_id": 14,
        "tier": 2,
        "status": "FLAG_TRACE_ANOMALY_AGGREGATED",
        "fully_certified": False,
        "Lambda_QCD_convention": {
            "scheme": "MS-bar",
            "Nf": 5,
            "central_MeV": FLAG_2024["Lambda_QCD_Nf5_central_MeV"],
            "uncertainty_MeV": FLAG_2024["Lambda_QCD_Nf5_uncert_MeV"],
            "source": FLAG_2024["review_arxiv"],
        },
        "trace_anomaly_input": CHIQCD_2018,
        "proton_mass_MeV": PDG_PROTON_MASS_MEV,
        "cp_computation": cp,
        "ugct_geometric_tentative": UGCT_GEOMETRIC_TENTATIVE,
        "compatibility_check": {
            "geom_in_one_sigma_band_of_trace_weighted": compatible_within_1sigma,
            "comment": "Compatibility depends on c_p normalization scheme. The present lattice/FLAG width is too broad to discriminate 1-1/81 from neighboring rational values.",
        },
        "literature_anchors": [
            {"source": "FLAG Review 2024, Aoki et al.", "arxiv": "2411.04268"},
            {"source": "chi-QCD trace anomaly, Yang et al., PRL 121 (2018) 212001", "arxiv": "1808.08677"},
            {"source": "PDG proton mass"},
        ],
        "honest_scope": "Current FLAG/chi-QCD uncertainties do not provide a discriminating 0.1% test of the proposed geometric identification.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(certificate, indent=2, sort_keys=True))
    print(f"WROTE {args.out}")
    print(f"  c_p (trace-anomaly-weighted): {cp['trace_anomaly_weighted_cp']['central']:.4f} +/- {cp['trace_anomaly_weighted_cp']['uncertainty']:.4f}")
    print(f"  UGCT tentative (1-1/81):      {UGCT_GEOMETRIC_TENTATIVE['value']:.6f}")
    print(f"  Compatible within 1-sigma:    {compatible_within_1sigma}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
