# redstring-wfm backlog

Deferred work for this package. Redstring defects found along the way are in
the root `BACKLOG.md` (B166, B167). Each entry says what is deferred and why.

## Blocking a slice

### W1. The training backend is undecided (blocks slice 5)

Slices 5-6 need gradients. NumPy has no autograd, so the choice is (a)
hand-derived backward passes for Eq 3-6 and the losses, checked against finite
differences, or (b) torch for training, with NumPy kept as the inference
reference. The earlier plan put the optimiser last, so the losses had nothing to
optimise until slice 11. Decide before slice 5 starts. See `docs/plan.md`.

### W2. The max-nodes cap M has no value (set in slice 6)

ADR 0002 A7. The paper gives no cap and hub entities can explode the induced
subgraph. The value is chosen empirically on the synthetic regression set, and
the choice is recorded with its measurements, not claimed from the paper.

## Temporary code to remove

### W3. Local copy of reciprocal rank fusion (remove when root B167 ships)

Slice 4 uses a local copy of the three-line RRF formula, because redstring does
not export `reciprocal_rank_fusion` from its top-level API. Delete the copy and
import the public function once B167 lands in a redstring release. The copy must
use the same `RRF_K = 60` so the two cannot drift silently; a test should compare
them while both exist.

### W4. The version pin cannot receive new upstream API in a minor release

`redstring>=0.12,<0.13` cannot pick up a public addition made in the 0.12 line
unless it ships as a patch release. Development uses a path source to the
repository's own redstring. Whether `redstring` 0.12.0 is published to the index
was not verified. Before any release of this package, confirm the pin resolves
from the index without the path source.

## Persistence

### W5. Checkpoints have no remapping policy for re-keyed entity ids

ADR 0001 point 4. Entity lookup tables are keyed by `EntityId`, and ids are
`uuid5` per extraction run. After a merge or a re-extraction, a checkpoint trained
on the old ids refers to entities that no longer exist, and a new entity has no
row. v1 raises an explicit error when the id space differs. A remapping policy
needs the merge history, which is part of the redstring consolidation log, and
is deferred until a caller needs to load a checkpoint across a merge.

## Out of scope for v1 (recorded so they are not rediscovered)

### W6. NCCL backend

The paper's distributed training. v1 supplies a CPU stand-in whose contract is
partition equivalence (slice 9), not a GPU backend.

### W7. Foundation-model pretraining

Out of scope. The paper's pretrained encoder is used as an input, not reproduced.

### W8. Reproducing the paper's tables

Not attempted. §4.4 states that the newly completed cells and diagnostic sweeps
are "constructed planning values and require validation". No paper figure becomes
a regression target. Results are reported as measured here.

### W9. Markdown and LLM-generated wiki pages

Passages are caller-supplied chunks (ADR 0001, point 7). The paper's graph uses
chunks, so nothing in its math needs generated pages.

### W10. Temporal extents

Dropped from v1. The paper has no temporal component, and redstring's edges carry
no time. Revisit only if a use case needs time, with its own ADR.

### W11. Stale-entity retraction

Not implemented. Root BACKLOG B32 records the redstring limit. A graph that only
grows is the accepted input for v1.

### W12. Zero-shot entities

ADR 0002 A14. Passages are zero-shot through `W_p`. Entities are not, because their
lookup rows are trained. A policy for unseen entities is deferred until the
synthetic evaluation shows whether zero-initialised rows hurt.

### W13. Ablations of the paper's structural choices

Reverse edges (A11), link types (A12), and weight sharing across layers (A2) are
fixed by ADR 0002 and not varied in v1. Each needs an ablation before its choice is
claimed to matter.

### W14. The optional torch trainer

Only relevant if W1 resolves to (b), and then only as its own extra and slice. Not on
the default import path.

### W15. This package's tests are not run by CI

The root CI `pytest` job runs the root `tests/` tree. `packages/redstring-wfm/tests`
is run only by hand with `uv run pytest` from that directory, so a regression here
can land green. Wire a CI job, or a root `pytest` path, before the first slice that
ships behaviour. Slice 0 adds only the import-boundary test.
