# Relative-kernel construction of the normalized Wilson transfer

This is a stronger construction than the absolute dressed-cutoff estimate in
`dressed_space.md`. The error is relative to the true vacuum normalization;
it does not contain `exp(325.2)` and does not need a numerical vacuum trial.
All statements below are on the complete finite-volume Hilbert space, with
the gauge-invariant restriction understood when discussing physical states.

The proof constructs a finite-rank positive operator with an explicitly
specified polynomial temporal kernel. It does not assert that the enormous
retained Gram matrix or its eigenvectors have already been materialized.

## 1. A polynomial with positive character coefficients

Set `beta=271/20`, `t=beta/6`, and

\[
 x(g)=\frac{\beta}{3}\operatorname{Re}\operatorname{Tr}g
     =t\bigl(\chi_3(g)+\chi_{\bar3}(g)\bigr),
 \qquad -\beta/2\le x(g)\le\beta.
\]

For an integer `n>=0`, let

\[
 p_n(x)=\sum_{j=0}^{n}\frac{x^j}{j!}.
\]

The direct sum representation `V=3+3bar` has character
`chi_V=chi_3+chi_3bar`. Thus

\[
 p_n(x(g))=\sum_{r}a_r^{(n)}\chi_r(g),\qquad
 a_r^{(n)}=\sum_{j=0}^{n}\frac{t^j}{j!}
            \operatorname{mult}(r,V^{\otimes j})\ge0.
\]

Every coefficient is an exactly computable nonnegative rational number.
Tensoring with a fundamental or antifundamental increases `p+q` by at most
one, so `a_(p,q)^(n)=0` for `p+q>n`. Conversely, the highest-weight summand of
`3^tensor p tensor 3bar^tensor q` is `(p,q)`. This occurs in
`V^tensor(p+q)`, proving

\[
 a_{p,q}^{(n)}>0\quad\Longleftrightarrow\quad p+q\le n.
\]

The exact exponential has the same series continued through every `j`.
Its character coefficients are therefore at least those of the polynomial.
This assertion is coefficientwise positivity; it does **not** incorrectly
assume that a character, or a pointwise Taylor remainder, is nonnegative.

Let

\[
 Z_\beta=\int_{SU(3)}e^{x(g)}\,dg.
\]

Denote convolution by `e^x/Z_beta` by `C_1`, and convolution by
`p_n(x)/Z_beta` by `C_(1,n)`. Schur orthogonality gives their eigenvalues on
irrep matrix coefficients as `a_r/(d_r Z_beta)` and
`a_r^(n)/(d_r Z_beta)`. Consequently

\[
 0\le C_{1,n}\le C_1
\]

in operator order. Moreover the range of `C_(1,n)` is exactly the complete
one-link Peter--Weyl space of degree at most `n`.

## 2. Uniform relative pointwise error

If `n+2>beta`, the absolute exponential tail is bounded by

\[
 r_n=\sum_{j>n}\frac{\beta^j}{j!}
 \le\frac{\beta^{n+1}}
 {(n+1)!\,[1-\beta/(n+2)]}=:R_n.
\]

Therefore on the entire allowed trace interval,

\[
 |e^x-p_n(x)|\le R_n,
 \qquad
 \left|\frac{p_n(x)}{e^x}-1\right|
 \le e^{\beta/2}R_n=:\epsilon_n.
\]

The useful construction chooses `epsilon_n<1`. It then follows that `p_n`
is strictly positive on the entire trace interval and

\[
 (1-\epsilon_n)e^x\le p_n(x)\le(1+\epsilon_n)e^x.
\]

Here is an optional strictly sharper proved bound. For `x>=0`,

\[
 \frac{d}{dx}\left(1-e^{-x}p_n(x)\right)
     =e^{-x}\frac{x^n}{n!}\ge0.
\]

The positive-side relative error is thus at most `exp(-beta) R_n`.
For `x=-y`, `0<=y<=beta/2`, the integral or Lagrange Taylor remainder gives

\[
 |e^{-y}-p_n(-y)|\le\frac{y^{n+1}}{(n+1)!}.
\]

Hence the following is also an admissible uniform relative error:

\[
 \epsilon_n^{\rm sharp}=
 \max\left\{e^{-\beta}R_n,
 e^{\beta/2}\frac{(\beta/2)^{n+1}}{(n+1)!}\right\}.
\]

All subsequent statements accept either certified epsilon. They remain
valid if the deliberately coarser first bound is used.

## 3. Tensor products preserve both kinds of control

Put `E=24`, `C=C_1^tensor E` and `C_n=C_(1,n)^tensor E`. All these operators
are simultaneously diagonal in the link representation basis, with
nonnegative eigenvalues. Thus

\[
 0\le C_n\le C.
\]

Let `k(U,V)` and `k_n(U,V)` be their product convolution kernels. The previous
relative estimate gives

\[
 (1-\epsilon)^E\le\frac{k_n(U,V)}{k(U,V)}
                   \le(1+\epsilon)^E.
\]

