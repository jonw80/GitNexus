# Certified character support compression

This calculation compresses the V15 one-plaquette squared weight before coupled integration. It does not evaluate the coupled spatial Gram matrix.

Let

\[
f(U)=p_{233}\!\left(\frac{271}{240}(3+\chi_3(U)+\chi_{\bar3}(U))\right)^2
=\sum_{p+q\le466}c_{pq}\chi_{pq}(U).
\]

All coefficients are positive exact rationals, with conjugate symmetry. The shift is nonnegative on SU(3), so \(f(U)\ge1\). These are the unscaled V15 factors, not independently normalized plaquette probabilities.

For a complete triangular character cutoff \(K\), define

\[
f_K=\sum_{p+q\le K}c_{pq}\chi_{pq},\qquad
\epsilon_K=\sum_{p+q>K}c_{pq}d_{pq},\qquad
d_{pq}=\frac{(p+1)(q+1)(p+q+2)}2.
\]

Unitarity implies \(|\chi_{pq}(U)|\le d_{pq}\). Consequently, for every SU(3) matrix,

\[
|f-f_K|\le\epsilon_K\le\epsilon_K f.
\]

Conjugate symmetry makes \(f_K\) real. If \(\epsilon_K<1\),

\[
0<(1-\epsilon_K)f\le f_K\le(1+\epsilon_K)f.
\]

This proof does not assume individual characters are nonnegative or that discarding positive character coefficients is pointwise monotone. Neither assertion would be valid in general.

For any linked plaquette holonomies, without any independence assumption,

\[
(1-\epsilon_K)^s\prod_{j=1}^s f(U_{p_j})
\le\prod_{j=1}^s f_K(U_{p_j})
\le(1+\epsilon_K)^s\prod_{j=1}^s f(U_{p_j}).
\]

Set \(s=18\) if the six earlier plaquette factors remain exact, or \(s=24\) when truncating every factor. Multiplication by the remaining positive factors preserves the bound. Hence, on any common retained basis, integrating the quadratic form \(|\sum_i v_i\psi_i(U)|^2\) gives

\[
(1-\epsilon_K)^sG\preceq G_K\preceq(1+\epsilon_K)^sG.
\]

In particular,

\[
\left\|G^{-1/2}(G_K-G)G^{-1/2}\right\|
\le (1+\epsilon_K)^s-1.
\]

The inverse exists for a finite linearly independent Haar basis because the original product weight is at least one. The bound is basis independent and applies to all retained states, not only the 729-state principal submatrix. It is a relative matrix-approximation certificate, **not an evaluated matrix**.

The exact calculation sums the positive rational coefficients into total-degree shells, sums all discarded dimension-weighted shells, and finds the first cutoff meeting each specified 24-factor error. Upper decimals are rounded toward positive infinity. Exact single-factor tails are included in the certificate. A finite character MPO for \(\chi_r(U_1U_2U_3^*U_4^*)\) can retain two representation matrix indices across a cut; the reported direct-sum matrix-element dimension is \(\sum_{p+q\le K}d_{pq}^2\). It is not an optimal tensor-network bond dimension or an estimate of total contraction cost.

## Remaining computation

Shared-link Haar tensors, physical retained-basis indices, and elimination of the lattice's connected cycles remain. The support truncation reduces the local factor count and comes with an all-24-factor relative error certificate, but it does not remove those dependencies. No full coupled Gram matrix, spectral gap, or continuum claim follows from this compression alone.
