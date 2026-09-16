"""All-24-plaquette vacuum Gram enclosure from exact coupled Haar moments.

Radau envelopes enclose the integral at the target coupling. This is a broad
scalar enclosure, not a full Gram matrix evaluation or a tensor contraction.
"""
from fractions import Fraction as F
from decimal import Decimal,Context,ROUND_FLOOR,ROUND_CEILING
from pathlib import Path
import hashlib,json,math
H=Path(__file__).resolve().parent
LO=Context(prec=90,rounding=ROUND_FLOOR);UP=Context(prec=90,rounding=ROUND_CEILING)
def cv(x,up=False):
    return (UP if up else LO).divide(Decimal(x.numerator),Decimal(x.denominator))
def iv(x):return (F(x),F(x))
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def neg(a):return (-a[1],-a[0])
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    v=[x*y for x in a for y in b];return min(v),max(v)
def div(a,b):
    assert not b[0]<=0<=b[1]
    return mul(a,(1/b[1],1/b[0]))
def sqrt_iv(x):
    z=10**110;k=math.isqrt(x.numerator*z*z//x.denominator)
    return F(k,z),F(k+1,z)
def exp_decimal(x,upper):
    ctx=UP if upper else LO;x=cv(x,upper);assert x>=0
    term=total=Decimal(1)
    for k in range(1,1601):
        term=ctx.divide(ctx.multiply(term,x),Decimal(k));total=ctx.add(total,term)
    if upper:
        ratio=UP.divide(x,Decimal(1602))
        first=UP.divide(UP.multiply(term,x),Decimal(1601))
        denom=LO.subtract(Decimal(1),ratio);assert denom>0
        total=UP.add(total,UP.divide(first,denom))
    return total
def ratout(a):return [str(cv(a[0])),str(cv(a[1],True))]
def radau(endpoint,moments):
    z=F(endpoint);m0,m1,m2,m3,m4=moments
    aa=m2-z*m1;bb=m1-z*m0;cc=m3-z*m2;dd=m2-z*m1
    e=-(m3-z*m2);f=-(m4-z*m3);det=aa*dd-bb*cc
    b=(e*dd-bb*f)/det;c=(aa*f-e*cc)/det
    disc=b*b-4*c;assert disc>0;root=sqrt_iv(disc)
    nodes=[iv(z),div(sub(iv(-b),root),iv(2)),div(add(iv(-b),root),iv(2))]
    weights=[]
    for i in range(3):
        j,k=[q for q in range(3) if q!=i]
        num=add(sub(iv(m2),mul(add(nodes[j],nodes[k]),iv(m1))),mul(mul(nodes[j],nodes[k]),iv(m0)))
        den=mul(sub(nodes[i],nodes[j]),sub(nodes[i],nodes[k]))
        w=div(num,den);assert w[0]>0;weights.append(w)
    assert all(F(-36)<=x[0]<=x[1]<=F(72) for x in nodes)
    # Exact polynomial orthogonality underlying Radau degree-four exactness.
    assert m3+(b-z)*m2+(c-z*b)*m1-z*c*m0==0
    assert m4+(b-z)*m3+(c-z*b)*m2-z*c*m1==0
    # Independently enclose each reproduced moment.
    for p,mu in enumerate(moments):
        total=iv(0)
        for x,w in zip(nodes,weights):
            xp=iv(1)
            for _ in range(p):xp=mul(xp,x)
            total=add(total,mul(w,xp))
        assert total[0]<=mu<=total[1]
    lower=Decimal(0);upper=Decimal(0)
    for x,w in zip(nodes,weights):
        y=add(iv(F(813,5)),mul(iv(F(271,60)),x))
        lower=LO.add(lower,LO.multiply(cv(w[0]),exp_decimal(y[0],False)))
        upper=UP.add(upper,UP.multiply(cv(w[1],True),exp_decimal(y[1],True)))
    return {'endpoint':str(z),'interior_polynomial':[str(c),str(b),'1'],'nodes':[ratout(x) for x in nodes],'weights':[ratout(x) for x in weights],'quadrature_lower':str(lower),'quadrature_upper':str(upper)}
def main():
    source=H/'EXACT_SPATIAL_HAAR_MOMENTS.json'
    if not source.exists():source=H.parents[1]/'recovered_v13/results/moments/EXACT_SPATIAL_HAAR_MOMENTS.json'
    inp=json.loads(source.read_text());moments=list(map(F,inp['moments']));assert moments==list(map(F,['1','0','12','6','3890/9']))
    left=radau(-36,moments);right=radau(72,moments)
    cert=H/'TARGET_COUPLING_CERTIFICATE.json'
    if not cert.exists():cert=H.parents[1]/'target_wilson_v14/TARGET_COUPLING_CERTIFICATE.json'
    eps=F(json.loads(cert.read_text())['spatial_relative_tail_upper'])
    relative=1-48*eps;assert relative>0
    low=LO.multiply(cv(relative),Decimal(left['quadrature_lower']));high=Decimal(right['quadrature_upper'])
    assert low>0 and high>low
    # All 24 factors retained via D=sum_p ReTr U_p, not a six-loop product.
    out={'status':'CERTIFIED_BROAD_ALL_24_VACUUM_GRAM_ENCLOSURE','source_moments_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'moments':[str(x) for x in moments],'target_beta':'271/20','target_t':'271/60','plaquettes_included':24,'spatial_degree':233,'left_Radau':left,'right_Radau':right,'G00_lower':str(low),'G00_upper':str(high),'enclosure_ratio_upper':str(UP.divide(high,low)),'normalization':'G=E292* W^2 E292, constant basis vector; scalar shifts removed as V14','full_spatial_Gram_computed':False,'precise_vacuum_integral_computed':False,'scope':'Global correlated integral enclosure using inherited exact coupled moments through degree four. No plaquette factors omitted; no high-precision contraction claimed.'}
    (H/'ALL_24_VACUUM_GRAM_ENCLOSURE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
