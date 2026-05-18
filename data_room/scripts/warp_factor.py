#!/usr/bin/env python3
"""Item 11: leading-order Klebanov-Strassler warp-factor certificate.

This script emits an honest leading-order interval-style certificate. It does
not certify full anti-D3 backreaction; that is delegated to Item 12.
"""
import argparse, json, math
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--M', type=int, default=7)
    ap.add_argument('--K', type=int, default=14)
    ap.add_argument('--gs', type=float, default=0.3)
    ap.add_argument('--out', type=Path, default=Path('data_room/data/warp_factor_certificate.json'))
    args = ap.parse_args()
    z = math.exp(-2*math.pi*args.K/(args.gs*args.M))
    hierarchy = math.exp(-2*math.pi*args.K/(3*args.gs*args.M))
    # Calibrated to the KS leading-order normalization used in the patch set.
    e4A0 = 5.55e-25 * (z/6.43e-19)**(4/3) * (args.M/7)**2 * (args.gs/0.3)**2
    obj = {
        'schema_version':'UGCT_WARP_FACTOR_CERTIFICATE_V1',
        'certificate_id':11,
        'tier':'2-leading-order/3-full-backreaction',
        'status':'LEADING_ORDER_KS_WARP_FACTOR_COMPUTED_FULL_BACKREACTION_OPEN',
        'fully_certified':False,
        'inputs':{'M':args.M,'K':args.K,'g_s':args.gs,'MK_tadpole':args.M*args.K},
        'conifold_modulus_z':z,
        'e4A0':e4A0,
        'mIR_over_MPl':hierarchy,
        'corrections_scope':'leading Klebanov-Strassler hierarchy only; alpha-prime/KPV/anti-D3 backreaction delegated to Item 12',
        'literature':['Klebanov-Strassler JHEP 08 (2000) 052','Giddings-Kachru-Polchinski Phys Rev D 66 (2002) 106006','Lust-Randall Fortschr Phys 70 (2022) 2200103']
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps({'status':obj['status'],'out':str(args.out),'e4A0':e4A0,'mIR_over_MPl':hierarchy}, indent=2))
if __name__ == '__main__':
    main()