Because `(1+epsilon)^E+(1-epsilon)^E>=2`,

\[
 |k-k_n|\le\eta_n k,\qquad
 \eta_n=(1+\epsilon)^E-1.
\]

For odd `n` a further simplification is available: the Taylor remainder
`e^x-p_n(x)` has the sign of `x^(n+1)`, and is therefore nonnegative for
every real `x`. In that case

\[
 0\le k-k_n\le\bigl[1-(1-\epsilon)^E\bigr]k.
\]

Thus odd `n` permits the smaller choice
`eta_n=1-(1-epsilon)^E`. This refinement is optional; the general formula
works for every parity. The true `Z_beta` appears in both kernels and cancels
in every pointwise ratio.

## 4. Actual Wilson dressing and a relative operator bound

Let `S=exp(aD/2)` as in `dressed_space.md`, and define

\[
 T=SCS,\qquad T_n=SC_nS,\qquad\Delta_n=T-T_n.
\]

Operator positivity proved in Section 3 gives `Delta_n>=0`. Multiplying both
kernel variables by the same positive function `s` preserves the pointwise
relative estimate:

\[
 |\Delta_n(U,V)|\le\eta_n T(U,V).
\]

Put `lambda_0=||T||`. For every `f`, the nonnegative kernel of `T` gives the
following direct quadratic-form estimate:

\[
 \begin{split}
 |\langle f,\Delta_n f\rangle|
 &\le\iint |\Delta_n(U,V)|\,|f(U)|\,|f(V)|\,dU\,dV\\
 &\le\eta_n\langle |f|,T|f|\rangle\\
 &\le\eta_n\lambda_0\|f\|^2.
 \end{split}
\]

For a gauge-invariant `f`, its absolute value is also gauge invariant, so
this proof applies directly on the physical Hilbert space. Self-adjointness
now implies

\[
 \boxed{0\le\Delta_n\le\eta_n\lambda_0 I.}
\]

There is **no spatial-weight factor** in this estimate, and no Perron
eigenfunction enters the proof. Gauge averaging preserves the pointwise
bound as well. The operator norm `lambda_0` is the true vacuum eigenvalue:
the continuous strictly positive compact kernel has a unique positive top
eigenvector, which is gauge invariant because `T` commutes with the gauge
group and its positive top eigenspace is one-dimensional.

## 5. Complete revised retained space and external complement

Let `E_box(n)` project onto every spin network for which

\[
 p_e+q_e\le n\quad\hbox{for each of the 24 links}.
\]

Include every allowed invariant-tensor multiplicity, every momentum and
every flux sector. Section 1 proves exactly

\[
 \operatorname{range}(C_n)=\operatorname{range}(E_{\rm box}(n)).
\]

Therefore `T_n` has finite rank and

\[
 \mathcal R_n=\operatorname{range}(T_n)
       =S\operatorname{range}(E_{\rm box}(n)).
\]

For an orthonormal electric basis let `F=S E_box(n)`, `G=F*F`,
`U=F G^(-1/2)`, and `P=UU*`, `Q=I-P`. The previous Gram lower bound proves
that these inverse square roots exist. The same positive-residual argument
as in `dressed_space.md`, with `delta=eta_n lambda_0`, yields

\[
 \boxed{0\le Q(T/\lambda_0)Q\le\eta_n Q},
 \qquad
 \boxed{\|Q(T/\lambda_0)U\|\le\eta_n/2}.
\]

In particular this is a bound on the **entire external complement**, not
just on omitted high degrees. The retained space is defined independently of
the incomplete old coordinate catalog.

For physical retained compression `A=U*TU`, surrogate `A_n=U*T_nU` and
`D_n=A-A_n`, the sharper matrix inequality is

\[
 B^*B\le\eta_n\lambda_0D_n-D_n^2,
 \quad B=QTU.
\]

All exact same-operator integral identities for `G,H,J,A,M2,B*B` in the
companion note remain valid after replacing its total-degree projector by
this complete box projector. Its `C` factors remain the **full** convolution
when physical moments are meant. Substituting the polynomial `C_n` defines
surrogate moments and must be labeled as such.

## 6. Certified normalization without knowing the true vacuum

Let `lambda_n=||T_n||`. Assume `eta_n<1`, as for the useful choices of `n`.
Positive operator order and Section 4 give

\[
 (1-\eta_n)\lambda_0\le\lambda_n\le\lambda_0,
 \qquad
 \boxed{\lambda_n\le\lambda_0
                   \le\frac{\lambda_n}{1-\eta_n}}.
\]

The same factor-one argument proved in the companion note gives

\[
 \boxed{\left\|\frac{T}{\lambda_0}
              -\frac{T_n}{\lambda_n}\right\|\le\eta_n}.
\]

For completeness, write `d=lambda_0-lambda_n`, so
`0<=d<=eta_n lambda_0`. Then the difference above is
`Delta_n/lambda_0-d T_n/(lambda_0 lambda_n)`. Both positive terms are bounded
by `eta_n I`, so their difference is bounded in norm by `eta_n`, not twice
that value.

