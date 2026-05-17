#!/usr/bin/env python3
from emit_cert import write_json, base

obj = base(3, 'gvw_attractor', 1, 'READY_FOR_KRAWCZYK_CERTIFICATION', False)
obj.update({
  'tooling': ['python-flint acb_mat', 'Bertini', 'INTLAB optional'],
  'algorithm': 'Interval Krawczyk contraction for D_a W = 0 including axio-dilaton.',
  'output_schema': ['z_star_box','tau_star_box','DW_residual_max','krawczyk_contracted'],
  'reproduction': 'python scripts/attractor_interval_solve.py --flux <id> --pf_basis data/pf_basis.json',
  'references': [
    'Moore hep-th/9807087',
    'Tucker Validated Numerics (2011)',
    'Honma-Otsuka arXiv:1910.10725'
  ],
  'honesty_note': 'Unique-root interval certification requires an actual flux choice and period basis evaluation.'
})
write_json('data/attractor_intervals.json', obj)
