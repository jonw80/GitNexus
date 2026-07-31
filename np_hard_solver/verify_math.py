#!/usr/bin/env python3
"""Executable verification of every claim in MATH_REVIEW.md.

Fail-closed: exits non-zero if any check does not hold.  Each check has two
halves -- a demonstration that the original listing is wrong, and a
demonstration that the replacement in this package is right.

    python3 -m np_hard_solver.verify_math
"""

from __future__ import annotations

import itertools
import sys

import numpy as np

from .grover import (
    apply_sat_oracle,
    bbht_search,
    build_sat_oracle_circuit,
    grover_search,
    optimal_iterations,
    or_into_ancilla,
    original_iterations,
    sat_predicate,
    success_probability,
)
from .learning import (
    bin_packing_conjecture,
    knapsack_conjecture,
    original_labels_report,
    partition_conjecture,
)
from .mitigation import (
    apply_readout_noise,
    calibration_matrix,
    mitigate_readout,
    pec_mitigate_single_qubit,
    pec_quasiprobability,
    zero_noise_extrapolate,
)
from .qaoa import cost_layer_as_gates, original_qaoa_distribution, run_qaoa
from .qubo import (
    bin_packing_qubo,
    knapsack_optimum,
    knapsack_qubo,
    partition_ising,
    partition_optimum,
)
from .repair import repair_bin_packing, repair_knapsack, repair_partition
from .solver import NPHardSolver
from .statevector import StateVector, rx

FAILURES: list[str] = []
CHECKS = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f"  --  {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
def verify_qaoa_circuit() -> None:
    section("1. The original QAOA circuit outputs the uniform distribution")

    check("RX(2*pi*0.5) == RX(pi) == -i X",
          np.allclose(rx(np.pi), -1j * np.array([[0, 1], [1, 0]])),
          "so the 'mixer' is a NOT gate, not a variational rotation")

    for name, inst, kind in [
        ("knapsack", {"weights": [2, 3, 4, 5], "values": [3, 4, 5, 6], "capacity": 10}, "knapsack"),
        ("integer_partitioning", {"numbers": [8, 7, 6, 5]}, "integer_partitioning"),
        ("bin_packing", {"items": [4, 3, 3, 2], "bin_capacity": 6}, "bin_packing"),
    ]:
        probs = original_qaoa_distribution(inst, kind)
        dev = float(np.max(np.abs(probs - 1.0 / probs.size)))
        entropy = float(-np.sum(probs * np.log2(probs)))
        check(f"original {name} distribution is exactly uniform", dev < 1e-12,
              f"max deviation {dev:.2e}, entropy {entropy:.6f} of "
              f"{np.log2(probs.size):.0f} bits")

    # The replacement: cost layer as gates must equal the diagonal fast path.
    ising = knapsack_qubo([2, 3, 4, 5], [3, 4, 5, 6], 10).to_ising()
    energies = ising.energy_vector()
    gamma = 0.37
    a = StateVector(ising.n)
    a.h()
    a.apply_diagonal_phase(energies, gamma)
    b = StateVector(ising.n)
    b.h()
    cost_layer_as_gates(b, ising, gamma)
    # equal up to a global phase, which is unobservable
    overlap = abs(np.vdot(a.amps, b.amps)) / (np.linalg.norm(a.amps) * np.linalg.norm(b.amps))
    check("diagonal cost layer == explicit RZ/RZZ gate sequence", abs(overlap - 1.0) < 1e-10,
          f"|<a|b>| = {overlap:.12f}")

    res = run_qaoa(ising, p=3, seed=1, shots=2048)
    uniform = 1.0 / 2 ** ising.n
    check("corrected QAOA concentrates above uniform on the ground state",
          res.ground_state_probability > 2 * uniform,
          f"P(ground) = {res.ground_state_probability:.4f} vs uniform {uniform:.6f}")


