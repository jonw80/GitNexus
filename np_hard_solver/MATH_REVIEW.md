# Mathematical review of `UniversalNPHardSolver.pdf`

Audit of the 24-page listing, with every claim checked numerically.
Run `python3 -m np_hard_solver.verify_math` to reproduce; it is fail-closed.

---

## Verdict

The central claim does not survive contact with the mathematics, and it is not
a bug that can be patched. Two results settle it:

**The QAOA circuit provably returns the uniform distribution.** Not
approximately — exactly. The final line of `assemble_qaoa_circuit` is

```python
qaoa_circuit.rx(2 * np.pi * 0.5, range(num_qubits))
```

and `RX(π) = -iX`, a NOT gate on every qubit. The circuit is therefore
`H^⊗n`, then a diagonal cost layer, then a bit flip. `H^⊗n` gives every basis
state amplitude `1/√N`; a diagonal layer changes phases only, leaving every
`|amplitude|` at `1/√N`; and `X^⊗n` permutes basis states. A permutation of a
uniform distribution is uniform. Measured deviation from uniform: `5.6e-17`,
i.e. floating-point noise, and the output entropy is maximal — the distribution
is indistinguishable from ignoring the problem and flipping coins. Whatever the
code computes, the weights, values, and capacity never reach the result.

The argument holds at any register width, which matters because the width is
itself wrong: `num_qubits = len(problem_instance)` measures the length of a
*dict*, so the paper's own 4-item example runs on 3 qubits (see §5).

**Grover gives a quadratic speedup, and quadratic is not enough.** Even with a
flawless oracle, the cost is `Θ(√(2ⁿ)) = Θ(2^(n/2))`. At n = 100 that is
`8.8e14` oracle calls; at one call per nanosecond, about ten days, and doubling
n to 200 multiplies the cost by `1e15`. This is not an implementation
weakness: the BBBV theorem (Bennett, Bernstein, Brassard, Vazirani, 1997)
proves `Ω(√N)` queries are *necessary* for unstructured search, so no
oracle-based method does better. A polynomial-time NP-hard solver cannot be
assembled from these parts.

So the package in this directory implements what the listing can correctly be:
a **hybrid quantum-classical heuristic** with honest cost accounting, not a
universal solver. The rest of this document is the defect-by-defect audit.

---

## 1. Errors in the optimisation model

### 1.1 The cost Hamiltonian is not the problem's

The listing uses, for knapsack:

```python
angle = 2 * np.pi * min(values[i], values[j]) / capacity
```

The correct derivation. Maximise `Σ vᵢxᵢ` subject to `Σ wᵢxᵢ ≤ C`. Introduce a
binary-expanded slack `s` and penalise:

```
H = -Σ vᵢxᵢ + λ(Σ wᵢxᵢ + s - C)²
```

Expanding, and using `xᵢ² = xᵢ` for binary variables:

```
(Σ wᵢxᵢ)² = Σ wᵢ²xᵢ + 2 Σ_{i<j} wᵢwⱼ xᵢxⱼ
```

so the quadratic coupling is proportional to **`wᵢ·wⱼ`** — the *weights*, not
the values, and not their minimum. Substituting `xᵢ = (1-zᵢ)/2` gives
`J_ij = λ wᵢwⱼ/2`.

The listing's coupling is not even proportional to the right one: over the
example instance, `wᵢwⱼ / min(vᵢ,vⱼ)` ranges from 2.0 to 4.0. There are also
no single-qubit `RZ` terms, so the linear objective `-Σvᵢxᵢ` is absent
entirely, and no penalty weight λ, so the capacity constraint is unrepresented.

Fixed in `qubo.py`. The knapsack QUBO's ground state is verified against exact
dynamic programming; the partition Ising ground energy is verified to equal the
squared minimum partition difference.

### 1.2 No variational loop

`QAOA`, `COBYLA`, `QAOAAnsatz`, and `AmplificationProblem` are imported and
never used. The circuit is a single layer at fixed angles. QAOA without
optimisation of (γ, β) is not QAOA. Fixed in `qaoa.py` with a multi-restart
COBYLA loop over the true expectation value ⟨H_C⟩.

### 1.3 The bin-packing register is quadratic in the item count

`num_bins = num_items` gives `n²` qubits. At the listing's own
`max_items = 20`, that is **400 qubits** — a state vector of `2^400 ≈ 2.6e120`
amplitudes, and `iterations = int(π/4·√(2^400)) ≈ 1.3e60`. Aer's simulator
tops out near 30 qubits. Fixed by deriving the bin budget from
first-fit-decreasing, which is an `11/9·OPT + 1` approximation and therefore a
sound upper bound; a 4-item instance drops from 16 qubits to a formulation that
fits.

---

## 2. Errors in the quantum mechanics

### 2.1 The Grover iteration count assumes exactly one solution

