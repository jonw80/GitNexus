#!/usr/bin/env python3
"""Tests of build_frontier_certificates.py, checked with the strict gate's own functions. Needs cypari2.
Run from the repository root:  python3 data_room/scripts/test_build_frontier_certificates.py   (exits 1 on a failure)
"""
import copy
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frontier_records as fr  # noqa: E402
from frontier_test_support import FAKE_Y4, load, make_root  # noqa: E402

bf = load(HERE / "build_frontier_certificates.py", "build_frontier_certificates")
gate = load(HERE / "verify_frontier_closeout.py", "verify_frontier_closeout")
sidecars = load(HERE / "verify_referee_sidecars.py", "verify_referee_sidecars")
ENV = {"GITHUB_RUN_ID": "4242", "GITHUB_SHA": "abc"}
HEIGHT = 100


def strict(root, item, rec):
    fail = []
    gate.check_common(item, rec, root / fr.ITEMS[item][1], fr.ITEMS[item][2], fail)
    gate.check_item(item, rec, fail)
    return fail


def expect_build_error(fn):
    try:
        fn()
    except bf.BuildError as exc:
        return str(exc)
    raise AssertionError("BuildError expected")


with tempfile.TemporaryDirectory() as d:
    root = make_root(Path(d))
    out = bf.build_all(root, ENV, height=HEIGHT)

    # 1. six records, each with its scope, provenance and hash; none passes the strict gate
    expect = {"prime_race": "CONDITIONAL", "proton_cp": "OPEN", "pfaffian": "OPEN", "uplift": "OPEN",
              "cosmological_constant": "OPEN", "hadamard_divisor": "OPEN"}
    assert set(out) == set(expect), sorted(out)
    for item, scope in expect.items():
        rec = json.loads((root / fr.ITEMS[item][0]).read_text())
        tex = (root / fr.ITEMS[item][1]).read_text()
        assert rec == out[item][0] and rec["scope_category"] == scope and rec["fully_certified"] is False, item
        assert rec["payload_hash"] == gate.canonical_hash(rec) and rec["schema_version"].startswith("UGCT_"), item
        assert rec["computed_by"] == bf.COMPUTED_BY and rec["source_workflow_run_id"] == "4242", item
        assert rec["status"] != fr.ITEMS[item][2] and any("status mismatch" in f for f in strict(root, item, rec)), item
        for i in rec["inputs"]:
            assert fr.sha256_file(root / i["path"]) == i["sha256"], (item, i)
        assert f"Scope: \\texttt{{{scope}}}" in tex and rec["status"] in tex.replace("\\_", "_"), item
        assert (rec["open_items"] if scope == "OPEN" else rec["hypotheses"]), item
        assert sidecars.check(root, item)["ok"], sidecars.check(root, item)

    # 2. prime race: conditional on GRH + LI, reproduces Rubinstein-Sarnak, and says the typed interval contradicts it
    pr = out["prime_race"][0]
    assert pr["grh_used"] is True and pr["linear_independence_used"] is True and len(pr["hypotheses"]) == 2
    assert pr["results"]["zero_count"] == 50 and all(pr["checks"].values()), pr["checks"]
    assert abs(pr["conditional_density_estimate"]["value"] - 0.9959) < 1e-4, pr["conditional_density_estimate"]
    assert pr["results"]["delta_with_zeros_up_to_T"] > pr["results"]["delta_tail_corrected"]
    assert any("incompatible" in f for f in pr["findings"]) and pr["results"]["log10_bound_beyond_t_max"] < -10

    # 3. proton: per-scheme c_p from published lattice QCD; M_Pl e^-44 is the Lambda of no scheme
    pc = out["proton_cp"][0]
    rows = {r["key"]: r for r in pc["per_scheme"]}
    assert abs(rows["MSbar_nf3"]["c_p"] - 2.776) < 1e-3 and abs(rows["V_nf3"]["c_p"] - 1.882) < 1e-3, rows
    assert pc["c_p_interval"] is None and "none of these schemes" in pc["findings"][0]
    assert "no scheme in the table" in pc["findings"][1] and "declared_scheme.json" in pc["open_items"][0]

    # 4. Pfaffian: chi(O_D) = -(D^4 + c2 D^2)/24 from the run's tensor; the typed widening is rechecked
    pf = out["pfaffian"][0]
    assert pf["results"]["chi_O_D"]["A"]["chi_O_D"] == "1" and pf["results"]["chi_O_D"]["B"]["chi_O_D"] == "-1"
    assert pf["results"]["divisors_with_chi_1"] == ["A"] and all(pf["checks"].values())
    assert pf["zero_modes_removed"] is False and pf["pfaffian_interval"] is None

    # 5. uplift: smallest eigenvalue of the typed interval matrix over its box, Gershgorin, the run's tadpole
    up = out["uplift"][0]
    lam = min((a + c) / 2 - math.sqrt(((a - c) / 2) ** 2 + b * b)
              for a in (0.041, 0.047) for b in (-0.004, 0.004) for c in (0.036, 0.044))
    assert abs(up["results"]["typed_matrix_lambda_min"] - lam) < 1e-12 and abs(up["results"]["typed_matrix_gershgorin_lower"] - 0.032) < 1e-12
    assert up["results"]["d3_tadpole_chi_over_24"] == 127 and all(up["checks"].values())

    # 6. cosmological constant: the typed interval is not the Minkowski sum and excludes the observed value
    cc = out["cosmological_constant"][0]
    lo, hi = cc["results"]["minkowski_sum_of_typed_terms"]
    assert abs(lo / 1.1505e-122 - 1) < 1e-12 and abs(hi / 1.2695e-122 - 1) < 1e-12
    obs = cc["results"]["observed"]["rho_over_M_Pl4"]
    assert abs(obs / 1.1320e-123 - 1) < 1e-3 and not cc["results"]["observed_in_stated_interval_M_Pl"]
    assert not cc["results"]["observed_in_stated_interval_reduced"] and cc["results"]["stated_contains_sum"]
    assert abs(cc["results"]["formula_P10_N_chi_over_24_log10"] + 339.21) < 0.01
    assert cc["dependency"] == {"item": "uplift", "certificate": fr.ITEMS["uplift"][0], "scope_category": "OPEN",
                                "status": "UPLIFT_STABILITY_OPEN"}
    assert cc["depends_on_uplift_certificate"] == "UPLIFT_STABILITY_OPEN"

    # 7. Hadamard: every strict flag false; the manuscript's own RH statement is recorded
    hd = out["hadamard_divisor"][0]
    assert not any(hd[k] for k in ("xi_divisor_identified", "nonvanishing_factor_verified", "no_spurious_zeros_verified",
                                   "hurwitz_transfer_verified", "h2_tail_graph_norm_verified",
                                   "parity_gap_persistence_verified"))
    assert "Riemann hypothesis" in hd["findings"][0]

    # 8. a declared scheme makes the proton record VERIFIED with the published value; it passes the strict gate and
    #    its sidecar is referee-grade
    (root / bf.PROTON_DECLARED).write_text(json.dumps({"scheme": "MSbar_nf3", "declared_by": "test",
                                                       "declared_on": "2026-11-27",
                                                       "statement": "Lambda_QCD is Lambda_MSbar with N_f = 3."}))
    rec, tex = bf.build_proton(root, ENV)
    fr.write(root, "proton_cp", rec, tex)
    assert rec["scope_category"] == "VERIFIED" and rec["status"] == "VERIFIED_PROTON_CP_LATTICE_QCD"
    assert strict(root, "proton_cp", rec) == [], strict(root, "proton_cp", rec)
    assert abs(rec["c_p_interval"]["lower"] - (rec["c_p"] - 2 * rec["c_p_sigma"])) < 1e-12 and abs(rec["c_p"] - 2.776) < 1e-3
    assert abs(rec["comparison"]["ratio"] - 2.81) < 0.01 and rec["inputs"][-1]["path"] == bf.PROTON_DECLARED
    assert sidecars.referee_failures(tex) == [], sidecars.referee_failures(tex)
    assert sidecars.check(root, "proton_cp")["ok"], sidecars.check(root, "proton_cp")
    for bad in ({"scheme": "MSbar_nf6", "declared_by": "x", "declared_on": "y", "statement": "z"}, {"scheme": "V_nf3"}):
        (root / bf.PROTON_DECLARED).write_text(json.dumps(bad))
        assert "declared_scheme.json" in expect_build_error(lambda: bf.build_proton(root, ENV))
    (root / bf.PROTON_DECLARED).unlink()

    # 9. a Y4 record for a workflow without Sage carries the independent results and stays OPEN
    rec, tex = bf.build_y4_not_built(root, ENV, bf.load_y4(root))
    fr.write(root, "y4_tensor", rec, tex)
    assert rec["scope_category"] == "OPEN" and rec["nonzero_quadruple_intersections"] == 2
    assert "tensor verified flag required" in strict(root, "y4_tensor", rec)

    # 10. a non-integral chi(O_D) or an asymmetric typed Hessian is refused
    bad_y4 = copy.deepcopy(FAKE_Y4)
    bad_y4["c2_pairings"]["A,A"] = "-15"
    assert "not an integer" in expect_build_error(lambda: bf.build_pfaffian(root, ENV, bad_y4))
    typed = json.loads((root / bf.UPLIFT_TYPED).read_text())
    typed["interval_hessian_matrix"][1][0] = {"lower": -0.003, "upper": 0.004}
    (root / bf.UPLIFT_TYPED).write_text(json.dumps(typed))
    assert "not symmetric" in expect_build_error(lambda: bf.build_uplift(root, ENV, None))

with tempfile.TemporaryDirectory() as d:
    # 11. without this run's Y4 tensor the Y4-derived numbers are absent and the records say so
    root = make_root(Path(d), y4=None)
    out = bf.build_all(root, {}, only=["pfaffian", "cosmological_constant"], height=HEIGHT)
    assert set(out) == {"pfaffian", "uplift", "cosmological_constant"}
    for item in out:
        rec = out[item][0]
        assert rec["source_workflow_run_id"] == "local" and any(bf.Y4_TENSOR in i for i in rec["open_items"]), item
        assert bf.Y4_TENSOR not in [i["path"] for i in rec["inputs"]], item
    assert out["pfaffian"][0]["results"] == {} and "d3_tadpole_chi_over_24" not in out["uplift"][0]["results"]

print("frontier record builder: all tests passed")
