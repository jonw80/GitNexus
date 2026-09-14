#!/usr/bin/env python3
"""Test CG dual transport without changing any pinned numerical basis file."""
import os, json, math, hashlib, importlib.util, functools, collections
from pathlib import Path
import numpy as np
import scipy.sparse as sp

root=Path(__file__).parent
out=Path(os.environ['V174_OUT'])
out.mkdir(parents=True,exist_ok=True)
red=Path(os.environ['V174_REDUCER'])
assert hashlib.sha256(red.read_bytes()).hexdigest()=='8d16d84065eeb4269471c125e2e0c25cc4929d37ffebb3d827e642a5bdf8d4c8'
spec=importlib.util.spec_from_file_location('R',red)
R=importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

@functools.lru_cache(128)
def pinned_cg(r,f,t):
    p=R._cgpath(r,f,t)
    if not p.exists():
        raise RuntimeError(('missing immutable CG',r,f,t))
    with np.load(p,allow_pickle=False) as z:
        return tuple(np.array(m,copy=True) for m in z['maps'])

@functools.lru_cache(96)
def pinned_basis(sl):
    p=R._basispath(sl)
    if not p.exists():
        raise RuntimeError(('missing immutable fixed basis',sl))
    with np.load(p,allow_pickle=False) as z:
        return np.array(z['V'],copy=True)

R.cg_maps=pinned_cg
R.fixed_basis_sorted=pinned_basis
dual_rows=[]
cg_rows=[]
def bar(r):return (r[1],r[0])

@functools.lru_cache(None)
def dual(r):
    r=tuple(r); rb=bar(r)
    if r>rb:
        return dual(rb).T
    # This singlet defines a new dual identification only. It does not replace
    # any cached CG map or fixed vertex basis.
    old_ns=R.cgc.null_space
    R.cgc.null_space=R.robust_null_space
    try:
        maps=R._raw_intertwiners(r,rb,(0,0))
    finally:
        R.cgc.null_space=old_ns
    assert len(maps)==1,(r,len(maps))
    d=R.irrep(*r).dim
    J=np.array(maps[0]).reshape(d,d)*math.sqrt(d)
    pivot=int(np.argmax(np.abs(J)))
    if J.ravel()[pivot]<0:J=-J
    ortho=float(np.max(np.abs(J.T@J-np.eye(d))))
    residual=0.
    a,b=R.irrep(*r),R.irrep(*rb)
    for F,G in [(a.F1,b.F1),(a.F2,b.F2),(a.E1,b.E1),(a.E2,b.E2)]:
        residual=max(residual,float(np.max(np.abs(F@J+J@G.T))))
    if ortho>1e-10 or residual>1e-10:
        raise RuntimeError(('dual map failed',r,ortho,residual))
    if r==rb and np.max(np.abs(J-J.T))>1e-10:
        raise RuntimeError(('self-dual symmetry failed',r))
    dual_rows.append({'rep':r,'dimension':d,'orthogonality':ortho,'invariance':residual})
    return J

@functools.lru_cache(None)
def incoming_sign(oldbar,actbar,newbar):
    r,f,t=bar(oldbar),bar(actbar),bar(newbar)
    maps=pinned_cg(r,f,t); incoming=pinned_cg(oldbar,actbar,newbar)
    assert len(maps)==len(incoming)==1,(r,f,t)
    dr,df,dt=R.irrep(*r).dim,R.irrep(*f).dim,R.irrep(*t).dim
    C=maps[0].reshape(dr,df,dt)
    transported=np.einsum('ic,ag,iak,kv->cgv',dual(r),dual(f),C,dual(t),optimize=True).reshape(dr*df,dt)
    raw=incoming[0]
    alpha=float(np.vdot(raw,transported)/dt)
    sign=1 if alpha>=0 else -1
    defect=float(np.max(np.abs(transported-sign*raw)))
    if abs(abs(alpha)-1)>1e-10 or defect>1e-10:
        raise RuntimeError(('incoming map is not a phase transport',oldbar,actbar,newbar,alpha,defect))
    cg_rows.append({'oldbar':oldbar,'actionbar':actbar,'newbar':newbar,'phase':sign,'alpha':alpha,'max_residual':defect})
    return sign

old_local=R.local_matrix
@functools.lru_cache(50000)
def local(oldlabs,newlabs,actitems,old_fixed,new_fixed):
    phase=1
    for leg,act in actitems:
        if leg>=3:
            phase*=incoming_sign(tuple(oldlabs[leg]),tuple(act),tuple(newlabs[leg]))
    return phase*old_local(oldlabs,newlabs,actitems,old_fixed,new_fixed)

C0,_=R.low_raw_C()
s,ncc,contr,eigres,logc=R.recover_phase(C0)
H0=(C0@sp.diags(s.astype(float))).tocsr()
D0=(H0-H0.T).tocoo()
asym0=float(np.abs(D0.data).max()) if D0.nnz else 0.
assert ncc==1 and contr==0 and asym0<=1e-8
R.local_matrix=local
C1,_=R.low_raw_C()
D1=(C1-C1.T).tocoo()
asym1=float(np.abs(D1.data).max()) if D1.nnz else 0.

