# UGCT formal layer

What in the UGCT / *Principia* is proved, what is imported from published work, what is
assumed, and what was fitted — checked by machine on every commit
(`.github/workflows/ugct-formal.yml`).

| Path | What it is |
|---|---|
| `lean/` | Lean 4 + Mathlib proofs. `lean/report.txt` lists, for each theorem, every axiom it rests on (`#print axioms`). |
| `derivation_ledger.json` | The derivation graph: 82 nodes (postulates, measured inputs, theorems, imports, claims), one per line. |
| `check_ledger.py` | Ledger rules R0–R5. R5 compares every node's label with the Lean axiom report. |
| `fermat_point_couplings.py` | Weil–Petersson metric and normalized Yukawa coupling of the Fermat quintic, recomputed from the Picard–Fuchs equation alone. |
| `block_lattice.py` | H₃(X₅, ℤ) built from Pham's vanishing cycles, and the integral lattice of each character block (ledger T11). |
| `prereg/` | Pre-registered tests, committed before their results: the Law 1 exactness tests, the exact-coupling tests, the four generations of the evolutionary search (T14-T20) and the X₅ accuracy scans (T21, T22), with their scripts and output. |

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
5. `block_lattice.py`: builds H₃(X₅, ℤ) from Pham's vanishing cycles and checks that it is
   unimodular of rank 204, that the radical is the monodromy-fixed part, and that the
   (1,1,1,3,4) block carries 25 times the principal polarization used for T7.
6. `prereg/evolution_gen2.py`, `prereg/evolution_gen3.py` and `prereg/evolution_gen4.py`: the checks behind
   T14-T20.
   Generation 3 certifies in exact arithmetic (`prereg/exact_forms.py`, over ℚ(ζ₂₀)) that every
   charge of H₃(X₅, ℤ) has α⁻¹ ≤ 20.31: each block's Hodge form is built exactly and every vector up
   to the bound is enumerated. Both scripts exit with status 1 if any pre-registered check fails; the
   `prereg/test_*.py` files test the exact arithmetic and the pass/fail logic.
7. `prereg/x5_dictionary.py` and `prereg/x5_accuracy_scan.py`: 47 numbers that X₅ determines. Where
   possible they are recomputed from X₅'s defining data:
   * the Chern numbers;
   * the Gopakumar–Vafa numbers, from the periods in exact arithmetic;
   * the 51 Galois blocks;
   * the conifold newform of level 25, identified by point counts;
   * the L-values, checked with PARI.

   The scans then test whether any of the numbers makes Law 1 accurate (T21, T22). Scan A tries
   additive corrections to Law 1. Scan B tries products of up to three of the numbers against α⁻¹
   at CODATA precision, about 24.8 million forms. Both scans use null models. Every hit is
   recomputed at 50 digits, and the run fails if a window count differs from the verified count.

## Run locally

    cd lean
    lake exe cache get && lake build
    lake env lean Report.lean > report.txt
    cd ..
    python3 check_ledger.py derivation_ledger.json --lean lean/report.txt
    python3 fermat_point_couplings.py 40
    python3 block_lattice.py
    python3 prereg/test_exact_forms.py && python3 prereg/test_evolution_gen1_checks.py
    python3 prereg/test_evolution_gen2_checks.py
    python3 prereg/test_evolution_gen3_checks.py && python3 prereg/test_evolution_gen4_checks.py
    python3 prereg/evolution_gen2.py && python3 prereg/evolution_gen3.py && python3 prereg/evolution_gen4.py
    python3 prereg/test_x5_accuracy_checks.py && python3 prereg/x5_dictionary.py && python3 prereg/x5_accuracy_scan.py
