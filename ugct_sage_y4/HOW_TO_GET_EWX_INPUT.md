# How to obtain the exact Esole-Yau `Ewx` Chow computation input

The final 235 higher-Cartan values cannot be certified from the current partial JSON. They require one explicit algebraic-geometry computation: the resolved ambient Chow ring of the chosen Esole-Yau `Ewx` small-resolution chamber.

The workflow expects the result to be inserted into:

```text
data/esole_yau_ewx_resolved_ambient_chow.json
```

under the block:

```json
"exact_higher_cartan_computation": {
  "status": "RESOLVED_EWX_HIGHER_CARTAN_INPUT_VERIFIED",
  "variables": [],
  "quotient_ideal_generators": [],
  "divisor_lifts": {},
  "integration_functional": {
    "top_monomial_values": {}
  },
  "provenance": {
    "toolchain": "SageMath or Macaulay2 or OSCAR",
    "toolchain_version": "...",
    "source_geometry": "Esole-Yau split SU(5)/A4 Ewx small resolution over B3=P(O+K_dP8)",
    "sr_linear_ideal_hash": "sha256:...",
    "proper_transform_hash": "sha256:...",
    "script_hash": "sha256:...",
    "independent_rerun_hash": "sha256:..."
  }
}
```

## What must be computed

The required exact values are the remaining degree-four monomials:

```text
D_base * C_i * C_j * C_k     200 values
C_i * C_j * C_k * C_l         35 values
```

where:

```text
D_base in {R,H,E1,...,E8}
C_i in {C1,C2,C3,C4}
```

These are not determined by the universal A4 Cartan-pair rule alone. They depend on the actual resolved ambient exceptional geometry of the chosen small-resolution chamber.

## Required mathematical input

To compute them, construct the global resolved ambient Chow ring:

```text
A^*(resolved ambient) / <SR ideal, linear equivalences, proper-transform equations>
```

for the `Ewx` chamber, including:

1. Ambient divisor variables.
2. Blowup sequence for the selected `Ewx` resolution.
3. Full Stanley-Reisner ideal after all blowups.
4. Full linear-equivalence ideal after all blowups.
5. Proper-transform Tate hypersurface / complete-intersection equations.
6. Divisor lifts for `R,H,E1,...,E8,Z,C1,...,C4` into the resolved ambient ring.
7. Integration functional for top-degree normal forms.

## Practical route in Sage/Macaulay2/OSCAR

1. Start from the split SU(5) Tate model over `B3=P(O+K_dP8)`.
2. Use the Esole-Yau `Ewx` small-resolution chamber.
3. Encode the blowups as a resolved ambient toric/Chow presentation.
4. Build the quotient ideal from:
   - SR generators,
   - linear-equivalence generators,
   - proper-transform equations.
5. Reduce every required monomial modulo the quotient ideal.
6. Integrate the resulting top-degree normal forms using the base `dP8/B3` integration map.
7. Export the 235 values as exact integers/rationals.
8. Populate `exact_higher_cartan_computation` or directly populate `data/higher_cartan_closure_rules.json -> exact_values` with provenance.

## Acceptance test

After populating the exact input, run:

```bash
cd ugct_sage_y4
sage -python compute_higher_cartan_exact_values.sage
sage -python compute_exceptional_rules_from_chow.sage
python3 extract_higher_cartan_requirements.py
python3 validate_higher_cartan_exact_certificate.py
sage -python run_chow_tensor.sage
python3 validate_full_payload.py
```

A successful exact closure gives:

```text
EXACT_HIGHER_CARTAN_COMPUTATION_COMPLETED
EXACT_HIGHER_CARTAN_CERTIFICATE_VERIFIED
EXCEPTIONAL_SECTOR_VERIFIED
FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED
```

If the result is instead:

```text
EXACT_HIGHER_CARTAN_COMPUTATION_NOT_RUN
```

then the resolved `Ewx` Chow-ring input is still not supplied.

## Important rule

Do not certify the final 235 values by setting them to zero unless the resolved `Ewx` Chow-ring computation proves those exact zero values. Fallback execution is useful for testing pipeline completeness, but it is not an independent exact self-intersection certificate.