```python
iterations = int(np.pi / 4 * np.sqrt(2**num_items))
```

This is optimal only for `M = 1` marked states. The general optimum is
`round(π/(4θ) - ½)` with `θ = arcsin(√(M/N))`. Over-rotating past the optimum
drives the success amplitude *back down* — `sin²((2k+1)θ)` is periodic, not
monotone:

| N | M | listing's k | P(success) | correct k | P(success) |
|---|---|---|---|---|---|
| 1024 | 16 | 25 | 0.0117 | 6 | 0.9966 |
| 4096 | 64 | 50 | 0.0084 | 6 | 0.9966 |
| 65536 | 256 | 201 | 0.0051 | 12 | 0.9999 |

Multiple optimal or feasible solutions is the generic case, so this fires
almost always. Fixed in `grover.py`, including the Boyer–Brassard–Høyer–Tapp
schedule for when M is unknown in advance — which is the realistic situation
and which the listing has no answer for at all.

### 2.2 The oracles are not oracles

A Grover oracle must be the diagonal reflection `|x⟩ → -|x⟩` exactly on the
satisfying set. `_knapsack_oracle` instead applies

```python
oracle.rz(weights[i] * np.pi / capacity, i)
...
oracle.rx(values[i] * np.pi / capacity, i)
```

`RX` rotates each qubit off the computational basis, so the register no longer
decomposes into "marked" and "unmarked" subspaces and the amplitude
amplification geometry is gone. The oracle also never evaluates the capacity
constraint — nothing in it computes `Σwᵢxᵢ` or compares it to `C`. The `cz`
gates apply a fixed phase pattern independent of the problem data.

Fixed with genuine phase oracles built from explicit predicates, plus a
gate-level CNF oracle verified against its classical predicate on all
assignments.

### 2.3 `assemble_or_gate` computes AND

```python
def assemble_or_gate(self, num_qubits):
    or_gate = QuantumCircuit(num_qubits)
    or_gate.mcx(list(range(num_qubits - 1)), num_qubits - 1)
```

A multi-controlled X is a generalised Toffoli: `target ^= AND(controls)`. It
differs from OR on exactly the inputs that matter for SAT — (0,1) and (1,0).
OR requires De Morgan: invert the inputs, MCX, invert the target, restore the
inputs. The listing also has no ancilla, so the MCX target is a *variable*
qubit, which the clause overwrites.

### 2.4 The SAT oracle never uncomputes

The listing appends the clause circuits, applies `mcz`, then appends *the same
circuits again*. Uncomputation requires the **inverse**. Each clause block is
`X(inputs)` then `MCX`; applying that twice gives `X·MCX·X·MCX ≠ I`, because X
on a control does not commute with the MCX. The ancillas stay entangled with
the variables and the interference that Grover depends on is destroyed.

### 2.5 The "quantum annealing" solver does no annealing

`QuantumAnnealingSolver` builds a fixed circuit with no transverse field, no
schedule, and no adiabatic evolution. It applies `cirq.X(q)**numbers[i]` —
integer powers of X, so `X^even = I` and `X^odd = X`, encoding only the parity
of each number and discarding its magnitude. It then applies `H` to every qubit
*after* the cost layer, scrambling it, and calls `result.histogram(key='x')` on
a circuit with no measurement gates and no key `'x'`.

### 2.6 The classical circuit-SAT checker misdescribes two gates

```python
elif gate == "Z":
    state[0] = 1 - state[0]
elif gate == "H":
    state[0], state[1] = state[1], state[0]
```

Z is diagonal: `Z|0⟩ = |0⟩`, `Z|1⟩ = -|1⟩`. It never changes a computational
basis state, but the code flips the bit. H maps `|0⟩ → (|0⟩+|1⟩)/√2`, which is
not a basis state at all — no deterministic bit-vector model can represent it,
so the function is unsound in principle, not just in detail.

---

## 3. Errors in the error mitigation

### 3.1 Measurement mitigation is never calibrated

```python
meas_calibs, state_labels = complete_meas_cal(qr=..., circlabel='mcal')
meas_fitter = CompleteMeasFitter(meas_calibs, state_labels)
```

`complete_meas_cal` returns *circuits*. They are never executed, so the fitter
receives no calibration data — the constructor wants results. The next line
calls `meas_fitter.filter.apply(self.results)` on a plain counts `dict`, then
`.get_counts(0)` on the return value, which a dict does not have.

Fixed by building the calibration matrix explicitly and inverting it under
non-negativity and normalisation constraints — an unconstrained inverse
routinely returns negative "probabilities" once shot noise is present.

### 3.2 Zero-noise extrapolation is a no-op

```python
noise_model = NoiseModel()
scaled_noise_model = noise_model.scale(scale)
```

