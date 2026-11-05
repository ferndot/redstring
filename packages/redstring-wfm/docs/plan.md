# redstring-wfm: implementation plan

Status: revised after three subagent reviews and one independent review of
their findings (see `adr/0001` and `adr/0002`). Supersedes the plan presented
on 2026-11-05.

Source paper: arXiv 2609.18182, "Wiki Foundation Model for Complex Agentic
Reasoning" (Tencent Youtu Lab). Paper line numbers below refer to the
extracted text of that paper.

## Scope

Implement WFM's wiki-graph retrieval over a redstring knowledge graph:
an attentive graph model (Eq 3-6), the three losses (Eq 9-12), the
two-phase curriculum, seed selection and induced-subgraph retrieval (Eq 7),
and the self-reflection loop (Eq 8). Evaluate directionally against the
paper's ablations.

## Decisions in force

| Decision | Choice | Record |
|---|---|---|
| Placement | `packages/redstring-wfm`, depends on `redstring>=0.12,<0.13` | adr/0001 |
| Import boundary | Only `redstring_wfm.build` imports redstring | adr/0001 |
| Store port | None. `WikiGraph` is built in memory per query | adr/0001 |
| Persistence | Model parameters only, as an `.npz` checkpoint | adr/0001 |
| Passages | Caller-supplied `StoredChunk`s, linked to entities | adr/0001 |
| W_v | Trainable d×d value projection per layer, applied to neighbour state h_u | adr/0002 |
| Reflection | Loop returns answer, Final flag, round count, accumulated evidence. Reject/Open is a generator evidence policy, not a loop state | adr/0002 |
| Time | Dropped from v1 (paper has no temporal component; edges carry no time) | adr/0002 |
| Retraction | Not implemented. Known input limit (BACKLOG B32) | adr/0002 |
| Training backend | Torch trains (autograd); NumPy does inference and is the oracle | adr/0003 |
| Max-nodes cap | M = 200, nearest-seed truncation, ties by id, counted; swept in slice 6 | adr/0004 |

The max-nodes cap is decided provisionally (ADR 0004: M = 200, deterministic truncation, counted); slice 6 sweeps it.

## Slices

Each slice is one PR. Commits within a slice stay small.

0. **Scaffold and boundaries.** Package skeleton, `pyproject.toml`, import
   contract test, ADR-0001 and ADR-0002, this plan, BACKLOG entries.
1. **Domain value objects.** `WikiNode`, `WikiEdge`, `Passage`, `WikiGraph`
   as frozen dataclasses holding only ids, text, embeddings and kinds. No
   redstring types. Tests pin values, not just construction.
2. **Builder (the only translator).** Reads a tenant's entities, relationships
   and chunks through `GraphStore` and `ChunkStore` read methods and produces
   a `WikiGraph`. Passage embeddings come from a caller-supplied
   `EmbeddingProvider`. Tests use two tenants with colliding ids
   (`(tenant_id, id)` keying) and assert each read path is tenant-scoped.
3. **Layer-0 states and attention forward pass (NumPy).** Entity lookup
   table, `W_p` for passages, Eq 3-6 propagation with `W_v` on h_u, per-layer
   parameters. Oracles: a hand-computed 3-node case, a loop reference against
   the vectorised code, and a padding-exclusion test (padding must not enter
   the softmax).
4. **Seeds and induced subgraph.** Seeds from RRF over entity hits and
   passage hits. Induced subgraph of radius L (default 3) with a max-nodes
   cap, re-induced per reflection round. Oracles: a diamond-shaped graph
   (shortest path, not first-found), and a case where a passage is reachable
   only through a second hop.
5. **Losses and training path (torch).** `L_align` (InfoNCE, cosine, τ), `L_TransE`
   (tail corruption only, L2, on propagated h_e), `L_var` (hinge over logits
   π against ε), weight decay λ3. Forward parity with the NumPy reference
   checked to a stated tolerance (ADR 0003).
6. **Two-phase curriculum and synthetic multi-hop regression.** Phase I
   trains `W_p` and lookup tables under `L_align` on layer-0 states. Phase II
   unfreezes everything. Synthetic graphs with known multi-hop answers. Runs
   the ablations the paper reports (no L_var, cold start, DistMult aggregator,
   no reflection, no final flag). Directional only: no paper figure becomes
   a regression target.
7. **Reflection loop.** Pure policy for the Final flag. Orchestrator with
   budget B (default 4) that accumulates evidence `C(t) = C(t-1) ∪ D(t)`,
   re-induces the subgraph each round, and passes the original `q` to the
   generator. `ReflectionOutcome` is a frozen value object: answer, final
   flag, rounds executed, budget-exhausted flag, evidence. The
   `EvidencePolicy` (GROUNDED for Reject, OPEN) is configured on the
   generator; under GROUNDED an abstaining answer is valid.
8. **Evaluation harness.** Recall@{2,5,10,20} and LLM-judged accuracy in
   both evidence policies. Keeps the paper's ablation set. Reports raw
   measured numbers only.
9. **CPU partition equivalence.** Partitioned and unpartitioned runs must
   agree. Summation order is fixed so the result is bit-exact; a tolerance is
   used only where bit-exactness is impossible, and that exception is written
   down.
10. **Torch training path is complete.** Per ADR 0003 this is the training
    path, not an optional extra. Lives in its own extra, off the default import path.

## Upstream redstring changes

Needed before the dependent slices:

- **Export `reciprocal_rank_fusion` and `RRF_K` from top-level
  `redstring.__all__`.** Currently only the module-level `__all__` in
  `domain/fusion.py` carries them, which is an internal path. Until a
  redstring release ships this, slice 4 uses a local copy of the three-line
  formula, marked with a BACKLOG entry to delete it.
- **Stale-entity retraction (B32).** Not needed. Recorded as a known limit.
- **Hop-distance `neighbors`.** Not needed. Radius is computed client-side:
  BFS over `get_relationships_for`, with passage hops through
  `ChunkReader.get_by_entity`.

## Out of scope for v1

NCCL backend; foundation-model pretraining; reproducing the paper's tables;
markdown or LLM-generated wiki pages; temporal extents; retraction;
persistence of the graph (parameters only); unseen-entity zero-shot for
entities (passages are zero-shot via `W_p`; entities are not).
