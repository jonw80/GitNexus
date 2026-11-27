#!/usr/bin/env python3
"""Test support for the frontier record builders and the scoped gate: a temporary repository root holding copies of
the builders and of every input file they read, and a small stand-in Y4 tensor."""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COPIED = [
    "data_room/scripts/build_frontier_certificates.py", "data_room/scripts/build_ym_import_record.py",
    "ugct_sage_y4/build_y4_tensor_manifest.py", "ugct_formal/proton_cp_published_lattice.py",
    "data_room/primary/proton/ensemble.json", "data_room/primary/prime_race/arb_matrices.json",
    "data_room/data/prime_race_density_verified.json", "data_room/primary/pfaffian/operator_matrix.json",
    "data_room/primary/uplift/hessian_matrix.json", "data_room/primary/cosmology/interval_sum.json",
    "data_room/primary/hadamard/determinant_identity.tex", "data_room/primary/ym/ym_companion_status.json",
]

# chi(O_A) = -(-8 - 16)/24 = 1 and chi(O_B) = -(0 + 24)/24 = -1
FAKE_Y4 = {
    "schema_version": "UGCT_Y4_INDEPENDENT_EJK_PUSHFORWARD_V1", "status": "INDEPENDENT_TENSOR_COMPUTED", "failures": [],
    "basis": ["A", "B"], "quadruple_intersections": {"A,A,A,A": "-8", "A,A,B,B": "2"},
    "c2_pairings": {"A,A": "-16", "A,B": "3", "B,B": "24"},
    "chi_Y4": "3048", "d3_tadpole_chi_over_24": "127", "int_c2_squared": "1496", "nonzero_count": 2,
    "total_degree4_monomials": 5,
    "checks": {"chi_matches_published_formula": True, "todd_genus": "2", "riemann_roch_failures": 0,
               "calabi_yau_condition": True},
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_root(tmp: Path, y4: dict | None = FAKE_Y4) -> Path:
    for rel in COPIED:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, tmp / rel)
    if y4 is not None:
        path = tmp / "ugct_sage_y4/data/y4_independent_tensor.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(y4))
    return tmp
