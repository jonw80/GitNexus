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

def assess_crossing(r2, w2):
    """The reverse reference check alone is not the crossing gate."""
    finite = math.isfinite(r2) and math.isfinite(w2) and r2 >= 0 and w2 >= 0
    gd = abs(r2-w2) if finite else None
    ge = abs(r2-EXPECTED_G10) if finite else None
    passed = finite and gd <= 1e-8 and ge <= 1e-6
    return {'status':'PASS' if passed else 'FAIL_CLOSED',
            'R2':r2 if math.isfinite(r2) else None,
            'W2':w2 if math.isfinite(w2) else None,
            'expected_G10':EXPECTED_G10,
            'gram_abs_diff':gd,'gram_tolerance':1e-8,
            'expected_abs_diff':ge,'reference_tolerance':1e-6,
            'finite_nonnegative':finite,
            'reverse_reference_abs_diff':abs(w2-EXPECTED_G10) if math.isfinite(w2) else None,
            'external_norm_authorized':bool(passed)}

def check_coverage(metas, nshards):
    if len(metas) != nshards or {m['shard'] for m in metas} != set(range(nshards)):
        raise ValueError('missing or duplicate shard identity')
    cursor=0
    for m in sorted(metas,key=lambda m:m['lo']):
        if m['nshards'] != nshards or m['lo'] != cursor or m['hi'] <= m['lo']:
            raise ValueError('incomplete or overlapping source coverage')
        if m['sources'] != m['hi']-m['lo']:
            raise ValueError('source count disagrees with range')
        cursor=m['hi']
    if cursor != 7576:
        raise ValueError('source coverage does not end at 7576')

def cross(a):
    import scipy.sparse as sp
    R=load_R(); low=R.low_states; psi=np.asarray(R.psi,float)
    if len(low)!=7576 or psi.shape!=(7576,) or not np.isfinite(psi).all():
        raise ValueError('invalid component-10 input')
    if a.nshards<=0 or not 0<=a.shard<a.nshards:
        raise ValueError('invalid shard')
    C,outside=R.low_raw_C()
    phase,ncc,contr,eigres,logc=R.recover_phase(C)
    H=(R.A*(C@sp.diags(phase.astype(float)))+sp.diags(logc)).tocsr()
    asym=(H-H.T).tocoo()
    sym=float(np.abs(asym.data).max()) if asym.nnz else 0.0
    if ncc!=1 or contr!=0 or not math.isfinite(sym) or sym>1e-8:
        raise ValueError(('phase gate failed',ncc,contr,sym))
    phase_sha=hashlib.sha256(np.asarray(phase,dtype=np.int8).tobytes()).hexdigest()
    input_sha=sha256(Path(os.environ['V174_INPUT'])/'component10.npz')
    lo=len(low)*a.shard//a.nshards; hi=len(low)*(a.shard+1)//a.nshards
    accR={}; accW={}; br=oc=0; recip=0.0
    for i in range(lo,hi):
        key,vb=low[i]; raw=R.encode_state(key,vb); ns=R.orbit_size_bytes(raw); q=float(psi[i])
        for pidx in range(24):
            for ar in (1,-1):
                for nk in R.branches(key,pidx,ar):
                    if R.degree(nk)<10 or not R.valid_key(nk): continue
                    br+=1
                    for labs in R.gvl(nk): R.FIXED_LABELS.add(R.slabels(labs))
                    tc=R.transition_choices(key,nk,pidx,ar,vb,True,True,True)
                    if tc is None: continue
                    aff,pf,pr,choices=tc; base=list(vb)
                    for comb in itertools.product(*choices):
                        vr=pr; vf=pf; tvb=base.copy()
                        for v,(bb,xf,xr) in zip(aff,comb): tvb[v]=bb; vf*=xf; vr*=xr
                        if abs(vf)<=1e-13 and abs(vr)<=1e-13: continue
                        high=R.canon_state_bytes(R.encode_state(nk,tuple(tvb))); nt=R.orbit_size_bytes(high)
                        fac=R.A*math.sqrt(ns/nt)*q
                        if abs(vf)>1e-13: accR[high]=accR.get(high,0.0)+fac*vf*int(phase[i])
                        if abs(vr)>1e-13: accW[high]=accW.get(high,0.0)+fac*vr
                        oc+=1
                        if abs(vf)>1e-13 and abs(vr)>1e-13:
                            recip=max(recip,abs(abs(vf/vr)-1.0))
    keys=sorted(set(accR)|set(accW))
    K=np.frombuffer(b''.join(keys),dtype=np.uint8).reshape(-1,56).copy()
    F=np.array([accR.get(k,0.) for k in keys]); W=np.array([accW.get(k,0.) for k in keys])
    meta={'schema':'GZYM_C10_TWO_DIRECTION_SHARD_V2','shard':a.shard,'nshards':a.nshards,
          'lo':lo,'hi':hi,'sources':hi-lo,'targets':len(keys),'branches':br,'outcomes':oc,
          'reciprocity_abs_ratio_minus_1':recip,'reducer_sha256':sha256(os.environ['V174_REDUCER']),
          'expected_inventory_sha256':EXPECTED_INV,'input_sha256':input_sha,'phase_sha256':phase_sha,
          'phase_gate':{'ncc':int(ncc),'contr':int(contr),'symmetry':sym}}
    np.savez_compressed(a.out,K=K,R=F,W=W,meta=np.array(json.dumps(meta)))
    print(json.dumps(meta,indent=2))

