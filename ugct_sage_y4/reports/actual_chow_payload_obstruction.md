# Actual Chow Payload Obstruction

Status: `ACTUAL_ESOLE_YAU_EWX_QUOTIENT_IDEAL_DATA_NOT_PRESENT`

This is the final tensor blocker. The workflow is complete and attempts the computation in the correct order. The remaining problem is not a missing script step; it is the absence of the actual compactification-specific Esole--Yau `Ewx` resolved ambient Chow presentation.

## Required file

`ugct_sage_y4/data/esole_yau_ewx_resolved_ambient_chow.json`

## Required concrete payload

The file must contain either:

1. A complete exact table:

```json
"exceptional_intersection_values": {
  "<canonical degree-four monomial>": "<exact integer/rational>",
  "... all 1509 exceptional monomials ...": "..."
}
```

or:

2. A Sage-computable quotient presentation:

```json
"sage_polynomial_mode": {
  "variables": [...],
  "quotient_ideal_generators": [
    "full SR ideal generators",
    "full linear-equivalence generators",
    "proper-transform / complete-intersection relations"
  ],
  "divisor_lifts": {...},
  "integration_functional": {
    "top_monomial_values": {...}
  }
}
```

## Why this cannot be generated from the current package alone

The current package contains:

- the supported `dP8/B3/zero-section/A4-Cartan-pair` sector;
- the GitHub Sage execution environment;
- the exceptional-rule loader;
- the quotient-ring reduction interface;
- the active `y4_intersection_ring_full.json` validator target.

It does not contain the actual resolved ambient SR ideal, the resolved ambient linear-equivalence ideal, the proper-transform class, or the integration functional for the chosen Esole--Yau `Ewx` chamber. Without those exact algebraic data, any numerical/rational assignment to the 1509 exceptional monomials would be invented and cannot be used as a certificate.

## Current exact workflow result

The workflow now correctly reports:

```text
CHOW_INPUT_INCOMPLETE
No quotient ideal generators supplied; exact SR/linear/proper-transform relations are absent.
missing_keys:
  - sage_polynomial_mode.quotient_ideal_generators
  - sr_ideal_generators
  - linear_equivalence_generators
  - proper_transform_class
```

## Closure condition

The tensor block closes only when the workflow reports:

```text
EXCEPTIONAL_RULES_COMPUTED_AND_VERIFIED
unsupported_multisets = 0
full_chamber_specific_tensor_verified = true
FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED
```
