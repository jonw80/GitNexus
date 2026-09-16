# Independent audit: what certifies a compressed full spatial Gram contraction

Scope: finite periodic SU(3) geometry, 24 links and 24 plaquettes, spatial order 233 and complete temporal cutoff 292. This is a mathematical audit of V14/V15. It does not assert execution of the remaining coupled Haar integrations.

## 1. The full object and its unavoidable rank

Let E:C^D -> L²(G^24) be the specified complete orthonormal physical Peter–Weyl basis map. Let W=product_p p233(x_s(U_p)), and set M=sup W. Then

G=E*W²E, and I <= G <= M² I.

Proof: integrate |Ez|² against 1 <= W² <= M². Here M=p233(10.1625)^24; equality at all identity links gives the supremum. Shared plaquette links cause no problem for this supremum, but prevent factorization of Haar integrals.

For every linear matrix Gc of rank r<D, ||G-Gc|| >= 1: choose a unit vector z in ker Gc; ||(G-Gc)z||=||Gz||>=1. If a compressed operator is represented only on a strict subspace and extended by zero, the same obstruction applies. Thus an absolute full-Gram error below one cannot be achieved by a genuinely lower-rank Gram approximation. This does not prohibit a compact full-rank tensor representation or a representation I+L with low-rank L; their error still requires proof.

A quadrature/Monte Carlo Gram estimate using s<D point evaluations has rank <=s and therefore obeys the same obstruction for every realization. A low-rank empirical covariance cannot be silently promoted to a certified complete Gram matrix.

## 2. Correct target for spectral compression

Let K be the strictly positive temporal diagonal on the complete retained basis. Define

H=K^(1/2) G K^(1/2), R=G^(1/2) K G^(1/2).

Both have the same eigenvalues with multiplicity. Indeed, for X=G^(1/2)K^(1/2), R=XX* and H=X*X, and X is invertible. This replacement avoids forming G^(1/2) and preserves all finite transfer eigenvalues. It does not identify the same coordinate matrices for physical moment vectors: the relevant change of orthonormal basis is the unitary in the polar decomposition of X and must be accounted for if entries or vacuum overlaps are reported.

For an orthogonal coordinate projector P commuting with K, write Q=I-P and

H = [[A, B*], [B, C]].

Every omitted coordinate, including all its physical intertwiners and all sectors, must be in Q. Set k_Q=max diagonal(K|Q), q=M² k_Q. Then

0 <= C <= q I.

Proof: QHQ <= M² QKQ. This is a complete omitted-space estimate, valid without entrywise integration in Q, albeit potentially extremely weak.

If ||A||<=a, positivity of H gives ||B||<=sqrt(a q). To prove it, positivity of the two-dimensional compression to x in P,y in Q gives |<y,Bx>|² <= <x,Ax><y,Cy>. Taking unit-vector suprema proves the claim.

Consequently, if Ac is an evaluated approximation with ||A-Ac||<=e, then

||H - (Ac direct-sum 0)|| <= e + (q+sqrt(q²+4 a q))/2 =: eta.

Proof: first use the triangle inequality for the A error, then bound the quadratic form of [[0,B*],[B,C]] in absolute value by 2sqrt(aq)||x||||y||+q||y||². The largest eigenvalue of the scalar matrix [[0,sqrt(aq)],[sqrt(aq),q]] is the displayed quantity. This is often a much weaker estimate than actually calculating B, but it is valid for the full complement.

If a tighter directly certified crossing bound b is known, replace sqrt(aq) by b. If q is not small compared with the leading transfer eigenvalue, a temporal cutoff alone has not justified compression.

A more favorable block bound can be obtained using H's finite Schur complement: for z>q,

A <= A+B*(z-C)^(-1)B <= A+B*B/(z-q).

It still needs B*B or a certified bound for it. The mere existence of a tensor network is no substitute for this input.

## 3. Normalization and a valid finite-gap certificate

Assume Ac is positive and its Perron eigenvalue lambda_c>0 is enclosed. If ||H-(Ac direct-sum 0)||<=eta and l>0 is a certified lower bound for lambda_1(H), then

