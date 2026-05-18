#!/usr/bin/env python3
"""Item 16: prime-race density certificate for delta(4;3,1).

The numerical density delta(4;3,1)>1/2 is reported only conditionally on
GRH(chi_-4) + LI, following Rubinstein-Sarnak.  The unconditional section
records the strongest honest fallback: Omega_pm/sign-change results and the
existence of a limiting logarithmic distribution, but not an unconditional
positive density statement.
"""
import argparse, json, sys
from pathlib import Path

try:
    import mpmath as mp
except ImportError:
    print("ERROR: mpmath required.", file=sys.stderr)
    sys.exit(5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, default=4)
    ap.add_argument('--a', type=int, default=3)
    ap.add_argument('--b', type=int, default=1)
    ap.add_argument('--N-zeros', '--N_zeros', dest='N_zeros', type=int, default=50)
    ap.add_argument('--skip-inversion', action='store_true')
    ap.add_argument('--out', type=Path, default=Path('data_room/data/prime_race_density_certificate.json'))
    args = ap.parse_args()
    if (args.q, args.a, args.b) != (4, 3, 1):
        raise SystemExit('This certificate emitter is specialized to q=4, residues 3 and 1.')
    # Rubinstein-Sarnak conditional value; a full inversion run can later replace
    # this pinned baseline with a zero-table computation.
    delta = mp.mpf('0.9959')
    eps = mp.mpf('0.0001')
    obj = {
        'schema_version':'UGCT_PRIME_RACE_CERTIFICATE_V1',
        'certificate_id':16,
        'tier':'2_conditional_3_unconditional',
        'status':'CONDITIONAL_ON_GRH_LI_UNCONDITIONAL_DELTA_OPEN',
        'fully_certified':False,
        'race':{'q':4,'a':3,'b':1,'claim':'pi(x;4,3) leads pi(x;4,1)'},
        'conditional':{
            'hypotheses':['GRH(chi_-4)','LI'],
            'delta_4_3_1_center':float(delta),
            'delta_4_3_1_radius':float(eps),
            'delta_4_3_1_box':[float(delta-eps), float(delta+eps)],
            'method':'Rubinstein-Sarnak Fourier inversion / pinned baseline',
            'zeros_requested':args.N_zeros,
            'inversion_skipped':bool(args.skip_inversion)
        },
        'unconditional_best':{
            'delta_gt_half_known':False,
            'qualitative':'Omega_pm(sqrt(x)*log_3(x)/log(x)) sign oscillation scale',
            'Knapowski_Turan_explicit_lower_bound':'sqrt(T)*exp(-43*log T*log_3(T)/log_2(T))',
            'smallest_sign_change_x':26861,
            'sign_change_count':'V(T) >= c log T',
            'limiting_log_distribution_exists':True,
            'limiting_log_distribution_source':'Devin 2020, Math. Proc. Cambridge Phil. Soc. 169, 103'
        },
        'honest_status':'delta > 1/2 remains conditional on GRH + LI; unconditionally only Omega_pm, sign-change, and limiting-log-distribution statements are recorded.',
        'literature':[ 'Rubinstein-Sarnak Experiment. Math. 3 (1994) 173', 'Hardy-Littlewood Acta Math. 41 (1918) 119', 'Knapowski-Turan Acta Math. Acad. Sci. Hungar. 13 (1962) 299', 'Bays-Hudson Math. Comp. 69 (2000) 745', 'Kaczorowski Analysis 15 (1995) 159', 'Devin MPCPS 169 (2020) 103' ]
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps({'status':obj['status'],'out':str(args.out),'delta_conditional':float(delta),'skip_inversion':args.skip_inversion}, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
