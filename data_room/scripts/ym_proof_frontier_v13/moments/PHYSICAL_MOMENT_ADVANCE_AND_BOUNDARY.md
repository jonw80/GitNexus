# Actual Wilson spatial moments and the remaining matrix gate

This calculation concerns the full finite Wilson transfer, with temporal
coupling fixed at beta = 271/20. It supplies exact spatial integration data and
rigorous numerical physical moments on a specified two-dimensional test space
at a small anisotropic spatial coupling. It does **not** supply the complete
retained physical matrices at the target isotropic coupling.

## Operator, common basis, and meaning of the new calculation

Use the pinned 24-link, 24-plaquette geometry and normalized product Haar
measure. Let

\[
D=\sum_{p=0}^{23}\operatorname{Re}\operatorname{Tr}U_p,\quad
C=C_\beta^{\otimes24},\quad T(t)=e^{tD/2}C e^{tD/2}.
\]

The target is t = beta/3 = 271/60. Here t is varied solely to construct an
exact analytic calculation and test its domain of validity. Replacing that
target by a small t is not a solution of the target-coupling problem.

The executed common basis begins with

\[
e=(1,D/\sqrt{12}),\quad F(t)=e^{tD/2}e,\quad
G(t)=F(t)^*F(t),\quad U(t)=F(t)G(t)^{-1/2}.
\]

For real t, the columns of U(t) are orthonormal. Denote their Gram matrix by
I; this does not redefine any earlier action moment called N. Define

\[
H=e^*e^{tD}Ce^{tD}e,\qquad
J=e^*e^{tD}Ce^{tD}Ce^{tD}e.
\]

Then the actual same-operator moments are

\[
A=G^{-1/2}HG^{-1/2},\qquad M_2=G^{-1/2}JG^{-1/2},
\quad B^*B=M_2-A^2,
\quad B=(I-UU^*)TU.
\]

The intermediates in H and J use the full multiplication and full temporal
operator, with no two-dimensional projector inserted between factors. Thus
the crossing refers to the entire complement of this two-dimensional space.
That space is a numerical construction test, distinct from the complete
order-248 retained space in V12.

## Exact full-geometry Haar integration

`exact_spatial_jets.py` enumerates every oriented-plaquette trace multiset of
total degree at most four. Linkwise multiplication by a center element proves
that any multiset with nonzero link triality has zero integral. Every survivor
is evaluated exactly. Single-loop survivors use SU(3) character fusion. All
other survivors use the Haar tensors

\[
\int U_{ab}\bar U_{cd}\,dU=\delta_{ac}\delta_{bd}/3
\]

and the two-fundamental/two-antifundamental tensor, whose two Weingarten
coefficients are 1/8 and -1/24. These are exact SU(3) formulas at this degree:
there is no extra determinant sector when the two degrees match and are
below three. The program explicitly checks that no mixed survivor requires
a different Haar tensor. Free closed indices each contribute the integer 3.

The resulting exact moments are

\[
\int1=1,\quad\int D=0,\quad\int D^2=12,\quad
\int D^3=6,\quad\boxed{\int D^4=3890/9}.
\]

There are 249,900 degree-four multisets, of which 312 survive the exact center
filter. The fourth moment contains the finite-torus surface contribution
2/9 beyond the independent-plaquette expression 432. Therefore this is an
integration of the actual geometry, rather than an independent-plaquette
replacement.

For example, the true spatial partition function begins

\[
\int e^{tD}=1+6t^2+t^3+(1945/108)t^4+O(t^5).
\]

## Exact complete temporal spectral moments of the spatial action

Set x = c_(1,0), y = c_(2,0), z = c_(1,1), with charge-conjugate coefficients
equal. The projectors on each link are

\[
3\otimes3=6\oplus\bar3,\quad P_6=(I+\mathrm{Swap})/2,
\quad P_{\bar3}=(I-\mathrm{Swap})/2,
\]

\[
3\otimes\bar3=1\oplus8,\quad
(P_1)_{ac;bd}=\delta_{ac}\delta_{bd}/3,\quad P_8=I-P_1.
\]

Applying the full central convolution to the right pair of plaquette traces
and then integrating against the left pair gives 1,800 exact contractions.
The result is the positive polynomial

\[
\begin{split}
Q(x,y,z)={}&144+6z^4+3y^4+\frac{89}{27}x^4
 +\frac{64}{27}x^4z+\frac{256}{27}x^4z^2\\
&+\frac{16}{3}x^4y^2+\frac{16}{3}x^5y
 +\frac{20}{3}x^6+\frac{128}{3}x^6z\\
&+32x^6y+16x^7+\frac{4214}{27}x^8.
\end{split}
\]

