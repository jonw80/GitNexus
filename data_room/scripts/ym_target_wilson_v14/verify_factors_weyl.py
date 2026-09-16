"""Independent Laurent-polynomial/Weyl extraction of every local coefficient."""
from pathlib import Path
from itertools import permutations
import gzip,json,math,hashlib,time
H=Path(__file__).resolve().parent
SHIFTS=[(1,0),(0,1),(-1,-1),(-1,0),(0,-1),(1,1)]
WEYL=[]
for perm in permutations((2,1,0)):
    # Vandermonde alternant with positive term (2,1,0).
    inv=sum(perm[i]<perm[j] for i in range(3) for j in range(i+1,3))
    WEYL.append((perm[0]-perm[2],perm[1]-perm[2],(-1)**inv))
def check(filename,a,b):
    source=H/filename;data=json.loads(gzip.decompress(source.read_bytes()))
    order=data['degree'];h={(0,0):1};den=1;start=time.monotonic()
    for k in range(order,0,-1):
        out={}
        for (x,y),v in h.items():
            z=a*v;out[x,y]=out.get((x,y),0)+3*z
            for dx,dy in SHIFTS:
                key=(x+dx,y+dy);out[key]=out.get(key,0)+z
        den*=b*k;out[0,0]+=den;h=out
        if (order-k+1)%75==0:print(f'{filename}: Laurent degree {order-k+1}/{order}',flush=True)
    assert den==int(data['common_denominator'])
    for row in data['coefficients']:
        p,q=row['p'],row['q'];x,y=p+q+2,q+1
        value=sum(sign*h.get((x-u,y-v),0) for u,v,sign in WEYL)
        assert value==int(row['numerator']),(p,q)
    return {'file':filename,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'rows_verified':len(data['coefficients']),'laurent_terms':len(h),
            'elapsed_seconds':time.monotonic()-start,'status':'PASS_ALL_COEFFICIENTS'}
def main():
    records=[]
    for f,a,b in [('SPATIAL_233_FACTOR.json.gz',271,240),('TEMPORAL_292_FACTOR.json.gz',271,120)]:
        r=check(f,a,b);records.append(r);print(json.dumps(r),flush=True)
    (H/'INDEPENDENT_WEYL_VERIFICATION.json').write_text(json.dumps({'status':'PASS_ALL_70566_COEFFICIENTS','method':'Full two-variable Laurent polynomial times Weyl alternant, without representation fusion','checks':records},indent=2)+'\n')
if __name__=='__main__':main()
