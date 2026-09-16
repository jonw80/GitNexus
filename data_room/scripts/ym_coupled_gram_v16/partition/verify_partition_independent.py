"""Independent scalar Radau audit; no generator imports.
Bisection of rational quadratics, distinct range-reduced exponential arithmetic.
The inherited Haar moments are inputs, not independently rederived here.
"""
from fractions import Fraction as F
from decimal import Decimal as D, Context, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
lo=Context(prec=145,rounding=ROUND_FLOOR)
hi=Context(prec=145,rounding=ROUND_CEILING)
def add(x,y): return x[0]+y[0],x[1]+y[1]
def mul(x,y):
 v=[a*b for a in x for b in y];return min(v),max(v)
def neg(x):return -x[1],-x[0]
def sub(x,y):return add(x,neg(y))
def div(x,y):
 assert y[0]*y[1]>0
 return mul(x,(1/y[1],1/y[0]))
def I(x):return F(x),F(x)
def decimal(x,up=False):return (hi if up else lo).divide(D(x.numerator),D(x.denominator))
def exp_interval(x):
 # 10 range-reduction squarings; 128 Taylor terms at y <= 1/2.
 assert 0<=x<=500
 y=x/1024;yl=decimal(y);yu=decimal(y,True)
 tl=tu=sl=su=D(1)
 for k in range(1,129):
  tl=lo.divide(lo.multiply(tl,yl),D(k)); sl=lo.add(sl,tl)
  tu=hi.divide(hi.multiply(tu,yu),D(k)); su=hi.add(su,tu)
 first=hi.divide(hi.multiply(tu,yu),D(129))
 denominator=lo.subtract(D(1),hi.divide(yu,D(130)))
 su=hi.add(su,hi.divide(first,denominator))
 for _ in range(10):sl=lo.multiply(sl,sl);su=hi.multiply(su,su)
 return sl,su
def root_bisection(b,c,left,right,increasing):
 def pol(x):return x*x+b*x+c
 left,right=F(left),F(right)
 assert (pol(left)<=0<=pol(right)) if increasing else (pol(left)>=0>=pol(right))
 for _ in range(430):
  mid=(left+right)/2; val=pol(mid)
  if (val<0)==increasing:left=mid
  else:right=mid
 return left,right
cert=json.loads((P/'ALL_24_VACUUM_GRAM_ENCLOSURE.json').read_text())
moment_source=P/'EXACT_SPATIAL_HAAR_MOMENTS.json'
if not moment_source.exists():moment_source=P.parents[1]/'recovered_v13/results/moments/EXACT_SPATIAL_HAAR_MOMENTS.json'
assert hashlib.sha256(moment_source.read_bytes()).hexdigest()==cert['source_moments_sha256']
assert json.loads(moment_source.read_text())['moments']==cert['moments']
m=list(map(F,cert['moments']));assert m==[F(1),F(0),F(12),F(6),F(3890,9)]
results={}
for key,edge in [('left_Radau',-36),('right_Radau',72)]:
 r=cert[key];c,b,lead=map(F,r['interior_polynomial']);assert lead==1
 # Exact orthogonality of (x-edge)(x²+b*x+c) to 1 and x.
 poly=[-edge*c,c-edge*b,b-edge,F(1)]
 for shift in [0,1]:assert sum(a*m[i+shift] for i,a in enumerate(poly))==0
 nodes=[I(edge),root_bisection(b,c,-5,0,False),root_bisection(b,c,0,6,True)]
 weights=[]
 for i in range(3):
  j,k=[j for j in range(3) if j!=i]
  # Integrate Lagrange cardinal polynomial using exact first three moments.
  numerator=add(sub(I(m[2]),mul(add(nodes[j],nodes[k]),I(m[1]))),mul(mul(nodes[j],nodes[k]),I(m[0])))
  denominator=mul(sub(nodes[i],nodes[j]),sub(nodes[i],nodes[k]))
  weights.append(div(numerator,denominator))
 for computed,published in zip(nodes,r['nodes']):assert F(published[0])<=computed[0]<=computed[1]<=F(published[1])
 for computed,published in zip(weights,r['weights']):assert 0<F(published[0])<=computed[0]<=computed[1]<=F(published[1])
 for degree in range(5):
  out=I(0)
  for node,weight in zip(nodes,weights):
   power=I(1)
   for _ in range(degree):power=mul(power,node)
   out=add(out,mul(weight,power))
  assert out[0]<=m[degree]<=out[1]
 qlo=qhi=D(0)
 for node,weight in zip(nodes,weights):
  y=add(I(F(813,5)),mul(I(F(271,60)),node))
  a=exp_interval(y[0])[0];bexp=exp_interval(y[1])[1]
  qlo=lo.add(qlo,lo.multiply(decimal(weight[0]),a))
  qhi=hi.add(qhi,hi.multiply(decimal(weight[1],True),bexp))
 assert D(r['quadrature_lower'])<=qlo<=qhi<=D(r['quadrature_upper'])
 results[key]={'quadrature_lower':str(qlo),'quadrature_upper':str(qhi),'orthogonality':True,'moments_0_through_4':True,'published_node_weight_intervals_contain_independent_intervals':True}
source=P/'TARGET_COUPLING_CERTIFICATE.json'
if not source.exists():source=P.parents[1]/'target_wilson_v14/TARGET_COUPLING_CERTIFICATE.json'
eps=F(json.loads(source.read_text())['spatial_relative_tail_upper']);factor=1-48*eps
assert factor>0
left=F(results['left_Radau']['quadrature_lower']);right=F(results['right_Radau']['quadrature_upper'])
assert F(cert['G00_lower'])<=factor*left
assert F(cert['G00_upper'])>=right
assert F(cert['enclosure_ratio_upper'])>=F(cert['G00_upper'])/F(cert['G00_lower'])
assert cert['full_spatial_Gram_computed'] is False and cert['precise_vacuum_integral_computed'] is False
out={'status':'PASS_INDEPENDENT_RADAU_SCALAR_AUDIT','independently_recomputed_haar_moments':False,'scope':'Conditional on supplied exact Haar moments; validates quadrature, outward arithmetic, polynomial-weight correction and scope flags. Not full Gram contraction.','checks':results,'hermite_remainder_sign':'positive f^(5); left endpoint gives lower, right endpoint upper'}
(P/'INDEPENDENT_PARTITION_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status'])
