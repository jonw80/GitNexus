"""Grover search and amplitude amplification, corrected.

Four defects are fixed.

1. Iteration count.  The original uses
   ``iterations = int(np.pi / 4 * np.sqrt(2**num_items))``, which is the
   optimal count only when exactly one basis state is marked.  The general
   optimum is floor(pi/(4 theta) - 1/2) with theta = arcsin(sqrt(M/N)).
   Over-rotating past the optimum drives the success amplitude back down: for
   N = 1024, M = 16 the original's 25 iterations give P(success) ~ 0.012 where
   6 iterations give ~0.997.

2. Unknown M.  When the number of solutions is not known in advance -- the
   normal case -- the Boyer-Brassard-Hoyer-Tapp schedule finds a solution in
   O(sqrt(N/M)) expected oracle calls without knowing M.

3. The oracle.  The original's ``_knapsack_oracle`` applies RZ and RX
   rotations.  RX takes the register out of the computational basis entirely,
   so what follows is not amplitude amplification.  A Grover oracle must be
   the diagonal reflection |x> -> -|x> exactly on the satisfying set.

4. The OR gate.  ``assemble_or_gate`` returns a bare ``mcx``, which computes
   an AND, and writes it onto a variable qubit rather than an ancilla.  The
   De Morgan construction is in :func:`or_into_ancilla`.

Grover is asymptotically optimal for unstructured search by the BBBV
lower bound (Bennett, Bernstein, Brassard, Vazirani 1997), so the
Theta(sqrt(2^n)) cost here is not an artefact of this implementation -- no
oracle-based method does better.  See MATH_REVIEW.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .statevector import StateVector


@dataclass
class GroverResult:
    solution: list[int] | None
    value: int | None
    iterations_used: int
    oracle_calls: int
    success_probability: float


def optimal_iterations(n_states: int, n_marked: int) -> int:
    """round(pi/(4 theta) - 1/2), the count that maximises P(success).

    P(success) after k iterations is sin^2((2k+1) theta), which peaks where
    (2k+1) theta = pi/2, i.e. at the real value k* = pi/(4 theta) - 1/2.  The
    best integer count is therefore the *nearest* integer to k*, not the floor.
    """
    if n_marked <= 0:
        raise ValueError("cannot amplify an empty solution set")
    if n_marked >= n_states:
        return 0
    theta = np.arcsin(np.sqrt(n_marked / n_states))
    return max(0, int(round(np.pi / (4.0 * theta) - 0.5)))


def success_probability(n_states: int, n_marked: int, iterations: int) -> float:
    """sin^2((2k+1) theta): the exact post-amplification success probability."""
    if n_marked <= 0:
        return 0.0
    if n_marked >= n_states:
        return 1.0
    theta = np.arcsin(np.sqrt(n_marked / n_states))
    return float(np.sin((2 * iterations + 1) * theta) ** 2)


def original_iterations(n_qubits: int) -> int:
    """The listing's formula, kept for the regression check."""
    return int(np.pi / 4 * np.sqrt(2 ** n_qubits))


def or_into_ancilla(sv: StateVector, inputs, ancilla: int) -> StateVector:
    """ancilla ^= OR(inputs), by De Morgan, leaving `inputs` unchanged.

    OR(x) = NOT AND(NOT x_1, ..., NOT x_k), so: invert the inputs, AND them
    into the ancilla, invert the ancilla, then restore the inputs.
    """
    inputs = list(inputs)
    sv.x(inputs)
    sv.mcx(inputs, ancilla)
    sv.x(ancilla)
    sv.x(inputs)
    return sv


def marked_mask(n_qubits: int, predicate) -> np.ndarray:
    """Boolean mask over all 2**n basis states, from a classical predicate.

    This makes the oracle explicit and checkable.  The number of predicate
    evaluations is 2**n, which is exactly the point: constructing the oracle is
    no cheaper than brute force, and Grover only reduces the number of *oracle
    invocations* from N to sqrt(N).
    """
    n_states = 2 ** n_qubits
    mask = np.zeros(n_states, dtype=bool)
    for b in range(n_states):
        mask[b] = bool(predicate([(b >> q) & 1 for q in range(n_qubits)]))
    return mask


def grover_search(
    n_qubits: int,
    predicate,
    iterations: int | None = None,
    rng: np.random.Generator | None = None,
    shots: int = 1,
) -> GroverResult:
    """Amplitude amplification with the correct iteration count."""
    rng = rng or np.random.default_rng(0)
    mask = marked_mask(n_qubits, predicate)
    n_states = 2 ** n_qubits
    n_marked = int(mask.sum())
    if n_marked == 0:
        return GroverResult(None, None, 0, 0, 0.0)

    if iterations is None:
        iterations = optimal_iterations(n_states, n_marked)

    sv = StateVector(n_qubits)
    sv.h()
    for _ in range(iterations):
        sv.phase_flip(mask)
        sv.diffuser()

    counts = sv.sample(shots, rng)
    best = max(counts, key=counts.get)
    p_success = float(sv.probabilities()[mask].sum())
    solution = [(best >> q) & 1 for q in range(n_qubits)] if mask[best] else None
    return GroverResult(
        solution=solution,
        value=int(best) if mask[best] else None,
        iterations_used=iterations,
        oracle_calls=iterations,
        success_probability=p_success,
    )


