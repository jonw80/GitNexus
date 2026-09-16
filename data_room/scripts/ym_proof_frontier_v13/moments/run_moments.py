#!/usr/bin/env python3
"""Fail-closed entry point for the standalone V13 moment calculation."""
import hashlib,json,subprocess,sys,time
from pathlib import Path

BASE=Path(__file__).resolve().parent;WORK=BASE/'workspace';OUT=WORK/'proof_frontier_v13/moments'
EXPECTED={
 'MOMENT_WILSON_COEFFICIENT_INPUT.json':'PASS_REGENERATED_OUTWARD_BESSEL_DETERMINANTS',
 'TEMPORAL_VACUUM_SEPARATION_CERTIFICATE.json':'PASS_ALL_IRREP_GLOBAL_BOUND',
 'EXACT_SPATIAL_HAAR_MOMENTS.json':'PASS_EXACT_FOURTH_ORDER_HAAR_INTEGRATION',
 'EXACT_TEMPORAL_SPECTRAL_MOMENTS.json':'PASS_EXACT_LINK_PROJECTORS_AND_HAAR_TENSORS',
 'PHYSICAL_MOMENT_JETS_CERTIFICATE.json':'PASS_EXACT_SPATIAL_JETS_AND_OUTWARD_NUMERICAL_EVALUATION',
}

def main():
    start=time.monotonic()
    (BASE/'MOMENT_EXECUTION_CERTIFICATE.json').unlink(missing_ok=True)
    for row in json.loads((BASE/'STAGED_SOURCE_PROVENANCE.json').read_text()):
        assert hashlib.sha256((BASE/row['path']).read_bytes()).hexdigest()==row['staged_sha256'],row['path']
    for filename in EXPECTED:(OUT/filename).unlink(missing_ok=True)
    steps=[]
    commands=[[sys.executable,str(BASE/'prepare_inputs.py')]]+[[sys.executable,str(OUT/f)] for f in ['exact_spatial_jets.py','temporal_projector_moments.py','certify_physical_moment_jets.py']]
    for cmd in commands:
        then=time.monotonic();p=subprocess.run(cmd,cwd=WORK,capture_output=True,text=True)
        name=Path(cmd[1]).stem
        (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
        if p.returncode:raise RuntimeError(f'{name} failed with exit {p.returncode}: {p.stderr[-2000:]}')
        steps.append({'script':name,'returncode':p.returncode,'elapsed_seconds':time.monotonic()-then})
    records=[]
    for filename,status in EXPECTED.items():
        p=OUT/filename;x=json.loads(p.read_text());assert x['status']==status,(filename,x.get('status'))
        records.append({'path':str(p.relative_to(BASE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'status':status})
    spatial=json.loads((OUT/'EXACT_SPATIAL_HAAR_MOMENTS.json').read_text())
    physical=json.loads((OUT/'PHYSICAL_MOMENT_JETS_CERTIFICATE.json').read_text())
    spectral=json.loads((OUT/'EXACT_TEMPORAL_SPECTRAL_MOMENTS.json').read_text())
    assert spatial['moments']==['1','0','12','6','3890/9']
    assert spectral['total_electric_sectors_after_aggregation']==13
    assert physical['target_beta_full_physical_matrices_materialized'] is False
    assert physical['volume_uniform_or_continuum_claim'] is False
    cert={'schema':'YM_MINIMAL_PHYSICAL_MOMENT_EXECUTION_V13','status':'PASS_ALL_REQUIRED_CALCULATIONS_AND_SCOPE_GATES','steps':steps,'outputs':records,'elapsed_seconds':time.monotonic()-start,'target_isotropic_full_moments_closed':False,'continuum_closed':False}
    (BASE/'MOMENT_EXECUTION_CERTIFICATE.json').write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps(cert,indent=2))
if __name__=='__main__':main()
