# Law 1 exactness: pre-registered tests (2026-11-24)

Frozen before any value below was computed by script (gate G8). The commit hash and GitHub's
timestamp are the record. Results go in a separate, later commit.

**Target.** L = πΓ(1/5)³/Γ(2/5), exact. Measured α⁻¹(0) = 137.035999177(21) (CODATA 2022).
δ_obs = α⁻¹(0) − L. An exact law must reproduce δ_obs within ±1σ (σ = 2.1×10⁻⁸) with nothing
fitted and without using the measured α (G2).

**Candidates (no free parameters).**

| | Reading of Law 1 | Correction δ |
|---|---|---|
| A | α(0) itself | 0 |
| B | MS-bar coupling at μ = m_e in the electron-only effective theory | α⁻¹(0) − α̂⁻¹(m_e), two loops: α(0) = [1 − 15(α/4π)²]·α̂(m_e) at μ = on-shell m_e (Grozin, arXiv:1212.5144) |
| C | On-shell running coupling α(Q) at a scale fixed in advance: Q = α·m_e (Bohr momentum), m_e, m_μ, M_Pl | α⁻¹(0) − α⁻¹(Q), one-loop vacuum polarization of e, μ, τ, exact integral. M_Pl is the manuscript's "19 decades" argument. |
| D | Exact infrared coupling of a U(1) of type IIB on X₅ at the Fermat point. N = 2 special geometry is exact for vector multiplets, and at a CM point the gauge-kinetic matrix is algebraic (M1, T7), so α⁻¹ = 4π × an algebraic number. | Structural test: is L/π algebraic? Lean T9 says no, conditional on Rohrlich's conjecture (K1). |
| E | Scan of simple correction terms (p/q)·α^k·π^m, with p, q ∈ {1,…,10}, k ∈ {1, 2, 3}, m ∈ {−3,…,3} | Every term within ±1σ, and the chance that a target drawn at random (log-uniform on [δ_obs/2, 2δ_obs]) has at least one hit |

**Disclosure.** While this list was being written, the term α²/π was noticed to lie near δ_obs.
At leading order this is the same as reading C at Q = √15·α·m_e (14.4 keV), the manuscript's
bridge scale. It is therefore treated as a search result (G9), whatever its p-value.

**Decision rule.** A candidate from A–D that lands within ±1σ makes Law 1 exact under that reading.
A hit from E alone is an observation, not a derivation.
