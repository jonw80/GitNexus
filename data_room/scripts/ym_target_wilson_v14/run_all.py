"""Execute the target-coupling calculation without treating open gates as pass."""
from pathlib import Path
import subprocess,sys,json,hashlib
H=Path(__file__).resolve().parent
def main():
    (H/'EXECUTION_MANIFEST.json').unlink(missing_ok=True)
    for script in ['certify_target.py','build_factors.py','verify_factors_weyl.py','verify_target.py']:
        subprocess.run([sys.executable,str(H/script)],cwd=H,check=True)
    c=json.loads((H/'TARGET_COUPLING_CERTIFICATE.json').read_text())
    w=json.loads((H/'INDEPENDENT_WEYL_VERIFICATION.json').read_text())
    assert w['status']=='PASS_ALL_70566_COEFFICIENTS'
    assert not c['full_target_matrix_contractions_executed']
    files=['TARGET_COUPLING_CERTIFICATE.json','FACTOR_EXECUTION.json','INDEPENDENT_WEYL_VERIFICATION.json','INDEPENDENT_SCALAR_VERIFICATION.json','SPATIAL_233_FACTOR.json.gz','TEMPORAL_292_FACTOR.json.gz']
    rows=[{'path':p,'bytes':(H/p).stat().st_size,'sha256':hashlib.sha256((H/p).read_bytes()).hexdigest()} for p in files]
    result={'status':'PASS_LOCAL_FACTORS_AND_ERROR_BOUND_ONLY','outputs':rows,
      'target_beta':'271/20','full_target_matrices_closed':False,'uniform_physical_gap_closed':False,'continuum_closed':False}
    (H/'EXECUTION_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
