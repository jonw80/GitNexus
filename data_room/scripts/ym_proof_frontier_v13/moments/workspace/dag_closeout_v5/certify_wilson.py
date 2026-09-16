"""Certify V135 Wilson coefficients, infinite tails, and all stored log columns.

No SciPy special function or determinant is used in the certificate.
The two beta interpretations are both retained; no silent convention change.
"""
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from itertools import permutations
from collections import Counter
import hashlib,json,math,struct,time,sys
import numpy as np
from intervals import I,D,UP,PREC,rational_record

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'full_moments_v4'
ORDER=[10,0,15,4,8,1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def bessel_factory(beta):
    t=I(beta)/6
    @lru_cache(None)
    def bes(n):
        # k=0,...,119, then a positive geometric majorant.
        term=t**n/math.factorial(n); value=term
        for k in range(1,120):
            term=term*t*t/(k*(n+k));value+=term
        first=term*t*t/(120*(n+120))
        ratio=t*t/(121*(n+121))
        assert ratio.hi<1
        tail=first/(1-ratio)
        return value+I(0,tail.hi)
    return t,bes

def determinant(m):
    total=I(0)
    for perm in permutations(range(3)):
        inversions=sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        term=I(-1 if inversions%2 else 1)
        for i,j in enumerate(perm):term*=m[i][j]
        total+=term
    return total

def wilson_table(beta,reps):
    t,bes=bessel_factory(beta)
    @lru_cache(None)
    def coeff(p,q):
        lam=(p+q,q,0);c=I(0)
        for s in range(-55,56):
            c+=determinant([[bes(abs(s+lam[i]-i+j)) for j in range(3)] for i in range(3)])
        # For |s|>=56 all orders >=m=56-(p+q+2).
        # I_(n+1)(2t)<=t/(n+1) I_n(2t), termwise in its positive series.
        m=56-(p+q+2);assert m>=0
        ratio=(t/(m+1))**3;assert ratio.hi<1
        tail=12*bes(m)**3/(1-ratio)
        return c+I(tail.hi.copy_negate(),tail.hi),tail
    c0,_=coeff(0,0);assert c0.lo>0
    out={}
    for p,q in sorted(reps):
        c,tail=coeff(p,q);d=(p+1)*(q+1)*(p+q+2)//2
        a=I(1) if (p,q)==(0,0) else c/(d*c0)
        assert a.lo>0
        loga=I(0) if (p,q)==(0,0) else a.log()
        out[16*p+q]={'rep':[p,q],'coefficient':a,'log':loga,'tail':tail,'c':c}
    return out,c0

def scan():
    """Outward ranges for every exact ratio Lhat_i/What_i, by link multiset.

    Ratios use IEEE binary64 division plus adjacent enclosing floats. Each
    source coordinate is visited; zero-W coordinates require zero L.
    """
    summaries=[]; reps=set();cohorts={};t=time.time()
    inputs=json.loads((ROOT/'inputs.json').read_text())
    for c in ORDER:
        p=ROOT/f'sources_{c}.bin'
        expected=next(x['output_sha256'] for x in inputs['sources'] if x['component']==c)
        assert sha(p)==expected
        data=p.read_bytes();assert data[:8]==b'YMFIBR04'
        count=struct.unpack_from('<I',data,8)[0];assert count==313682
        off=12;ncoord=nnonzero=0;groups={};nks=Counter()
        for j in range(count):
            key=data[off:off+24];nk=data[off+24];dims=data[off+25:off+33]
            sz=struct.unpack_from('<I',data,off+33)[0];assert sz==math.prod(dims)
            off+=37;w=np.frombuffer(data,'<f8',sz,off+8*sz);l=np.frombuffer(data,'<f8',sz,off+16*sz)
            assert np.isfinite(w).all() and np.isfinite(l).all()
            nz=w!=0;assert np.all(l[~nz]==0)
            if np.any(nz):
                ratio=l[nz]/w[nz];assert np.isfinite(ratio).all()
                lo=float(np.nextafter(ratio.min(),-np.inf));hi=float(np.nextafter(ratio.max(),np.inf))
                sig=bytes(sorted(key));old=groups.get(sig)
                groups[sig]=(min(old[0],lo),max(old[1],hi)) if old else (lo,hi)
            reps.update((r//16,r%16) for r in key)
            ncoord+=sz;nnonzero+=int(nz.sum());nks[nk]+=1;off+=24*sz
        assert off==len(data)
        summaries.append({'component':c,'fibers':count,'dense_coordinates':ncoord,'nonzero_W':nnonzero,'source_sha256':expected,'key_orbit_sizes':dict(nks),'signatures':len(groups)})
        cohorts[c]=groups
        print('SOURCE_SCANNED',c,count,len(groups),'seconds',round(time.time()-t,2),flush=True)
    return reps,summaries,cohorts

def propagate(table,cohorts,moments,beta):
    logs={}
    for sig in set().union(*(g.keys() for g in cohorts.values())):
        logs[sig]=sum((table[r]['log']*n for r,n in Counter(sig).items()),I(0))
    per=[];err=[]
    norm=moments['orthonormal_W_normalization']['matrices']
    a0=rational_record(moments['a']);a=I(beta)/3;da=(a-a0).abs_upper()
    for i,c in enumerate(ORDER):
        best=D(0);worst=None
        for sig,(lo,hi) in cohorts[c].items():
            e=(I(lo,hi)-logs[sig]).abs_upper()
            if e>best:best=e;worst=sig
        g=rational_record(moments['primitive_exact_moments']['W_W_upper'][i][i])
        n=rational_record(moments['N'][i][i])
        el=I(best)*g.sqrt();eta=I(best)+I(da)*(n/g).sqrt();err.append(eta)
        per.append({'component':c,'max_log_multiplier_error_upper':str(best),'log_column_error_norm_upper':str(el.hi),'normalized_affine_column_error_upper':str(eta.hi),'worst_signature':[[r//16,r%16,k] for r,k in sorted(Counter(worst).items())]})
    mats={};radius={};checks={}
    for name in ['A','M2','BstarB']:
        m=[];rr=[]
        for i in range(6):
            row=[];rrow=[]
            for j in range(6):
                old=rational_record(norm[name][i][j])
                if name=='A':rad=err[j]
                else:
                    ni=rational_record(norm[name][i][i]).sqrt();nj=rational_record(norm[name][j][j]).sqrt()
                    rad=ni*err[j]+nj*err[i]+err[i]*err[j]
                row.append((old+I(rad.hi.copy_negate(),rad.hi)).record());rrow.append(str(rad.hi))
            m.append(row);rr.append(rrow)
        mats[name]=m;radius[name]=rr
        if name!='A':
            floors=[]
            for i in range(6):
                val=I(m[i][i]['lower'])
                for j in range(6):
                    if i!=j:val-=max(D(m[i][j]['lower']).copy_abs(),D(m[i][j]['upper']).copy_abs())
                floors.append(val.lo)
            checks[name]={'gershgorin_lower':str(min(floors)),'positive':min(floors)>0}
    return {'exact_beta':str(beta),'a_minus_stored_a_absolute_upper':str(da),'columns':per,'enclosed_matrices':mats,'entry_error_radius_upper':radius,'checks':checks,'scope':'Exact Wilson logarithms applied to stored dyadic W; stored dyadic X held fixed. BstarB uses orthonormal W and the residual Gram. CG, crossing and plaquette action errors remain outside this certificate.'}

def run():
    reps,summaries,cohorts=scan()
    # Cover all local-kernel labels too, beyond those present in W.
    req=np.frombuffer((ROOT/'requests.bin').read_bytes(),np.uint8,offset=4).reshape(-1,42)
    reps.update((int(r)//16,int(r)%16) for r in req[:,24:36].ravel())
    moments=json.loads((ROOT/'FULL_MATRICES.json').read_text());assert moments['components']==ORDER
    regimes={}
    for name,beta in [('decimal_13_55',F(271,20)),('binary64_13_55',F(13.55))]:
        table,c0=wilson_table(beta,reps)
        r=propagate(table,cohorts,moments,beta)
        r.update({'vacuum_coefficient':c0.record(),'representations':[{'rep':x['rep'],'coefficient':x['coefficient'].record(),'log':x['log'].record(),'unnormalized_shift_tail_absolute_upper':str(x['tail'].hi)} for x in table.values()]})
        regimes[name]=r
        print('WILSON_CERTIFIED',name,len(table),'max log error',max(D(x['max_log_multiplier_error_upper']) for x in r['columns']),flush=True)
    out={'schema':'YM_WILSON_LOG_OUTWARD_V5','status':'PASS_FOR_DECLARED_ERROR_FAMILY','precision_decimal_digits':PREC,'bessel_terms':120,'shift_range':[-55,55],'components':ORDER,'source_scan':summaries,'regimes':regimes,'input_moments_sha256':sha(ROOT/'FULL_MATRICES.json'),'source_hashes':{p.name:sha(p) for p in [HERE/'intervals.py',Path(__file__)]},'physical_operator_outward_certificate':False,'continuum_certificate':False}
    write(HERE/'WILSON_LOG_CERTIFICATE.json',out)
    write(HERE/'LOG_RATIO_COHORTS.json',{'components':{str(c):[{'signature':list(sig),'exact_ratio_enclosure_binary64':[lo,hi]} for sig,(lo,hi) in sorted(g.items())] for c,g in cohorts.items()}})

if __name__=='__main__':run()
