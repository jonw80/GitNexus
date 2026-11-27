import Ugct.Foundations

/-!
# UGCT layer 1: which Γ-monomials the periods of X₅ can produce

A formal Γ-monomial at fifths is an integer exponent vector `x : Fin 5 → ℤ`, standing for
`π^(x 0) · Γ(1/5)^(x 1) · Γ(2/5)^(x 2) · Γ(3/5)^(x 3) · Γ(4/5)^(x 4)`
up to an algebraic factor.

`reachable` is what the standard operations produce from the periods of the Fermat quintic:
products and quotients of periods `ω(a) = (1/5) ∏ Γ(aᵢ/5)`, powers of π, and the reflection
factors `Γ(j/5) Γ(1 - j/5) = π / sin(jπ/5)`.  The Gauss multiplication relation at n = 5 is the
sum of the two reflection relations (`UGCT.gauss_mul_five`), so it adds nothing new.

Main result, `mem_reachable_iff`: a formal monomial is reachable **if and only if** its grade
`x₁ + 2x₂ + 3x₃ + 4x₄ (mod 5)` is zero.  The grade is a complete test, and it takes one line to
apply to any candidate formula.

This is a statement about formal exponent vectors.  The corresponding statement about real
numbers needs Rohrlich's conjecture; see `Ugct.Conditional`.
-/

namespace UGCT.Grading

/-- Exponent vectors: index 0 is π, index j = 1, …, 4 is Γ(j/5). -/
abbrev Mono := Fin 5 → ℤ

/-- The generator vectors: `gen 0` is π, `gen j` is Γ(j/5). -/
def gen (j : Fin 5) : Mono := Pi.single j 1

/-- The grade: π has weight 0 and Γ(j/5) has weight j, modulo 5. -/
def grade : Mono →+ ZMod 5 where
  toFun x := (x 1 : ZMod 5) + 2 * x 2 + 3 * x 3 + 4 * x 4
  map_zero' := by simp
  map_add' x y := by simp only [Pi.add_apply, Int.cast_add]; ring

lemma grade_apply (x : Mono) :
    grade x = (x 1 : ZMod 5) + 2 * x 2 + 3 * x 3 + 4 * x 4 := rfl

lemma grade_gen (j : Fin 5) : grade (gen j) = ((j : ℕ) : ZMod 5) := by
  fin_cases j <;> simp [grade_apply, gen]

/-- A character of the Fermat quintic: every `aᵢ ∈ {1,2,3,4}` and `Σ aᵢ ≡ 0 (mod 5)`. -/
def IsChar (a : Fin 5 → Fin 5) : Prop :=
  (∀ i, a i ≠ 0) ∧ ∑ i, ((a i : ℕ) : ZMod 5) = 0

/-- The exponent vector of the period `ω(a) = (1/5) ∏ᵢ Γ(aᵢ/5)` (the factor 1/5 is algebraic). -/
def periodVec (a : Fin 5 → Fin 5) : Mono := ∑ i, gen (a i)

theorem grade_periodVec {a : Fin 5 → Fin 5} (ha : IsChar a) : grade (periodVec a) = 0 := by
  rw [periodVec, map_sum]
  simp only [grade_gen]
  exact ha.2

/-- Generators of the reachable lattice: all periods, π, and the two reflection factors. -/
def generators : Set Mono :=
  {v | ∃ a, IsChar a ∧ v = periodVec a} ∪ {gen 0, gen 1 + gen 4, gen 2 + gen 3}

/-- Everything the standard operations produce from the periods of `X₅`. -/
def reachable : AddSubgroup Mono := AddSubgroup.closure generators

theorem grade_eq_zero_of_mem {x : Mono} (hx : x ∈ reachable) : grade x = 0 := by
  have hle : reachable ≤ grade.ker := by
    rw [reachable, AddSubgroup.closure_le]
    rintro v (⟨a, ha, rfl⟩ | rfl | rfl | rfl)
    · exact grade_periodVec ha
    · show grade (gen 0) = 0
      simp [grade_apply, gen]
    · show grade (gen 1 + gen 4) = 0
      simp [grade_apply, gen]; decide
    · show grade (gen 2 + gen 3) = 0
      simp [grade_apply, gen]; decide
  exact hle hx

/-- The two periods used to span the grade-zero lattice. -/
def aY : Fin 5 → Fin 5 := ![1, 1, 1, 3, 4]
def aB : Fin 5 → Fin 5 := ![1, 1, 2, 2, 4]

lemma isChar_aY : IsChar aY := ⟨by decide, by decide⟩
lemma isChar_aB : IsChar aB := ⟨by decide, by decide⟩

lemma periodVec_aY : periodVec aY = 3 • gen 1 + gen 3 + gen 4 := by
  funext i
  fin_cases i <;> simp [periodVec, aY, gen, Pi.single_apply] <;> decide

lemma periodVec_aB : periodVec aB = 2 • gen 1 + 2 • gen 2 + gen 4 := by
  funext i
  fin_cases i <;> simp [periodVec, aB, gen, Pi.single_apply] <;> decide

