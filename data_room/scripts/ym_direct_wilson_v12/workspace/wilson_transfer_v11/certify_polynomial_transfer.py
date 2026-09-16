#!/usr/bin/env python3
"""Exact finite temporal Wilson polynomial and normalized full-space errors.

The finite coefficient file is executed.  The enormous spatial Gram matrix
is defined by exact group integrals but is NOT asserted numerically executed.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal
from collections import defaultdict
import hashlib
import json
import math
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'dag_closeout_v5'))
from intervals import I
sys.path.insert(0,str(HERE/'direct_review'))
from certify_gauge_fixed_perron import exp_interval

BETA=F(271,20)
LINKS=24
ORDER=72


def dim(p,q):
    return (p+1)*(q+1)*(p+q+2)//2


def fusion(p,q):
    return [(r,s) for r,s in ((p+1,q),(p-1,q+1),(p,q-1),
                              (p,q+1),(p+1,q-1),(p-1,q)) if min(r,s)>=0]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remainder(order):
    assert order+2>BETA
    first=I(BETA)**(order+1)/math.factorial(order+1)
    tail=first/(1-I(BETA)/(order+2))
    ebeta=exp_interval(I(BETA))
    ehalf=exp_interval(I(BETA/2))
    positive=tail/ebeta
    negative=ehalf*(I(BETA/2)**(order+1))/math.factorial(order+1)
    eps=max(positive.hi,negative.hi)
    assert eps<1
    # Positive binomial sum avoids subtracting almost equal decimal endpoints.
    eta=sum((math.comb(LINKS,j)*I(eps)**j for j in range(1,LINKS+1)),I(0))
    return {'order':order,'uniform_single_link_relative_error_upper':str(eps),
            'positive_argument_relative_remainder_upper':str(positive.hi),
            'negative_argument_relative_remainder_upper':str(negative.hi),
            'unnormalized_positive_tail_upper':str(tail.hi),
            'normalized_full_transfer_error_upper':str(eta.hi),
            'full_external_normalized_compression_upper':str(eta.hi),
            'normalized_crossing_norm_upper':str((eta/2).hi),
            'normalized_BstarB_operator_upper':str((eta*eta/4).hi),
            'normalized_second_moment_difference_upper':str((2*eta).hi),
            'exact_unit_vacuum_external_component_norm_upper':str((eta/(2*(1-eta))).hi) if eta.hi<1 else None,
            'Perron_ratio_lambda_n_over_lambda_0_lower':str(max(Decimal(0),(1-eta).lo)),
            'Perron_ratio_lambda_0_over_lambda_n_upper':str((1/(1-eta)).hi) if eta.hi<1 else None}


def exact_coefficients():
    denominator=120**ORDER*math.factorial(ORDER)
    sums=defaultdict(int)
    mult={(0,0):1}
    checks=[]
    factorial=math.factorial(ORDER)
    for n in range(ORDER+1):
        assert sum(dim(*r)*value for r,value in mult.items())==6**n
        weight=271**n*120**(ORDER-n)*(factorial//math.factorial(n))
        for r,value in mult.items():
            sums[r]+=value*weight
        checks.append(len(mult))
        if n<ORDER:
            nxt=defaultdict(int)
            for r,value in mult.items():
                for target in fusion(*r):
                    nxt[target]+=value
            mult=nxt
    expected={(p,q) for p in range(ORDER+1) for q in range(ORDER+1-p)}
    assert set(sums)==expected
    assert all(sums[r]>0 and sums[r]==sums[r[::-1]] for r in expected)
    identity_value=sum(F(BETA)**n/math.factorial(n) for n in range(ORDER+1))
    assert F(sum(dim(*r)*value for r,value in sums.items()),denominator)==identity_value
    records=[{'rep':list(r),'dimension':dim(*r),'character_numerator':str(sums[r]),
              'normalized_convolution_eigenvalue_numerator':str(sums[r]),
              'normalized_convolution_eigenvalue_denominator':str(dim(*r)*sums[(0,0)])}
             for r in sorted(sums,key=lambda r:(sum(r),r))]
    output={'schema':'YM_EXACT_TEMPORAL_WILSON_POLYNOMIAL_V11',
            'beta_exact':str(BETA),'order':ORDER,
            'character_polynomial':'p_n((beta/6)(chi_3+chi_3bar))',
            'common_character_coefficient_denominator':str(denominator),
            'one_link_polynomial_partition_numerator':str(sums[(0,0)]),
            'one_link_polynomial_partition_denominator':str(denominator),
            'normalization_for_stored_eigenvalues':'Divide by exact polynomial partition Z_n; this common scalar cancels upon Perron normalization of the spatially dressed tensor product.',
            'loewner_suboperator_convention':'For 0<=C_n<=C use denominator Z_beta, NOT Z_n. Normalized full transfer T_n/||T_n|| is identical under either common scalar convention.',
            'representation_count':len(records),
            'every_irrep_with_p_plus_q_at_most_order_present':True,
            'all_character_coefficients_strictly_positive':True,
            'all_conjugation_identities_exact':True,
            'all_tensor_dimension_identities_exact':len(checks),
            'polynomial_identity_value_at_identity_exact':str(identity_value),
            'representations':records,'script_sha256':sha(__file__)}
    path=HERE/'EXACT_WILSON_POLYNOMIAL_COEFFICIENTS.json'
    path.write_text(json.dumps(output,indent=2)+'\n')
    return output,path


def main():
    coeff,path=exact_coefficients()
    records=[remainder(n) for n in [24,32,40,48,56,64,72,80]]
    chosen=next(x for x in records if x['order']==ORDER)
    eta=I(chosen['normalized_full_transfer_error_upper'])
    assert eta.hi < Decimal('1e-24')
    # Six edge-disjoint plaquettes give independent local characters of all
    # degrees <=ORDER. This is a lower bound, not a complete dimension count.
    per_loop=(ORDER+1)*(ORDER+2)//2
    dimension_lower=per_loop**6
    result={'schema':'YM_DIRECT_NORMALIZED_WILSON_CONSTRUCTION_V11',
            'status':'PASS_EXACT_COEFFICIENTS_AND_FULL_SPACE_OPERATOR_BOUNDS',
            'exact_beta':str(BETA),'spatial_links':24,'spatial_plaquettes':24,
            'operator':'T=S C_beta^tensor24 S, S=exp((beta/6) D_spatial), with the exact normalized single-link Wilson convolution.',
            'retained_space':'R_n=S E_box_n H_GI, E_box_n retains EVERY link assignment with EACH p_e+q_e<=n and EVERY gauge intertwiner, at ALL momenta.',
            'chosen_order':ORDER,'one_link_representations_executed':coeff['representation_count'],
            'exact_coefficient_file_sha256':sha(path),
            'Perron_ratio_convention':'Every lambda_n/lambda_0 ratio uses C_n=p_n/Z_beta in each link. The stored rational table uses p_n/Z_n; its finite top eigenvalue is multiplied by (Z_beta/Z_n)^24. That common scalar cancels in T_n/||T_n||, but must be restored for absolute Perron comparisons.',
            'chosen_bounds':chosen,'order_scan':records,
            'retained_dimension_lower_bound':str(dimension_lower),
            'dimension_lower_bound_derivation':'[((n+1)(n+2)/2)]^6 independent characters on six edge-disjoint loops; multiplication by S is invertible.',
            'maximum_total_degree_in_box':24*ORDER,
            'includes_dressed_V9_catalog_and_dressed_V10_witness_family':True,
            'finite_approximation_kernel':'S(U) product_e p_n((beta/3) ReTr(U_e V_e^*)) S(V). Divide by its top eigenvalue; omitted common Z_beta^(-24) cancels.',
            'finite_Gram_matrix':'G_ij=integral conj(e_i) exp((beta/3) D_spatial) e_j dHaar; K_n=D_n^(1/2) G D_n^(1/2), D_n=product of the stored rational temporal eigenvalues.',
            'normalized_finite_operator':'F D_n F*/||D_n^(1/2)G D_n^(1/2)||, F e_i=S e_i. This is the fully defined finite-rank operator; its full Gram entries were not numerically generated.',
            'proof':['Positive tensor-character coefficients give 0<=C_n<=C using exact Z_beta normalization.',
                     'For x>=0 the relative exponential-series tail increases with x; for x<=0 use the signed Taylor integral remainder.',
                     'Product kernel relative error is <=eta=(1+epsilon)^24-1.',
                     'For every f, |<f,(T-T_n)f>|<=eta<|f|,T|f|><=eta lambda_0 ||f||^2, without any spatial norm factor or computed Perron function.',
                     'The complete dressed box is exactly range(T_n), so its FULL external compression is bounded by eta after normalization.',
                     'Positive residual gives crossing norm<=eta/2, B*B<=eta^2/4, and normalized approximation norm<=eta.'],
            'mathematically_defined_complete_retained_space':True,
            'full_retained_Gram_matrix_entries_executed':False,
            'finite_approximation_eigenvalues_executed':False,
            'Perron_normalization_absolute_value_computed_to_eta_precision':False,
            'continuum_claim':False,
            'sources':{str(p.relative_to(ROOT)):sha(p) for p in
                       [Path(__file__),HERE/'direct_review/certify_gauge_fixed_perron.py',ROOT/'dag_closeout_v5/intervals.py']}}
    (HERE/'DIRECT_NORMALIZED_WILSON_CERTIFICATE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'order':ORDER,'irreps':coeff['representation_count'],
                      'bounds':chosen,'dimension_lower_bound':str(dimension_lower)},indent=2))


if __name__=='__main__':
    main()
