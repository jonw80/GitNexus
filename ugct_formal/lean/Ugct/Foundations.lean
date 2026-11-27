import Mathlib

/-!
# UGCT layer 1: mathematics

Every theorem in this file is checked by Lean's kernel against Mathlib.
`#print axioms` on any of them lists only Lean's three foundational axioms
(`propext`, `Classical.choice`, `Quot.sound`): no physics and no measured number.

Ledger nodes: T2 (reflection and Gauss multiplication at n = 5) and the
algebraic identity used in Law 1.  The Fermat period `omegaY` is written with
Griffiths' formula as a *definition*: the statement that this number is a
period of the Fermat quintic is an imported theorem (Hodge theory of
hypersurfaces is not in Mathlib), not something proved here.
-/

open Real

namespace UGCT

/-- Reflection formula at `s = 1/5`. -/
theorem gamma_one_mul_gamma_four : Gamma (1/5) * Gamma (4/5) = π / sin (π / 5) := by
  have h := Real.Gamma_mul_Gamma_one_sub (1/5 : ℝ)
  rw [show (1:ℝ) - 1/5 = 4/5 by norm_num, show π * (1/5) = π / 5 by ring] at h
  exact h

/-- Reflection formula at `s = 2/5`. -/
theorem gamma_two_mul_gamma_three : Gamma (2/5) * Gamma (3/5) = π / sin (2 * (π / 5)) := by
  have h := Real.Gamma_mul_Gamma_one_sub (2/5 : ℝ)
  rw [show (1:ℝ) - 2/5 = 3/5 by norm_num, show π * (2/5) = 2 * (π / 5) by ring] at h
  exact h

lemma sin_pi_div_five_pos : 0 < sin (π / 5) :=
  Real.sin_pos_of_pos_of_lt_pi (by positivity) (by linarith [Real.pi_pos])

lemma cos_pi_div_five_pos : 0 < cos (π / 5) := by
  rw [Real.cos_pi_div_five]; positivity

/-- `8 sin²(π/5) cos(π/5) = √5`. -/
theorem eight_sin_sq_mul_cos : 8 * sin (π / 5) ^ 2 * cos (π / 5) = √5 := by
  have h5 : (√5 : ℝ) ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  rw [Real.sin_sq, Real.cos_pi_div_five]
  linear_combination (-(√5 + 3) / 8) * h5

/-- Gauss multiplication formula for `n = 5`:
`Γ(1/5) Γ(2/5) Γ(3/5) Γ(4/5) = 4π²/√5`, written without division. -/
theorem gauss_mul_five :
    √5 * (Gamma (1/5) * Gamma (2/5) * Gamma (3/5) * Gamma (4/5)) = 4 * π ^ 2 := by
  have hs := sin_pi_div_five_pos
  have hc := cos_pi_div_five_pos
  have key := eight_sin_sq_mul_cos
  have hD : 2 * sin (π / 5) ^ 2 * cos (π / 5) ≠ 0 :=
    (mul_pos (mul_pos two_pos (pow_pos hs 2)) hc).ne'
  have e : Gamma (1/5) * Gamma (2/5) * Gamma (3/5) * Gamma (4/5)
      = π ^ 2 / (2 * sin (π / 5) ^ 2 * cos (π / 5)) := by
    calc Gamma (1/5) * Gamma (2/5) * Gamma (3/5) * Gamma (4/5)
        = (Gamma (1/5) * Gamma (4/5)) * (Gamma (2/5) * Gamma (3/5)) := by ring
      _ = (π / sin (π / 5)) * (π / (2 * sin (π / 5) * cos (π / 5))) := by
          rw [gamma_one_mul_gamma_four, gamma_two_mul_gamma_three, Real.sin_two_mul]
      _ = π ^ 2 / (2 * sin (π / 5) ^ 2 * cos (π / 5)) := by
          rw [div_mul_div_comm]; congr 1 <;> ring
  rw [e, mul_div_assoc', div_eq_iff hD]
  linear_combination (-π ^ 2) * key

/-- The Fermat period on the character `a = (1,1,1,3,4)`, written with Griffiths'
formula `ω(a) = (1/5) ∏ Γ(aᵢ/5)`. -/
noncomputable def omegaY : ℝ := (1/5) * Gamma (1/5) ^ 3 * Gamma (3/5) * Gamma (4/5)

/-- The number `N_Y = 3√5 Γ(1/5)` of Lemma 6.12. -/
noncomputable def NY : ℝ := 3 * √5 * Gamma (1/5)

/-- The algebraic identity used in Law 1:
`(5/3)/(4π) · N_Y · ω(1,1,1,3,4) = π Γ(1/5)³ / Γ(2/5)`.
This is pure mathematics; whether the left side is a coupling constant is not. -/
theorem alpha_identity :
    (5/3) / (4 * π) * NY * omegaY = π * Gamma (1/5) ^ 3 / Gamma (2/5) := by
  have hg := gauss_mul_five
  have h2 : Gamma (2/5) ≠ 0 := (Real.Gamma_pos_of_pos (by norm_num)).ne'
  unfold NY omegaY
  rw [eq_div_iff h2]
  calc (5/3) / (4 * π) * (3 * √5 * Gamma (1/5))
          * ((1/5) * Gamma (1/5) ^ 3 * Gamma (3/5) * Gamma (4/5)) * Gamma (2/5)
      = Gamma (1/5) ^ 3 * (√5 * (Gamma (1/5) * Gamma (2/5) * Gamma (3/5) * Gamma (4/5)))
          / (4 * π) := by ring
    _ = Gamma (1/5) ^ 3 * (4 * π ^ 2) / (4 * π) := by rw [hg]
    _ = π * Gamma (1/5) ^ 3 := by rw [div_eq_iff (by positivity)]; ring

end UGCT
