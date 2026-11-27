#!/usr/bin/env python3
"""Build six of the eight frontier records from computations done in this run.

The Y4 manifest (ugct_sage_y4/build_y4_tensor_manifest.py) and the Yang-Mills import record
(data_room/scripts/build_ym_import_record.py) have their own builders. This script writes the other six, each to the
path the strict gate (verify_frontier_closeout.py) reads, with a scope category (see frontier_records.py):

  prime_race             CONDITIONAL  delta(4;3,1) under GRH + LI, from the zeros of L(s, chi_-4) computed here (PARI)
  proton_cp              OPEN         c_p = m_p / Lambda per scheme from published lattice QCD; VERIFIED once
                                      data_room/primary/proton/declared_scheme.json names the scheme of Lambda_QCD
  pfaffian               OPEN         chi(O_D) of the basis divisors from this run's Y4 tensor; no instanton operator
  uplift                 OPEN         no effective potential exists; arithmetic rechecks of the typed Hessian
  cosmological_constant  OPEN         Minkowski sum of the typed terms, the observed value, the e^(-6N)/24^6 formula
  hadamard_divisor       OPEN         no operator exists; the manuscript states this identification is RH-level

Until 2026-11-27 emit_frontier_closeout_artifacts.py typed these certificates in with status VERIFIED. Every number
below is computed here or read from a hashed input; the typed primary files are read only to be checked.

Run from the repository root (needs cypari2 for the prime race):
  python3 data_room/scripts/build_frontier_certificates.py [--only ITEM ...] [--prime-race-height T]
Exits 1 if a computation fails its own checks.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontier_records as fr  # noqa: E402

COMPUTED_BY = "data_room/scripts/build_frontier_certificates.py"
Y4_TENSOR = "ugct_sage_y4/data/y4_independent_tensor.json"
PROTON_MODULE = "ugct_formal/proton_cp_published_lattice.py"
PROTON_DECLARED = "data_room/primary/proton/declared_scheme.json"
PROTON_TYPED = "data_room/primary/proton/ensemble.json"
PRIME_TYPED = "data_room/primary/prime_race/arb_matrices.json"
PRIME_MANUSCRIPT = "data_room/data/prime_race_density_verified.json"
PFAFFIAN_TYPED = "data_room/primary/pfaffian/operator_matrix.json"
UPLIFT_TYPED = "data_room/primary/uplift/hessian_matrix.json"
COSMO_TYPED = "data_room/primary/cosmology/interval_sum.json"
HADAMARD_TYPED = "data_room/primary/hadamard/determinant_identity.tex"

# Rubinstein and Sarnak, "Chebyshev's bias", Experiment. Math. 3 (1994) 173-197: delta(4;3,1) = 0.9959 (4 digits)
RUBINSTEIN_SARNAK_DELTA_4_3_1 = 0.9959

# Observed vacuum energy inputs (published values, used as published)
COSMO_SNAPSHOT = {
    "H0_km_s_Mpc": {"value": 67.36, "sigma": 0.54},
    "Omega_Lambda": {"value": 0.6847, "sigma": 0.0073},
    "source": "Planck 2018 results VI, A&A 641, A6 (2020), Table 2, TT,TE,EE+lowE+lensing",
    "M_Pl_GeV": {"value": 1.220890e19, "sigma": 0.000014e19, "source": "CODATA 2022 Planck mass, not reduced"},
    "hbar_GeV_s": {"value": 6.582119569509066e-25, "source": "exact in the SI (h and e fixed)"},
    "Mpc_m": {"value": 3.0856775814913673e22, "source": "IAU 2012/2015: au exact, pc = 648000/pi au"},
}


class BuildError(Exception):
    pass


def base(item: str, env: dict) -> dict:
    return {"schema_version": fr.SCHEMA, "item": item, "computed_by": COMPUTED_BY, **fr.run_info(env)}


def load_y4(root: Path):
    """This run's independent Y4 tensor (ugct_sage_y4/independent_y4_pushforward.py), or None."""
    path = root / Y4_TENSOR
    if not path.exists():
        return None
    d = json.loads(path.read_text())
    return d if d.get("status") == "INDEPENDENT_TENSOR_COMPUTED" and not d.get("failures") else None


def y4_missing_item() -> str:
    return (f"This run has no Y4 tensor ({Y4_TENSOR} from ugct_sage_y4/independent_y4_pushforward.py), so the "
            "Y4-derived numbers of this record were not computed.")


# ----------------------------------------------------------------------------------------------------------------
# prime race: delta(4;3,1) under GRH + LI
# ----------------------------------------------------------------------------------------------------------------

