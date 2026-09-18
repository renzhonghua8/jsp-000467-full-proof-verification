# Independent statement review of the full Erdős 577 proof

Reviewed upstream revision: `plby/lean-proofs` commit
`8822f7ddef30fadbd92e1c6ab4ed897af356af5e`.

Primary mathematical source: Hong Wang, *Proof of the Erdős–Faudree
Conjecture on Quadrilaterals*, Graphs and Combinatorics 26 (2010), 833–877,
Theorem B. DOI: <https://doi.org/10.1007/s00373-010-0948-3>.
Problem statement: <https://www.erdosproblems.com/577>.

## Exact target and independent interpretation

For every natural number k and every finite simple graph G with 4k vertices
and minimum degree at least 2k, the entire vertex set can be partitioned into
k ordinary four-cycles. Chords are permitted. There is no fixed upper bound
on k, additional density assumption, or hypothesis supplying a packing.

`Statement.lean` imports Mathlib only. Its `FourCycleFactor G k` requires:

1. One standard `(SimpleGraph.cycleGraph 4).Copy G` for each `i : Fin k`.
2. Pairwise disjoint vertex ranges for those copies.
3. The union of all those vertex ranges equals the entire vertex set.

The independent `factorOfEmbedding` proves that the public proof's result,
an injective map from `Fin k × Fin 4` with consecutive cyclic edges, entails
all three conditions. Global injectivity ensures four distinct vertices per
cycle and disjointness between cycles. Equality of finite cardinalities
ensures coverage. This also checks k = 0, which is harmless and stronger
than a statement restricted to positive k.

`Bridge.lean` derives this independently stated factor theorem from
`Erdos577.erdos_577`. It also gives the pointwise-degree variant. Its final
two commands expose the actual transitive axioms of these bridge theorems.

## Read-only proof-architecture review

The upstream public main proof handles the empty and four-vertex cases,
then argues by contradiction for the general case:

1. Extend a counterexample to an edge-maximal graph with no C4 factor.
   This exists because the graph has a finite vertex type; adding edges
   cannot decrease any degree.
2. Construct a partition into k−1 four-cycle blocks and four remaining
   vertices, consisting of a triangle and an attached leaf. Optimize two
   finite scores (total edges in the blocks and number of complete blocks).
3. The attachment, exchange, and classification lemmas prove Wang's
   Claims 2.5–2.7 for an arbitrary maximizing configuration.
4. For the leaf x and two triangle vertices a,b, each four-cycle block S
   has weight `2 deg_S(x) + deg_S(a) + deg_S(b) ≤ 8`.
5. The remainder contributes exactly 6 to that weight. The k−1 blocks
   therefore give total weight at most `6 + 8(k−1) = 8k−2`, whereas the
   minimum degree gives total weight at least 8k. This is a contradiction.

The source structures examined (`Packing`, `Saturated`, `TriangleChain`,
`Feasible`, `Strong`) have the advertised mathematical meanings. In
particular `Strong` adds only actual attachment to the two optimization
conditions; it does not assume the final theorem. The main import is
`ErdosProblems.Erdos577.FinalCount`, not the separate comparator challenge
file, which deliberately contains an unfinished benchmark placeholder.

This source reading establishes semantic correspondence. Separately, the
recorded reproduction compiled the whole 851-module transitive proof-source
dependency closure and bridge with Lean 4.33.0 and the pinned Mathlib revision.
It directly traversed the actual endpoint bodies, found exactly `propext`,
`Classical.choice`, and `Quot.sound`, and completed a full imported-environment
`--fresh` kernel replay. The upstream `SOURCE_AUDIT.md` remains historical
context rather than a substitute for these newly observed results.

## Attribution

The full proof is existing public work from `plby/lean-proofs`. This review
and bridge do not confer originality or prize priority on the present user.
The previous k = 1 contribution is not used in the full proof above.
