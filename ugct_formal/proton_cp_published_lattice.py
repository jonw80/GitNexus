#!/usr/bin/env python3
"""The proton coefficient c_p = m_p / Lambda from published lattice QCD, without new lattice runs.

The manuscript defines c_p by m_p = c_p Lambda_QCD with Lambda_QCD = M_Pl e^-44 = 949.99 MeV, and names a lattice/HPC
run (Anvil) to compute it. The dimensionless QCD number such a run would produce is m_N / Lambda in a stated scheme
and number of flavours. Lattice QCD has already computed Lambda in the MS-bar scheme with continuum extrapolation,
finite-volume control and scale setting (FLAG 2024 averages of N_f = 2+1 and 2+1+1 results), and lattice QCD
reproduces the measured nucleon mass, so the ratio is m_p(CODATA) / Lambda(FLAG).

What this cannot do: compare with UGCT. c_p depends on the scheme of Lambda (MS-bar N_f = 3 and the static-potential
scheme differ by a factor exp(7/18) = 1.475 exactly), and the manuscript does not say which scheme M_Pl e^-44 is in.
Its own two presentations (949.99 MeV with c_p ~ 0.988, and "[0.231, 0.244] GeV conventional MS-bar" with
c_p in [3.84, 4.06]) fit no N_f of FLAG 2024. Also, e^-44 is not chi(Y4)/24 of the stated construction: that is
3048/24 = 127 (ugct_sage_y4/independent_y4_pushforward.py).

Inputs (snapshot; each is a published value used exactly as published):
  m_p c^2 = 938.272 089 43(29) MeV               CODATA 2022 (Rev. Mod. Phys. 97, 025002 (2025))
  M_Pl c^2 = 1.220 890(14) x 10^19 GeV            CODATA 2022 Planck mass (sqrt(hbar c / G), not reduced)
  Lambda_MSbar^(3,4,5) = 338(10), 295(10), 213(8) MeV, alpha_s(m_Z) = 0.1183(7)
                                                  FLAG Review 2024, arXiv:2411.04268, Table 2
Exact scheme conversion (one loop is exact for Lambda ratios, Celmaster-Gonsalves):
  alpha_V = alpha_MS (1 + a1 alpha_MS/(4 pi) + ...), a1 = 31/3 - 10 n_f/9 (Fischler; Billoire),
  Lambda_V / Lambda_MS = exp(a1 / (2 beta0)), beta0 = 11 - 2 n_f / 3.

Run:  python3 ugct_formal/proton_cp_published_lattice.py [results.txt]   (exits 1 if a check fails)
"""
import hashlib
import json
import math
import sys

SNAPSHOT = {
    "m_p_MeV": {"value": 938.27208943, "sigma": 0.00000029, "source": "CODATA 2022"},
    "M_Pl_GeV": {"value": 1.220890e19, "sigma": 0.000014e19, "source": "CODATA 2022 Planck mass, not reduced"},
    "Lambda_MSbar_MeV": {
        "3": {"value": 338.0, "sigma": 10.0},
        "4": {"value": 295.0, "sigma": 10.0},
        "5": {"value": 213.0, "sigma": 8.0},
        "source": "FLAG Review 2024, arXiv:2411.04268, Table 2 (N_f = 2+1 and 2+1+1 averages)",
    },
    "alpha_s_mZ": {"value": 0.1183, "sigma": 0.0007, "source": "FLAG Review 2024"},
    "manuscript": {"Lambda_QCD_MeV": 949.99, "c_p_clue": "1 - 1/81", "lattice_presentation_GeV": [0.231, 0.244],
                   "lattice_presentation_c_p": [3.84, 4.06],
                   "source": "UGCT Principia (post-review 5), Theorems 21.5-21.6, Remark 21.4; first_principles_lattice_certificate.pdf"},
}


