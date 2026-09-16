# V14: polynomial Wilson transfer at the actual target coupling

This result removes the small-spatial-coupling restriction of the V13 approximation. It does **not** evaluate the full spatial Gram matrix, prove a volume-uniform physical spectral gap, or construct continuum Yang–Mills fields.

## Operator and positive shifts

Keep the supplied finite SU(3) lattice geometry and Wilson convention. There are E=24 spatial links and P=24 spatial plaquettes. Set beta=271/20 and t=beta/3=271/60. Let

\[
T=S C_\beta^{\otimes E}S,\qquad
S(U)=\prod_p e^{(\beta/6)\operatorname{ReTr}U_p},\qquad
C_\beta(g,h)=Z_\beta^{-1}e^{(\beta/3)\operatorname{ReTr}(gh^*)}.
\]

Haar measure has mass one. Work on the gauge-invariant Hilbert space. The spatial weight is gauge invariant and the temporal convolution commutes with gauge transformations. Its positive Perron eigenfunction is gauge invariant by simplicity, so the full-space kernel estimates below also apply to the physical restriction.

For SU(3), -3/2 <= ReTr(g) <= 3. The lower bound follows by writing the three eigenvalue phases with zero total phase: minimization of cos(a)+cos(b)+cos(a+b) gives -3/2. Define

\[
x_s(g)=\frac{\beta}{6}\left(\operatorname{ReTr}g+\frac32\right)
=\frac{271}{240}(3+\chi_3(g)+\chi_{\bar3}(g)),
\]
\[
x_t(g)=\frac{\beta}{3}\left(\operatorname{ReTr}g+\frac32\right)
=\frac{271}{120}(3+\chi_3(g)+\chi_{\bar3}(g)).
\]

Thus 0<=x_s<=3 beta/4=10.1625 and 0<=x_t<=3 beta/2=20.325. The shifts are constants, not a change of the Wilson coupling or action. Put p_n(x)=sum_{k=0}^n x^k/k! and define

\[
S_m=e^{-\beta P/4}\prod_p p_m(x_s(U_p)),\qquad
C_n(g,h)=Z_\beta^{-1}e^{-\beta/2}p_n(x_t(gh^*)),\qquad
\widetilde T=S_m C_n^{\otimes E}S_m.
\]

The exponentials and Z_beta here are scalar factors. They cancel from the Perron-normalized finite transfer; they need not be subtracted as nearly equal floating-point numbers.

## Uniform local relative error, valid at the target

For z>=0 and n+2>z, define

\[
\varepsilon_n(z)=
\frac{e^{-z}z^{n+1}}{(n+1)!\,[1-z/(n+2)]}.
\]

For 0<=x<=z,

\[
0\le 1-e^{-x}p_n(x)\le\varepsilon_n(z).
\]

Indeed the derivative of 1-e^{-x}p_n(x) is e^{-x}x^n/n!, so its maximum is at z. The remaining positive exponential series at z is bounded by its first term times a geometric sum with ratio z/(n+2). No analytic continuation from t=0 is used.

Write eps_s=epsilon_m(3 beta/4), eps_t=epsilon_n(3 beta/2), and suppose both are below one. For the **pointwise kernels**,

\[
(1-\varepsilon_s)^{2P}(1-\varepsilon_t)^E T(U,V)
\le\widetilde T(U,V)\le T(U,V).
\]

Therefore, with

\[
\delta=2P\varepsilon_s+E\varepsilon_t<1,
\]

we have |T(U,V)-Ttilde(U,V)|<=delta T(U,V), by the product union bound. Haar gauge averaging preserves these pointwise inequalities.

**Important distinction:** pointwise kernel order is not Loewner order. The spatial multiplication changes both ends of the transfer, and no claim Ttilde<=T in quadratic-form order is made.

## Positivity and normalization theorem

Each power of 3+chi3+chi3bar is a character of a representation with nonnegative integer multiplicities (three trivial summands plus the fundamental and conjugate). Hence C_n is a positive self-adjoint convolution. S_m is a strictly positive real multiplication operator. Ttilde is therefore positive self-adjoint, finite rank, and has a strictly positive continuous kernel.

Let lambda=||T|| and mu=||Ttilde|| be the Perron eigenvalues. For every f,

\[
|\langle f,(T-\widetilde T)f\rangle|
\le\delta\langle |f|,T|f|\rangle
\le\delta\lambda\|f\|^2.
\]

Self-adjointness gives ||T-Ttilde||<=delta lambda. Pointwise kernel order and the nonnegative Perron vector give

\[
(1-\delta)\lambda\le\mu\le\lambda.
\]

Consequently

\[
\boxed{\left\|T/\lambda-\widetilde T/\mu\right\|\le2\delta.}
\]

Proof: split the difference as (T-Ttilde)/lambda plus (1/lambda-1/mu)Ttilde. The first norm is at most delta; the second is (lambda-mu)/lambda, also at most delta.

