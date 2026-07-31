"""Error mitigation, corrected.

Measurement mitigation.  The original passes *circuits* where the fitter wants
*results*::

    meas_calibs, state_labels = complete_meas_cal(qr=..., circlabel='mcal')
    meas_fitter = CompleteMeasFitter(meas_calibs, state_labels)

The calibration circuits are never executed, so the fitter has no calibration
data.  It then calls ``meas_fitter.filter.apply(self.results)`` on a plain
counts ``dict`` and follows with ``.get_counts(0)``, which a dict does not
have.  Below the calibration matrix is built explicitly and inverted under
non-negativity and normalisation constraints, because an unconstrained inverse
routinely produces negative "probabilities".

Zero-noise extrapolation.  ``NoiseModel`` has no ``.scale()`` method, and the
model the original builds is empty, so all three "scaled" runs are identical
noiseless runs and the fitted slope is zero -- the extrapolation is a no-op.
Noise is scaled here by the standard unitary-folding identity: replacing U with
U (U^dag U)^n multiplies the effective noise by 2n+1 while leaving the ideal
operation unchanged.  The index the original uses into ``np.polyfit`` is
actually right (``coefficients[1]`` is the intercept, i.e. the zero-noise
value), but it then drops every non-positive entry without renormalising, so
the output is not a distribution.

Probabilistic error cancellation.  ``apply_probabilistic_error_cancellation``
appends ``rx(2 arcsin(sqrt(error_rate)))``, which *injects* a coherent error of
that strength rather than cancelling anything, and
``combine_probabilistic_error_cancellation_results`` simply sums the counts
from three different error rates, tripling the shot count with no
quasi-probability weights.  Real PEC samples from a quasi-probability
decomposition of the inverse noise map and averages with signs, at a variance
cost of gamma^2.  That is implemented below for the single-qubit bit-flip
channel it is being applied to.
"""

from __future__ import annotations

import numpy as np


def calibration_matrix(n_qubits: int, p_flip: float) -> np.ndarray:
    """A[measured, true] for independent symmetric bit flips at rate ``p_flip``."""
    if not 0.0 <= p_flip < 0.5:
        raise ValueError(f"p_flip must be in [0, 0.5), got {p_flip}")
    single = np.array([[1 - p_flip, p_flip], [p_flip, 1 - p_flip]])
    a = np.array([[1.0]])
    for _ in range(n_qubits):
        a = np.kron(a, single)
    return a


def apply_readout_noise(probs: np.ndarray, p_flip: float) -> np.ndarray:
    n = int(np.log2(probs.size))
    return calibration_matrix(n, p_flip) @ probs


def mitigate_readout(noisy: np.ndarray, p_flip: float, iterations: int = 500) -> np.ndarray:
    """Invert the calibration matrix subject to p >= 0 and sum(p) = 1.

    Uses the standard non-negative least-squares fixed point (multiplicative
    Richardson-Lucy style updates), which keeps the iterate on the simplex --
    a raw ``np.linalg.solve`` gives negative entries as soon as there is shot
    noise.
    """
    n = int(np.log2(noisy.size))
    a = calibration_matrix(n, p_flip)
    obs = np.clip(noisy, 0.0, None)
    s = obs.sum()
    if s <= 0:
        raise ValueError("observed distribution has no weight")
    obs = obs / s

    est = np.full(noisy.size, 1.0 / noisy.size)
    for _ in range(iterations):
        pred = a @ est
        pred = np.where(pred <= 0, 1e-300, pred)
        est = est * (a.T @ (obs / pred))
        est = np.clip(est, 0.0, None)
        total = est.sum()
        if total <= 0:
            break
        est = est / total
    return est


def fold_noise_scale(base_error: float, scale: float) -> float:
    """Effective error after unitary folding U -> U (U^dag U)^n, scale = 2n+1."""
    if scale < 1.0:
        raise ValueError(f"folding cannot scale noise below 1.0, got {scale}")
    # Error accumulates once per application of the folded circuit.
    return 1.0 - (1.0 - base_error) ** scale


def zero_noise_extrapolate(distributions, scale_factors) -> np.ndarray:
    """Linear Richardson extrapolation to zero noise, renormalised to a distribution.

    ``distributions[k]`` is the outcome distribution at ``scale_factors[k]``.
    """
    scales = np.asarray(scale_factors, dtype=float)
    if scales.size < 2:
        raise ValueError("need at least two noise scales to extrapolate")
    stack = np.vstack([np.asarray(d, dtype=float) for d in distributions])
    if stack.shape[0] != scales.size:
        raise ValueError(
            f"{stack.shape[0]} distributions for {scales.size} scale factors"
        )

    # Fit each outcome independently; polyfit returns [slope, intercept] for
    # deg=1, so index 1 is the value extrapolated to zero noise.
    coeffs = np.polyfit(scales, stack, deg=1)
    extrapolated = coeffs[1]

    # Clip and renormalise: extrapolation can overshoot below zero, and a
    # distribution that is merely truncated no longer sums to one.
    extrapolated = np.clip(extrapolated, 0.0, None)
    total = extrapolated.sum()
    if total <= 0:
        raise ValueError("extrapolation produced no positive weight")
    return extrapolated / total


def pec_quasiprobability(p_flip: float) -> tuple[np.ndarray, float]:
    """Quasi-probability decomposition of the inverse bit-flip channel.

    The bit-flip channel is (1-p) I + p X.  Its inverse, as a linear map, is
    a I + b X with

        a = (1-p) / (1 - 2p),   b = -p / (1 - 2p)

    Only ``b`` is negative, so sampling weights are |a|, |b| normalised by
    gamma = |a| + |b| = 1/(1-2p), and each sample carries the sign of its
    coefficient.  The variance overhead is gamma^2, which is the real cost PEC
    pays and the original never accounts for.
    """
    if not 0.0 <= p_flip < 0.5:
        raise ValueError(f"p_flip must be in [0, 0.5), got {p_flip}")
    denom = 1.0 - 2.0 * p_flip
    coeffs = np.array([(1.0 - p_flip) / denom, -p_flip / denom])
    gamma = float(np.abs(coeffs).sum())
    return coeffs, gamma


def pec_mitigate_single_qubit(noisy: np.ndarray, p_flip: float) -> np.ndarray:
    """Apply the inverse bit-flip map with correct signs, then renormalise."""
    if noisy.size != 2:
        raise ValueError("this PEC helper covers the single-qubit channel only")
    coeffs, _ = pec_quasiprobability(p_flip)
    flipped = noisy[::-1]
    out = coeffs[0] * noisy + coeffs[1] * flipped
    out = np.clip(out, 0.0, None)
    return out / out.sum()