`NoiseModel` has no `.scale()` method, and the model constructed here is
empty. All three "scaled" runs are therefore identical noiseless runs, the
fitted slope is zero, and the extrapolation returns the input.

The `np.polyfit` index is actually **correct** — `polyfit` returns
highest-degree-first, so for `deg=1`, `coefficients[1]` is the intercept, the
value extrapolated to zero noise. That one line is right. But the code then
drops every bitstring with a non-positive extrapolated count and never
renormalises, so the result is not a probability distribution.

Fixed with unitary folding (`U → U(U†U)ⁿ` scales noise by `2n+1` while leaving
the ideal operation unchanged), plus clipping and renormalisation.

### 3.3 "Probabilistic error cancellation" injects error

```python
pec_circuit.rx(2 * np.arcsin(np.sqrt(error_rate)), qubit)
```

`RX(2·arcsin(√p))` produces a flip with probability p. This *adds* a coherent
error of the requested strength; it cancels nothing. The combining step then
simply sums counts across three error rates, tripling the shot count with no
quasi-probability weights and no signs.

Real PEC samples from a quasi-probability decomposition of the *inverse* noise
map. For the bit-flip channel `(1-p)I + pX`, the inverse is `aI + bX` with
`a = (1-p)/(1-2p)` and `b = -p/(1-2p)`. The negative coefficient is the whole
point, and the sampling overhead is `γ² = (1/(1-2p))²` — a real cost the
listing never accounts for.

---

## 4. Errors in the machine learning

All three label definitions are broken, in three different ways, and **all
three classifiers score below their own majority-class baseline**:

| problem | listing's label | accuracy | majority baseline | lift |
|---|---|---|---|---|
| knapsack | `total_value >= 0.5 * capacity` | 0.980 | 0.985 | −0.005 |
| integer partitioning | `total_sum % 2 == 0` | 0.485 | 0.535 | −0.050 |
| bin packing | `total_size <= 2 * bin_capacity` | 0.495 | 0.510 | −0.015 |

- **knapsack** — `capacity ~ U(1, Σw)` while `total_value ≈ 50n`, so the label
  is 1 about 98.5% of the time. The forest learns the majority class.
- **integer partitioning** — the label is the *parity* of `total_sum`, and
  `total_sum` is itself a feature. Parity has no monotone threshold structure,
  so an axis-aligned tree ensemble can only memorise it and cannot generalise
  across the split. Chance level, as predicted.
- **bin packing** — the label depends on `bin_capacity`, which is **not among
  the features** and is drawn independently of those that are. The label is
  close to independent of everything the model can see.

`conjectures["feature_importances"]` taken from a chance-level model is noise,
so every "conjecture" the system emits is uninformative.

Separately, `analyze_datasets` assigns into one `insights` dict *inside* the
loop over 1000 instances, so it returns statistics for instance #1000 rather
than for the corpus.

Fixed in `learning.py` by predicting genuinely structural properties — whether
a cheap greedy heuristic attains the exact optimum — with the decisive quantity
present as a feature, and by reporting every result against both a
majority-class baseline and a label-permutation null:

At 500 instances (the size `verify_math.py` uses):

| problem | corrected label | accuracy | baseline | z | verdict |
|---|---|---|---|---|---|
| integer partitioning | a perfect partition exists | 0.880 | 0.690 | +6.3 | significant |
| bin packing | FFD attains `⌈total/cap⌉` | 0.810 | 0.770 | +2.4 | borderline |
| knapsack | greedy-by-density attains the DP optimum | 0.620 | 0.670 | +0.2 | **not significant** |

The partition model puts 57% of its importance on `sum_parity`, which is what
theory demands — an odd total makes a perfect partition impossible. Bin packing
crosses the significance threshold at 800 instances (z ≈ +3.5) and sits below
it at 500; it is reported as borderline rather than rounded up. The knapsack
row is a genuine negative result: these summary statistics do not predict when
greedy is optimal, and the harness says so rather than dressing it up.

That is the substantive difference from the original. The original's pipeline
had no baseline and no null, so it would have reported its 0.98 knapsack
accuracy as a success when the majority-class baseline was 0.985.

---

## 5. Defects that stop the code running at all

The example on the final page cannot execute. In rough order of when they fire:

