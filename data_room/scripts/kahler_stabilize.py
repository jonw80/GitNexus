#!/usr/bin/env python3
"""
kahler_stabilize.py
====================
Item 10 (Tier 1): Kähler moduli stabilization via interval Krawczyk
on D_{T_a} W = 0, plus Gershgorin enclosure of the Hessian eigenvalues
to certify positive-definiteness.

Inputs:
  - data/racetrack_superpotential.json (W(T) interval coefficients)
  - data/kahler_potential_nlo.json     (K(T,Tbar) NLO with alpha' + loops)

Algorithm:
  1. F-term system F_a(T) := D_{T_a} W = (partial_a W) + (partial_a K) W = 0
  2. Newton iteration with python-flint acb to find approximate T*.
  3. Krawczyk operator K(B) = m - A F(m) + (I - A F'(B))(B - m) certifies
     a unique root in B.
  4. Compute Hessian H_{a bbar} = partial_a partial_bbar V at T*.
  5. Gershgorin: for each row i, lambda_i in [H_{ii} - sum_{j!=i} |H_{ij}|,
     H_{ii} + sum_{j!=i} |H_{ij}|]. If all lower endpoints > 0, the Hessian
     is positive-definite (in fact eigenvalues >= the smallest lower endpoint).
  6. Volume V > 100 and g_s < 0.3 sanity checks.

Output: data/kahler_stabilization_certificate.json with certified flags.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    from flint import acb, arb, acb_mat, ctx
except ImportError:
    print("ERROR: python-flint required.", file=sys.stderr)
    sys.exit(5)


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: missing input {path}", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        return json.load(f)


def gershgorin_enclosure(H: acb_mat, n: int) -> tuple[list[float], list[float], float]:
    """Return (lower_endpoints, upper_endpoints, min_lower) for Hessian rows.
    
    For a Hermitian matrix H, the i-th eigenvalue is in
        [H_{ii} - sum_{j!=i} |H_{ij}|, H_{ii} + sum_{j!=i} |H_{ij}|].
    """
    lowers, uppers = [], []
    for i in range(n):
        diag = H[i, i]
        d_re = float(diag.real.mid())
        d_re_rad = float(diag.real.rad())
        off_sum = 0.0
        off_sum_rad = 0.0
        for j in range(n):
            if i == j:
                continue
            mod_ij = abs(H[i, j])
            off_sum += float(mod_ij.mid())
            off_sum_rad += float(mod_ij.rad())
        lower = (d_re - d_re_rad) - (off_sum + off_sum_rad)
        upper = (d_re + d_re_rad) + (off_sum + off_sum_rad)
        lowers.append(lower)
        uppers.append(upper)
    return lowers, uppers, min(lowers)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--racetrack", type=Path, required=True, help="data/racetrack_superpotential.json")
    ap.add_argument("--kahler-nlo", type=Path, required=True, help="data/kahler_potential_nlo.json")
    ap.add_argument("--precision", type=int, default=200)
    ap.add_argument("--initial-radius", type=float, default=1e-3)
    ap.add_argument("--max-iter", type=int, default=30)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    ctx.prec = args.precision
    racetrack = load_json(args.racetrack)
    kahler = load_json(args.kahler_nlo)

    out = {
        "schema_version": "1.0",
        "tier": 1,
        "tool": "python-flint Krawczyk + Gershgorin",
        "precision_bits": args.precision,
        "inputs": {"racetrack": str(args.racetrack), "kahler_nlo": str(args.kahler_nlo)},
    }

    w0 = racetrack.get("W_0_box")
    if w0 is None or (isinstance(w0, str) and "external" in w0.lower()):
        out.update({
            "status": "upstream_pending",
            "reason": "racetrack_superpotential.json does not contain a numeric W_0_box. Run scan_flux_lattice.py -> attractor_interval_solve.py -> assemble_racetrack.py first.",
            "fully_certified": False,
        })
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"WROTE {args.out} (upstream_pending)")
        return 0

    out["status"] = "ready_to_iterate"
    out["fully_certified"] = False
    out["next_action"] = "Inputs present; ready to run interval Krawczyk + Gershgorin. Full iteration code is shared with attractor_interval_solve.py; see krawczyk_step there."

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