For every nonnegative integer j,

\[
\boxed{q_j=\langle D^2,C^jD^2\rangle=Q(x^j,y^j,z^j).}
\]

The checks Q(1,1,1) = 3890/9 and Q(0,0,0) = 144 respectively recover the
identity action and the constant Haar projector. All coefficients are
nonnegative squared spectral weights. A separate diagnostic applies the V9
spatial D matrix twice to its Haar vacuum and groups squared amplitudes by
link irreps. It matches all 13 rational weights to ordinary floating-point
roundoff. This is an independent consistency check, not the proof of the
rational coefficients; the exact tensor calculation is authoritative.

Directed evaluation of the certified Wilson coefficient intervals gives

\[
\kappa=x^4=0.25822917671824958944\ldots,
\quad q_1=164.0103926594691159854\ldots,
\quad q_2=145.5667664284859451028\ldots.
\]

The JSON contains outward endpoints rather than rounded point estimates.

## Fully specified physical matrix Taylor coefficients

All subscripts below label coefficients of t^k, not derivatives. Put

\[
C_P=\operatorname{diag}(1,\kappa),\quad
d=\begin{pmatrix}0&\sqrt{12}\\\sqrt{12}&1/2\end{pmatrix},
\quad d_2=\begin{pmatrix}12&\sqrt3\\\sqrt3&3890/108\end{pmatrix},
\]

\[
R_j=\begin{pmatrix}12\kappa^j&\sqrt3\kappa^j\\
\sqrt3\kappa^j&q_j/12\end{pmatrix}.
\]

Direct expansion of the unprojected products yields

\[
G_0=I,\ G_1=d,\ G_2=d_2/2;
\quad H_0=C_P,\ H_1=dC_P+C_Pd,
\quad H_2=(d_2C_P+C_Pd_2)/2+R_1,
\]

\[
J_0=C_P^2,\quad J_1=dC_P^2+C_PdC_P+C_P^2d,
\]

\[
J_2=(d_2C_P^2+C_Pd_2C_P+C_P^2d_2)/2
      +R_1C_P+C_PR_1+R_2.
\]

The inverse square-root series is

\[
G^{-1/2}=I-td/2+t^2(3d^2/8-d_2/4)+O(t^3).
\]

Multiplying these explicit matrix series supplies A and M2 in one and the
same orthonormal dressed basis. `certify_physical_moment_jets.py` executes
the matrix arithmetic with directed intervals. It independently checks the
second-order crossing identity against

\[
\boxed{(B^*B)_2=\operatorname{diag}
\left(0,\frac{q_2-144-3\kappa^2}{12}\right).}
\]

Indeed, at t = 0 the first crossing column is zero; the second is
C Q_0 D^2/sqrt(12), where Q_0 removes 1 and D/sqrt(12). Squaring its norm
gives the displayed identity using the *full* C. Its nonzero entry is

\[
0.1138932921133491812856537997267\ldots>0.
\]

## True Perron normalization and rigorous local remainder

At t = 0, the top eigenvector of C is 1 and its eigenvalue is 1. The already
certified all-irrep coefficient bound c_(p,q) <= x for nontrivial irreps bounds the rest of
the full Haar-space spectrum by x. Restriction to gauge-invariant functions
can only improve this separation. For complex t,

\[
\|T(t)-C\|\le e^{72|t|}-1.
\]

At r = 1/1000 the right side is less than (1-x)/2. The resolvent Neumann
series on the circle centered at 1 of radius (1-x)/2 therefore defines a
rank-one analytic eigenvalue lambda(t) throughout this disk. For real t it
is the actual Perron eigenvalue. Its first coefficients follow by solving
the eigenvalue equation order by order:

\[
\lambda(t)=1+\ell_2t^2+O(t^3),\qquad
\ell_2=\frac{6(1+\kappa)}{1-\kappa}
       =10.177503378886583385\ldots.
\]

Here T'(0)1 = (1+kappa)D/2, so its entire first-order nonvacuum part lies
in the known C-eigenspace of D. No unknown spatial integral enters this
perturbative normalization.

Consequently the actual Perron-normalized matrix coefficients are

\[
\widehat A_2=A_2-\ell_2A_0,\qquad
\widehat M_{2,2}=M_{2,2}-2\ell_2M_{2,0}.
\]

Write delta = exp(72r)-1. On the complex circle, the analytic continuation
of G^(-1/2) has norm at most (1-delta)^(-1/2), and |lambda(t)| is at least
1-delta. Thus

