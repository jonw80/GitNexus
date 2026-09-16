# Direct Wilson spectral separation without the huge Gram matrix

This is an executed **analytic spectral enclosure** for the actual fixed-volume
Wilson transfer and its complete polynomial surrogates. It does not construct
the enormous Gram matrix, numerical eigenvectors, or a useful continuum gap.
It supplies an independently proved surrogate eigenvalue ratio `r`, which was
missing from the V11 finite-rank approximation discussion. The resulting
separation is exponentially small, so the target `0.015` gate remains open.

## 1. A likelihood-ratio contraction lemma

Let `P_x` and `P_y` be probability measures with strictly positive densities
relative to a common measure. Suppose

\[
 \sup_{u,v}\frac{P_x(u)P_y(v)}{P_y(u)P_x(v)}\le R,\qquad R\ge1.
\]

Then their total variation distance, with convention
`TV(P,Q)=sup_A |P(A)-Q(A)|`, obeys

\[
 \operatorname{TV}(P_x,P_y)\le\frac{\sqrt R-1}{\sqrt R+1}.
\]

**Proof.** Set `r=dP_x/dP_y`, `m=inf r`, `M=sup r`. Its mean is one,
so `m<=1<=M`, and `M/m<=R`. The convex function `(r-1)_+` lies below
its chord over `[m,M]`; integrating gives

\[
 \operatorname{TV}(P_x,P_y)
 \le\frac{(M-1)(1-m)}{M-m}.
\]

Put `t=M/m`. The last expression equals
`[(t+1)-tm-1/m]/(t-1)`. The arithmetic-geometric mean inequality
`tm+1/m>=2 sqrt(t)` makes this at most
`(sqrt(t)-1)/(sqrt(t)+1)`, which increases with `t`. The case `t=1`
has zero variation. This proves the claim, including limiting infima.

Consequently every bounded real function satisfies

\[
 \operatorname{osc}(Pf)\le
 \frac{\sqrt R-1}{\sqrt R+1}\operatorname{osc}(f).
\]

This follows from the dual characterization of total variation applied to
`(f-inf f)/osc(f)`, whose values lie in `[0,1]`.

## 2. Exact Wilson normalization cancels out of the cross-ratio

Let `X=SU(3)^24` with normalized product Haar measure,

\[
 T(U,V)=s(U) k(U,V)s(V),\quad
 k(U,V)=Z_\beta^{-24}
 \exp\left[\frac\beta3\sum_e\operatorname{ReTr}(U_eV_e^*)\right],
 \quad s(U)=e^{\beta D(U)/6}.
\]

This is the actual Wilson transfer used in V11. Its continuous strictly
positive kernel makes it compact and positivity improving. Its largest
eigenvalue `lambda_0` is simple, with continuous strictly positive
eigenfunction `phi`. The V10/V11 positivity argument makes the spectrum
nonnegative. Gauge invariance of `T` and simplicity make `phi` gauge
invariant. These conclusions hold before numerical computation of `phi`.

The exactly normalized Perron Doob kernel is

\[
 P_U(dV)=\frac{T(U,V)\phi(V)}{\lambda_0\phi(U)}dV.
\]

All spatial factors, Perron factors and scalar normalization cancel in

\[
 \frac{P_U(V)P_{U'}(V')}{P_{U'}(V)P_U(V')}
 =\frac{k(U,V)k(U',V')}{k(U',V)k(U,V')}.
\]

For `g in SU(3)`, `-3/2<=ReTr(g)<=3`. Thus the logarithm of each
one-link cross-ratio is at most `3 beta`, and the full one is at most
`3 beta E`, where `E=24`. This maximum is actually attained: take
`U=V=I`, `U'=V'=zI` on every link, where `z=exp(2 pi i/3)`.
Both numerator traces equal three and both denominator traces equal
`-3/2`. The cross-ratio maximum is unchanged by the exact positive spatial
dressing. Attainment concerns the kernel cross-ratio; it does not assert
sharpness of the gauge-invariant spectral-gap estimate.

Applying Section 1 with `R=exp(3 beta E)` gives

\[
 \theta=\frac{e^{3\beta E/2}-1}{e^{3\beta E/2}+1},\qquad
 \delta=1-\theta=\frac{2}{e^{3\beta E/2}+1}.
\]

For every nonconstant eigenfunction of the Doob operator, oscillation
contraction implies `|lambda_j/lambda_0|<=theta`. To justify using
oscillation, a nonzero eigenfunction of a continuous compact integral
kernel is continuous, and division by the strictly positive continuous
`phi` preserves boundedness. The zero eigenvalue already satisfies the
bound. Restricting to the gauge-invariant subspace cannot introduce an
eigenvalue violating it. Hence this is a bound on **all** physical states,
every momentum, flux and electric degree.

