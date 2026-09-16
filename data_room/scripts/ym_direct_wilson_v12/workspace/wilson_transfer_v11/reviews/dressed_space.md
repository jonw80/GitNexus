# A complete dressed retained space for the finite Wilson transfer

This note proves a replacement for a coordinate-catalog complement argument.
The replacement includes every electric label and every intertwiner below its
cutoff, in all translation momenta and electric-flux sectors. It concerns the
actual transfer operator, not the additive operator `a D + log C`.

**Execution boundary.** The definitions and estimates below are exact
mathematical constructions. A cutoff and a scalar error bound can be evaluated
without constructing their enormous matrices. This note does not assert that
all matrix entries at a large cutoff have been generated. In particular,
`A_m`, the exactly defined finite-rank surrogate, is not relabeled as the exact
compression `A` of the full transfer.

## 1. Operator and complete electric cutoff

Work in the full gauge-invariant subspace of normalized Haar
`L2(SU(3)^24)`. There are 24 spatial plaquettes and

\[
 \beta=271/20,\quad a=\beta/3=271/60,\quad
 D=\sum_{p=1}^{24}\operatorname{Re}\operatorname{Tr}U_p,
 \quad S=M_{\exp(aD/2)},\quad W=S^2=M_{\exp(aD)}.
\]

The normalized one-link Wilson convolution has Fourier eigenvalues
`c_(p,q)>0`, with `c_(0,0)=1`; `C` is the tensor product of its 24 copies.
The genuine transfer is

\[
 T=SCS.
\]

Since `-36 <= D <=72`,

\[
 e^{-162.6}I\le W\le e^{325.2}I.
\]

Let `E_m` be the orthogonal projector onto **all** gauge-invariant spin
networks with

\[
 \sum_{e=1}^{24}(p_e+q_e)\le m.
\]

An exact finite enumeration is: list every 24-tuple of nonnegative Dynkin
labels satisfying this inequality, and for each tuple retain an orthonormal
basis of the full invariant-tensor space at each of the eight vertices.
Contract these tensors against normalized link matrix coefficients. No
translation averaging or catalog filtering is part of this definition.

To verify completeness, linkwise Peter--Weyl orthogonality makes normalized
matrix coefficients orthonormal; their tensor products form a complete
orthonormal basis of the product Haar space. Gauge averaging projects the
vertex index spaces precisely onto their invariant-tensor spaces. Thus all
the stated invariant tensors, and only those, span the specified electric
subspace. For fixed `m` the number of labels and the tensor dimensions are
finite. This also proves that the union of these subspaces is dense.

Electric degree is preserved by gauge transformations, translations and the
Wilson convolution, so `E_m` commutes with `C`. The cutoff includes every
translation momentum; it does not repeat the V9 restriction to translation
orbit sums. Write `Q_e=I-E_m`.

Suppose a certified number `tau_m` satisfies

\[
 0\le Q_e C Q_e\le\tau_m Q_e.
\]

It is sufficient to bound the maximum of
`product_e c_(p_e,q_e)` over **all** link assignments whose total degree is at
least `m+1`; ignoring the gauge constraint only enlarges this maximum. The
V10 all-irrep theorem gives the readily available bound

\[
 \tau_m\le\rho^{m+1},\qquad
 \rho=0.7128552093544991687\ldots.
\]

A sharper convolution bound on all 24 link degrees may replace this bound
without changing any proof below.

## 2. Retain the spatially dressed electric modes

Let `e_i` be the complete orthonormal basis of `range(E_m)`, and define

\[
 F e_i=S e_i,\qquad G=F^*F=E_mWE_m,
 \qquad U=F G^{-1/2}.
\]

All inverse square roots here are the unique positive inverse square roots.
The uniform lower bound on `W` gives

\[
 e^{-162.6}I\le G\le e^{325.2}I,
 \quad U^*U=I.
\]

The revised retained space and its orthogonal projector are

\[
 \mathcal R_m=S\operatorname{range}(E_m),\qquad
 P_m=UU^*=F G^{-1}F^*,\quad Q_m=I-P_m.
\]

This is a finite-dimensional subspace even though the individual vectors
`S e_i` have infinite electric expansions. The displayed exact formula, not a
truncated exponential of a finite plaquette matrix, defines them.

Define the finite-rank transfer and its residual by

\[
 T_m=S E_m C E_m S,\qquad
 \Delta_m=T-T_m=S Q_e C Q_e S.
\]

Both terms are positive, and `range(T_m)=range(P_m)`. The range equality
follows because `C` is strictly positive on the finite electric space and
`G` is invertible. In particular

\[
 0\le\Delta_m\le\delta_m I,\qquad
 \delta_m=e^{325.2}\tau_m.
\]

The possible very large number `delta_m` is a real limitation at low cutoffs,
not a reason to discard the spatial dressing factor.

## 3. The entire external complement and the crossings

