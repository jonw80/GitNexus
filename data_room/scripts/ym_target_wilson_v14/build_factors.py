"""Full exact character expansions of both target-coupling local factors.

Each numerator and the shared denominator are integers. No spatial Gram
contraction or numerical Perron eigenvector is claimed by this generator.
"""
from pathlib import Path
from fractions import Fraction as F
import gzip,json,math,time,hashlib
H=Path(__file__).resolve().parent
def dim(p,q):return (p+1)*(q+1)*(p+q+2)//2
def fuse(h):
    out={}
    for (p,q),v in h.items():
        for r,w in [((p,q),3),((p+1,q),1),((p,q+1),1)]:out[r]=out.get(r,0)+w*v
        if p:
            for r in [(p-1,q+1),(p-1,q)]:out[r]=out.get(r,0)+v
        if q:
            for r in [(p+1,q-1),(p,q-1)]:out[r]=out.get(r,0)+v
    return out
def build(order,gamma,label):
    numer={(0,0):1};den=1
    for k in range(order,0,-1):
        numer={r:gamma.numerator*v for r,v in fuse(numer).items()}
        den*=gamma.denominator*k;numer[(0,0)]+=den
    assert den==math.factorial(order)*gamma.denominator**order
    assert len(numer)==(order+1)*(order+2)//2
    assert all(v>0 and numer[q,p]==v for (p,q),v in numer.items())
    assert all(p+q<=order for p,q in numer)
    assert numer[order,0]==gamma.numerator**order
    x=9*gamma;t=s=F(1)
    for k in range(1,order+1):t*=x/k;s+=t
    assert F(sum(dim(p,q)*v for (p,q),v in numer.items()),den)==s
    data={'schema':'YM_SHIFTED_POSITIVE_CHARACTER_FACTOR_V14','kind':label,
          'argument':str(gamma)+'*(3+chi_3+chi_3bar)','degree':order,
          'common_denominator':str(den),
          'coefficients':[{'p':p,'q':q,'numerator':str(numer[p,q])} for p,q in sorted(numer)],
          'scope':'Complete local character factor, not a spatial matrix or continuum proof.'}
    raw=(json.dumps(data,separators=(',',':'))+'\n').encode()
    p=H/(label+'_FACTOR.json.gz');p.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
    reopened=json.loads(gzip.decompress(p.read_bytes()));assert reopened==data
    return {'file':p.name,'degree':order,'representations':len(numer),
            'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'checks':['all support entries present','positive integer numerators','exact charge conjugation','exact dimension evaluation','highest weight coefficient','gzip round trip']}
def main():
    c=json.loads((H/'TARGET_COUPLING_CERTIFICATE.json').read_text());start=time.monotonic()
    rows=[]
    for n,g,label in [(c['spatial_degree'],F(271,240),'SPATIAL_233'),(c['temporal_degree'],F(271,120),'TEMPORAL_292')]:
        row=build(n,g,label);rows.append(row);print(json.dumps(row),flush=True)
    out={'status':'PASS_COMPLETE_LOCAL_FACTORS','elapsed_seconds':time.monotonic()-start,
         'factors':rows,'total_representations':sum(r['representations'] for r in rows),
         'full_spatial_Gram_computed':False,'full_target_matrices_computed':False,
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (H/'FACTOR_EXECUTION.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
