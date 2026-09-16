# A nonzero neutral local observable for the actual finite Wilson transfer

This result identifies a genuine connected observable in the **fixed finite
Wilson theory** and proves its nonzero variance and exponential time
clustering. It does not identify a continuum field, compute its mass, or
identify the lowest excitation of the neutral sector. The exact Perron
function is used through its defining equation; its numerical coordinates
are not assumed available.

## 1. Operator and observable

Use the V11 operator on normalized product Haar measure on
`X=SU(3)^24`, at `beta=271/20`:

\[
 T(U,V)=s(U)k(U,V)s(V),\qquad
 s(U)=e^{\beta D(U)/6},\qquad
 D(U)=\sum_{p=1}^{24}\operatorname{ReTr}U_p,
\]
\[
 k(U,V)=Z_\beta^{-24}
 e^{(\beta/3)\sum_e\operatorname{ReTr}(U_eV_e^*)}.
\]

The continuous strictly positive kernel has a simple positive largest
eigenvalue `lambda_0` and continuous strictly positive unit eigenfunction
`phi`. The character expansion of each temporal exponential has strictly
positive coefficients for every SU(3) irrep: each irrep `(p,q)` appears in
`(3+3bar)^(p+q)`, with a positive term in the exponential series. Thus the
convolution is positive and injective. Multiplication by `s` is bounded
and boundedly invertible, so `T` is also positive and injective. These facts
apply to the gauge-invariant restriction as well.

Let `O(U)=ReTr U_(p0)` for the elementary `(mu,nu)=(0,1)` plaquette
based at vertex zero. Index a positive link by `e=3*v+mu`, with its target
vertex `v xor (1<<(2-mu))`. The loop's ordered link indices are
`(0,13,6,1)` with orientations `(+1,+1,-1,-1)`. This is the reverse
orientation of the V11 pinned plaquette zero, up to cyclic ordering, so
its real trace is identical. The script constructs all 24 elementary
plaquettes directly from the periodic `2^3` cubic lattice and checks that
they are closed loops
with four distinct links, and that every link belongs to four plaquettes.

Under a vertex gauge transformation, a closed plaquette holonomy changes
by conjugation. Therefore `O` is gauge invariant. Multiplying the links
crossing any one of the three spatial periodic dual cuts by
`z=exp(2 pi i/3)` multiplies the plaquette by `z` to the signed number of
cut crossings. This number is zero for every plaquette and every cut,
as the script checks exactly. Hence `O` has neutral electric center flux.

Simultaneously applying a gauge transformation or a center cut to `U,V`
leaves `T(U,V)` invariant. The normalized positive Perron function is
therefore invariant under these transformations, by simplicity. Define

\[
 d\pi(U)=\phi(U)^2dU,\qquad
 m=\int O\,d\pi,\qquad
 \psi=(O-m)\phi.
\]

Then `psi` is gauge invariant, center neutral and orthogonal to the
vacuum. It is a local plaquette excitation before centering; it is not a
projection to zero momentum. The argument below proves `psi != 0`.

## 2. An explicit local Perron-density comparison

Fix every link except one chosen link `e` of `p0`, and compare two values
`U_e,U'_e`. Write `U,U'` for the full resulting configurations. The SU(3)
trace range is `[-3/2,3]`. Changing one link can change each of its four
incident plaquette traces by at most `9/2`, so

