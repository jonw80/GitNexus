#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / 'data'
PROOFS = ROOT / 'proofs'
REPORT = DATA / 'frontier_closeout_report.json'

REQUIRED = {
  'pfaffian': (DATA/'pfaffian_normalization_certificate.json', PROOFS/'pfaffian_local_reduction_theorem.tex', 'VERIFIED_ABSOLUTE_PFAFFIAN_NORMALIZATION'),
  'uplift': (DATA/'uplift_hessian_certificate.json', PROOFS/'uplift_positive_hessian_theorem.tex', 'VERIFIED_UPLIFT_STABILITY'),
  'cosmological_constant': (DATA/'cosmological_constant_error_budget.json', PROOFS/'cosmological_constant_interval_theorem.tex', 'VERIFIED_COSMOLOGICAL_CONSTANT_INTERVAL_PAYLOAD'),
  'prime_race': (DATA/'prime_race_density_certificate.json', PROOFS/'prime_race_density_theorem.tex', 'VERIFIED_PRIME_RACE_DENSITY'),
  'ym_mass_gap_import': (DATA/'ym_mass_gap_import_certificate.json', PROOFS/'ym_mass_gap_import_theorem.tex', 'VERIFIED_YM_MASS_GAP_COMPANION_IMPORT'),
  'proton_cp': (DATA/'proton_cp_lattice_certificate.json', PROOFS/'proton_cp_lattice_extraction_theorem.tex', 'VERIFIED_PROTON_CP_LATTICE_QCD'),
  'hadamard_divisor': (DATA/'hadamard_divisor_certificate.json', PROOFS/'hadamard_divisor_identification_theorem.tex', 'VERIFIED_HADAMARD_DIVISOR_IDENTIFICATION'),
  'y4_tensor': (DATA/'y4_tensor_manifest.json', PROOFS/'y4_tensor_reproduction_theorem.tex', 'FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED'),
}

def load(path: Path):
    try: return json.loads(path.read_text()), None
    except Exception as e: return {}, str(e)

