# ADR 0002: Assumptions where the WFM paper is silent or inconsistent

Status: accepted; A7 amended by ADR 0004. Every item below is an assumption of this implementation,
**not** a paper result, and each is a candidate for ablation.

## Context

An independent review (paper text checked against Eq 1-13 and §3-4) found that
the earlier plan misread two parts of the paper and filled several gaps
silently. This ADR records the corrected reading and every remaining fill.

## Corrected readings (from the paper)

- **W_v applies to the neighbour state.** In the message `m_v = Σ α(v,r,u)
  (W_v h_u + e_r)` (Eq 5), W_v multiplies `h_u`, the neighbour's state at layer
  l-1. Text enters once, at layer 0, through `W_p`. Entities start from a
  trainable lookup table `e_e`, not from text.
- **Reject and Open are evaluation modes.** The paper defines them as the
  generator's evidence policy (§4.1): Reject uses only retrieved evidence and
  abstains when it is insufficient; Open also allows parametric knowledge. The
  reflection loop is controlled only by the per-round Final flag and the budget
  B, and returns `a^(B)` when the budget runs out.
- **Cosine similarity is the paper's.** Eq 10 defines `sim` as cosine, and Eq 7
  reuses it. It is cited, not assumed.
- **Depth.** The default is L = 3 attentive layers (§4 setup).

## Assumptions (not paper-derived)

| # | Item | Assumption | Why |
|---|---|---|---|
| A1 | W_v | Trainable d×d matrix per layer, applied to h_u | Eq 5 forces d×d; per-layer is the default; the paper does not say whether layers share weights |
| A2 | Weight sharing across layers | Not shared | Paper silent; ablate |
| A3 | Query width | Eq 7 compares `T(q)` (width d_t) with `h^(L)` (width d). Apply `W_p` to the query so both have width d | Paper silent on the mismatch |
| A4 | Ranking scope | TopK over passages in the induced subgraph | Eq 7 ranks over all of D, but only subgraph passages have propagated states |
| A5 | Seeds | RRF over entity hits and passage hits, with RRF_K = 60 | §3.2 says retrieval "identifies seed entities and passages". The paper seeds both kinds, so no mapping of passage hits to entities is applied |
| A6 | Subgraph radius | L hops (default 3) over the bipartite entity–passage and entity–entity graph | §3.2 implies deeper layers need a radius at least L; a smaller radius wastes layers |
| A7 | Max-nodes cap M | Amended by ADR 0004: default 200, swept in slice 6 | Paper gives no cap; hub nodes can explode the subgraph |
| A8 | Re-induction | Seeds and subgraph are recomputed per round from the round's query | Eq 7 indexes by q(t) |
| A9 | Evidence | `C(t) = C(t-1) ∪ D(t)`, accumulated across rounds | §3.3 |
| A10 | Generator query | The generator receives the original `q`, not `q(t)` | §3.3 |
| A11 | Reverse edges | Messages flow along both directions of each relation | Paper silent on direction; Eq 1 is written from the source side only |
| A12 | Link types | One entity–passage link type. "Described" vs "mentioned" (§3.1) is not expressible with `StoredChunk.entity_ids` | Redstring has one link type; ablate if needed |
| A13 | Passage update | Passages are updated by Eq 6 like entities | §3.2 says both are updated; the update rule is written for entities |
| A14 | Unseen entities | Zero-initialised lookup rows, flagged. The zero-shot claim holds for passages (through `W_p`) but not entities | Lookup tables are transductive; §3.1 vs Def. 1 disagree |
| A15 | Phase II switch | Fixed epoch count, chosen on the synthetic regression set | §3.4 gives no switch schedule |
| A16 | Loss constants | γ, τ, λ1, λ3 are hyperparameters with defaults chosen on synthetic data | Paper lists them without values |
| A17 | Variance hinge | Applied to logits π, not to α | Eq 9 as written |
| A18 | TransE | Tail corruption only, L2 distance, on propagated h_e | Eq 10-11 as written |
| A19 | Padding | Padding positions are excluded from the softmax neighbourhood | Needed for the CPU partition equivalence test (§3.5) |

Paper defaults used unchanged: L = 3, ε = 0.05, λ2 = 0.1, k = 20, B = 4
(§4 setup, l.724). The paper says the defaults for the diagnostic sweeps are
"constructed planning values and require validation". They are therefore
treated as starting points, not targets (see plan.md).

## Consequences

- Each A-item needs a test or an ablation that would reveal a wrong choice.
- No paper figure becomes a regression target. Synthetic regression uses
  measured outputs of this implementation.
- Changing any A-item later is a new ADR, not an edit.
