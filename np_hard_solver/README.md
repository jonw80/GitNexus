# np_hard_solver

Mathematical audit and corrected implementation of the routines in
`UniversalNPHardSolver.pdf`.

**[MATH_REVIEW.md](MATH_REVIEW.md) is the write-up.** Start there.

## Running the verification

```bash
pip install -r requirements.txt
python3 -m np_hard_solver.verify_math
```

Fail-closed: exits non-zero if any check does not hold. 53 checks, covering
each defect in the review — one half showing the original is wrong, the other
showing the replacement is right. The bin-packing section runs a 16-qubit QAOA
optimisation and takes a few minutes.

## Using the solver

```python
from np_hard_solver import NPHardSolver

solver = NPHardSolver(p=3, seed=2)
sol = solver.solve(
    {"weights": [2, 3, 4, 5], "values": [3, 4, 5, 6], "capacity": 10},
    "knapsack",
)
print(sol.assignment, sol.objective, sol.optimal)
# [1, 1, 0, 1] 13.0 True
```

Supported: `knapsack`, `integer_partitioning`, `bin_packing` (QAOA),
`boolean_satisfiability`, `max_independent_set` (Grover).

Every result carries `classical_baseline` and
`quantum_improved_on_classical` so it is visible whether the quantum step
contributed anything. On instances small enough to simulate, it usually does
not.

## Scope

This is a **heuristic**, not a universal NP-hard solver. Grover's speedup is
quadratic and provably optimal among oracle methods (BBBV 1997), so the cost
stays exponential in the number of variables; QAOA carries no approximation
guarantee at fixed depth. Nothing here runs in polynomial time. The reasoning
is in [MATH_REVIEW.md](MATH_REVIEW.md).

Pure NumPy/SciPy — the original's `qiskit` and `cirq` calls target APIs that
were removed in Qiskit 1.0 or never existed.
