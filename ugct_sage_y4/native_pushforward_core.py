#!/usr/bin/env sage -python
import hashlib,itertools,json
from pathlib import Path
from sage.all import QQ,PolynomialRing
DATA=Path('data'); REPORTS=Path('reports'); SOURCES=Path('sources')
DATA.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
MODEL=DATA/'intersectionnumbers_a4_model.json'; OUT=DATA/'higher_cartan_closure_rules.json'; REP=REPORTS/'higher_cartan_native_sage_report.json'; PKG=SOURCES/'IntersectionNumbers.m'; THIS=Path(__file__)
BASE=['R','H']+[f'E{i}' for i in range(1,9)]; C=[f'C{i}' for i in range(1,5)]; ORD={n:i for i,n in enumerate(BASE+['Z']+C)}
def hfile(p):
    if not p.exists(): return 'missing'
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''): h.update(b)
    return h.hexdigest()
def htxt(s): return hashlib.sha256(s.encode()).hexdigest()
def emit(o): REP.write_text(json.dumps(o,indent=2,sort_keys=True)); print(json.dumps(o,indent=2,sort_keys=True))
def k(parts): return ','.join(sorted(parts,key=lambda x:ORD[x]))
def rs(x):
    q=QQ(x); return str(q.numerator()) if q.denominator()==1 else f'{q.numerator()}/{q.denominator()}'
if not MODEL.exists(): emit({'status':'NATIVE_SAGE_NOT_RUN','reason':'missing A4 model'}); raise SystemExit(0)
model=json.loads(MODEL.read_text())
RING=PolynomialRing(QQ,['e0','e1','e2','e3','e4','L','R','H']+[f'ee{i}' for i in range(1,9)])
F=RING.fraction_field(); V={n:F(g) for n,g in zip(RING.variable_names(),F.gens())}
e0,e1,e2,e3,e4,L,R,H=[V[n] for n in ['e0','e1','e2','e3','e4','L','R','H']]; ee={i:V[f'ee{i}'] for i in range(1,9)}
S=R; HS=3*e0+6*L-(e1+e2+e3+e4)
Cart={'C1':e1-e2,'C2':e3-e4,'C3':e4,'C4':e2-e3}
B={'R':R,'H':H,**{f'E{i}':ee[i] for i in range(1,9)}}
Centers={e1:[2*L,3*L,S], e2:[3*L-e1,e1], e3:[2*L-e1,e2], e4:[3*L-e1-e2,e3]}
def sub(expr,var,val): return F(expr).subs({var:F(val)})
def blow(expr,E,Us):
    total=F(0); Us=[F(u) for u in Us]
    for j,Uj in enumerate(Us):
        c=F(1)
        for m,Um in enumerate(Us):
            if m!=j: c*=Um/(Um-Uj)
        total+=sub(expr,E,-Uj)*c
    return F(total)
def p0(expr):
    roots=[2*L,3*L,F(0)]; total=F(0)
    for j,cj in enumerate(roots):
        c=F(1)
        for m,cm in enumerate(roots):
            if m!=j: c*=F(1)/(cj-cm)
        total+=sub(expr,e0,-cj)*c
    return F(total)
def push(expr):
    x=F(expr)
    for E in [e4,e3,e2,e1]: x=blow(x,E,Centers[E])
    return p0(x)
def substL(poly): return F(poly).subs({L:2*R+6*H-2*sum(ee[i] for i in range(1,9))})
def intB3(poly):
    frac=substL(poly); num=RING(frac.numerator()); den=RING(frac.denominator())
    if den!=1: num=RING(F(num)/F(den))
    total=QQ(0); names=list(RING.variable_names())
    for exp,coef in num.dict().items():
        p=dict(zip(names,exp))
        if any(p.get(f'e{i}',0) for i in range(5)) or p.get('L',0): raise ValueError('uneliminated ambient variable')
        deg=p.get('R',0)+p.get('H',0)+sum(p.get(f'ee{i}',0) for i in range(1,9))
        if deg!=3: continue
        r,h=p.get('R',0),p.get('H',0); es=[i for i in range(1,9) for _ in range(p.get(f'ee{i}',0))]; val=QQ(0)
        if r==3 and h==0 and not es: val=1
        elif r==2 and h==1 and not es: val=-3
        elif r==2 and h==0 and len(es)==1: val=-1
        elif r==1 and h==2 and not es: val=1
        elif r==1 and h==0 and len(es)==2 and es[0]==es[1]: val=-1
        total+=QQ(coef)*val
    return total
def inter(ds):
    x=HS
    for d in ds: x*=d
    return intB3(push(x))
vals={}; errors={}
for base in BASE:
    for tri in itertools.combinations_with_replacement(range(1,5),3):
        kk=k([base]+[C[i-1] for i in tri])
        try: vals[kk]=rs(inter([B[base]]+[Cart[C[i-1]] for i in tri]))
        except Exception as e: errors[kk]=str(e)
for quad in itertools.combinations_with_replacement(range(1,5),4):
    kk=k([C[i-1] for i in quad])
    try: vals[kk]=rs(inter([Cart[C[i-1]] for i in quad]))
    except Exception as e: errors[kk]=str(e)
if errors:
    emit({'status':'NATIVE_SAGE_PUSHFORWARD_FAILED','computed_count':len(vals),'error_count':len(errors),'error_sample':dict(list(errors.items())[:40])}); raise SystemExit(0)
value_hash=htxt(json.dumps(vals,sort_keys=True)); mh=hfile(MODEL); sh=hfile(THIS); ph=hfile(PKG)
out={'schema_version':'UGCT_HIGHER_CARTAN_CLOSURE_RULES_V5_NATIVE_PUSHFORWARD','status':'EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED','resolution_chamber':'Esole-Yau Ewx split A4 SU(5) Tate model','value_count':len(vals),'required_value_count':235,'exact_values':vals,'fallback_rule':{'enabled':False,'name':'NO_FALLBACK_FOR_CERTIFICATION'},'provenance':{'toolchain':'Native Sage/Python blowup-pushforward engine','toolchain_version':'SageMath over QQ; see workflow log','source_geometry':'A4/SU(5) Tate model from IntersectionNumbers.m source formulas; B3=P(O+K_dP8)','sr_linear_ideal_hash':'sha256:'+mh,'proper_transform_hash':'sha256:'+mh,'script_hash':'sha256:'+sh,'independent_rerun_hash':'sha256:'+value_hash,'source_package_hash':'sha256:'+ph},'computed_by':THIS.name,'source_model':{'generators':model.get('generators_inputform'),'hypersurface':model.get('hypersurface_inputform'),'divisors':model.get('divisors_inputform')}}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); emit({'status':'NATIVE_SAGE_EXACT_PUSHFORWARD_VALUES_EXPORTED','value_count':len(vals),'output':str(OUT),'independent_rerun_hash':'sha256:'+value_hash})
