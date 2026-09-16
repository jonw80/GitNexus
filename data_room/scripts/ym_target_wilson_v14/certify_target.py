"""Exact scalar enclosure for a polynomial Wilson transfer at the actual beta."""
from fractions import Fraction as F
from decimal import Decimal,Context,ROUND_FLOOR,ROUND_CEILING
from pathlib import Path
import math,json,hashlib
H=Path(__file__).resolve().parent
BETA=F(271,20)
UP=Context(prec=70,rounding=ROUND_CEILING)
DOWN=Context(prec=70,rounding=ROUND_FLOOR)
def dec(x,up=True):
    return str((UP if up else DOWN).divide(Decimal(x.numerator),Decimal(x.denominator)))
def exp_iv(x,n=1600):
    assert 0<=x<n+2
    t=s=F(1)
    for k in range(1,n+1):t*=x/k;s+=t
    tail=t*x/(n+1)/(1-x/(n+2))
    return s,s+tail
def tail_bound(z,n,exp_lower):
    assert n+2>z
    return z**(n+1)/math.factorial(n+1)/(1-z/(n+2))/exp_lower
def degree(z,tol):
    lo,hi=exp_iv(z,512)
    n=int(z)
    while tail_bound(z,n,lo)>tol:n+=1
    return n,tail_bound(z,n,lo)
def main():
    target=F(1,10**220);E=P=24
    # Union bound: delta<=2P eps_s+E eps_t, normalized error<=2delta.
    eps=target/(2*(2*P+E))
    m,es=degree(3*BETA/4,eps);n,et=degree(3*BETA/2,eps)
    delta=2*P*es+E*et
    _,exp_upper=exp_iv(3*BETA*E/2)
    gap_floor=2/(exp_upper+1)
    assert 2*delta<=target and 2*delta<gap_floor
    cases=[]
    for L in [2,4,8,16,32,64,128,256,512,1024]:
        e=3*L**3;tol=F(1,10**12)/(6*e)
        mm,ss=degree(3*BETA/4,tol);nn,tt=degree(3*BETA/2,tol)
        dd=4*e*ss+2*e*tt
        assert dd<=F(1,10**12)
        cases.append({'L':L,'links_and_plaquettes':e,'spatial_degree':mm,'temporal_degree':nn,'normalized_operator_error_upper':dec(dd)})
    out={'schema':'YM_TARGET_COUPLING_POLYNOMIAL_V14','status':'PASS_EXACT_SCALAR_BOUNDS',
         'beta':'271/20','target_t':'271/60','spatial_links':E,'spatial_plaquettes':P,
         'spatial_character_argument':'(271/240)*(3+chi_3+chi_3bar)',
         'temporal_character_argument':'(271/120)*(3+chi_3+chi_3bar)',
         'spatial_degree':m,'temporal_degree':n,
         'spatial_relative_tail_upper':dec(es),'temporal_relative_tail_upper':dec(et),
         'kernel_relative_error_upper':dec(delta),'normalized_operator_error_upper':dec(2*delta),
         'full_new_Q_compression_upper':dec(delta),'full_new_crossing_norm_upper':dec(delta),
         'full_new_BstarB_upper':dec(delta*delta),
         'same_basis_A_error_upper':dec(2*delta),'same_basis_M2_error_upper':dec(4*delta),
         'same_basis_BstarB_from_moments_error_upper':dec(8*delta),
         'inherited_finite_volume_log_gap_lower':dec(gap_floor,False),
         'uniform_approximation_examples':cases,
         'full_target_matrix_contractions_executed':False,
         'uniform_physical_gap_proved':False,'continuum_construction_proved':False,
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (H/'TARGET_COUPLING_CERTIFICATE.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
