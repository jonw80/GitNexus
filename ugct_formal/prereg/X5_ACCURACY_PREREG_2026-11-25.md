# Can numbers that come from X_5 make Law 1 accurate? Pre-registration (2026-11-25)

This file, `x5_dictionary.py`, `x5_accuracy_scan.py` and `test_x5_accuracy_checks.py` were committed before `x5_accuracy_scan.py` was run. The unit tests use planted dictionaries and planted targets only.

## Targets

- **Law 1:** L = pi Gamma(1/5)^3/Gamma(2/5) = 137.035982241257.
- **CODATA 2022:** alpha^-1 = 137.035999177(21).
- **Gap:** delta = alpha^-1 - L = 1.69357(21) x 10^-5 (sigma = 2.1 x 10^-8, relative 1.24 x 10^-3).

The earlier scan E (ALPHA_EXACTNESS, 2026-11-24) used generic terms (p/q) alpha^k pi^m. This scan uses only numbers that X_5 determines.

## Dictionary: 47 numbers

`x5_dictionary.py` computes them to 60 digits and recomputes what can be recomputed from X_5's defining data. It exits 1 if a check fails. The checks are:
- the Chern numbers from c(X) = (1+H)^5/(1+5H);
- h^{2,1} from the monomial count;
- the 204 characters of H^3 and their 51 Galois orbits;
- the Gopakumar-Vafa numbers n_1, n_2, n_3, from the Picard-Fuchs periods and the mirror map in exact rational arithmetic;
- the conifold newform, identified among the three newforms of S_4(Gamma_0(25)) by point counts of the Dwork quintic at psi = 1 over F_p for p = 2, 3, 7, 13, 17. Only the form with a_2 = 1 fits #X = 1 + 2p + p^2 + p^3 - a_p;
- PARI functional-equation checks for the L-functions;
- the closed forms of L(M2,2), zeta_K(2) and L(2, chi_5);
- the identity Law 1 = N_Y P(omega_Y)/(12 pi);
- the ledger values of M9.

| Group | Numbers |
|---|---|
| Topology and enumerative geometry | 5 (degree), 3 (dimension), 50 (c_2.H), 200 (abs chi), 100, 101 (h^{2,1}), 204 (b_3), 25/12, 5/6, 25/3, 31/3 and 31/12 (BCOV F_1), 2875, 609250, 317206375 (GV), 3125 (conifold), 75000 (abs Aut), 51 (Galois blocks) |
| Gepner and Landau-Ginzburg point | phi (quantum dimension), 9/5 (minimal-model central charge), sin(pi/5), sin(2 pi/5), tan 72 deg, (2/5) tan 72 deg (T13), (2/125) tan 72 deg (T14), cot(pi/5)/2 (Im t at the LG point) |
| Periods and couplings at the Fermat point | Gamma(1/5), Gamma(2/5), Gamma(3/5), Gamma(4/5), Gamma(1/5)^5, P(omega_Y) = Gamma(1/5)^3 Gamma(3/5) Gamma(4/5), kappa (M5), kappa^5 and g_psipsibar(0) (M9), L(M2,2) (Fermat motive) |
| Gamma class | xi = abs(chi) zeta(3)/(2 (2 pi)^3) |
| Arithmetic | L(f,1), L(f,2), L(f,3) for the conifold newform f; log phi; zeta_{Q(sqrt5)}(2); L(2, chi_5); 125 (abs disc Q(zeta_5)); 25 (level of f) |
| Flagged: UGCT's own formulas, not consequences of X_5 | N_Y (P8), L (Law 1) |

Each value enters through its absolute value.

## Scan A: additive corrections to Law 1

**Forms.** delta = D^e alpha^k pi^m, where:
- D is one of the 47 numbers, e = +-1, k = 0..4, m = -3..3, and alpha is the CODATA value. That gives 3,290 forms.
- A reference family with D = 1 (pure alpha^k pi^m) adds 35 forms. It contains alpha^2/pi (C30). It is not counted as X_5.

**Hit.** |form - delta| <= sigma. For each hit, the scan also prints the measurement-free version, with alpha replaced by 1/L.

**Null model.** 100,000 targets log-uniform in [delta/10, 10 delta], with the same relative window. p_A is the fraction of targets with at least one X_5 hit.

## Scan B: alpha^-1 itself at CODATA precision

**Forms.** pi^m D_1^p1 D_2^p2 D_3^p3 over at most three distinct dictionary numbers, with:
- p_i in {+-1, +-2, +-3};
- m = -3..3.

That gives 24,791,473 forms. Law 1 is one of them; it misses by 1.24 x 10^-7 (806 sigma).

**Hit.** |form - alpha^-1| <= 2 sigma.

**Null model.** 100,000 targets log-uniform in [alpha^-1/1.5, 1.5 alpha^-1]. p_B is the fraction with at least one hit.

**Secondary statistic.**
- The distinct forms at least as close to alpha^-1 as Law 1 is.
- The fraction of random targets that have such a form.

This measures whether Law 1's accuracy is surprising inside an X_5 dictionary of this size. The earlier family of 277k Gamma-formulas gave 0.3%.

**Consistency checks.** Every hit is recomputed at 50 digits. Each window count must equal the number of verified forms. The scan exits 1 otherwise.

## Pass criteria and prediction

**Evidence criterion.** A hit counts as evidence only if its scan's null probability is below 0.01.

**Mechanism check.** Every hit, evidence or not, goes to a mechanism check:
- a published physical or mathematical mechanism;
- the sigma-screen against Law 1's sigma = 1/5, where sigma is defined.

**Prediction.**
- Scan A has a null probability between 0.05 and 0.5, so any hit is at chance level. No X_5 hit has a mechanism.
- Scan B finds no hit within 2 sigma, with a null probability near 3 x 10^-4.
- The secondary fraction is of order 0.1. In a dictionary this large, Law 1's 0.124 ppm accuracy is not surprising.
