# Evolutionary search, generation 1: pre-registered (2026-11-25)

Target: alpha^-1(0) = 137.035999177(21) from X5 with nothing fitted. Hard constraints H1-H7: no measured
input upstream (G2); frozen before comparison (G8); invariant under Omega -> lambda Omega and Sp(204, Z) (G4);
scale and scheme declared (G5); every trial of this search counted (G9); Z5 selection rule respected or its
breaking explained; within +-1 sigma.

A. Weil systole of X5 (type IIB, Fermat point). Q(g) = <g, C g> with C the Weil operator i^(p-q) and < , >
   the unimodular intersection form of H_3(X5, Z) (block_lattice.py). Q(g) is the exact infrared coupling of
   a charge g (Q = 1/Im tau for a unit charge). The 51 character blocks are orthogonal for Q, and the
   projection of H_3 to block b is the dual lattice of the block sublattice, so
   min_b mu_b <= min_{g != 0} Q(g) <= min_b m_b, with m_b = min of Q on the block sublattice and mu_b = min
   on its dual. Candidate: alpha^-1_max(X5) = 1/min Q, the weakest coupling of any charge. Decision: if
   1/min_b mu_b < 137.035999177 no charge of X5 couples as weakly as the electron (class fails on magnitude).
B. Type IIA on the quintic at the Gepner point: the (1,1,1,1,1) block taken with its principal (unimodular)
   form; candidate alpha^-1 = 1/min Q. Same decision rule.
C. Worldsheet correlators. Every chiral three-point structure constant of the k = 3 N = 2 minimal model,
   squared, C^2 = gamma(1/5) gamma((l3+1)/5) / (gamma((l1+1)/5) gamma((l2+1)/5)) with l3 = l1 + l2 <= 3, is
   tested for grade 0. If all are grade 0, every correlator-built quantity of the Gepner model is grade 0 and
   the class cannot give Law 1 (grade 1).
