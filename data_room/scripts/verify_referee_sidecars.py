#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PROOFS = ROOT / 'proofs'
DATA = ROOT / 'data'
REPORT = DATA / 'referee_sidecar_report.json'

REQUIRED = [
  'pfaffian_local_reduction_theorem.tex',
  'uplift_positive_hessian_theorem.tex',
  'cosmological_constant_interval_theorem.tex',
  'prime_race_density_theorem.tex',
  'ym_mass_gap_import_theorem.tex',
  'proton_cp_lattice_extraction_theorem.tex',
  'hadamard_divisor_identification_theorem.tex',
  'y4_tensor_reproduction_theorem.tex',
]

REQUIRED_PHRASES = [
  'Fixed data and hypotheses',
  'Definitions',
  'Lemmas used',
  'Certificate theorem',
  'Certificate-field map',
  'Independent falsification conditions',
]

MATH_MARKERS = [
  r'\\begin\{theorem\}',
  r'\\begin\{lemma\}',
  r'\\begin\{proof\}',
  r'\\[',
]

FORBIDDEN_SKELETON = [
  'proof omitted',
  'details omitted',
  'to be completed',
  'tbd',
  'placeholder',
  'sketch only',
]

def check(path: Path):
    failures=[]
    if not path.exists():
        return {'file':str(path.relative_to(REPO)),'ok':False,'failures':['missing']}
    text=path.read_text()
    if len(text) < 3500:
        failures.append(f'sidecar too short for referee-grade derivation: {len(text)} bytes')
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            failures.append(f'missing section: {phrase}')
    for marker in MATH_MARKERS:
        if not re.search(marker, text):
            failures.append(f'missing mathematical marker: {marker}')
    lemma_count=len(re.findall(r'\\begin\{lemma\}', text))
    if lemma_count < 2:
        failures.append(f'expected at least two lemmas, found {lemma_count}')
    if 'The verifier checks' not in text and 'workflow checks' not in text and 'The workflow checks' not in text:
        failures.append('missing explicit verifier/workflow check map')
    low=text.lower()
    bad=[b for b in FORBIDDEN_SKELETON if b in low]
    if bad:
        failures.append(f'contains non-referee skeleton language: {bad}')
    return {'file':str(path.relative_to(REPO)),'bytes':len(text),'lemma_count':lemma_count,'ok':not failures,'failures':failures}

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    records=[check(PROOFS / name) for name in REQUIRED]
    ok=all(r['ok'] for r in records)
    report={'schema_version':'UGCT_REFEREE_SIDECAR_REPORT_V1','status':'REFEREE_SIDECARS_VERIFIED' if ok else 'REFEREE_SIDECARS_NOT_VERIFIED','records':records}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
