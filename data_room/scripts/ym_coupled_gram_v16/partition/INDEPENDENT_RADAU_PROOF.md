# Independent audit of the all-24-plaquette scalar enclosure

The checker `verify_partition_independent.py` imports no generator functions. It independently brackets the interior Radau nodes by 430 rational bisection steps, integrates their Lagrange cardinal polynomials to obtain weights, checks all moments of orders zero through four, and bounds exponentials by a different algorithm: 128 Taylor terms after division by 1024, a positive geometric remainder, then ten directed-rounding squarings. It uses 145 decimal digits rather than the generator's 90. Every independently obtained interval is contained in the corresponding published interval. Execution returned `PASS_INDEPENDENT_RADAU_SCALAR_AUDIT`.

## Exact polynomial and quadrature facts

The input is the probability law of D=sum over all 24 plaquettes ReTr(U_p), whose support lies in [-36,72]. The supplied Haar moments are m0=1,m1=0,m2=12,m3=6,m4=3890/9. This audit verifies arithmetic conditional on those moments; it does not independently rederive the underlying coupled Haar moments.

For a fixed endpoint z, the quadratic p(x)=x²+b*x+c is selected so that (x-z)p(x) is orthogonal to 1 and x under this law. The checker verifies both identities exactly from rational b,c. Its two interior real roots and endpoint z define the three quadrature nodes. The weights are the integrals of the degree-two cardinal Lagrange polynomials, so the rule is exact through degree two. For any polynomial r of degree <=4, division gives r=q(x)(x-z)p(x)+s(x) with degree(q)<=1 and degree(s)<=2. Orthogonality integrates the first term to zero; it also vanishes at each node. Hence the rule is exact through degree four. The checker separately encloses each of those five reproduced moments and verifies all three weights are positive.

## Why left Radau is a lower bound and right Radau an upper bound

Let f(x)=exp(813/5+(271/60)x). Interpolate f at the endpoint once and at each interior node twice (function and derivative). The Hermite interpolant h has degree <=4. Its error is

f(x)-h(x)=f^(5)(xi)/5! * (x-z)(x-r1)^2(x-r2)^2

for an intermediate xi, with the identity continued at interpolation nodes. Since f^(5)>0 on the whole interval, z=-36 makes this error nonnegative and z=72 makes it nonpositive. Integrating and using degree-four exactness of the quadrature shows

Q_left(f) <= integral f(D) <= Q_right(f).

This sign argument applies to the original correlated law of D. It does not presume plaquette independence.

## Polynomial spatial weight and scalar normalization

For each plaquette, x_s=(271/240)(3+chi3+chi3bar) is in [0,10.1625]. The V14 local bound is

(1-eps) exp(x_s) <= p233(x_s) <= exp(x_s).

Squaring and multiplying all 24 factors yields

(1-48 eps) exp(2 sum_p x_s) <= W² <= exp(2 sum_p x_s),

using (1-eps)^48 >=1-48eps>0. Moreover 2 sum_p x_s=813/5+(271/60)D. Consequently the reported enclosure

(1-48eps) Q_left(f) <= G00 <= Q_right(f)

is valid. The inherited eps is an upper bound, so using it weakens the lower bound safely. The final directed decimal conversion preserves this inequality.

## Audit of generator exponential routine

The generator sums positive Taylor terms through degree 1600. For an upper bound, the first omitted term has index 1601 and each subsequent term ratio is at most x/1602. Thus its tail expression first/(1-x/1602) is valid for 0<=x<1602, covering all arguments here (at most 487.8). FLOOR arithmetic gives a lower positive partial sum; CEILING arithmetic and a FLOOR denominator give an upper bound. Node and weight interval products remain positive in the exponential sum. Rational root enclosures and sign-aware interval division are valid. No arithmetic or remainder-sign defect was found.

## Scope

The output is a broad correlated scalar integral enclosure, approximately 1.5842e78 <=G00<=7.59895e206. It includes all 24 spatial factors in the defining integral. Its large width (ratio about 4.797e128) prevents describing it as a precise scalar contraction. It does not evaluate the other entries of the full Gram matrix, certify a finite-rank approximation, or prove a spectral gap. The published false scope flags are appropriate.