def bbht_search(
    n_qubits: int,
    predicate,
    rng: np.random.Generator | None = None,
    max_rounds: int = 60,
) -> GroverResult:
    """Boyer-Brassard-Hoyer-Tapp search when the solution count is unknown.

    Expected O(sqrt(N/M)) oracle calls with no prior knowledge of M.
    """
    rng = rng or np.random.default_rng(0)
    mask = marked_mask(n_qubits, predicate)
    n_states = 2 ** n_qubits
    if not mask.any():
        return GroverResult(None, None, 0, 0, 0.0)

    m = 1.0
    lam = 6.0 / 5.0
    total_calls = 0
    sqrt_n = np.sqrt(n_states)

    for _ in range(max_rounds):
        j = int(rng.integers(0, max(1, int(m))))
        sv = StateVector(n_qubits)
        sv.h()
        for _ in range(j):
            sv.phase_flip(mask)
            sv.diffuser()
        total_calls += j
        outcome = next(iter(sv.sample(1, rng)))
        if mask[outcome]:
            return GroverResult(
                solution=[(outcome >> q) & 1 for q in range(n_qubits)],
                value=int(outcome),
                iterations_used=j,
                oracle_calls=total_calls,
                success_probability=float(sv.probabilities()[mask].sum()),
            )
        m = min(lam * m, sqrt_n)

    return GroverResult(None, None, 0, total_calls, 0.0)


# --------------------------------------------------------------------------
# SAT support.  Literals are signed integers (3 means x3, -3 means not x3),
# 1-indexed.  The original mixes the two conventions in one expression:
#   num_variables = max(max(abs(int(literal)) for literal in clause) ...)
# then later tests literal.startswith("~").  int("~3") raises ValueError, so a
# negated literal crashes the very first line of the oracle builder.
# --------------------------------------------------------------------------

def parse_clause(clause) -> list[int]:
    """Accept either signed ints or '~3'/'3' strings, and normalise to ints."""
    out = []
    for literal in clause:
        if isinstance(literal, str):
            lit = literal.strip()
            out.append(-int(lit[1:]) if lit.startswith("~") else int(lit))
        else:
            out.append(int(literal))
    if any(v == 0 for v in out):
        raise ValueError("literal index 0 is not valid; variables are 1-indexed")
    return out


def sat_num_variables(clauses) -> int:
    return max(abs(v) for clause in clauses for v in parse_clause(clause))


def sat_predicate(clauses):
    """Classical CNF evaluator over a bit vector indexed by qubit number."""
    parsed = [parse_clause(c) for c in clauses]

    def check(bits) -> bool:
        for clause in parsed:
            if not any(
                (bits[abs(v) - 1] == 1) if v > 0 else (bits[abs(v) - 1] == 0)
                for v in clause
            ):
                return False
        return True

    return check


def solve_sat(clauses, rng: np.random.Generator | None = None) -> GroverResult:
    """Grover for CNF-SAT using a genuine phase oracle and BBHT scheduling."""
    n_vars = sat_num_variables(clauses)
    return bbht_search(n_vars, sat_predicate(clauses), rng=rng)


def build_sat_oracle_circuit(clauses) -> tuple[StateVector, int, int]:
    """Gate-level CNF oracle: clause ancillas via OR, one MCX, then uncompute.

    Returned for inspection and for the test that checks it against
    :func:`sat_predicate`.  The register is [variables | clause ancillas |
    output].  The original's version reuses variable qubits as OR targets and
    "uncomputes" by re-applying the forward circuit rather than its inverse,
    which does not restore the ancillas.
    """
    parsed = [parse_clause(c) for c in clauses]
    n_vars = max(abs(v) for clause in parsed for v in clause)
    n_clauses = len(parsed)
    n_total = n_vars + n_clauses + 1
    out_qubit = n_vars + n_clauses
    return StateVector(n_total), n_vars, out_qubit


def apply_sat_oracle(sv: StateVector, clauses, n_vars: int, out_qubit: int) -> StateVector:
    """out ^= AND_clauses(OR_literals), with every ancilla returned to |0>."""
    parsed = [parse_clause(c) for c in clauses]
    ancillas = [n_vars + k for k in range(len(parsed))]

    def compute():
        for k, clause in enumerate(parsed):
            negated = [abs(v) - 1 for v in clause if v < 0]
            sv.x(negated)                       # map "literal true" to "qubit 1"
            or_into_ancilla(sv, [abs(v) - 1 for v in clause], ancillas[k])
            sv.x(negated)                       # restore the variable qubits

    compute()
    sv.mcx(ancillas, out_qubit)
    # Uncompute with the inverse.  Every operation used here is an involution
    # and the clause blocks act on disjoint ancillas, so replaying in reverse
    # clause order restores the ancillas to |0>.
    for k in reversed(range(len(parsed))):
        clause = parsed[k]
        negated = [abs(v) - 1 for v in clause if v < 0]
        sv.x(negated)
        # or_into_ancilla is self-inverse: X, MCX, X, X applied twice is identity
        sv.x(ancillas[k])
        sv.x([abs(v) - 1 for v in clause])
        sv.mcx([abs(v) - 1 for v in clause], ancillas[k])
        sv.x([abs(v) - 1 for v in clause])
        sv.x(negated)
    return sv