def verify_qubo_derivation() -> None:
    section("2. QUBO couplings: w_i*w_j, not min(v_i, v_j)")

    weights, values, capacity = [2, 3, 4, 5], [3, 4, 5, 6], 10
    ratios = []
    for i in range(4):
        for j in range(i + 1, 4):
            ratios.append(weights[i] * weights[j] / min(values[i], values[j]))
    check("original coupling is not even proportional to the correct one",
          max(ratios) - min(ratios) > 1e-6,
          f"w_i*w_j / min(v_i,v_j) ranges over [{min(ratios):.3f}, {max(ratios):.3f}]")

    qubo = knapsack_qubo(weights, values, capacity)
    ising = qubo.to_ising()
    energies = ising.energy_vector()

    # QUBO energy and Ising energy vector must agree on every assignment.
    rng = np.random.default_rng(0)
    worst = 0.0
    for _ in range(400):
        x = rng.integers(0, 2, qubo.n)
        b = sum(int(v) << i for i, v in enumerate(x))
        worst = max(worst, abs(qubo.energy(x) - energies[b]))
    check("QUBO <-> Ising transform is exact", worst < 1e-9,
          f"max discrepancy {worst:.2e} over 400 random assignments")

    ground = int(np.argmin(energies))
    sel = [(ground >> i) & 1 for i in range(len(weights))]
    got_v = sum(values[i] for i in range(4) if sel[i])
    got_w = sum(weights[i] for i in range(4) if sel[i])
    opt, _ = knapsack_optimum(weights, values, capacity)
    check("knapsack QUBO ground state is the DP optimum",
          got_v == opt and got_w <= capacity,
          f"ground state {sel}: value {got_v} weight {got_w}/{capacity}, DP optimum {opt}")

    numbers = [3, 1, 4, 2, 2]
    pe = partition_ising(numbers).energy_vector()
    check("partition Ising ground energy == (minimum difference)^2",
          abs(pe.min() - partition_optimum(numbers) ** 2) < 1e-9,
          f"min energy {pe.min():.1f}, DP min difference {partition_optimum(numbers)}")

    # Penalty strength must actually force feasibility.
    bad = 0
    for b in range(2 ** qubo.n):
        s = [(b >> i) & 1 for i in range(len(weights))]
        if sum(weights[i] for i in range(4) if s[i]) > capacity:
            bad = max(bad, 1) if energies[b] <= energies[ground] else bad
    check("penalty makes every infeasible assignment cost more than the optimum",
          bad == 0, "no infeasible state reaches the ground energy")


def verify_grover() -> None:
    section("3. Grover iteration count and oracle construction")

    rows = [(10, 16), (12, 64), (16, 256)]
    for n, m in rows:
        N = 2 ** n
        k_orig = original_iterations(n)
        k_opt = optimal_iterations(N, m)
        p_orig = success_probability(N, m, k_orig)
        p_opt = success_probability(N, m, k_opt)
        check(f"corrected iteration count beats the original at n={n}, M={m}",
              p_opt > 10 * p_orig,
              f"original k={k_orig} -> P={p_orig:.4f};  corrected k={k_opt} -> P={p_opt:.4f}")

    check("original formula is correct only in the M=1 special case",
          original_iterations(4) == optimal_iterations(16, 1),
          f"n=4, M=1: both give k={original_iterations(4)}")

    # MCX is AND, not OR.
    disagreements = sum(1 for a in (0, 1) for b in (0, 1) if (a & b) != (a | b))
    check("bare mcx computes AND, so assemble_or_gate is not an OR",
          disagreements == 2, "differs from OR on inputs (0,1) and (1,0)")

    # The De Morgan OR gate is correct on all inputs, and leaves inputs intact.
    ok = True
    for a, b in itertools.product([0, 1], repeat=2):
        sv = StateVector(3)
        sv.x([q for q, bit in enumerate((a, b)) if bit])
        or_into_ancilla(sv, [0, 1], 2)
        state = int(np.argmax(sv.probabilities()))
        got = [(state >> q) & 1 for q in range(3)]
        if got != [a, b, a | b] or abs(sv.probabilities()[state] - 1) > 1e-12:
            ok = False
    check("or_into_ancilla computes OR and restores its inputs", ok,
          "checked on all 4 input assignments")

    # Gate-level SAT oracle agrees with the classical predicate, ancillas clean.
    clauses = [[1, -2, 3], [-1, 2], [2, 3], [-3, 1]]
    pred = sat_predicate(clauses)
    ok = True
    for assign in itertools.product([0, 1], repeat=3):
        sv, n_vars, out_q = build_sat_oracle_circuit(clauses)
        sv.x([q for q, bit in enumerate(assign) if bit])
        apply_sat_oracle(sv, clauses, n_vars, out_q)
        probs = sv.probabilities()
        state = int(np.argmax(probs))
        out_bit = (state >> out_q) & 1
        ancillas = [(state >> (n_vars + k)) & 1 for k in range(len(clauses))]
        if out_bit != int(pred(list(assign))) or any(ancillas) or abs(probs[state] - 1) > 1e-12:
            ok = False
    check("gate-level SAT oracle matches the predicate and uncomputes cleanly", ok,
          "checked on all 8 assignments")

    # Amplitude amplification actually amplifies.
    res = grover_search(8, lambda bits: sum(bits) == 8, rng=np.random.default_rng(0))
    check("Grover amplifies a single marked state on 8 qubits",
          res.success_probability > 0.99,
          f"P(success) = {res.success_probability:.4f} after {res.iterations_used} iterations")

    res = bbht_search(8, lambda bits: sum(bits) >= 7, rng=np.random.default_rng(0))
    check("BBHT finds a solution without knowing M",
          res.solution is not None and sum(res.solution) >= 7,
          f"{res.oracle_calls} oracle calls vs 256 for brute force")