The physical logarithmic transfer gap therefore satisfies

\[
 \boxed{\Delta_{\rm Wilson}\ge-\log(1-\delta)\ge\delta.}
\]

At `beta=271/20`, `E=24`, the executed outward interval gives

\[
 \boxed{\Delta_{\rm Wilson}>
 2.83257699229844260396763384223609\times10^{-212}.}
\]

The constant improves the V10 minorization lower bound by essentially a
factor of two. This is rigorous finite-volume progress, not a large gap.

## 3. An actual finite-surrogate spectral ratio

Use V11's polynomial `p_n(x)=sum_(j=0)^n x^j/j!` and the same exact
spatial function `s`. For all orders used below, the executed uniform
relative error for `p_(n-1)` is less than one on `[-beta/2,beta]`.
Therefore `p_n'=p_(n-1)>0`, and its exact minimum and maximum are

\[
 m_n=p_n(-\beta/2)>0,\qquad M_n=p_n(\beta)>m_n.
\]

Both are **exact rational numbers** stored in the certificate. The
polynomial temporal kernel is a product of 24 positive factors between
these two endpoints, so its cross-ratio is at most `(M_n/m_n)^(2E)`.
The same center configuration attains this kernel bound. The same
Doob argument proves for the finite-rank positive operator `T_n`

\[
 \boxed{\frac{\mu_1}{\mu_0}\le1-\delta_n,\qquad
 \delta_n=\frac{2(m_n/M_n)^E}{1+(m_n/M_n)^E}>0.}
\]

No numerical diagonalization, matrix entries, or approximate vacuum are
assumed here. This is an analytically certified bound on the actual
surrogate eigenvalues, obtained directly from its kernel. The scalar
`Z_beta^(-E)` or `Z_n^(-E)` cancels after normalization.

V11 independently proves
`||T/lambda_0-T_n/mu_0||<=eta_n`. The variational eigenvalue principle
therefore gives the physical bound

\[
 \lambda_1/\lambda_0\le1-\delta_n+\eta_n.
\]

If `eta_n<delta_n`, then

\[
 \boxed{\Delta_{\rm Wilson}\ge\delta_n-\eta_n>0.}
\]

This supplies the missing finite-matrix spectral-ratio condition by an
analytic enclosure. It avoids claiming that a small truncation error
alone implies a gap.

## 4. Executed cutoff comparison

All numbers displayed here are rounded in the conservative direction.

| Polynomial order | Normalized error upper bound | Transfer via this surrogate |
|---:|---:|---:|
| 72 | `3.669494456e-28` | Does not beat the contraction deficit |
| 246 | `6.136673450e-211` | Does not beat the contraction deficit |
| 247 | `3.352122158e-212` | Does not beat the contraction deficit |
| 248 | `1.823726980e-213` | Gap greater than `2.65020429438379e-212` |
| 255 | `2.302018922e-222` | Positive, nearly the direct bound |

Order 248 is the first passing order **among those scanned at this
boundary**; no optimization theorem about every possible finite
approximation is asserted. Its **31,125 one-link irreps have now also been
materialized**, with exact integer character numerators over one common
denominator, in `EXACT_ORDER248_TEMPORAL_FACTOR.json.gz`. The generation
check verifies 249 tensor-dimension identities, positivity and conjugation
for every coefficient, five exact polynomial values using an independent
Jacobi--Trudi character evaluation, and the exact center endpoint. The
compressed coefficient file is 10,569,454 bytes. The astronomical spatial
Gram matrix remains uncomputed.

To reproduce:

```sh
python wilson_closeout_v12/design/certify_direct_spectral_contraction.py
python wilson_closeout_v12/design/build_order248_temporal_factor.py
```

The certificate records dependency hashes. Stable arithmetic computes the
deficit directly, never by subtracting a `1e-212` number from one at
ordinary precision. Every displayed interval for the rational deficit is
checked against its exact fraction.

## 5. Remaining calculation and its precise scope

This step closes an all-state, fixed-volume **positive separation** and the
finite-surrogate spectral-ratio prerequisite at a sufficiently accurate
cutoff. The full Gram matrix, numerical vacuum coordinates and numerical
physical moments remain uncomputed. The direct bound is much smaller than
the requested `0.015` threshold. It decreases as
`2 exp(-3 beta E/2)` as volume or beta increases, so it does not close a
uniform mass gap or any continuum obligation.

Improving this substantially requires information beyond a worst-case
temporal cross-ratio: for example a rigorous compression of the actual
spatially weighted kernel or a positive vacuum trial with a sharp certified
residual. This kernel contraction argument already uses the exact maximal
cross-ratio; simply repeating it more accurately will not produce `0.015`.
No affine `aD+log C` eigenvalue is imported into this calculation.
