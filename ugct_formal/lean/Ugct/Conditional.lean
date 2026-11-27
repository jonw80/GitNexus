import Ugct.Grading

/-!
# UGCT layer 1, conditional: from formal monomials to real numbers

`Ugct.Grading` decides which *formal* Γ-monomials the periods produce.  To conclude that a
*real number* such as `π Γ(1/5)³ / Γ(2/5)` is not an algebraic multiple of any product of
periods, one needs to know that the real numbers Γ(j/5) obey no multiplicative relations beyond
the standard ones.  That is Rohrlich's conjecture.  It is open, so it enters here as a declared
`axiom`, and Lean lists it under `#print axioms` for every theorem that uses it.

Restricted to denominator 5, the standard relations (reflection, Gauss multiplication, and the
Koblitz–Ogus criterion that characterizes them) allow exactly the exponent patterns
`x₁ = x₄, x₂ = x₃`; the axiom below states that no other pattern gives an algebraic number.
-/

open Real UGCT.Grading

namespace UGCT.Conditional

/-- The real number a formal monomial stands for. -/
noncomputable def realMono (x : Mono) : ℝ :=
  π ^ (x 0) * Gamma (1/5) ^ (x 1) * Gamma (2/5) ^ (x 2) * Gamma (3/5) ^ (x 3)
    * Gamma (4/5) ^ (x 4)

lemma realMono_pos (x : Mono) : 0 < realMono x := by
  unfold realMono
  have h1 : 0 < Gamma (1/5) := Real.Gamma_pos_of_pos (by norm_num)
  have h2 : 0 < Gamma (2/5) := Real.Gamma_pos_of_pos (by norm_num)
  have h3 : 0 < Gamma (3/5) := Real.Gamma_pos_of_pos (by norm_num)
  have h4 : 0 < Gamma (4/5) := Real.Gamma_pos_of_pos (by norm_num)
  have := zpow_pos Real.pi_pos (x 0)
  have := zpow_pos h1 (x 1); have := zpow_pos h2 (x 2)
  have := zpow_pos h3 (x 3); have := zpow_pos h4 (x 4)
  positivity

lemma realMono_add (x y : Mono) : realMono (x + y) = realMono x * realMono y := by
  have h1 : Gamma (1/5) ≠ 0 := (Real.Gamma_pos_of_pos (by norm_num)).ne'
  have h2 : Gamma (2/5) ≠ 0 := (Real.Gamma_pos_of_pos (by norm_num)).ne'
  have h3 : Gamma (3/5) ≠ 0 := (Real.Gamma_pos_of_pos (by norm_num)).ne'
  have h4 : Gamma (4/5) ≠ 0 := (Real.Gamma_pos_of_pos (by norm_num)).ne'
  simp only [realMono, Pi.add_apply, zpow_add₀ Real.pi_ne_zero, zpow_add₀ h1, zpow_add₀ h2,
    zpow_add₀ h3, zpow_add₀ h4]
  ring

lemma realMono_sub (x y : Mono) : realMono (x - y) = realMono x / realMono y := by
  rw [eq_div_iff (realMono_pos y).ne', ← realMono_add, sub_add_cancel]

lemma realMono_alphaVec : realMono alphaVec = π * Gamma (1/5) ^ 3 / Gamma (2/5) := by
  simp [realMono, alphaVec, gen, div_eq_mul_inv]

lemma realMono_gammaOneVec : realMono gammaOneVec = Gamma (1/5) := by
  simp [realMono, gammaOneVec, gen]

/-- **Rohrlich's conjecture at denominator 5** (open problem; declared, not proved).
If `π^k Γ(1/5)^m₁ Γ(2/5)^m₂ Γ(3/5)^m₃ Γ(4/5)^m₄` is algebraic, then `m₁ = m₄` and `m₂ = m₃`. -/
axiom rohrlich_five (x : Mono) (h : IsAlgebraic ℚ (realMono x)) : x 1 = x 4 ∧ x 2 = x 3

/-- Under Rohrlich's conjecture: a monomial of nonzero grade is not an algebraic multiple of
anything the periods produce. -/
theorem not_algebraic_multiple {v : Mono} (hv : grade v ≠ 0) {x : Mono} (hx : x ∈ reachable)
    {q : ℝ} (hq : IsAlgebraic ℚ q) : realMono v ≠ q * realMono x := by
  intro h
  have hq' : realMono (v - x) = q := by
    rw [realMono_sub, h, mul_div_assoc, div_self (realMono_pos x).ne', mul_one]
  obtain ⟨h14, h23⟩ := rohrlich_five (v - x) (by rw [hq']; exact hq)
  have hzero : grade (v - x) = 0 := by
    have h5 : (5 : ZMod 5) = 0 := rfl
    rw [grade_apply, h14, h23]
    linear_combination (((v - x) 4 : ZMod 5) + ((v - x) 3 : ZMod 5)) * h5
  rw [map_sub, grade_eq_zero_of_mem hx, sub_zero] at hzero
  exact hv hzero

/-- Under Rohrlich's conjecture: the closed form of Law 1 is not an algebraic multiple of any
product of periods of `X₅`, powers of π and reflection factors. -/
theorem alpha_closed_form_not_from_periods {x : Mono} (hx : x ∈ reachable) {q : ℝ}
    (hq : IsAlgebraic ℚ q) : π * Gamma (1/5) ^ 3 / Gamma (2/5) ≠ q * realMono x := by
  rw [← realMono_alphaVec]
  exact not_algebraic_multiple (by rw [grade_alphaVec]; decide) hx hq

/-- Under Rohrlich's conjecture: the bare `Γ(1/5)` in `N_Y = 3√5 Γ(1/5)` cannot come from the
periods either. -/
theorem gamma_one_fifth_not_from_periods {x : Mono} (hx : x ∈ reachable) {q : ℝ}
    (hq : IsAlgebraic ℚ q) : Gamma (1/5) ≠ q * realMono x := by
  rw [← realMono_gammaOneVec]
  exact not_algebraic_multiple (by rw [grade_gammaOneVec]; decide) hx hq

end UGCT.Conditional
