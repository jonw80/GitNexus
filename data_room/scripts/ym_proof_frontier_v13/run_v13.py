from pathlib import Path
import subprocess,sys,json,hashlib
H=Path(__file__).resolve().parent
(H/'V13_EXECUTION_MANIFEST.json').unlink(missing_ok=True)
commands=['moments/run_moments.py','bounds/adaptive_truncation.py','bounds/uniformity/certify_uniformity.py','bounds/uniformity/review_adaptive_truncation.py']
for s in commands:
    p=subprocess.run([sys.executable,str(H/s)],capture_output=True,text=True)
    (H/(Path(s).stem+'.log')).write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(s+' failed: '+p.stderr[-2000:])
    print('PASS '+s,flush=True)
required=['moments/MOMENT_EXECUTION_CERTIFICATE.json','bounds/ADAPTIVE_TRUNCATION_CERTIFICATE.json','bounds/uniformity/UNIFORMITY_SCALAR_CERTIFICATE_V13.json','bounds/uniformity/ADAPTIVE_TRUNCATION_INDEPENDENT_REVIEW.json']
mc=json.loads((H/required[0]).read_text())
assert mc['status']=='PASS_ALL_REQUIRED_CALCULATIONS_AND_SCOPE_GATES'
for r in mc['outputs']:
    p=H/'moments'/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    required.append(str(p.relative_to(H)))
records=[]
for f in required:
    p=H/f;x=json.loads(p.read_text())
    records.append({'path':f,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'status':x.get('status','EXECUTED_WITH_ASSERTIONS')})
out={'status':'PASS_NINE_REQUIRED_OUTPUTS','outputs':records,'full_target_matrices_closed':False,'uniform_physical_gap_closed':False,'continuum_closed':False}
assert len(records)==9
(H/'V13_EXECUTION_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
