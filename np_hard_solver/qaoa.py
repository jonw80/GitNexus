"""QAOA, with the variational loop the original omits.

Three separate defects are fixed here.

1. The original applies a single cost layer and then
   ``qaoa_circuit.rx(2 * np.pi * 0.5, range(num_qubits))``.  RX(pi) = -i X, so
   the "mixer" is a NOT on every qubit: a permutation of the computational
   basis.  Since H^{\\otimes n} produces a uniform amplitude distribution and
   the cost layer is diagonal (phases only), the measured distribution is
   *exactly uniform* -- provably independent of the problem data.  A real
   mixer is RX(2 beta) with beta a free parameter.

2. There is no classical optimisation of (gamma, beta).  ``COBYLA`` and
   ``QAOA`` are imported and never used.  Here the angles are optimised
   against the true expectation value <H_C>.

3. The cost layer uses ``min(values[i], values[j]) / capacity`` instead of the
   couplings derived in :mod:`np_hard_solver.qubo`.

The cost unitary exp(-i gamma H_C) is applied directly to the diagonal of
H_C.  That is the same operator the RZ/RZZ gate sequence implements -- see
:func:`cost_layer_as_gates`, which is checked against it in the test suite --
but evaluating it in one pass keeps the optimisation loop cheap.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from .qubo import Ising
from .statevector import StateVector


@dataclass
class QAOAResult:
    best_bits: list[int]
    best_energy: float
    expectation: float
    gammas: np.ndarray
    betas: np.ndarray
    probabilities: np.ndarray
    n_evaluations: int
    shots: int
    ground_state_probability: float
    found_ground_state: bool


def cost_layer_as_gates(sv: StateVector, ising: Ising, gamma: float) -> StateVector:
    """exp(-i gamma H_C) written out as the RZ/RZZ sequence it decomposes into.

    Kept so the diagonal fast path can be verified against an explicit gate
    sequence rather than taken on trust.
    """
    for q in range(ising.n):
        if ising.h[q] != 0.0:
            sv.rz(2.0 * gamma * float(ising.h[q]), q)
    for i in range(ising.n):
        for j in range(i + 1, ising.n):
            if ising.J[i, j] != 0.0:
                sv.rzz(2.0 * gamma * float(ising.J[i, j]), i, j)
    return sv


def run_qaoa(
    ising: Ising,
    p: int = 3,
    seed: int = 0,
    n_restarts: int = 4,
    maxiter: int = 400,
    shots: int = 1024,
) -> QAOAResult:
    """Optimise the QAOA angles for a diagonal cost Hamiltonian.

    The returned assignment is the best of ``shots`` *sampled* bitstrings, which
    is what a real device yields.  Picking the lowest-energy state anywhere in
    the support of the final distribution would flatter the method: that state
    is present with non-zero amplitude even for random angles, so reporting it
    would measure the enumeration, not the optimisation.
    """
    if p < 1:
        raise ValueError(f"p must be at least 1, got {p}")
    energies = ising.energy_vector()
    n = ising.n
    rng = np.random.default_rng(seed)

    # Normalise the cost scale so a single gamma range covers every instance;
    # without this, gamma * H_C wraps around 2*pi and the landscape is hostile.
    scale = float(np.std(energies))
    if scale == 0.0:
        scale = 1.0
    reduced = energies / scale

    evaluations = 0

    def prepare(params: np.ndarray) -> np.ndarray:
        nonlocal evaluations
        evaluations += 1
        gammas, betas = params[:p], params[p:]
        sv = StateVector(n)
        sv.h()
        for layer in range(p):
            sv.apply_diagonal_phase(reduced, float(gammas[layer]))
            sv.rx(2.0 * float(betas[layer]))       # the mixer, with a free beta
        return sv.probabilities()

    def objective(params: np.ndarray) -> float:
        return float(prepare(params) @ energies)

    best = None
    for _ in range(n_restarts):
        x0 = np.concatenate([
            rng.uniform(0.0, np.pi, size=p),
            rng.uniform(0.0, np.pi / 2.0, size=p),
        ])
        res = minimize(objective, x0, method="COBYLA",
                       options={"maxiter": maxiter, "rhobeg": 0.35})
        if best is None or res.fun < best.fun:
            best = res

    probs = prepare(best.x)

    sv = StateVector(n)
    sv.amps = np.sqrt(probs).astype(complex)
    counts = sv.sample(shots, rng)
    best_state = min(counts, key=lambda b: energies[b])

    ground_energy = float(energies.min())
    ground_prob = float(probs[np.isclose(energies, ground_energy)].sum())
    return QAOAResult(
        best_bits=[(best_state >> q) & 1 for q in range(n)],
        best_energy=float(energies[best_state]),
        expectation=float(best.fun),
        gammas=best.x[:p],
        betas=best.x[p:],
        probabilities=probs,
        n_evaluations=evaluations,
        shots=shots,
        ground_state_probability=ground_prob,
        found_ground_state=bool(np.isclose(energies[best_state], ground_energy)),
    )


def original_qaoa_distribution(problem_instance: dict, specific_problem: str) -> np.ndarray:
    """Reproduce the listing's circuit verbatim, for the regression check.

    Faithful to pages 3-4 of the PDF, including ``num_qubits =
    len(problem_instance)``.  Returns the measured probability distribution,
    which the test suite asserts is uniform.
    """
    num_qubits = len(problem_instance)          # the original's dict-length bug
    sv = StateVector(num_qubits)
    sv.h()
    if specific_problem == "knapsack":
        values = problem_instance["values"]
        capacity = problem_instance["capacity"]
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                sv.rzz(2 * np.pi * min(values[i], values[j]) / capacity, i, j)
    elif specific_problem == "integer_partitioning":
        numbers = problem_instance["numbers"]
        target_sum = sum(numbers) // 2
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                sv.rzz(2 * np.pi * min(numbers[i], numbers[j]) / target_sum, i, j)
    elif specific_problem == "bin_packing":
        items = problem_instance["items"]
        bin_capacity = problem_instance["bin_capacity"]
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                sv.rzz(2 * np.pi * min(items[i], items[j]) / bin_capacity, i, j)
    sv.rx(2 * np.pi * 0.5)                      # the original's fixed "mixer"
    return sv.probabilities()
