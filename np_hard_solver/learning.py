"""Instance-feature learning, with labels that are actually learnable.

The three label definitions in the original are each broken in a different way,
and all three classifiers score *below* their majority-class baseline:

  knapsack             label = 1 if total_value >= 0.5 * capacity
        capacity is drawn from U(1, sum(weights)) while total_value is ~50*n,
        so the label is 1 about 98.5% of the time.  The forest learns the
        majority class and nothing else.

  integer_partitioning label = 1 if total_sum % 2 == 0
        total_sum is itself a feature, so this asks an axis-aligned threshold
        ensemble to compute the parity of a continuous input.  Parity has no
        monotone threshold structure; a tree can only memorise it, and cannot
        generalise across the train/test split.  Accuracy sits at chance.

  bin_packing          label = 1 if total_size <= 2 * bin_capacity
        bin_capacity is *not* among the features, and it is drawn independently
        of them, so the label is close to independent of everything the model
        sees.  Chance again.

``feature_importances_`` from a chance-level model is noise, so the
"conjectures" the original emits carry no information.

The replacements below predict genuinely structural properties -- whether a
cheap greedy heuristic attains the exact optimum -- with the decisive quantity
present as a feature, and every result is reported against a majority-class
baseline and a label-permutation null so a non-result cannot be mistaken for a
finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score, train_test_split

from .qubo import first_fit_decreasing, knapsack_optimum, partition_optimum


@dataclass
class Conjecture:
    problem: str
    label_definition: str
    n_instances: int
    accuracy: float
    majority_baseline: float
    lift: float
    cv_mean: float
    cv_std: float
    permutation_mean: float
    permutation_std: float
    z_score: float
    significant: bool
    feature_names: list[str] = field(default_factory=list)
    feature_importances: list[float] = field(default_factory=list)

    def summary(self) -> str:
        verdict = "SIGNIFICANT" if self.significant else "not distinguishable from chance"
        return (
            f"{self.problem}: acc={self.accuracy:.4f} "
            f"baseline={self.majority_baseline:.4f} lift={self.lift:+.4f} "
            f"cv={self.cv_mean:.4f}+/-{self.cv_std:.4f} z={self.z_score:+.2f} -> {verdict}"
        )


def _evaluate(problem, label_definition, features, labels, names, seed=42) -> Conjecture:
    x = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=int)

    x_tr, x_te, y_tr, y_te = train_test_split(
        x, y, test_size=0.2, random_state=seed, stratify=y if len(set(y)) > 1 else None
    )
    clf = RandomForestClassifier(n_estimators=200, random_state=seed).fit(x_tr, y_tr)
    acc = float(accuracy_score(y_te, clf.predict(x_te)))
    baseline = float(max(np.mean(y_te), 1.0 - np.mean(y_te)))

    cv = cross_val_score(
        RandomForestClassifier(n_estimators=200, random_state=seed), x, y, cv=5
    )

    # Permutation null: refit on shuffled labels to see what "accuracy" this
    # feature set and this class balance produce with no signal at all.
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(12):
        y_shuf = rng.permutation(y)
        a, b, c, d = train_test_split(x, y_shuf, test_size=0.2, random_state=seed)
        m = RandomForestClassifier(n_estimators=100, random_state=seed).fit(a, c)
        null.append(accuracy_score(d, m.predict(b)))
    null = np.asarray(null)
    z = float((acc - null.mean()) / null.std()) if null.std() > 0 else 0.0

    return Conjecture(
        problem=problem,
        label_definition=label_definition,
        n_instances=int(x.shape[0]),
        accuracy=acc,
        majority_baseline=baseline,
        lift=acc - baseline,
        cv_mean=float(cv.mean()),
        cv_std=float(cv.std()),
        permutation_mean=float(null.mean()),
        permutation_std=float(null.std()),
        z_score=z,
        significant=bool(acc > baseline and z > 3.0),
        feature_names=list(names),
        feature_importances=[float(v) for v in clf.feature_importances_],
    )


def knapsack_conjecture(n_instances=600, seed=0, max_items=14, max_weight=30) -> Conjecture:
    """Does greedy-by-value-density attain the exact DP optimum?

    The capacity is drawn as a *fraction* of total weight rather than uniformly
    on [1, sum(w)].  Uniform draws put most instances in the regime where
    almost everything fits and greedy is trivially optimal, which is the same
    class-collapse that makes the original's knapsack label useless.
    """
    rng = np.random.default_rng(seed)
    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(6, max_items + 1))
        w = rng.integers(1, max_weight + 1, size=n)
        v = rng.integers(1, 100, size=n)
        cap = max(int(w.min()), int(rng.uniform(0.2, 0.8) * w.sum()))

        opt, _ = knapsack_optimum(w, v, cap)
        # greedy by density
        order = sorted(range(n), key=lambda i: -v[i] / w[i])
        slack, greedy = cap, 0
        for i in order:
            if w[i] <= slack:
                slack -= int(w[i])
                greedy += int(v[i])

        density = v / w
        feats.append([
            n, float(w.sum()), float(v.sum()), float(cap),
            float(cap) / float(w.sum()),            # capacity ratio: the decisive one
            float(w.max()), float(w.min()), float(v.max()), float(v.min()),
            float(density.mean()), float(density.std()), float(density.max() - density.min()),
        ])
        labels.append(1 if greedy == opt else 0)

    names = ["n_items", "total_weight", "total_value", "capacity", "capacity_ratio",
             "max_weight", "min_weight", "max_value", "min_value",
             "mean_density", "std_density", "density_spread"]
    return _evaluate("knapsack", "greedy-by-density attains the DP optimum",
                     feats, labels, names)


def partition_conjecture(n_instances=600, seed=0, max_numbers=14, max_value=40) -> Conjecture:
    """Does a perfect (zero-difference) partition exist?"""
    rng = np.random.default_rng(seed)
    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(2, max_numbers + 1))
        a = rng.integers(1, max_value + 1, size=n)
        total = int(a.sum())
        feats.append([
            n, float(total),
            float(total % 2),                      # parity, as an explicit binary feature
            float(a.max()), float(a.min()), float(a.mean()), float(a.std()),
            float(a.max()) / float(total),         # dominance: max > total/2 blocks balance
            float(n) / float(total),
        ])
        labels.append(1 if partition_optimum(a) == 0 else 0)

    names = ["n_numbers", "total_sum", "sum_parity", "max_number", "min_number",
             "mean", "std", "max_over_total", "count_over_total"]
    return _evaluate("integer_partitioning", "a perfect partition exists",
                     feats, labels, names)


def bin_packing_conjecture(n_instances=600, seed=0, max_items=16, max_size=40) -> Conjecture:
    """Does first-fit-decreasing attain the ceil(total/capacity) lower bound?

    As with knapsack, the capacity is a fraction of the total so that instances
    land in the regime where FFD sometimes fails; drawing it uniformly makes
    the answer "yes" over 90% of the time and the label near-constant.
    """
    rng = np.random.default_rng(seed)
    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(8, max_items + 1))
        it = rng.integers(1, max_size + 1, size=n)
        cap = max(int(it.max()), int(rng.uniform(0.12, 0.30) * it.sum()))

        bins = len(first_fit_decreasing(it, cap))
        lower_bound = int(np.ceil(it.sum() / cap))
        feats.append([
            n, float(it.sum()), float(cap),        # capacity is a feature now
            float(it.sum()) / float(cap),          # the load ratio
            float(it.max()), float(it.min()), float(it.mean()), float(it.std()),
            float(it.max()) / float(cap),
            float(np.mean(it > cap / 2)),          # fraction of items that cannot pair up
        ])
        labels.append(1 if bins == lower_bound else 0)

    names = ["n_items", "total_size", "bin_capacity", "load_ratio", "max_item",
             "min_item", "mean_item", "std_item", "max_over_cap", "frac_over_half"]
    return _evaluate("bin_packing", "FFD attains the ceil(total/capacity) bound",
                     feats, labels, names)


def original_labels_report(n_instances=1000, seed=0) -> list[Conjecture]:
    """Reproduce the original's three label definitions, for the regression check."""
    rng = np.random.default_rng(seed)

    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(1, 21))
        w = rng.integers(1, 101, size=n)
        v = rng.integers(1, 101, size=n)
        cap = int(rng.integers(1, int(w.sum()) + 1))
        feats.append([n, w.sum(), v.sum(), w.max(), v.max(), w.min(), v.min()])
        labels.append(1 if v.sum() >= 0.5 * cap else 0)
    ks = _evaluate("knapsack (original)", "total_value >= 0.5 * capacity", feats, labels,
                   ["n", "tw", "tv", "mxw", "mxv", "mnw", "mnv"])

    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(1, 21))
        a = rng.integers(1, 101, size=n)
        feats.append([n, a.sum(), a.max(), a.min()])
        labels.append(1 if a.sum() % 2 == 0 else 0)
    pt = _evaluate("integer_partitioning (original)", "total_sum % 2 == 0", feats, labels,
                   ["n", "sum", "max", "min"])

    feats, labels = [], []
    for _ in range(n_instances):
        n = int(rng.integers(1, 21))
        it = rng.integers(1, 101, size=n)
        cap = int(rng.integers(1, int(it.sum()) + 1))
        feats.append([n, it.sum(), it.max(), it.min()])
        labels.append(1 if it.sum() <= 2 * cap else 0)
    bp = _evaluate("bin_packing (original)", "total_size <= 2 * bin_capacity", feats, labels,
                   ["n", "total", "max", "min"])

    return [ks, pt, bp]
