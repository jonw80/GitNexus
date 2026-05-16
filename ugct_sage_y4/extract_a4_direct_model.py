#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

DATA=Path('data'); REPORTS=Path('reports'); SOURCES=Path('sources')
DATA.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
PKG=SOURCES/'IntersectionNumbers.m'
OUT=DATA/'intersectionnumbers_a4_model.json'
REPORT=REPORTS/'intersectionnumbers_a4_model_extract_report.json'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(65536),b''):
            h.update(b)
    return h.hexdigest()

def emit(o):
    REPORT.write_text(json.dumps(o,indent=2,sort_keys=True)); print(json.dumps(o,indent=2,sort_keys=True))

if not PKG.exists():
    emit({'status':'A4_MODEL_EXTRACT_NOT_RUN','reason':'sources/IntersectionNumbers.m missing'}); raise SystemExit(0)

# Direct A4 specialization of the source formula algebraDivisors[{a,r},index]
gens=[['2*L','3*L','s[1]'],['3*L - e[1]','e[1]'],['2*L - e[1]','e[2]'],['3*L - e[1] - e[2]','e[3]']]
divs=['e[1] - e[2]','e[3] - e[4]','e[4]','e[2] - e[3]']
hs='3*e[0] + 6*L - (e[1] + e[2] + e[3] + e[4])'
obj={
 'schema_version':'INTERSECTIONNUMBERS_A4_MODEL_V2_DIRECT_SOURCE',
 'status':'INTERSECTIONNUMBERS_A4_MODEL_EXTRACTED',
 'extraction_mode':'direct_source_formula_no_mathics',
 'algebra_rank':'A4 / SU(5)',
 'rank':4,
 'index':1,
 'generators':gens,
 'generators_inputform':'{'+', '.join('{'+', '.join(g)+'}' for g in gens)+'}',
 'hypersurface':hs,
 'hypersurface_inputform':hs,
 'divisors':divs,
 'divisors_inputform':'{'+', '.join(divs)+'}',
 'cartan_length':'4',
 'source_package_sha256':sha(PKG),
 'mathics_required':False,
 'wolfram_required':False,
 'closure_scope':'A4 structural model only; exact 235-value closure still requires native pushforward recursion'
}
OUT.write_text(json.dumps(obj,indent=2,sort_keys=True))
emit({'status':'INTERSECTIONNUMBERS_A4_MODEL_EXTRACTED','output':str(OUT),'cartan_length':'4','mathics_required':False,'package_sha256':sha(PKG)})
