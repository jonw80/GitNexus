"""Exact spatial Gram factors and a 729-state Loewner lower bound.

This does NOT contract the full 24-plaquette Gram matrix.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, Context, ROUND_CEILING, ROUND_FLOOR
from itertools import product
import gzip, hashlib, json, math, sys, time
sys.set_int_max_str_digits(0)
H=Path(__file__).resolve().parent
UP=Context(prec=45,rounding=ROUND_CEILING)
DOWN=Context(prec=45,rounding=ROUND_FLOOR)
def dec(x,up=True):
    return str((UP if up else DOWN).divide(Decimal(x.numerator),Decimal(x.denominator)))
def dim(p,q):return (p+1)*(q+1)*(p+q+2)//2
def fuse(h,kind='both'):
    out={}
    for (p,q),v in h.items():
        dest=[]
        if kind=='both':dest.append(((p,q),3))
        if kind in ['both','fund']:
            dest.append(((p+1,q),1))
            if p:dest.append(((p-1,q+1),1))
            if q:dest.append(((p,q-1),1))
        if kind in ['both','anti']:
            dest.append(((p,q+1),1))
            if q:dest.append(((p+1,q-1),1))
            if p:dest.append(((p-1,q),1))
        for r,w in dest:out[r]=out.get(r,0)+w*v
    return out
def write(name,data):
    (H/name).write_text(json.dumps(data,indent=2)+'\n')
def geometry():
    vs=list(product(range(2),repeat=3));edges=[(x,m) for x in vs for m in range(3)]
    idx={e:i for i,e in enumerate(edges)};ps=[]
    def shift(x,m):y=list(x);y[m]^=1;return tuple(y)
    for x in vs:
        for m in range(3):
            for n in range(m+1,3):
                ps.append([(idx[x,m],1),(idx[shift(x,m),n],1),(idx[shift(x,n),m],-1),(idx[x,n],-1)])
    sets=[set(e for e,s in p) for p in ps]
    assert len(ps)==24 and all(len(s)==4 for s in sets)
    def cover(remaining,chosen):
        if not remaining:return chosen
        first=min(remaining)
        for i,s in enumerate(sets):
            if first in s and s<=remaining:
                z=cover(remaining-s,chosen+[i])
                if z is not None:return z
    selected=cover(set(range(24)),[]);assert len(selected)==6
    return edges,ps,selected
def sqrt_iv(x,digits=100):
    scale=10**digits;k=math.isqrt(x.numerator*scale*scale//x.denominator)
    lo=F(k,scale);hi=F(k+1,scale)
    assert lo*lo<=x<=hi*hi
    return lo,hi
def main():
    start=time.monotonic();source=H.parent/'target_wilson_v14'/'SPATIAL_233_FACTOR.json.gz'
    if not source.exists():source=H/'SPATIAL_233_FACTOR.json.gz'
    raw=source.read_bytes();expected='f97793054f201684dcc983353dd33dbd924807d2351cadad0880beff402b44a7'
    assert hashlib.sha256(raw).hexdigest()==expected
    original=json.loads(gzip.decompress(raw));a0={(r['p'],r['q']):int(r['numerator']) for r in original['coefficients']};den0=int(original['common_denominator'])
    m=233;N=2*m;aa,bb=271,240
    sums=[sum(math.comb(k,j) for j in range(max(0,k-m),min(k,m)+1)) for k in range(N+1)]
    numer={(0,0):sums[N]};den=1
    for k in range(N,0,-1):
        numer={r:aa*v for r,v in fuse(numer).items()}
        den*=bb*k;numer[(0,0)]+=sums[k-1]*den
        if k%50==0:print('square recurrence remaining',k,'terms',len(numer),flush=True)
    assert den==math.factorial(N)*bb**N
    assert len(numer)==(N+1)*(N+2)//2
    assert all(v>0 and numer[q,p]==v for (p,q),v in numer.items())
    identity=sum(dim(p,q)*v for (p,q),v in numer.items())
    identity0=sum(dim(p,q)*v for (p,q),v in a0.items())
    assert F(identity,den)==F(identity0,den0)**2
    # Independent multiplication of the original factor by each test character.
    vectors=[a0,fuse(a0,'fund'),fuse(a0,'anti')]
    gram=[[F(sum(v*w.get(r,0) for r,v in z.items()),den0**2) for w in vectors] for z in vectors]
    a,b,d,e=[F(numer[r],den) for r in [(0,0),(1,0),(1,1),(2,0)]]
    d+=a;e+=b
    assert gram==[[a,b,b],[b,d,e],[b,e,d]]
    assert a*d>b*b and (d-e)*(a*(d+e)-2*b*b)>0
    poly={'schema':'YM_SQUARED_SPATIAL_CHARACTER_FACTOR_V15','degree':N,'source_sha256':expected,'common_denominator':str(den),'coefficients':[{'p':p,'q':q,'numerator':str(numer[p,q])} for p,q in sorted(numer)],'scope':'One plaquette w squared; full spatial product not contracted.'}
    factor=H/'SPATIAL_SQUARED_466.json.gz';factor.write_bytes(gzip.compress((json.dumps(poly,separators=(',',':'))+'\n').encode(),mtime=0))
    edges,ps,selected=geometry();rank=((293*294)//2)**6
    write('GEOMETRY_AND_DIMENSION.json',{'edges':edges,'plaquettes':ps,'six_edge_disjoint_plaquette_ids':selected,'retained_cutoff':292,'irreps_per_loop':43071,'full_rank_lower_bound':rank,'neutral_zero_momentum_rank_lower_bound':(rank+7)//8,'dense_real_float64_bytes_lower_bound':8*rank*rank})
    # Exact compact encoding of all 729 by 729 entries of the LOWER operator.
    unit=[F(1),b/a,d/a,e/a];counts=list(t for t in product(range(7),repeat=4) if sum(t)==6);lookup={t:i for i,t in enumerate(counts)}
    values=[math.prod(unit[i]**t[i] for i in range(4)) for t in counts]
    words=list(product(range(3),repeat=6));types=[[0,1,1],[1,2,3],[1,3,2]];indices=bytearray()
    for u in words:
        for v in words:
            c=[0]*4
            for x,y in zip(u,v):c[types[x][y]]+=1
            indices.append(lookup[tuple(c)])
    assert len(indices)==729**2
    packed=H/'GRAM_LOWER_729_CODES.bin.gz';packed.write_bytes(gzip.compress(bytes(indices),mtime=0))
    for i in range(729):
        for j in range(i):assert indices[i*729+j]==indices[j*729+i]
    write('GRAM_LOWER_729_VALUES.json',{'status':'EXACT_SIX_PLAQUETTE_LOWER_OPERATOR_ONLY','shape':[729,729],'basis':'lexicographic product of [1,chi_3,chi_3bar] over the six listed plaquettes','normalization':'divide lower operator and full principal Gram by a^6, a=integral(w^2)','scale_a':str(a),'entry_codes_file':packed.name,'values':[{'counts':c,'exact':str(v),'lower':dec(v,False),'upper':dec(v)} for c,v in zip(counts,values)],'full_24_plaquette_principal_Gram_computed':False})
    trace=1+(d+e)/a;dis=(1-(d+e)/a)**2+8*(b/a)**2;sl,sh=sqrt_iv(dis)
    ivs=[((trace-sh)/2,(trace-sl)/2),((d-e)/a,(d-e)/a),((trace+sl)/2,(trace+sh)/2)]
    assert all(lo>0 for lo,hi in ivs)
    lamlo=min(lo for lo,hi in ivs);lamhi=max(hi for lo,hi in ivs)
    local={'basis':['1','chi_3','chi_3bar'],'exact':[[str(x) for x in row] for row in gram],'normalized_entry_intervals':[[[dec(x/a,False),dec(x/a)] for x in row] for row in gram],'normalized_eigenvalue_intervals':[[dec(lo,False),dec(hi)] for lo,hi in ivs],'lower_729_smallest_eigenvalue_lower':dec(lamlo**6,False),'lower_729_largest_eigenvalue_upper':dec(lamhi**6),'lower_729_condition_number_upper':dec((lamhi/lamlo)**6),'vacuum_full_Gram_entry_lower':dec(a**6,False)}
    write('EXACT_LOCAL_GRAM.json',local)
    summary={'status':'PASS_EXACT_LOCAL_GRAM_AND_729_LOWER_BOUND','squared_factor_coefficients':len(numer),'lower_operator_shape':[729,729],'entry_value_classes':len(values),'independent_checks':['original coefficient Parseval and three character-multiplied vectors match all nine Gram entries','dimension evaluation at identity','exact conjugation','exact positive principal minors','six loops partition all 24 links','all 531441 code entries generated; symmetry checked'],'elapsed_seconds':time.monotonic()-start,'full_spatial_Gram_computed':False,'full_principal_729_Gram_computed':False,'volume_uniform_gap_proved':False,'continuum_proved':False,'source_factor_sha256':expected,'squared_factor_sha256':hashlib.sha256(factor.read_bytes()).hexdigest(),'entry_codes_sha256':hashlib.sha256(packed.read_bytes()).hexdigest()}
    write('GRAM_EXECUTION_V15.json',summary);print(json.dumps(summary,indent=2),flush=True);print(json.dumps({k:v for k,v in local.items() if k!='exact'},indent=2),flush=True)
if __name__=='__main__':main()
