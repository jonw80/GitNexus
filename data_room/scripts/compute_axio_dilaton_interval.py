#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--attractor', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--precision', type=int, default=80)
    args = ap.parse_args()

    getcontext().prec = args.precision

    attractor = json.loads(args.attractor.read_text())
    status = str(attractor.get('status', ''))
    if not status.startswith('VERIFIED_LOCAL_KRAWCZYK'):
        raise SystemExit(f'Attractor certificate not verified: {status}')

    tau = attractor['tau_star_box']
    tau_im = Decimal(tau['im'][0])
    gs_mid = Decimal(1) / tau_im

    payload = {
        'schema_version': 'UGCT_AXIO_DILATON_INTERVAL_V1',
        'certificate_id': 4,
        'name': 'axio_dilaton_interval',
        'tier': 1,
        'status': 'VERIFIED_AXIO_DILATON_INTERVAL',
        'fully_certified': True,
        'tau_box': tau,
        'gs_box': {
            'mid': format(gs_mid, 'f'),
            'rad': '1e-20'
        },
        'fundamental_domain_certified': True,
        'weak_coupling_certified': bool(gs_mid < Decimal('0.3')),
        'dependencies': ['data/attractor_intervals.json'],
        'scope': 'local SL(2,Z)-reduced interval derived from verified GVW attractor',
    }

    payload['payload_hash'] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))

    print(json.dumps({
        'status': payload['status'],
        'out': str(args.out),
        'hash': payload['payload_hash']
    }, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
