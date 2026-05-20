# Journal Referee Completeness Standard for UGCT Closeouts

This document records the journal-level standard for promoting UGCT/GZYM closeout artifacts from verifier-passing certificate notes to referee-auditable derivations.

The current GitNexus sidecar verifier checks morphology: fixed data, definitions, theorem environments, proof blocks, and falsification sections. That is necessary, but it is not enough. A journal referee will not accept a Boolean field such as `spectral_identification_verified: true` or `backreaction_terms_included: true` unless the proof file derives that field from source data, imported theorems with verified hypotheses, or reproducible interval arithmetic.

## 1. Acyclic proof architecture

Every sidecar must expose a directed acyclic dependency graph.

### UGCT DAG

1. Geometry and topology: Fermat quintic, dP8 surface, twist class, Y4 Chow/intersection tensor.
2. Periods and fluxes: Griffiths periods, GVW attractor, flux vectors, Kähler normalizations.
3. Yukawa and mixing sectors: residue pairings, CKM/PMNS, CP phase, charged fermion masses.
4. Cosmological observables: Kähler stabilization, uplift/backreaction, reheating, baryogenesis, dark matter.
5. Quantum gravity: period fluctuations, tadpole-regulated state spaces, graviton/spacetime emergence.

No downstream observable may be fed backward to choose an upstream geometric object.

### GZYM DAG

1. Operator-theoretic closure: finite-volume Faddeev-Popov operator and positivity domain.
2. Gribov region and localized Zwanziger fields.
3. Infrared bounds: reflection positivity, Schur complements, Grassmann integration.
4. RG stability: finite-range covariance decomposition and BKAR/KP estimates.
5. Mass gap: OS reconstruction and positive spectral gap.

No spectral-gap hypothesis may be used to prove an earlier infrared or RG estimate.

## 2. Lemma closure requirement

Every lemma in a sidecar must terminate in one of two ways:

- a complete proof paragraph with the actual operator estimates, algebraic reductions, or interval computation; or
- an imported theorem citation with a local hypothesis-check map showing that the objects in the sidecar satisfy the theorem's assumptions.

A sidecar is not journal-complete if a lemma is supported only by a JSON Boolean flag.

## 3. Numerical constant reproducibility

Every numerical constant or interval must provide:

- source artifacts with SHA-256 hashes;
- exact formula;
- script path;
- precision and rounding mode;
- output field in the certificate;
- independent check or residual bound.

Interval claims must be generated with outward-rounded arithmetic. The proof text and the JSON payload must match.

## 4. Imported theorem mapping

A citation is not enough. Each imported theorem must list:

- theorem name and source;
- hypotheses of the theorem;
- local objects being substituted into those hypotheses;
- verification method for each hypothesis;
- conclusion used downstream.

Examples: Kotecky-Preiss activity bounds, Davis-Kahan spectral projection stability, Hurwitz normal convergence, OS reconstruction, Quillen/Bismut-Zhang determinant-line formulas, Krawczyk/interval-Newton inclusion.

## 5. Hard closeout requirements

### Pfaffian normalization

Required: exact operator, domain, boundary conditions, zero-mode computation, determinant-line convention, finite determinant/Berezin computation, zeta or heat-kernel tail bound, collar/gauge-independence proof, and interval output.

### Anti-D3/uplift backreaction

Required: exact effective potential, compact moduli window, interval gradient residual, exact interval Hessian matrix, eigenvalue lower bound, boundary exclusion, and proof that higher-order alpha-prime and backreaction terms are included or explicitly bounded.

### Cosmological constant

Required: full topological formula, all upstream dependencies, error budget, loop coefficients, nonperturbative data, and proof of no hidden tuning parameter.

### Prime-race density

Required: hypercharge residue map selecting the modulus-four race, Hodge-Riemann positivity, orthogonality to ordinary Tate main term, determinant/explicit-formula transfer, certified Arb matrices, parity-gap transfer, and density interval above one half.

### YM/proton

Required: GZYM reflection positivity, OS reconstruction, RG convergence, imported companion theorem hash, and a real lattice snapshot compatibility certificate for the proton trace-anomaly coefficient.

### Hadamard/RH bridge

Required: proof of `F_infty(z) = c Xi(z)`, Persistence-Weil decomposition, H2 graph-norm tail, parity dominance, Davis-Kahan transfer, Hurwitz transfer, and zero-free auxiliary factor.

### Y4 tensor

Required: full Ewx chamber data, Stanley-Reisner ideal, linear equivalences, proper-transform class, pushforward rules, 1509-rule exceptional reduction table, tensor export, and hashes.

## 6. Journal readiness gate

The repository must distinguish three statuses:

- `STRUCTURAL_CERTIFICATE_VERIFIED`: files exist and pass morphology checks.
- `REFEREE_SIDECARS_VERIFIED`: sidecars have theorem/proof structure and falsification sections.
- `JOURNAL_DERIVATIONS_COMPLETE`: all lemmas are proved or imported with verified hypotheses, all constants are reproduced from source artifacts, and all intervals match executable computations.

Only the final status is suitable for a journal referee claim that the derivations are complete.
