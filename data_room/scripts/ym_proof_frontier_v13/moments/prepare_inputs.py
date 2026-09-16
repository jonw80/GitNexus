#!/usr/bin/env python3
"""Generate the minimal certified inputs with the independent Bessel engine."""
import base64,hashlib,json,sys
from fractions import Fraction as F
from pathlib import Path

BASE=Path(__file__).resolve().parent;WORK=BASE/'workspace';OUT=WORK/'proof_frontier_v13/moments'
sys.path.insert(0,str(WORK/'dag_closeout_v5'))
sys.path.insert(0,str(WORK/'wilson_transfer_v11/direct_review'))
from certify_wilson import wilson_table
from certify_gauge_fixed_perron import exp_interval
from intervals import I

def main():
    geo=json.loads((BASE/'GEOMETRY_INPUT.json').read_text())
    raw=base64.b64decode(geo['geometry_base64'],validate=True)
    assert hashlib.sha256(raw).hexdigest()==geo['geometry_sha256']
    dest=WORK/geo['geometry_filename'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    reps=[(p,q) for p in range(10) for q in range(p+1) if p+q<10]
    assert len(reps)==30 and len({16*p+q for p,q in reps})==30
    table,z=wilson_table(F(271,20),reps);rho=table[16]['coefficient']
    checks=[]
    for p,q in reps:
        if p+q>1:
            assert table[16*p+q]['coefficient'].hi<rho.lo
            checks.append({'rep':[p,q],'coefficient':table[16*p+q]['coefficient'].record()})
    # Positive character expansion at the identity: d_r*A_r<=exp(beta).
    # Every p+q>=10 has d_r>=66, so c_r<=exp(beta)/(66^2*A_00).
    tail=exp_interval(I(F(271,20)))/(66**2*z)
    assert tail.hi<rho.lo
    needed=[(0,0),(1,0),(2,0),(1,1)]
    coeff={'schema':'YM_MINIMAL_BESSEL_WILSON_COEFFICIENTS_V13','status':'PASS_REGENERATED_OUTWARD_BESSEL_DETERMINANTS','beta_exact':'271/20','representation_count':4,'Z_beta':z.record(),'representations':[{'rep':[p,q],'coefficient':table[16*p+q]['coefficient'].record()} for p,q in needed]}
    (OUT/'MOMENT_WILSON_COEFFICIENT_INPUT.json').write_text(json.dumps(coeff,indent=2)+'\n')
    bound={'schema':'YM_TEMPORAL_VACUUM_SEPARATION_V13','status':'PASS_ALL_IRREP_GLOBAL_BOUND','beta_exact':'271/20','all_irreducibles_covered':True,'global_bound':'c_(p,q)<=rho=c_(1,0)<1 for all nontrivial irreps','rho':rho.record(),'finite_conjugacy_representatives':30,'finite_nontrivial_nonfundamental_checks':checks,'tail_first_degree':10,'tail_minimum_dimension':66,'tail_upper':tail.record(),'tail_proof':'Positive character coefficients imply d_r*A_r<=exp(beta), hence c_r<=exp(beta)/(d_r^2*Z_beta); conjugation covers q>p.','degree_power_bound_claim':False}
    (OUT/'TEMPORAL_VACUUM_SEPARATION_CERTIFICATE.json').write_text(json.dumps(bound,indent=2)+'\n')
    print(json.dumps({'status':bound['status'],'finite_reps':30,'tail_upper':str(tail.hi)}))
if __name__=='__main__':main()