The temporal normalization `Z_beta^(-24)` is a common scalar multiplier in
`T_n` and `lambda_n`; it cancels exactly in `T_n/lambda_n`. Thus the
normalized polynomial transfer can be specified using the exact rational
character coefficients without importing approximate Bessel normalization
constants. The spatial exponential is still the exact function `S`; it is
not an exponential of a truncated matrix.

**Normalization convention for the executed coefficient table.** The stored
rational one-link eigenvalues divide the polynomial by its own exact
partition integral `Z_n`, rather than by `Z_beta`. If tildes denote this
stored convention, then

\[
 \widetilde T_n=(Z_\beta/Z_n)^{24}T_n,
 \quad\widetilde\lambda_n=(Z_\beta/Z_n)^{24}\lambda_n,
 \quad\frac{\widetilde T_n}{\widetilde\lambda_n}
       =\frac{T_n}{\lambda_n}.
\]

The normalized operator and all its stated normalized error bounds are
unchanged. The inequalities `T_n<=T` and the ratio enclosure
`1-eta_n<=lambda_n/lambda_0<=1` refer specifically to the `Z_beta`
suboperator convention. They must not be applied to `tilde(lambda_n)`
without the displayed scalar conversion.

If `mu_j` are the ordered eigenvalues of `T_n`, with zeros appended, and
`lambda_j` those of `T`, the normalized operator estimate and the min--max
principle imply

\[
 \left|\frac{\lambda_j}{\lambda_0}
        -\frac{\mu_j}{\lambda_n}\right|\le\eta_n.
\]

Consequently an independently evaluated finite-matrix bound
`mu_1/lambda_n<=r` with `r+eta_n<1` proves

\[
 \operatorname{gap}[-\log(T/\lambda_0)]
 \ge-\log(r+\eta_n).
\]

The approximation theorem alone does not supply `r`. In particular it does
not turn a very small truncation error into a computed large physical gap.

One useful consequence needs no gap estimate. If `phi` is the exact unit
vacuum, its component outside the revised retained space satisfies

\[
 Q\phi=Q(T/\lambda_0)P\phi+Q(T/\lambda_0)Q\phi,
 \qquad
 \|Q\phi\|\le\frac{\eta_n}{2(1-\eta_n)}\|P\phi\|
             \le\frac{\eta_n}{2(1-\eta_n)}.
\]

Thus the exact vacuum is contained in the revised space to this norm error.
This does not identify its coordinates inside the retained space or prove
that the finite Perron eigenvector approximates it to the same accuracy;
that latter claim would require a suitable eigenvalue-separation estimate.

## 7. Executed scalar certificate at order 72

The companion `DIRECT_NORMALIZED_WILSON_CERTIFICATE.json` records the
outward evaluation at `n=72`; its exact character table contains all
`(73*74)/2=2701` one-link representations. Rounded **upward** for readability,
its consequences are

| Certified quantity | Upper bound |
|---|---:|
| Single-link relative kernel error | `1.5289560233e-29` |
| Normalized full transfer error | `3.6694944559e-28` |
| Entire normalized external compression | `3.6694944559e-28` |
| Normalized crossing norm | `1.8347472280e-28` |
| Normalized crossing squared, `B*B` | `3.3662973904e-56` |

The second-moment operators obey the independent consequence

\[
 \left\|(T/\lambda_0)^2-(T_n/\lambda_n)^2\right\|
 \le2\eta_n<7.3389889117\times10^{-28},
\]

by writing `X²-Y²=X(X-Y)+(X-Y)Y` for the two contractions `X,Y`.

These errors apply to the newly defined full dressed box. They do not become
error bounds for the old V9 retained catalog. The new box has at least
`2701^6=388282220975269366201` independent states, already witnessed by
product characters on the six edge-disjoint plaquettes. Multiplication by
`S` is invertible and preserves that dimension. This lower bound makes the
matrix execution boundary concrete.

## 8. What is constructive and what remains to be executed

The polynomial `p_n`, its finite exact rational character coefficient table,
the tensor-product temporal kernel, and the exact spatial dressing specify
`T_n` completely. The retained box and its orthogonal projection are exact
finite definitions. A scalar certificate for `epsilon_n,eta_n` certifies the
normalized operator and full-complement errors without enumerating its rank.

Materializing the full Gram matrix, certifying its eigenvalue separation, or
producing numerical physical `A,M2,B*B` entries is a different computation.
The finite box can be astronomically large despite its compact factorized
kernel description. Claims of executed matrices must therefore be supported
by actual matrix artifacts, not by these formulas alone.

For any fixed finite volume the approximation error tends to zero as
`n->infinity`. The approximation theorem does not establish a nonvanishing
gap uniformly as the volume grows, continuum correlation-function limits,
nontriviality, Euclidean covariance or physical continuum identification.