theorem mem_of_grade_eq_zero {x : Mono} (hx : grade x = 0) : x ∈ reachable := by
  have h5 : ((5 : ℕ) : ℤ) ∣ x 1 + 2 * x 2 + 3 * x 3 + 4 * x 4 := by
    rw [← ZMod.intCast_zmod_eq_zero_iff_dvd]
    push_cast
    exact hx
  obtain ⟨t, ht⟩ := h5
  push_cast at ht
  have mem : ∀ v ∈ generators, v ∈ reachable := fun v hv => AddSubgroup.subset_closure hv
  have h0 : gen 0 ∈ reachable := mem _ (Or.inr (by simp))
  have h14 : gen 1 + gen 4 ∈ reachable := mem _ (Or.inr (by simp))
  have h23 : gen 2 + gen 3 ∈ reachable := mem _ (Or.inr (by simp))
  have hY : periodVec aY ∈ reachable := mem _ (Or.inl ⟨aY, isChar_aY, rfl⟩)
  have hB : periodVec aB ∈ reachable := mem _ (Or.inl ⟨aB, isChar_aB, rfl⟩)
  have hx' : x = x 0 • gen 0 + x 4 • (gen 1 + gen 4) + x 3 • (gen 2 + gen 3)
      + (2 * t - x 2 - x 3 - 2 * x 4) • (periodVec aY - (gen 1 + gen 4) - (gen 2 + gen 3))
      + (t - x 3 - x 4) • (periodVec aB - (gen 1 + gen 4)) := by
    rw [periodVec_aY, periodVec_aB]
    funext i
    fin_cases i <;> simp [gen] <;> linarith
  rw [hx']
  refine add_mem (add_mem (add_mem (add_mem ?_ ?_) ?_) ?_) ?_
  · exact zsmul_mem h0 _
  · exact zsmul_mem h14 _
  · exact zsmul_mem h23 _
  · exact zsmul_mem (sub_mem (sub_mem hY h14) h23) _
  · exact zsmul_mem (sub_mem hB h14) _

/-- **The grading criterion.**  A formal Γ-monomial at fifths can be produced from the periods
of the Fermat quintic by the standard operations if and only if its grade is zero. -/
theorem mem_reachable_iff (x : Mono) : x ∈ reachable ↔ grade x = 0 :=
  ⟨grade_eq_zero_of_mem, mem_of_grade_eq_zero⟩

/-! ### The manuscript's closed forms, tested -/

/-- `π Γ(1/5)³ / Γ(2/5)` (Law 1). -/
def alphaVec : Mono := gen 0 + 3 • gen 1 - gen 2
/-- `Γ(1/5)`, the factor in `N_Y = 3√5 Γ(1/5)` (Lemma 6.12; `3√5` is algebraic). -/
def gammaOneVec : Mono := gen 1
/-- `25 / (π² Γ(2/5)³)` (the sin²θ_W closed form). -/
def sin2WVec : Mono := -(2 • gen 0) - 3 • gen 2
/-- `Γ(1/5) Γ(2/5) / (25π)` (Law 4, λ_H). -/
def lambdaHVec : Mono := gen 1 + gen 2 - gen 0
/-- `Γ(2/5) / Γ(1/5)` (the |V_cb| factor of Theorem 18.1). -/
def vcbFactorVec : Mono := gen 2 - gen 1
/-- `κ² = Γ(3/5)³ Γ(1/5) / (Γ(2/5)³ Γ(4/5))`, the Distler–Greene Yukawa constant (control). -/
def kappaSqVec : Mono := gen 1 + 3 • gen 3 - 3 • gen 2 - gen 4

theorem grade_alphaVec : grade alphaVec = 1 := by
  simp [grade_apply, alphaVec, gen]; decide
theorem grade_gammaOneVec : grade gammaOneVec = 1 := by
  simp [grade_apply, gammaOneVec, gen]
theorem grade_sin2WVec : grade sin2WVec = 4 := by
  simp [grade_apply, sin2WVec, gen]; decide
theorem grade_lambdaHVec : grade lambdaHVec = 3 := by
  simp [grade_apply, lambdaHVec, gen]; decide
theorem grade_vcbFactorVec : grade vcbFactorVec = 1 := by
  simp [grade_apply, vcbFactorVec, gen]; decide
theorem grade_kappaSqVec : grade kappaSqVec = 0 := by
  simp [grade_apply, kappaSqVec, gen]; decide

theorem alpha_not_reachable : alphaVec ∉ reachable := by
  rw [mem_reachable_iff, grade_alphaVec]; decide
theorem gammaOne_not_reachable : gammaOneVec ∉ reachable := by
  rw [mem_reachable_iff, grade_gammaOneVec]; decide
theorem sin2W_not_reachable : sin2WVec ∉ reachable := by
  rw [mem_reachable_iff, grade_sin2WVec]; decide
theorem lambdaH_not_reachable : lambdaHVec ∉ reachable := by
  rw [mem_reachable_iff, grade_lambdaHVec]; decide
theorem vcbFactor_not_reachable : vcbFactorVec ∉ reachable := by
  rw [mem_reachable_iff, grade_vcbFactorVec]; decide
/-- Positive control: the published Yukawa constant is produced by the periods. -/
theorem kappaSq_reachable : kappaSqVec ∈ reachable := by
  rw [mem_reachable_iff, grade_kappaSqVec]

end UGCT.Grading