Because `Q_m T_m=0=T_m Q_m`,

\[
 Q_m T Q_m=Q_m\Delta_m Q_m,
 \qquad 0\le Q_mTQ_m\le\delta_m Q_m.
\]

This estimate includes **every** omitted low-degree state, every higher
degree, every multiplicity and every momentum. It depends on completeness of
`E_m`, not on any claim that the old V9 catalog happened to exhaust a degree
range. Notice that `Q_m` and `Q_e` are different projectors.

In the certified orthonormal retained basis define

\[
A=U^*TU,\quad A_m=U^*T_mU=G^{1/2}C_mG^{1/2},
 \quad C_m=E_mCE_m,
\]
\[
 D_m=A-A_m=U^*\Delta_mU,\qquad B=Q_mTU=Q_m\Delta_mU.
\]

For the surrogate eigenvalues one may instead use the finite matrix

\[
 K_m=C_m^{1/2}G C_m^{1/2}.
\]

It has the same eigenvalues as `A_m`: these are `XX*` and `X*X` for
`X=G^(1/2) C_m^(1/2)`. This alternative needs only diagonal square roots of
the known electric eigenvalues, and avoids first forming `G^(1/2)`. It does
not change the required full group integral for `G` or provide an automatic
condition-number certificate.

Since `0<=Delta_m<=delta_m I`, spectral calculus gives
`Delta_m^2<=delta_m Delta_m`. Therefore

\[
 \begin{split}
 B^*B
 &=U^*\Delta_m^2U-D_m^2\\
 &\le\delta_mD_m-D_m^2
 \le\frac{\delta_m^2}{4}I.
 \end{split}
\]

Thus the crossing bound improves the elementary `||B||<=delta_m` to

\[
 \boxed{\|B\|\le\delta_m/2}.
\]

The reverse crossing is exactly `B^*=U^*TQ_m`, since the actual transfer is
self-adjoint. This proves an identity; independent forward and reverse
numerical evaluation remains necessary if numerical crossing data are claimed.

If desired, enlarge the retained space further by adding the old V9
coordinates and the explicit V10 obstruction polynomial. The same complement
and crossing estimates hold for **any** orthogonal projector `P>=P_m`, because
`T_m` still has no crossing to its complement. Use an independent basis for
the enlarged span, or quotient the kernel of its Gram matrix. Merely adding
one old obstruction vector without the complete dressed cutoff gives no such
tail theorem.

## 4. Exact same-operator moments from independent integrals

The following three finite matrices are separately defined by actual group
integrals:

\[
 G=E_mWE_m,\qquad H=E_mWCWE_m,\qquad
 J=E_mWCWCWE_m.
\]

For example, with `k(U,V)` the normalized temporal kernel,

\[
 G_{ij}=\int\overline{e_i(U)}W(U)e_j(U)\,dU,
\]
\[
 H_{ij}=\iint\overline{e_i(U)}W(U)k(U,V)W(V)e_j(V)\,dU\,dV,
\]
\[
 J_{ij}=\iiint\overline{e_i(U)}W(U)k(U,V)W(V)
       k(V,Z)W(Z)e_j(Z)\,dU\,dV\,dZ.
\]

Fubini applies: each integrand is continuous on a compact domain. Direct
multiplication of `T=SCS` now proves

\[
 \boxed{A=G^{-1/2}HG^{-1/2}},\qquad
 \boxed{M_2=U^*T^2U=G^{-1/2}JG^{-1/2}},
\]
\[
 \boxed{B^*B=M_2-A^2}.
\]

In particular `J` is an independent second-action integral; it is not defined
by imposing the residual identity. These formulas include all intermediate
electric states through the full operator `C` and the full multiplication
operator `W`. Inserting `E_m` between the factors of `H` or `J` changes the
physical moment and is not permitted without a remainder estimate.

An explicit crossing formula in the same basis is

\[
 B=(I-FG^{-1}F^*)S Q_e C Q_e W E_mG^{-1/2}.
\]

Consequently every displayed moment and both crossing directions belongs to
one and the same operator and one orthonormal basis. This resolves the
**mathematical definition** of the common basis; it does not claim that large
matrices `G,H,J` have been integrated in this run.

## 5. True Perron normalization and certified spectral consequences

Let `lambda_0=||T||` and `lambda_m=||T_m||`. By positivity and the residual
estimate,

\[
 \lambda_m\le\lambda_0\le\lambda_m+\delta_m.
\]

Since the degree-zero constant vector is retained and `C_m` contains its
unit eigenvalue,

\[
 T_m\ge |s\rangle\langle s|,\quad
 s=e^{aD/2},\quad
 \lambda_m\ge Z_{\rm sp}:=\int e^{aD}\,dU.
\]

Any rigorously evaluated lower bound `L_sp<=Z_sp` therefore bounds both
`lambda_m` and `lambda_0` below. This is substantially better than relying
only on `Z_sp>=1` when an explicit partition-function lower bound is
available.

