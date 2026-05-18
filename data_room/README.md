# UGCT Certificate Layer Closure Specification

Date of record: 2026-05-16

This data room records the remaining downstream certificate layer for *Principia Mathematica Physica* after the native Sage closure of the Ewx/Y4 Chow-ring tensor sector.

Resolved geometry already closed in CI:

- resolved split A4/SU(5) Tate Calabi-Yau fourfold Y4 over B3 = P(O + K_dP8);
- chi(Y4)=1056 and tadpole chi(Y4)/24=44 as the working payload target;
- 235 exact higher-Cartan Ewx values exported by the native Sage blowup-pushforward engine;
- 1509 exceptional-sector reduction rules verified;
- full chamber-specific degree-four Y4 tensor verified.

This directory is not another Chow-ring patch.  It is the downstream stabilization, arithmetic, lattice-QCD, and proof-certificate layer.

## Tier policy

- Tier 1: operationally closable with documented symbolic/interval tooling in ordinary CI or a modest local run.
- Tier 2: operationally specified but requiring nontrivial compute, external snapshots, or HPC-scale enumeration.
- Tier 3: research-frontier or contested.  The honest deliverable is a schema, literature map, and open-problem statement, not a false certificate.

## Certificate inventory

1. Flux scan — Tier 2
2. Picard-Fuchs basis intervals — Tier 1
3. GVW attractor interval solve — Tier 1
4. Axio-dilaton interval — Tier 1
5. Instanton divisors / zero modes — Tier 1-2
6. Hidden-sector ranks and tadpole — Tier 1
7. Pfaffian prefactors — Tier 3 frontier
8. Racetrack superpotential — Tier 2, inherits Item 7 width
9. String-loop coefficients — Tier 2
10. Kahler stabilization — Tier 1, inherits Item 7 width
11. Warp factor — Tier 2 leading order / Tier 3 full backreaction
12. Uplift/backreaction stability — Tier 3 contested
13. Cosmological constant error budget — Tier 2, inherits Item 12
14. Lattice-QCD c_p trace-anomaly certificate — Tier 2
15. Global arithmetic identity F_infty=c Xi — Tier 1 proof-layer item
16. Prime-race density delta(4;3,1)>1/2 — conditional Tier 2 / unconditional Tier 3

## Honesty rule

No file in this data room may claim `VERIFIED_*` unless it contains a concrete computation, interval certificate, proof artifact, or named external dataset snapshot sufficient to reproduce the assertion.  Tier 3 files must explicitly set `fully_certified:false` and state the frontier obstruction.

## CI

The workflow `.github/workflows/certs.yml` runs the unified Principia certificate layer.  The current Tier-1 dependency chain computes concrete local certificates for `pf_basis.json`, `attractor_intervals.json`, and `axio_dilaton_interval.json`, then validates the full payload bundle.  Tier-2 and Tier-3 records remain explicitly labeled by evidentiary status rather than being promoted by name alone.

Last trigger note: 2026-05-18 unified certificate compute rerun.
