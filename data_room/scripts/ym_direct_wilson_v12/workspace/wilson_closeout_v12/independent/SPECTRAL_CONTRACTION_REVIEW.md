# Independent review of V12 direct spectral contraction

The mathematical argument is valid for the specified compact, fixed spatial
lattice Wilson transfer. It proves a positive separation for all physical
states without computing a huge Gram matrix. Its size is approximately
`2.8325769923e-212`, so it does not close the `0.015` target or any uniform
infinite-volume/continuum mass-gap assertion.

## SU(3) endpoint proof and exact cross-ratio

Write the eigenvalues of a special unitary matrix as
`exp(i alpha), exp(i beta), exp(-i(alpha+beta))`. Setting
`c=cos((alpha+beta)/2)` and `d=cos((alpha-beta)/2)` gives

\[
 \operatorname{ReTr}g=2cd+2c^2-1
 \ge 2c^2-2|c|-1
 =2(|c|-1/2)^2-3/2\ge-3/2.
\]

The upper bound three follows term by term. The two endpoints are attained
at a nontrivial central element and the identity. In the kernel cross-ratio
there are two positive and two negative trace terms per link. Its logarithm
is therefore at most `(beta/3)*9=3 beta` per link. Taking
`U=V=I`, `U'=V'=z I` on every link attains the total `3 beta E`.

No gauge projection of the pointwise kernel is needed for this estimate:
it first holds on the entire product group and hence for the invariant
physical subspace. It is not a claim that this worst-case coefficient is
the exact spectral contraction coefficient on physical states.

## Doob normalization and spectral applicability

The kernel is continuous, symmetric, strictly positive on a compact space,
and its convolution factor has nonnegative character coefficients. Thus
the transfer is a compact, positive self-adjoint operator with a simple
strictly positive continuous top eigenfunction. It is gauge invariant by
uniqueness and commutation with the gauge action. The Perron Doob kernel is
a Markov kernel; its cross-ratio cancels both spatial multipliers and all
unknown Perron factors exactly.

The likelihood-ratio proof in the producer is correct: the chord bound on
`(r-1)_+`, followed by `t*m+1/m >= 2 sqrt(t)`, gives the total-variation
coefficient `(sqrt(R)-1)/(sqrt(R)+1)`. A nonzero eigenfunction of the original
continuous integral operator is continuous. Dividing by the positive
Perron function keeps it bounded. For every nonprincipal eigenvalue the
resulting eigenfunction is nonconstant, so oscillation contraction gives
the claimed eigenvalue-ratio bound. Zero eigenvalues also satisfy it.

## Polynomial surrogate and normalized perturbation

The independently checked derivative remainder is less than one at every
listed order, so `p_n'=p_(n-1)>0` on the complete allowed trace interval.
The positive minimum and maximum are consequently the exact rational
endpoint values. The same center configuration attains the polynomial
kernel cross-ratio `(M_n/m_n)^(2E)`. Character coefficient positivity gives
positive semidefiniteness, and positive pointwise kernels give simple top
eigenvalues. The ratio deficit `2(m_n/M_n)^E/(1+(m_n/M_n)^E)` is therefore
a bound on the actual finite-surrogate spectrum, without diagonalization.

The factor-one normalization bound from V11 is also valid. If
`D=T-T_n`, `0<=D<=eta*lambda_0 I`, and `d=lambda_0-mu_0`, then

\[
 \frac{T}{\lambda_0}-\frac{T_n}{\mu_0}
 =\frac{D}{\lambda_0}-\frac{dT_n}{\lambda_0\mu_0}.
\]

Each positive term is between zero and `eta I`; their difference lies
between `-eta I` and `eta I`. The bound is `eta`, not an assumed equality
and not an estimate imported from the affine logarithmic surrogate.
The variational principle now gives a physical deficit at least
`delta_n-eta_n` when positive. Scalar changes from `Z_beta` to `Z_n`
cancel under Perron normalization.

## Independent arithmetic and execution boundary

`verify_spectral_contraction.py` imports none of the producer's code or
interval functions. It computes rational exponential enclosures from
Taylor sums with geometric tails (orders 512 and 1800), evaluates each
endpoint by descending Horner recursion, calculates exact rational
surrogate deficits, and checks the producer's decimal intervals and
conservative remainders. It also checks the source hashes.

The sufficient transferred-gap test fails at orders 72, 246 and 247 and
passes at orders 248 and 255. A failed sufficient test is not a statement
that the corresponding actual transfer has zero gap. No proof is asserted
here that 248 is globally optimal among approximation methods.

The complete retained space is mathematically specified. Its full Gram
matrix, vacuum coordinates, and individual physical moment matrices have
not been executed by this scalar certificate. The fixed-volume result
decays with beta and the number of links; continuum obligations remain
open. No substantive mathematical gap was found within this stated scope.
