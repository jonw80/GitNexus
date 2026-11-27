"""Post-hoc (not pre-registered): chance that ANY base formula of family G plus ANY correction term of family E
lands within +-1 sigma of a target, estimated by moving the target.  python3 -I two_step_lookelsewhere.py"""
from fractions import Fraction
import numpy as np
from mpmath import mpf, gamma, pi, sqrt, log
lg1, lg2, lpi, lr5 = (float(log(gamma(mpf(1) / 5))), float(log(gamma(mpf(2) / 5))), float(log(pi)), float(log(sqrt(5))))
coefs = sorted({Fraction(p, q) for p in range(1, 11) for q in range(1, 11)})
lc = np.array([np.log(c.numerator / c.denominator) for c in coefs])
e6 = np.arange(-6, 7)
A, B, C, E = np.meshgrid(e6, e6, e6, np.array([0, 1]), indexing="ij")
G = np.exp(((A * lpi + B * lg1 + C * lg2 + E * lr5).ravel()[:, None] + lc[None, :]).ravel())
a = 1 / 137.035999177
corr = np.array(sorted({float(c.numerator) / c.denominator * a ** k * np.pi ** m
                        for c in coefs for k in (1, 2, 3) for m in range(-3, 4)}))
sig = 2.1e-8


def hits(t, signs, G, corr, sig):
    """Number of (base g, sign s) with some correction c in corr such that |g + s c - t| <= sig.

    corr must be sorted and positive. Every base within the largest correction (plus sig) of t is
    considered. (Corrected 2026-11-26: the first version kept only bases within 0.1% of t, which drops
    pairs whose correction is larger than 0.1% of t.)
    """
    near = G[np.abs(G - t) <= corr[-1] + sig]
    n = 0
    for s in signs:
        d = (t - near) * s                        # needed correction, with the sign allowed
        d = d[d > 0]
        i = np.searchsorted(corr, d)
        ok = np.zeros(len(d), dtype=bool)
        for j in (i - 1, i):
            inb = (j >= 0) & (j < len(corr))
            ok[inb] |= np.abs(corr[j[inb]] - d[inb]) <= sig
        n += int(ok.sum())
    return n


if __name__ == "__main__":
    print("actual target 137.035999177:", hits(137.035999177, (1,), G, corr, sig), "pair(s) with positive correction")
    rng = np.random.default_rng(1)
    T = 137.035999177 * (1 + rng.uniform(-1e-3, 1e-3, 4000))
    for signs, label in (((1,), "positive corrections"), ((1, -1), "either sign")):
        h = np.array([hits(t, signs, G, corr, sig) for t in T])
        print(f"random targets within 0.1% ({label}): P(at least one hit) = {np.mean(h > 0):.4f}, mean hits = {h.mean():.4f}")
