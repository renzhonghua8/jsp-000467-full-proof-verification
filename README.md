# JSP-000467 / Erdős 577: full-theorem verification review

This package reviews the existing complete Lean proof of the Erdős–Faudree
quadrilateral theorem and connects it to an independently stated conclusion
using standard Mathlib graph copies. It covers every natural number `k`,
including all `k ≥ 2` cases omitted from our earlier four-vertex submission.

**Verification status: pending.** The independent statement and bridge have
been prepared, and the source review is in progress. The full transitive
proof-source rebuild, bridge compilation, and final axiom reports must finish
before this package can report a successful reproduction. Historical upstream
build reports are evidence of prior work, not results of this reproduction.

## Complete mathematical statement

For every natural number `k` and every finite simple graph `G` with exactly
`4k` vertices, if every vertex has degree at least `2k`, then `G` has `k`
pairwise vertex-disjoint cycles of length exactly four. Those cycles cover
every vertex. They are ordinary cycles: additional chords are allowed.

There is no upper bound on `k`, no strict inequality replacing the degree
threshold, and no hypothesis that already supplies the desired packing.
The harmless `k = 0` case is included alongside all positive `k`.

Hong Wang proved the mathematical theorem in *Proof of the Erdős–Faudree
Conjecture on Quadrilaterals*, Graphs and Combinatorics 26 (2010), 833–877,
Theorem B. [Published paper](https://doi.org/10.1007/s00373-010-0948-3).

## Prior work and this package's contribution

The complete Lean proof is existing public work in Boris Alexeev's
[`plby/lean-proofs`](https://github.com/plby/lean-proofs) repository. Its
upstream progress and source-audit documents record completion on
**2026-08-28**. This package retains that attribution. It does not claim a
new mathematical solution, authorship of the existing full Lean proof, or
first-formalization priority.

Our contribution is the independent Mathlib statement, its bridge from the
existing theorem, a source and statement audit, and reproducible evidence
from rebuilding the complete transitive proof-source dependency closure.
The last item remains pending until the recorded checks complete.

The earlier submission proved only `k = 1`. Its prior-art search did not
locate this full public development. The present review corrects that
omission and treats the full development as prior work; it does not relabel
the earlier base case as a proof of the general theorem.

## Pinned sources and environment

| Component | Exact reference |
| --- | --- |
| Upstream proof repository | `https://github.com/plby/lean-proofs` |
| Upstream proof revision | `8822f7ddef30fadbd92e1c6ab4ed897af356af5e` |
| Main upstream source | `src/latest/ErdosProblems/Erdos577.lean` |
| Lean toolchain | `leanprover/lean4:v4.33.0` |
| Mathlib revision | `db584cd6d46c92f209a44c0f1c829460d327499d` |

The [pinned main source](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577.lean)
imports `ErdosProblems.Erdos577.FinalCount`. The rebuild must follow that
module's complete transitive import closure. The separate comparator
challenge is not a proof dependency and must not be substituted for the
actual theorem.

Mathlib and its dependencies must use the matching pinned environment.
Any use of compiled Mathlib caches must be disclosed: rebuilding all
project proof sources does not by itself mean rebuilding Lean, Mathlib,
and every bundled dependency from source.

## Independent conclusion and bridge

`Jsp467FullReview/Statement.lean` imports Mathlib only. It defines a
`FourCycleFactor G k` by requiring:

1. A standard `(SimpleGraph.cycleGraph 4).Copy G` for each index in `Fin k`.
2. Pairwise disjoint vertex ranges for these copies.
3. The union of those ranges to equal the entire vertex set.

It proves that an injective cyclic-edge witness on `Fin k × Fin 4`, together
with the exact vertex count, yields this conclusion. The argument checks
distinctness, disjointness, and coverage instead of relying on the name of
an upstream packing definition.

`Jsp467FullReview/Bridge.lean` imports the pinned full proof and derives:

- `Jsp467FullReview.erdos_faudree_full`, with Mathlib's minimum degree.
- `Jsp467FullReview.erdos_faudree_full_pointwise`, with an explicit degree
  bound for every vertex.

Both statements quantify over arbitrary `k` and arbitrary finite vertex
types. Neither depends on our earlier `k = 1` proof.

## Required verification evidence

Before marking this reproduction complete, retain the exact commands,
source hashes, environment revisions, process exit codes, and complete
logs for:

- Source inventory and the complete transitive project import closure.
- Rebuilding every module in that closure in the pinned environment.
- Compiling the independent statement and both final bridge theorems.
- The actual transitive axiom reports of the upstream endpoint and both
  bridge endpoints; investigate anything beyond `propext`,
  `Classical.choice`, and `Quot.sound`.
- Source review for placeholders, custom axioms, and other mechanisms
  that could bypass the intended theorem.
- Any additional kernel replay actually performed, with its exact module
  targets and imported-environment boundary identified.

Source scans alone do not prove correctness. A completed build alone does
not establish that the formal statement matches the original mathematics.
This package records both kinds of evidence separately.

## Prize and submission status

This is a verification and statement-bridge contribution concerning an
existing full formalization. It is not a first-formalization claim and does
not establish award eligibility or a recipient decision. Any public
submission must retain the original mathematical and formalization credits
and accurately report the completed checks and remaining limitations.

This repository is a verification work in progress. Its existence is not
evidence of a completed build, an official submission, or acceptance.

## Reproduce

With Git, Python 3.9+, and Elan installed, run from this repository:

```sh
bash scripts/fetch_upstream.sh
python3 scripts/source_audit.py --output verification/source-audit.json
lake update
lake exe cache get
LEAN_NUM_THREADS=2 lake build
lake env lean Jsp467FullReview/Audit.lean
```

The proof is fetched unchanged from the pinned original repository into an
ignored directory; no upstream proof source is redistributed here. This
package does not grant a license for the upstream code. Mathlib's matching
compiled cache is used, but every module in the Erdős 577 proof dependency
closure is compiled from source. CI starts without this project's build
cache. A repeat local build may reuse its own previous outputs.

## References

- [Erdős Problem 577](https://www.erdosproblems.com/577).
- [JSP-000467 catalog entry](https://github.com/TheJustinSunPrize/awards/blob/main/problems/catalog-0401-0500.md#jsp-000467).
- [Hong Wang's published paper](https://doi.org/10.1007/s00373-010-0948-3).
- [Pinned complete Lean endpoint](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577.lean).
- [Pinned upstream completion record](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577/PROGRESS.md).
- [Pinned upstream source audit](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577/SOURCE_AUDIT.md).
