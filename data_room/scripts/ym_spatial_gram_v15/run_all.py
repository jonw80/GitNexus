from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,Context,ROUND_CEILING
import subprocess,sys,json,gzip,hashlib
sys.set_int_max_str_digits(0)
H=Path(__file__).resolve().parent
def finalize():
    source=H/'SPATIAL_233_FACTOR.json.gz'
    if not source.exists():source=H.parent/'target_wilson_v14'/source.name
    c=json.loads(gzip.decompress(source.read_bytes()));den=int(c['common_denominator'])
    vmax=F(sum((r['p']+1)*(r['q']+1)*(r['p']+r['q']+2)//2*int(r['numerator']) for r in c['coefficients']),den)
    ctx=Context(prec=45,rounding=ROUND_CEILING)
    def upper(x):return str(ctx.divide(Decimal(x.numerator),Decimal(x.denominator)))
    bounds={'full_Gram_operator_lower':1,'full_Gram_operator_upper':upper(vmax**48),'principal_729_Loewner_lower':'L=K tensor power 6','principal_729_Loewner_upper_factor_times_L':upper(vmax**36),'scope':'Broad operator enclosures, not evaluated full Gram entries. Scalar shifts have been removed as in V14.'}
    (H/'FULL_GRAM_COARSE_ENCLOSURE.json').write_text(json.dumps(bounds,indent=2)+'\n')
    cert=json.loads((H/'GRAM_EXECUTION_V15.json').read_text());verify=json.loads((H/'INDEPENDENT_GRAM_VERIFICATION.json').read_text())
    assert not cert['full_spatial_Gram_computed']
    assert verify['status']=='PASS_ALL_531441_LOWER_ENTRIES_AND_EXACT_LDL'
    files=['SPATIAL_SQUARED_466.json.gz','EXACT_LOCAL_GRAM.json','GRAM_LOWER_729_CODES.bin.gz','GRAM_LOWER_729_VALUES.json','GEOMETRY_AND_DIMENSION.json','GRAM_EXECUTION_V15.json','INDEPENDENT_GRAM_VERIFICATION.json','FULL_GRAM_COARSE_ENCLOSURE.json']
    out={'status':'PASS_PARTIAL_CONTRACTIONS_FULL_GRAM_OPEN','files':[{'name':f,'bytes':(H/f).stat().st_size,'sha256':hashlib.sha256((H/f).read_bytes()).hexdigest()} for f in files],'full_spatial_Gram_computed':False}
    (H/'EXECUTION_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
def main():
    source=H.parent/'ym_target_wilson_v14'
    if source.exists():
        sys.path.insert(0,str(source));import build_factors
        build_factors.H=H;build_factors.build(233,F(271,240),'SPATIAL_233')
    for f in ['calculate_gram.py','verify_gram.py']:subprocess.run([sys.executable,str(H/f)],check=True,cwd=H)
    finalize()
if __name__=='__main__':main()