\[
 |\log s(U)-\log s(U')|
 \le\frac\beta6\,4\,\frac92=3\beta.
\]

For every `V`, only one temporal factor changes. Hence

\[
 e^{-3\beta/2}\le\frac{k(U,V)}{k(U',V)}
 \le e^{3\beta/2}.
\]

The Perron equation, with a positive integrand, now gives

\[
 \frac{\phi(U)}{\phi(U')}
 =\frac{s(U)}{s(U')}
 \frac{\int k(U,V)s(V)\phi(V)dV}
      {\int k(U',V)s(V)\phi(V)dV}
 \in[e^{-9\beta/2},e^{9\beta/2}].
\]

For fixed remaining links `u`, the conditional density of `U_e` under
`pi` is

\[
 \rho_u(g)=\frac{\phi(g,u)^2}{\int\phi(h,u)^2dh}.
\]

The ratio of any two numerator values is at most `exp(9 beta)`. Integrating
the corresponding inequality over `h` proves the uniform conditional
comparison

\[
 \boxed{e^{-9\beta}\le\rho_u(g)\le e^{9\beta}}
\]

for every fixed `u,g`. This uses the true Perron function of the actual
Wilson operator, with no trial-state substitution and no temporal cutoff.

## 3. Exact Haar variance and a nonzero physical state

For fixed other links, the plaquette holonomy has the form `A g B` or
`A g^* B`, with fixed SU(3) matrices `A,B`. Under Haar-distributed `g` it
is Haar-distributed. For Haar `h` in SU(3), center invariance gives

\[
 \int\operatorname{Tr}h\,dh=0,\qquad
 \int(\operatorname{Tr}h)^2dh=0.
\]

Indeed multiplication by `zI` multiplies the two integrals by `z` and
`z^2`, respectively. Schur orthogonality gives

\[
 \int|\operatorname{Tr}h|^2dh
 =\sum_{i,j}\frac{\delta_{ij}}3=1.
\]

Expanding the square of the real part consequently gives

\[
 \operatorname{Var}_{\mathrm{Haar}}(\operatorname{ReTr}h)=\frac12.
\]

For each conditional distribution and any real constant `a`, the density
comparison implies

\[
 \int(O-a)^2\rho_u\,dg\ge e^{-9\beta}\int(O-a)^2dg.
\]

Taking the infimum over `a` and then using total variance proves

\[
 \boxed{\|\psi\|^2=\operatorname{Var}_{\pi}(O)
 \ge\frac12e^{-9\beta}>0.}
\]

The opposite universal bound follows from the observable's range:

\[
 \operatorname{Var}_{\pi}(O)\le\frac{(3+3/2)^2}{4}=\frac{81}{16}.
\]

The lower bound remains valid at fixed beta on other cubic spatial volumes
with the same four-plaquette incidence and with a plaquette containing a
link exactly once. It tends to zero as beta tends to infinity. This fact
does not imply continuum nontriviality or a volume-uniform spectral gap.

## 4. Exact finite Wilson time correlations

The Perron Doob transition kernel is

\[
 P(U,dV)=\frac{T(U,V)\phi(V)}{\lambda_0\phi(U)}dV.
\]

The Perron equation makes it Markov. Symmetry of `T` gives detailed balance
with `pi`, so `pi` is stationary. Its finite path distribution is exactly

\[
 d\pi(U_0)\prod_{j=0}^{n-1}P(U_j,dU_{j+1})
 =\frac{\phi(U_0)\phi(U_n)}{\lambda_0^n}
   \prod_{j=0}^{n-1}T(U_j,U_{j+1})\prod_{j=0}^n dU_j.
\]

Inserting the specified kernel, its exponent has the Wilson temporal
plaquette term on each step, the full spatial term `(beta/3)D` on each
interior slice, and half spatial terms on its two boundaries. The endpoint
weights are the exact Perron boundary functions. This identifies the
correlations as vacuum correlations of the same finite Wilson transfer;
no affine logarithmic operator is used.

Writing `T_hat=T/lambda_0`, the connected plaquette correlation at integer
time separation is therefore

\[
 C(n)=\mathbb E_\pi[(O(U_0)-m)(O(U_n)-m)]
     =\langle\psi,\widehat T^{\,n}\psi\rangle.
\]

The direct contraction proof in `../design/` establishes on the entire
nonvacuum Hilbert space

\[
 0\le\widehat T|_{\phi^\perp}\le(1-\delta)I,
 \qquad \delta=\frac{2}{e^{3\beta E/2}+1},\quad E=24.
\]

Thus for every integer `n>=0`,

\[
 \boxed{0\le C(n)\le\operatorname{Var}_\pi(O)(1-\delta)^n
 \le\frac{81}{16}e^{-\delta n}.}
\]

Injectivity and positivity of `T`, together with `psi != 0`, strengthen
the first inequality to strict positivity for every finite `n`. In
spectral terms the nonzero positive measure of `psi` has support in
`(0,1-delta]` in transfer-eigenvalue coordinates. This identifies a
nonempty neutral physical spectral channel. It does not identify its
lowest energy, its overlap with a particular eigenvector, or a scalar
glueball mass.

Summing the geometric upper bound also gives finite quantities

\[
 \tau_{\rm int}=1+2\sum_{n\ge1}\frac{C(n)}{C(0)}
 \le\frac2\delta-1=e^{3\beta E/2},
\]
\[
 \chi_{\rm time}=C(0)+2\sum_{n\ge1}C(n)
 \le\frac{81}{16}e^{3\beta E/2}.
\]

These very weak constants are bounds, not numerical estimates of the
physical variance, spectrum or autocorrelation time.

## 5. Reproduction and remaining identification obligations

Run `python wilson_closeout_v12/physical/certify_neutral_channel.py`.
The certificate contains the exact geometry tests, rational Haar moments,
directed enclosures for the exponential constants and source hashes.
The code verifies the constants supporting the proof; it does not replace
the operator arguments or materialize the true Perron vector.

The independent command
`python wilson_closeout_v12/physical/verify_neutral_constants_exact.py`
checks the exponential enclosures using exact rational Taylor sums at
their full arguments, with a geometric remainder. It imports none of the
directed interval implementation. The separate geometry reference audit
checks that every generated plaquette agrees with the V11 binary geometry
up to cyclic ordering and reversal, both of which preserve its real trace.

The closed statement is finite-volume physical identification of this
neutral nonzero local observable and its true same-operator time
correlation. Still open are numerical physical moment arrays, a sharp
neutral gap, a gap uniform along a continuum scaling trajectory,
renormalized field identification, continuum correlation-function limits,
continuum nontriviality and the remaining continuum axioms. Integer
transfer time here has not been assigned a physical lattice spacing.
