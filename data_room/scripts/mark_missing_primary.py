#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CHECKS = {
 'pfaffian_normalization_certificate.json': ['data_room/primary/pfaffian/operator_matrix.json'],
 'uplift_hessian_certificate.json': ['data_room/primary/uplift/hessian_matrix.json'],
 'cosmological_constant_error_budget.json': ['data_room/primary/cosmology/interval_sum.json'],
 'prime_race_density_certificate.json': ['data_room/primary/prime_race/arb_matrices.json'],
 'ym_mass_gap_import_certificate.json': ['data_room/primary/ym/companion_hash.txt'],
 'proton_cp_lattice_certificate.json': ['data_room/primary/proton/ensemble.json'],
 'hadamard_divisor_certificate.json': ['data_room/primary/hadamard/determinant_identity.tex'],
 'y4_tensor_manifest.json': ['ugct_sage_y4/reports/chow_tensor_export.json']
}
records=[]
for cert, reqs in CHECKS.items():
    p = DATA / cert
    if not p.exists():
        continue
    obj = json.loads(p.read_text())
    missing = [r for r in reqs if not (ROOT.parent / r).exists()]
    obj['required_primary_files'] = reqs
    if missing:
        obj['journal_derivation_status'] = 'SOURCE_BACKED_PARTIAL'
        obj['journal_gaps'] = ['missing primary file: ' + m for m in missing]
    records.append({'certificate': cert, 'missing': missing, 'status': obj.get('journal_derivation_status')})
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))
(DATA/'primary_missing_report.json').write_text(json.dumps({'records':records}, indent=2, sort_keys=True))
print(json.dumps({'records':records}, indent=2, sort_keys=True))