def snapshot_sha256():
    return hashlib.sha256(json.dumps(SNAPSHOT, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ratio_interval(num, num_sig, den, den_sig):
    """central value and 1-sigma of num/den (independent errors), plus the 1-sigma interval."""
    c = num / den
    s = c * math.hypot(num_sig / num, den_sig / den)
    return c, s, (c - s, c + s)


def v_scheme_ratio(nf):
    a1 = 31.0 / 3.0 - 10.0 * nf / 9.0
    beta0 = 11.0 - 2.0 * nf / 3.0
    return math.exp(a1 / (2.0 * beta0))


def compute():
    """The per-scheme rows, Lambda_UGCT = M_Pl e^-44 (MeV, with its sigma) and the check failures."""
    failures = []
    mp, mps = SNAPSHOT["m_p_MeV"]["value"], SNAPSHOT["m_p_MeV"]["sigma"]
    mpl, mpls = SNAPSHOT["M_Pl_GeV"]["value"] * 1e3, SNAPSHOT["M_Pl_GeV"]["sigma"] * 1e3       # MeV
    lam_ugct = mpl * math.exp(-44)
    lam_ugct_s = mpls * math.exp(-44)

    # checks against the manuscript's own numbers and exact identities
    if abs(lam_ugct - SNAPSHOT["manuscript"]["Lambda_QCD_MeV"]) > 0.01:
        failures.append(f"M_Pl e^-44 = {lam_ugct:.3f} MeV, manuscript says 949.99")
    if abs(mp / lam_ugct - (1 - 1 / 81)) > 5e-5:
        failures.append("m_p / (M_Pl e^-44) is not within 5e-5 of 1 - 1/81 (manuscript Remark 21.4)")
    if abs(v_scheme_ratio(3) - math.exp(7 / 18)) > 1e-15:
        failures.append("V-scheme ratio for n_f = 3 is not exp(7/18)")

    rows = []
    for nf in ("3", "4", "5"):
        lam = SNAPSHOT["Lambda_MSbar_MeV"][nf]
        c, s, iv = ratio_interval(mp, mps, lam["value"], lam["sigma"])
        pull = (lam_ugct - lam["value"]) / math.hypot(lam["sigma"], lam_ugct_s)
        rows.append({"key": f"MSbar_nf{nf}", "Lambda_value_MeV": lam["value"], "Lambda_sigma_MeV": lam["sigma"],
                     "scheme": f"MS-bar, N_f = {nf}", "Lambda_MeV": f"{lam['value']:.0f}({lam['sigma']:.0f})",
                     "c_p": c, "c_p_sigma": s, "c_p_interval_1sigma": iv,
                     "Lambda_UGCT_over_Lambda": lam_ugct / lam["value"], "pull_sigma": pull})
    lam3 = SNAPSHOT["Lambda_MSbar_MeV"]["3"]
    rv = v_scheme_ratio(3)
    c, s, iv = ratio_interval(mp, mps, lam3["value"] * rv, lam3["sigma"] * rv)
    rows.append({"key": "V_nf3", "Lambda_value_MeV": lam3["value"] * rv, "Lambda_sigma_MeV": lam3["sigma"] * rv,
                 "scheme": "static potential (V), N_f = 3", "Lambda_MeV": f"{lam3['value'] * rv:.0f}({lam3['sigma'] * rv:.0f})",
                 "c_p": c, "c_p_sigma": s, "c_p_interval_1sigma": iv,
                 "Lambda_UGCT_over_Lambda": lam_ugct / (lam3["value"] * rv),
                 "pull_sigma": (lam_ugct - lam3["value"] * rv) / math.hypot(lam3["sigma"] * rv, lam_ugct_s)})
    return rows, lam_ugct, lam_ugct_s, failures


def main(out=None):
    mp = SNAPSHOT["m_p_MeV"]["value"]
    rows, lam_ugct, lam_ugct_s, failures = compute()
    lo, hi = SNAPSHOT["manuscript"]["lattice_presentation_c_p"]
    fits = [r["scheme"] for r in rows if r["c_p_interval_1sigma"][0] <= hi and r["c_p_interval_1sigma"][1] >= lo]

    lines = [
        "Proton coefficient c_p = m_p / Lambda from published lattice QCD (no new lattice run)",
        f"input snapshot sha256: {snapshot_sha256()}",
        f"m_p = {mp:.8f} MeV (CODATA 2022); M_Pl e^-44 = {lam_ugct:.3f}({lam_ugct_s:.3f}) MeV (manuscript Lambda_QCD)",
        "",
        f"{'scheme':32s} {'Lambda [MeV]':>13s} {'c_p = m_p/Lambda':>18s} {'1-sigma interval':>18s} "
        f"{'M_Pl e^-44 / Lambda':>20s} {'pull':>8s}",
    ]
    for r in rows:
        lines.append(f"{r['scheme']:32s} {r['Lambda_MeV']:>13s} {r['c_p']:>11.3f} +- {r['c_p_sigma']:.3f} "
                     f"  [{r['c_p_interval_1sigma'][0]:.3f}, {r['c_p_interval_1sigma'][1]:.3f}] "
                     f"{r['Lambda_UGCT_over_Lambda']:>14.3f} {r['pull_sigma']:>9.0f} sigma")
    lines += [
        "",
        f"manuscript c_p with Lambda = M_Pl e^-44: m_p/949.99 = {mp / lam_ugct:.6f}. This is the measured ratio, not a QCD",
        "computation: lattice QCD computes m_N/Lambda only once the scheme of Lambda is fixed.",
        f"manuscript 'lattice presentation' c_p in [{lo}, {hi}] with Lambda in [0.231, 0.244] GeV 'MS-bar': overlaps the "
        f"1-sigma FLAG 2024 interval for {fits if fits else 'no scheme listed'}.",
        f"M_Pl e^-44 is {rows[0]['Lambda_UGCT_over_Lambda']:.1f} times Lambda_MSbar^(3) and {rows[3]['Lambda_UGCT_over_Lambda']:.1f} "
        "times Lambda_V^(3); it is not the Lambda parameter of",
        "MS-bar QCD for any number of flavours (pulls above).",
        "",
        "checks: " + ("all passed" if not failures else "; ".join(failures)),
    ]
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if out:
        with open(out, "w") as fh:
            fh.write(text)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
