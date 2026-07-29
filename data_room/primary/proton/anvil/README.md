# Anvil — Lattice/HPC Production Path for Item 14

This directory is the **GitNexus production gate** that upgrades the existing bounded c_p certificate to `PRESERVED_LATTICE_HPC_CERTIFICATE`.

## Files present

| File | Role |
|------|------|
| `RUNBOOK.md` | Full 14-phase production objective (gauge ensembles → EMT → continuum/FV/scale → c_p) |
| `verify_proton_cp_anvil.py` | Closed-fail verifier. Emits `PRESERVED_LATTICE_HPC_CERTIFICATE` **only** when every required artifact exists, keys are complete, hashes match, and no forbidden indicators appear |
| `STATUS.json` | Current gate state (artifacts intentionally absent) |

## Required artifacts (still to be produced by real lattice run)

- `anvil_job_metadata.json`
- `raw_correlators_manifest.json`
- `analysis_windows.json`
- `continuum_extrapolation.json`
- `finite_volume.json`
- `scale_setting.json`
- `trace_anomaly.json`

## Honesty contract

- No synthetic configurations.
- No construction of correlators from the experimental proton mass.
- No back-solving for c_p.
- The seven JSON files are **absent by design** until a production GitNexus orchestration on HPC (SIMULATeQCD / Grid / Chroma / MILC) deposits first-principles data.

Run the verifier at any time:

```bash
python data_room/primary/proton/anvil/verify_proton_cp_anvil.py
```

It will correctly report `STATUS: FAIL` until the real lattice artifacts appear.
