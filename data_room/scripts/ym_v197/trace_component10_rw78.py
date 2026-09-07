#!/usr/bin/env python3
import os, sys, json, math, time, pathlib, hashlib, importlib.util, itertools, collections
import numpy as np

RED = pathlib.Path(os.environ['V174_REDUCER'])
HIST = pathlib.Path(os.environ['V174_HISTORICAL_RESULT'])
OUT = pathlib.Path(os.environ['V197_OUT'])
OUT.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location('v174_reducer', RED)
ren = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ren)

cross = np.load(HIST / 'crossing_component10.npz', allow_pickle=False)
K0 = np.asarray(cross['states56'], np.uint8)
R0 = np.asarray(cross['R'], np.float64)
W0 = np.asarray(cross['W'], np.float64)
phase = np.asarray(np.load(HIST / 'phase.npy', allow_pickle=False), np.int8)

if K0.shape != (1612533, 56):
    raise RuntimeError(('unexpected historical crossing shape', K0.shape))
if phase.shape != (7576,):
    raise RuntimeError(('unexpected phase shape', phase.shape))

r2 = float(R0 @ R0)
w2 = float(W0 @ W0)
magdef = np.abs(np.abs(R0) - np.abs(W0))
bad_idx = np.flatnonzero(magdef > 1e-12)
bad_states = {bytes(K0[j].tolist()): int(j) for j in bad_idx}
bad_keys = {bytes(K0[j, :48].tolist()) for j in bad_idx}

if len(bad_idx) != 78 or len(bad_keys) != 64:
    raise RuntimeError(('historical bad-target tripwire changed', len(bad_idx), len(bad_keys)))
if abs((r2 - w2) - 3.7292559682100546e-05) > 1e-12:
    raise RuntimeError(('historical R/W norm defect changed', r2, w2, r2-w2))

# The historical reducer used this phase in the failing crossing.  Replaying only
# the 64 canonical target keys preserves the exact branch/coefficient machinery
# while avoiding the 1.6M-target accumulator.  Every retained contribution is
# recorded before and after translation canonicalization.
ren.CACHE = pathlib.Path(os.environ['V174_CACHE'])
s = phase
psi = ren.psi
if len(psi) != len(s):
    raise RuntimeError(('psi/phase length mismatch', len(psi), len(s)))

accR = collections.defaultdict(float)
accW = collections.defaultdict(float)
records = []
seen_key_branches = 0
kept_terms = 0
t0 = time.time()

for i, (key, vb) in enumerate(ren.low_states):
    if abs(float(psi[i])) <= 1e-18:
        continue
    ns = ren.orbit_size_bytes(ren.encode_state(key, vb))
    for pidx in range(24):
        for ar in (1, -1):
            for nk in ren.branches(key, pidx, ar):
                dg = ren.degree(nk)
                if dg < 10 or dg > 13 or not ren.valid_key(nk):
                    continue
                raw_key48 = bytes([x for rr in nk for x in rr])
                canon_key48 = ren.key_trans_info(raw_key48)[0]
                if canon_key48 not in bad_keys:
                    continue
                seen_key_branches += 1
                for labs in ren.gvl(nk):
                    ren.FIXED_LABELS.add(ren.slabels(labs))
                tc = ren.transition_choices(key, nk, pidx, ar, vb, True, True, True)
                if tc is None:
                    continue
                aff, pf, pr, choices = tc
                base = list(vb)
                for comb in itertools.product(*choices):
                    vf = pf
                    vr = pr
                    tvb = base.copy()
                    for v, (bb, xf, xr) in zip(aff, comb):
                        tvb[v] = bb
                        vf *= xf
                        vr *= xr
                    if abs(vf) <= 1e-13 and abs(vr) <= 1e-13:
                        continue
                    raw = ren.encode_state(nk, tuple(tvb))
                    rb = ren.canon_state_bytes(raw)
                    if rb not in bad_states:
                        continue
                    nt = ren.orbit_size_bytes(rb)
                    fac = math.sqrt(ns / nt)
                    rf = ren.A * fac * vf * float(s[i]) * float(psi[i]) if abs(vf) > 1e-13 else 0.0
                    rw = ren.A * fac * vr * float(psi[i]) if abs(vr) > 1e-13 else 0.0
                    accR[rb] += rf
                    accW[rb] += rw
                    kept_terms += 1
                    edge_sign = 0
                    if abs(rf) > 1e-18 and abs(rw) > 1e-18:
                        edge_sign = 1 if rf * rw > 0 else -1
                    records.append({
                        'target_index': bad_states[rb],
                        'target56_hex': rb.hex(),
                        'raw_target56_hex': raw.hex(),
                        'raw_key48_hex': raw_key48.hex(),
                        'canon_key48_hex': canon_key48.hex(),
                        'source_i': i,
                        'source_phase': int(s[i]),
                        'source_psi': float(psi[i]),
                        'pidx': pidx,
                        'ar': ar,
                        'vf': float(vf),
                        'vr': float(vr),
                        'forward_contribution': float(rf),
                        'reverse_contribution': float(rw),
                        'edge_sign': edge_sign,
                    })
    if (i + 1) % 500 == 0:
        print('FORENSIC', i+1, '/', len(ren.low_states), 'key_branches', seen_key_branches, 'kept_terms', kept_terms, 'sec', time.time()-t0, flush=True)

