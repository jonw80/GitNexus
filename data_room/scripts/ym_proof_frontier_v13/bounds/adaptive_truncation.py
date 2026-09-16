#!/usr/bin/env python3
"""Exact-rational all-volume Wilson truncation bounds, not a uniform gap."""
from decimal import Decimal, Context, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
BETA = F(271, 20)
TARGET = F(1, 10**12)
UP = Context(prec=60, rounding=ROUND_CEILING)
DOWN = Context(prec=60, rounding=ROUND_FLOOR)

def display(q, upper=True):
    ctx = UP if upper else DOWN
    return str(ctx.divide(Decimal(q.numerator), Decimal(q.denominator)))

def exp_bounds(x, n=256):
    assert 0 <= x < n+2
    term = total = F(1)
    for k in range(1,n+1):
        term *= x/k
        total += term
    first = term*x/(n+1)
    return total, total + first/(1-x/(n+2))

def epsilon(n, beta_exp, half_exp):
    assert n+2 > BETA
    positive = BETA**(n+1)/math.factorial(n+1)/(1-BETA/(n+2))/beta_exp[0]
    negative = half_exp[1]*(BETA/2)**(n+1)/math.factorial(n+1)
    return max(positive, negative)

def minimum_cubic_side(edges_needed):
    # Integer arithmetic only: E=3 L^3. Sides >=2 keep plaquettes nondegenerate.
    lo,hi=1,2
    while 3*hi**3 < edges_needed:hi *= 2
    while hi-lo>1:
        mid=(lo+hi)//2
        if 3*mid**3 >= edges_needed:hi=mid
        else:lo=mid
    return hi

def main():
    be,he=exp_bounds(BETA),exp_bounds(BETA/2)
    cases=[]
    for L in [2,4,8,16,32,64,128,256,512,1024]:
        E=3*L**3
        n=12
        while n+2 <= BETA or 2*E*epsilon(n,be,he)>TARGET:n+=1
        eps=epsilon(n,be,he)
        assert E*eps <= F(1,2)
        bound=2*E*eps
        assert bound <= TARGET
        cases.append({'spatial_side':L,'links':E,'selected_per_link_degree':n,
                      'one_link_irreps':(n+1)*(n+2)//2,
                      'single_link_relative_error_upper':display(eps),
                      'normalized_full_operator_error_upper':display(bound),
                      'full_external_compression_upper':display(bound),
                      'crossing_norm_upper':display(bound/2),
                      'BstarB_operator_upper':display(bound**2/4),
                      'normalized_second_moment_error_upper':display(2*bound),
                      'full_matrices_assembled':False})
    obstructions=[]
    for n in [72,248]:
        assert n%2==0
        # rho=1-p_n(beta)/exp(beta) >= first omitted positive term / exp(beta).
        rho_lower=BETA**(n+1)/math.factorial(n+1)/be[1]
        edge_threshold=(rho_lower.denominator+rho_lower.numerator-1)//rho_lower.numerator
        L=minimum_cubic_side(edge_threshold)
        E=3*L**3
        assert E*rho_lower>=1
        assert L==2 or 3*(L-1)**3*rho_lower<1
        obstructions.append({'fixed_order':n,
            'positive_endpoint_relative_remainder_lower':display(rho_lower,False),
            'cubic_side_with_E_times_rho_at_least_one':str(L),
            'number_of_links':str(E),
            'optimal_scalar_rescaled_pointwise_relative_error_lower':'1/3',
            'pointwise_scope':'Explicit unaveraged product-group kernel; no claim about the separately gauge-averaged kernel or an operator-norm lower bound.',
            'reason':'Even n gives p_n(-beta/2)>exp(-beta/2), p_n(beta)<exp(beta). The ratio of endpoint product ratios is at least exp(E*rho)>2. Any common scalar leaves worst relative error at least (R-1)/(R+1)>1/3.',
            'does_not_refute_volume_uniform_physical_gap':True})
    result={'schema':'YM_ADAPTIVE_COMPLETE_WILSON_TRUNCATION_V13',
        'status':'PASS_ALL_VOLUME_OPERATOR_APPROXIMATION_WITH_ADAPTIVE_CUTOFF',
        'beta_exact':str(BETA),'uniform_operator_error_target_exact':str(TARGET),
        'theorem':'For every finite cubic spatial volume, choose n(E) with 2 E epsilon_n <= target <=1. For the complete dressed representation box, ||T/lambda0-T_n/mu0||<=target, ||Q T_hat Q||<=target, ||Q T_hat P||<=target/2.',
        'uniformity_scope':'Operator approximation at fixed beta and volume-dependent complete cutoff; not a mass gap, convergence of continuum observables, or uniform matrix dimension.',
        'selection_terminates_for_every_finite_volume':True,
        'selection_termination_reason':'At fixed beta, the factorial Taylor remainder tends to zero as n tends to infinity.',
        'executed_volumes':cases,'fixed_cutoff_obstructions':obstructions,
        'uniform_physical_gap_closed':False,'continuum_obligations_closed':False,
        'full_numerical_physical_moment_matrices_closed':False,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'ADAPTIVE_TRUNCATION_CERTIFICATE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'cutoffs':[[r['spatial_side'],r['selected_per_link_degree']] for r in cases],
                      'fixed_order_obstruction_sides':[r['cubic_side_with_E_times_rho_at_least_one'] for r in obstructions]},indent=2))

if __name__=='__main__':main()
