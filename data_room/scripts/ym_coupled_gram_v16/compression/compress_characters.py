"""Exact dimension-weighted SU(3) character truncation of V15 w233 squared.
Does not contract the coupled lattice or evaluate its Gram matrix.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, Context, ROUND_CEILING
import gzip,json,hashlib,sys,time
sys.set_int_max_str_digits(0)
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
CTX=Context(prec=40,rounding=ROUND_CEILING)
def upper(x):return str(CTX.divide(Decimal(x.numerator),Decimal(x.denominator)))
def dim(p,q):return (p+1)*(q+1)*(p+q+2)//2
def main():
 start=time.monotonic();path=ROOT/'spatial_gram_v15/SPATIAL_SQUARED_466.json.gz';path=path if path.exists() else OUT.parent/'inputs/SPATIAL_SQUARED_466.json.gz';raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()=='cc53bafa1eab11f6ca7db4f7b5d8d7a8c5ddbe30ee59af6cff9b38fb865c2a9c';source=json.loads(gzip.decompress(raw));den=int(source['common_denominator']);N=source['degree'];rows=[(r['p'],r['q'],int(r['numerator'])) for r in source['coefficients']]
 shell=[0]*(N+1)
 for p,q,c in rows:
  assert c>0
  shell[p+q]+=dim(p,q)*c
 tails=[0]*(N+1);running=0
 for k in range(N,-1,-1):tails[k]=running;running+=shell[k]
 records=[]
 for k in range(N+1):
  eps=Fraction(tails[k],den)
  if k in [0,4,8,12,16,20,24,28,32,36,40,48,56,64,80,96,128,160,233,292,466] or eps<Fraction(1,10**12) and (k==0 or Fraction(tails[k-1],den)>=Fraction(1,10**12)):
   item={'cutoff_p_plus_q':k,'irreps':(k+1)*(k+2)//2,'one_matrix_element_bond_dimension':sum(dim(p,q)**2 for p in range(k+1) for q in range(k+1-p)),'single_factor_absolute_error_upper':upper(eps),'single_factor_relative_error_upper':upper(eps),'positivity_certified':eps<1}
   if eps<1:
    item['all_24_factors_relative_error_upper']=upper((1+eps)**24-1)
    item['remaining_18_factors_relative_error_upper']=upper((1+eps)**18-1)
   records.append(item)
 targets=[]
 for target in [Fraction(1,10**6),Fraction(1,10**12),Fraction(1,10**20),Fraction(1,10**40),Fraction(1,10**100),Fraction(1,10**220)]:
  for k in range(N+1):
   eps=Fraction(tails[k],den)
   if eps<1 and (1+eps)**24-1<=target:break
  targets.append({'requested_all_24_relative_error':str(target),'minimal_cutoff':k,'irreps':(k+1)*(k+2)//2,'single_factor_error_exact':str(eps),'all_24_error_upper':upper((1+eps)**24-1),'remaining_18_error_upper':upper((1+eps)**18-1),'bond_dimension':sum(dim(p,q)**2 for p in range(k+1) for q in range(k+1-p))})
 k=next(t['minimal_cutoff'] for t in targets if t['requested_all_24_relative_error']=='1/1000000000000')
 selected=[{'p':p,'q':q,'numerator':str(c)} for p,q,c in rows if p+q<=k]
 artifact={'schema':'YM_SPATIAL_CHARACTER_COMPRESSION_V16','cutoff':k,'common_denominator':str(den),'coefficients':selected,'source_sha256':hashlib.sha256(raw).hexdigest(),'scope':'Truncated single plaquette squared polynomial; coupled Haar contractions not executed.'}
 payload=gzip.compress((json.dumps(artifact,separators=(',',':'))+'\n').encode(),mtime=0);(OUT/'COMPRESSED_SPATIAL_FACTOR.json.gz').write_bytes(payload)
 data={'schema':'YM_CHARACTER_COMPRESSION_CERTIFICATE_V16','source_sha256':hashlib.sha256(raw).hexdigest(),'source_degree':N,'source_coefficients':len(rows),'character_bound':'abs(chi_pq(U)) <= dim(p,q)','single_factor_minimum_proved':1,'normalization':'unscaled w233 squared, consistent with V15','scope':'Relative pointwise product and Loewner Gram approximation only; no integration execution','full_coupled_Gram_computed':False,'records':records,'targets':targets,'compressed_artifact_sha256':hashlib.sha256(payload).hexdigest(),'compressed_artifact_bytes':len(payload),'elapsed_seconds':time.monotonic()-start}
 (OUT/'CHARACTER_COMPRESSION_CERTIFICATE.json').write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps({'targets':[{z:t[z] for z in ['minimal_cutoff','irreps','all_24_error_upper','bond_dimension']} for t in targets],'compressed_bytes':len(payload)},indent=2))
if __name__=='__main__':main()
