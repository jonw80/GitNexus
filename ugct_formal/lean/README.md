# UGCT formal layer (Lean 4 + Mathlib)

Machine-checked part of the UGCT derivation graph. Lean's kernel checks every proof, and
`#print axioms` lists everything each theorem rests on. Explanation and results:
`claude/FORMAL_DERIVATION_SYSTEM_2026-11-21.md`.

## Layers
| Module | Layer | What may appear in `#print axioms` |
|---|---|---|
| `Ugct/Foundations.lean` | mathematics: Gauss multiplication at n = 5, the Law 1 identity | Lean's three (`propext`, `Classical.choice`, `Quot.sound`) |
| `Ugct/Grading.lean` | mathematics: which Γ-monomials the periods produce (iff grade 0) | Lean's three |
| `Ugct/FermatPoint.lean` | mathematics: every Fermat-point Weil–Petersson and normalized-Yukawa monomial has grade 0 | Lean's three |
| `Ugct/Conditional.lean` | mathematics resting on an open conjecture | Lean's three + `rohrlich_five` |
| `Ugct/Postulates.lean` | physics: postulates as named axioms; Law 1 | Lean's three + the postulates used |

Measured numbers never appear here. Comparison with data is a separate step, run only after a
derived expression is frozen.

## Build and check
Requires [elan](https://github.com/leanprover/elan). In this folder:

    lake exe cache get                       # prebuilt Mathlib, about 2-3 minutes
    lake build                               # kernel-checks all modules
    lake env lean Report.lean > report.txt   # axioms of every reported theorem
    python3 ../check_ledger.py ../derivation_ledger.json --lean report.txt

The last command fails if any ledger label disagrees with what Lean reports: for example a node
marked PROVEN whose theorem uses a postulate, or a claim whose theorem uses a postulate the ledger
does not list upstream.

Versions: Lean `v4.37.0-rc1`, Mathlib `v4.37.0-rc1` (pinned in `lake-manifest.json`). Mathlib's
style linters are switched off in `lakefile.toml`; this does not affect kernel checking.

## Adding a result
1. State and prove it as a Lean theorem in the right layer. A proof containing `sorry` shows up
   as `sorryAx` in the report and is rejected by the checker.
2. A new physical assumption becomes an `axiom` in `Postulates.lean`, named with its ledger id
   (`P12_...`), and is added to `meta.lean.axiom_map` in the ledger. An open mathematical
   statement becomes an `axiom` named as a conjecture and gets a CONJECTURE node.
3. Add `#print axioms <name>` to `Report.lean`.
4. Add the theorem name to the node's `"lean"` list in `derivation_ledger.json`.
5. Rebuild, regenerate `report.txt`, rerun the checker.
