#!/usr/bin/env python3
"""Exact SU(3) Haar moments of the pinned full 24-plaquette action through order 4.

Each matrix-entry integral uses exact rational SU(3) orthogonality/degree-two
Weingarten contraction. A linkwise center-charge filter is exact and exhaustive.
No Monte Carlo, affine transfer, or uncomputed numerical eigenvalue is used.
"""
from collections import Counter
from fractions import Fraction as F
import hashlib
from itertools import combinations_with_replacement
import json
from math import factorial
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def fusion(r,sgn):
    p,q=r
    out=[(p+1,q),(p-1,q+1),(p,q-1)] if sgn==1 else [(p,q+1),(p+1,q-1),(p-1,q)]
    return [x for x in out if min(x)>=0]

def single_loop_integral(signs):
    d={(0,0):1}
    for s in signs:
        out=Counter()
        for r,m in d.items():
            for t in fusion(r,s): out[t]+=m
        d=out
    return F(d.get((0,0),0))

def find(d,x):
    while d[x]!=x: x=d[x]
    return x

def merge(d,a,b):
    a,b=find(d,a),find(d,b)
    if a!=b: d[b]=a

def integrate(ids,words):
    if len(set(i//2 for i in ids))==1:
        return single_loop_integral([1 if i%2==0 else -1 for i in ids])
    links={}
    for k,i in enumerate(ids):
        for j,(e,s) in enumerate(words[i]):
            a,b=4*k+j,4*k+(j+1)%4
            if s==-1: a,b=b,a
            links.setdefault(e,{1:[],-1:[]})[s].append((a,b))
    states=[(list(range(4*len(ids))),F(1))]
    kinds=Counter()
    for e,sides in sorted(links.items()):
        u,v=sides[1],sides[-1]
        assert len(u)==len(v), (ids,e,u,v)
        n=len(u)
        assert n in (1,2), (ids,e,n)
        kinds[n]+=1
        next_states=[]
        perms=[(0,)] if n==1 else [(0,1),(1,0)]
        for old,c in states:
            for sigma in perms:
                for tau in perms:
                    d=old.copy()
                    for j in range(n):
                        merge(d,u[j][0],v[sigma[j]][0])
                        merge(d,u[j][1],v[tau[j]][1])
                    w=F(1,3) if n==1 else F(1,8) if sigma==tau else F(-1,24)
                    next_states.append((d,c*w))
        states=next_states
    value=sum(c*3**len({find(d,j) for j in range(len(d))}) for d,c in states)
    return value

def main():
    geo=ROOT/'full_moments_v4/geometry.bin'
    raw=geo.read_bytes()
    assert raw[:8]==b'YMGEOM04'
    edges=struct.unpack('96B',raw[520:616]); signs=struct.unpack('96b',raw[616:712])
    words=[]
    for p in range(24):
        word=list(zip(edges[4*p:4*p+4],signs[4*p:4*p+4]))
        assert len(set(e for e,s in word))==4
        words.extend([word,[(e,-s) for e,s in reversed(word)]])
    charge=[]
    for word in words:
        x=[0]*24
        for e,s in word:x[e]=s
        charge.append(x)
    rows=[]; moments=[F(1)]
    for k in range(1,5):
        survivors=[]; tot=F(0); candidates=0
        for ids in combinations_with_replacement(range(48),k):
            candidates+=1
            if any(sum(charge[i][e] for i in ids)%3 for e in range(24)):continue
            value=integrate(ids,words)
            denom=1
            for n in Counter(ids).values():denom*=factorial(n)
            mult=factorial(k)//denom
            term=F(mult,2**k)*value;tot+=term
            survivors.append({'oriented_trace_ids':list(ids),'integral':str(value),'multinomial':mult,'contribution_to_action_moment':str(term)})
        moments.append(tot)
        rows.append({'order':k,'candidate_multisets':candidates,'center_balanced_multisets':len(survivors),'moment':str(tot),'survivors':survivors})
        print(k,candidates,len(survivors),str(tot),flush=True)
    cert={
       'schema':'YM_FULL_SPATIAL_HAAR_MOMENTS_V13',
       'status':'PASS_EXACT_FOURTH_ORDER_HAAR_INTEGRATION',
       'operator_action':'D=sum_{p=0}^{23} Re Tr U_p on the exact 24-link geometry',
       'moments':[str(x) for x in moments],
       'spatial_partition_Taylor_coefficients':[str(x/factorial(k)) for k,x in enumerate(moments)],
       'raw_basis':['1','D'],
       'G_series_through_second_order':[[[str(moments[i+j+k]/factorial(k)) for j in range(2)] for i in range(2)] for k in range(3)],
       'rows':rows,
       'target_beta_matrices_materialized':False,
       'sources':{str(geo.relative_to(ROOT)):hashlib.sha256(raw).hexdigest(),str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    (HERE/'EXACT_SPATIAL_HAAR_MOMENTS.json').write_text(json.dumps(cert,indent=2)+'\n')
if __name__=='__main__': main()