||H/lambda_1(H) - (Ac/lambda_c direct-sum 0)|| <= 2 eta/l.

Proof: Weyl gives |lambda_1(H)-lambda_c|<=eta. Split the normalized difference into (H-Hc)/lambda_1(H) plus Hc[1/lambda_1(H)-1/lambda_c]. The two norms are at most eta/l. A convenient lower bound is max(certified lower(lambda_c)-eta, any independent positive Rayleigh lower bound).

For a certified second eigenvalue upper u2 of Hc, Weyl gives lambda_2(H)<=u2+eta. A sufficient strict gap condition is u2+eta<l. A dimensionless transfer gap lower bound is then 1-(u2+eta)/l. At physical time step a_t the corresponding energy-gap lower bound is -log((u2+eta)/l)/a_t, provided the ratio lies in (0,1).

These statements are finite-volume only. Volume uniformity requires the same positive lower physical energy bound for the volume family. Continuum reconstruction is additional work.

## 4. Full-matrix certification from weights versus entries

A deterministic pointwise estimate for approximated squared weight v_c is unusually useful. If

(1-epsilon) W² <= v_c <= (1+epsilon) W²,

then the exactly integrated Gc=E*v_c E satisfies (1-epsilon)G <= Gc <= (1+epsilon)G. The same relative order holds for Hc=K^(1/2)GcK^(1/2). Thus ||H-Hc||<=epsilon||H||, and the normalized H operators differ by at most 2epsilon when Hc is positive and nonzero.

This result does not remove the need to integrate v_c, and depends on a pointwise two-sided multiplicative bound. Positivity of individual SU(3) character expansion coefficients does not establish that bound: nontrivial characters take negative or non-real values. Dropping character terms is not generally pointwise monotone. Dropping spatial positive factors w²>=1, as in V15, supplies only a one-sided lower Gram bound.

By contrast, an entrywise error bound |Gij-Gcij|<=epsilon gives only ||G-Gc||<=D epsilon in general. The example G=I+epsilon J, Gc=I, where J is the all-ones matrix, has error D epsilon despite every entry error being epsilon. Hermiticity and positive definiteness do not remove this issue. To avoid D amplification, supply a proven induced norm, Frobenius bound, Loewner enclosure, or suitable weighted relative norm. Selected entries and selected low-dimensional blocks do not certify all entries.

Random integration can support probabilistic confidence statements only with proved concentration hypotheses, sample count, normalization and failure probability. It is not a deterministic outward interval certificate. Adaptive sampling and simultaneous many-entry claims require their own error accounting.

## 5. Tensor representation versus executed contraction

An exact spin-network/representation-ring expression is a finite algebraic representation. A certified numerical contraction additionally needs:

- Fixed lattice orientation/incidence and all 24 plaquette factors.
- A reproducible physical basis including every intertwiner multiplicity, or a proved invariant compression with the omitted-space bound above.
- SU(3) Haar tensors, including the epsilon invariant where fundamental/conjugate trialities permit it. A U(3)-only pair-contraction rule is insufficient for general SU(3) integrals.
- A specified contraction order and actual intermediate tensors or an executable factored representation supporting the requested entries/operator actions.
- Bounds on every discarded tensor component and their amplification by the surrounding network. Small local singular values alone are not global operator error bounds.
- A final deterministic error for the full matrix/operator and a compatible normalization certificate.

Finite-support Fourier data for one plaquette do not provide any of these coupled global contractions automatically. A compressed expression that merely relocates the full hard integral into unresolved Haar tensors is a plan, not an executed answer.

## 6. Audit conclusion

V14's complete external-complement theorem is valid for its full finite range. V15's 729-state lower operator does not evaluate the full 24-plaquette Gram matrix. There is no contradiction between these statements.

A valid computational route can first evaluate a finite P block of H, certify its full K-weighted omitted tail, and prove a normalized spectral error. Alternatively it can contract a full-rank tensor representation with a proved operator error. Neither route is closed simply by local coefficient generation, rank compression, Monte Carlo estimates, or formal tensor construction.