Let Pi be the orthogonal projection onto the **full range** of Ttilde, and Q=I-Pi. Since Q Ttilde=Ttilde Q=0,

\[
\boxed{0\le Q(T/\lambda)Q\le\delta Q,\qquad
\|Q(T/\lambda)\Pi\|\le\delta,\qquad B^*B\le\delta^2 I.}
\]

These cover every external state, including omitted low-degree states. They hold for this explicitly revised range, not for the old P157 or any chosen subset. The sharper delta/2 crossing bound from a positive operator residual cannot simply be imported here; the residual of the spatially modified operator need not be positive.

For any single orthonormal basis U of this full range, the actual normalized physical moments and polynomial-transfer moments satisfy

\[
\|A-A_0\|\le2\delta,\qquad
\|M_2-A_0^2\|\le4\delta,\qquad
0\le M_2-A^2\le\delta^2I,
\]

where A=U*(T/lambda)U, M2=U*(T/lambda)^2 U, A0=U*(Ttilde/mu)U. The second estimate uses ||X²-Y²||<=2||X-Y|| for positive contractions. Thus all matrices refer to the same operator and basis. These are norm-error theorems; they are not a list of computed physical matrix entries.

## Executed values

The exact-rational scalar calculation selects spatial order m=233 and temporal order n=292. It obtains

\[
\delta<8.289795602707641\times10^{-222},\qquad
\|\widehat T-\widehat{\widetilde T}\|
<1.657959120541529\times10^{-221},
\]
\[
\|Q\widehat T\Pi\|<8.289795602707641\times10^{-222},\qquad
B^*B<6.872071113467094\times10^{-443}I.
\]

Both entire local character expansions were generated with exact integer numerators and shared denominators: 27,495 spatial coefficients and 43,071 temporal coefficients. The six SU(3) fundamental/conjugate fusion terms and three identity copies implement multiplication by 3+chi3+chi3bar. Horner's exact recurrence is h<-1+(gamma/k)(3+chi3+chi3bar)h for k=n,...,1. This proves by induction that the generated coefficients are those of p_n(gamma(3+chi3+chi3bar)). A separate Laurent-polynomial/Weyl-alternant calculation verifies the coefficients without using those fusion rules.

For arbitrary finite cubic volumes E=P=3L³, selecting m(E),n(E) with 2[2P eps_s+E eps_t]<=epsilon gives a common approximation error epsilon. The finite range, basis dimension, and polynomial orders depend on volume. This is an approximation theorem, not a physical gap theorem.

## Exact finite matrix prescribed, but not contracted

Let E_n denote an orthonormal basis map for the complete per-link p+q<=n gauge-invariant Peter–Weyl box, retaining every intertwiner, momentum and flux sector. Every temporal irrep in that box has a strictly positive coefficient; no higher irrep occurs. Thus

\[
\operatorname{range}\widetilde T=S_m\operatorname{range}E_n.
\]

Remove the common scalar from S_m and write W=product_p p_m(x_s(U_p)). Then W>=1 pointwise. Let K be the temporal tensor-product diagonal, with each one-link eigenvalue equal to its character coefficient divided by the representation dimension. After dropping a common positive scalar,

\[
\widetilde T=F K F^*,\quad F=WE_n,\quad
G=E_n^*W^2E_n,\quad U=FG^{-1/2},
\]
\[
R=G^{1/2}KG^{1/2},\quad
A_0=R/\lambda_{\max}(R),\quad M_{2,0}=A_0^2.
\]

This gives a finite algebraic prescription at the **actual target coupling**. Every Gram entry is a finite polynomial Haar integral; SU(3) invariant tensor contraction evaluates it in principle. G>=I, so there is no exact rank ambiguity once E_n is correctly orthonormal. This does not make the contractions small or numerically well-conditioned: ||G|| can be as large as p_m(3 beta/4)^(2P). We have generated K's local factors, not the full spatial G, R, its Perron vector, or its spectrum. The earlier huge retained-dimension obstruction remains; degree 292 is larger than degree 248. Symbolic prescription must not be labeled numerical execution.

## Why the other two obligations remain open

The inherited finite-volume gap floor 2/(exp(3 beta E/2)+1) still has zero infimum over volumes. Making approximation error smaller than that floor does not improve its volume dependence. Even an exactly represented family diag(1,1-1/L) has zero approximation error and gaps tending to zero. Thus there is no valid implication from this uniform approximation theorem to a uniform physical gap.

The fixed-cutoff DLR/reflection-positive limits proved in V13 do not specify a tuned beta(a) trajectory, construct renormalized continuum observables, establish continuous Euclidean covariance, or prove a common physical-time decay exponent on a dense limiting core. Those are still inputs needed for the continuum and spectral reconstruction arrows. No new proof of those inputs is obtained here.

**Status:** target-coupling spatial/temporal polynomial approximation and its complete external-error theorem are established; full numerical target matrix contractions, volume-uniform physical mass gap, and continuum construction remain unproved.
