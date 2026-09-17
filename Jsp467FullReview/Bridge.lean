import Jsp467FullReview.Statement
import ErdosProblems.Erdos577

/-!
# Bridge from the reviewed full proof to an independently stated conclusion

The source proof is public prior work by the contributors to `plby/lean-proofs`.
This bridge is an independent statement check, not a claim of authorship of
that proof. It must be compiled with the source's full dependency closure.
-/

namespace Jsp467FullReview

/-- Full arbitrary-`k` theorem: standard Mathlib four-cycle copies form a factor. -/
theorem erdos_faudree_full {V : Type*} [Fintype V] (G : SimpleGraph V)
    [DecidableRel G.Adj] (k : ℕ) (hcard : Fintype.card V = 4 * k)
    (hdegree : 2 * k ≤ G.minDegree) : HasFourCycleFactor G k := by
  obtain ⟨f, hf⟩ := Erdos577.erdos_577 G k hcard hdegree
  exact ⟨factorOfEmbedding G k hcard f hf⟩

/-- Equivalent pointwise degree hypotheses, with no lower bound on `k` omitted. -/
theorem erdos_faudree_full_pointwise {V : Type*} [Fintype V] (G : SimpleGraph V)
    [DecidableRel G.Adj] (k : ℕ) (hcard : Fintype.card V = 4 * k)
    (hdegree : ∀ v, 2 * k ≤ G.degree v) : HasFourCycleFactor G k := by
  obtain ⟨f, hf⟩ := Erdos577.exists_disjoint_four_cycles G k hcard hdegree
  exact ⟨factorOfEmbedding G k hcard f hf⟩

#print axioms erdos_faudree_full
#print axioms erdos_faudree_full_pointwise

end Jsp467FullReview
