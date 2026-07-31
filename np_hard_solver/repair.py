"""Classical post-processing, with the direction errors fixed.

Knapsack.  The original computes ``remaining_capacity = capacity -
total_weight`` when it has already established ``total_weight > capacity``, so
the value is negative, and then loops over the *unselected* items adding any
whose weight is ``<= remaining_capacity``.  With positive weights that test is
never true, so an over-capacity selection is returned unrepaired.  Repair has
to evict items first.

Number partitioning.  The original moves an element from the smaller side to
the larger side and records ``difference -= 2 * num``.  Moving a from the
lighter side to the heavier side changes the difference from d to d + 2a: the
bookkeeping subtracts where the truth adds.  It then rebuilds the partition
from the unmodified ``set1``, discarding whatever moves it did make, and uses
``numbers.index(num)`` which collides on duplicate values.

Bin packing.  The original indexes ``bins[assignment[i]]`` where ``assignment``
is a *bit* vector, so only bins 0 and 1 are ever reachable; calls
``bins.index(bin)`` on a list of lists, which matches by value and returns the
wrong index whenever two bins hold equal contents; and uses
``items.index(item)`` which collides on duplicate item sizes.  All three are
value-lookup bugs that disappear once indices are carried explicitly.
"""

from __future__ import annotations

import numpy as np


def repair_knapsack(selection, weights, values, capacity):
    """Make a selection feasible, then fill greedily.  Returns a 0/1 list.

    Eviction order is increasing value density, so the least efficient items
    leave first; the refill pass then adds the most efficient items that still
    fit.  Both directions are monotone in the feasible set, so the result is
    always feasible and never worse than the input.
    """
    sel = [int(b) for b in selection]
    w = list(weights)
    v = list(values)
    if len(sel) != len(w):
        raise ValueError(
            f"selection has {len(sel)} bits but the instance has {len(w)} items"
        )

    def total(field):
        return sum(field[i] for i in range(len(sel)) if sel[i])

    # 1. evict until feasible, cheapest value-per-weight first
    order = sorted((i for i in range(len(sel)) if sel[i]),
                   key=lambda i: v[i] / w[i] if w[i] else float("inf"))
    k = 0
    while total(w) > capacity and k < len(order):
        sel[order[k]] = 0
        k += 1

    # 2. refill with whatever still fits, densest first
    slack = capacity - total(w)
    for i in sorted((i for i in range(len(sel)) if not sel[i]),
                    key=lambda i: -(v[i] / w[i]) if w[i] else float("-inf")):
        if w[i] <= slack:
            sel[i] = 1
            slack -= w[i]

    return sel


def repair_partition(assignment, numbers):
    """Greedy descent on |sum(A) - sum(B)|, moving items by index.

    A move of element a from the heavier side to the lighter side reduces the
    difference exactly when 2a < d.  The loop applies the largest such move
    available and stops at a local minimum, so the difference is monotonically
    non-increasing and termination is guaranteed.
    """
    side = [int(b) for b in assignment]
    a = list(numbers)
    if len(side) != len(a):
        raise ValueError(
            f"assignment has {len(side)} bits but the instance has {len(a)} numbers"
        )

    def sums():
        s1 = sum(a[i] for i in range(len(side)) if side[i] == 1)
        s0 = sum(a[i] for i in range(len(side)) if side[i] == 0)
        return s1, s0

    while True:
        s1, s0 = sums()
        diff = s1 - s0
        if diff == 0:
            break
        heavy = 1 if diff > 0 else 0
        d = abs(diff)
        # move the largest element that strictly improves the difference
        candidates = [i for i in range(len(side)) if side[i] == heavy and 2 * a[i] < d]
        if not candidates:
            break
        best = max(candidates, key=lambda i: a[i])
        side[best] = 1 - heavy

    return side


def repair_bin_packing(assignment, items, bin_capacity):
    """Make a bin assignment feasible via first-fit on overflow, by index.

    ``assignment[i]`` is the integer bin index of item i.  Overfull bins are
    emptied largest-item-first into any bin with room, opening a new bin when
    none has room.  Returns a list of bin indices, renumbered to be contiguous.
    """
    assign = [int(b) for b in assignment]
    it = list(items)
    if len(assign) != len(it):
        raise ValueError(
            f"assignment has {len(assign)} entries but the instance has {len(it)} items"
        )
    if any(x > bin_capacity for x in it):
        raise ValueError("an item exceeds the bin capacity; instance is infeasible")

    n_bins = max(max(assign) + 1, len(it))
    bins: list[list[int]] = [[] for _ in range(n_bins)]
    for i, b in enumerate(assign):
        bins[b % n_bins].append(i)

    def load(b):
        return sum(it[i] for i in bins[b])

    for b in range(n_bins):
        while load(b) > bin_capacity:
            # evict the largest item in the overfull bin
            victim = max(bins[b], key=lambda i: it[i])
            bins[b].remove(victim)
            for target in range(n_bins):
                if target != b and load(target) + it[victim] <= bin_capacity:
                    bins[target].append(victim)
                    break
            else:
                bins.append([victim])
                n_bins += 1

    out = [0] * len(it)
    next_id = 0
    for b in range(n_bins):
        if not bins[b]:
            continue
        for i in bins[b]:
            out[i] = next_id
        next_id += 1
    return out


def bits_to_bin_indices(bits, n_items, n_bins):
    """Decode a one-hot x[i,j] register into one bin index per item.

    The original conflates a bit vector with a bin index.  With the QUBO in
    :func:`np_hard_solver.qubo.bin_packing_qubo` the register really is one-hot
    per item, so decoding means picking the set bit -- and falling back to bin 0
    when the one-hot constraint was violated, which the repair pass then fixes.
    """
    bits = list(bits)
    out = []
    for i in range(n_items):
        row = bits[i * n_bins:(i + 1) * n_bins]
        hot = [j for j, b in enumerate(row) if b]
        out.append(hot[0] if len(hot) == 1 else (hot[0] if hot else 0))
    return out
