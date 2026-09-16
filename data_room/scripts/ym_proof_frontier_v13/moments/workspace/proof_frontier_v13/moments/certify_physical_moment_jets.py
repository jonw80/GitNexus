#!/usr/bin/env python3
"""Outward numerical same-Wilson moment jets and complete-space size bounds."""
from fractions import Fraction as F
import hashlib,json,sys
from pathlib import Path
from exact_spatial_jets import HERE,ROOT
sys.path.insert(0,str(ROOT/'dag_closeout_v5'))
sys.path.insert(0,str(ROOT/'wilson_transfer_v11/direct_review'))
from intervals import I
from certify_gauge_fixed_perron import exp_interval

def add(a,b):return [[a[i][j]+b[i][j] for j in range(2)] for i in range(2)]
def scale(a,s):return [[s*x for x in row] for row in a]
def mul(a,b):return [[sum((a[i][k]*b[k][j] for k in range(2)),I(0)) for j in range(2)] for i in range(2)]
def rec(a):return [[x.record() for x in row] for row in a]
def diag(a,b):return [[I(a),I(0)],[I(0),I(b)]]

def main():
    path=HERE/'MOMENT_WILSON_COEFFICIENT_INPUT.json'
    coef=json.loads(path.read_text());lookup={tuple(r['rep']):I(r['coefficient']['lower'],r['coefficient']['upper']) for r in coef['representations']}
    uniform_path=HERE/'TEMPORAL_VACUUM_SEPARATION_CERTIFICATE.json'
    uniform=json.loads(uniform_path.read_text())
    assert uniform['all_irreducibles_covered'] and uniform['beta_exact']=='271/20'
    c=[lookup[(1,0)],lookup[(2,0)],lookup[(1,1)]];k=c[0]**4
    spec=json.loads((HERE/'EXACT_TEMPORAL_SPECTRAL_MOMENTS.json').read_text())
    def q(order):
        total=I(0)
        for row in spec['polynomial']:
            term=I(F(row['coefficient']))
            for x,n in zip(c,row['exponents']):term*=x**(n*order)
            total+=term
        return total
    q1,q2=q(1),q(2);mu4=I(F(3890,9));s12=I(12).sqrt();s3=I(3).sqrt()
    ID=diag(1,1);C=diag(1,k);C2=mul(C,C)
    d=[[I(0),s12],[s12,I(F(1,2))]]
    d2=[[I(12),s3],[s3,mu4/12]]
    r1=[[12*k,s3*k],[s3*k,q1/12]]
    r2=[[12*k*k,s3*k*k],[s3*k*k,q2/12]]
    g=[ID,d,scale(d2,I(F(1,2)))]
    h=[C,add(mul(d,C),mul(C,d)),add(scale(add(mul(d2,C),mul(C,d2)),I(F(1,2))),r1)]
    j1=add(add(mul(d,C2),mul(C2,d)),mul(mul(C,d),C))
    j2=add(scale(add(add(mul(d2,C2),mul(C2,d2)),mul(mul(C,d2),C)),I(F(1,2))),add(add(mul(r1,C),mul(C,r1)),r2))
    jj=[C2,j1,j2]
    rr1=scale(d,I(F(-1,2)));rr2=add(scale(mul(d,d),I(F(3,8))),scale(g[2],I(F(-1,2))))
    def orthogonalize(seq):
        a0=seq[0]
        a1=add(seq[1],add(mul(rr1,a0),mul(a0,rr1)))
        a2=seq[2]
        for term in [mul(rr1,seq[1]),mul(seq[1],rr1),mul(rr2,a0),mul(a0,rr2),mul(mul(rr1,a0),rr1)]:a2=add(a2,term)
        return [a0,a1,a2]
    a=orthogonalize(h);m=orthogonalize(jj)
    lam2=6*(1+k)/(1-k)
    ah=[a[0],a[1],add(a[2],scale(a[0],-lam2))]
    mh=[m[0],m[1],add(m[2],scale(m[0],-2*lam2))]
    cross2=(q2-144-3*k*k)/12
    assert cross2.lo>0
    check=add(m[2],scale(add(add(mul(a[0],a[2]),mul(a[2],a[0])),mul(a[1],a[1])),I(-1)))
    for i in range(2):
        for z in range(2):
            expected=cross2 if i==z==1 else I(0)
            assert max(check[i][z].lo,expected.lo)<=min(check[i][z].hi,expected.hi)
    r=I(F(1,1000));delta=exp_interval(72*r)-1
    assert delta.hi<((1-c[0])/2).lo
    moment_caps={
       'normalized_A':exp_interval(144*r)/(1-delta)**2,
       'normalized_M2':exp_interval(216*r)/(1-delta)**3,
    }
    # A real example in the proven analytic disk. The same t is used for all
    # matrices and the Perron normalization, but differs from target beta/3.
    small=I(F(1,10**12));ratio=small/r
    actual={}
    for name,seq in [('normalized_A',ah),('normalized_M2',mh)]:
        trunc=add(add(seq[0],scale(seq[1],small)),scale(seq[2],small*small))
        err=moment_caps[name]*ratio**3/(1-ratio)
        actual[name]={'matrix':rec([[x+I(err.hi.copy_negate(),err.hi) for x in row] for row in trunc]),'operator_norm_Taylor_remainder_upper':str(err.hi)}
    bc=moment_caps['normalized_M2']+moment_caps['normalized_A']**2
    berr=bc*ratio**3/(1-ratio)
    bsmall=diag(0,cross2*small*small)
    actual['normalized_BstarB']={'matrix':rec([[x+I(berr.hi.copy_negate(),berr.hi) for x in row] for row in bsmall]),'operator_norm_Taylor_remainder_upper':str(berr.hi),'additionally_positive_semidefinite':True}
    assert (cross2*small*small).lo>berr.hi
    x=I(F(271,60));target_remainders={}
    for name,w in [('G',1),('H',2),('J',3)]:
        y=72*w*x;bound=exp_interval(y)*y**3/6
        target_remainders[name]=str(bound.hi)
    size=[]
    for n in (72,248):
        labels=(n+1)*(n+2)//2;rank=labels**6;kzero=(rank+7)//8
        size.append({'cutoff':n,'one_loop_characters':labels,'neutral_dimension_lower_bound':str(rank),'neutral_zero_momentum_dimension_lower_bound':str(kzero),'one_real_float64_dense_matrix_bytes_lower_bound':str(8*rank*rank),'one_real_float64_upper_triangle_bytes_lower_bound':str(4*rank*(rank+1)),'neutral_zero_momentum_one_real_float64_dense_matrix_bytes_lower_bound':str(8*kzero*kzero)})
    cert={'schema':'YM_SAME_WILSON_PHYSICAL_MOMENT_JETS_V13',
          'status':'PASS_EXACT_SPATIAL_JETS_AND_OUTWARD_NUMERICAL_EVALUATION',
          'family':'T(t)=exp(tD/2) C_beta exp(tD/2), beta_temporal=271/20, target t=271/60',
          'retained_basis':'e=(1,D/sqrt12); F(t)=exp(tD/2)e; G=F*F; U=F G^(-1/2)',
          'moment_definitions':{'G':'e* exp(tD) e','H':'e* exp(tD) C exp(tD) e','J':'e* exp(tD) C exp(tD) C exp(tD) e','A':'G^(-1/2) H G^(-1/2)','M2':'G^(-1/2) J G^(-1/2)','BstarB':'M2-A^2, full complement Q=I-UU*'},
          'Taylor_convention':'coefficient arrays for t^0,t^1,t^2; not derivatives (which include factorials)',
          'kappa':k.record(),'q1_full_temporal_spatial_moment':q1.record(),'q2_full_temporal_spatial_moment':q2.record(),
          'G_coefficients':list(map(rec,g)),'H_coefficients':list(map(rec,h)),'J_coefficients':list(map(rec,jj)),
          'orthonormal_basis_Gram':rec(ID),'physical_A_coefficients':list(map(rec,a)),'physical_M2_coefficients':list(map(rec,m)),
          'Perron_lambda_t2_coefficient':lam2.record(),
          'Perron_normalized_A_coefficients':list(map(rec,ah)),
          'Perron_normalized_M2_coefficients':list(map(rec,mh)),
          'full_Q_BstarB_t2_coefficient':rec(diag(0,cross2)),
          'common_analytic_radius':str(r.lo),'circle_operator_perturbation_upper':str(delta.hi),
          'small_spatial_coupling_example':{'t':'1/1000000000000','beta_spatial':'3/1000000000000','beta_temporal':'271/20','orthonormal_basis_Gram':rec(ID),**actual,'scope':'Actual normalized Wilson moment enclosures at the stated anisotropic spatial coupling; not the target isotropic beta.'},
          'target_t_second_order_remainder_bounds':target_remainders,
          'target_t_second_order_remainder_is_useful':False,
          'complete_retained_dimension_and_storage_bounds':size,
          'target_beta_full_physical_matrices_materialized':False,
          'volume_uniform_or_continuum_claim':False,
          'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),path,HERE/'EXACT_TEMPORAL_SPECTRAL_MOMENTS.json',uniform_path,ROOT/'dag_closeout_v5/intervals.py',ROOT/'wilson_transfer_v11/direct_review/certify_gauge_fixed_perron.py']}}
    (HERE/'PHYSICAL_MOMENT_JETS_CERTIFICATE.json').write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps({k:cert[k] for k in ['status','kappa','q1_full_temporal_spatial_moment','q2_full_temporal_spatial_moment','Perron_lambda_t2_coefficient','full_Q_BstarB_t2_coefficient','complete_retained_dimension_and_storage_bounds']},indent=2))
if __name__=='__main__':main()