\[
\|\widehat A(t)\|\le K_A=e^{144r}/(1-\delta)^2,
\quad \|\widehat M_2(t)\|\le K_M=e^{216r}/(1-\delta)^3.
\]

These statements use the holomorphic products RHR and RJR at complex t;
they coincide with the physical compressions on the real axis. Cauchy's
coefficient estimate gives, after truncating at second order and for |t|<r,

\[
\|\mathrm{remainder}\|\le K\frac{(|t|/r)^3}{1-|t|/r}.
\]

For the full-Q residual use K = K_M + K_A^2. At the explicitly stated
anisotropic test point t = 10^(-12), these inequalities produce actual
outward numerical 2-by-2 matrices for normalized A, M2, and B*B, with a
strictly positive lower bound on the second diagonal entry of B*B. Their
common orthonormal basis Gram is exactly I. This is a reproducible physical
moment calculation, but only at that test point and in that small space.

The target 271/60 is outside this analytic certificate. Even the global
elementary bounds for the raw G,H,J second-order remainders there are about
9.79e147, 1.34e290, and 7.72e431. Those are valid, unusably wide error bounds.
The calculation therefore gives no numerical target-beta physical matrix.

Even on this two-dimensional space the missing target entries can be stated
as separate, concrete scalar contractions. Define the one-, two-, and
three-slice partition integrals

\[
Z_1(s)=\int e^{sD(U)}dU,
\quad Z_2(s_0,s_1)=\iint e^{s_0D(U)}k(U,V)e^{s_1D(V)}dU\,dV,
\]

\[
Z_3(s_0,s_1,s_2)=\iiint e^{s_0D(U)}k(U,V)e^{s_1D(V)}
k(V,Z)e^{s_2D(Z)}dU\,dV\,dZ.
\]

Then G consists of Z1, Z1'/sqrt(12), and Z1''/12; H consists of Z2 and
its two endpoint first derivatives and mixed derivative; J consists of Z3
and its endpoint derivatives with respect to s0 and s2. Evaluate all slice
parameters at the *same* target t. These contractions, with explicit error
bounds, are absent from the target-coupling numerical record. Their
definitions are fixed by the supplied geometry and Wilson operator; they
are additional calculations, not free fit parameters. The one-link
coefficient table alone is not a numerical evaluation of these interacting
spatial and multi-slice integrals.

## Why the complete retained matrix has not been executed

Six verified edge-disjoint plaquette loops partition the 24 links. Products
of their normalized characters form an orthonormal family. At box cutoff n
there are L_n = (n+1)(n+2)/2 irreps available per loop, hence L_n^6 linearly
independent gauge-invariant states. Every such contractible-loop product is
center-flux neutral. Multiplication by the positive invertible S preserves
linear independence and the symmetry sector.

This lower bound survives translation restriction up to a factor eight.
The original states have distinct electric link assignments. Each orbit of
assignments under the eight translations contains at most eight of them.
The translation average of a selected character product is nonzero: at the
identity configuration all its translated values equal a positive product
of representation dimensions. Averages from distinct assignment orbits
are orthogonal by Peter--Weyl orthogonality. Therefore the neutral,
zero-momentum rank is at least ceil(L_n^6/8).

At n = 248, already

\[
\dim\mathcal R_{248}\ge
909193161720279693603515625,
\]

and the neutral zero-momentum subspace has dimension at least
113649145215034961700439454. One dense real float64 matrix on the full
lower-bound dimension would need at least 6.613e54 bytes; even on the
neutral zero-momentum lower bound it needs at least 1.033e53 bytes.
This is a dense-storage lower bound, **not** a proof that symbolic,
matrix-free, tensor-network or differently retained approaches are
impossible. Such an approach must actually contract the spatial weights
with certified truncation and conditioning bounds before numerical full
matrices or their spectrum can be claimed.

## DAG consequence

The new closed nodes are exact geometric Haar moments through fourth order,
exact complete temporal spectral moments of D^2, same-operator normalized
physical Taylor matrices through second order, and a rigorously enclosed
small-coupling numerical construction test. The still-open target node is
the complete spatial G,H,J integration at t = 271/60, followed by its
Perron normalization and spectral estimates. No continuum or
volume-uniform conclusion follows from these local Taylor nodes.

Reproduce the exact and interval results in this order:

```
python proof_frontier_v13/moments/exact_spatial_jets.py
python proof_frontier_v13/moments/temporal_projector_moments.py
python proof_frontier_v13/moments/certify_physical_moment_jets.py
python proof_frontier_v13/moments/check_v9_spectral_weights.py
```

The last command is only the separately labeled historical-matrix
diagnostic; the first three commands generate the proof-bearing data.