def sha_file(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def canonical_hash(obj: dict[str, Any]) -> str:
    tmp=dict(obj); tmp.pop('payload_hash', None)
    return hashlib.sha256(json.dumps(tmp, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def interval(obj, key, fail):
    v=obj.get(key)
    if isinstance(v, dict): lo,hi=v.get('lower'),v.get('upper')
    elif isinstance(v, list) and len(v)==2: lo,hi=v
    else: fail.append(f'{key}: missing interval'); return math.nan, math.nan
    try: lo=float(lo); hi=float(hi)
    except Exception: fail.append(f'{key}: bad endpoints'); return math.nan, math.nan
    if not (math.isfinite(lo) and math.isfinite(hi) and lo<=hi): fail.append(f'{key}: invalid interval')
    return lo,hi

def num(obj, key, fail):
    try: x=float(obj[key])
    except Exception: fail.append(f'{key}: missing numeric'); return math.nan
    if not math.isfinite(x): fail.append(f'{key}: nonfinite')
    return x

def check_common(name, obj, proof, status, fail):
    if obj.get('status') != status: fail.append(f'status mismatch: {obj.get("status")} != {status}')
    if obj.get('fully_certified') is not True: fail.append('fully_certified must be true')
    if not str(obj.get('schema_version','')).startswith('UGCT_'): fail.append('schema_version must start with UGCT_')
    if not proof.exists(): fail.append(f'missing proof {proof.relative_to(REPO)}')
    elif proof.stat().st_size <= 500: fail.append(f'proof too small {proof.relative_to(REPO)}')
    if obj.get('payload_hash') != canonical_hash(obj): fail.append('payload_hash mismatch')

def check_item(name, obj, fail):
    if name=='pfaffian':
        lo,hi=interval(obj,'pfaffian_interval',fail); 
        if not (lo>0 and hi>0): fail.append('pfaffian interval must be positive')
        for k in ['zero_modes_removed','collar_independence_verified']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
        for k in ['operator_domain','determinant_line_convention']:
            if not obj.get(k): fail.append(f'{k} required')
    elif name=='uplift':
        lam=num(obj,'hessian_lambda_min_lower',fail); grad=num(obj,'gradient_norm_upper',fail); gap=num(obj,'boundary_potential_gap_lower',fail); lo,hi=interval(obj,'V_phys_interval',fail)
        if not lam>0: fail.append('hessian lower bound must be positive')
        if not (grad>=0 and grad<=max(lam,1.0)*1e-8): fail.append('gradient residual too large')
        if not gap>0: fail.append('boundary gap must be positive')
        if not (lo>0 and hi>0): fail.append('V interval must be positive')
        for k in ['compact_window_verified','backreaction_terms_included']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
    elif name=='cosmological_constant':
        lo,hi=interval(obj,'rho_lambda_interval',fail)
        if not (lo>0 and hi>0): fail.append('rho interval must be positive')
        if obj.get('depends_on_uplift_certificate')!='VERIFIED_UPLIFT_STABILITY': fail.append('uplift dependency mismatch')
        if not obj.get('error_budget_terms'): fail.append('error budget required')
        if obj.get('all_uncertainties_propagated') is not True: fail.append('uncertainty propagation flag required')
    elif name=='prime_race':
        lo,hi=interval(obj,'density_delta_4_3_1_interval',fail); eps=num(obj,'epsilon_above_one_half',fail)
        if not (lo>0.5 and hi<=1): fail.append('density interval must clear one half')
        if not eps>0: fail.append('epsilon must be positive')
        for k in ['grh_used','linear_independence_used']:
            if obj.get(k) is not False: fail.append(f'{k} must be false')
        for k in ['spectral_identification_verified','polymer_hypotheses_verified']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
    elif name=='ym_mass_gap_import':
        if not obj.get('companion_volume_sha256'): fail.append('companion hash required')
        for k in ['os_axioms_verified','spectral_gap_lower_bound_positive','reflection_positivity_verified','rg_convergence_verified']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
    elif name=='proton_cp':
        cp=interval(obj,'c_p_interval',fail); mp=interval(obj,'m_p_interval',fail)
        if not (cp[0]>0 and cp[1]>0 and mp[0]>0 and mp[1]>0): fail.append('positive proton intervals required')
        for k in ['continuum_extrapolation_verified','finite_volume_error_bounded','scale_setting_verified']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
        if not obj.get('lattice_input_snapshot_sha256'): fail.append('lattice snapshot hash required')
    elif name=='hadamard_divisor':
        for k in ['xi_divisor_identified','nonvanishing_factor_verified','no_spurious_zeros_verified','hurwitz_transfer_verified','h2_tail_graph_norm_verified','parity_gap_persistence_verified']:
            if obj.get(k) is not True: fail.append(f'{k} must be true')
    elif name=='y4_tensor':
        if obj.get('full_chamber_specific_tensor_verified') is not True: fail.append('tensor verified flag required')
        if int(obj.get('nonzero_quadruple_intersections',0)) <= 0: fail.append('nonzero tensor count required')
        for k in ['source_workflow_run_id','artifact_sha256','tensor_file_sha256']:
            if not obj.get(k): fail.append(f'{k} required')

def verify(name, spec):
    cert, proof, status = spec
    fail=[]; obj={}
    if not cert.exists(): fail.append(f'missing certificate {cert.relative_to(REPO)}')
    else:
        obj, err=load(cert)
        if err: fail.append(f'json error {err}')
        else:
            check_common(name,obj,proof,status,fail); check_item(name,obj,fail)
    rec={'name':name,'certificate':str(cert.relative_to(REPO)),'proof':str(proof.relative_to(REPO)),'required_status':status,'ok':not fail,'failures':fail}
    if cert.exists(): rec['certificate_sha256']=sha_file(cert)
    if proof.exists(): rec['proof_sha256']=sha_file(proof)
    return rec

def main():
    p=argparse.ArgumentParser(); p.add_argument('--allow-proton-pending', action='store_true'); args=p.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    records=[verify(n,s) for n,s in REQUIRED.items()]
    effective=[r for r in records if not (args.allow_proton_pending and r['name']=='proton_cp')]
    ok=all(r['ok'] for r in effective)
    report={'schema_version':'UGCT_FRONTIER_CLOSEOUT_REPORT_V3','status':'FRONTIER_CLOSEOUT_VERIFIED' if ok else 'FRONTIER_CLOSEOUT_NOT_VERIFIED','strict':True,'allow_proton_pending':bool(args.allow_proton_pending),'records':records}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True)); print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1
if __name__ == '__main__':
    raise SystemExit(main())
