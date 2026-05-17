#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PROOFS = ROOT / 'proofs'
DATA.mkdir(parents=True, exist_ok=True)
PROOFS.mkdir(parents=True, exist_ok=True)


def write_json(relpath, obj):
    p = ROOT / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps({'wrote': str(p), 'status': obj.get('status'), 'tier': obj.get('tier')}, indent=2, sort_keys=True))


def base(cert_id, name, tier, status, fully_certified=False):
    return {
        'schema_version': 'UGCT_CERTIFICATE_V1',
        'certificate_id': cert_id,
        'name': name,
        'tier': tier,
        'status': status,
        'fully_certified': fully_certified,
        'date_recorded': '2026-05-16'
    }