More generally, let `L>0` be **any** certified lower bound on the true
`lambda_0`, such as an independently proved slab variational bound. This is
enough for every normalized error estimate below. Such a bound need not be a
lower bound on `Z_sp` or `lambda_m`; only
`lambda_m>=max(Z_sp,L-delta_m)` follows in general. In particular the new
slab lower bound must not silently be used as a lower bound for the finite
surrogate eigenvalue.

The actual normalized Wilson transfer is `T_hat=T/lambda_0`. It has norm
one. Its full external compression and crossing satisfy

\[
 0\le Q_m\widehat TQ_m\le(\delta_m/L)Q_m,
 \quad\|Q_m\widehat TU\|\le\delta_m/(2L).
\]

There is also a factor-one normalized approximation estimate. Put
`d=lambda_0-lambda_m`, so `0<=d<=delta_m`. Then

\[
 \frac{T}{\lambda_0}-\frac{T_m}{\lambda_m}
 =\frac{\Delta_m}{\lambda_0}
 -\frac{dT_m}{\lambda_0\lambda_m}.
\]

The two positive terms on the right are each bounded above by
`delta_m/lambda_0 I`. Their difference consequently lies between
`-delta_m/lambda_0 I` and `+delta_m/lambda_0 I`. Hence

\[
 \boxed{\left\|\frac{T}{\lambda_0}
       -\frac{T_m}{\lambda_m}\right\|
       \le\frac{\delta_m}{\lambda_0}\le\frac{\delta_m}{L}}.
\]

This estimate does not require an explicitly computed true Perron vector.
However, the normalized finite matrix itself still requires `G` and
`lambda_m` to be evaluated before a numerical approximation is claimed.

Write `mu_j` for the ordered eigenvalues of `T_m`, with zeros appended, and
`lambda_j` for the ordered eigenvalues of `T`. The variational eigenvalue
principle gives, for every `j`,

\[
 \mu_j\le\lambda_j\le\mu_j+\delta_m,
 \qquad
 \frac{\mu_j}{\mu_0+\delta_m}
 \le\frac{\lambda_j}{\lambda_0}
 \le\frac{\mu_j+\delta_m}{\mu_0}.
\]

If actual enclosures prove `mu_1+delta_m<mu_0`, then the physical logarithmic
transfer gap is at least

\[
 \log\frac{\mu_0}{\mu_1+\delta_m}>0.
\]

Without those eigenvalue enclosures a small tail does **not** itself certify
the desired gap. The earlier finite-volume Doob lower bound remains a
separate valid baseline.

For normalized physical moments use `A_hat=A/lambda_0` and
`M2_hat=M2/lambda_0^2`. Besides the crossing bounds above, positivity and
`0<=T_hat<=I` imply

\[
 A_{\rm hat}^2\le M_{2,\rm hat}\le A_{\rm hat},
 \qquad 0\le B_{\rm hat}^*B_{\rm hat}
          \le A_{\rm hat}-A_{\rm hat}^2.
\]

These are useful independent consistency checks on any eventual interval
matrix integration.

## 6. Elementary six-loop normalization baseline

The verified edge-disjoint plaquettes `[0,7,9,13,19,22]` partition all 24
links. Their holonomies are independent Haar variables. Let `D_pack` be
their six-plaquette sum and `D_rest` the other 18 plaquettes, and define the
probability density proportional to `exp(a D_pack)`.

Every unselected plaquette has a proper nonempty intersection with a packed
loop. Pick one shared link and one unshared link of that loop. Multiply their
link matrices by center phases chosen to preserve the oriented packed
holonomy. The packed weight and Haar measure are unchanged, whereas the
trace of the unselected plaquette is multiplied by a nontrivial cube root of
unity. Its expectation is therefore zero. Thus `E_pack D_rest=0`.

Writing `Z_beta=int_SU(3) exp((beta/3) ReTr U) dU`, Jensen's inequality gives

\[
 Z_{\rm sp}=Z_\beta^6
     \mathbb E_{\rm pack}e^{aD_{\rm rest}}
     \ge Z_\beta^6.
\]

This proof does not assume that arbitrary spin-foam coefficients have a
positive sign. A gauge-fixed product-measure variational estimate can improve
this lower bound; the companion V11 normalization calculation handles that
evaluation separately.

## 7. Scope that remains open

The retained space has been revised by an exact complete prescription, and
the positive finite-rank Wilson approximation has a rigorous full-space
remainder. The use of `S E_m`, as opposed to an incomplete coordinate catalog,
is what makes the external bound valid for omitted low degrees as well.

The finite matrix integrals, their interval conditioning, useful physical
eigenvalue separation, volume-uniform estimates, continuum Schwinger
functions, nontriviality and physical continuum identification are additional
obligations. None is supplied merely by choosing a very large formal cutoff.
