# Attribution and provenance

## Mathematical proof

Hong Wang, *Proof of the Erdős–Faudree Conjecture on Quadrilaterals*,
Graphs and Combinatorics 26 (2010), 833–877, Theorem B.
DOI: [10.1007/s00373-010-0948-3](https://doi.org/10.1007/s00373-010-0948-3).

The result concerns every finite simple graph on `4k` vertices with minimum
degree at least `2k`, for arbitrary natural `k`. Its conclusion is a
spanning collection of `k` vertex-disjoint ordinary four-cycles.

## Existing complete Lean formalization

The full proof sources belong to the existing development in Boris
Alexeev's [`plby/lean-proofs`](https://github.com/plby/lean-proofs)
repository, not to this review's author.

Reviewed revision: `8822f7ddef30fadbd92e1c6ab4ed897af356af5e`.
Main source: `src/latest/ErdosProblems/Erdos577.lean`.
Main endpoint used by the review: `Erdos577.erdos_577`.

The pinned upstream `PROGRESS.md` and `SOURCE_AUDIT.md` record completion
of the exact theorem on **2026-08-28**. This is an upstream historical
record; it is not a claim that this review independently established the
earliest public timestamp or adjudicated contributor priority. The pinned
snapshot and the retained upstream notices are the provenance evidence.

Retain any additional contributor acknowledgments present in the upstream
sources. Referencing and checking those sources does not transfer their
authorship or create a new license for redistributing them.

## Present review and bridge

Prepared for GitHub account `renzhonghua8`, with Codex assistance.

The present contribution consists of:

- An independent full statement using standard Mathlib four-cycle copies,
  pairwise disjointness, and coverage of every vertex.
- A bridge from the pinned upstream theorem to that statement.
- A review of source dependencies, statement fidelity, and provenance.
- Reproducible full proof-source rebuild evidence when the pending
  verification finishes.

These contributions do not claim authorship of Wang's mathematics or the
upstream full Lean development. They do not claim first formalization,
award priority, official verification, or prize eligibility.

## Correction to the earlier contribution

Our earlier JSP-000467 package established only the `k = 1` case and did
not locate the existing complete formalization during its prior-art
search. The current review corrects that prior-art omission explicitly.
The old base-case package is not evidence of the general theorem and is
not a dependency of the reviewed full proof.

## Verification status

The current full proof-source rebuild and bridge verification are
**pending**. Upstream historical success reports remain attributed to
upstream. Only new commands and results actually observed in this review
may later be added as independent reproduction evidence.

