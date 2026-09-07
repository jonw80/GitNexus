#!/usr/bin/env python3
import os, json, pathlib, collections, math

OUT = pathlib.Path(os.environ['V197_OUT'])
records=[]
with (OUT/'forensic_contributions.jsonl').open() as f:
    for line in f:
        if line.strip(): records.append(json.loads(line))

def sgn(x, eps=1e-18):
    if x > eps: return 1
    if x < -eps: return -1
    return 0

edge=[r for r in records if r.get('edge_sign')]
by_raw=collections.defaultdict(list)
by_target=collections.defaultdict(list)
for r in edge:
    by_raw[(r['target56_hex'],r['raw_target56_hex'])].append(r)
    by_target[r['target56_hex']].append(r)

conf_raw={k:v for k,v in by_raw.items() if len({r['edge_sign'] for r in v})>1}
conf_target={k:v for k,v in by_target.items() if len({r['edge_sign'] for r in v})>1}

# Compact one + and one - witness for each raw-target contradiction.
witnesses=[]
for (tgt,raw), rs in sorted(conf_raw.items()):
    plus=next(r for r in rs if r['edge_sign']==1)
    minus=next(r for r in rs if r['edge_sign']==-1)
    def slim(r):
        return {
            'target_index':r['target_index'], 'target56_hex':r['target56_hex'],
            'raw_target56_hex':r['raw_target56_hex'], 'source_i':r['source_i'],
            'source_phase':r['source_phase'], 'pidx':r['pidx'], 'ar':r['ar'],
            'vf':r['vf'], 'vr':r['vr'], 'vf_sign':sgn(r['vf']), 'vr_sign':sgn(r['vr']),
            'local_relation_sign_vf_vr':sgn(r['vf']*r['vr']),
            'edge_sign_source_phase_times_local_relation':r['edge_sign'],
            'forward_contribution':r['forward_contribution'],
            'reverse_contribution':r['reverse_contribution']
        }
    witnesses.append({'target56_hex':tgt,'raw_target56_hex':raw,'plus':slim(plus),'minus':slim(minus)})

# Contingency tables.  These are diagnostic only; they are not used as a fitted correction.
def count_table(keyfn):
    c=collections.Counter(keyfn(r) for r in edge)
    return [{'key':list(k) if isinstance(k,tuple) else k,'count':v} for k,v in sorted(c.items(), key=lambda kv:str(kv[0]))]

# Test a few symmetry-motivated sign factors only as falsification diagnostics.
# A candidate passes a target-consistency test iff corrected edge signs are unique
# on every raw target. No candidate is promoted as a repair by this script.
candidates={
    'none':lambda r:1,
    'ar':lambda r:int(r['ar']),
    'minus_ar':lambda r:-int(r['ar']),
    'pidx_parity':lambda r:1 if int(r['pidx'])%2==0 else -1,
    'ar_times_pidx_parity':lambda r:int(r['ar'])*(1 if int(r['pidx'])%2==0 else -1),
}
candidate_results={}
for name,fac in candidates.items():
    raw_bad=0; target_bad=0
    for rs in by_raw.values():
        if len({r['edge_sign']*fac(r) for r in rs})>1: raw_bad+=1
    for rs in by_target.values():
        if len({r['edge_sign']*fac(r) for r in rs})>1: target_bad+=1
    candidate_results[name]={'raw_conflict_count':raw_bad,'canonical_target_conflict_count':target_bad,'passes_raw':raw_bad==0,'passes_full_target':target_bad==0}

# For each pidx, ask whether one global sign flip for that plaquette index could
# make all raw targets consistent. This is a constraint problem, not a fit:
# each contradictory pair generates f[p1]/f[p2] = -edge1/edge2.
# Solve the +/- graph and report whether such a pidx-only gauge exists.
adj=collections.defaultdict(list)
constraint_count=0
for rs in conf_raw.values():
    for a in rs:
        for b in rs:
            if a is b or a['edge_sign']==b['edge_sign']: continue
            pa,pb=int(a['pidx']),int(b['pidx'])
            # Need edge_a*f(pa) = edge_b*f(pb); so f(pb)=edge_a*edge_b*f(pa).
            rel=int(a['edge_sign']*b['edge_sign'])
            adj[pa].append((pb,rel)); adj[pb].append((pa,rel)); constraint_count+=1
pidx_phase={}; pidx_contradictions=0
for root in range(24):
    if root in pidx_phase: continue
    pidx_phase[root]=1; q=collections.deque([root])
    while q:
        a=q.popleft()
        for b,rel in adj[a]:
            z=pidx_phase[a]*rel
            if b not in pidx_phase: pidx_phase[b]=z; q.append(b)
            elif pidx_phase[b]!=z: pidx_contradictions+=1

# Evaluate the derived pidx-only gauge on all records if its constraint graph is consistent.
pidx_gauge_eval=None
if pidx_contradictions==0:
    raw_bad=0; target_bad=0
    for rs in by_raw.values():
        if len({r['edge_sign']*pidx_phase[int(r['pidx'])] for r in rs})>1: raw_bad+=1
    for rs in by_target.values():
        if len({r['edge_sign']*pidx_phase[int(r['pidx'])] for r in rs})>1: target_bad+=1
    pidx_gauge_eval={'raw_conflict_count':raw_bad,'canonical_target_conflict_count':target_bad,'passes_raw':raw_bad==0,'passes_full_target':target_bad==0}

summary={
    'schema':'GZYM_V197_RW78_CONFLICT_STRUCTURE_V1',
    'record_count':len(records),'edge_record_count':len(edge),
    'raw_conflict_count':len(conf_raw),'canonical_target_conflict_count':len(conf_target),
    'witness_count':len(witnesses),
    'counts_by_pidx_ar_edge_sign':count_table(lambda r:(int(r['pidx']),int(r['ar']),int(r['edge_sign']))),
    'counts_by_ar_sourcephase_localrelation_edge':count_table(lambda r:(int(r['ar']),int(r['source_phase']),sgn(r['vf']*r['vr']),int(r['edge_sign']))),
    'symmetry_candidate_falsification':candidate_results,
    'pidx_only_gauge_constraint':{
        'constraint_pairs':constraint_count,
        'contradictions':pidx_contradictions,
        'phase_by_pidx':{str(k):int(v) for k,v in sorted(pidx_phase.items())},
        'evaluation':pidx_gauge_eval,
        'interpretation':'diagnostic only; a consistent pidx-only gauge would still require derivation from the action/orientation conventions before use'
    },
    'raw_conflict_witnesses':witnesses
}
(OUT/'conflict_structure.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ('raw_conflict_witnesses','counts_by_pidx_ar_edge_sign','counts_by_ar_sourcephase_localrelation_edge')},indent=2))
