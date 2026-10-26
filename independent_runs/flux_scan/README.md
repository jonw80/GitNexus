# Independent mass-free flux scan

Runs the manuscript's flux selection exactly as written, with no measured mass in any step.
Source: *UGCT_Principia_strengthened_post_review 5*, chapter "The Flux Attractor and Explicit
Integer Vectors": Definition "Flux-admissible attractor triple" and Section "Full Hypergeometric
Attractor Solve".

| Clause | What is run |
|---|---|
| (i) tadpole | every n in Z^4 with 0 < Σ n_i² ≤ 44 (9,696 vectors) |
| (ii) attractor closure | D_z W = 0, W(z) = Σ_μ n^μ ω_μ(0) ₄F₃(a_μ/5; 1,1,1; 3125z) |
| (iii) physical branch | real z* with 0 < 3125z* < 0.99 (and, separately, the negative branch) |
| (iv) hierarchy | Y_u < Y_c < Y_t, Y_d < Y_s < Y_b, Y_e < Y_μ < Y_τ over all triples |

The text leaves four things implicit, so each is run as a separate variant (none is tuned):
- monomial type b ↔ character a = b + (1,1,1,1,1) (Griffiths residue correspondence);
- ω_μ(0) = (1/5)∏Γ(a_i/5);
- the four ₄F₃ parameters: first four or last four entries of the sorted character;
- D_z: the flat derivative, or ∂_z + K_z with the manuscript's K = −log vol, vol = (5/6)|ω₀|².

Files (in `independent_runs/flux_scan/`): `mass_free_scan.py` (sharded scan), `merge_shards.py`, `census_iv.py` (clause iv),
`verify_printed.py` (printed vectors at 30 digits with mpmath).
The workflow `.github/workflows/mass-free-flux-scan.yml` runs eight shards in parallel and merges them.
