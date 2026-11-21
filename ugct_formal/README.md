# UGCT formal layer

What in the UGCT / *Principia* is proved, what is imported from published work, what is
assumed, and what was fitted — checked by machine on every commit
(`.github/workflows/ugct-formal.yml`).

| Path | What it is |
|---|---|
| `lean/` | Lean 4 + Mathlib proofs. `lean/report.txt` lists, for each theorem, every axiom it rests on (`#print axioms`). |
| `derivation_ledger.json` | The derivation graph: 65 nodes (postulates, measured inputs, theorems, imports, claims), one per line. |
| `check_ledger.py` | Ledger rules R0–R5. R5 compares every node's label with the Lean axiom report. |
| `fermat_point_couplings.py` | Weil–Petersson metric and normalized Yukawa coupling of the Fermat quintic, recomputed from the Picard–Fuchs equation alone. |

## What CI checks

1. `lake build`: Lean's kernel checks every proof; any `sorry` fails the run.
2. The regenerated axiom report must equal the committed `lean/report.txt`.
3. `check_ledger.py --lean`: a node marked PROVEN may not rest on a postulate or conjecture;
   a claim whose Lean theorem uses a postulate must list that postulate upstream.
4. `fermat_point_couplings.py`: from the Picard–Fuchs equation of X₅, the conifold monodromy
   and Hodge theory, it recomputes at the Fermat point
   * g(0) = 25 (γ(2/5)/γ(1/5))⁵ = 0.19225645…,
   * normalized Yukawa = κ⁵ = 1.55531899…, with κ² = γ(1/5)/γ(2/5)³ (Distler–Greene),
   * and, as a control, χ(X₅) = −200 from the large-complex-structure limit.

   γ(x) = Γ(x)/Γ(1−x). Nothing physical goes in and nothing is fitted. The run fails if any
   value disagrees.

## Run locally

    cd lean
    lake exe cache get && lake build
    lake env lean Report.lean > report.txt
    cd ..
    python3 check_ledger.py derivation_ledger.json --lean lean/report.txt
    python3 fermat_point_couplings.py 40