| # | Location | Defect |
|---|---|---|
| 1 | `assemble_qaoa_circuit` | `num_qubits = len(problem_instance)` takes the length of a **dict** — 3 — so the 4-item example is encoded on 3 qubits and item 3 is silently dropped |
| 2 | `assemble_qaoa_circuit` | never adds a measurement, so `get_counts` has nothing to return |
| 3 | `hybrid_solver` | never calls `classical_preprocessing`, so `self.problem_instance` is unset when `post_process_result` dereferences it → `AttributeError` |
| 4 | `hybrid_solver` | if `select_quantum_algorithm` returns `None`, both branch variables are unbound → `UnboundLocalError` |
| 5 | `select_quantum_algorithm` | falls off the end and returns `None` for any unlisted problem |
| 6 | `assemble_boolean_satisfiability_oracle` | `abs(int(literal))` on `"~3"` raises `ValueError`; literals are treated as ints and strings in the same expression |
| 7 | `assemble_*_oracle` | `oracle_circuit.mcz(...)` — `QuantumCircuit` has no `mcz` method |
| 8 | `_diffusion_operator` | `diffusion.mct(...)` — removed from Qiskit, renamed `mcx` |
| 9 | imports | `cirq`, `QuantumRegister`, `ClassicalRegister`, `GroverOperator`, `NoiseModel`, `complete_meas_cal`, `CompleteMeasFitter` all used, none imported |
| 10 | imports | `Aer` and `execute` were removed from `qiskit` in 1.0; `qiskit.algorithms` was removed in 1.0 |
| 11 | `post_process_result` | reads counts strings left-to-right against a qubit-0-is-rightmost register, reversing the item order |
| 12 | `assemble_grover_circuit` | `max_independent_set` routes to Grover but has no oracle branch — returns H + measure, i.e. uniform noise |
| 13 | `generate_datasets` | `datasets` unbound for any unlisted problem type |
| 14 | `assemble_qaoa_circuit` | `target_sum = sum(numbers) // 2` is 0 for a single-element instance → division by zero |
| 15 | `_update_solver` | reads `insights["total_weight"]` → `KeyError` for partitioning and bin packing |
| 16 | `_update_solver` | rebinds `quantum_annealing_solver.solve` to a lambda calling `solve_with_quantum_annealing`, which calls `quantum_annealing_solver.solve` → **unbounded recursion** on the second refinement pass |

---

## 6. Errors in the classical post-processing

### 6.1 Knapsack repair cannot repair

```python
if total_weight <= capacity:
    return self.solution
else:
    remaining_capacity = capacity - total_weight   # negative by construction
    ...
    if item[1] <= remaining_capacity:              # never true for positive weights
```

The `else` branch is reached precisely when the selection is over capacity, so
`remaining_capacity` is negative — and the code then loops over *unselected*
items looking for ones to **add**. With positive weights the guard is never
satisfied, so the repair is a no-op and an infeasible solution is returned.
Repair has to evict.

Fixed by evicting in increasing value density until feasible, then refilling in
decreasing density. Verified over 200 random instances: always feasible, never
worse than a feasible input.

### 6.2 Partition repair has the sign backwards

```python
num = smaller_set.pop()
larger_set.append(num)
difference -= 2 * num
```

Moving `a` from the lighter side to the heavier side changes the difference
from `d` to `d + 2a`. The bookkeeping subtracts where the truth adds — moving 1
from `[1,2]` to `[10]` takes the difference from 7 to **9**, while the counter
records 5. The function then rebuilds the partition from the *unmodified*
`set1`, discarding whatever moves it made, and uses `numbers.index(num)`, which
collides on duplicate values.

### 6.3 Bin-packing post-processing has three lookup bugs

```python
bins[assignment[i]] += self.problem_instance["items"][i]
```

`assignment` is a **bit** vector, so only bins 0 and 1 are ever reachable
regardless of how many bins the encoding allocated. Then `bins.index(bin)`
searches a list of lists *by value*, returning the wrong index whenever two
bins hold equal contents, and `assignment[items.index(item)] = i` collides on
duplicate item sizes. All three vanish once indices are carried explicitly
instead of being recovered by value lookup.

---

## What this package provides

| file | contents |
|---|---|
| `statevector.py` | exact NumPy state-vector simulator; explicit bit conventions; refuses oversized registers |
| `qubo.py` | correct QUBO/Ising formulations with slack variables and penalty bounds, plus exact DP references |
| `qaoa.py` | QAOA with a real mixer and a real variational loop; the original circuit preserved for the regression check |
| `grover.py` | correct iteration counts, BBHT for unknown M, genuine phase oracles, De Morgan OR |
| `repair.py` | classical repair with the directions fixed |
| `mitigation.py` | calibrated readout mitigation, folding-based ZNE, signed quasi-probability PEC |
| `learning.py` | learnable labels, with baselines and a permutation null |
| `solver.py` | orchestration with the control-flow defects fixed |
| `verify_math.py` | fail-closed verification of everything above |

Every solver reports the classical baseline alongside its own result and states
whether the quantum step improved on it. On the small instances that fit in a
state-vector simulation, it usually does not — which is the honest finding, and
the reason the reporting exists.

### Scope, stated plainly

This is a heuristic. QAOA carries no approximation guarantee at fixed depth;
Grover is exponential and provably optimal among oracle methods. Nothing here
solves NP-hard problems in polynomial time, and by BBBV no rearrangement of
these components will.
