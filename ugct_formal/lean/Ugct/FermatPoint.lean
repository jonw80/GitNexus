import Ugct.Grading

/-!
# What X₅ itself outputs at the Fermat point has grade 0

At the Fermat point the Weil–Petersson metric of the marginal deformation
`∏ xᵢ^{sᵢ}` (`∑ sᵢ = 5`, `sᵢ ≤ 3`) and the normalized Yukawa couplings are monomials in
`γ(j/5) = Γ(j/5) / Γ(1 - j/5)` (Cecotti–Vafa tt*, 1991; Aleshkin–Belavin, 2018):

* `G_s = ∏ᵢ γ((sᵢ+1)/5) / γ(1/5)^5`
* `κ̂²_{abc} = ∏ᵢ γ(1/5) / (γ((aᵢ+1)/5) γ((bᵢ+1)/5) γ((cᵢ+1)/5))`, with `a + b + c = (3,3,3,3,3)`.

For the direction `s = (1,1,1,1,1)` both formulas are re-derived numerically from the
Picard–Fuchs equation alone in `fermat_point_couplings.py` (agreement to 37 digits).

This file proves that every such monomial has grade 0, hence lies in the
period-generated class `reachable`.  The closed form used for α⁻¹ has grade 1
(`alpha_not_reachable`), so it is not a quantity of this kind.
-/

namespace UGCT.Grading

/-- Exponent vector of `γ(j/5) = Γ(j/5) / Γ((5 - j)/5)`. -/
def gammaVec (j : Fin 5) : Mono := gen j - gen (-j)

theorem grade_gammaVec (j : Fin 5) : grade (gammaVec j) = 2 * ((j : ℕ) : ZMod 5) := by
  fin_cases j <;> simp [gammaVec, grade_gen] <;> decide

theorem grade_gammaVec_succ (j : Fin 4) : grade (gammaVec j.succ) = 2 * ((j : ℕ) : ZMod 5) + 2 := by
  rw [grade_gammaVec, Fin.val_succ]; push_cast; ring

theorem grade_gammaVec_one : grade (gammaVec 1) = 2 := by
  rw [grade_gammaVec]; decide

/-- Weil–Petersson metric at the Fermat point, deformation `∏ xᵢ^{sᵢ}` (`sᵢ ≤ 3`). -/
def wpVec (s : Fin 5 → Fin 4) : Mono :=
  (∑ i, gammaVec (s i).succ) - 5 • gammaVec 1

/-- Square of the normalized Yukawa coupling of three marginal deformations. -/
def yukVec (a b c : Fin 5 → Fin 4) : Mono :=
  ∑ i, (gammaVec 1 - gammaVec (a i).succ - gammaVec (b i).succ - gammaVec (c i).succ)

theorem grade_wpVec (s : Fin 5 → Fin 4) (hs : ∑ i, (s i : ℕ) = 5) : grade (wpVec s) = 0 := by
  have hs' : (∑ i, ((s i : ℕ) : ZMod 5)) = 0 := by
    rw [← Nat.cast_sum, hs]; rfl
  simp only [wpVec, map_sub, map_sum, map_nsmul, grade_gammaVec_succ, grade_gammaVec_one]
  rw [Finset.sum_add_distrib, ← Finset.mul_sum, hs']
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
  decide

theorem grade_yukVec (a b c : Fin 5 → Fin 4) (h : ∀ i, (a i : ℕ) + b i + c i = 3) :
    grade (yukVec a b c) = 0 := by
  unfold yukVec
  rw [map_sum]
  refine Finset.sum_eq_zero fun i _ => ?_
  have hi : ((a i : ℕ) : ZMod 5) + ((b i : ℕ) : ZMod 5) + ((c i : ℕ) : ZMod 5) = 3 := by
    have := congrArg (Nat.cast (R := ZMod 5)) (h i)
    push_cast at this
    exact this
  simp only [map_sub, grade_gammaVec_succ, grade_gammaVec_one]
  have e : (2 : ZMod 5) - (2 * ((a i : ℕ) : ZMod 5) + 2) - (2 * ((b i : ℕ) : ZMod 5) + 2)
      - (2 * ((c i : ℕ) : ZMod 5) + 2)
      = -2 * (((a i : ℕ) : ZMod 5) + ((b i : ℕ) : ZMod 5) + ((c i : ℕ) : ZMod 5)) - 4 := by ring
  rw [e, hi]
  decide

theorem wpVec_mem_reachable (s : Fin 5 → Fin 4) (hs : ∑ i, (s i : ℕ) = 5) :
    wpVec s ∈ reachable :=
  (mem_reachable_iff _).2 (grade_wpVec s hs)

theorem yukVec_mem_reachable (a b c : Fin 5 → Fin 4) (h : ∀ i, (a i : ℕ) + b i + c i = 3) :
    yukVec a b c ∈ reachable :=
  (mem_reachable_iff _).2 (grade_yukVec a b c h)

/-- The direction computed from the Picard–Fuchs equation: `s = (1,1,1,1,1)`. -/
theorem wp_fermat_direction_reachable : wpVec (fun _ => 1) ∈ reachable :=
  wpVec_mem_reachable _ (by decide)

theorem yukawa_fermat_direction_reachable :
    yukVec (fun _ => 1) (fun _ => 1) (fun _ => 1) ∈ reachable :=
  yukVec_mem_reachable _ _ _ (fun _ => rfl)

end UGCT.Grading
