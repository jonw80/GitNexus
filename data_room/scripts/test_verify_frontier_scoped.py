#!/usr/bin/env python3
"""Tests of verify_frontier_scoped.py on records built by the record builders. Needs cypari2.
Run from the repository root:  python3 data_room/scripts/test_verify_frontier_scoped.py   (exits 1 on a failure)
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frontier_records as fr  # noqa: E402
from frontier_test_support import load, make_root  # noqa: E402

bf = load(HERE / "build_frontier_certificates.py", "build_frontier_certificates")
ym = load(HERE / "build_ym_import_record.py", "build_ym_import_record")
scoped = load(HERE / "verify_frontier_scoped.py", "verify_frontier_scoped")
ENV = {"GITHUB_RUN_ID": "9001"}


def build_everything(root: Path, env: dict) -> None:
    bf.build_all(root, env, only=list(bf.BUILDERS) + ["y4_tensor_not_built"], height=100)
    rec, tex = ym.build(root, env)
    (root / ym.OUT_JSON).write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    (root / ym.OUT_TEX).write_text(tex)


def failures(root: Path, env=ENV) -> dict:
    report = scoped.verify(root, env)
    return {r["name"]: r["failures"] for r in report["records"] if r["failures"]}


def edit(root: Path, item: str, change, rehash: bool = True) -> None:
    path = root / fr.ITEMS[item][0]
    rec = json.loads(path.read_text())
    change(rec)
    if rehash:
        rec["payload_hash"] = fr.canonical_hash(rec)
    path.write_text(json.dumps(rec))


def fresh(base: Path, tmp: Path) -> Path:
    dst = tmp / f"copy{len(list(tmp.iterdir()))}"
    shutil.copytree(base, dst)
    return dst


with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    base = make_root(tmp / "base")
    build_everything(base, ENV)

    # 1. records built in this run pass, whatever their scope; the strict tally is reported beside it
    report = scoped.verify(base, ENV)
    assert report["status"] == "FRONTIER_RECORDS_SCOPED_AND_COMPUTED_IN_RUN", failures(base)
    assert report["strict_tally"] == "0/8" and report["table_problems"] == []
    assert report["scope_counts"] == {"VERIFIED": 0, "CONDITIONAL": 1, "OPEN": 7, "NEGATIVE": 0}, report["scope_counts"]

    # 2. records from another run (or committed ones) fail
    f = failures(base, {"GITHUB_RUN_ID": "9002"})
    assert set(f) == set(fr.ITEMS) and all("is not this run" in " ".join(v) for v in f.values()), f

    # 3. a changed field without a new hash fails
    root = fresh(base, tmp)
    edit(root, "uplift", lambda r: r["results"].update(typed_matrix_lambda_min=0.5), rehash=False)
    assert failures(root) == {"uplift": ["payload_hash does not match the canonical hash"]}, failures(root)

    # 4. relabelling a record VERIFIED fails the strict checks; an OPEN record without open items fails
    root = fresh(base, tmp)
    edit(root, "pfaffian", lambda r: r.update(scope_category="VERIFIED"))
    edit(root, "hadamard_divisor", lambda r: r.update(open_items=[]))
    f = failures(root)
    assert "scope VERIFIED but the strict checks fail" in f["pfaffian"][0], f
    assert any("needs a non-empty open_items" in x for x in f["hadamard_divisor"]), f

    # 5. an input file changed after the record was written fails
    root = fresh(base, tmp)
    with open(root / bf.COSMO_TYPED, "a") as fh:
        fh.write(" ")
    assert failures(root) == {"cosmological_constant": [f"input {bf.COSMO_TYPED} changed after the record was written"]}

    # 6. the typed certificate this replaces passes the strict checks but not the scoped gate
    root = fresh(base, tmp)
    typed = {"schema_version": "UGCT_PFAFFIAN_NORMALIZATION_CERTIFICATE_V1",
             "status": "VERIFIED_ABSOLUTE_PFAFFIAN_NORMALIZATION", "fully_certified": True,
             "operator_domain": "typed", "determinant_line_convention": "typed",
             "pfaffian_interval": {"lower": 0.997, "upper": 1.003}, "zero_modes_removed": True,
             "collar_independence_verified": True}
    typed["payload_hash"] = fr.canonical_hash(typed)
    (root / fr.ITEMS["pfaffian"][0]).write_text(json.dumps(typed))
    rec = next(r for r in scoped.verify(root, ENV)["records"] if r["name"] == "pfaffian")
    assert rec["strict_ok"] is True and rec["ok"] is False, rec
    for need in ("scope_category None", "computed_by None", "inputs must be a list", "is not this run"):
        assert any(need in x for x in rec["failures"]), (need, rec["failures"])

    # 7. a record not written by a builder, a sidecar that does not state the scope, or a stale dependency fails
    root = fresh(base, tmp)
    edit(root, "proton_cp", lambda r: r.update(computed_by="data_room/scripts/emit_frontier_closeout_artifacts.py"))
    tex = root / fr.ITEMS["prime_race"][1]
    tex.write_text(tex.read_text().replace("Scope: \\texttt{CONDITIONAL}", "Scope: conditional"))
    edit(root, "uplift", lambda r: r.update(status="UPLIFT_STABILITY_REVISED"))
    f = failures(root)
    assert "is not a record builder" in f["proton_cp"][0] and f["prime_race"] == ["the sidecar does not state the scope category"]
    assert "dependency on uplift" in " ".join(f["cosmological_constant"]), f

    # 8. a declared proton scheme makes one record VERIFIED, and the strict tally counts it
    root = fresh(base, tmp)
    (root / bf.PROTON_DECLARED).write_text(json.dumps({"scheme": "MSbar_nf3", "declared_by": "test",
                                                       "declared_on": "2026-11-27", "statement": "N_f = 3 MS-bar."}))
    fr.write(root, "proton_cp", *bf.build_proton(root, ENV))
    report = scoped.verify(root, ENV)
    assert report["status"] == "FRONTIER_RECORDS_SCOPED_AND_COMPUTED_IN_RUN" and report["strict_tally"] == "1/8", failures(root)

print("scoped frontier gate: all tests passed")
