#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PROOFS = ROOT / 'proofs'
REPORT = DATA / 'journal_readiness_report.json'

ITEMS = {
    'pfaffian': ('pfaffian_normalization_certificate.json', 'pfaffian_local_reduction_theorem.tex'),
    'uplift': ('uplift_hessian_certificate.json', 'uplift_positive_hessian_theorem.tex'),
    'cosmological_constant': ('cosmological_constant_error_budget.json', 'cosmological_constant_interval_theorem.tex'),
    'prime_race': ('prime_race_density_certificate.json', 'prime_race_density_theorem.tex'),
    'ym_mass_gap_import': ('ym_mass_gap_import_certificate.json', 'ym_mass_gap_import_theorem.tex'),
    'proton_cp': ('proton_cp_lattice_certificate.json', 'proton_cp_lattice_extraction_theorem.tex'),
    'hadamard_divisor': ('hadamard_divisor_certificate.json', 'hadamard_divisor_identification_theorem.tex'),
    'y4_tensor': ('y4_tensor_manifest.json', 'y4_tensor_reproduction_theorem.tex'),
}

JSON_FIELDS = ['source_artifacts', 'constant_derivations', 'theorem_dependencies', 'lemma_proof_map', 'dependency_dag']
TEX_SECTIONS = ['Source artifact table', 'Derivation of constants', 'Imported theorem dependencies', 'Proof of Lemma', 'Rounding and reproducibility']

def read_json(path: Path):
    if not path.exists(): return {}, [f'missing {path}']
    try: obj = json.loads(path.read_text())
    except Exception as exc: return {}, [f'json error: {exc}']
    return obj if isinstance(obj, dict) else {}, []

def artifact_exists(rel: str) -> bool:
    return (ROOT.parent / rel).exists()

def check_item(name: str, cert_name: str, proof_name: str):
    missing = []
    gaps = []
    cert = DATA / cert_name
    proof = PROOFS / proof_name
    obj, errs = read_json(cert)
    missing.extend(errs)
    if obj:
        for field in JSON_FIELDS:
            value = obj.get(field)
            if not isinstance(value, list) or len(value) == 0:
                missing.append(f'json:{field}')
        for i, art in enumerate(obj.get('source_artifacts', []) if isinstance(obj.get('source_artifacts'), list) else []):
            if not isinstance(art, dict):
                missing.append(f'source_artifacts[{i}]:not_object'); continue
            if not art.get('path') or not art.get('sha256') or not art.get('role'):
                missing.append(f'source_artifacts[{i}]:path_sha256_role_required')
            elif not artifact_exists(str(art['path'])):
                missing.append(f'source_artifacts[{i}]:missing_file:{art["path"]}')
        for i, row in enumerate(obj.get('constant_derivations', []) if isinstance(obj.get('constant_derivations'), list) else []):
            for req in ['name','formula','input_artifacts','script','rounding_mode','output_field']:
                if not isinstance(row, dict) or not row.get(req): missing.append(f'constant_derivations[{i}]:{req}')
        for i, row in enumerate(obj.get('theorem_dependencies', []) if isinstance(obj.get('theorem_dependencies'), list) else []):
            for req in ['name','source','hypotheses','hypothesis_check_map','conclusion_used']:
                if not isinstance(row, dict) or not row.get(req): missing.append(f'theorem_dependencies[{i}]:{req}')
        if obj.get('journal_derivation_status') != 'SOURCE_BACKED_COMPLETE':
            gaps.extend(obj.get('journal_gaps', ['journal_derivation_status is not SOURCE_BACKED_COMPLETE']))
    if not proof.exists():
        missing.append(f'missing proof:{proof_name}')
        text = ''
    else:
        text = proof.read_text()
        for section in TEX_SECTIONS:
            if section not in text: missing.append(f'tex:{section}')
    return {'name': name, 'certificate': cert_name, 'proof': proof_name, 'semantic_fields_present': len(missing)==0, 'journal_ready': len(missing)==0 and len(gaps)==0, 'missing_requirements': sorted(set(missing)), 'journal_gaps': gaps}

def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    records = [check_item(name, cert, proof) for name, (cert, proof) in ITEMS.items()]
    ready = all(r['journal_ready'] for r in records)
    report = {'schema_version':'UGCT_JOURNAL_READINESS_REPORT_V2','status':'JOURNAL_READY' if ready else 'JOURNAL_READINESS_GAPS_REMAIN','meaning':'Checks semantic fields, source artifacts, and explicit remaining proof gaps. This does not certify truth; it reports whether source-backed derivations are present.','records':records}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
