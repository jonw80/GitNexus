# GitNexus Production Objective — Anvil Lattice/HPC Certificate

Goal

Produce the seven primary artifacts required for promotion:

- anvil_job_metadata.json
- raw_correlators_manifest.json
- analysis_windows.json
- continuum_extrapolation.json
- finite_volume.json
- scale_setting.json
- trace_anomaly.json

along with

verify_proton_cp_anvil.py

which should finish with

STATUS:
PRESERVED_LATTICE_HPC_CERTIFICATE

only if every verification passes.

---

Phase 1 — Environment

Provision

* MPI
* OpenMP
* CUDA (if GPUs)
* HDF5
* FFTW
* Eigen
* LAPACK
* BLAS
* Python
* NumPy
* SciPy
* pandas

Install one production lattice code such as:

* SIMULATeQCD
* Grid
* Chroma
* MILC

These provide production HMC, Dirac solvers, and gauge-field evolution suitable for large lattice calculations.

---

Phase 2 — Gauge Ensembles

Generate real SU(3) gauge fields.

Target:

Nf = 2+1(+1)
β values: β1, β2, β3
Physical pion mass
Three lattice spacings minimum
Two physical volumes minimum
mπL > 4

Every configuration receives

configuration_id
trajectory
acceptance
plaquette
topological_charge
random_seed
autocorrelation_length

No synthetic configurations.

---

Phase 3 — Wilson / Clover / Domain-Wall Inversions

For every saved configuration:

Solve D ψ = η for u, d

Store residual, iterations, solver tolerance, wall time

---

Phase 4 — Two-point Correlators

Construct C2(t) using the standard proton interpolator

χ(x)=ε_abc (u^T_a C γ5 u_b) u_c

Store every measurement: configuration_id, source_id, sink_id, t, Re, Im

No averaging yet.

---

Phase 5 — EMT Three-point Functions

Insert T_μν. Compute C3(t,τ) for T^μ_μ

This is the trace-anomaly observable required to determine the forward matrix element. Modern lattice workflows obtain the trace-anomaly contribution through a renormalized energy–momentum tensor with continuum matching and extrapolation rather than by inference from the proton mass.

Store τ, operator, matrix element, bootstrap sample

---

Phase 6 — Bootstrap

Bootstrap every observable (10,000 samples)

Output mean, std, covariance matrix

---

Phase 7 — Excited-state Analysis

Fit 1-state, 2-state, 3-state

Compare χ²/dof, AIC, BIC

Automatically select the model using the predetermined rule documented in analysis_windows.json.

---

Phase 8 — Continuum Extrapolation

Fit a², a⁴, mixed using 3+ lattice spacings.

Output continuum limit, systematic uncertainty, χ²

---

Phase 9 — Finite-volume Analysis

Repeat identical physics at L1, L2, L3. Compute ΔFV. Store finite_volume.json

---

Phase 10 — Scale Setting

Choose one observable (w0, t0, r0, Ω mass). Propagate uncertainty through every derived observable. Store scale_setting.json

---

Phase 11 — Renormalization

Determine Z_T. Compute operator mixing. Produce mixing matrix.

---

Phase 12 — Trace Anomaly

Evaluate ⟨p|T^μ_μ|p⟩. Store central, bootstrap, systematics.

---

Phase 13 — Extract c_p

Only now compute

c_p = ⟨p|T^μ_μ|p⟩ / (2 m_p Λ_QCD)

using the normalization adopted by the UGCT certificate.

Do not use the experimental proton mass to construct correlators or back-solve for c_p.

---

Phase 14 — Promotion Verification

Generate raw_correlators_manifest.json containing SHA256, file sizes, configuration count, ensemble IDs.

Then execute verify_proton_cp_anvil.py

Promotion is allowed only if every required file exists, hashes match, metadata are complete, and all verification rules pass.

---

GitNexus Success Criteria

The run is complete only if it produces:

✓ Raw correlators
✓ EMT matrix elements
✓ Bootstrap covariance
✓ Excited-state analysis
✓ Continuum extrapolation
✓ Finite-volume study
✓ Scale setting
✓ Trace anomaly
✓ cp interval
✓ SHA manifests
✓ Verifier PASS

Only after those outputs exist should the certificate change from bounded compatibility to preserved first-principles lattice/HPC certificate. Any attempt to populate those files from the target proton mass or from symbolic derivations rather than the lattice computation should be treated as a verification failure.
