#!/usr/bin/env python3
"""Check the TeX sidecar of each frontier record, by the record's scope.

Every sidecar must exist, state the record's scope category and status, name the script that computed the record, and
contain no placeholder language. The sidecar of a VERIFIED record must in addition be a referee-grade derivation: the
sections Fixed data and hypotheses, Definitions, Lemmas used, Certificate theorem, Certificate-field map and
Independent falsification conditions; theorem, lemma and proof environments with at least two lemmas; a displayed
equation; at least 3500 bytes; and a statement of what the workflow checks. A CONDITIONAL, OPEN or NEGATIVE record is
a record, not a theorem, and its sidecar is not required to take theorem form (until 2026-11-27 every sidecar was,
and emit_referee_proof_sidecars.py typed theorem text for certificates that had no computation behind them).

Writes data_room/data/referee_sidecar_report.json. Exits 1 if a sidecar fails.
Run from the repository root:  python3 data_room/scripts/verify_referee_sidecars.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontier_records as fr  # noqa: E402

REPORT = "data_room/data/referee_sidecar_report.json"

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
    r'\\\[',
]

FORBIDDEN_SKELETON = [
    'proof omitted',
    'details omitted',
    'to be completed',
    'tbd',
    'placeholder',
    'sketch only',
]


def referee_failures(text: str) -> list[str]:
    """The referee-grade structure required of a VERIFIED record's sidecar."""
    failures = []
    if len(text.encode()) < 3500:
        failures.append(f'sidecar too short for referee-grade derivation: {len(text.encode())} bytes')
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            failures.append(f'missing section: {phrase}')
    for marker in MATH_MARKERS:
        if not re.search(marker, text):
            failures.append(f'missing mathematical marker: {marker}')
    lemma_count = len(re.findall(r'\\begin\{lemma\}', text))
    if lemma_count < 2:
        failures.append(f'expected at least two lemmas, found {lemma_count}')
    if 'The verifier checks' not in text and 'workflow checks' not in text and 'The workflow checks' not in text:
        failures.append('missing explicit verifier/workflow check map')
    return failures


def check(root: Path, item: str) -> dict:
    cert_rel, proof_rel, _ = fr.ITEMS[item]
    out = {'name': item, 'file': proof_rel}
    try:
        rec = json.loads((root / cert_rel).read_text())
    except Exception as exc:
        return {**out, 'ok': False, 'failures': [f'record {cert_rel} unreadable or missing: {exc}']}
    scope, status = rec.get('scope_category'), rec.get('status')
    out.update(scope_category=scope, status=status)
    path = root / proof_rel
    if not path.exists():
        return {**out, 'ok': False, 'failures': ['missing']}
    text = path.read_text()
    plain = text.replace('\\_', '_')
    failures = []
    if f'Scope: \\texttt{{{scope}}}' not in plain:
        failures.append('does not state the scope category')
    if not status or str(status) not in plain:
        failures.append('does not state the status')
    if not rec.get('computed_by') or rec['computed_by'] not in plain:
        failures.append('does not name the script that computed the record')
    bad = [b for b in FORBIDDEN_SKELETON if b in text.lower()]
    if bad:
        failures.append(f'contains non-referee skeleton language: {bad}')
    if scope == 'VERIFIED':
        failures += referee_failures(text)
    return {**out, 'bytes': len(text.encode()), 'referee_grade_required': scope == 'VERIFIED',
            'ok': not failures, 'failures': failures}


def main() -> int:
    root = Path.cwd()
    records = [check(root, item) for item in fr.ITEMS]
    ok = all(r['ok'] for r in records)
    report = {'schema_version': 'UGCT_REFEREE_SIDECAR_REPORT_V2',
              'status': 'REFEREE_SIDECARS_VERIFIED' if ok else 'REFEREE_SIDECARS_NOT_VERIFIED',
              'rule': 'every sidecar states its record; referee-grade structure is required of VERIFIED records only',
              'records': records}
    (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT).write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
