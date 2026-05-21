#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
DATA=ROOT/'data'
OUT=DATA/'primary_math_structural_report.json'

def rec(name,ok,derived,fail): return {'name':name,'ok':ok,'derived':derived,'failures':fail}

def ym():
    p=REPO/'data_room/primary/ym/companion_hash.txt'; f=[]
    if not p.exists(): f.append('missing companion marker'); txt=''
    else: txt=p.read_text().strip()
    if not txt: f.append('empty companion marker')
    return rec('ym_mass_gap_import',not f,{'bytes':len(txt),'lines':len(txt.splitlines())},f)

def hadamard():
    p=REPO/'data_room/primary/hadamard/determinant_identity.tex'; f=[]
    if not p.exists(): return rec('hadamard_divisor',False,{},['missing determinant identity'])
    txt=p.read_text(); req=['D(s)=E(s)\\Xi(s)','H2 graph-norm tail','Parity-gap persistence','Hurwitz transfer','zero-free']
    missing=[x for x in req if x not in txt]
    f += ['missing marker: '+x for x in missing]
    return rec('hadamard_divisor',not f,{'markers_present':len(req)-len(missing),'markers_required':len(req)},f)

def y4():
    p=REPO/'ugct_sage_y4/reports/chow_tensor_export.json'; f=[]
    if not p.exists(): return rec('y4_tensor',False,{},['missing tensor export'])
    o=json.loads(p.read_text()); q=o['quadruple_intersection_tensor']; count=int(q['nonzero_count']); entries=q.get('entries') or q.get('sample_entries') or []
    if count<=0: f.append('nonpositive count')
    for e in entries:
        if len(e.get('indices',[]))!=4: f.append('entry lacks four indices')
        if not isinstance(e.get('value'),int): f.append('entry value not integer')
    w=o.get('workflow',{})
    imported=('compressed' in q.get('encoding','').lower() and w.get('status')=='FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED' and w.get('run_id') and w.get('job_id') and w.get('artifact_id'))
    if len(entries)!=count and not imported: f.append('partial tensor without import metadata')
    return rec('y4_tensor',not f,{'nonzero_count':count,'inline_entries':len(entries),'manifest_import':bool(imported)},f)

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    rows=[ym(),hadamard(),y4()]; ok=all(r['ok'] for r in rows)
    out={'schema_version':'UGCT_PRIMARY_MATH_STRUCTURAL_V1','status':'PASSED' if ok else 'FAILED','records':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
