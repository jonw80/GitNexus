#!/usr/bin/env python3
import os, json, math, itertools, argparse, importlib.util, hashlib
from pathlib import Path
import numpy as np

EXPECTED_G10=204.7027392787848
EXPECTED_REDUCER='8d16d84065eeb4269471c125e2e0c25cc4929d37ffebb3d827e642a5bdf8d4c8'
EXPECTED_INV='a52dd10abd71c10340dd364f0287d1a46df150c5a9150a2f3c7e4aa8e8b0bf0a'

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_R():
    p=Path(os.environ['V174_REDUCER']); assert sha256(p)==EXPECTED_REDUCER
    spec=importlib.util.spec_from_file_location('R',p); R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R); return R

def cross(a):
    R=load_R(); low=R.low_states; psi=np.asarray(R.psi,float)
    assert len(low)==len(psi)==7576
    lo=len(low)*a.shard//a.nshards; hi=len(low)*(a.shard+1)//a.nshards
    acc={}; br=oc=0; recip=0.0
    for i in range(lo,hi):
        key,vb=low[i]; raw=R.encode_state(key,vb); ns=R.orbit_size_bytes(raw); q=float(psi[i])
        for pidx in range(24):
            for ar in (1,-1):
                for nk in R.branches(key,pidx,ar):
                    dg=R.degree(nk)
                    if dg<10 or dg>13 or not R.valid_key(nk): continue
                    br+=1
                    for labs in R.gvl(nk): R.FIXED_LABELS.add(R.slabels(labs))
                    tc=R.transition_choices(key,nk,pidx,ar,vb,True,True,True)
                    if tc is None: continue
                    aff,pf,pr,choices=tc; base=list(vb)
                    for comb in itertools.product(*choices):
                        vr=pr; vf=pf; tvb=base.copy()
                        for v,(bb,xf,xr) in zip(aff,comb): tvb[v]=bb; vf*=xf; vr*=xr
                        if abs(vr)<=1e-13: continue
                        high=R.canon_state_bytes(R.encode_state(nk,tuple(tvb))); nt=R.orbit_size_bytes(high)
                        val=float(R.A*math.sqrt(ns/nt)*vr*q)
                        acc[high]=acc.get(high,0.0)+val; oc+=1
                        if abs(vf)>1e-13: recip=max(recip,abs(abs(vf/vr)-1.0))
    keys=sorted(acc); K=np.frombuffer(b''.join(keys),dtype=np.uint8).reshape(-1,56).copy(); W=np.array([acc[k] for k in keys])
    meta={'schema':'GZYM_V199_C10_PINNED_INV_SHARD_V1','shard':a.shard,'nshards':a.nshards,'lo':lo,'hi':hi,'sources':hi-lo,'targets':len(keys),'branches':br,'outcomes':oc,'reciprocity_abs_ratio_minus_1':recip,'reducer_sha256':sha256(os.environ['V174_REDUCER']),'expected_inventory_sha256':EXPECTED_INV}
    np.savez_compressed(a.out,K=K,W=W,meta=np.array(json.dumps(meta)))
    print(json.dumps(meta,indent=2))

def merge(a):
    files=sorted(Path(a.shards).glob('v199_c10_*.npz')); assert len(files)==a.nshards
    acc={}; metas=[]
    for p in files:
        z=np.load(p,allow_pickle=False); m=json.loads(str(z['meta'].item())); metas.append(m)
        for row,w in zip(z['K'],z['W']):
            k=bytes(row.tolist()); acc[k]=acc.get(k,0.0)+float(w)
    metas.sort(key=lambda m:m['lo']); assert metas[0]['lo']==0 and metas[-1]['hi']==7576
    for x,y in zip(metas,metas[1:]): assert x['hi']==y['lo']
    W=np.array([acc[k] for k in sorted(acc)]); g=float(W@W); defect=abs(g-EXPECTED_G10)
    cert={'schema':'GZYM_V199_C10_PINNED_INVENTORY_GATE_V1','status':'PASS' if defect<=1e-8 else 'FAIL_CLOSED','G10':g,'expected':EXPECTED_G10,'abs_defect':defect,'tolerance':1e-8,'target_union':len(acc),'reducer_sha256':metas[0]['reducer_sha256'],'inventory_sha256':EXPECTED_INV,'shards':metas}
    Path(a.outdir).mkdir(parents=True,exist_ok=True); Path(a.outdir,'V199_C10_PINNED_INVENTORY_CERT.json').write_text(json.dumps(cert,indent=2)); print(json.dumps(cert,indent=2))
    if cert['status']!='PASS': raise SystemExit(2)

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('cross'); q.add_argument('--shard',type=int,required=True); q.add_argument('--nshards',type=int,default=8); q.add_argument('--out',required=True)
    q=s.add_parser('merge'); q.add_argument('--shards',required=True); q.add_argument('--nshards',type=int,default=8); q.add_argument('--outdir',required=True)
    a=p.parse_args(); cross(a) if a.cmd=='cross' else merge(a)
if __name__=='__main__': main()
