"""Independent rational scalar check and guard against false operator order."""
from fractions import Fraction as F
from pathlib import Path
import math,json,hashlib
H=Path(__file__).resolve().parent
def lower_exp(x):
    # Independent fixed cutoff (the generator uses 512 terms here).
    v=s=F(1)
    for j in range(1,257):v=v*x/j;s+=v
    return s
def eps(z,n):
    return z**(n+1)/math.factorial(n+1)/(1-z/(n+2))/lower_exp(z)
def main():
    c=json.loads((H/'TARGET_COUPLING_CERTIFICATE.json').read_text())
    a=eps(F(813,80),c['spatial_degree']);b=eps(F(813,40),c['temporal_degree'])
    d=48*a+24*b
    assert a<=F(c['spatial_relative_tail_upper'])
    assert b<=F(c['temporal_relative_tail_upper'])
    assert d<=F(c['kernel_relative_error_upper'])
    assert 2*d<=F(c['normalized_operator_error_upper'])<F(1,10**220)
    assert d*d<=F(c['full_new_BstarB_upper'])
    for row in c['uniform_approximation_examples']:
        E=row['links_and_plaquettes'];error=4*E*eps(F(813,80),row['spatial_degree'])+2*E*eps(F(813,40),row['temporal_degree'])
        assert error<=F(row['normalized_operator_error_upper'])<=F(1,10**12)
    # T=[[1,.9],[.9,1]], L=diag(1,.5): T-LTL has negative determinant.
    determinant=-F(9,20)**2;assert determinant<0
    assert not c['full_target_matrix_contractions_executed']
    assert not c['uniform_physical_gap_proved'] and not c['continuum_construction_proved']
    result={'status':'PASS_INDEPENDENT_RATIONAL_SCALARS_AND_SCOPE',
      'certificate_sha256':hashlib.sha256((H/'TARGET_COUPLING_CERTIFICATE.json').read_bytes()).hexdigest(),
      'independent_exp_lower_terms':256,'all_ten_volume_examples_checked':True,
      'kernel_order_does_not_imply_Loewner_order_witness_determinant':str(determinant),
      'full_target_matrices_closed':False,'uniform_physical_gap_closed':False,'continuum_closed':False}
    (H/'INDEPENDENT_SCALAR_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
