# Direct normalized Wilson calculation, V12

This runner computes an exact order-248 one-link temporal factor (31,125
SU(3) irreps), proves fixed-volume all-state spectral separation for the
actual Wilson transfer, and checks the coefficient table through an
independent Laurent/Weyl construction. It also certifies a finite-volume
center-neutral plaquette observable and its connected-correlation bound.

Run with Python 3.12 and NumPy 2.1.3:

```
python data_room/scripts/ym_direct_wilson_v12/workspace/wilson_closeout_v12/run_certification.py
```

Every subprocess failure stops the runner. Required output files and the
reviewed exact-table SHA-256 are checked before the execution manifest is
written. The coefficient archive is generated, not downloaded from a
historical crossing job. No private repository evidence is included.

The physical finite-volume logarithmic gap bound is only about
2.83e-212 at beta=271/20 on the fixed 24-link lattice. It does not prove
the 0.015 target, compute the huge spatial Gram/moment matrices, or close
uniform-volume or continuum Yang–Mills obligations. Historical affine
crossing outputs are not reused as physical Wilson spectral data.