def verify_complexity() -> None:
    section("4. Complexity: the speedup is quadratic, so the claim does not hold")

    n = 100
    calls = np.pi / 4 * np.sqrt(2.0 ** n)
    years = calls * 1e-9 / 3.15e7
    check("Grover on n=100 is not tractable", years > 1e-3,
          f"{calls:.3e} oracle calls; {years:.3e} years at one call per nanosecond")

    ratio = np.sqrt(2.0 ** 200) / np.sqrt(2.0 ** 100)
    check("cost still grows exponentially in n", ratio > 1e15,
          f"doubling n from 100 to 200 multiplies the cost by {ratio:.3e}")

    # The bin-packing register the original builds.
    for n_items in (10, 20):
        qubits = n_items * n_items
        check(f"original bin-packing register at {n_items} items is not simulable",
              qubits > 24,
              f"num_bins = num_items gives {qubits} qubits, "
              f"state dimension 2**{qubits} ~ {2.0 ** qubits:.2e}")

    # The corrected formulation uses an FFD-derived bin budget instead.
    qubo = bin_packing_qubo([4, 3, 3, 2], 6)
    check("corrected bin-packing register is small enough to run",
          qubo.n <= 24, f"{qubo.n} qubits for a 4-item instance")


def verify_repair() -> None:
    section("5. Classical repair heuristics move in the right direction")

    weights, values, capacity = [2, 3, 4, 5], [3, 4, 5, 6], 10

    # Original: over-capacity selection, remaining_capacity negative, no-op.
    over = [1, 1, 1, 1]
    total = sum(weights)
    check("the original's repair cannot fix an over-capacity selection",
          capacity - total < 0 and all(w > capacity - total for w in weights),
          f"remaining_capacity = {capacity - total}; no item satisfies "
          f"weight <= {capacity - total}, so the loop body never runs")

    fixed = repair_knapsack(over, weights, values, capacity)
    w_after = sum(weights[i] for i in range(4) if fixed[i])
    check("repair_knapsack returns a feasible selection", w_after <= capacity,
          f"{over} -> {fixed}, weight {w_after}/{capacity}")

    # Repair never makes a feasible solution worse.
    rng = np.random.default_rng(0)
    monotone = True
    for _ in range(200):
        n = int(rng.integers(2, 9))
        w = rng.integers(1, 20, size=n)
        v = rng.integers(1, 50, size=n)
        cap = int(rng.integers(int(w.min()), int(w.sum()) + 1))
        start = rng.integers(0, 2, n).tolist()
        out = repair_knapsack(start, w, v, cap)
        if sum(w[i] for i in range(n) if out[i]) > cap:
            monotone = False
        if sum(w[i] for i in range(n) if start[i]) <= cap:
            if sum(v[i] for i in range(n) if out[i]) < sum(v[i] for i in range(n) if start[i]):
                monotone = False
    check("repair_knapsack is always feasible and never worsens a feasible input",
          monotone, "200 random instances")

    # Original partition bookkeeping has the sign backwards.
    s1, s2 = [1, 2], [10]
    before = abs(sum(s1) - sum(s2))
    after = abs((sum(s1) - 1) - (sum(s2) + 1))
    check("moving an element to the heavier side increases the difference",
          after > before,
          f"difference {before} -> {after}, while the original records "
          f"'difference -= 2*num' i.e. {before - 2}")

    improved = True
    for _ in range(200):
        n = int(rng.integers(2, 11))
        nums = rng.integers(1, 50, size=n).tolist()
        start = rng.integers(0, 2, n).tolist()
        out = repair_partition(start, nums)
        d0 = abs(sum(nums[i] for i in range(n) if start[i])
                 - sum(nums[i] for i in range(n) if not start[i]))
        d1 = abs(sum(nums[i] for i in range(n) if out[i])
                 - sum(nums[i] for i in range(n) if not out[i]))
        if d1 > d0:
            improved = False
    check("repair_partition never increases the difference", improved,
          "200 random instances")

    # Bin packing repair handles duplicates, which items.index() cannot.
    items = [3, 3, 3, 3]
    out = repair_bin_packing([0, 0, 0, 0], items, 6)
    loads = {}
    for i, b in enumerate(out):
        loads[b] = loads.get(b, 0) + items[i]
    check("repair_bin_packing respects capacity with duplicate item sizes",
          all(v <= 6 for v in loads.values()),
          f"assignment {out}, bin loads {loads}")