def prime_race_density(height: int) -> dict:
    """delta(4;3,1) = 1/2 + (1/pi) int_0^oo (sin t / t) prod_{gamma > 0} J0(2t / sqrt(1/4 + gamma^2)) dt
    (Rubinstein-Sarnak; GRH for L(s, chi_-4) and LI), with the zeros 0 < gamma <= T computed by PARI.

    The zeros above T are represented by exp(-S_T t^2) with S_T = sum_{gamma > T} 1/gamma^2 estimated from the zero
    density (1/2pi) log(q t / 2pi): S_T = (log(qT/2pi) + 1) / (2 pi T). The integral is cut at t_max = 26 pi; beyond it
    |integrand| <= prod |J0(t w_k)| / t is bounded with |J0(x)| <= sqrt(2/(pi x)) (x > 0), checked on a grid here."""
    import cypari2
    pari = cypari2.Pari()
    pari.default("parisizemax", 1000000000)
    pari.set_real_precision(19)
    q = 4
    L = pari("lfuncreate(-4)")
    zeros = pari.lfunzeros(L, height)
    half = pari("(Z, h) -> select(g -> g <= h, Z)")(zeros, height // 2)
    weights = pari("(Z) -> vector(#Z, k, 2/sqrt(1/4 + Z[k]^2))")
    intervals = 26
    integrate = pari("(W, S, J) -> 1/2 + sum(j = 0, J - 1, intnum(t = j*Pi, (j+1)*Pi, "
                     "if(t, sin(t)/t, 1) * prod(k = 1, #W, besselj(0, t*W[k])) * exp(-S*t^2)))/Pi")

    def s_tail(T):
        return (math.log(q * T / (2 * math.pi)) + 1) / (2 * math.pi * T)

    w, w_half = weights(zeros), weights(half)
    d_trunc = float(integrate(w, 0, intervals))
    d_corr = float(integrate(w, s_tail(height), intervals))
    d_corr_half = float(integrate(w_half, s_tail(height // 2), intervals))

    # tail of the t-integral beyond t_max, in log10
    t_max = intervals * math.pi
    ws = [float(x) for x in w]
    k_set = [x for x in ws if t_max * x >= 2 / math.pi]
    log10_c = sum(0.5 * math.log10(2 / (math.pi * t_max * x)) for x in k_set)
    log10_tail = log10_c - math.log10(len(k_set) / 2) - math.log10(math.pi) if k_set else 0.0
    bessel_grid_max = float(pari("my(M = 0); for(i = 1, 40000, my(x = i/100.); "
                                 "M = max(M, sqrt(Pi*x/2)*abs(besselj(0, x)))); M"))

    count = len(zeros)
    main_term = height / (2 * math.pi) * math.log(q * height / (2 * math.pi * math.e))
    drift = abs(d_corr - d_corr_half)
    err = 3 * drift + 10 ** log10_tail
    gammas = [float(zeros[i]) for i in range(min(3, count))]
    return {
        "height_T": height, "zero_count": count, "first_zeros": gammas,
        "zero_count_main_term": main_term, "pari_version": ".".join(str(x) for x in pari.version()),
        "zeros_source": f"PARI/GP lfunzeros(lfuncreate(-4), {height}) at 19 digits",
        "delta_with_zeros_up_to_T": d_trunc,
        "tail_sum_estimate_S_T": s_tail(height),
        "delta_tail_corrected": d_corr,
        "delta_tail_corrected_at_T_over_2": d_corr_half,
        "change_T_over_2_to_T": drift,
        "quadrature": f"PARI intnum on {intervals} intervals [j pi, (j+1) pi], 19 digits",
        "t_max": t_max, "log10_bound_beyond_t_max": log10_tail,
        "bessel_bound_grid_max": bessel_grid_max,
        "estimate": d_corr, "numerical_error_estimate": err,
        "estimate_interval": [d_corr - err, d_corr + err],
        "error_estimate_definition": "3 x |delta(T) - delta(T/2)| (tail-corrected) + bound beyond t_max; "
                                     "a numerical estimate, not an interval-arithmetic enclosure",
    }


def build_prime_race(root: Path, env: dict, height: int) -> tuple[dict, str]:
    res = prime_race_density(height)
    typed = json.loads((root / PRIME_TYPED).read_text())
    typed_iv = typed.get("density_interval") or {}
    lo_t, hi_t = float(typed_iv.get("lower", "nan")), float(typed_iv.get("upper", "nan"))
    checks = {
        "zero count within log(qT) of the main term": abs(res["zero_count"] - res["zero_count_main_term"])
                                                      <= math.log(4 * height),
        "first zero 6.0209... (L(s, chi_-4))": abs(res["first_zeros"][0] - 6.020948904697597) < 1e-9,
        "tail-corrected value stable from T/2 to T (change < 1e-4)": res["change_T_over_2_to_T"] < 1e-4,
        "|J0(x)| <= sqrt(2/(pi x)) on the grid (0, 400]": res["bessel_bound_grid_max"] <= 1.0,
        "reproduces Rubinstein-Sarnak 0.9959 (4 digits)":
            abs(res["estimate"] - RUBINSTEIN_SARNAK_DELTA_4_3_1) <= 5e-5 + res["numerical_error_estimate"],
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise BuildError(f"prime race: checks failed: {failed}")
    est, err = res["estimate"], res["numerical_error_estimate"]
    typed_compatible = lo_t <= est + err and est - err <= hi_t
    typed_finding = (f"The typed 'unconditional' interval [{lo_t}, {hi_t}] in {PRIME_TYPED} is "
                     + ("compatible with this value." if typed_compatible else
                        "incompatible with this value: if it held, GRH or LI would fail for chi_-4."))
    rec = base("prime_race", env)
    rec.update({
        "status": "PRIME_RACE_DENSITY_CONDITIONAL_ON_GRH_LI",
        "scope_category": "CONDITIONAL",
        "race": {"q": 4, "a": 3, "b": 1, "claim": "logarithmic density of x with pi(x;4,3) > pi(x;4,1)"},
        "hypotheses": ["GRH for L(s, chi_-4): every nontrivial zero has real part 1/2.",
                       "LI: the positive ordinates of those zeros are linearly independent over Q."],
        "grh_used": True, "linear_independence_used": True,
        "spectral_identification_verified": False, "polymer_hypotheses_verified": False,
        "results": res,
        "conditional_density_estimate": {"value": est, "numerical_error_estimate": err,
                                         "interval": [est - err, est + err]},
        "checks": checks,
        "findings": [
            f"Under GRH and LI, delta(4;3,1) = {est:.6f} (numerical error estimate {err:.1e}), reproducing "
            "Rubinstein-Sarnak (1994), 0.9959.",
            typed_finding,
            f"The manuscript's own record {PRIME_MANUSCRIPT} states that the prime-race density is conditional on GRH.",
        ],
        "open_items": ["An unconditional delta(4;3,1) > 1/2 needs a proof without GRH and LI; none is known, and the "
                       "typed certificate's spectral-identification and polymer flags have no computation behind them."],
        "derivations": [{"name": "conditional_density_estimate",
                         "formula": "1/2 + (1/pi) int_0^oo (sin t/t) prod_{0<gamma<=T} J0(2t/sqrt(1/4+gamma^2)) "
                                    "exp(-S_T t^2) dt",
                         "script": COMPUTED_BY, "inputs": [], "output_field": "conditional_density_estimate",
                         "rounding": "19-digit PARI arithmetic; numerical error estimate as stated"}],
        "theorem_dependencies": [{"name": "Rubinstein-Sarnak limiting distribution",
                                  "source": "Rubinstein and Sarnak, Experiment. Math. 3 (1994) 173-197",
                                  "hypotheses": "GRH and LI for L(s, chi_-4)",
                                  "hypothesis_check_map": "hypotheses (assumed, not checked)",
                                  "conclusion_used": "delta(4;3,1) = P(X > 0) with the stated characteristic function"},
                                 {"name": "Gil-Pelaez inversion", "source": "Gil-Pelaez, Biometrika 38 (1951) 481",
                                  "hypotheses": "X a real random variable with characteristic function phi",
                                  "hypothesis_check_map": "phi(t) = e^{it} prod J0(2t/|1/2 + i gamma|)",
                                  "conclusion_used": "P(X > 0) = 1/2 + (1/pi) int_0^oo Im phi(t)/t dt"}],
        "inputs": [fr.input_entry(root, PRIME_TYPED, "typed density interval, compared"),
                   fr.input_entry(root, PRIME_MANUSCRIPT, "manuscript's conditional statement, cited")],
        "replaces": "a typed VERIFIED certificate with density [0.50000037, 0.50000490] and grh_used = false",
    })
    fr.finalize(rec)
    tex = fr.record_tex(rec, "Prime race $\\delta(4;3,1)$: conditional record", [
        r"Under GRH and LI for $L(s,\chi_{-4})$ (Rubinstein--Sarnak),",
        r"\[\delta(4;3,1)=\tfrac12+\frac1\pi\int_0^\infty\frac{\sin t}{t}\prod_{\gamma>0}"
        r"J_0\!\Big(\frac{2t}{\sqrt{1/4+\gamma^2}}\Big)\,dt .\]",
        f"This run computes the {res['zero_count']} zeros with $0<\\gamma\\le{height}$ with PARI, represents the zeros "
        f"above $T$ by $e^{{-S_T t^2}}$, and finds $\\delta(4;3,1)={est:.6f}$ with numerical error estimate "
        f"${fr.tex_sci(err)}$ (not an interval enclosure). Rubinstein and Sarnak give $0.9959$. "
        "The result is conditional; no unconditional statement is made."])
    return rec, tex


# ----------------------------------------------------------------------------------------------------------------
# proton coefficient
# ----------------------------------------------------------------------------------------------------------------

def load_module(root: Path, rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, root / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_proton(root: Path, env: dict) -> tuple[dict, str]:
    mod = load_module(root, PROTON_MODULE, "proton_cp_published_lattice")
    rows, lam_ugct, lam_ugct_s, failures = mod.compute()
    if failures:
        raise BuildError(f"proton: {PROTON_MODULE} checks failed: {failures}")
    snap = mod.SNAPSHOT
    lo_m, hi_m = snap["manuscript"]["lattice_presentation_c_p"]
    table = [{"key": r["key"], "scheme": r["scheme"], "Lambda_MeV": r["Lambda_value_MeV"],
              "Lambda_sigma_MeV": r["Lambda_sigma_MeV"], "c_p": r["c_p"], "c_p_sigma": r["c_p_sigma"],
              "M_Pl_e^-44_over_Lambda": r["Lambda_UGCT_over_Lambda"], "pull_sigma": r["pull_sigma"]} for r in rows]
    overlap = [r["scheme"] for r in rows if r["c_p"] - 2 * r["c_p_sigma"] <= hi_m and r["c_p"] + 2 * r["c_p_sigma"] >= lo_m]
    mp, mps = snap["m_p_MeV"]["value"], snap["m_p_MeV"]["sigma"]
    findings = [
        f"M_Pl e^-44 = {lam_ugct:.2f}({lam_ugct_s:.2f}) MeV is " + "; ".join(
            f"{r['Lambda_UGCT_over_Lambda']:.2f} x Lambda of {r['scheme']} ({r['pull_sigma']:.0f} sigma)" for r in rows)
        + ": it is the Lambda parameter of none of these schemes.",
        f"The manuscript's c_p interval [{lo_m}, {hi_m}] ({PROTON_TYPED}) overlaps the 2-sigma published interval of "
        + (", ".join(overlap) if overlap else "no scheme in the table") + ".",
        f"m_p / (M_Pl e^-44) = {mp / lam_ugct:.6f} is the measured ratio, not a QCD computation.",
    ]
    inputs = [fr.input_entry(root, PROTON_MODULE, "published-value snapshot and computation"),
              fr.input_entry(root, PROTON_TYPED, "manuscript's c_p interval, compared")]
    rec = base("proton_cp", env)
    flag_dep = {"name": "FLAG 2024 averages of Lambda_MSbar", "source": "FLAG Review 2024, arXiv:2411.04268, Table 2",
                "hypotheses": "lattice results admitted by FLAG's continuum-limit, finite-volume and renormalization criteria",
                "hypothesis_check_map": "lattice_controls_basis",
                "conclusion_used": "Lambda_MSbar for N_f = 3, 4, 5 as published"}
    conversion_dep = {"name": "Lambda ratio between schemes",
                      "source": "Celmaster and Gonsalves, Phys. Rev. D 20 (1979) 1420",
                      "hypotheses": "alpha' = alpha (1 + a1 alpha/(4 pi) + ...)",
                      "hypothesis_check_map": "a1 = 31/3 - 10 n_f/9 (Fischler; Billoire)",
                      "conclusion_used": "Lambda'/Lambda = exp(a1/(2 beta0)) exactly"}
    rec.update({"per_scheme": table, "Lambda_UGCT_MeV": lam_ugct, "Lambda_UGCT_sigma_MeV": lam_ugct_s,
                "lattice_input_snapshot_sha256": mod.snapshot_sha256(), "findings": findings,
                "theorem_dependencies": [flag_dep, conversion_dep]})
    declared = root / PROTON_DECLARED
    if not declared.exists():
        rec.update({
            "status": "PROTON_CP_SCHEME_NOT_DECLARED", "scope_category": "OPEN",
            "continuum_extrapolation_verified": False, "finite_volume_error_bounded": False,
            "scale_setting_verified": False, "c_p_interval": None, "m_p_interval": None,
            "open_items": [f"Declare the scheme and number of flavours of Lambda_QCD = M_Pl e^-44 in {PROTON_DECLARED} "
                           "(keys: scheme, one of " + ", ".join(r["key"] for r in rows) + "; declared_by; declared_on; "
                           "statement). The record then takes the published c_p of that scheme (ledger C17).",
                           "Give a source for the exponent 44: chi(Y4)/24 of the stated construction is 127 (ledger T23)."],
            "inputs": inputs,
            "derivations": [{"name": "per_scheme", "formula": "c_p = m_p(CODATA) / Lambda(FLAG, scheme)",
                             "script": PROTON_MODULE, "inputs": [PROTON_MODULE], "output_field": "per_scheme",
                             "rounding": "double precision; first-order Gaussian error propagation"}],
        })
        fr.finalize(rec)
        tex = fr.record_tex(rec, "Proton coefficient $c_p$: record", [
            r"Published lattice QCD fixes $c_p=m_p/\Lambda$ once the scheme of $\Lambda$ is named "
            r"(\texttt{ugct\_formal/proton\_cp\_published\_lattice.py}: FLAG 2024 $\Lambda_{\overline{\rm MS}}$ for three, "
            r"four and five flavours and the static-potential scheme). The manuscript does not name the scheme of "
            r"$\Lambda_{\rm QCD}=M_{\rm Pl}e^{-44}$, so no certificate is issued.",
            r"\begin{itemize}"] + [f"\\item {fr.tex_escape(r['scheme'])}: $\\Lambda={r['Lambda_value_MeV']:.0f}"
                                   f"({r['Lambda_sigma_MeV']:.0f})$ MeV, $c_p={r['c_p']:.3f}\\pm{r['c_p_sigma']:.3f}$."
                                   for r in rows] + [r"\end{itemize}"])
        return rec, tex

    dec = json.loads(declared.read_text())
    keys = {r["key"]: r for r in rows}
    missing = [k for k in ("scheme", "declared_by", "declared_on", "statement") if not dec.get(k)]
    if missing or dec.get("scheme") not in keys:
        raise BuildError(f"proton: {PROTON_DECLARED} must name scheme (one of {sorted(keys)}), declared_by, "
                         f"declared_on and statement; missing or unknown: {missing or dec.get('scheme')}")
    r = keys[dec["scheme"]]
    c, s = r["c_p"], r["c_p_sigma"]
    if not dec["scheme"].startswith("V_"):
        rec["theorem_dependencies"] = [flag_dep]
    rec.update({
        "status": "VERIFIED_PROTON_CP_LATTICE_QCD", "scope_category": "VERIFIED",
        "declared_scheme": dec, "scheme": r["scheme"],
        "c_p": c, "c_p_sigma": s,
        "c_p_interval": {"lower": c - 2 * s, "upper": c + 2 * s},
        "m_p_interval": {"lower": mp - 2 * mps, "upper": mp + 2 * mps},
        "interval_coverage": "value +- 2 sigma, first-order Gaussian propagation of independent errors",
        "continuum_extrapolation_verified": True, "finite_volume_error_bounded": True, "scale_setting_verified": True,
        "lattice_controls_basis": "FLAG Review 2024 averages, which admit only results meeting FLAG's continuum-limit, "
                                  "finite-volume and renormalization criteria; this record imports the published "
                                  "average and runs no lattice computation",
        "comparison": {"Lambda_UGCT_MeV": lam_ugct, "Lambda_scheme_MeV": r["Lambda_value_MeV"],
                       "ratio": r["Lambda_UGCT_over_Lambda"], "pull_sigma": r["pull_sigma"],
                       "predicted_m_p_MeV": c * lam_ugct, "measured_m_p_MeV": mp},
        "open_items": [],
        "inputs": inputs + [fr.input_entry(root, PROTON_DECLARED, "declared scheme of Lambda_QCD")],
        "derivations": [{"name": "c_p_interval", "formula": "c_p = m_p / Lambda_scheme, interval c_p +- 2 sigma",
                         "script": PROTON_MODULE, "inputs": [PROTON_MODULE, PROTON_DECLARED],
                         "output_field": "c_p_interval", "rounding": "double precision"}],
        "verification_rule": "verified when the scheme of Lambda_QCD is declared and the published continuum-limit "
                             "lattice value of Lambda in that scheme and the CODATA proton mass are used as published",
    })
    rec["findings"].append(f"With the declared scheme ({r['scheme']}) the prediction m_p = c_p M_Pl e^-44 = "
                           f"{c * lam_ugct:.0f} MeV against the measured {mp:.3f} MeV.")
    if dec.get("sealed_before_comparison") is not True:
        rec["findings"].append(f"The scheme was declared on {dec['declared_on']} by {dec['declared_by']}, after the "
                               "per-scheme comparison with M_Pl e^-44 was known, so that comparison does not meet the "
                               "freeze gate G8; what this record certifies is the published c_p in the declared scheme.")
    fr.finalize(rec)
    return rec, proton_verified_tex(rec, r, dec)


def proton_verified_tex(rec: dict, r: dict, dec: dict) -> str:
    c, s = rec["c_p"], rec["c_p_sigma"]
    lo, hi = rec["c_p_interval"]["lower"], rec["c_p_interval"]["upper"]
    e = fr.tex_escape
    return "\n".join([
        r"\section*{Proton coefficient $c_p$ from published lattice QCD}",
        f"Generated by \\texttt{{{e(COMPUTED_BY)}}} in run {e(rec['source_workflow_run_id'])}. "
        f"Scope: \\texttt{{VERIFIED}}. Status: \\texttt{{{e(rec['status'])}}}.",
        r"\subsection*{Fixed data and hypotheses}",
        f"The scheme of $\\Lambda_{{\\rm QCD}}$ is declared in \\texttt{{{e(PROTON_DECLARED)}}} by {e(dec['declared_by'])} "
        f"on {e(dec['declared_on'])}: {e(dec['statement'])} Inputs, used as published: $m_p=938.27208943(29)$ MeV "
        f"(CODATA 2022) and $\\Lambda={r['Lambda_value_MeV']:.1f}({r['Lambda_sigma_MeV']:.1f})$ MeV in the scheme "
        f"{e(r['scheme'])} (FLAG Review 2024, arXiv:2411.04268, Table 2, with the exact scheme conversion below for the "
        r"static-potential scheme). The errors of $m_p$ and $\Lambda$ are independent.",
        r"\subsection*{Definitions}",
        r"The proton coefficient is $c_p=m_p/\Lambda$ in the declared scheme. For independent Gaussian errors the "
        r"first-order standard deviation of a ratio is",
        r"\[\sigma_{c_p}=c_p\sqrt{(\sigma_{m_p}/m_p)^2+(\sigma_\Lambda/\Lambda)^2}.\]",
        r"\subsection*{Lemmas used}",
        r"\begin{lemma}[Scheme conversion]\label{lem:pcp-scheme}",
        r"If $a'=a(1+c_1a+O(a^2))$ with $a=\alpha_s/(4\pi)$ and $\mu\,da/d\mu=-2\beta_0a^2+O(a^3)$, then "
        r"$\Lambda'/\Lambda=\exp(c_1/(2\beta_0))$ exactly.",
        r"\end{lemma}",
        r"\begin{proof}",
        r"Write $\Lambda=\mu\exp(-1/(2\beta_0a))(\beta_0a)^{-\beta_1/(2\beta_0^2)}(1+O(a))$. Since "
        r"$1/a'=1/a-c_1+O(a)$, the exponential factors differ by $\exp(c_1/(2\beta_0))$ and the power-law factors by "
        r"$1+O(a)$. Both $\Lambda$ and $\Lambda'$ are independent of $\mu$, so letting $\mu\to\infty$ ($a\to0$) gives "
        r"the ratio exactly. For the static potential $c_1=a_1=31/3-10n_f/9$ and $\beta_0=11-2n_f/3$; for $n_f=3$ "
        r"the ratio is $e^{7/18}$.",
        r"\end{proof}",
        r"\begin{lemma}[Ratio interval]\label{lem:pcp-ratio}",
        r"With the definitions above, $c_p\pm2\sigma_{c_p}$ is the two-standard-deviation interval of $m_p/\Lambda$ to "
        r"first order in the relative errors.",
        r"\end{lemma}",
        r"\begin{proof}",
        r"Linearize $\log c_p=\log m_p-\log\Lambda$: the variances of independent terms add, so "
        r"$(\sigma_{c_p}/c_p)^2=(\sigma_{m_p}/m_p)^2+(\sigma_\Lambda/\Lambda)^2$; here the second term dominates by "
        r"more than six orders of magnitude.",
        r"\end{proof}",
        r"\subsection*{Certificate theorem}",
        r"\begin{theorem}",
        f"In the declared scheme, $c_p={c:.4f}\\pm{s:.4f}$, so $c_p\\in[{lo:.4f},{hi:.4f}]$ at two standard deviations.",
        r"\end{theorem}",
        r"\begin{proof}",
        r"Divide the published values (Lemma~\ref{lem:pcp-scheme} for the scheme conversion, if any) and apply "
        r"Lemma~\ref{lem:pcp-ratio}.",
        r"\end{proof}",
        f"Comparison (reported, not part of the theorem): $M_{{\\rm Pl}}e^{{-44}}={rec['comparison']['Lambda_UGCT_MeV']:.2f}$ "
        f"MeV is {rec['comparison']['ratio']:.3f} times $\\Lambda$ of this scheme, and $c_p M_{{\\rm Pl}}e^{{-44}}="
        f"{rec['comparison']['predicted_m_p_MeV']:.0f}$ MeV against the measured $m_p$. The same published inputs give, "
        r"for each scheme the snapshot covers:",
        r"\begin{itemize}"] + [
        f"\\item {e(row['scheme'])}: $\\Lambda={row['Lambda_MeV']:.0f}({row['Lambda_sigma_MeV']:.0f})$ MeV, "
        f"$c_p={row['c_p']:.3f}\\pm{row['c_p_sigma']:.3f}$, $M_{{\\rm Pl}}e^{{-44}}/\\Lambda="
        f"{row['M_Pl_e^-44_over_Lambda']:.2f}$." for row in rec["per_scheme"]] + [
        r"\end{itemize}",
        r"\subsection*{Certificate-field map}",
        r"The workflow checks that \texttt{c\_p\_interval} and \texttt{m\_p\_interval} are positive, that the three "
        r"lattice-control flags are set (they record that the imported FLAG averages satisfy FLAG's criteria; no lattice "
        r"run is made here), that \texttt{lattice\_input\_snapshot\_sha256} is present, and that the payload hash, run "
        r"identifier and input hashes match.",
        r"\subsection*{Independent falsification conditions}",
        r"The record is wrong if the published inputs differ from the snapshot in "
        r"\texttt{ugct\_formal/proton\_cp\_published\_lattice.py}, if the declared scheme is not the scheme of the "
        r"manuscript's $\Lambda_{\rm QCD}$, or if recomputing $m_p/\Lambda$ gives values outside the interval.",
    ]) + "\n"


# ----------------------------------------------------------------------------------------------------------------
# Pfaffian
# ----------------------------------------------------------------------------------------------------------------

def chi_od_table(y4: dict) -> dict:
    """chi(O_D) = -(D^4 + c2 . D^2)/24 for each basis divisor D of a CY4 (Riemann-Roch with c1 = 0)."""
    q = {tuple(k.split(",")): Fraction(v) for k, v in y4["quadruple_intersections"].items()}
    c2 = {tuple(k.split(",")): Fraction(v) for k, v in y4["c2_pairings"].items()}
    out = {}
    for d in y4["basis"]:
        d4, c2d2 = q.get((d, d, d, d), Fraction(0)), c2.get((d, d), Fraction(0))
        out[d] = {"D4": str(d4), "c2_D2": str(c2d2), "chi_O_D": str(-(d4 + c2d2) / 24)}
    return out


def p1_cohomology(d: int) -> tuple[int, int]:
    """(h^0, h^1) of O(d) on P^1."""
    return max(d + 1, 0), max(-d - 1, 0)


def hirzebruch_cohomology(n: int, a: int, b: int) -> tuple[int, int, int]:
    """(h^0, h^1, h^2) of O(a C0 + b f) on the Hirzebruch surface F_n (C0^2 = -n, C0.f = 1, f^2 = 0).
    For a >= 0, pi_* O(a C0 + b f) = sum_{k=0..a} O(b - k n) on P^1 and R^1 pi_* = 0; for a = -1 every group vanishes;
    for a <= -2 Serre duality with K = -2 C0 - (n + 2) f reduces to the first case."""
    if a >= 0:
        parts = [p1_cohomology(b - k * n) for k in range(a + 1)]
        return sum(x[0] for x in parts), sum(x[1] for x in parts), 0
    if a == -1:
        return 0, 0, 0
    d0, d1, d2 = hirzebruch_cohomology(n, -2 - a, -(n + 2) - b)
    return d2, d1, d0


# The basis divisors E1..E8 of the Y4 tensor are the pullbacks of the exceptional curves e_i of S = dP8 (e_i^2 = -1,
# K_S.e_i = -1) through B3 = P(O + K_S) -> S: vertical divisors over F_i = P(O + K_S|e_i), a Hirzebruch surface F_1.
VERTICAL_OVER_CURVES = {f"E{i}": {"curve": f"e_{i}", "self_intersection": -1, "K_S_degree": -1} for i in range(1, 9)}


def vertical_rigidity(name: str, curve: dict, d4: Fraction, c2d2: Fraction) -> dict:
    """h^{0,p} of the vertical divisor D = pi^{-1}(F) over F = P(O + K_S|c) for a smooth rational curve c in S, from the
    Leray spectral sequence with pi_* O = O and R^1 pi_* O = K_B3 restricted to F:
        h^{0,p}(D) = h^p(F, O_F) + h^{p-1}(F, K_B3|F),  K_B3|F = K_F - N_F = -2 C0 - (n + 2 + s) f,
    with n = |K_S.c|, s = c^2 and N_F = s f. Cross-checks against the tensor: D^4 = 0, c2.D^2 = 12 c1(B3).F.F = 24 s
    and chi(O_D) = sum (-1)^p h^{0,p}."""
    n, s_ = abs(curve["K_S_degree"]), curve["self_intersection"]
    kb = (-2, -(n + 2 + s_))
    o_f = hirzebruch_cohomology(n, 0, 0)
    h = hirzebruch_cohomology(n, *kb)
    h0p = [o_f[0], o_f[1] + h[0], o_f[2] + h[1], h[2]]
    chi = h0p[0] - h0p[1] + h0p[2] - h0p[3]
    return {"base_surface": f"F_{n} = P(O + K_S|{curve['curve']}) in B3", "K_B3_on_F_C0_f": list(kb),
            "h0p": h0p, "rigid": h0p == [1, 0, 0, 0], "chi_from_h0p": chi,
            "chi_from_tensor": str(-(d4 + c2d2) / 24), "D4_tensor": str(d4), "c2_D2_tensor": str(c2d2),
            "c2_D2_from_base": 24 * s_}


def build_pfaffian(root: Path, env: dict, y4) -> tuple[dict, str]:
    typed = json.loads((root / PFAFFIAN_TYPED).read_text())
    fb = typed.get("finite_block") or {}
    lo, hi = (Fraction(str(x)) for x in fb.get("pfaffian_interval", [0, 0]))
    rad = Fraction(str(fb.get("collar_variation_radius", 0))) + Fraction(str(fb.get("spectral_tail_radius", 0)))
    final = [float(lo - rad), float(hi + rad)]
    arithmetic_ok = final == [float(Fraction(str(x))) for x in fb.get("final_interval", [0, 0])]
    rec = base("pfaffian", env)
    findings = [f"The typed file's final_interval {fb.get('final_interval')} is its pfaffian_interval "
                f"{fb.get('pfaffian_interval')} widened by the two recorded radii (arithmetic "
                f"{'rechecked' if arithmetic_ok else 'does not match'}); the pfaffian_interval itself has no operator "
                "data behind it: the file holds no matrix entries, eigenvalues or determinant computation."]
    inputs = [fr.input_entry(root, PFAFFIAN_TYPED, "typed operator summary, checked")]
    checks = {"typed final_interval = pfaffian_interval widened by the radii": arithmetic_ok}
    results = {}
    open_items = ["Define the fluctuation operator of the instanton on its divisor and compute its primed Pfaffian "
                  "(determinant) with a fixed determinant-line normalization; no such operator or computation is in "
                  "the repository, and the typed zero-mode and collar-independence flags have nothing behind them."]
    if y4:
        table = chi_od_table(y4)
        ones = [d for d, v in table.items() if v["chi_O_D"] == "1"]
        integral = all(Fraction(v["chi_O_D"]).denominator == 1 for v in table.values())
        checks["chi(O_D) integral for every basis divisor"] = integral
        results = {"chi_O_D": table, "divisors_with_chi_1": ones,
                   "formula": "chi(O_D) = -(D^4 + c2(Y4) D^2)/24 (Riemann-Roch on a Calabi-Yau fourfold)"}
        findings.append(f"From this run's Y4 tensor, chi(O_D) = 1 (Witten's necessary condition for an instanton "
                        f"contribution) holds for {', '.join(ones)}; it is necessary, not sufficient.")
        inputs.append(fr.input_entry(root, Y4_TENSOR, "this run's Y4 intersection tensor"))
        if not integral:
            raise BuildError("pfaffian: chi(O_D) is not an integer for some basis divisor")
        q = {tuple(k.split(",")): Fraction(v) for k, v in y4["quadruple_intersections"].items()}
        c2 = {tuple(k.split(",")): Fraction(v) for k, v in y4["c2_pairings"].items()}
        rig = {d: vertical_rigidity(d, VERTICAL_OVER_CURVES[d], q.get((d, d, d, d), Fraction(0)),
                                    c2.get((d, d), Fraction(0))) for d in y4["basis"] if d in VERTICAL_OVER_CURVES}
        if rig:
            results["vertical_divisor_rigidity"] = rig
            consistent = all(r["D4_tensor"] == "0" and r["c2_D2_tensor"] == str(r["c2_D2_from_base"])
                             and r["chi_from_tensor"] == str(r["chi_from_h0p"]) for r in rig.values())
            checks["E_i: D^4 = 0, c2.D^2 = 12 c1(B3).F.F and chi(O_D) = sum (-1)^p h^{0,p}, from the tensor"] = consistent
            if not consistent:
                raise BuildError("pfaffian: the vertical-divisor geometry disagrees with this run's tensor: "
                                 + json.dumps(rig))
            rigid = [d for d, r in rig.items() if r["rigid"]]
            findings.append(
                f"{', '.join(rigid)} are the vertical divisors over the surfaces F_i = P(O + K_S|e_i) = F_1 of B3. With "
                "R^1 pi_* O = K_B3 (Leray), h^{0,p}(E_i) = h^p(O_F) + h^{p-1}(F, K_B3|F) = (1, 0, 0, 0), because "
                "K_B3|F = -2 C0 - 2 f has no cohomology: each is rigid in Witten's sense, assuming the fibration over F_i "
                "is flat with E_i smooth. The same holds over each of the 240 (-1)-curves of dP8. Each F_i meets the GUT "
                "divisor along e_i, so these instantons intersect the SU(5) stack. Z and C1-C4 also have chi = 1 but are "
                "not vertical, so they are not D3-instanton candidates in the F-theory limit.")
            open_items.append("Count the charged zero modes on the curves e_i where F_i meets the GUT divisor; they "
                              "depend on the gauge flux restricted to e_i, which the model does not specify.")
        else:
            open_items.append("Compute h^{0,i}(D) for the candidate divisors; chi(O_D) = 1 does not by itself make D "
                              "rigid.")
    else:
        open_items.append(y4_missing_item())
    rec.update({"status": "PFAFFIAN_NORMALIZATION_OPEN", "scope_category": "OPEN",
                "zero_modes_removed": False, "collar_independence_verified": False, "pfaffian_interval": None,
                "results": results, "checks": checks, "findings": findings, "open_items": open_items,
                "inputs": inputs,
                "derivations": ([{"name": "chi_O_D", "formula": "-(D^4 + c2 D^2)/24", "script": COMPUTED_BY,
                                  "inputs": [Y4_TENSOR], "output_field": "results.chi_O_D",
                                  "rounding": "exact rational arithmetic"}]
                                + ([{"name": "vertical_divisor_rigidity",
                                     "formula": "h^{0,p}(D) = h^p(O_F) + h^{p-1}(F, K_B3|F) on F_1",
                                     "script": COMPUTED_BY, "inputs": [Y4_TENSOR],
                                     "output_field": "results.vertical_divisor_rigidity",
                                     "rounding": "exact integer arithmetic"}] if results.get("vertical_divisor_rigidity")
                                   else [])) if y4 else [],
                "replaces": "a typed VERIFIED certificate with Pfaffian interval [0.997, 1.003]"})
    fr.finalize(rec)
    rows = [f"\\item ${fr.tex_escape(d)}$: $D^4={v['D4']}$, $c_2D^2={v['c2_D2']}$, $\\chi(\\mathcal O_D)={v['chi_O_D']}$."
            for d, v in (results.get("chi_O_D") or {}).items()]
    tex = fr.record_tex(rec, "Instanton Pfaffian normalization: record", [
        "No instanton operator is defined in the repository, so no Pfaffian is computed and no certificate is issued.",
        r"From this run's $Y_4$ tensor, $\chi(\mathcal O_D)=-(D^4+c_2D^2)/24$ for the basis divisors:" if rows else "",
    ] + ([r"\begin{itemize}"] + rows + [r"\end{itemize}"] if rows else []))
    return rec, tex


# ----------------------------------------------------------------------------------------------------------------
# uplift
# ----------------------------------------------------------------------------------------------------------------

def interval_matrix_min_eigenvalue(m) -> tuple[float, float]:
    """For a symmetric 2x2 interval matrix [[a, b], [b, c]]: the smallest eigenvalue over the box (lambda_min is concave
    in the entries, so its minimum is at a vertex) and the Gershgorin lower bound."""
    a = [Fraction(str(m[0][0]["lower"])), Fraction(str(m[0][0]["upper"]))]
    b = [Fraction(str(m[0][1]["lower"])), Fraction(str(m[0][1]["upper"]))]
    c = [Fraction(str(m[1][1]["lower"])), Fraction(str(m[1][1]["upper"]))]
    if [m[1][0]["lower"], m[1][0]["upper"]] != [m[0][1]["lower"], m[0][1]["upper"]]:
        raise BuildError("uplift: the typed Hessian is not symmetric")
    vals = []
    for x in a:
        for y in b:
            for z in c:
                mean, half = (x + z) / 2, (x - z) / 2
                vals.append(float(mean) - math.sqrt(float(half * half + y * y)))
    bmax = max(abs(b[0]), abs(b[1]))
    gersh = float(min(a[0] - bmax, c[0] - bmax))
    return min(vals), gersh


def build_uplift(root: Path, env: dict, y4) -> tuple[dict, str]:
    typed = json.loads((root / UPLIFT_TYPED).read_text())
    lam, gersh = interval_matrix_min_eigenvalue(typed["interval_hessian_matrix"])
    stated = float(typed.get("hessian_lambda_min_lower"))
    needed = ["data_room/data/racetrack_superpotential.json", "data_room/data/kahler_potential_nlo.json"]
    absent = [p for p in needed if not (root / p).exists()]
    checks = {"stated lambda_min_lower <= smallest eigenvalue over the typed interval matrix": stated <= lam,
              "stated lambda_min_lower <= Gershgorin bound of the typed matrix": stated <= gersh}
    results = {"typed_matrix_lambda_min": lam, "typed_matrix_gershgorin_lower": gersh,
               "stated_lambda_min_lower": stated, "inputs_of_kahler_stabilize_absent": absent}
    v = typed.get("V_phys_interval") or {}
    findings = [
        "The interval Hessian entries are typed: the file holds no effective potential, no moduli values and no "
        "derivative computation, so the matrix cannot be recomputed.",
        f"On the typed matrix the smallest eigenvalue over the interval box is {lam:.5f} and Gershgorin gives "
        f"{gersh:.5f}; both are consistent with the stated {stated}, as arithmetic on typed numbers only.",
        f"V_phys_interval [{v.get('lower')}, {v.get('upper')}] is the same pair of numbers as the typed "
        "cosmological-constant interval; it is not computed from a potential.",
    ]
    open_items = ["Write the effective potential from the stated flux, Kahler and uplift data and compute the critical "
                  "point (Krawczyk) and the interval Hessian from it; the gradient bound, Krawczyk radius and boundary "
                  "gap in the typed file are typed."]
    if absent:
        open_items.append("data_room/scripts/kahler_stabilize.py needs " + " and ".join(absent) + ", which do not exist.")
    inputs = [fr.input_entry(root, UPLIFT_TYPED, "typed interval Hessian, checked")]
    if y4:
        results["d3_tadpole_chi_over_24"] = int(y4["d3_tadpole_chi_over_24"])
        findings.append(f"The D3 tadpole of this run's Y4 is chi(Y4)/24 = {y4['d3_tadpole_chi_over_24']}; the "
                        "cosmology payload lists tadpole_bound_44 as an upstream dependency.")
        inputs.append(fr.input_entry(root, Y4_TENSOR, "this run's Y4 intersection tensor (tadpole)"))
    else:
        open_items.append(y4_missing_item())
    rec = base("uplift", env)
    rec.update({"status": "UPLIFT_STABILITY_OPEN", "scope_category": "OPEN",
                "compact_window_verified": False, "backreaction_terms_included": False,
                "results": results, "checks": checks, "findings": findings, "open_items": open_items,
                "inputs": inputs,
                "derivations": [{"name": "typed_matrix_lambda_min",
                                 "formula": "min over the 8 vertices of (a+c)/2 - sqrt(((a-c)/2)^2 + b^2)",
                                 "script": COMPUTED_BY, "inputs": [UPLIFT_TYPED],
                                 "output_field": "results.typed_matrix_lambda_min",
                                 "rounding": "exact rationals, one square root in double precision"}],
                "replaces": "a typed VERIFIED certificate with Hessian lower bound 0.031 and V in [1.04, 1.38]e-122"})
    fr.finalize(rec)
    tex = fr.record_tex(rec, "Uplift stability: record", [
        "No effective potential is in the repository, so there is no critical point or Hessian to compute and no "
        "certificate is issued. The checks below are arithmetic on the typed matrix."])
    return rec, tex


# ----------------------------------------------------------------------------------------------------------------
# cosmological constant
# ----------------------------------------------------------------------------------------------------------------

def observed_rho_lambda() -> dict:
    s = COSMO_SNAPSHOT
    h0 = s["H0_km_s_Mpc"]["value"] * 1e3 / s["Mpc_m"]["value"] * s["hbar_GeV_s"]["value"]      # GeV
    mpl, ol = s["M_Pl_GeV"]["value"], s["Omega_Lambda"]["value"]
    rho = 3 * ol * (h0 / mpl) ** 2 / (8 * math.pi)                                                 # units of M_Pl^4
    rel = math.sqrt((2 * s["H0_km_s_Mpc"]["sigma"] / s["H0_km_s_Mpc"]["value"]) ** 2
                    + (s["Omega_Lambda"]["sigma"] / ol) ** 2 + (2 * s["M_Pl_GeV"]["sigma"] / mpl) ** 2)
    return {"rho_over_M_Pl4": rho, "relative_sigma_uncorrelated": rel,
            "rho_over_reduced_M_P4": rho * (8 * math.pi) ** 2,
            "rho_quarter_meV": rho ** 0.25 * mpl * 1e12,
            "formula": "rho_Lambda / M_Pl^4 = 3 Omega_Lambda (hbar H0 / M_Pl)^2 / (8 pi)",
            "note": "uncorrelated propagation; the Planck fit correlates H0 and Omega_Lambda, so this overstates the error"}


def build_cosmological_constant(root: Path, env: dict, y4, uplift: dict | None) -> tuple[dict, str]:
    typed = json.loads((root / COSMO_TYPED).read_text())
    terms = typed["interval_terms"]
    centre = sum(Fraction(str(t["center"])) for t in terms)
    radius = sum(Fraction(str(t["radius"])) for t in terms)
    msum = [float(centre - radius), float(centre + radius)]
    st = typed["rho_lambda_interval"]
    s_lo, s_hi = float(st["lower"]), float(st["upper"])
    obs = observed_rho_lambda()
    rho = obs["rho_over_M_Pl4"]
    ln24 = math.log(24)
    top44 = math.exp(-6 * 44 - 6 * ln24)
    results = {"minkowski_sum_of_typed_terms": msum, "stated_interval": [s_lo, s_hi],
               "stated_equals_sum": msum == [s_lo, s_hi],
               "stated_contains_sum": s_lo <= msum[0] and msum[1] <= s_hi,
               "observed": obs, "observed_snapshot": COSMO_SNAPSHOT,
               "stated_lower_over_observed": s_lo / rho,
               "observed_in_stated_interval_M_Pl": s_lo <= rho <= s_hi,
               "observed_in_stated_interval_reduced": s_lo <= obs["rho_over_reduced_M_P4"] <= s_hi,
               "formula_P10": "rho_Lambda = M_Pl^4 e^(-6N) / 24^6",
               "formula_P10_N44": top44, "formula_P10_N44_over_observed": top44 / rho}
    findings = [
        f"The stated interval [{s_lo}, {s_hi}] is not the Minkowski sum of the six listed terms "
        f"([{msum[0]:.4e}, {msum[1]:.4e}]); it is wider, so 'Minkowski interval enclosure' does not describe it.",
        f"The observed rho_Lambda = {rho:.4e} M_Pl^4 ({obs['rho_over_reduced_M_P4']:.3e} in reduced Planck units; "
        f"rho^(1/4) = {obs['rho_quarter_meV']:.3f} meV) lies outside the stated interval in either convention: the "
        f"stated lower end is {s_lo / rho:.1f} times the observed value.",
        f"M_Pl^4 e^(-6N)/24^6 with N = 44 gives {top44:.4e} M_Pl^4, {100 * (top44 / rho - 1):+.1f}% from the observed "
        "value.",
    ]
    open_items = ["Compute the vacuum energy from a stabilized potential, each of the six terms from its own "
                  "computation; the six centres and radii are typed, and the uplift item it depends on is open."]
    inputs = [fr.input_entry(root, COSMO_TYPED, "typed interval terms, checked")]
    if y4:
        n = int(y4["d3_tadpole_chi_over_24"])
        log10_top = (-6 * n - 6 * ln24) / math.log(10)
        results.update({"d3_tadpole_chi_over_24": n, "formula_P10_N_chi_over_24_log10": log10_top})
        findings.append(f"N = 44 is not chi(Y4)/24 = {n} of this run's tensor; with N = {n} the formula gives "
                        f"10^{log10_top:.1f} M_Pl^4.")
        open_items.append("Derive the exponent of the topological formula; 6 x 44 = 264 has no source in Y4 "
                          f"(chi/24 = {n}).")
        inputs.append(fr.input_entry(root, Y4_TENSOR, "this run's Y4 intersection tensor (tadpole)"))
    else:
        open_items.append(y4_missing_item())
    dep = {"item": "uplift", "certificate": fr.ITEMS["uplift"][0],
           "scope_category": (uplift or {}).get("scope_category"), "status": (uplift or {}).get("status")}
    rec = base("cosmological_constant", env)
    rec.update({"status": "COSMOLOGICAL_CONSTANT_INTERVAL_OPEN", "scope_category": "OPEN",
                "depends_on_uplift_certificate": dep["status"], "dependency": dep,
                "all_uncertainties_propagated": False, "rho_lambda_interval": None,
                "results": results, "findings": findings, "open_items": open_items, "inputs": inputs,
                "derivations": [{"name": "minkowski_sum_of_typed_terms", "formula": "[sum c - sum r, sum c + sum r]",
                                 "script": COMPUTED_BY, "inputs": [COSMO_TYPED],
                                 "output_field": "results.minkowski_sum_of_typed_terms",
                                 "rounding": "exact rationals from the decimal strings"},
                                {"name": "observed", "formula": obs["formula"], "script": COMPUTED_BY, "inputs": [],
                                 "output_field": "results.observed", "rounding": "double precision"}],
                "replaces": "a typed VERIFIED certificate with rho_Lambda in [1.04, 1.38]e-122"})
    fr.finalize(rec)
    tex = fr.record_tex(rec, "Cosmological constant: record", [
        r"The typed payload states $\rho_\Lambda\in[1.04,1.38]\cdot10^{-122}$ as a Minkowski sum of six interval terms. "
        f"This run sums the terms ($[{msum[0]:.4e},{msum[1]:.4e}]$), computes the observed value "
        f"$\\rho_\\Lambda={rho:.4e}\\,M_{{\\rm Pl}}^4$ from Planck 2018 $H_0$ and $\\Omega_\\Lambda$, and evaluates "
        r"$M_{\rm Pl}^4e^{-6N}/24^6$. No certificate is issued: the uplift item it depends on is open."])
    return rec, tex


# ----------------------------------------------------------------------------------------------------------------
# Hadamard divisor
# ----------------------------------------------------------------------------------------------------------------

def build_hadamard(root: Path, env: dict) -> tuple[dict, str]:
    text = (root / HADAMARD_TYPED).read_text()
    data_markers = [m for m in ("pmatrix", "bmatrix", "tabular", "array") if m in text]
    rec = base("hadamard_divisor", env)
    rec.update({
        "status": "HADAMARD_DIVISOR_IDENTIFICATION_OPEN", "scope_category": "OPEN",
        **{k: False for k in ("xi_divisor_identified", "nonvanishing_factor_verified", "no_spurious_zeros_verified",
                              "hurwitz_transfer_verified", "h2_tail_graph_norm_verified",
                              "parity_gap_persistence_verified")},
        "results": {"primary_artifact_matrix_or_table_markers": data_markers},
        "findings": [
            "The manuscript states that F_infty = c Xi, the identification this item asserts, would with its other "
            "inputs prove the Riemann hypothesis, and that it cannot be introduced as an unstated imported theorem, a "
            "numerical certificate or a convention (UGCT Principia post-review 5, 'No-hidden-input theorem for the "
            "global arithmetic bridge').",
            f"The primary artifact {HADAMARD_TYPED} states the criterion in prose; it defines no operator K_Lambda(s) "
            f"and holds {'no' if not data_markers else 'some'} matrix or table data; the tail bound 4e-13 and parity gap "
            "2.8e-6 of the typed certificate have no computation behind them.",
        ],
        "open_items": ["Construct K_Lambda(s) and prove det_reg(I + K_infty(s)) = E(s) Xi(s) with E zero-free on the "
                       "transfer strip; by the manuscript's own theorem this is a route to the Riemann hypothesis."],
        "inputs": [fr.input_entry(root, HADAMARD_TYPED, "typed primary artifact, read")],
        "derivations": [],
        "replaces": "a typed VERIFIED certificate with six true flags",
    })
    fr.finalize(rec)
    tex = fr.record_tex(rec, "Hadamard divisor identification: record", [
        r"The claimed identity is $\det_{\rm reg}(I+K_\infty(s))=E(s)\Xi(s)$ with $E$ zero-free on the transfer strip. "
        r"No operator $K_\Lambda(s)$ is defined in the repository, so nothing can be computed, and no certificate is "
        r"issued."])
    return rec, tex


# ----------------------------------------------------------------------------------------------------------------
# Y4 record for workflows without Sage
# ----------------------------------------------------------------------------------------------------------------

def build_y4_not_built(root: Path, env: dict, y4) -> tuple[dict, str]:
    rec = base("y4_tensor", env)
    rec.update({"status": "Y4_TENSOR_NOT_BUILT_IN_THIS_WORKFLOW", "scope_category": "OPEN",
                "full_chamber_specific_tensor_verified": False,
                "built_by": "ugct_sage_y4/build_y4_tensor_manifest.py in .github/workflows/ugct-sage-y4.yml",
                "open_items": ["The verification criterion (the Sage tensor and the independent exact pushforward agree "
                               "on every degree-four monomial) is checked by ugct_sage_y4/build_y4_tensor_manifest.py "
                               "in ugct-sage-y4.yml; this workflow has no Sage."],
                "inputs": [], "derivations": []})
    if y4:
        rec.update({"nonzero_quadruple_intersections": int(y4["nonzero_count"]),
                    "results": {k: y4.get(k) for k in ("chi_Y4", "d3_tadpole_chi_over_24", "int_c2_squared",
                                                      "nonzero_count", "total_degree4_monomials")},
                    "checks": {k: y4["checks"].get(k) for k in ("chi_matches_published_formula", "todd_genus",
                                                               "riemann_roch_failures", "calabi_yau_condition")},
                    "inputs": [fr.input_entry(root, Y4_TENSOR, "this run's independent Y4 tensor")]})
        rec["findings"] = [f"The independent exact pushforward ran in this run: chi(Y4) = {y4['chi_Y4']}, chi/24 = "
                           f"{y4['d3_tadpole_chi_over_24']}, {y4['nonzero_count']} nonzero quadruple intersections."]
    else:
        rec["open_items"].append(y4_missing_item())
    fr.finalize(rec)
    tex = fr.record_tex(rec, "Y4 tensor: record for a workflow without Sage", [
        "This workflow does not run Sage, so it does not build the Y4 manifest; the manifest is built and checked in "
        "the Sage Y4 workflow."])
    return rec, tex


BUILDERS = ("prime_race", "proton_cp", "pfaffian", "uplift", "cosmological_constant", "hadamard_divisor")


def build_all(root: Path, env: dict, only=None, height: int = 400) -> dict:
    only = list(only or BUILDERS)
    y4 = load_y4(root)
    out = {}
    if "prime_race" in only:
        out["prime_race"] = build_prime_race(root, env, height)
    if "proton_cp" in only:
        out["proton_cp"] = build_proton(root, env)
    if "pfaffian" in only:
        out["pfaffian"] = build_pfaffian(root, env, y4)
    if "uplift" in only or "cosmological_constant" in only:
        out["uplift"] = build_uplift(root, env, y4)                # the cosmology record depends on it
    if "cosmological_constant" in only:
        out["cosmological_constant"] = build_cosmological_constant(root, env, y4, out["uplift"][0])
    if "hadamard_divisor" in only:
        out["hadamard_divisor"] = build_hadamard(root, env)
    if "y4_tensor_not_built" in only:
        out["y4_tensor"] = build_y4_not_built(root, env, y4)
    for item, (rec, tex) in out.items():
        fr.write(root, item, rec, tex)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="*", choices=list(BUILDERS) + ["y4_tensor_not_built"])
    p.add_argument("--prime-race-height", type=int, default=400)
    args = p.parse_args(argv)
    root = Path.cwd()
    try:
        out = build_all(root, dict(os.environ), args.only, args.prime_race_height)
    except BuildError as exc:
        print(f"FAILED: {exc}")
        return 1
    print(json.dumps({item: {"scope_category": rec["scope_category"], "status": rec["status"]}
                      for item, (rec, _) in out.items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
