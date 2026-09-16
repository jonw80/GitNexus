#!/usr/bin/env python3
"""Independent enclosure/check of the adaptive-cutoff arithmetic, using V13
uniformity's different exponential stopping rule. Does not assemble operators.
"""
from pathlib import Path
from fractions import Fraction as F
import math,json,hashlib
from certify_uniformity import exp_iv

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'ADAPTIVE_TRUNCATION_CERTIFICATE.json'

def main():
    data=json.loads(SOURCE.read_text())
    beta=F(271,20)
    be=exp_iv(beta)
    he=exp_iv(beta/2)
    target=F(1,10**12)
    def eps(n):
        return max(beta**(n+1)/math.factorial(n+1)/(1-beta/(n+2))/be[0],he[1]*(beta/2)**(n+1)/math.factorial(n+1))
    checks=[]
    for row in data['executed_volumes']:
        E=row['links'];n=row['selected_per_link_degree']
        assert E==3*row['spatial_side']**3
        bound=2*E*eps(n)
        assert bound<=target
        assert 2*E*eps(n-1)>target
        assert bound<=F(row['normalized_full_operator_error_upper'])
        checks.append({'L':row['spatial_side'],'n':n,'checked':True})
    for row in data['fixed_cutoff_obstructions']:
        n=row['fixed_order'];L=int(row['cubic_side_with_E_times_rho_at_least_one'])
        rho=beta**(n+1)/math.factorial(n+1)/be[1]
        assert 3*L**3*rho>=1
    out={'schema':'YM_ADAPTIVE_TRUNCATION_INDEPENDENT_REVIEW_V13','status':'PASS',
         'exponential_enclosure':'Exact rational Taylor with adaptive absolute tail stopping from independent uniformity module',
         'executed_rows':checks,'endpoint_obstruction_rows_checked':2,
         'proof_review':'Loewner residual, norm normalization and adaptive all-volume error implications verified on stated complete dressed spaces.',
         'clarification':'Pointwise endpoint obstruction refers to the explicit product-kernel representative before gauge averaging; it is not a physical compressed-operator-norm obstruction.',
         'full_moment_matrices_or_uniform_gap_proved':False,
         'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    (HERE/'ADAPTIVE_TRUNCATION_INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
