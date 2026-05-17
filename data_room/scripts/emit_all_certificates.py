#!/usr/bin/env python3
"""Emit the UGCT downstream certificate-layer payloads.

This script implements the 2026-05-16 closure specification for the 15
outstanding full-payload items plus the conditional prime-race item. It does not
pretend that Tier-3 research-frontier problems are solved. Instead it replaces
ambiguous placeholder/external markers with explicit certificate records:

  * Tier 1: operationally closable now by interval/symbolic tooling;
  * Tier 2: specified but requiring HPC, external snapshots, or larger runs;
  * Tier 3: research-frontier/contested, delivered as schema + literature +
    open-problem statement.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROOFS = ROOT / "proofs"
DATA.mkdir(parents=True, exist_ok=True)
PROOFS.mkdir(parents=True, exist_ok=True)

DATE = "2026-05-16"


def write_json(rel, obj):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))
    print(json.dumps({"wrote": rel, "status": obj.get("status"), "tier": obj.get("tier")}, sort_keys=True))


def cert(cid, name, tier, status, fully_certified=False, **kw):
    obj = {
        "schema_version": "UGCT_CERTIFICATE_V1",
        "certificate_id": cid,
        "name": name,
        "tier": tier,
        "status": status,
        "fully_certified": fully_certified,
        "date_recorded": DATE,
        "geometry_context": {
            "fourfold": "resolved Tate SU(5) Calabi-Yau fourfold Y4",
            "base": "B3 = P(O + K_dP8)",
            "chi_Y4": 1056,
            "tadpole_chi_over_24": 44,
            "y4_tensor_status": "FULL_CHAMBER_SPECIFIC_TENSOR_VERIFIED"
        }
    }
    obj.update(kw)
    return obj

common_tools = {
    "cytools": "CYTools v1.4.9, GPLv3, with periods/flux/geometry APIs",
    "arb": "python-flint / Arb ball arithmetic",
    "sage": "SageMath exact arithmetic cross-checks",
    "oscar": "OSCAR.jl toric/cohomology computations"
}

items = []

items.append(("data/flux_scan_summary.json", cert(1, "flux_scan", 2, "SPECIFIED_SUBLATTICE_CI_FULL_SCAN_HPC", False,
    input_schema={"polytope_id":"string","Sigma_matrix":"integer matrix","tadpole_target":44,"search_box":{"flux_quanta_max":"integer"},"wall_constraints":{"FW_quantization":True}},
    algorithm="Enumerate quantized G4 fluxes satisfying 1/2 N^T Sigma N <= 44, FW congruence, primitivity and Hodge-type filters; certify surviving vacua with the GVW attractor Krawczyk solver.",
    output_schema=["n_admissible","n_certified_LCS","min_abs_W0_certified","compute_hours","warnings"],
    tooling=[common_tools["cytools"], "JAXVacua", common_tools["arb"], common_tools["sage"]],
    reproduction="docker run liammcallister/cytools:1.4.9 python scripts/scan_flux_lattice.py --N_max 12 --primitive --certify_attractor",
    closure_action="Run restricted sublattice in CI; full h31-scale scan is HPC.",
    warnings=["Full Sigma-lattice scan is HPC-scale.","Tadpole conjecture may obstruct complete stabilization for chi(Y4)/24=44 if h31 is large."],
    literature=["Witten 1996 flux quantization", "Demirtas-Kim-McAllister-Moritz PRL 124 (2020)", "JAXVacua JHEP 12 (2023) 146"]
)))

items.append(("data/pf_basis.json", cert(2, "picard_fuchs_basis_intervals", 1, "READY_FOR_INTERVAL_PERIOD_BASIS_COMPUTATION", False,
    input_schema={"polytope":"resolved geometry handle","triangulation":"FRST or fixed triangulation","lcs_chart":"coordinate chart","precision_bits":"integer"},
    algorithm="Frobenius basis around the LCS point, prepotential derivatives, GV-invariant instanton corrections, and Arb truncation tail bounds.",
    output_schema=["basis_ordering","evaluation_point","Pi_acb_strings","monodromy","conifold_loci","truncation_order","tail_bound"],
    tooling=[common_tools["cytools"], common_tools["arb"], common_tools["sage"]],
    reproduction="python data_room/scripts/compute_pf_basis.py --precision 200 --max_gv_deg 30",
    closure_action="Tier-1: close by running CYTools periods plus Arb tail certification.",
    literature=["Hosono-Klemm-Theisen-Yau CMP 167 (1995)", "CYTools arXiv:2211.03823"]
)))

items.append(("data/attractor_intervals.json", cert(3, "gvw_attractor_interval_solve", 1, "READY_FOR_KRAWCZYK_CERTIFICATION", False,
    input_schema={"pf_basis":"data/pf_basis.json","flux_id":"string","initial_box":"complex interval box"},
    algorithm="Interval Krawczyk operator for F=(D_a W, D_tau W)=0; K(B) subset int(B) certifies a unique root in the box.",
    output_schema=["z_star_box","tau_star_box","DW_residual_max","krawczyk_contracted","unique_in_box","distance_to_conifold"],
    tooling=[common_tools["arb"], "Bertini/alphaCertified optional"],
    reproduction="python data_room/scripts/attractor_interval_solve.py --flux <id> --pf_basis data/pf_basis.json",
    closure_action="Tier-1 once PF intervals and flux row are available.",
    literature=["Moore hep-th/9807087", "Honma-Otsuka arXiv:1910.10725", "Tucker Validated Numerics"]
)))

items.append(("data/axio_dilaton_interval.json", cert(4, "axio_dilaton_interval", 1, "READY_FOR_INTERVAL_SOLVE", False,
    input_schema={"attractor_intervals":"data/attractor_intervals.json","RR_flux":"vector","NS_flux":"vector"},
    algorithm="Compute tau = N_RR^T Sigma Pi / N_NS^T Sigma Pi with Arb intervals and reduce to the SL(2,Z) fundamental domain.",
    output_schema=["tau_box","gs_box","fundamental_domain_certified","S_duality_orbit_repr"],
    tooling=[common_tools["arb"], common_tools["sage"]],
    reproduction="python data_room/scripts/axio_dilaton_solve.py --attractor data/attractor_intervals.json",
    closure_action="Tier-1 after Items 2-3.",
    literature=["KKLT Phys Rev D 68 (2003) 046005"]
)))

items.append(("data/instanton_divisors.json", cert(5, "instanton_divisors_zero_modes", "1-2", "READY_FOR_ZERO_MODE_AND_FW_SCAN", False,
    input_schema={"Y4_data":"resolved tensor/chow data","kahler_cone":"generators","G4_flux":"certified flux"},
    algorithm="Compute divisor hodge diamonds/chi(O_D), Freed-Witten integrality, flux restriction, and SU(5) charged-zero-mode absence via toric/sheaf cohomology.",
    output_schema=["D_id","hodge_diamond","FW_passed","charged_modes","contributes_to_W"],
    tooling=[common_tools["cytools"], common_tools["oscar"], common_tools["sage"]],
    reproduction="julia data_room/scripts/instanton_zero_modes.jl --geometry ... --G4 ...",
    closure_action="Tier 1-2 depending on availability of matter line bundle data.",
    literature=["Witten NPB 474 (1996)", "Freed-Witten Asian J Math 3 (1999)", "Bies-Mayrhofer-Pehle-Weigand JHEP 08 (2017)"]
)))

items.append(("data/hidden_sector_ranks.json", cert(6, "hidden_sector_ranks_tadpole", 1, "READY_FOR_TADPOLE_AND_ANOMALY_SCAN", False,
    input_schema={"flux":"certified G4 flux","base_divisors":"list"},
    algorithm="Enumerate hidden stacks, ranks and matter; check tadpole use, anomaly/Freed-Witten compatibility and residual D3 budget.",
    output_schema=["g_i","N_i","matter","anomaly_check","FW_check","tadpole_contribution"],
    tooling=[common_tools["oscar"], common_tools["cytools"]],
    reproduction="python data_room/scripts/hidden_sector_scan.py",
    closure_action="Tier-1 after flux and divisor data.",
    literature=["Krause-Mayrhofer-Weigand JHEP 08 (2012)", "Cvetic-Halverson-Lin-Liu-Tian PRL 123 (2019)"]
)))

items.append(("data/pfaffian_prefactors.json", cert(7, "pfaffian_prefactors", 3, "FRONTIER_ONLY_ZERO_LOCUS_CERTIFIABLE", False,
    input_schema={"rigid_divisors":"Item 5","G4_flux":"Item 1","z_star":"Item 3"},
    algorithm="Compute holomorphic zero locus/order-of-vanishing; absolute one-loop normalization remains uncertaified.",
    output_schema=["D_id","holomorphic_factor_zero_locus","vanishing_order","normalization_ambiguity","tier","fully_certified"],
    tooling=[common_tools["oscar"], "Bismut-Zhang anomaly formula for ratios only"],
    reproduction="julia data_room/scripts/pfaffian_zero_locus.jl --divisor ...",
    closure_action="Tier-3: do not claim absolute interval for |A_i|; record zero locus and ambiguity.",
    open_problem_flag=True,
    pfaffian_normalization_uncertified=True,
    literature=["Cvetic-Donagi-Halverson-Marsano JHEP 11 (2012)", "Bismut-Zhang JDG 41 (1995)", "Curio-Krause arXiv:0904.2738"]
)))

items.append(("data/racetrack_superpotential.json", cert(8, "racetrack_superpotential", 2, "SPECIFIED_INHERITS_PFAFFIAN_WIDTH", False,
    input_schema={"W0":"Item 1/3","A_i":"Item 7","T_i":"Item 10","N_i":"Item 5/6"},
    algorithm="Assemble W(T)=W0+sum_i A_i exp(-2*pi*T_i/N_i) and propagate Arb intervals, with sensitivity to Pfaffian widths.",
    output_schema=["W_interval","sensitivity_table","dominant_width_source"],
    tooling=[common_tools["arb"], "SymPy"],
    reproduction="python data_room/scripts/assemble_racetrack.py --inputs ...",
    closure_action="Tier-2, conditional on Item 7 envelope.",
    inherited_uncertainties=["pfaffian_prefactors"]
)))

items.append(("data/string_loop_coefficients.json", cert(9, "string_loop_coefficients", 2, "SYSTEMATIC_INTERVAL_SPECIFIED", False,
    input_schema={"kahler_moduli":"intersection data","brane_locations":"D7/O7/F-theory limit"},
    algorithm="Berg-Haack-Kors and Berg-Haack-Pajer loop forms evaluated at the GVW vacuum; record O(g_s^2) systematic remainder.",
    output_schema=["C_KK_intervals","C_W_intervals","R_K_bound","bhp_systematic"],
    tooling=[common_tools["arb"], "SymPy"],
    reproduction="python data_room/scripts/string_loop_coefficients.py",
    closure_action="Tier-2: systematic interval with BHP conjectural/generalized status.",
    literature=["Berg-Haack-Kors JHEP 11 (2005)", "Berg-Haack-Pajer JHEP 09 (2007)", "Gao-Hebecker-Schreyer-Venken JHEP 09 (2022)"]
)))

items.append(("data/kahler_stabilization_certificate.json", cert(10, "kahler_stabilization", 1, "READY_FOR_INTERVAL_HESSIAN_CERTIFICATE", False,
    input_schema={"K":"alpha prime + loops","W":"racetrack superpotential"},
    algorithm="Solve D_T W=0 by interval Krawczyk; certify Hessian positivity by Gershgorin; check large volume and small coupling.",
    output_schema=["T_star_box","eigenvalue_intervals","V_star","gs_star","certified_flags"],
    tooling=[common_tools["arb"], "INTLAB optional"],
    reproduction="python data_room/scripts/kahler_stabilize.py",
    closure_action="Tier-1 after Items 8-9; inherits Pfaffian width.",
    inherited_uncertainties=["pfaffian_prefactors"],
    literature=["KKLT hep-th/0301240", "BBHL hep-th/0204254", "LVS hep-th/0502058"]
)))

items.append(("data/warp_factor_certificate.json", cert(11, "warp_factor", "2-3", "LEADING_ORDER_KS_CLOSABLE_FULL_BACKREACTION_FRONTIER", False,
    input_schema={"M":"integer","K":"integer","gs":"interval","conifold_modulus":"interval"},
    algorithm="Leading-order Klebanov-Strassler hierarchy and Arb integration of warp functions; full alpha-prime/KPV/backreaction inherits Item 12.",
    output_schema=["e4A0_box","mIR_over_MPl_box","corrections_propagated","backreaction_flag"],
    tooling=[common_tools["arb"], common_tools["sage"]],
    reproduction="python data_room/scripts/warp_factor.py --M ... --K ... --gs ...",
    closure_action="Tier-2 at leading order; Tier-3 for full backreacted warp factor.",
    inherited_uncertainties=["uplift_backreaction"],
    literature=["Klebanov-Strassler JHEP 08 (2000)", "GKP Phys Rev D 66 (2002)", "Lust-Randall Fortschr Phys 70 (2022)"]
)))

items.append(("data/uplift_backreaction_certificate.json", cert(12, "uplift_backreaction_stability", 3, "CONTESTED_RESEARCH_FRONTIER_NOT_FULLY_CERTIFIED", False,
    input_schema={"warp_data":"Item 11","D3_tadpole_budget":44,"condensate_scale":"interval"},
    algorithm="Static leading-order checks only; full anti-D3 backreaction and post-uplift Hessian positivity are literature-contested for tadpole budget 44.",
    output_schema=["delta_K_over_K_estimate","BBL_bound_satisfied","alternative_uplift_paths","goldstino_present","fully_certified"],
    tooling=[common_tools["arb"], "SymPy"],
    reproduction="python data_room/scripts/backreaction_static_check.py",
    closure_action="Tier-3: emit negative/frontier indicator, not a successful dS certificate.",
    open_problem_flag=True,
    fully_certified=False,
    Bena_Buchel_Lust_bound_satisfied=False,
    literature=["Bena-Grana-Kuperstein-Massai Phys Rev D 87 (2013)", "Bena-Buchel-Lust arXiv:1910.08094", "Lust-Randall arXiv:2206.04708", "Hebecker-Schreyer-Venken arXiv:2208.02826"]
)))

items.append(("data/cosmological_constant_error_budget.json", cert(13, "cosmological_constant_error_budget", 2, "SPECIFIED_INHERITS_BACKREACTION_WIDTH", False,
    input_schema={"Items_1_to_12":"certificate outputs"},
    algorithm="Propagate V_* = e^K(K^{-1}DWDWbar-3|W|^2)+V_uplift into rho_Lambda interval with separate error-source accounting.",
    output_schema=["rho_Lambda_quarter_meV_box","alpha_prime","loops","warp","antiD3","KK","dominant_sources"],
    tooling=[common_tools["arb"], "mpmath"],
    reproduction="python data_room/scripts/cosmo_const_budget.py --inputs all",
    closure_action="Tier-2; inherits Item 12 width.",
    inherited_uncertainties=["uplift_backreaction"],
    literature=["Demirtas-Kim-McAllister-Moritz-Rios-Tascon JHEP 12 (2021)", "Polchinski et al. JHEP 07 (2016)"]
)))

items.append(("data/cp_trace_anomaly_certificate.json", cert(14, "cp_trace_anomaly", 2, "FLAG_AGGREGATION_READY_HPC_FOR_SUBPERCENT", False,
    input_schema={"FLAG_alpha_s":"snapshot","lattice_metadata":"optional ensembles"},
    algorithm="Aggregate FLAG alpha_s and trace-anomaly lattice results; compare tentative geometric c_p=1-1/81 against lattice interval.",
    output_schema=["Lambda_QCD_MeV_box","cp_lat_box","geometric_value","compatible_within_1sigma","flag_aggregation_version"],
    tooling=["Chroma+QUDA/GRID optional", common_tools["arb"]],
    reproduction="python data_room/scripts/cp_anomaly_from_flag.py --flag 2024",
    closure_action="Tier-2: close at current FLAG width; subpercent discrimination is multi-year HPC.",
    literature=["FLAG 2024 arXiv:2411.04268", "Yang et al. PRL 121 (2018)"]
)))

items.append(("data/global_arithmetic_id_certificate.json", cert(15, "global_arithmetic_identity", 1, "MAIN_MANUSCRIPT_PROOF_PRESENT", False,
    input_schema={"psi_infty":"main manuscript","H2_P_P3_chain":"main manuscript"},
    algorithm="Record proof-layer dependency: CCM/Connes-vS route or Burnol-Hadamard alternative; no new numerical computation.",
    output_schema=["proof_file","proof_strategy","dependencies","conditional_language_check"],
    tooling=["LaTeX", "Lean4 scaffold optional"],
    reproduction="make -C data_room/proofs global_arithmetic_id_certificate.pdf",
    closure_action="Tier-1 proof-layer item; already in main manuscript, sidecar records dependencies.",
    literature=["Connes-Consani-Moscovici Ann Funct Anal 15 (2024)", "Connes-van Suijlekom CMP 406 (2025)", "Burnol CRAS 335 (2002)", "Burnol Forum Math 16 (2004)"]
)))

items.append(("data/prime_race_density_certificate.json", cert(16, "prime_race_density_4_3_1", "2_conditional_3_unconditional", "CONDITIONAL_ON_GRH_LI_UNCONDITIONAL_DELTA_OPEN", False,
    conditional={"hypotheses":["GRH(chi_-4)","LI"],"delta_4_3_1_box":"[0.9959 +/- 1e-4]","method":"Rubinstein-Sarnak Fourier inversion"},
    unconditional_best={"Omega_pm":"sqrt(x)*log_3(x)/log(x) scale", "smallest_sign_change_x":26861, "sign_change_count":"V(T) >= c log T", "limiting_log_distribution_exists":True, "delta_gt_half_known":False},
    output_schema=["conditional","unconditional_best","honest_status"],
    tooling=["mpmath", common_tools["arb"], "LMFDB zero snapshot"],
    reproduction="python data_room/scripts/prime_race_delta.py --q 4 --a 3 --b 1 --N_zeros 100000",
    closure_action="Conditional Tier-2; unconditional positive density remains Tier-3/open.",
    honest_status="delta > 1/2 remains conditional on GRH + LI; unconditionally only Omega_pm/sign-change/distributional statements are recorded.",
    literature=["Rubinstein-Sarnak Experiment Math 3 (1994)", "Hardy-Littlewood Acta Math 41 (1918)", "Knapowski-Turan 1962", "Bays-Hudson Math Comp 69 (2000)", "Devin MPCPS 169 (2020)"]
)))

for rel, obj in items:
    write_json(rel, obj)

proof = r"""\section*{Global Arithmetic Identity Certificate}
This sidecar records the proof-layer status for the identity $F_\infty=c\,\Xi$.
The main manuscript carries the analytic construction.  The certificate layer
records two proof routes: a Connes--Consani--Moscovici / Connes--van Suijlekom
spectral route, and an alternative Burnol--Hadamard uniqueness route conditional
only on the H2+(P)+(P3) analytic input already stated in the main manuscript.
"""
(PROOFS / "global_arithmetic_id_certificate.tex").write_text(proof)

index = {
    "schema_version": "UGCT_CERTIFICATE_LAYER_AGGREGATE_V1",
    "status": "CERTIFICATE_LAYER_SPECIFIED_WITH_TIERED_CLOSURE",
    "date_recorded": DATE,
    "total_items": len(items),
    "tier1_operational": [2,3,4,5,6,10,15],
    "tier2_hpc_or_external": [1,8,9,11,13,14,16],
    "tier3_frontier": [7,12,16],
    "honesty_policy": "Tier-3 items are not promoted to verified certificates.",
    "files": [rel for rel, _ in items] + ["proofs/global_arithmetic_id_certificate.tex"]
}
write_json("data/INDEX.generated.json", index)
