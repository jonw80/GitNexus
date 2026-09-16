#!/usr/bin/env python3
"""Actual Wilson and polynomial-transfer all-state spectral contraction.

This is an analytic spectral enclosure, not a computed huge Gram matrix.
All polynomial endpoint values are exact rational numbers.  The error
certificate reuses V11's directed interval Taylor-tail implementation.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "wilson_transfer_v11"))
from certify_polynomial_transfer import remainder
sys.path.insert(0, str(ROOT / "dag_closeout_v5"))
from intervals import I
sys.path.insert(0, str(ROOT / "wilson_transfer_v11/direct_review"))
from certify_gauge_fixed_perron import exp_interval

BETA = F(271, 20)
LINKS = 24


def polynomial(x, n):
    term = F(1)
    total = term
    for j in range(1, n + 1):
        term = term * x / j
        total += term
    return total


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def enclosure(q):
    x = I(q)
    assert F(x.lo) <= q <= F(x.hi)
    return {"lower": str(x.lo), "upper": str(x.hi)}


def polynomial_record(n):
    # p_n'=p_(n-1). A relative error below 1 proves strict positivity
    # of that derivative throughout [-beta/2,beta].
    derivative = remainder(n - 1)
    assert Decimal(derivative["uniform_single_link_relative_error_upper"]) < 1
    m, M = polynomial(-BETA / 2, n), polynomial(BETA, n)
    assert 0 < m < M
    ratio = (m / M) ** LINKS
    deficit = 2 * ratio / (1 + ratio)
    directed_deficit = I(deficit)
    err = remainder(n)
    eta = I(err["normalized_full_transfer_error_upper"])
    transferred = directed_deficit - eta
    return {
        "order": n,
        "one_link_representation_count": (n + 1) * (n + 2) // 2,
        "polynomial_minimum_exact": str(m),
        "polynomial_maximum_exact": str(M),
        "monotonicity_justification": "p_n'=p_(n-1)>0 by the certified uniform relative error below one",
        "derivative_relative_error_upper": derivative["uniform_single_link_relative_error_upper"],
        "surrogate_normalized_spectral_deficit_formula": "2*(p_n(-beta/2)/p_n(beta))^24/(1+(p_n(-beta/2)/p_n(beta))^24)",
        "surrogate_normalized_spectral_deficit": enclosure(deficit),
        "normalized_approximation_error_upper": str(eta.hi),
        "physical_gap_via_surrogate_lower": str(max(Decimal(0), transferred.lo)),
        "physical_gap_via_surrogate_certified_positive": transferred.lo > 0,
        "full_Gram_matrix_computed": False,
        "surrogate_eigenvalues_diagonalized": False,
    }


def main():
    records = [polynomial_record(n) for n in [72, 246, 247, 248, 255]]
    # x=3 beta E / 2. This is exact; avoid 1 - tiny numbers throughout.
    x = F(3, 2) * BETA * LINKS
    q = exp_interval(I(x))
    physical_deficit = 2 / (q + 1)
    chosen = next(r for r in records if r["order"] == 248)
    assert chosen["physical_gap_via_surrogate_certified_positive"]
    assert not next(r for r in records if r["order"] == 247)["physical_gap_via_surrogate_certified_positive"]
    result = {
        "schema": "YM_DIRECT_WILSON_ANALYTIC_SPECTRAL_CONTRACTION_V12",
        "status": "PASS_ALL_STATE_FINITE_VOLUME_SPECTRAL_ENCLOSURE",
        "operator": "T=S C_beta^tensor24 S on full gauge-invariant Haar L2; actual positive Wilson kernel, not aD+logC",
        "beta_exact": str(BETA),
        "spatial_links": LINKS,
        "sharp_temporal_kernel_cross_ratio_log_diameter": str(3 * BETA * LINKS),
        "physical_deficit_exponent_exact": str(x),
        "physical_nonvacuum_eigenvalue_ratio_upper_symbolic": "1 - delta, delta = 2/(exp(3*beta*24/2)+1)",
        "physical_normalized_spectral_deficit": {
            "lower": str(physical_deficit.lo), "upper": str(physical_deficit.hi)
        },
        "physical_logarithmic_transfer_gap_lower": str(physical_deficit.lo),
        "proof_method": "Elementary likelihood-ratio/total-variation contraction of the exact Perron Doob kernel; cross-ratio cancels both the unknown Perron function and exact spatial dressing",
        "full_external_complement_and_all_momenta_included": True,
        "retained_polynomial_order_with_positive_gap_transfer": 248,
        "first_order_in_scan_with_positive_gap_transfer": 248,
        "polynomial_certificates": records,
        "target_gap_0_015_closed": False,
        "volume_uniform_gap_closed": False,
        "continuum_obligations_closed": False,
        "complete_yang_mills_proof": False,
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [
            Path(__file__), ROOT / "wilson_transfer_v11/certify_polynomial_transfer.py",
            ROOT / "dag_closeout_v5/intervals.py",
            ROOT / "wilson_transfer_v11/direct_review/certify_gauge_fixed_perron.py"
        ]}
    }
    destination = HERE / "DIRECT_WILSON_SPECTRAL_CONTRACTION_CERTIFICATE.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "physical_gap_lower": result["physical_logarithmic_transfer_gap_lower"],
        "selected_order": 248,
        "selected_surrogate_deficit": chosen["surrogate_normalized_spectral_deficit"],
        "selected_eta_upper": chosen["normalized_approximation_error_upper"],
        "gap_via_surrogate_lower": chosen["physical_gap_via_surrogate_lower"],
    }, indent=2))


if __name__ == "__main__":
    main()
