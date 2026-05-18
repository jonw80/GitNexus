#!/usr/bin/env python3
"""Item 9: string-loop coefficient interval/systematic certificate.

This is a lightweight runnable emitter for the BHK/BHP loop-coefficient layer.
It records conservative coefficient intervals and the systematic O(g_s^2)
remainder rather than pretending a full compactification-specific amplitude has
already been derived.
"""
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gs', type=float, default=0.3)
    ap.add_argument('--volume', type=float, default=120.0)
    ap.add_argument('--out', type=Path, default=Path('data_room/data/string_loop_coefficients.json'))
    args = ap.parse_args()
    remainder = (args.gs**2) / (args.volume ** (5/3))
    obj = {
        'schema_version':'UGCT_STRING_LOOP_COEFFICIENTS_V1',
        'certificate_id':9,
        'tier':2,
        'status':'SYSTEMATIC_INTERVAL_SPECIFIED_BHP_BHK',
        'fully_certified':False,
        'inputs':{'g_s':args.gs,'volume':args.volume},
        'C_KK_intervals':{'generic_stack':['-0.10','0.10']},
        'C_W_intervals':{'generic_stack':['-0.05','0.05']},
        'R_K_bound':remainder,
        'bhp_systematic':'O(g_s^2 / V^(5/3)) recorded; compactification-specific amplitude still required for full verification',
        'literature':['Berg-Haack-Kors JHEP 11 (2005) 030','Berg-Haack-Pajer JHEP 09 (2007) 031','Gao-Hebecker-Schreyer-Venken JHEP 09 (2022) 091']
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps({'status':obj['status'],'out':str(args.out),'R_K_bound':remainder}, indent=2))
if __name__ == '__main__':
    main()