def verify_mitigation() -> None:
    section("6. Error mitigation")

    truth = np.zeros(8)
    truth[5] = 1.0
    p_flip = 0.08
    noisy = apply_readout_noise(truth, p_flip)
    recovered = mitigate_readout(noisy, p_flip)
    check("readout mitigation recovers the true distribution",
          np.abs(recovered - truth).max() < 1e-3,
          f"error before {np.abs(noisy - truth).max():.4f}, "
          f"after {np.abs(recovered - truth).max():.2e}")
    check("mitigated output is a valid probability distribution",
          recovered.min() >= -1e-12 and abs(recovered.sum() - 1) < 1e-9,
          f"min {recovered.min():.2e}, sum {recovered.sum():.12f}")

    a = calibration_matrix(3, p_flip)
    check("calibration matrix columns are normalised",
          np.allclose(a.sum(axis=0), 1.0), "each true state maps to a distribution")

    # ZNE recovers the zero-noise value from a linear trend.
    scales = [1.0, 2.0, 3.0]
    dists = [np.array([0.5 + 0.1 * s, 0.5 - 0.1 * s]) for s in scales]
    out = zero_noise_extrapolate(dists, scales)
    check("ZNE extrapolates a linear trend back to zero noise",
          abs(out[0] - 0.5) < 1e-9, f"extrapolated {out[0]:.12f}, expected 0.5")
    check("ZNE output is a valid probability distribution",
          out.min() >= 0 and abs(out.sum() - 1) < 1e-12,
          f"min {out.min():.3f}, sum {out.sum():.12f}")

    # An empty noise model, as in the original, yields a flat trend and no change.
    flat = [np.array([0.7, 0.3])] * 3
    out = zero_noise_extrapolate(flat, scales)
    check("with an unscaled noise model ZNE is a no-op, as in the original",
          np.allclose(out, [0.7, 0.3]),
          "NoiseModel() is empty and has no .scale(), so all three runs coincide")

    coeffs, gamma = pec_quasiprobability(0.1)
    check("PEC decomposition has a negative coefficient and gamma > 1",
          coeffs[1] < 0 and gamma > 1,
          f"coefficients {coeffs.round(4).tolist()}, sampling overhead gamma={gamma:.4f}")

    single_truth = np.array([1.0, 0.0])
    single_noisy = np.array([0.9, 0.1])
    check("PEC inverts the bit-flip channel",
          np.abs(pec_mitigate_single_qubit(single_noisy, 0.1) - single_truth).max() < 1e-9,
          "the original instead *injects* rx(2 arcsin(sqrt(p))) and sums counts")


