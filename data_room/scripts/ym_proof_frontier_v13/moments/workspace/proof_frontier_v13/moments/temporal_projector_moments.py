#!/usr/bin/env python3
"""Exact <D^2,C_beta^j D^2> polynomial in fundamental, sextet, adjoint c_r.

Uses local SU(3) invariant projectors and Haar tensors, not a low-space
compression between temporal factors. C_beta^j is the FULL 24-link operator.
"""
from collections import Counter,defaultdict
from fractions import Fraction as F
import hashlib,itertools,json,struct
from pathlib import Path
from exact_spatial_jets import ROOT,HERE,find,merge,fusion

def haar(factors,d):
    links={}
    for e,s,a,b in factors:
        links.setdefault(e,{1:[],-1:[]})[s].append((a,b))
    states=[(d,F(1))]
    for e,sides in sorted(links.items()):
        u,v=sides[1],sides[-1];n=len(u)
        assert n==len(v) and n in (1,2),(e,u,v)
        perms=[(0,)] if n==1 else [(0,1),(1,0)]
        nxt=[]
        for old,c in states:
            for sigma in perms:
                for tau in perms:
                    d1=old.copy()
                    for j in range(n):
                        merge(d1,u[j][0],v[sigma[j]][0]);merge(d1,u[j][1],v[tau[j]][1])
                    w=F(1,3) if n==1 else F(1,8) if sigma==tau else F(-1,24)
                    nxt.append((d1,c*w))
        states=nxt
    return sum(c*3**len({find(d,j) for j in range(len(d))}) for d,c in states)

def single(left,right):
    d={(0,0):1}
    for i in right:
        out=Counter()
        for r,m in d.items():
            for t in fusion(r,1 if i%2==0 else -1):out[t]+=m
        d=out
    result=defaultdict(F)
    for r,m in d.items():
        a={r:m}
        for i in left:
            b=Counter()
            for s,n in a.items():
                for t in fusion(s,1 if i%2==0 else -1):b[t]+=n
            a=b
        z=a.get((0,0),0)
        exp=(0,0,0) if r==(0,0) else (4,0,0) if sum(r)==1 else (0,0,4) if r==(1,1) else (0,4,0)
        result[exp]+=z
    return result

def contraction(left,right,words):
    if len(set(i//2 for i in left+right))==1:return single(left,right)
    fac=[];ridx=defaultdict(list)
    for k,i in enumerate(left+right):
        for j,(e,s) in enumerate(words[i]):
            a,b=4*k+j,4*k+(j+1)%4
            if s==-1:a,b=b,a
            if k>=2:ridx[e].append(len(fac))
            fac.append((e,s,a,b))
    # Each state: factors (None means contracted singlet), equality forest,
    # exact scalar coefficient, exponents of c3,c6,c8.
    states=[(fac,list(range(16)),F(1),(0,0,0))]
    for e,ix in sorted(ridx.items()):
        nxt=[]
        for fs,d,c,exp in states:
            def emit(fnew,dnew,coef,var):
                ee=list(exp)
                if var is not None:ee[var]+=1
                nxt.append((fnew,dnew,c*coef,tuple(ee)))
            if len(ix)==1:
                emit(fs,d,F(1),0);continue
            assert len(ix)==2
            i,j=ix;u,v=fs[i],fs[j]
            if u[1]==v[1]:
                # Symmetric/antisymmetric row projectors.
                sw=fs.copy();sw[i]=(u[0],u[1],v[2],u[3]);sw[j]=(v[0],v[1],u[2],v[3])
                emit(fs,d,F(1,2),1);emit(fs,d,F(1,2),0)
                emit(sw,d,F(1,2),1);emit(sw,d,F(-1,2),0)
            else:
                emit(fs,d,F(1),2)
                ds=d.copy();merge(ds,u[2],v[2]);merge(ds,u[3],v[3])
                sing=fs.copy();sing[i]=sing[j]=None
                emit(sing,ds,F(1,3),None);emit(sing,ds,F(-1,3),2)
        states=nxt
    out=defaultdict(F)
    for fs,d,c,exp in states:
        out[exp]+=c*haar([f for f in fs if f is not None],d)
    return {e:c for e,c in out.items() if c}

def main():
    raw=(ROOT/'full_moments_v4/geometry.bin').read_bytes()
    edges=struct.unpack('96B',raw[520:616]);signs=struct.unpack('96b',raw[616:712]);words=[]
    for p in range(24):
        w=list(zip(edges[4*p:4*p+4],signs[4*p:4*p+4]))
        words.extend([w,[(e,-s) for e,s in reversed(w)]])
    spatial=json.loads((HERE/'EXACT_SPATIAL_HAAR_MOMENTS.json').read_text())
    out=defaultdict(F);contractions=0
    for row in spatial['rows'][3]['survivors']:
        ids=row['oriented_trace_ids'];parts=set(itertools.combinations(range(4),2));split=set()
        for ij in parts:
            right=tuple(ids[i] for i in ij);left=tuple(ids[i] for i in range(4) if i not in ij);split.add((left,right))
        for left,right in sorted(split):
            mult=(1 if left[0]==left[1] else 2)*(1 if right[0]==right[1] else 2)
            for e,c in contraction(left,right,words).items():out[e]+=F(mult,16)*c
            contractions+=1
    out={e:c for e,c in sorted(out.items()) if c}
    assert sum(out.values())==F(spatial['moments'][4])
    assert out.get((0,0,0))==144
    assert all(c>=0 for c in out.values()),out
    cert={'schema':'YM_EXACT_FULL_TEMPORAL_SPATIAL_SPECTRAL_MOMENTS_V13',
          'status':'PASS_EXACT_LINK_PROJECTORS_AND_HAAR_TENSORS',
          'quantity':'q_j=<D^2,C_beta^j D^2> for the full 24-link normalized temporal operator',
          'variables':['c_(1,0)^j=c_(0,1)^j','c_(2,0)^j=c_(0,2)^j','c_(1,1)^j'],
          'polynomial':[{'exponents':list(e),'coefficient':str(c)} for e,c in out.items()],
          'total_electric_sectors_after_aggregation':len(out),
          'ordered_pair_multiset_contractions':contractions,
          'identity_operator_check':str(sum(out.values())),
          'haar_projector_check':str(out[(0,0,0)]),
          'full_physical_Wilson_matrices_at_target_beta_computed':False,
          'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'exact_spatial_jets.py',HERE/'EXACT_SPATIAL_HAAR_MOMENTS.json']}}
    (HERE/'EXACT_TEMPORAL_SPECTRAL_MOMENTS.json').write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps(cert,indent=2))
if __name__=='__main__':main()
