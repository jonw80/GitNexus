#!/usr/bin/env python3
"""Independent exact-rational audit of V12's finite-volume certificate.

This program imports no V11/V12 implementation or interval module. It uses
finite rational Taylor sums and a geometric tail, with substantially more
terms than the producer. Endpoint polynomials use descending Horner steps.
"""
from decimal import Decimal, Context, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math
import sys

sys.set_int_max_str_digits(0)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "wilson_closeout_v12/design/DIRECT_WILSON_SPECTRAL_CONTRACTION_CERTIFICATE.json"
BETA = F(271, 20)
E = 24
DOWN = Context(prec=100, rounding=ROUND_FLOOR)
UP = Context(prec=100, rounding=ROUND_CEILING)


def display(x, up=False):
    ctx = UP if up else DOWN
    return str(ctx.divide(Decimal(x.numerator), Decimal(x.denominator)))


def horner_exp(x, n):
    acc = F(1)
    for j in range(n, 0, -1):
        acc = 1 + x * acc / j
    return acc


def exponential_bounds(x, n):
    assert 0 <= x < n + 2
    lower = horner_exp(x, n)
    tail = x ** (n + 1) / math.factorial(n + 1) / (1 - x / (n + 2))
    return lower, lower + tail


def main():
    cert = json.loads(SOURCE.read_text())
    assert F(cert["beta_exact"]) == BETA
    assert cert["spatial_links"] == E
    assert F(cert["sharp_temporal_kernel_cross_ratio_log_diameter"]) == 3 * BETA * E
    for relative, expected in cert["source_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative

    exp_beta = exponential_bounds(BETA, 512)
    exp_half = exponential_bounds(BETA / 2, 512)
    exp_diameter_half = exponential_bounds(3 * BETA * E / 2, 1800)
    true_deficit = (2 / (exp_diameter_half[1] + 1), 2 / (exp_diameter_half[0] + 1))
    stored = cert["physical_normalized_spectral_deficit"]
    assert F(stored["lower"]) <= true_deficit[0] <= true_deficit[1] <= F(stored["upper"])

    def independent_epsilon(n):
        first = BETA ** (n + 1) / math.factorial(n + 1)
        positive = first / (1 - BETA / (n + 2)) / exp_beta[0]
        negative = exp_half[1] * (BETA / 2) ** (n + 1) / math.factorial(n + 1)
        return max(positive, negative)

    checks = []
    for row in cert["polynomial_certificates"]:
        n = row["order"]
        low = horner_exp(-BETA / 2, n)
        high = horner_exp(BETA, n)
        assert low == F(row["polynomial_minimum_exact"])
        assert high == F(row["polynomial_maximum_exact"])
        assert 0 < low < high
        assert row["one_link_representation_count"] == (n + 1) * (n + 2) // 2
        derivative_epsilon = independent_epsilon(n - 1)
        assert derivative_epsilon <= F(row["derivative_relative_error_upper"]) < 1
        ratio = (low / high) ** E
        deficit = 2 * ratio / (1 + ratio)
        stored_deficit = row["surrogate_normalized_spectral_deficit"]
        assert F(stored_deficit["lower"]) <= deficit <= F(stored_deficit["upper"])
        eps = independent_epsilon(n)
        # Exact rational arithmetic loses no tiny increment in 1+epsilon.
        eta_upper = (1 + eps) ** E - 1
        stored_eta = F(row["normalized_approximation_error_upper"])
        assert eta_upper <= stored_eta
        gap_lower = max(F(0), deficit - eta_upper)
        assert F(row["physical_gap_via_surrogate_lower"]) <= gap_lower
        passes = deficit > stored_eta
        assert passes == row["physical_gap_via_surrogate_certified_positive"]
        assert row["full_Gram_matrix_computed"] is False
        assert row["surrogate_eigenvalues_diagonalized"] is False
        checks.append({
            "order": n,
            "endpoint_fractions_match": True,
            "monotonicity_bound_verified": True,
            "exact_deficit_enclosure_verified": True,
            "independent_eta_upper": display(eta_upper, True),
            "reported_eta_is_conservative": True,
            "independent_surrogate_gap_lower": display(gap_lower),
            "reported_sufficient_gap_test_passes": passes,
        })
    assert all(cert[k] is False for k in ["target_gap_0_015_closed", "volume_uniform_gap_closed", "continuum_obligations_closed", "complete_yang_mills_proof"])
    report = {
        "schema": "YM_V12_INDEPENDENT_RATIONAL_SPECTRAL_AUDIT",
        "status": "PASS",
        "arithmetic": "Exact Fraction throughout; independent descending Horner evaluation and rational geometric exponential tails. Decimal is used only to print outward intervals.",
        "exponential_orders": {"beta": 512, "beta_over_two": 512, "diameter_over_two": 1800},
        "independent_physical_gap_deficit_interval": {
            "lower": display(true_deficit[0]),
            "upper": display(true_deficit[1], True),
        },
        "polynomial_checks": checks,
        "producer_source_hashes_verified": len(cert["source_sha256"]),
        "mathematical_review": "SPECTRAL_CONTRACTION_REVIEW.md",
        "certificate_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "continuum_claim": False,
    }
    output = HERE / "INDEPENDENT_SPECTRAL_CONTRACTION_AUDIT.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "orders_checked": len(checks), "physical_gap_deficit_interval": report["independent_physical_gap_deficit_interval"]}, indent=2))


if __name__ == "__main__":
    main()
