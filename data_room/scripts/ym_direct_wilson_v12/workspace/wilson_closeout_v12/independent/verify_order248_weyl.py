#!/usr/bin/env python3
"""Independently check every order-248 Wilson coefficient using exact weights.

Only Python's standard library is used. No fusion-rule recurrence is imported or
used: this computes powers of the six fundamental/antifundamental Laurent
monomials, then extracts irreducible characters with the SU(3) Weyl denominator.

Run from any directory, optionally supplying --input and --output paths.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
from itertools import permutations
import json
import math
from pathlib import Path
import time


def dimension(p: int, q: int) -> int:
    return (p + 1) * (q + 1) * (p + q + 2) // 2


def verify(source: Path) -> dict:
    raw = source.read_bytes()
    payload = gzip.decompress(raw) if source.suffix == ".gz" else raw
    cert = json.loads(payload)
    n = cert["order"]
    if n != 248 or Fraction(cert["beta_exact"]) != Fraction(271, 20):
        raise AssertionError("This verifier is pinned to order 248, beta 271/20")
    common = int(cert["common_character_denominator"])
    assert common == 120 ** n * math.factorial(n)
    assert cert["representation_count"] == (n + 1) * (n + 2) // 2

    # At diag(x,y,(xy)^-1), chi_3+chi_3bar has weights
    # (1,0),(0,1),(-1,-1),(-1,0),(0,-1),(1,1).
    # The integer encoding x*stride+y is injective throughout the complete walk
    # and Weyl-extraction domains because their y-range has width < stride.
    stride = 4 * n + 17
    steps = (stride, 1, -stride - 1, -stride, -1, stride + 1)
    walks = {0: 1}
    polynomial = defaultdict(int)
    integer_weight = common
    expected_walk_count = 1
    walk_digest = hashlib.sha256()
    for k in range(n + 1):
        total_walk_count = sum(walks.values())
        assert total_walk_count == expected_walk_count
        walk_digest.update(f"{k}:{total_walk_count}\n".encode("ascii"))
        for weight, multiplicity in walks.items():
            polynomial[weight] += integer_weight * multiplicity
        if k < n:
            nxt = defaultdict(int)
            a, b, c, d, e, f = steps
            for weight, multiplicity in walks.items():
                nxt[weight + a] += multiplicity
                nxt[weight + b] += multiplicity
                nxt[weight + c] += multiplicity
                nxt[weight + d] += multiplicity
                nxt[weight + e] += multiplicity
                nxt[weight + f] += multiplicity
            walks = nxt
            integer_weight, remainder = divmod(integer_weight * 271, 120 * (k + 1))
            assert remainder == 0
            expected_walk_count *= 6
        if k % 32 == 0 or k == n:
            print(f"Laurent powers: {k}/{n}; {len(walks)} monomials", flush=True)

    # A_rho=sum_w sign(w)e^(w rho), rho=(2,1,0) in three eigenvalue
    # exponents. The coefficient at lambda+rho=(p+q+2,q+1) is a_(p,q).
    denominator = []
    for perm in permutations((2, 1, 0)):
        inversions_from_descending = sum(
            perm[i] < perm[j] for i in range(3) for j in range(i + 1, 3)
        )
        denominator.append((
            (perm[0] - perm[2]) * stride + perm[1] - perm[2],
            (-1) ** inversions_from_descending,
        ))

    coefficients = {}
    for row in cert["representations"]:
        p, q = row["p"], row["q"]
        assert isinstance(p, int) and isinstance(q, int) and p >= 0 and q >= 0
        assert (p, q) not in coefficients, "Duplicate representation"
        target = (p + q + 2) * stride + q + 1
        value = sum(sign * polynomial.get(target - shift, 0)
                    for shift, sign in denominator)
        assert value == int(row["character_numerator"]) > 0, (p, q)
        assert row["dimension"] == dimension(p, q), (p, q)
        coefficients[p, q] = value

    assert set(coefficients) == {
        (p, q) for p in range(n + 1) for q in range(n + 1 - p)
    }
    partition = coefficients[0, 0]
    assert partition == int(cert["polynomial_partition_numerator"])
    for (p, q), value in coefficients.items():
        assert value == coefficients[q, p]

    # Independent evaluation at the identity: every one of the six Laurent
    # monomials is 1, and beta=6*(271/120). All quantities remain integers.
    identity_numerator = 0
    integer_weight = common
    six_power = 1
    for k in range(n + 1):
        identity_numerator += integer_weight * six_power
        if k < n:
            integer_weight, remainder = divmod(integer_weight * 271, 120 * (k + 1))
            assert remainder == 0
            six_power *= 6
    dimension_weighted_sum = sum(dimension(p, q) * v
                                 for (p, q), v in coefficients.items())
    assert dimension_weighted_sum == identity_numerator == sum(polynomial.values())

    # Exhaust the immediate possible dominant boundary outside p+q<=n.
    # For p+q>n, target_x>=n+3 and every A_rho x-shift<=2, so the
    # required Laurent x-coordinate exceeds n. Such coefficients are zero.
    outside_checked = 0
    for p in range(n + 2):
        q = n + 1 - p
        target = (p + q + 2) * stride + q + 1
        assert sum(sign * polynomial.get(target - shift, 0)
                   for shift, sign in denominator) == 0
        outside_checked += 1

    values_digest = hashlib.sha256()
    for (p, q), value in sorted(coefficients.items()):
        values_digest.update(f"{p},{q}:{value}\n".encode("ascii"))

    return {
        "schema": "YM_V12_INDEPENDENT_ORDER248_WEYL_VERIFICATION",
        "status": "PASS_ALL_31125_EXACT_CHARACTER_NUMERATORS",
        "order": n,
        "beta_exact": "271/20",
        "coefficient_count": len(coefficients),
        "all_exact_coefficients_match": True,
        "all_dimensions_match": True,
        "all_conjugation_identities_match": True,
        "polynomial_partition_matches": True,
        "exact_identity_value_matches": True,
        "support_complete_through_order": True,
        "outside_boundary_coefficients_checked": outside_checked,
        "all_more_distant_dominant_coefficients_zero_reason":
            "Laurent x-support is [-n,n]; target_x=p+q+2; every Weyl x-shift<=2.",
        "laurent_monomial_count": len(polynomial),
        "walk_dimension_identities_checked": n + 1,
        "walk_dimension_sequence_sha256": walk_digest.hexdigest(),
        "canonical_exact_coefficient_sha256": values_digest.hexdigest(),
        "normalized_eigenvalue_interpretation":
            "Each table eigenvalue is a_(p,q)/(dim(p,q)*a_(0,0)); all exact factors verified. "
            "This uses polynomial Z_n, not true Z_beta. Restore Z_n/Z_beta before absolute Loewner comparisons.",
        "method": "Exact six-weight Laurent walks followed by Weyl antisymmetrization; no fusion recurrence.",
        "full_spatial_Gram_executed": False,
        "spatial_transfer_spectrum_computed": False,
        "continuum_claim": False,
        "source_sha256": {
            source.name: hashlib.sha256(raw).hexdigest(),
            "decompressed_input": hashlib.sha256(payload).hexdigest(),
            Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=here.parent / "design/EXACT_ORDER248_TEMPORAL_FACTOR.json.gz")
    parser.add_argument("--output", type=Path,
                        default=here / "ORDER248_WEYL_VERIFICATION.json")
    args = parser.parse_args()
    started = time.monotonic()
    result = verify(args.input)
    result["elapsed_seconds"] = time.monotonic() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"],
                      "coefficient_count": result["coefficient_count"],
                      "elapsed_seconds": result["elapsed_seconds"],
                      "certificate": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
