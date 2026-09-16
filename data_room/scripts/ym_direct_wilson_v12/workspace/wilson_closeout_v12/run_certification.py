#!/usr/bin/env python3
"""Fail-closed local/GitHub entry point for the direct Wilson V12 calculation."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def run(relative):
    print('RUN', relative, flush=True)
    subprocess.run([sys.executable, str(ROOT / relative)], cwd=ROOT, check=True)

def required(relative):
    p = ROOT / relative
    if not p.is_file() or p.stat().st_size == 0:
        raise RuntimeError('Missing required output: ' + relative)
    return p

def main():
    if not __debug__:
        raise RuntimeError('Certification requires Python assertions enabled')
    for relative in [
        'wilson_closeout_v12/design/certify_direct_spectral_contraction.py',
        'wilson_closeout_v12/design/build_order248_temporal_factor.py',
        'wilson_closeout_v12/independent/verify_spectral_contraction.py',
        'wilson_closeout_v12/independent/verify_order248_weyl.py',
        'wilson_closeout_v12/physical/certify_neutral_channel.py',
        'wilson_closeout_v12/physical/verify_neutral_constants_exact.py',
    ]:
        run(relative)
    # Output paths/statuses are explicitly checked, not inferred from shell success.
    outputs = [
        'design/DIRECT_WILSON_SPECTRAL_CONTRACTION_CERTIFICATE.json',
        'design/EXACT_ORDER248_TEMPORAL_FACTOR.json.gz',
        'design/ORDER248_TEMPORAL_GENERATION_CHECK.json',
        'independent/INDEPENDENT_SPECTRAL_CONTRACTION_AUDIT.json',
        'independent/ORDER248_WEYL_VERIFICATION.json',
        'physical/FINITE_NEUTRAL_CHANNEL_CERTIFICATE.json',
        'physical/INDEPENDENT_NEUTRAL_CONSTANTS_CHECK.json',
    ]
    files = [required('wilson_closeout_v12/' + s) for s in outputs]
    for p in files:
        if p.suffix == '.json':
            record = json.loads(p.read_text())
            if not record.get('status', '').startswith('PASS'):
                raise RuntimeError('Certificate did not pass: ' + str(p))
    spectral = json.loads(files[0].read_text())
    if spectral['complete_yang_mills_proof'] or spectral['continuum_obligations_closed']:
        raise RuntimeError('Unexpected continuum closure claim')
    if spectral['retained_polynomial_order_with_positive_gap_transfer'] != 248:
        raise RuntimeError('Unexpected cutoff')
    digest = hashlib.sha256(files[1].read_bytes()).hexdigest()
    if digest != 'ef54ec6abaddf4fd72926dbd28f7c607cfd821cd1f963d52cd0fc90f874e2cbe':
        raise RuntimeError('Exact coefficient table differs from reviewed local calculation')
    manifest = {
        'schema': 'YM_DIRECT_WILSON_V12_EXECUTED_RUN',
        'status': 'PASS_FINITE_VOLUME_CALCULATION_AND_INDEPENDENT_CHECKS',
        'git_commit': os.environ.get('GITHUB_SHA'),
        'github_run_id': os.environ.get('GITHUB_RUN_ID'),
        'complete_yang_mills_proof': False,
        'continuum_obligations_closed': False,
        'source_sha256': {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*.py')) if '__pycache__' not in p.parts
        },
        'outputs': [
            {'path': str(p.relative_to(ROOT)), 'size_bytes': p.stat().st_size,
             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files
        ],
    }
    destination = HERE / 'EXECUTION_MANIFEST.json'
    destination.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'outputs': len(files),
                      'table_sha256': digest}, indent=2), flush=True)

if __name__ == '__main__':
    main()
