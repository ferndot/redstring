# redstring-wfm: handoff

On `main` and on `claude/wfm-system-implementation-0aa7f4-bln9hn`, which are at the same commit. Everything is pushed.
Read in this order: `docs/plan.md`, then `docs/adr/0001`–`0004`, then `BACKLOG.md`.

## Where things stand

Slice 0 (scaffold, ADRs, plan) and slice 1 (`WikiGraph` value objects) are done.
Slice 2 (the builder) is next and has not started.

| Commit | What |
|---|---|
| `b417651` | Plan, ADR 0001 (boundaries), ADR 0002 (paper-gap assumptions), backlogs |
| `084dfed` | The mypy typing fix in `constrained.py` **and** the package scaffold, in one commit. Its message describes only the typing fix. Accepted as-is; history not rewritten. |
| `7074329` | Large-file hook limit raised to 1024 KB, for the tracked root lock |
| `fa9a017` | Root `uv.lock` tracked (was gitignored) |
| `0c142ea` | Package `uv.lock` tracked |
| `db1877a` | ADR 0003: torch trains, NumPy infers |
| `3da1330` | Slice 1: `WikiNode`, `WikiEdge`, `WikiGraph` (frozen, self-validating) |
| `f5179e9` | ADR 0004: provisional max-nodes cap M = 200 |

Tests: `cd packages/redstring-wfm && uv run pytest` — 20 pass. The package's tests
are not run by root CI yet (backlog W15).

## Decisions in force

- **Placement.** `packages/redstring-wfm`, a standalone uv project, *not* in the root
  workspace. Depends on `redstring>=0.12,<0.13` via a path source in development.
- **Import boundary (ADR 0001).** Only `redstring_wfm.build` imports `redstring`.
  Enforced by `tests/unit/test_import_boundary.py`, which was broken on purpose and restored.
- **No store port.** `WikiGraph` is derived, built in memory per query. Only trained
  parameters persist, as an `.npz` checkpoint (not yet built).
- **Training (ADR 0003).** Torch autograd trains; NumPy does inference and is the oracle
  the torch forward is checked against, to a stated tolerance. Torch sits in its own extra.
- **Paper corrections (ADR 0002).** `W_v` multiplies the *neighbour* state `h_u` (Eq 5),
  not a text embedding. Reject/Open are evaluation modes, not loop states. Text enters once,
  through `W_p` at layer 0.
- **Assumptions (ADR 0002, A1–A19).** Each is a flagged choice the paper does not make.
  Changing one needs a new ADR.
- **Max-nodes cap (ADR 0004).** M = 200, provisional. Truncation keeps nodes nearest the
  seeds, ties broken by id, and is counted. Slice 6 sweeps 50 / 200 / 1000.
- **Passages** are caller-supplied `StoredChunk`s linked to entities. No generated pages.
- **Out of scope for v1:** temporal extents, stale-entity retraction (redstring B32),
  a graph store port, NCCL, pretraining, reproducing the paper's tables. See package
  `BACKLOG.md` W6–W13.

## Next: slice 2, the builder

The only module that imports redstring. It should:

- read a tenant's entities, relationships and chunks through the `GraphStore` and
  `ChunkStore` read methods (`get_relationships_for`, `ChunkReader.get_by_entity`, etc.);
- take passage embeddings from a caller-supplied redstring `EmbeddingProvider`
  (no new `TextEncoder` port, per the reviews);
- produce a `WikiGraph`, with `tenant_id` set from the caller;
- **test tenancy**: two tenants whose node ids collide, so an implementation keying on
  id alone fails;
- pin the translation with literal expected values, not values computed by the builder.

Watch for: `EntityId`/`ChunkId` are redstring `NewType`s and must become plain `str` in
WFM types. Chunk `entity_ids` may name absorbed ids after a merge (redstring B166) — the
builder should not assume they are canonical until B166 is resolved.

## Open items

- **Slice 4 owes** the truncation counter and deterministic truncation (ADR 0004), plus a
  local RRF copy until redstring exports `reciprocal_rank_fusion` (root B167; package W3).
- **Slice 6** sweeps M and resolves the paper-gap assumptions it can measure.
- **Upstream:** redstring B166 (merge-stale chunk entity ids) and B167 (RRF not exported).
- **Package tests not in CI** (W15). Wire before any slice ships behaviour.
- **Pin:** `redstring>=0.12,<0.13` cannot receive new upstream API in a minor release
  (W4). Confirm it resolves from the index before any release.
- **Checkpoints** have no remapping policy for re-keyed entity ids (W5).

## Repo gotchas learned the hard way

- **Install the hook in any fresh clone:** `uv sync --all-extras && uv run pre-commit install`.
  Without it, every commit passes silently.
- **mypy checks all of `src/`** whenever a Python file is committed, so one unrelated
  type error blocks every Python commit. The root lock now pins pydantic 2.14.x.
- **Hooks can rewrite files and block the commit** (ruff format, ruff fix). Re-`git add`
  and commit again. Check `git diff --cached` before committing: `git commit` takes
  *everything* staged, which is how `084dfed` got two changes.
- **Large-file limit is 1024 KB.** Keep `uv.lock` files under it; a larger lock needs a
  deliberate limit change, not a bypass.
- **Commit messages carry no model identifier**, per the session rules. The
  `Claude-Session:` trailer is kept.
- **No `--no-verify`.** The one history rewrite requested (splitting `084dfed`) was denied
  and not repeated; that commit stays as it is.