def merge(a):
    files=sorted(Path(a.shards).glob('v199_c10_*.npz'))
    if len(files)!=a.nshards: raise ValueError('shard file count mismatch')
    accR={}; accW={}; metas=[]
    for p in files:
        with np.load(p,allow_pickle=False) as z:
            if not {'K','R','W','meta'}.issubset(z.files):
                raise ValueError('both independently computed directions are required')
            m=json.loads(str(z['meta'].item())); metas.append(m)
            K,F,W=z['K'],z['R'],z['W']
            if K.dtype!=np.uint8 or K.shape!=(len(F),56) or W.shape!=F.shape or F.ndim!=1:
                raise ValueError('invalid shard coordinate shape or dtype')
            if not np.isfinite(F).all() or not np.isfinite(W).all():
                raise ValueError('non-finite crossing amplitudes')
            keys=[row.tobytes() for row in K]
            if keys!=sorted(set(keys)): raise ValueError('duplicate or unsorted target coordinate')
            if m['schema']!='GZYM_C10_TWO_DIRECTION_SHARD_V2':
                raise ValueError('unrecognized two-direction shard schema')
            if m['reducer_sha256']!=EXPECTED_REDUCER or m['expected_inventory_sha256']!=EXPECTED_INV:
                raise ValueError('pinned custody mismatch')
            pg=m['phase_gate']
            if pg['ncc']!=1 or pg['contr']!=0 or not math.isfinite(pg['symmetry']) or pg['symmetry']>1e-8:
                raise ValueError('invalid phase certificate')
            for k,f,w in zip(keys,F,W):
                accR[k]=accR.get(k,0.0)+float(f); accW[k]=accW.get(k,0.0)+float(w)
    check_coverage(metas,a.nshards)
    for field in ('input_sha256','phase_sha256'):
        if len({m[field] for m in metas})!=1: raise ValueError('incompatible shard '+field)
    keys=sorted(set(accR)|set(accW))
    F=np.array([accR.get(k,0.) for k in keys]); W=np.array([accW.get(k,0.) for k in keys])
    r2=math.fsum(float(x)*float(x) for x in F); w2=math.fsum(float(x)*float(x) for x in W)
    cert=assess_crossing(r2,w2)
    cert.update({'schema':'GZYM_C10_TWO_DIRECTION_CROSSING_GATE_V2','target_union':len(keys),
                 'reducer_sha256':EXPECTED_REDUCER,'inventory_sha256':EXPECTED_INV,
                 'shards':sorted(metas,key=lambda m:m['lo']),
                 'arithmetic_scope':'binary64 diagnostic; not an outward operator certificate'})
    Path(a.outdir).mkdir(parents=True,exist_ok=True)
    K=np.frombuffer(b''.join(keys),dtype=np.uint8).reshape(-1,56).copy()
    np.savez_compressed(Path(a.outdir)/'crossing_component10.npz',states56=K,R=F,W=W)
    Path(a.outdir,'V199_C10_PINNED_INVENTORY_CERT.json').write_text(json.dumps(cert,indent=2,allow_nan=False))
    print(json.dumps(cert,indent=2,allow_nan=False))
    if cert['status']!='PASS': raise SystemExit(2)

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('cross'); q.add_argument('--shard',type=int,required=True); q.add_argument('--nshards',type=int,default=8); q.add_argument('--out',required=True)
    q=s.add_parser('merge'); q.add_argument('--shards',required=True); q.add_argument('--nshards',type=int,default=8); q.add_argument('--outdir',required=True)
    a=p.parse_args(); cross(a) if a.cmd=='cross' else merge(a)
if __name__=='__main__': main()
