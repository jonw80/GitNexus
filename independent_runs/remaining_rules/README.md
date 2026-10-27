# Two remaining mass-free definitions, run as written

`remaining_rules_check.py` runs the two mass-free definitions in the UGCT record that the flux scan in
`independent_runs/flux_scan/` does not cover. No measured mass enters either test.

| Test | Source | What is run |
|---|---|---|
| A | κ₃ worked example (post-review-5 manuscript) | R(z) = (ω₁ω̄₂ − ω₂ω̄₁)/(2i\|ω₀\|²) at the printed z*, for each reading of ω₁, ω₂: raw Frobenius solutions, the (2πi)⁻ᵏ normalisation, and the integral symplectic pair (X¹, F₁) |
| B | Theorem 1.26, Definition "Intrinsic flux dominance predicate" | λ_max(Y†Y) > λ₂ > λ₁ with Y_f = D_f(N)^{1/2} Ω D_f(N)^{1/2}, printed κ, Ω = 1 (the manuscript gives no entries for Ω), C_lin rebuilt from the coupling of `data_room/scripts/fermat_101_period_derivative.py`; literal and generation-labelled readings over all 9,696³ triples |

Run: `python remaining_rules_check.py` (numpy, mpmath). The workflow
`.github/workflows/remaining-rules-check.yml` runs it on this branch only.
