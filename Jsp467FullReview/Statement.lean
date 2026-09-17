import Mathlib.Combinatorics.SimpleGraph.CycleGraph
import Mathlib.Combinatorics.SimpleGraph.Finite

/-!
# An independent statement of the full Erdős--Faudree theorem

This file imports Mathlib only. It does not use any definitions from the
formalization being reviewed. A factor consists of ordinary Mathlib copies
of `cycleGraph 4`, with pairwise disjoint vertex sets covering the graph.
-/

namespace Jsp467FullReview

variable {V : Type*}

/-- Exactly `k` ordinary four-cycles, vertex disjoint and spanning all vertices. -/
structure FourCycleFactor (G : SimpleGraph V) (k : ℕ) where
  cycles : Fin k → (SimpleGraph.cycleGraph 4).Copy G
  vertex_disjoint : Pairwise fun i j ↦
    Disjoint (Set.range (cycles i)) (Set.range (cycles j))
  covers : (⋃ i, Set.range (cycles i)) = Set.univ

/-- The independently defined complete conclusion. -/
def HasFourCycleFactor (G : SimpleGraph V) (k : ℕ) : Prop :=
  Nonempty (FourCycleFactor G k)

/-- Cyclic edges on four different vertices give a standard Mathlib graph copy. -/
def fourCycleOfEdges (G : SimpleGraph V) (f : Fin 4 ↪ V)
    (hadj : ∀ j, G.Adj (f j) (f (j + 1))) :
    (SimpleGraph.cycleGraph 4).Copy G where
  toHom := {
    toFun := f
    map_rel' := by
      intro i j hij
      rw [SimpleGraph.cycleGraph_adj] at hij
      simp only [sub_eq_iff_eq_add'] at hij
      rcases hij with hij | hij
      · subst i
        exact (hadj j).symm
      · subst j
        exact hadj i }
  injective' := f.injective

/-- A product-indexed injective cyclic witness implies the full standard factor.
The equal cardinalities are used to prove that the cycles cover every vertex. -/
noncomputable def factorOfEmbedding [Fintype V] (G : SimpleGraph V) (k : ℕ)
    (hcard : Fintype.card V = 4 * k) (f : Fin k × Fin 4 ↪ V)
    (hadj : ∀ i j, G.Adj (f (i, j)) (f (i, j + 1))) : FourCycleFactor G k := by
  classical
  let q : Fin k → (SimpleGraph.cycleGraph 4).Copy G := fun i ↦
    fourCycleOfEdges G {
      toFun := fun j ↦ f (i, j)
      inj' := fun a b h ↦ (Prod.mk.inj (f.injective h)).2 } (hadj i)
  have hsurj : Function.Surjective f := by
    by_contra hnot
    have hlt := Fintype.card_lt_of_injective_not_surjective f f.injective hnot
    simp [hcard, Nat.mul_comm] at hlt
  refine ⟨q, ?_, ?_⟩
  · intro i j hij
    apply Set.disjoint_left.mpr
    intro v hi hj
    obtain ⟨a, ha⟩ := hi
    obtain ⟨b, hb⟩ := hj
    have he : f (i, a) = f (j, b) := ha.trans hb.symm
    exact hij (Prod.mk.inj (f.injective he)).1
  · apply Set.eq_univ_of_forall
    intro v
    obtain ⟨⟨i, j⟩, hv⟩ := hsurj v
    exact Set.mem_iUnion.mpr ⟨i, ⟨j, hv⟩⟩

end Jsp467FullReview
