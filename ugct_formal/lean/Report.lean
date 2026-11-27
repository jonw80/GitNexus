import Ugct

/-! The dependency report.  For each theorem, Lean's kernel lists every axiom it rests on.
    Lean's own foundation is `propext`, `Classical.choice`, `Quot.sound`; anything else listed
    is a declared postulate or conjecture. -/

-- Layer 1: mathematics
#print axioms UGCT.gauss_mul_five
#print axioms UGCT.alpha_identity
#print axioms UGCT.Grading.mem_reachable_iff
#print axioms UGCT.Grading.alpha_not_reachable
#print axioms UGCT.Grading.gammaOne_not_reachable
#print axioms UGCT.Grading.grade_wpVec
#print axioms UGCT.Grading.grade_yukVec
#print axioms UGCT.Grading.wp_fermat_direction_reachable
#print axioms UGCT.Grading.yukawa_fermat_direction_reachable
#print axioms UGCT.Grading.sin2W_not_reachable
#print axioms UGCT.Grading.lambdaH_not_reachable
#print axioms UGCT.Grading.vcbFactor_not_reachable
#print axioms UGCT.Grading.kappaSq_reachable
-- Layer 1, conditional on an open conjecture
#print axioms UGCT.Conditional.alpha_closed_form_not_from_periods
#print axioms UGCT.Conditional.gamma_one_fifth_not_from_periods
-- Layer 2: physics
#print axioms UGCT.Physics.law1
#print axioms UGCT.Physics.law1_of_postulates
