#!/usr/bin/env python3
"""Build the eight frontier records in a workflow that does not run Sage.

  Yang-Mills import          data_room/scripts/build_ym_import_record.py, from the author's status file
  six computed records       data_room/scripts/build_frontier_certificates.py (prime race, proton, Pfaffian, uplift,
                             cosmological constant, Hadamard divisor)
  Y4 tensor                  a record saying the manifest is built in the Sage workflow, with this run's independent
                             Y4 results if ugct_sage_y4/independent_y4_pushforward.py ran first

Until 2026-11-26/27 this script typed the certificates in: status VERIFIED, true flags and intervals with no
computation behind them (the Y4, proton and Yang-Mills ones were replaced on 2026-11-26, the other five on 2026-11-27).
Each record now states its scope (VERIFIED, CONDITIONAL, OPEN or NEGATIVE); verify_frontier_scoped.py checks them.

Run from the repository root (needs cypari2 for the prime race):
  python3 data_room/scripts/emit_frontier_closeout_artifacts.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if load("build_ym_import_record").main() != 0:
        print("FAILED: build_ym_import_record.py")
        return 1
    bf = load("build_frontier_certificates")
    return bf.main(["--only", *bf.BUILDERS, "y4_tensor_not_built"])


if __name__ == "__main__":
    os.chdir(HERE.parents[1])
    sys.exit(main())
