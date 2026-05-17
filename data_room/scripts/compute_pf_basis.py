#!/usr/bin/env python3
from emit_cert import write_json, base

obj = base(2, 'pf_basis', 1, 'READY_FOR_INTERVAL_COMPUTATION', False)
obj.update({
  'tooling': ['CYTools v1.4.9', 'python-flint/Arb', 'SageMath'],
  'algorithm': 'Frobenius expansion around the LCS point with GV-invariant truncation bounds.',
  'output_schema': ['basis_ordering','evaluation_point','Pi','monodromy','tail_bound'],
  'reproduction': 'python scripts/compute_pf_basis.py --precision 200 --max_gv_deg 30',
  'literature': [
    'Hosono-Klemm-Theisen-Yau CMP 167 (1995) 301',
    'Demirtas-Rios-Tascon-McAllister arXiv:2211.03823'
  ],
  'honesty_note': 'This CI emitter records the operational specification. Numerical intervals require CYTools-backed geometry data.'
})
write_json('data/pf_basis.json', obj)
