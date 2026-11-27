# Evolutionary search: generation 3 pre-registration (2026-11-25)

Written before running `evolution_gen3.py`. Same target and hard constraints as generations 1 and 2: make Law 1, alpha^-1 = pi Gamma(1/5)^3/Gamma(2/5), an exact consequence of X_5 with nothing fitted.

## Generation 2 outcome (EVOLUTION_GEN2_RESULTS_2026-11-25.txt)

- **A.** The exponential period I(a, c) = Int_0^inf e^(-c x^5) x^(a-1) dx scales as c^(-a/5); this was checked for a = 1..6. Under W -> cW, a Gamma-monomial at fifths therefore has weight -grade/5 (mod 1). The Kaehler-scale obstruction and the grade obstruction (T3) are one obstruction. The 0-of-6561 count only restates this once the scaling is granted.
- **B.** The three readings of N_Y omega_Y have torus characters (2,1,1,3,4), (1,2,1,3,4) and (1,1,2,3,4). None is a multiple of (1,1,1,1,1), so P8's normalization depends on the choice of Fermat coordinates. All 4,904 torus-neutral products of one to three periods have grade 0.
- **C. Synthesis.** Take a quantity built from X_5 that depends neither on the presentation (the torus) nor on the Kaehler gauge (the scale). It has trivial character, hence grade 0. Law 1 has grade 1. A surviving construct must therefore supply one physical object of scale weight 1/5 (mod 1). P8 supplies it by postulate (N_Y = 3 sqrt5 Gamma(1/5)). No presentation-invariant construct does. This agrees with P8's ledger basis and adds the torus computation.

All Generation 1 and 2 classes are retired. Generation 3 aims at the gap found in C: each candidate tries to supply scale weight 1/5 physically. Each candidate carries its pass criterion and predicted verdict.

## G3-1 Laplace factor of the affine chart

Never applied to alpha.

**Claims (identities).**
- Law 1 = N_Y P(omega_Y)/(12 pi), where P(omega_Y) = prod Gamma(a_i/5)/Gamma(|a|/5) for a = (1,1,1,3,4).
- N_Y = 15 sqrt5 Gamma(6/5). Here Gamma(6/5) is the Laplace factor Gamma(|a'|/5) of the affine chart x_0 = 1, with a' = (1,1,1,3).
- Equivalently, Law 1 = sin(2 pi/5) 5^4 Int_{R+^4} e^(-sum x_i^5) x_4^2 d^4x. This is an exponential period of W_4 = x_1^5 + ... + x_4^5, which has c-hat = 12/5.

**Test.** Check both identities to 50 digits.

**Pass.** Accept only if X_5 alone fixes the hyperplane and the insertion, with no choice.

**Predicted verdict: Critical.** The hyperplane x_0 = 0 (5 choices) and the placement of the insertion (4) are free, and W_4 is not critical (c-hat 12/5, not 3).

## G3-2 tt* normalization

Never applied to alpha.

The tt*-orthonormal Ramond ground state of character k in one x^5 factor is omega_k = alpha_k lambda^(k/5) x^(k-1) dx, with alpha_k proportional to [sqrt(sin(k pi/5)) Gamma(k/5)]^-1 (Leaf-Herrmann 1991, eq. A.11; Cecotti-Vafa 1991). So sqrt(g_k) = Gamma(k/5) pi^(-1/2) x algebraic.

**Claims.**
- (i) A thimble central charge in tt*-orthonormal normalization contains no Gamma: it is algebraic x pi^(n/2).
- (ii) Law 1 = pi^2 sqrt(g_1^3 g_3) x algebraic, which is the norm of x_4^2 d^4x in the four-field model.
- (iii) A single n-copy state with characters in {1..4}^n has the Gamma-content of Law 1 (exponents (3, -1) on Gamma(1/5), Gamma(2/5)) only if n is even and n >= 4. In particular no such state exists for n = 5, the critical Gepner model (c-hat 3). No product of Gepner-projected states (sum of characters = 0 mod 5) has it either, by grade.

**Test.** Exact exponent enumeration for n <= 8, and a 50-digit check of (ii).

**Pass.** Accept only if a critical, projected (n = 5) realization exists.

**Predicted verdict: Critical.** Parity rules out n = 5, and grade rules out the projected states.

## G3-3 Laplace scale fixed by S-duality

Never applied.

**Claim.** If the Laplace variable is the IIB coupling, then Int_0^inf e^(-t/g_s) t^(6/5 - 1) dt = g_s^(6/5) Gamma(6/5). The SL(2,Z) fixed points tau = i and tau = e^(i pi/3) fix g_s = 1 and g_s = 2/sqrt3.

**Test.** Do the two fixed points give the same value?

**Pass.** Accept only if X_5 singles out one fixed point and a mechanism makes the dilaton the Laplace variable.

**Predicted verdict: Critical.** There are two fixed points, differing by a factor (2/sqrt3)^(6/5) = 1.188; there is no mechanism; and the presentation dependence of G3-1 remains.

## E Escalation: a meta-technique (character-graded reachability)

Instead of generating constructs, compute the character of every generator that the hard constraints admit:
- periods of X_5 and of its branes, and their conjugates;
- pi and the algebraic numbers;
- Hodge norms, ratios, canonically normalized central charges, structure constants and couplings.

If all of them have trivial character and the target has grade 1, the frontier is empty under the hard constraints (conditional on K1). The output is then the list of minimal relaxations, each tagged with the constraint it breaks:
- R1: a non-critical sector;
- R2: a coordinate choice;
- R3: an external scale of weight 1/5;
- R4: dropping exactness (C30).

**Test.**
- Confirm grade {0} on every generator computed so far: Gen-1 C, Gen-2 B, and the projected states of G3-2.
- Certify the magnitude no-go with Fincke-Pohst (PARI qfminim) on all 51 dual block forms, replacing the box search of Gen-1 A. The pass criterion is that every block has the same certified dual minimum (2/125) tan 72 deg = 0.0492429, and that the block minimum is 10 tan 72 deg = 30.7768.
