# JSP-000467 / Erdős 577: full-theorem verification review

This package reviews the existing complete Lean proof of the Erdős–Faudree
quadrilateral theorem and connects it to an independently stated conclusion
using standard Mathlib graph copies. It covers every natural number `k`,
including all `k ≥ 2` cases omitted from our earlier four-vertex submission.

**Verification status: passed for checked commit
`90eb2ad461ee23d9843b8972fc4a48ac9e566f62`.** GitHub Actions
[run 35226375007](https://github.com/renzhonghua8/jsp-000467-full-proof-verification/actions/runs/35226375007)
freshly compiled all 851 modules in the pinned proof-source closure and the
independent bridge. It then completed both direct constant-body axiom audits
and a full `--fresh` replay of the imported environment in Lean's kernel.
The job and audit command exited successfully.

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
The recorded reproduction completed successfully on 2026-09-17 UTC.

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

## Recorded verification evidence

The evidence retains the exact commands, source hashes, environment revisions,
process exit codes, and complete log for:

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

The successful run checked these exact records:

| Record | Result |
| --- | --- |
| Review repository commit | `90eb2ad461ee23d9843b8972fc4a48ac9e566f62` |
| Pinned upstream commit | `8822f7ddef30fadbd92e1c6ab4ed897af356af5e` |
| Source closure | 851 modules; 851 unique fresh build records; no missing or duplicate module |
| Source-audit SHA-256 | `b0b0fbbcbfd9255683e3b68b144374e4ade5900b1d27c6f08bfc7e1ce438a5b2` |
| CI log SHA-256 | `1310b30b4309d33a36a6e574dd08757f758259d8ad93b0a8ffc699a5922e05c7` |
| Evidence bundle | [`v1.0.0` archive](https://github.com/renzhonghua8/jsp-000467-full-proof-verification/releases/download/v1.0.0/jsp-000467-full-proof-verification-evidence-v1.0.0.tar.gz); 152,430 bytes; SHA-256 `85921e9051778d4a512a29fa840e029eaf946b0413d12c1c940fe133e9c7bfed` |
| Direct axiom-body audit | All three endpoints contain exactly `propext`, `Classical.choice`, and `Quot.sound`; no disallowed axiom |
| Full kernel replay | `leanchecker --fresh --verbose Jsp467FullReview.Bridge`; pass; exit status 0 |
| Replay boundary | All transitive imports loaded for the bridge were replayed into an empty environment by the same Lean 4.33.0 kernel |

Matching compiled Mathlib caches supplied stored terms. The replay rechecked
those loaded mathematical declarations, but this is not a claim that Mathlib
was compiled from source or that a separately implemented kernel was used.

## Prize and submission status

This is a verification and statement-bridge contribution concerning an
existing full formalization. It is not a first-formalization claim and does
not establish award eligibility or a recipient decision. Any public
submission must retain the original mathematical and formalization credits
and accurately report the completed checks and remaining limitations.

This repository records a completed technical reproduction for the exact
commit and run above. It does not constitute official Prize verification,
acceptance, recipient confirmation, or an award decision.

## Reproduce

With Git, Python 3.9+, and Elan installed, run from this repository:

```sh
bash scripts/fetch_upstream.sh
python3 scripts/source_audit.py --output verification/source-audit.json
lake exe cache get
LEAN_NUM_THREADS=1 lake build
lake env lean Jsp467FullReview/Audit.lean
bash scripts/kernel_audit.sh . "$(lean --print-prefix)/bin" verification/kernel
```

The proof is fetched unchanged from the pinned original repository into an
ignored directory; no upstream proof source is redistributed here. This
package does not grant a license for the upstream code. Mathlib's matching
compiled cache is used, but the reproduction is configured to compile every
module in the Erdős 577 proof dependency closure from source. CI starts without
this project's build cache. A repeat local build may reuse its own previous outputs.

CI compiles the same source closure in six deterministic topological stages
(`python3 scripts/build_stage.py --stage 1` through `--stage 6`), followed by
the independent bridge. This exposes intermediate progress without omitting
any proof dependency. Lake uses one normal scheduling worker and each Lean
compiler is limited to two threads via `weakLeanArgs`.

The first complete-source CI attempt compiled 66 proof modules before receiving
a termination signal (exit 143); its overall status is cancelled, not passed.
No mathematical error was reported before termination. It is not evidence of
a complete verification.

Run [35203111492](https://github.com/renzhonghua8/jsp-000467-full-proof-verification/actions/runs/35203111492)
subsequently completed all six proof-source stages, the independent bridge,
and the axiom-printing step. GitHub then cancelled the job at its four-hour
limit during the additional full imported-environment replay. That replay
had about 51 minutes available and did not finish; no replay success or direct
axiom-body audit result is claimed from this run.

The replacement [run 35226375007](https://github.com/renzhonghua8/jsp-000467-full-proof-verification/actions/runs/35226375007)
used a six-hour job budget while preserving the same theorem statements,
source pins, and full `--fresh` checker scope. It completed all six stages,
the bridge, axiom printing, direct constant-body inspection, and full replay
successfully. The audit took 2:01:54 wall time, used at most 8,764,992 KiB
resident memory for the combined audit command, and exited with status 0.

## References

- [Erdős Problem 577](https://www.erdosproblems.com/577).
- [JSP-000467 catalog entry](https://github.com/TheJustinSunPrize/awards/blob/main/problems/catalog-0401-0500.md#jsp-000467).
- [Hong Wang's published paper](https://doi.org/10.1007/s00373-010-0948-3).
- [Pinned complete Lean endpoint](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577.lean).
- [Pinned upstream completion record](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577/PROGRESS.md).
- [Pinned upstream source audit](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos577/SOURCE_AUDIT.md).