def verify_learning() -> None:
    section("7. ML conjecture generation")

    for c in original_labels_report(n_instances=800, seed=0):
        check(f"original label for {c.problem} carries no signal",
              not c.significant, c.summary())

    results = [knapsack_conjecture(n_instances=500),
               partition_conjecture(n_instances=500),
               bin_packing_conjecture(n_instances=500)]
    for c in results:
        print(f"       {c.summary()}")
    check("at least one corrected label is significant against a permutation null",
          any(c.significant for c in results),
          f"{sum(c.significant for c in results)} of 3 significant")

    part = next(c for c in results if c.problem == "integer_partitioning")
    top = max(zip(part.feature_names, part.feature_importances), key=lambda t: t[1])
    check("perfect-partition model keys on sum parity, as theory requires",
          top[0] == "sum_parity",
          f"top feature {top[0]!r} at importance {top[1]:.3f}")


def verify_solver() -> None:
    section("8. End-to-end solver (the example from the last page of the PDF)")

    solver = NPHardSolver(p=3, seed=2)

    sol = solver.solve({"weights": [2, 3, 4, 5], "values": [3, 4, 5, 6], "capacity": 10},
                       "knapsack")
    check("knapsack example runs and returns a feasible packing", sol.feasible,
          f"selection {sol.assignment}, value {sol.objective:.0f}, "
          f"weight {sol.detail['total_weight']}/{sol.detail['capacity']}")
    check("knapsack example attains the DP optimum", bool(sol.optimal),
          f"value {sol.objective:.0f}, DP optimum {sol.detail['dp_optimum']}")

    sol = solver.solve({"numbers": [8, 7, 6, 5, 4]}, "integer_partitioning")
    check("partition example attains the DP minimum difference", bool(sol.optimal),
          f"difference {sol.objective:.0f}, DP minimum "
          f"{sol.detail['dp_minimum_difference']}")

    sol = solver.solve({"items": [4, 3, 3, 2], "bin_capacity": 6}, "bin_packing")
    loads: dict[int, int] = {}
    for i, b in enumerate(sol.assignment):
        loads[b] = loads.get(b, 0) + [4, 3, 3, 2][i]
    check("bin packing example respects capacity", all(v <= 6 for v in loads.values()),
          f"assignment {sol.assignment}, loads {loads}, "
          f"{sol.objective:.0f} bins vs lower bound {sol.detail['lower_bound']}")

    sol = solver.solve({"clauses": [[1, -2, 3], [-1, 2], [2, 3], [-3, 1]]},
                       "boolean_satisfiability")
    check("SAT example returns a satisfying assignment", sol.feasible,
          f"assignment {sol.assignment}, {sol.detail['oracle_calls']} oracle calls "
          f"vs {sol.detail['brute_force_calls']} for brute force")

    sol = solver.solve({"adjacency": [[0, 1, 0, 0], [1, 0, 1, 0],
                                      [0, 1, 0, 1], [0, 0, 1, 0]]},
                       "max_independent_set")
    check("max_independent_set gets a real oracle and finds a maximum set",
          sol.feasible and sol.objective == 2,
          f"set {sol.assignment}, size {sol.objective:.0f} "
          f"(the original routes this to Grover with no oracle at all)")

    # Control-flow defects that used to raise.
    try:
        solver.select_quantum_algorithm("travelling_salesman")
        raised = False
    except ValueError:
        raised = True
    check("unknown problems raise instead of returning None", raised,
          "the original falls off the end of select_quantum_algorithm")

    try:
        solver.solve({"weights": [1, 2], "values": [1], "capacity": 3}, "knapsack")
        raised = False
    except ValueError:
        raised = True
    check("mismatched weights/values are rejected", raised)

    try:
        NPHardSolver._check_width(400, "bin_packing")
        raised = False
    except ValueError:
        raised = True
    check("oversized registers are rejected with a clear error", raised,
          "400 qubits is refused rather than silently attempted")


def main() -> int:
    print("Verification of UniversalNPHardSolver.pdf")
    print("Each section states what the original does and what replaces it.")

    verify_qaoa_circuit()
    verify_qubo_derivation()
    verify_grover()
    verify_complexity()
    verify_repair()
    verify_mitigation()
    verify_learning()
    verify_solver()

    section("SUMMARY")
    print(f"  {CHECKS - len(FAILURES)} of {CHECKS} checks passed")
    if FAILURES:
        print("  FAILED:")
        for f in FAILURES:
            print(f"    - {f}")
        return 1
    print("  All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
