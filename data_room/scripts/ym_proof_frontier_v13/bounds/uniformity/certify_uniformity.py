#!/usr/bin/env python3
"""Exact-rational/outward audit of the uniformity arrows, with no assigned seed.

Run from any working directory. No third-party packages or network required.
Exponential intervals use rational Taylor sums plus a geometric positive tail.
Decimal conversion is directed; all pass/fail comparisons use Fractions.
"""
from fractions import Fraction as F
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def exp_iv(x, digits=110):
    x = F(x)
    if x < 0:
        lo, hi, n = exp_iv(-x, digits)
        return 1 / hi, 1 / lo, n
    s = term = F(1)
    n = 0
    while True:
        nxt = term * x / (n + 1)
        if n + 2 > x:
            tail = nxt / (1 - x / (n + 2))
            if tail <= F(1, 10**digits):
                return s, s + tail, n
        n += 1
        term = nxt
        s += term

def dec(x, rounding):
    with localcontext() as c:
        c.prec = 90
        c.rounding = rounding
        return str(Decimal(x.numerator) / Decimal(x.denominator))

def interval(lo, hi):
    return {"lower": dec(lo, ROUND_FLOOR), "upper": dec(hi, ROUND_CEILING)}

def tanh_iv(x):
    lo, hi, _ = exp_iv(2 * F(x))
    return (lo - 1)/(lo + 1), (hi - 1)/(hi + 1)

def main():
    beta = F(271,20)
    rho_lo,rho_hi,terms = exp_iv(-9*beta)
    qlo,qhi=tanh_iv(3*beta/4)
    small_beta=F(1,20)
    slo,shi=tanh_iv(3*small_beta/4)
    elo,ehi,_=exp_iv(F(1,4))
    small_q_lo,small_q_hi=18*elo*slo,18*ehi*shi
    assert 0 < small_q_lo <= small_q_hi < 1
    assert 18*qlo > 1  # The upper-bound formula fails; not an influence lower bound.
    ratio_lo,ratio_hi,_=exp_iv(F(999,1000))
    kp_ratio=(2*ratio_lo,2*ratio_hi)
    assert kp_ratio[0] > 1
    old_lo,old_hi,_=exp_iv(F(-1,100))
    new_lo,new_hi,_=exp_iv(-10)
    assert old_lo > 2*new_hi
    out={
        "schema":"YM_VOLUME_UNIFORMITY_ARROW_AUDIT_V13",
        "beta":"271/20",
        "calculation_method":"Fraction-only rational Taylor enclosure with geometric tail; directed 90-digit decimal serialization",
        "volume_uniform_fixed_cutoff":{
            "one_link_density_lower_bound_formula":"exp(-9*beta)",
            "density_bound_interval":interval(rho_lo,rho_hi),
            "normalized_plaquette_variance_floor_formula":"exp(-9*beta)/18",
            "normalized_plaquette_variance_floor_interval":interval(rho_lo/18,rho_hi/18),
            "unnormalized_plaquette_variance_floor_formula":"exp(-9*beta)/2",
            "unnormalized_plaquette_variance_floor_interval":interval(rho_lo/2,rho_hi/2),
            "exp_positive_taylor_last_degree":terms,
            "scope":"4D finite Wilson Gibbs volumes, finite-energy boundaries, and fixed-beta DLR limits; plaquettes with four distinct links"
        },
        "nonexpansion_curvature_actual_beta":{
            "a":"-128/5", "c":"813/10", "a_minus_c":"-1069/10",
            "g_squared":"120/271", "applicability":False,
            "reason":"a>c>0 fails; c/a is not a valid decay ratio when a is negative",
            "pure_wilson_window":"0 <= beta < 3/16"
        },
        "v120_quoted_stronger_CNS_margin":{
            "margin":"-527/10", "applicability":False,
            "note":"Even the archive's stronger 3/2-4*beta margin fails; this calculation does not independently import or verify that quoted theorem."
        },
        "repaired_elementary_WCI":{
            "formula":"q_mu <= 18*exp(mu)*tanh(3*beta/4)",
            "actual_beta_unweighted_upper_bound_formula_interval":interval(18*qlo,18*qhi),
            "actual_beta_gate":"NOT_CERTIFIED_BY_THIS_BOUND",
            "warning":"An upper bound above one does not show the actual influence row exceeds one and does not refute a mass gap.",
            "small_beta":"1/20", "mu":"1/4",
            "small_beta_weighted_upper_bound_interval":interval(small_q_lo,small_q_hi),
            "small_beta_gate":"CERTIFIED_VOLUME_UNIFORM_STRONG_MIXING"
        },
        "H6_envelope_KP_counterexample":{
            "activity":"single allowed polymer, size1, z=2*exp(-1/1000)",
            "source_envelope_satisfied":True,
            "minimum_over_a_positive_of_z_exp_a_over_a":interval(*kp_ratio),
            "KP_condition_fails_for_every_a":True,
            "scope":"Counterexample to implication from displayed activity envelope alone, not evidence that the actual Wilson polymer activity equals this value."
        },
        "equivalent_norm_counterexample":{
            "map":"T:R->R, T(x)=2*x", "operator_norm_in_every_norm":"2",
            "continuous":True, "can_rescale_norm_to_make_norm_le_1":False
        },
        "positive_radius_not_arbitrary_radius_counterexample":{
            "activity":"exp(-n/1000000)", "n":10000,
            "actual_activity_interval":interval(old_lo,old_hi),
            "claimed_2_exp_minus_n_over1000_interval":interval(2*new_lo,2*new_hi),
            "claimed_envelope_refuted":True
        },
        "DAG_status":{
            "finite_energy_uniform_local_variance":"PROVED",
            "small_beta_WCI":"PROVED_IN_STATED_DIFFERENT_REGIME",
            "H6_at_beta_271over20":"OPEN",
            "physical_beta_FCRG_entry_and_full_fibre_margin":"OPEN",
            "volume_uniform_clustering_actual_beta":"OPEN",
            "continuum_mass_gap":"OPEN"
        }
    }
    (ROOT/'UNIFORMITY_SCALAR_CERTIFICATE_V13.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({"arithmetic_checks":"PASS","physical_beta_uniform_gap":"OPEN","variance_floor":out["volume_uniform_fixed_cutoff"]["normalized_plaquette_variance_floor_interval"],"small_beta_q":out["repaired_elementary_WCI"]["small_beta_weighted_upper_bound_interval"]},indent=2))

if __name__=='__main__':main()
