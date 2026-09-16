"""Independent checks of the stored local Gram and every lower-matrix code."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import gzip,json,math,hashlib,sys
sys.set_int_max_str_digits(0)
H=Path(__file__).resolve().parent
def main():
    g=json.loads((H/'EXACT_LOCAL_GRAM.json').read_text());k=[[F(x) for x in r] for r in g['exact']]
    a=k[0][0];assert k==[list(r) for r in zip(*k)]
    # Direct rational LDL, separate from generator's principal-minor tests.
    lower=[[F(int(i==j)) for j in range(3)] for i in range(3)];diag=[]
    for i in range(3):
        d=k[i][i]-sum(lower[i][j]**2*diag[j] for j in range(i));assert d>0;diag.append(d)
        for z in range(i+1,3):lower[z][i]=(k[z][i]-sum(lower[z][j]*lower[i][j]*diag[j] for j in range(i)))/d
    v=json.loads((H/'GRAM_LOWER_729_VALUES.json').read_text());rows=v['values'];codes=gzip.decompress((H/v['entry_codes_file']).read_bytes())
    assert len(codes)==729**2
    values=[F(r['exact']) for r in rows];counts=[tuple(r['counts']) for r in rows]
    for r,x in zip(rows,values):
        c=r['counts'];assert sum(c)==6
        assert x==(k[0][1]/a)**c[1]*(k[1][1]/a)**c[2]*(k[1][2]/a)**c[3]
        assert F(r['lower'])<=x<=F(r['upper'])
    lookup={c:i for i,c in enumerate(counts)}
    # Decode rows/columns arithmetically rather than using generator's word list.
    types=((0,1,1),(1,2,3),(1,3,2));freq=Counter(codes)
    for i in range(729):
        for j in range(729):
            x,y=i,j;c=[0,0,0,0]
            for q in range(6):c[types[x%3][y%3]]+=1;x//=3;y//=3
            assert codes[729*i+j]==lookup[tuple(c)]
    for q,c in enumerate(counts):
        expected=math.factorial(6)//math.prod(math.factorial(x) for x in c)*4**c[1]*2**(c[2]+c[3])
        assert freq[q]==expected
    geom=json.loads((H/'GEOMETRY_AND_DIMENSION.json').read_text());ps=geom['plaquettes'];sel=geom['six_edge_disjoint_plaquette_ids']
    assert sorted(e for i in sel for e,s in ps[i])==list(range(24))
    for p in ps:
        starts=[];ends=[]
        for e,s in p:
            x,m=geom['edges'][e];y=x.copy();y[m]^=1
            starts.append(x if s==1 else y);ends.append(y if s==1 else x)
        assert ends==starts[1:]+starts[:1]
    cert=json.loads((H/'GRAM_EXECUTION_V15.json').read_text())
    assert not cert['full_spatial_Gram_computed'] and not cert['full_principal_729_Gram_computed']
    out={'status':'PASS_ALL_531441_LOWER_ENTRIES_AND_EXACT_LDL','verified_entries':len(codes),'verified_value_classes':len(rows),'geometric_plaquettes_closed':len(ps),'independent_exact_LDL_positive':True,'full_spatial_Gram_computed':False,'scope':'Independent verification of stored contractions and lower operator, not a full spatial contraction.'}
    (H/'INDEPENDENT_GRAM_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
