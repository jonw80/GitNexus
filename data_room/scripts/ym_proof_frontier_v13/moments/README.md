# V13 minimal actual-Wilson moment runner

Run with Python 3.12 and NumPy:

```
python run_moments.py
```

The runner regenerates the required Wilson coefficients from the interval
Bessel determinant engine. It independently re-establishes the global
temporal spectral bound with 30 finite conjugacy representatives and an
infinite positive-character dimension tail. It does not include or read the
1.4 MB V11 coefficient table, V9 matrices, private repository data, or any
historical affine spectral result.

It verifies pinned geometry bytes, performs exact Haar and link-projector
contractions, generates all 2-by-2 physical normalized moment Taylor
coefficients through second order in one dressed basis, and rigorously
encloses A, M2 and the full-Q B*B at the explicitly anisotropic construction
test beta_spatial=3e-12, beta_temporal=271/20. This test is not a result for the
target isotropic beta=271/20. Full target matrices, volume-uniform estimates,
and continuum claims stay false in the fail-closed scope checks.

The exact geometry and moment code is copied without mathematical changes.
The physical interval script changes exactly two coefficient-input paths;
`STAGED_SOURCE_PROVENANCE.json` lists original and staged hashes. Regenerated
Bessel coefficient intervals are slightly wider than the V11 independent
positive-series intervals. Their outputs are a separate calculation cohort,
not purported byte-identical V11/V13 positive-series results.

Required output statuses are checked, including presence of every expected
JSON. A failed subprocess, missing output, malformed JSON, hash mismatch,
failed assertion, or scope mismatch fails the runner. The successful summary
is `MOMENT_EXECUTION_CERTIFICATE.json`; scientific outputs are under
`workspace/proof_frontier_v13/moments/`.

The supplied proof text describes both the local original coefficient cohort
and this public cohort. The analytic argument needs only the regenerated
global maximum c_r<=c_fundamental for nontrivial irreps, not the stronger
degree-power bound from the original V10 certificate. The optional historical
matrix diagnostic command in the proof text is intentionally absent here.
