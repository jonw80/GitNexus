"""Exact state-vector simulator.

The listing under review imports ``Aer`` and ``execute`` from ``qiskit`` and
``QAOA``/``COBYLA``/``QAOAAnsatz`` from ``qiskit.algorithms``.  Both were
removed in Qiskit 1.0, and ``cirq``, ``QuantumRegister``, ``ClassicalRegister``,
``GroverOperator``, ``NoiseModel``, ``complete_meas_cal`` and
``CompleteMeasFitter`` are used without ever being imported.  ``mcz`` and
``mct`` are not methods of ``QuantumCircuit`` at all.  Rather than pin a dead
API, this module implements the handful of operations the algorithms actually
need, exactly, in NumPy.

Bit convention: qubit ``q`` is bit ``q`` of the basis-state index, i.e. qubit 0
is the least significant bit.  Measurement results are returned as integers and
as explicit ``list[int]`` bit vectors indexed by qubit number, never as strings
that a caller has to remember to reverse.
"""

from __future__ import annotations

import numpy as np

MAX_QUBITS = 24
"""Refuse to allocate beyond this.  2**24 complex128 amplitudes is 256 MiB."""

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def rx(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def rz(theta: float) -> np.ndarray:
    return np.array([[np.exp(-1j * theta / 2), 0],
                     [0, np.exp(1j * theta / 2)]], dtype=complex)


class StateVector:
    """A pure state on ``n`` qubits, initialised to |0...0>."""

    def __init__(self, n: int):
        if n < 1:
            raise ValueError(f"need at least one qubit, got {n}")
        if n > MAX_QUBITS:
            raise ValueError(
                f"{n} qubits exceeds the {MAX_QUBITS}-qubit simulation limit "
                f"(state vector would need 2**{n} amplitudes). This is the "
                f"wall the original bin-packing encoding hits at 400 qubits."
            )
        self.n = n
        self.amps = np.zeros(2 ** n, dtype=complex)
        self.amps[0] = 1.0

    # -- single-qubit gates -------------------------------------------------
    def apply_1q(self, q: int, u: np.ndarray) -> "StateVector":
        if not 0 <= q < self.n:
            raise IndexError(f"qubit {q} out of range for {self.n} qubits")
        axis = self.n - 1 - q
        t = self.amps.reshape([2] * self.n)
        t = np.tensordot(u, t, axes=([1], [axis]))
        self.amps = np.moveaxis(t, 0, axis).reshape(-1)
        return self

    def h(self, qubits=None) -> "StateVector":
        for q in self._targets(qubits):
            self.apply_1q(q, H)
        return self

    def x(self, qubits=None) -> "StateVector":
        for q in self._targets(qubits):
            self.apply_1q(q, X)
        return self

    def rx(self, theta: float, qubits=None) -> "StateVector":
        for q in self._targets(qubits):
            self.apply_1q(q, rx(theta))
        return self

    def rz(self, theta: float, qubits=None) -> "StateVector":
        for q in self._targets(qubits):
            self.apply_1q(q, rz(theta))
        return self

    def _targets(self, qubits):
        if qubits is None:
            return range(self.n)
        if isinstance(qubits, int):
            return [qubits]
        return list(qubits)

    # -- two-qubit and multi-qubit gates ------------------------------------
    def rzz(self, theta: float, i: int, j: int) -> "StateVector":
        """exp(-i theta/2 Z_i Z_j), applied as a diagonal phase."""
        idx = np.arange(self.amps.size)
        zi = 1 - 2 * ((idx >> i) & 1)
        zj = 1 - 2 * ((idx >> j) & 1)
        self.amps = self.amps * np.exp(-1j * theta / 2 * zi * zj)
        return self

    def mcx(self, controls, target: int) -> "StateVector":
        """Multi-controlled X: target ^= AND(controls).

        Note this is an AND, which is exactly why the original
        ``assemble_or_gate`` -- a bare ``mcx`` -- does not compute an OR.
        See :func:`np_hard_solver.grover.or_into_ancilla` for the correct
        De Morgan construction.
        """
        controls = list(controls)
        if target in controls:
            raise ValueError("target qubit may not also be a control")
        idx = np.arange(self.amps.size)
        mask = np.ones(self.amps.size, dtype=bool)
        for c in controls:
            mask &= ((idx >> c) & 1).astype(bool)
        src = idx[mask]
        # controls are unchanged by flipping the target, so `src` is closed
        # under `^ (1 << target)` and this assignment is a clean involution.
        self.amps[src] = self.amps[src ^ (1 << target)]
        return self

    # -- diagonal operations ------------------------------------------------
    def apply_diagonal_phase(self, energies: np.ndarray, gamma: float) -> "StateVector":
        """exp(-i gamma H) for a diagonal H given by its eigenvalue vector."""
        if energies.shape != self.amps.shape:
            raise ValueError(
                f"energy vector has length {energies.shape[0]}, expected "
                f"{self.amps.shape[0]}"
            )
        self.amps = self.amps * np.exp(-1j * gamma * energies)
        return self

    def phase_flip(self, marked: np.ndarray) -> "StateVector":
        """The Grover oracle proper: |x> -> -|x> for marked x, identity else."""
        self.amps = np.where(marked, -self.amps, self.amps)
        return self

    def diffuser(self) -> "StateVector":
        """Grover diffusion 2|s><s| - I about the uniform superposition."""
        self.amps = 2 * self.amps.mean() - self.amps
        return self

    # -- readout ------------------------------------------------------------
    def probabilities(self) -> np.ndarray:
        return np.abs(self.amps) ** 2

    def sample(self, shots: int, rng: np.random.Generator) -> dict[int, int]:
        p = self.probabilities()
        p = np.clip(p, 0.0, None)
        p = p / p.sum()
        draws = rng.choice(p.size, size=shots, p=p)
        vals, cnts = np.unique(draws, return_counts=True)
        return {int(v): int(c) for v, c in zip(vals, cnts)}


def bits_of(value: int, n: int) -> list[int]:
    """Bit vector of ``value``, indexed by qubit number (index 0 = qubit 0)."""
    return [(value >> q) & 1 for q in range(n)]


def value_of(bits) -> int:
    """Inverse of :func:`bits_of`."""
    return sum(int(b) << q for q, b in enumerate(bits))
