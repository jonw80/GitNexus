#!/usr/bin/env python3
import os, json, pathlib, collections, math

OUT=pathlib.Path(os.environ['V197_OUT'])
records=[]
with (OUT/'forensic_contributions.jsonl').open() as f:
    for line in f:
        if line.strip(): records.append(json.loads(line))

by_target=collections.defaultdict(list)
for r in records: by_target[r['target56_hex']].append(r)

max_individual=0.0
max_abs_ratio=0.0
local_relation=set()
for r in records:
    rf=float(r['forward_contribution']); rw=float(r['reverse_contribution']); s=int(r['source_phase'])
    max_individual=max(max_individual,abs(rf+s*rw))
    if abs(rf)>1e-30 and abs(rw)>1e-30:
        max_abs_ratio=max(max_abs_ratio,abs(abs(rf/rw)-1.0))
        local_relation.add(1 if float(r['vf'])*float(r['vr'])>0 else -1)

rows=[]; max_agg=0.0; old_def=0.0; corrected_def=0.0; r2=0.0; wc2=0.0
for tgt,rs in sorted(by_target.items(), key=lambda kv:kv[1][0]['target_index']):
    R=sum(float(r['forward_contribution']) for r in rs)
    Wold=sum(float(r['reverse_contribution']) for r in rs)
    Wc=sum(int(r['source_phase'])*float(r['reverse_contribution']) for r in rs)
    resid=R+Wc
    max_agg=max(max_agg,abs(resid))
    old=R*R-Wold*Wold
    new=R*R-Wc*Wc
    old_def+=old; corrected_def+=new; r2+=R*R; wc2+=Wc*Wc
    rows.append({'target_index':rs[0]['target_index'],'target56_hex':tgt,'R':R,'W_unphased':Wold,'W_reverse_low_phase':Wc,'R_plus_W_corrected':resid,'old_norm2_defect':old,'corrected_norm2_defect':new})

cert={
  'schema':'GZYM_V197_REVERSE_LOW_PHASE_CORRECTION_CERT_V1',
  'historical_run_id':33715499716,
  'derivation':{
    'low_phase_definition':'recover_phase returns s so the physical low vector is represented in the raw action-source convention by phi = s * psi',
    'forward_historical':'R_t = sum_i A * fac * vf(t,i) * s_i * psi_i',
    'reverse_historical_bug':'W_t = sum_i A * fac * vr(i,t) * psi_i',
    'reverse_corrected':'Wcorr_t = sum_i A * fac * vr(i,t) * s_i * psi_i',
    'reason':'the same low-basis diagonal phase converting physical coefficients to the raw source convention must be applied when the low vector appears as the reverse matrix-element bra; omitting s_i mixes opposite low gauge sectors at shared high-shell targets',
    'expected_pair_relation':'for the exact targeted records vf = -vr to roundoff, hence each forward contribution plus s_i times the reverse contribution vanishes to roundoff'
  },
  'target_count':len(by_target),'contribution_count':len(records),
  'observed_local_relation_signs_vf_times_vr':sorted(local_relation),
  'max_individual_abs_forward_plus_phase_reverse':max_individual,
  'max_abs_abs_forward_over_reverse_minus_1':max_abs_ratio,
  'max_target_abs_R_plus_Wcorr':max_agg,
  'targeted_R_norm2':r2,'targeted_Wcorr_norm2':wc2,'targeted_R2_minus_Wcorr2':r2-wc2,
  'sum_old_target_norm2_defect':old_def,'sum_corrected_target_norm2_defect':corrected_def,
  'correction_status':'TARGETED_78_STATE_CERTIFIED; FULL_CROSSING_RERUN_REQUIRED_BEFORE_PROOF_PROMOTION',
  'proof_grade_full_crossing':False,
  'rows':rows
}
(OUT/'reverse_low_phase_correction_cert.json').write_text(json.dumps(cert,indent=2))
print(json.dumps({k:v for k,v in cert.items() if k!='rows'},indent=2))

if local_relation != {-1}: raise SystemExit('targeted local relation not uniformly -1')
if max_individual > 2e-15: raise SystemExit(('individual corrected reciprocity too large',max_individual))
if max_agg > 2e-15: raise SystemExit(('aggregate corrected reciprocity too large',max_agg))
