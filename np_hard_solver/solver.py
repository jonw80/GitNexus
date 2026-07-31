"""The solver, restructured so the control flow actually runs.

Control-flow defects fixed here, independent of the mathematics:

* ``num_qubits = len(problem_instance)`` reads the length of a *dict*, so a
  four-item knapsack was encoded on three qubits.
* ``hybrid_solver`` never calls ``classical_preprocessing``, so
  ``self.problem_instance`` is unset when ``post_process_result`` dereferences
  it -- the example at the end of the listing raises ``AttributeError`` on the
  first run.
* ``assemble_qaoa_circuit`` adds no measurement, so ``get_counts`` has nothing
  to return.
* ``select_quantum_algorithm`` falls off the end and returns ``None`` for any
  unrecognised problem, after which both branch variables are unbound.
* ``max_independent_set`` is routed to Grover but has no oracle branch.
* ``generate_datasets`` leaves ``datasets`` unbound for unknown problem types.
* ``IterativeRefinementModule._update_solver`` rebinds
  ``solver.quantum_annealing_solver.solve`` to a lambda that calls
  ``solve_with_quantum_annealing``, which calls ``quantum_annealing_solver.solve``
  -- unbounded recursion on the second refinement pass.  It also reads
  ``insights["total_weight"]``, a ``KeyError`` for partitioning and bin packing.
* ``analyze_datasets`` assigns into one ``insights`` dict inside the loop, so it
  returns statistics for the last instance rather than the corpus.
* Counts were indexed as left-to-right strings against qubit-0-is-rightmost
  registers, reversing the item order.

Scope note.  This solves these problems with quantum *heuristics* (QAOA) and
Grover search.  Neither is polynomial time.  See MATH_REVIEW.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from . import grover as grover_mod
from .qaoa import run_qaoa
from .qubo import (
    QUBO,
    bin_packing_qubo,
    first_fit_decreasing,
    knapsack_optimum,
    knapsack_qubo,
    partition_ising,
    partition_optimum,
)
from .repair import (
    bits_to_bin_indices,
    repair_bin_packing,
    repair_knapsack,
    repair_partition,
)
from .statevector import MAX_QUBITS


@dataclass
class Solution:
    problem: str
    assignment: list[int]
    objective: float
    feasible: bool
    method: str
    qubits_used: int
    optimal: bool | None = None
    classical_baseline: float | None = None
    quantum_improved_on_classical: bool | None = None
    detail: dict[str, Any] = field(default_factory=dict)


class NPHardSolver:
    """Hybrid quantum-classical heuristic solver for three NP-hard problems."""

    PROBLEM_CATEGORIES = {
        "graph_problems": ["max_independent_set"],
        "combinatorial_optimization": ["knapsack", "integer_partitioning", "bin_packing"],
        "satisfiability_problems": ["boolean_satisfiability"],
    }

    QAOA_PROBLEMS = {"knapsack", "integer_partitioning", "bin_packing"}
    GROVER_PROBLEMS = {"boolean_satisfiability", "max_independent_set"}

    def __init__(self, p: int = 3, seed: int = 0, shots: int = 1024):
        self.p = p
        self.seed = seed
        self.shots = shots
        self.rng = np.random.default_rng(seed)
        self.problem_instance: dict | None = None

    # -- dispatch -----------------------------------------------------------
    def classify_problem(self, problem: str) -> str:
        for category, problems in self.PROBLEM_CATEGORIES.items():
            if problem in problems:
                return category
        raise ValueError(
            f"unknown problem {problem!r}; supported: "
            f"{sorted(self.QAOA_PROBLEMS | self.GROVER_PROBLEMS)}"
        )

    def select_quantum_algorithm(self, specific_problem: str) -> str:
        self.classify_problem(specific_problem)          # raises on unknown
        return "QAOA" if specific_problem in self.QAOA_PROBLEMS else "Grover"

    def solve(self, problem_instance: dict, specific_problem: str) -> Solution:
        """Preprocess, run the quantum heuristic, repair, and report."""
        self.problem_instance = problem_instance          # the missing step
        algorithm = self.select_quantum_algorithm(specific_problem)
        if algorithm == "QAOA":
            return self._solve_qaoa(problem_instance, specific_problem)
        return self._solve_grover(problem_instance, specific_problem)

    # -- QAOA path ----------------------------------------------------------
    def _solve_qaoa(self, inst: dict, problem: str) -> Solution:
        if problem == "knapsack":
            weights, values = list(inst["weights"]), list(inst["values"])
            capacity = inst["capacity"]
            if len(weights) != len(values):
                raise ValueError(
                    f"{len(weights)} weights but {len(values)} values"
                )
            qubo = knapsack_qubo(weights, values, capacity)
            self._check_width(qubo.n, problem)
            result = run_qaoa(qubo.to_ising(), p=self.p, seed=self.seed, shots=self.shots)

            raw = result.best_bits[:len(weights)]
            sel = repair_knapsack(raw, weights, values, capacity)
            quantum_v = sum(values[i] for i in range(len(sel)) if sel[i])

            # Classical reference: the same repair pass seeded from the empty
            # set, i.e. plain greedy-by-density. Reporting it makes it visible
            # whether the quantum proposal contributed anything at all.
            greedy = repair_knapsack([0] * len(weights), weights, values, capacity)
            greedy_v = sum(values[i] for i in range(len(greedy)) if greedy[i])

            if greedy_v > quantum_v:
                sel, chosen_v, method = greedy, greedy_v, "greedy-by-density (beat QAOA)"
            else:
                chosen_v, method = quantum_v, "QAOA + greedy repair"

            total_w = sum(weights[i] for i in range(len(sel)) if sel[i])
            opt, _ = knapsack_optimum(weights, values, capacity)
            return Solution(
                problem=problem, assignment=sel, objective=float(chosen_v),
                feasible=total_w <= capacity, method=method,
                qubits_used=qubo.n, optimal=(chosen_v == opt),
                classical_baseline=float(greedy_v),
                quantum_improved_on_classical=bool(quantum_v > greedy_v),
                detail={"total_weight": total_w, "capacity": capacity,
                        "dp_optimum": opt, "raw_qaoa_bits": raw,
                        "qaoa_value": quantum_v, "greedy_value": greedy_v,
                        "ground_state_probability": result.ground_state_probability},
            )

        if problem == "integer_partitioning":
            numbers = list(inst["numbers"])
            ising = partition_ising(numbers)
            self._check_width(ising.n, problem)
            result = run_qaoa(ising, p=self.p, seed=self.seed, shots=self.shots)

            side = repair_partition(result.best_bits, numbers)
            quantum_diff = self._partition_difference(side, numbers)

            greedy_side = self._greedy_partition(numbers)
            greedy_diff = self._partition_difference(greedy_side, numbers)

            if greedy_diff < quantum_diff:
                side, diff = greedy_side, greedy_diff
                method = "largest-first greedy (beat QAOA)"
            else:
                diff, method = quantum_diff, "QAOA + local-search repair"

            s1 = sum(numbers[i] for i in range(len(side)) if side[i])
            s0 = sum(numbers[i] for i in range(len(side)) if not side[i])
            best = partition_optimum(numbers)
            return Solution(
                problem=problem, assignment=side, objective=float(diff),
                feasible=True, method=method,
                qubits_used=ising.n, optimal=(diff == best),
                classical_baseline=float(greedy_diff),
                quantum_improved_on_classical=bool(quantum_diff < greedy_diff),
                detail={"sum_a": s1, "sum_b": s0, "dp_minimum_difference": best,
                        "raw_qaoa_bits": result.best_bits,
                        "qaoa_difference": quantum_diff, "greedy_difference": greedy_diff,
                        "ground_state_probability": result.ground_state_probability},
            )

        if problem == "bin_packing":
            items = list(inst["items"])
            cap = inst["bin_capacity"]
            qubo = bin_packing_qubo(items, cap)
            n_bins = len(first_fit_decreasing(items, cap))
            self._check_width(qubo.n, problem)
            result = run_qaoa(qubo.to_ising(), p=self.p, seed=self.seed, shots=self.shots)

            raw = bits_to_bin_indices(result.best_bits, len(items), n_bins)
            assign = repair_bin_packing(raw, items, cap)
            quantum_bins = len(set(assign))

            ffd = first_fit_decreasing(items, cap)
            ffd_assign = [0] * len(items)
            for b, bin_items in enumerate(ffd):
                for i in bin_items:
                    ffd_assign[i] = b

            if len(ffd) < quantum_bins:
                assign, used = ffd_assign, len(ffd)
                method = "first-fit-decreasing (beat QAOA)"
            else:
                used, method = quantum_bins, "QAOA + first-fit repair"

            lower = int(np.ceil(sum(items) / cap))
            return Solution(
                problem=problem, assignment=assign, objective=float(used),
                feasible=True, method=method,
                qubits_used=qubo.n, optimal=(used == lower),
                classical_baseline=float(len(ffd)),
                quantum_improved_on_classical=bool(quantum_bins < len(ffd)),
                detail={"bins_used": used, "lower_bound": lower,
                        "ffd_bins": len(ffd), "qaoa_bins": quantum_bins,
                        "raw_bin_indices": raw,
                        "ground_state_probability": result.ground_state_probability},
            )

        raise ValueError(f"no QAOA formulation registered for {problem!r}")

    # -- Grover path --------------------------------------------------------
    def _solve_grover(self, inst: dict, problem: str) -> Solution:
        if problem == "boolean_satisfiability":
            clauses = inst["clauses"]
            n_vars = grover_mod.sat_num_variables(clauses)
            self._check_width(n_vars, problem)
            res = grover_mod.solve_sat(clauses, rng=self.rng)
            satisfied = (
                res.solution is not None
                and grover_mod.sat_predicate(clauses)(res.solution)
            )
            return Solution(
                problem=problem, assignment=res.solution or [], objective=float(satisfied),
                feasible=satisfied, method="Grover (BBHT schedule)",
                qubits_used=n_vars, optimal=satisfied,
                detail={"oracle_calls": res.oracle_calls,
                        "brute_force_calls": 2 ** n_vars,
                        "iterations": res.iterations_used},
            )

        if problem == "max_independent_set":
            # The original routes this to Grover and then provides no oracle,
            # returning a bare H + measure circuit.  Here it gets a real one.
            adjacency = inst["adjacency"]
            n = len(adjacency)
            self._check_width(n, problem)
            target = inst.get("target_size")
            if target is None:
                target = self._largest_independent_set_size(adjacency)

            def predicate(bits):
                if sum(bits) != target:
                    return False
                chosen = [i for i, b in enumerate(bits) if b]
                return all(
                    not adjacency[u][v]
                    for a, u in enumerate(chosen) for v in chosen[a + 1:]
                )

            res = grover_mod.bbht_search(n, predicate, rng=self.rng)
            found = res.solution is not None
            return Solution(
                problem=problem, assignment=res.solution or [],
                objective=float(sum(res.solution)) if found else 0.0,
                feasible=found, method="Grover (BBHT schedule)",
                qubits_used=n, optimal=found,
                detail={"target_size": target, "oracle_calls": res.oracle_calls,
                        "brute_force_calls": 2 ** n},
            )

        raise ValueError(f"no Grover oracle registered for {problem!r}")

    @staticmethod
    def _partition_difference(side, numbers) -> int:
        s1 = sum(numbers[i] for i in range(len(side)) if side[i])
        s0 = sum(numbers[i] for i in range(len(side)) if not side[i])
        return abs(s1 - s0)

    @staticmethod
    def _greedy_partition(numbers) -> list[int]:
        """Largest-first greedy: place each number on the currently lighter side."""
        side = [0] * len(numbers)
        s1 = s0 = 0
        for i in sorted(range(len(numbers)), key=lambda k: -numbers[k]):
            if s1 <= s0:
                side[i] = 1
                s1 += numbers[i]
            else:
                side[i] = 0
                s0 += numbers[i]
        return side

    @staticmethod
    def _largest_independent_set_size(adjacency) -> int:
        n = len(adjacency)
        best = 0
        for b in range(2 ** n):
            chosen = [i for i in range(n) if (b >> i) & 1]
            if all(not adjacency[u][v]
                   for a, u in enumerate(chosen) for v in chosen[a + 1:]):
                best = max(best, len(chosen))
        return best

    @staticmethod
    def _check_width(n_qubits: int, problem: str) -> None:
        if n_qubits > MAX_QUBITS:
            raise ValueError(
                f"{problem} needs {n_qubits} qubits, above the {MAX_QUBITS}-qubit "
                f"simulation limit. State-vector cost is 2**n; this is a hard "
                f"wall, not a tuning parameter."
            )
