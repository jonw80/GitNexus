#!/usr/bin/env python3
"""Materialize the exact temporal factor for the V12 spectral cutoff.

No spatial Gram matrix is computed. All character numerators are positive
integers over one common denominator; normalized convolution eigenvalues
are numerator[r]/(dim[r]*numerator[0,0]).
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import gzip
import hashlib
import json
import math
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "wilson_transfer_v11"))
from certify_polynomial_transfer import fusion, dim
from certify_direct_spectral_contraction import polynomial

ORDER = 248


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    began = time.monotonic()
    n = ORDER
    factorial = math.factorial(n)
    denominator = 120**n * factorial
    sums = defaultdict(int)
    mult = {(0, 0): 1}
    tensor_checks = []
    for degree in range(n + 1):
        assert sum(dim(*r) * v for r, v in mult.items()) == 6**degree
        tensor_checks.append({"degree": degree, "representations": len(mult)})
        weight = 271**degree * 120**(n - degree) * (factorial // math.factorial(degree))
        for r, v in mult.items():
            sums[r] += v * weight
        if degree < n:
            nxt = defaultdict(int)
            for r, v in mult.items():
                for target in fusion(*r):
                    nxt[target] += v
            mult = nxt
    expected = {(p, q) for p in range(n + 1) for q in range(n + 1 - p)}
    assert set(sums) == expected
    assert all(v > 0 and v == sums[r[::-1]] for r, v in sums.items())
    # Independent character evaluation: Jacobi-Trudi and the generating
    # series 1/(1-t*z+t*z^2-z^3), not the fundamental fusion recursion.
    evaluation_checks = []
    for trace in [-1, 0, 1, 2, 3]:
        h = [1]
        for k in range(1, n + 2):
            h.append(trace * h[k-1] - (trace * h[k-2] if k >= 2 else 0) + (h[k-3] if k >= 3 else 0))
        numerator = 0
        for (p, q), value in sums.items():
            character = h[p+q] * h[q] - (h[p+q+1] * h[q-1] if q else 0)
            numerator += value * character
        expected_value = polynomial(F(271, 60) * trace, n)
        assert F(numerator, denominator) == expected_value
        evaluation_checks.append({"SU3_fundamental_trace": trace, "exact_identity_passed": True})
    triality_sums = [sum(dim(*r) * v for r, v in sums.items() if (r[0] + 2*r[1]) % 3 == t) for t in range(3)]
    assert triality_sums[1] == triality_sums[2]
    assert F(2*triality_sums[0] - triality_sums[1] - triality_sums[2], 2*denominator) == polynomial(F(-271,40), n)
    payload = {
        "schema": "YM_EXACT_WILSON_TEMPORAL_FACTOR_ORDER248_V12",
        "order": n, "beta_exact": "271/20", "representation_count": len(sums),
        "character_polynomial": "sum_j=0^248 [(271/120)(chi_3+chi_3bar)]^j/j!",
        "common_character_denominator": str(denominator),
        "polynomial_partition_numerator": str(sums[(0,0)]),
        "normalized_one_link_eigenvalue_formula": "character_numerator/(representation_dimension*polynomial_partition_numerator)",
        "absolute_suboperator_normalization": "Replace polynomial partition by true Z_beta before claiming T_n<=T. The scalar cancels from Perron-normalized full T_n.",
        "representations": [
            {"p": p, "q": q, "dimension": dim(p,q), "character_numerator": str(sums[(p,q)])}
            for p, q in sorted(sums, key=lambda r:(sum(r),r))
        ],
        "full_spatial_Gram_executed": False,
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / "wilson_transfer_v11/certify_polynomial_transfer.py"]},
    }
    path = HERE / "EXACT_ORDER248_TEMPORAL_FACTOR.json.gz"
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write((json.dumps(payload, separators=(",", ":")) + "\n").encode())
    certificate = {
        "schema": "YM_ORDER248_TEMPORAL_FACTOR_GENERATION_CHECK_V12",
        "status": "PASS", "order": n, "representation_count": len(sums),
        "strict_positive_coefficients_checked": len(sums),
        "conjugation_identities_checked": len(sums),
        "tensor_dimension_identities_checked": len(tensor_checks),
        "independent_Jacobi_Trudi_evaluations": evaluation_checks,
        "center_endpoint_exact_identity_passed": True,
        "coefficient_file": path.name, "coefficient_file_sha256": sha(path),
        "coefficient_file_bytes": path.stat().st_size,
        "elapsed_seconds": time.monotonic() - began,
        "full_spatial_Gram_matrix_executed": False,
        "finite_eigenvalues_diagonalized": False,
    }
    (HERE / "ORDER248_TEMPORAL_GENERATION_CHECK.json").write_text(json.dumps(certificate, indent=2) + "\n")
    print(json.dumps(certificate, indent=2))


if __name__ == "__main__":
    main()