def align(reference, candidate):
    adj=[[] for _ in range(R.NLOW)]
    coo=reference.tocoo()
    magnitude=0.;unsupported=0
    for i,j,x in zip(coo.row,coo.col,coo.data):
        y=float(candidate[i,j])
        magnitude=max(magnitude,abs(abs(x)-abs(y)))
        if abs(x)>1e-12 and abs(y)>1e-12:
            rel=1 if x*y>0 else -1
            adj[i].append((int(j),rel))
        elif abs(x-y)>1e-12:unsupported+=1
    extra=(candidate-reference.multiply(candidate.sign()*reference.sign())).tocoo()
    gauge=np.zeros(R.NLOW,dtype=np.int8);components=conflicts=0
    for start in range(R.NLOW):
        if gauge[start]:continue
        components+=1;gauge[start]=1;queue=collections.deque([start])
        while queue:
            i=queue.popleft()
            for j,rel in adj[i]:
                desired=int(gauge[i])*rel
                if gauge[j]==0:gauge[j]=desired;queue.append(j)
                elif gauge[j]!=desired:conflicts+=1
    diff=(candidate-sp.diags(gauge.astype(float))@reference@sp.diags(gauge.astype(float))).tocoo()
    residual=float(np.abs(diff.data).max()) if diff.nnz else 0.
    return gauge,{'components':components,'phase_conflicts':conflicts,
                  'magnitude_error':magnitude,'support_failures':unsupported,
                  'full_matrix_residual':residual,'pass':bool(conflicts==0 and residual<=1e-10)}

gauge,alignment=align(H0,C1)
np.save(out/'candidate_low_gauge.npy',gauge)
details=json.loads((root/'aggregate_evidence.json').read_text())
acc=collections.defaultdict(lambda:[[],[]])
term_errors=[]
def value(key,vb,nk,nvb,pidx,ar):
    factor=.5
    for li,_ in R.pl_edges[pidx]:
        factor*=math.sqrt(R.irrep(*key[li]).dim/R.irrep(*nk[li]).dim)
    ov,nv=R.gvl(key),R.gvl(nk)
    av=R.action_vertex_legs(pidx,ar)
    for v in R.pl_aff[pidx]:
        M=local(tuple(ov[v]),tuple(nv[v]),tuple(av[v]),True,True)
        factor*=M[nvb[v],vb[v]]
    return float(factor)
for term in details['terms']:
    key,vb=R.decode_state(bytes.fromhex(term['source56']))
    nk,nvb=R.decode_state(bytes.fromhex(term['raw_target']))
    i,pidx,ar=term['source'],term['pidx'],term['ar']
    f=value(key,vb,nk,nvb,pidx,ar)
    r=value(nk,nvb,key,vb,pidx,-ar)
    err=abs(f-r)
    ns=R.orbit_size_bytes(bytes.fromhex(term['source56']))
    nt=R.orbit_size_bytes(bytes.fromhex(term['target']))
    fac=R.A*math.sqrt(ns/nt)*float(R.psi[i])*int(gauge[i])
    acc[term['target']][0].append(fac*f)
    acc[term['target']][1].append(fac*r)
    term_errors.append({'source':i,'target':term['target'],'forward':f,'reverse':r,'abs_difference':err})
rows=[{'target':t,'R':math.fsum(v[0]),'W':math.fsum(v[1])} for t,v in sorted(acc.items())]
summary={'schema':'YM_DUAL_TRANSPORT_CANDIDATE_V1','status':'DIAGNOSTIC_ONLY',
         'low_original_symmetry':asym0,'low_corrected_symmetry':asym1,
         'low_operator_alignment':alignment,
         'target_count':len(rows),'term_count':len(term_errors),
         'max_term_adjoint_error':max(x['abs_difference'] for x in term_errors),
         'target_R2':math.fsum(x['R']**2 for x in rows),'target_W2':math.fsum(x['W']**2 for x in rows),
         'max_target_error':max(abs(x['R']-x['W']) for x in rows),
         'dual_map_count':len(dual_rows),'incoming_phase_count':len(cg_rows),
         'full_crossing_gate_passed':False,'external_norm_started':False}
result={'summary':summary,'dual_maps':dual_rows,'incoming_phases':cg_rows,'targets':rows,'terms':term_errors}
(out/'dual_transport_candidate.json').write_text(json.dumps(result,indent=2))
print('DUAL_TRANSPORT_SUMMARY_JSON='+json.dumps(summary),flush=True)
print('DUAL_TRANSPORT_DETAILS_JSON='+json.dumps(result),flush=True)
if asym1>1e-10 or not alignment['pass'] or summary['max_term_adjoint_error']>1e-10:
    raise SystemExit(2)
