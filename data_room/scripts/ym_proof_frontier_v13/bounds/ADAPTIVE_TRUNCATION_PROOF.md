# A volume-uniform approximation bound and its exact limitation

This advances the direct Wilson branch of the DAG. It proves a uniform
**operator approximation error** using a cutoff that grows with volume.
It does not prove a volume-uniform physical spectral gap or continuum limit.

Let E be the number of spatial links, beta>0 fixed, C_beta the normalized
Wilson convolution, S the exact positive spatial multiplication operator,
and T=S C_beta^tensor(E) S. Write p_n(x)=sum_{j=0}^n x^j/j!,
and use the true one-link partition Z_beta when defining C_n by p_n/Z_beta.
Every character coefficient is nonnegative and 0<=C_n<=C_beta. The complete
finite approximation is T_n=S C_n^tensor(E) S, with Perron eigenvalues
lambda_0 and mu_0 respectively. Take n sufficiently large for p_n>0 over
[-beta/2,beta]. Its range is the complete dressed space S E_box,n H_GI;
the box contains every irrep of degree p+q<=n on each link, every gauge
intertwiner and every momentum.

An explicit one-link relative-error upper bound is

\[
\epsilon_n=\max\left\{
 \frac{e^{-\beta}\beta^{n+1}}{(n+1)![1-\beta/(n+2)]},
 \frac{e^{\beta/2}(\beta/2)^{n+1}}{(n+1)!}\right\},
 \qquad n+2>\beta.
\]

For nonnegative arguments the relative exponential tail increases to its
endpoint at beta; for negative arguments the integral Taylor remainder
gives the second bound. The product kernel therefore has relative error
at most eta=(1+epsilon_n)^E-1. Exactly as in the V11 positive-residual
proof, for every f,

\[
0\le\langle f,(T-T_n)f\rangle
 \le\eta\langle |f|,T|f|\rangle
 \le\eta\lambda_0\|f\|^2.
\]

This does not require a numerical vacuum, and the possibly very large S
norm never enters the bound. If D=T-T_n and d=lambda_0-mu_0, then
0<=D<=eta lambda_0 I and 0<=d<=eta lambda_0. Thus

\[
 \frac{T}{\lambda_0}-\frac{T_n}{\mu_0}
 =\frac D{\lambda_0}-\frac{dT_n}{\lambda_0\mu_0}
\]

is a difference of two positive operators each bounded above by eta I.
Its norm is at most eta. If P is the orthogonal projection onto range(T_n)
and Q=I-P, then Q T_hat Q<=eta Q. Moreover the off-diagonal block of a
positive operator between 0 and eta I has norm at most eta/2: subtracting
(eta/2)I leaves a self-adjoint operator of norm at most eta/2 and preserves
that block. Hence ||Q T_hat P||<=eta/2 and B*B<=eta^2 I/4.

For 0<=x<=1/2, e^x-1<=2x (the convex function e^x lies below its endpoint
chord, whose slope is 2(e^(1/2)-1)<2). It follows that if

\[
2E\epsilon_n\le\varepsilon\le1,
\]

then eta<=[exp(E epsilon_n)-1]<=2 E epsilon_n<=varepsilon. At every finite
volume, such an n exists because factorial tails tend to zero. Therefore
the selection rule defines a family of complete approximations with one
uniform error constant over all finite volumes. The dimensions and chosen
cutoffs are not uniform. This is a valid forward implication; it does not
manufacture a uniform spectral separation of T_n.

The accompanying exact-rational script executes this rule for spatial
sides 2 through 1024, E=3L^3, beta=271/20 and error target 10^-12. It bounds
the necessary exponentials by positive rational Taylor sums plus explicit
geometric tails. It never subtracts a tiny error from a decimal one.

## Why one fixed polynomial order cannot give the same pointwise control

Consider an even fixed n, including V11's 72 and V12's 248. Put
r_+=p_n(beta)e^-beta<1 and r_-=p_n(-beta/2)e^(beta/2)>1, the latter by
the signed Taylor remainder. For the spatially dressed product kernels,
both ratios r_+^E and r_-^E occur: choose U_e V_e^*=I or a nontrivial
central SU(3) element on every link. The common positive spatial factors
cancel. Any scalar renormalization c>0 consequently has worst-case
pointwise relative error at least

\[
\min_{c>0}\max\{|c r_+^E-1|,|c r_-^E-1|\}
=\frac{(r_-/r_+)^E-1}{(r_-/r_+)^E+1}.
\]

The minimizer is c=2/(r_+^E+r_-^E), obtained by balancing the endpoint
errors. Since r_-/r_+>1, this obstruction tends to one as E tends to infinity.
It applies even if the scalar is the exact Perron-normalization ratio.
It is a pointwise relative-kernel obstruction, not a lower bound on the
normalized operator-norm error or a counterexample to a possible physical
mass gap.
The pointwise obstruction concerns the explicit kernel on the full product
group before gauge averaging. It does not assert the same lower bound for
the separately gauge-averaged kernel representing the physical restriction.

For an explicit rational witness, let
rho_lower=beta^(n+1)/[(n+1)! U_beta], where U_beta is an upper bound for
e^beta. Then 1-r_+>=rho_lower>0 and
log(r_-/r_+)>=-log(r_+)>=rho_lower. Whenever E rho_lower>=1, the displayed
error is greater than (e-1)/(e+1)>1/3. The script computes a finite cubic
volume with this property for each of n=72,248. These enormous volumes
exhibit failure of the proposed uniform inference; no large lattice is
numerically assembled.

## Outgoing DAG arrows

The adaptive construction closes the approximation-error uniformity node
for this volume-dependent family. It leaves open a useful retained spectral
gap, efficient spatial integration, H5 matched trajectory, H6 clustering
and the H7 continuum construction. The direct contraction gap
2/[exp(3 beta E/2)+1] still tends to zero with volume. Uniform approximation
of operators whose gaps have not been bounded uniformly does not supply
the missing uniform gap.
