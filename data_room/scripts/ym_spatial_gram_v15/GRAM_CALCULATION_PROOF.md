# V15 spatial Gram calculation: exact contractions and scope

The requested full matrix is
\[
G=E_{292}^{*}W^2E_{292},\qquad
W(U)=\prod_{p=1}^{24}w(U_p),\qquad
w(g)=p_{233}\!\left({271\over240}(3+\chi_3(g)+\chi_{\bar3}(g))\right).
\]
Here E292 is a complete orthonormal gauge-invariant Peter–Weyl basis map with per-link cutoff p+q<=292. All intertwiner and momentum sectors must be retained unless an additional restriction is explicitly proved appropriate. V15 does **not** evaluate this full matrix. It calculates exact local Gram contractions, the entire squared plaquette weight, and an exactly contracted 729-state lower operator for a principal compression of G.

## Squared plaquette weight

Write gamma=271/240 and Y=3+chi3+chi3bar. The square required in G is not a truncation of an exponential at twice the degree. Its exact polynomial is
\[
w^2=\sum_{k=0}^{466} {\gamma^k\over k!}s_kY^k,
\qquad s_k=\sum_{j=\max(0,k-233)}^{\min(k,233)}\binom{k}{j}.
\]
This follows by collecting degrees in p233(gamma Y)^2. In particular the high-order coefficients must include the binomial partial sums sk; replacing them by 2^k for k>233 would be wrong.

The program evaluates this polynomial exactly in the SU(3) representation ring. Starting h=s466 and descending k=466,...,1, set h=s(k-1)+(gamma/k)Yh. Multiplication by Y uses three trivial copies and the fundamental/conjugate tensor rules. Each step uses integer numerators and one common positive denominator. Induction proves the resulting coefficients are exactly those of the displayed polynomial. Every irrep p+q<=466 occurs with positive coefficient, giving 109,278 coefficients. Evaluation at the identity is checked against the square of the original V14 factor. Conjugation symmetry is also checked exactly.

Let cr denote the computed character coefficient of w^2. Haar character orthogonality gives c0=integral(w^2). This value and the following local matrix are verified independently by multiplying the original V14 character vector by 1, chi3 and chi3bar and taking coefficient-vector dot products. This independent check covers all nine local matrix entries; it is not a second independent verification of every one of the 109,278 squared-factor coefficients.

## Fully contracted local Gram matrix

For the Haar-orthonormal character family (1,chi3,chi3bar), the matrix is
\[
K=\begin{pmatrix}a&b&b\\b&d&e\\b&e&d\end{pmatrix},\quad
a=c_0,\quad b=c_{(1,0)},\quad d=c_0+c_{(1,1)},\quad e=c_{(2,0)}+c_{(1,0)}.
\]
The identities chi3 chi3bar=1+chi8 and chi3^2=chi6+chi3bar, together with conjugation invariance of w, prove the formula. Equivalently Kij=<w phii,w phij>. Exact positive principal minors check positive definiteness. The three eigenvalues are d-e and
\[
{a+d+e\pm\sqrt{(a-d-e)^2+8b^2}\over2}.
\]
The supplied intervals use rational square-root enclosures constructed by integer square root, and outward decimal conversion; they are not ordinary floating-point eigenvalues.

## A contracted lower operator inside the full 24-plaquette problem

The supplied periodic two-site-per-direction geometry has 24 distinct positive-direction links and 24 action plaquettes. The recorded exact-cover search selects six plaquettes whose link sets partition all 24 links. Under product Haar measure their six holonomies are independent Haar variables, even where the plaquettes share vertices. Therefore products of the three characters above form a 729-element orthonormal family of gauge-invariant functions. They belong to the complete cutoff-292 retained space.

Let V map its standard basis to these 729 functions, and let
\[
G_{729}=V^*W^2V,\quad L=K^{\otimes6}.
\]
Because Y(g)=3+2 ReTr(g)>=0 for SU(3), each w(g)>=1. Dropping the other 18 plaquette factors yields a **quadratic-form lower bound**:
\[
G_{729}\succeq L.
\]
Indeed, for every coefficient vector z, the difference is the Haar integral of |Vz|^2 times the nonnegative function
\[
\prod_{p\in S}w(U_p)^2\left(\prod_{p\notin S}w(U_p)^2-1\right).
\]
Independence makes the remaining integral exactly K tensor six times. This is an operator inequality, **not entrywise ordering**. The entries of L must not be substituted for those of G729, and G729 itself is only a principal compression of the requested full G.

Every entry of L/a^6 has been evaluated exactly: it is a product of six factors chosen from 1,b/a,d/a,e/a. There are at most 84 multiplicity classes. GRAM_LOWER_729_CODES.bin.gz contains the 531,441 row-major unsigned-byte indices into the exact rational value table GRAM_LOWER_729_VALUES.json. Basis order is lexicographic over six-tuples in {0,1,2}^6. This is an exact compact matrix representation, not a tensor network whose contractions remain to be done. The **full** Gram contractions remain to be done.

In particular, the actual full Gram entry for the constant vector obeys G00>=a^6. The eigenvalue bounds reported for L/a^6 apply to this lower operator; they are not the spectrum of G, G729 or the Wilson transfer.

## Size and the missing contraction

At cutoff 292 there are (293*294)/2=43,071 irreps for each of the six edge-disjoint loops. Their character products are an orthonormal family, so the complete retained dimension is at least 43,071^6. These loops are contractible and center-flux neutral. Taking translations can identify at most eight link-assignment patterns; the invariant averages do not vanish since their values at the identity are positive. Distinct assignment orbits give orthogonal averaged functions. Thus the neutral zero-momentum subspace alone has dimension at least ceil(43,071^6/8).

The exact counts and dense float64 byte lower bound are in GEOMETRY_AND_DIMENSION.json. These prove that a dense calculation is infeasible in this execution environment. They do not rule out a successful matrix-free or rigorously compressed method.

The full weight is the product of all 24 squared factors. Adjacent plaquettes share links, so Haar integration does not factorize into 24 independent one-plaquette integrals. A full evaluation must contract these shared-link representation matrices and the external basis/intertwiner tensors. V15 has not performed that contraction, constructed the complete basis explicitly, or certified a compression error replacing it. Consequently the full spatial Gram, normalized physical matrices and spectral-gap DAG nodes stay open.
