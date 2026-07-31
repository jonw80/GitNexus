"""QUBO / Ising formulations of the three optimisation problems.

The listing under review builds its cost layer from angles like

    angle = 2 * np.pi * min(values[i], values[j]) / capacity

which is not the cost Hamiltonian of any of these problems.  The derivation
below fixes that.

Knapsack.  Maximise sum_i v_i x_i subject to sum_i w_i x_i <= C.  Introduce a
binary-expanded slack s = sum_k 2^k y_k in [0, C] and fold the constraint into
the objective with a penalty:

    H = -sum_i v_i x_i + lam * (sum_i w_i x_i + s - C)^2

Expanding the square,

    (sum_i w_i x_i)^2 = sum_i w_i^2 x_i^2 + 2 sum_{i<j} w_i w_j x_i x_j
                      = sum_i w_i^2 x_i     + 2 sum_{i<j} w_i w_j x_i x_j

using x_i^2 = x_i for binary x.  So the quadratic coupling between item
variables is proportional to **w_i * w_j** -- the weights, not the values, and
not their minimum.  With integer weights the smallest possible constraint
violation is 1, so any lam > sum_i v_i makes every infeasible assignment cost
more than the best feasible one; that bound is used below.

Number partitioning.  Minimise (sum_i a_i s_i)^2 over spins s_i in {-1, +1}.
This is already an Ising model:

    (sum_i a_i s_i)^2 = sum_i a_i^2 + 2 sum_{i<j} a_i a_j s_i s_j

so J_ij = 2 a_i a_j and there is no local field at all.

Bin packing.  Variables x_ij (item i in bin j) and y_j (bin j is used), with a
one-hot constraint per item, a capacity constraint per bin, and a linking
constraint x_ij <= y_j.  The variable count is n_items * n_bins + n_bins, which
is why the original's ``num_bins = num_items`` choice is ruinous: it makes the
register n^2 qubits wide.  A tighter bin budget is derived here from
first-fit-decreasing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class QUBO:
    """Upper-triangular QUBO: E(x) = offset + sum_i Q[i,i] x_i + sum_{i<j} Q[i,j] x_i x_j."""

    n: int
    Q: np.ndarray
    offset: float = 0.0
    labels: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.Q.shape != (self.n, self.n):
            raise ValueError(f"Q must be {self.n}x{self.n}, got {self.Q.shape}")
        if not self.labels:
            self.labels = [f"x{i}" for i in range(self.n)]

    def energy(self, x) -> float:
        x = np.asarray(x, dtype=float)
        return float(self.offset + x @ np.triu(self.Q) @ x)

    def to_ising(self) -> "Ising":
        """Substitute x_i = (1 - z_i)/2 and collect terms.

        x_i      -> 1/2 - z_i/2
        x_i x_j  -> 1/4 - z_i/4 - z_j/4 + z_i z_j /4
        """
        Qd = np.diag(self.Q).astype(float)
        Qo = np.triu(self.Q, 1).astype(float)

        J = Qo / 4.0
        h = -Qd / 2.0 - (Qo.sum(axis=1) + Qo.sum(axis=0)) / 4.0
        const = self.offset + Qd.sum() / 2.0 + Qo.sum() / 4.0
        return Ising(n=self.n, h=h, J=J, offset=const, labels=list(self.labels))


@dataclass
class Ising:
    """E(z) = offset + sum_i h_i z_i + sum_{i<j} J[i,j] z_i z_j, z_i in {-1,+1}."""

    n: int
    h: np.ndarray
    J: np.ndarray
    offset: float = 0.0
    labels: list[str] = field(default_factory=list)

    def energy_vector(self) -> np.ndarray:
        """Diagonal of the cost Hamiltonian over all 2**n computational basis states.

        Index convention matches :mod:`np_hard_solver.statevector`: bit q of the
        basis index is qubit q, and z_q = 1 - 2 * bit_q (so bit 0 -> z=+1 -> x=0).
        """
        if self.n > 24:
            raise ValueError(f"{self.n} variables is too many to enumerate")
        idx = np.arange(2 ** self.n)
        z = np.empty((2 ** self.n, self.n), dtype=np.float64)
        for q in range(self.n):
            z[:, q] = 1.0 - 2.0 * ((idx >> q) & 1)
        e = np.full(2 ** self.n, self.offset, dtype=np.float64)
        e += z @ self.h
        iu, ju = np.triu_indices(self.n, k=1)
        if iu.size:
            e += (z[:, iu] * z[:, ju]) @ self.J[iu, ju]
        return e


def _slack_bits(upper: int) -> int:
    """Number of binary digits needed to express any integer in [0, upper]."""
    if upper <= 0:
        return 0
    return int(upper).bit_length()


def knapsack_qubo(weights, values, capacity, penalty=None) -> QUBO:
    """Penalty QUBO for 0/1 knapsack, minimised at the optimal packing."""
    w = np.asarray(weights, dtype=float)
    v = np.asarray(values, dtype=float)
    n_items = w.size
    if n_items == 0:
        raise ValueError("knapsack instance has no items")
    if capacity <= 0:
        raise ValueError(f"capacity must be positive, got {capacity}")

    # Slack only needs to cover the reachable range [0, min(capacity, sum w)].
    slack_max = int(min(capacity, w.sum()))
    n_slack = _slack_bits(slack_max)
    n = n_items + n_slack

    if penalty is None:
        # Any lam > sum(v) makes a unit constraint violation cost more than the
        # entire achievable objective, so every minimiser is feasible.
        penalty = float(v.sum()) + 1.0

    coeff = np.concatenate([w, np.array([2.0 ** k for k in range(n_slack)])])

    Q = np.zeros((n, n), dtype=float)
    # -sum_i v_i x_i  (items only)
    Q[np.arange(n_items), np.arange(n_items)] -= v
    # lam * (sum_a c_a t_a - C)^2, t = [x, y]
    #   = lam * ( sum_a c_a^2 t_a + 2 sum_{a<b} c_a c_b t_a t_b
    #             - 2C sum_a c_a t_a + C^2 )
    Q[np.arange(n), np.arange(n)] += penalty * (coeff ** 2 - 2.0 * capacity * coeff)
    ia, ib = np.triu_indices(n, k=1)
    Q[ia, ib] += penalty * 2.0 * coeff[ia] * coeff[ib]
    offset = penalty * capacity ** 2

    labels = [f"item{i}" for i in range(n_items)] + [f"slack2^{k}" for k in range(n_slack)]
    return QUBO(n=n, Q=Q, offset=offset, labels=labels)


def partition_ising(numbers) -> Ising:
    """Exact Ising model for number partitioning: J_ij = 2 a_i a_j, h = 0."""
    a = np.asarray(numbers, dtype=float)
    n = a.size
    if n == 0:
        raise ValueError("partition instance has no numbers")
    J = np.zeros((n, n), dtype=float)
    iu, ju = np.triu_indices(n, k=1)
    J[iu, ju] = 2.0 * a[iu] * a[ju]
    return Ising(n=n, h=np.zeros(n), J=J, offset=float((a ** 2).sum()),
                 labels=[f"a{i}" for i in range(n)])


def first_fit_decreasing(items, bin_capacity) -> list[list[int]]:
    """Classic FFD packing.  Returns a list of bins, each a list of item indices."""
    order = sorted(range(len(items)), key=lambda i: -items[i])
    bins: list[list[int]] = []
    loads: list[float] = []
    for i in order:
        for b in range(len(bins)):
            if loads[b] + items[i] <= bin_capacity:
                bins[b].append(i)
                loads[b] += items[i]
                break
        else:
            bins.append([i])
            loads.append(float(items[i]))
    return bins


def bin_packing_qubo(items, bin_capacity, n_bins=None, penalty=None) -> QUBO:
    """Penalty QUBO for bin packing with an FFD-derived bin budget."""
    it = np.asarray(items, dtype=float)
    n_items = it.size
    if n_items == 0:
        raise ValueError("bin packing instance has no items")
    if bin_capacity <= 0:
        raise ValueError(f"bin_capacity must be positive, got {bin_capacity}")
    if np.any(it > bin_capacity):
        raise ValueError("an item is larger than the bin capacity; instance is infeasible")

    if n_bins is None:
        # FFD is a 11/9-OPT+1 approximation, so its bin count is a safe budget,
        # and it is far below the original's n_bins = n_items.
        n_bins = len(first_fit_decreasing(it, bin_capacity))
    n_bins = int(max(1, min(n_bins, n_items)))

    slack_bits = _slack_bits(int(bin_capacity))
    n_x = n_items * n_bins           # x[i,j] : item i in bin j
    n_y = n_bins                     # y[j]   : bin j is used
    n_s = n_bins * slack_bits        # per-bin capacity slack
    n = n_x + n_y + n_s

    if penalty is None:
        penalty = float(n_bins) + 1.0

    def xi(i, j):
        return i * n_bins + j

    def yi(j):
        return n_x + j

    def si(j, k):
        return n_x + n_y + j * slack_bits + k

    Q = np.zeros((n, n), dtype=float)
    offset = 0.0

    def add_linear(a, c):
        Q[a, a] += c

    def add_quadratic(a, b, c):
        if a == b:
            Q[a, a] += c
        else:
            lo, hi = (a, b) if a < b else (b, a)
            Q[lo, hi] += c

    def add_squared(terms, const):
        """penalty * (sum_a c_a t_a + const)^2 with t binary."""
        for a, ca in terms:
            add_linear(a, penalty * (ca ** 2 + 2.0 * ca * const))
        for u in range(len(terms)):
            for v_ in range(u + 1, len(terms)):
                a, ca = terms[u]
                b, cb = terms[v_]
                add_quadratic(a, b, penalty * 2.0 * ca * cb)
        return penalty * const ** 2

    # objective: minimise the number of bins used
    for j in range(n_bins):
        add_linear(yi(j), 1.0)

    # each item in exactly one bin: (sum_j x_ij - 1)^2
    for i in range(n_items):
        offset += add_squared([(xi(i, j), 1.0) for j in range(n_bins)], -1.0)

    # capacity with slack: (sum_i it_i x_ij + sum_k 2^k s_jk - cap * y_j)^2
    for j in range(n_bins):
        terms = [(xi(i, j), float(it[i])) for i in range(n_items)]
        terms += [(si(j, k), 2.0 ** k) for k in range(slack_bits)]
        terms += [(yi(j), -float(bin_capacity))]
        offset += add_squared(terms, 0.0)

    labels = [f"x[{i},{j}]" for i in range(n_items) for j in range(n_bins)]
    labels += [f"y[{j}]" for j in range(n_bins)]
    labels += [f"s[{j},2^{k}]" for j in range(n_bins) for k in range(slack_bits)]
    return QUBO(n=n, Q=Q, offset=offset, labels=labels)


def knapsack_optimum(weights, values, capacity):
    """Exact 0/1 knapsack by dynamic programming; ground truth for the tests."""
    w = [int(x) for x in weights]
    v = [int(x) for x in values]
    cap = int(capacity)
    n = len(w)
    table = [[0] * (cap + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = w[i - 1], v[i - 1]
        row, prev = table[i], table[i - 1]
        for c in range(cap + 1):
            row[c] = prev[c] if wi > c else max(prev[c], prev[c - wi] + vi)
    # reconstruct
    chosen = [0] * n
    c = cap
    for i in range(n, 0, -1):
        if table[i][c] != table[i - 1][c]:
            chosen[i - 1] = 1
            c -= w[i - 1]
    return table[n][cap], chosen


def partition_optimum(numbers):
    """Exact minimum partition difference by subset-sum DP."""
    a = [int(x) for x in numbers]
    total = sum(a)
    reachable = 1  # bitset: bit s set iff subset sum s is reachable
    for x in a:
        reachable |= reachable << x
    best = total
    for s in range(total // 2, -1, -1):
        if (reachable >> s) & 1:
            best = total - 2 * s
            break
    return best
