"""Independent direct-row verification (no degree-shell accumulation)."""
from pathlib import Path
from fractions import Fraction as F
import gzip,json,hashlib,sys
sys.set_int_max_str_digits(0)
P=Path(__file__).resolve().parent
src=P.parents[1]/'spatial_gram_v15/SPATIAL_SQUARED_466.json.gz'
src=src if src.exists() else P.parent/'inputs/SPATIAL_SQUARED_466.json.gz'
raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()=='cc53bafa1eab11f6ca7db4f7b5d8d7a8c5ddbe30ee59af6cff9b38fb865c2a9c';a=json.loads(gzip.decompress(raw));c=json.loads((P/'CHARACTER_COMPRESSION_CERTIFICATE.json').read_text());d=int(a['common_denominator'])
assert hashlib.sha256(raw).hexdigest()==c['source_sha256']
rows={(r['p'],r['q']):int(r['numerator']) for r in a['coefficients']}
def dim(p,q):return (p+1)*(q+1)*(p+q+2)//2
def tail(k):return F(sum(v*dim(p,q) for (p,q),v in rows.items() if p+q>k),d)
for t in c['targets']:
 k=t['minimal_cutoff'];e=tail(k);assert e==F(t['single_factor_error_exact'])
 assert (1+e)**24-1<=F(t['requested_all_24_relative_error'])
 assert (1+tail(k-1))**24-1>F(t['requested_all_24_relative_error'])
 assert (1+e)**24-1<=F(t['all_24_error_upper'])
 assert (1+e)**18-1<=F(t['remaining_18_error_upper'])
 assert t['bond_dimension']==sum(dim(p,q)**2 for p,q in rows if p+q<=k)
payload=(P/'COMPRESSED_SPATIAL_FACTOR.json.gz').read_bytes();b=json.loads(gzip.decompress(payload));br={(r['p'],r['q']):int(r['numerator']) for r in b['coefficients']}
assert b['common_denominator']==a['common_denominator']
assert br=={r:v for r,v in rows.items() if sum(r)<=b['cutoff']}
assert all(br[p,q]==br[q,p] for p,q in br)
assert hashlib.sha256(payload).hexdigest()==c['compressed_artifact_sha256']
result={'status':'PASS_DIRECT_SUM_INDEPENDENT_COMPRESSION_CHECK','target_cutoffs_checked':len(c['targets']),'all_minimal_cutoffs_confirmed':True,'compressed_coefficients':len(br),'all_compressed_rows_match_source':True,'full_coupled_integration_executed':False}
(P/'INDEPENDENT_COMPRESSION_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
