#!/usr/bin/env python3
"""Independent rational Taylor bounds; imports no interval implementation."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent


def rational_exp_bounds(x, order):
    x = F(x)
    assert 0 <= x < order + 2
    term = total = F(1)
    for j in range(1, order + 1):
        term *= x/j
        total += term
    first = term*x/(order + 1)
    tail = first/(1-x/(order + 2))
    return total, total+tail


def main():
    path = HERE / "FINITE_NEUTRAL_CHANNEL_CERTIFICATE.json"
    c = json.loads(path.read_text())
    beta = F(c["exact_beta"])
    lo, hi = rational_exp_bounds(9*beta, 1000)
    vl, vu = 1/(2*hi), 1/(2*lo)
    recorded = c["true_connected_variance_lower_bound_enclosure"]
    assert F(recorded["lower"]) <= vl <= vu <= F(recorded["upper"])
    lo, hi = rational_exp_bounds(F(3,2)*beta*24, 2400)
    dl, du = 2/(hi+1), 2/(lo+1)
    recorded = c["spectral_deficit_enclosure"]
    assert F(recorded["lower"]) <= dl <= du <= F(recorded["upper"])
    recorded = c["integrated_autocorrelation_upper_bound_enclosure"]
    assert F(recorded["lower"]) <= lo <= hi <= F(recorded["upper"])
    assert c["continuum_field_identification_closed"] is False
    assert c["volume_uniform_gap_closed"] is False
    result = {"status": "PASS_EXACT_RATIONAL_INDEPENDENT_CONSTANTS",
              "method": "Direct positive Taylor series at full argument plus geometric tail, exact Fraction arithmetic; no Decimal or interval module imports",
              "orders": {"variance_exponential": 1000, "spectral_exponential": 2400},
              "variance_floor_enclosure_verified": True,
              "spectral_deficit_enclosure_verified": True,
              "integrated_autocorrelation_enclosure_verified": True,
              "scope_flags_verified": True,
              "certificate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / "INDEPENDENT_NEUTRAL_CONSTANTS_CHECK.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
