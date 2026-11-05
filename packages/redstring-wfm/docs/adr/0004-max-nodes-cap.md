# ADR 0004: The induced subgraph has a max-nodes cap of 200

Status: accepted. Amends ADR 0002, item A7 (which left the value to slice 6).
The default is provisional: slice 6 sweeps it, and the sweep may replace it.

## Context

The induced subgraph around the seeds (A6, radius L) can grow large when a
hub entity is reached. The paper gives no cap, and its parameter sweeps (Fig 3)
cover depth, budget and the variance threshold, not subgraph size.

## Decision

1. **Default cap M = 200 nodes**, counting entities and passages together.
   Retrieval depth is k = 20 and the model has L = 3 layers; 200 leaves room for
   each layer without letting one hub pull in most of a graph. This is a
   judgement, not a measurement.
2. **Deterministic truncation.** When the cap binds, keep the nodes nearest the
   seeds by hop distance, breaking ties by node id. Truncation must not depend on
   iteration order, or the CPU partition-equivalence check (slice 9) cannot be
   bit-exact.
3. **Count truncations.** The builder reports how many subgraphs hit the cap.
   A test asserts the counter is non-zero on an input that must truncate, so a cap
   that never fires cannot pass as a working one.
4. **Sweep in slice 6.** Compare M = 50, 200 and 1000 on the synthetic regression
   set. Any reported result states the M used and its truncation rate.

## Consequences

- The cap is a tunable with a stated default, not a hidden constant.
- If the sweep shows 200 is wrong, the default changes by a new ADR, not an edit.
- Without the cap, the induced subgraph is unbounded on hub-heavy graphs; the
  alternative (no cap, with a size limit in the builder alone) was rejected
  because it hides the cost from the results.