# Compare the targeted replay to the exact historical aggregate.
replay_rows = []
max_r_err = 0.0
max_w_err = 0.0
for rb, j in sorted(bad_states.items(), key=lambda kv: kv[1]):
    rr = float(accR.get(rb, 0.0))
    ww = float(accW.get(rb, 0.0))
    er = abs(rr - float(R0[j]))
    ew = abs(ww - float(W0[j]))
    max_r_err = max(max_r_err, er)
    max_w_err = max(max_w_err, ew)
    replay_rows.append({
        'index': j,
        'state56_hex': rb.hex(),
        'historical_R': float(R0[j]),
        'historical_W': float(W0[j]),
        'replay_R': rr,
        'replay_W': ww,
        'R_error': er,
        'W_error': ew,
        'historical_norm2_defect': float(R0[j]*R0[j] - W0[j]*W0[j]),
    })

# Diagnose whether the inconsistent sign is introduced only when translated raw
# representatives are collapsed to one canonical target, or already exists for
# one identical raw representative.
by_target = collections.defaultdict(list)
by_raw = collections.defaultdict(list)
for rec in records:
    if rec['edge_sign']:
        by_target[rec['target56_hex']].append(rec['edge_sign'])
        by_raw[(rec['target56_hex'], rec['raw_target56_hex'])].append(rec['edge_sign'])

target_sign_conflicts = {
    k: sorted(set(v)) for k, v in by_target.items() if len(set(v)) > 1
}
raw_sign_conflicts = {
    k[0] + ':' + k[1]: sorted(set(v)) for k, v in by_raw.items() if len(set(v)) > 1
}

# A canonical target is a transport-phase conflict when every individual raw
# representative has a single sign but different representatives carry different
# signs after canonicalization.
transport_conflicts = []
for tgt, signs in target_sign_conflicts.items():
    raw_groups = {raw: set(v) for (tt, raw), v in by_raw.items() if tt == tgt}
    if raw_groups and all(len(v) == 1 for v in raw_groups.values()) and len({next(iter(v)) for v in raw_groups.values()}) > 1:
        transport_conflicts.append(tgt)

if raw_sign_conflicts:
    classification = 'LOCAL_FORWARD_REVERSE_PHASE_INCONSISTENCY'
elif transport_conflicts:
    classification = 'CANONICALIZATION_TRANSPORT_PHASE_MISSING'
elif target_sign_conflicts:
    classification = 'TARGET_PHASE_CONFLICT_UNRESOLVED'
else:
    classification = 'NO_SIGN_CONFLICT; CHECK_MAGNITUDE_THRESHOLD_OR_BASIS'

summary = {
    'schema': 'GZYM_V197_COMPONENT10_RW78_FORENSIC_REPLAY_V1',
    'historical_run_id': 33715499716,
    'historical_R2': r2,
    'historical_W2': w2,
    'historical_R2_minus_W2': r2-w2,
    'bad_target_count': len(bad_idx),
    'bad_key_count': len(bad_keys),
    'seen_target_key_branches': seen_key_branches,
    'kept_contribution_terms': kept_terms,
    'targeted_replay_max_R_error': max_r_err,
    'targeted_replay_max_W_error': max_w_err,
    'target_sign_conflict_count': len(target_sign_conflicts),
    'raw_representative_sign_conflict_count': len(raw_sign_conflicts),
    'transport_conflict_target_count': len(transport_conflicts),
    'classification': classification,
    'reducer_sha256': hashlib.sha256(RED.read_bytes()).hexdigest(),
    'historical_phase_sha256': hashlib.sha256((HIST/'phase.npy').read_bytes()).hexdigest(),
    'elapsed_seconds': time.time()-t0,
    'replay_rows': replay_rows,
}

(OUT / 'forensic_summary.json').write_text(json.dumps(summary, indent=2))
with (OUT / 'forensic_contributions.jsonl').open('w') as f:
    for rec in records:
        f.write(json.dumps(rec, sort_keys=True) + '\n')
(OUT / 'target_sign_conflicts.json').write_text(json.dumps(target_sign_conflicts, indent=2, sort_keys=True))
(OUT / 'raw_sign_conflicts.json').write_text(json.dumps(raw_sign_conflicts, indent=2, sort_keys=True))
(OUT / 'transport_conflicts.json').write_text(json.dumps(transport_conflicts, indent=2))
print(json.dumps({k:v for k,v in summary.items() if k != 'replay_rows'}, indent=2), flush=True)

# Fail closed if the targeted replay did not reproduce the historical defect.
if max_r_err > 2e-10 or max_w_err > 2e-10:
    raise RuntimeError(('targeted replay mismatch', max_r_err, max_w_err))
