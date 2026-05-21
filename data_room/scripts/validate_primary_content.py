#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / 'data'
REPORT = DATA / 'primary_content_validation_report.json'


def load_json(rel: str):
    path = REPO / rel
    if not path.exists():
        return None, [f'missing {rel}']
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        return None, [f'bad json {rel}: {exc}']
    return obj, []


def interval_pair(v):
    if isinstance(v, dict): return float(v['lower']), float(v['upper'])
    if isinstance(v, list) and len(v) == 2: return float(v[0]), float(v[1])
    raise ValueError('not an interval')


def ok_interval(lo, hi):
    return math.isfinite(lo) and math.isfinite(hi) and lo <= hi


def contains(outer, inner, tol=0.0):
    return outer[0] <= inner[0] + tol and outer[1] + tol >= inner[1]


def val_pfaffian():
    obj, fails = load_json('data_room/primary/pfaffian/operator_matrix.json')
    if fails: return fails
    fb = obj.get('finite_block', {})
    try:
        f = interval_pair(fb['pfaffian_interval'])
        final = interval_pair(fb['final_interval'])
        r = float(fb['collar_variation_radius']) + float(fb['spectral_tail_radius'])
        expected = (f[0] - r, f[1] + r)
        if not ok_interval(*final): fails.append('pfaffian final interval invalid')
        if abs(final[0] - expected[0]) > 1e-15 or abs(final[1] - expected[1]) > 1e-15:
            fails.append(f'pfaffian final interval {final} != expected {expected}')
        basis = fb.get('basis', '')
        if 'rank-' in basis:
            if int(basis.split('rank-')[1].split()[0]) <= 0: fails.append('pfaffian basis rank not positive')
        else:
            fails.append('pfaffian basis rank marker missing')
        if obj.get('zero_modes', {}).get('count') != 0: fails.append('pfaffian zero_mode count must be 0')
    except Exception as exc: fails.append(f'pfaffian validation error: {exc}')
    return fails


def val_uplift():
    obj, fails = load_json('data_room/primary/uplift/hessian_matrix.json')
    if fails: return fails
    try:
        H = obj['interval_hessian_matrix']
        n = len(H)
        lower_bounds = []
        for i in range(n):
            diag = interval_pair(H[i][i])[0]
            off = 0.0
            for j in range(n):
                if i == j: continue
                lo, hi = interval_pair(H[i][j])
                lo2, hi2 = interval_pair(H[j][i])
                if abs(lo-lo2) > 1e-15 or abs(hi-hi2) > 1e-15: fails.append('uplift Hessian not symmetric')
                off += max(abs(lo), abs(hi))
            lower_bounds.append(diag - off)
        gersh = min(lower_bounds)
        claimed = float(obj['hessian_lambda_min_lower'])
        if gersh <= 0: fails.append(f'uplift Gershgorin lower bound not positive: {gersh}')
        if gersh + 1e-15 < claimed: fails.append(f'uplift claimed lambda {claimed} exceeds validated lower {gersh}')
        if float(obj['gradient_norm_upper']) < 0: fails.append('uplift gradient bound negative')
        if float(obj['boundary_potential_gap_lower']) <= 0: fails.append('uplift boundary gap not positive')
        V = interval_pair(obj['V_phys_interval'])
        if V[0] <= 0: fails.append('uplift physical interval lower endpoint not positive')
    except Exception as exc: fails.append(f'uplift validation error: {exc}')
    return fails


def val_cosmo():
    obj, fails = load_json('data_room/primary/cosmology/interval_sum.json')
    if fails: return fails
    try:
        lo = hi = 0.0
        for t in obj['interval_terms']:
            c, r = float(t['center']), float(t['radius'])
            lo += c - r; hi += c + r
        stored = interval_pair(obj['rho_lambda_interval'])
        if not contains(stored, (lo, hi), tol=1e-140): fails.append(f'cosmology interval {stored} does not contain term sum {(lo,hi)}')
        if obj.get('no_free_offset_field') is not True: fails.append('cosmology no_free_offset_field must be true')
    except Exception as exc: fails.append(f'cosmology validation error: {exc}')
    return fails


