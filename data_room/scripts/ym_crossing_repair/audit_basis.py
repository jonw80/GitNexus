#!/usr/bin/env python3
"""Aggregate crossing matrix elements before testing high-basis phase consistency."""
import os, json, math, itertools, importlib.util, hashlib, inspect, collections
from pathlib import Path
import numpy as np
import scipy.sparse as sp

EXPECTED_REDUCER = "8d16d84065eeb4269471c125e2e0c25cc4929d37ffebb3d827e642a5bdf8d4c8"
root = Path(__file__).parent
out = Path(os.environ["V174_OUT"])
out.mkdir(parents=True, exist_ok=True)
red = Path(os.environ["V174_REDUCER"])
assert hashlib.sha256(red.read_bytes()).hexdigest() == EXPECTED_REDUCER
spec = importlib.util.spec_from_file_location("R", red)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
print("REDUCER_SOURCE_JSON=" + json.dumps(red.read_text()), flush=True)
for path in sorted(Path(os.environ["V174_INPUT"]).rglob("*.py")):
    print("ENGINE_SOURCE_JSON=" + json.dumps({"path":str(path.relative_to(os.environ["V174_INPUT"])), "source":path.read_text()}), flush=True)

C, outside = R.low_raw_C()
s, ncc, contr, eigres, logc = R.recover_phase(C)
H = (R.A * (C @ sp.diags(s.astype(float))) + sp.diags(logc)).tocsr()
D = (H - H.T).tocoo()
sym = float(np.max(np.abs(D.data))) if D.nnz else 0.
assert ncc == 1 and contr == 0 and sym <= 1e-8, (ncc, contr, sym)
hist = np.load(Path(os.environ["RUNNER_TEMP"])/"hist-inv/phase.npy")
assert np.array_equal(s, hist)
print("PHASE_AUDIT_JSON=" + json.dumps({"ncc":ncc,"contr":contr,"symmetry":sym,"nnz":int(C.nnz),"eigres":float(eigres)}, default=int), flush=True)

targets = {bytes.fromhex(x) for x in json.loads((root/"target_filter.json").read_text())}
key_filter = {x[:48] for x in targets}
pairs = collections.defaultdict(lambda: [[], []])
terms = []
for i, (key, vb) in enumerate(R.low_states):
    ns = R.orbit_size_bytes(R.encode_state(key, vb))
    for pidx in range(24):
        for ar in (1,-1):
            for nk in R.branches(key,pidx,ar):
                if R.degree(nk) < 10 or not R.valid_key(nk):
                    continue
                key48 = bytes(x for rr in nk for x in rr)
                if R.key_trans_info(key48)[0] not in key_filter:
                    continue
                for labs in R.gvl(nk):
                    R.FIXED_LABELS.add(R.slabels(labs))
                tc = R.transition_choices(key,nk,pidx,ar,vb,True,True,True)
                if tc is None:
                    continue
                aff,pf,pr,choices = tc
                for comb in itertools.product(*choices):
                    tvb = list(vb)
                    vf,vr = pf,pr
                    for v,(bb,xf,xr) in zip(aff,comb):
                        tvb[v] = bb
                        vf *= xf
                        vr *= xr
                    if abs(vf) <= 1e-13 and abs(vr) <= 1e-13:
                        continue
                    raw = R.encode_state(nk,tuple(tvb))
                    target = R.canon_state_bytes(raw)
                    if target not in targets:
                        continue
                    fac = R.A * math.sqrt(ns/R.orbit_size_bytes(target))
                    pairs[(target,i)][0].append(fac*vf)
                    pairs[(target,i)][1].append(fac*vr)
                    terms.append({"target":target.hex(),"raw_target":raw.hex(),"source":i,
                        "source56":R.encode_state(key,vb).hex(),"phase":int(s[i]),
                        "pidx":pidx,"ar":ar,"vf":float(vf),"vr":float(vr),
                        "vertex_factors":[[int(v),int(bb),float(xf),float(xr)] for v,(bb,xf,xr) in zip(aff,comb)]})
    if (i+1)%1000 == 0:
        print("AUDIT_PROGRESS",i+1,"matrix_pairs",len(pairs),flush=True)

rows = []
by_target = collections.defaultdict(list)
for (target,i),(fs,rs) in sorted(pairs.items()):
    f,r = math.fsum(fs),math.fsum(rs)
    threshold = 1e-12
    required = 0 if abs(f)<=threshold or abs(r)<=threshold else (1 if f*int(s[i])*r>0 else -1)
    row = {"target":target.hex(),"source":i,"phase":int(s[i]),"forward":f,"reverse":r,
           "required_high_phase":required,"relative_magnitude_defect":abs(abs(f)-abs(r))/max(abs(f),abs(r),1e-300),
           "q":float(R.psi[i]),"term_count":len(fs)}
    rows.append(row)
    if required:
        by_target[target.hex()].append(row)
conflicts = [{"target":t,"edges":v} for t,v in by_target.items()
             if len({x["required_high_phase"] for x in v})>1]
summary = {"schema":"YM_AGGREGATED_CROSSING_BASIS_AUDIT_V1",
    "status":"DIAGNOSTIC_ONLY","reducer_sha256":EXPECTED_REDUCER,
    "target_filter_count":len(targets),"matrix_pair_count":len(rows),
    "term_count":len(terms),"aggregate_high_phase_conflict_count":len(conflicts),
    "phase_gate":{"ncc":int(ncc),"contradictions":int(contr),"symmetry":sym},
    "gate_tolerances":{"R2_W2":1e-8,"R2_G10":1e-6},"G10":204.7027392787848,
    "external_norm_started":False}
(out/"audit.json").write_text(json.dumps({"summary":summary,"rows":rows,"conflicts":conflicts,"terms":terms},indent=2))
print("BASIS_AUDIT_SUMMARY_JSON="+json.dumps(summary),flush=True)
print("BASIS_AUDIT_DETAILS_JSON="+json.dumps({"rows":rows,"conflicts":conflicts,"terms":terms}),flush=True)
