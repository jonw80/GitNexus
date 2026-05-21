#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
DATA=ROOT/'data'
OUT=DATA/'primary_math_core_report.json'

def j(rel):
    return json.loads((REPO/rel).read_text())

def I(v):
    if isinstance(v,dict): return (float(v['lower']),float(v['upper']))
    return (float(v[0]),float(v[1]))

def contains(a,b,tol=0.0):
    return a[0] <= b[0]+tol and a[1]+tol >= b[1]

def rec(name,ok,derived,fail):
    return {'name':name,'ok':ok,'derived':derived,'failures':fail}

def pfaffian():
    f=[]; o=j('data_room/primary/pfaffian/operator_matrix.json'); b=o['finite_block']
    p=I(b['pfaffian_interval']); r=float(b['collar_variation_radius'])+float(b['spectral_tail_radius'])
    d=(p[0]-r,p[1]+r); s=I(b['final_interval'])
    if abs(d[0]-s[0])>1e-15 or abs(d[1]-s[1])>1e-15: f.append('final interval mismatch')
    if o.get('zero_modes',{}).get('count')!=0: f.append('zero modes not removed')
    return rec('pfaffian',not f,{'computed_final_interval':d,'stated':s},f)

def uplift():
    f=[]; o=j('data_room/primary/uplift/hessian_matrix.json'); H=o['interval_hessian_matrix']; bounds=[]
    for i,row in enumerate(H):
        diag=I(row[i])[0]; off=0.0
        for k,x in enumerate(row):
            if k!=i:
                lo,hi=I(x); off += max(abs(lo),abs(hi))
        bounds.append(diag-off)
    g=min(bounds); claim=float(o['hessian_lambda_min_lower'])
    if g<=0: f.append('nonpositive Hessian bound')
    if g+1e-15<claim: f.append('claimed Hessian bound exceeds derived bound')
    if float(o['boundary_potential_gap_lower'])<=0: f.append('boundary gap not positive')
    if I(o['V_phys_interval'])[0]<=0: f.append('V interval not positive')
    return rec('uplift',not f,{'gershgorin_bounds':bounds,'lambda_claim':claim},f)

def cosmology():
    f=[]; o=j('data_room/primary/cosmology/interval_sum.json'); lo=hi=0.0
    for t in o['interval_terms']:
        c=float(t['center']); r=float(t['radius']); lo += c-r; hi += c+r
    s=I(o['rho_lambda_interval'])
    if not contains(s,(lo,hi),1e-140): f.append('rho interval does not contain term sum')
    if o.get('no_free_offset_field') is not True: f.append('free-offset guard not true')
    return rec('cosmology',not f,{'computed_sum':(lo,hi),'stated':s},f)

def prime():
    f=[]; o=j('data_room/primary/prime_race/arb_matrices.json')
    fw=I(o['polymer_cumulant_bounds']['finite_window_density_interval']); tail=float(o['arb_payload']['tail_bound_upper'])
    d=(fw[0]-tail,fw[1]-tail); s=I(o['density_interval'])
    if abs(d[0]-s[0])>1e-12 or abs(d[1]-s[1])>1e-12: f.append('density interval mismatch')
    if s[0] <= 0.5: f.append('density does not clear one half')
    if float(o['polymer_cumulant_bounds']['KP_norm_bound'])>=1: f.append('KP norm not below one')
    spec=o['spectral_identification']
    if spec.get('GRH_used') or spec.get('LI_used'): f.append('forbidden imported hypothesis flag')
    return rec('prime_race',not f,{'computed_density_interval':d,'epsilon':s[0]-0.5},f)

def proton():
    f=[]; o=j('data_room/primary/proton/ensemble.json')
    cp=I(o['c_p_interval']); lam=I(o['lambda_qcd_interval_GeV']); mp=I(o['proton_mass_interval_GeV'])
    mass=(cp[0]*lam[0],cp[1]*lam[1])
    if not contains(mass,mp,1e-12): f.append('mass interval not contained in cp*Lambda')
    for k,v in o['lattice_controls'].items():
        if v is not True: f.append('false lattice control '+k)
    return rec('proton_cp',not f,{'computed_mass_enclosure':mass,'stated_mass_interval':mp},f)

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    rows=[pfaffian(),uplift(),cosmology(),prime(),proton()]
    ok=all(r['ok'] for r in rows)
    out={'schema_version':'UGCT_PRIMARY_MATH_CORE_V1','status':'PASSED' if ok else 'FAILED','records':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