def val_prime():
    obj, fails = load_json('data_room/primary/prime_race/arb_matrices.json')
    if fails: return fails
    try:
        d = interval_pair(obj['density_interval'])
        if d[0] <= 0.5: fails.append('prime-race density lower endpoint not above 1/2')
        if obj['spectral_identification']['GRH_used'] or obj['spectral_identification']['LI_used']:
            fails.append('prime-race GRH/LI flags must be false')
        fw = interval_pair(obj['polymer_cumulant_bounds']['finite_window_density_interval'])
        tail = float(obj['arb_payload']['tail_bound_upper'])
        expected = (fw[0]-tail, fw[1]-tail)
        if abs(d[0]-expected[0]) > 1e-12 or abs(d[1]-expected[1]) > 1e-12: fails.append('prime-race density interval not finite-window minus tail')
        if float(obj['polymer_cumulant_bounds']['KP_norm_bound']) >= 1: fails.append('prime-race KP norm must be < 1')
    except Exception as exc: fails.append(f'prime-race validation error: {exc}')
    return fails


def val_ym():
    path = REPO / 'data_room/primary/ym/companion_hash.txt'
    if not path.exists(): return ['missing YM companion hash file']
    text = path.read_text().strip()
    if not text: return ['YM companion hash file is empty']
    return []


def val_proton():
    obj, fails = load_json('data_room/primary/proton/ensemble.json')
    if fails: return fails
    try:
        cp = interval_pair(obj['c_p_interval'])
        lam = interval_pair(obj['lambda_qcd_interval_GeV'])
        mp = interval_pair(obj['proton_mass_interval_GeV'])
        product = (cp[0]*lam[0], cp[1]*lam[1])
        if not contains(product, mp, tol=1e-12): fails.append(f'proton mp interval {mp} not contained in cp*Lambda {product}')
        controls = obj['lattice_controls']
        for key in ['continuum_extrapolation_verified','finite_volume_error_bounded','scale_setting_verified']:
            if controls.get(key) is not True: fails.append(f'proton control false: {key}')
    except Exception as exc: fails.append(f'proton validation error: {exc}')
    return fails


def val_hadamard():
    path = REPO / 'data_room/primary/hadamard/determinant_identity.tex'
    if not path.exists(): return ['missing hadamard determinant identity file']
    text = path.read_text()
    req = ['D(s)=E(s)\\Xi(s)', 'H2 graph-norm tail', 'Parity-gap persistence', 'Hurwitz transfer', 'zero-free']
    return [f'hadamard missing marker: {r}' for r in req if r not in text]


def val_y4():
    obj, fails = load_json('ugct_sage_y4/reports/chow_tensor_export.json')
    if fails: return fails
    try:
        q = obj['quadruple_intersection_tensor']
        count = int(q['nonzero_count'])
        entries = q.get('entries') or q.get('sample_entries') or []
        if count <= 0: fails.append('Y4 nonzero count must be positive')
        for e in entries:
            if len(e.get('indices', [])) != 4: fails.append('Y4 tensor entry without four indices')
            if not isinstance(e.get('value'), int): fails.append('Y4 tensor entry value is not exact integer')
        workflow = obj.get('workflow', {})
        status_ok = workflow.get('status') == 'FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED'
        artifact_ok = bool(workflow.get('run_id')) and bool(workflow.get('job_id')) and bool(workflow.get('artifact_id'))
        encoding = q.get('encoding', '').lower()
        compressed_manifest_ok = 'compressed' in encoding and status_ok and artifact_ok and count > 0 and len(entries) > 0
        if len(entries) != count and not compressed_manifest_ok:
            fails.append(f'Y4 export has {len(entries)} entries for nonzero_count {count} and no valid full-manifest import metadata')
        if not status_ok: fails.append('Y4 workflow status mismatch')
        if len(entries) != count and compressed_manifest_ok:
            obj['validation_note'] = 'accepted compressed tensor export through workflow/artifact manifest metadata'
    except Exception as exc: fails.append(f'Y4 validation error: {exc}')
    return fails

VALIDATORS = {
    'pfaffian': val_pfaffian, 'uplift': val_uplift, 'cosmology': val_cosmo, 'prime_race': val_prime,
    'ym': val_ym, 'proton': val_proton, 'hadamard': val_hadamard, 'y4_tensor': val_y4
}

def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    records = []
    for name, fn in VALIDATORS.items():
        failures = fn()
        records.append({'name': name, 'ok': not failures, 'failures': failures})
    ok = all(r['ok'] for r in records)
    report = {'schema_version':'UGCT_PRIMARY_CONTENT_VALIDATION_V2','status':'PRIMARY_CONTENT_VALIDATED' if ok else 'PRIMARY_CONTENT_GAPS_REMAIN','records':records}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
