# ADR 0001: Package boundaries for redstring-wfm

Status: accepted

## Context

WFM (arXiv 2609.18182) needs a wiki-graph model, a training path and a
retrieval loop. Redstring is a layered library with a binding architecture
contract, a public API gate (`redstring.__all__`), and rules that it never
fetches content and that extraction writes to no store. Putting numerical
code and training into redstring would break those rules and pull NumPy and
optional torch into the core.

## Decision

1. **Placement.** WFM lives in `packages/redstring-wfm` as a separate
   distribution, depending on `redstring>=0.12,<0.13`. In development it uses a
   path source for redstring. Redstring's own layers and contract are not
   changed by this package.

2. **Import boundary.** Only `redstring_wfm.build` may import `redstring`. Every
   other module works on WFM-owned types: `WikiNode`, `WikiEdge`, `Passage`,
   `WikiGraph`, which hold ids, text, embeddings and kinds. Enforced by an
   import-linter contract and a test that parses the package. The builder is
   the only anti-corruption translator.

3. **No store port.** `WikiGraph` is a derived read model. It is built in
   memory from `GraphStore` and `ChunkStore` reads for each query. Redstring
   ADR 0042 treats derived structures as recomputed, not stored, and the same
   reasoning applies here. A port is added only when a second consumer needs
   persistence, and that decision gets its own ADR.

4. **Persistence.** Only trained parameters persist, as an `.npz` checkpoint
   written by the package. Parameters are the one piece of state that cannot be
   recomputed from the graph. Entity lookup tables are keyed by `EntityId`;
   a checkpoint therefore records the id space it was trained on, and loading
   against a graph whose ids have changed (merges, per-run `uuid5`) is an
   explicit error until a remapping policy exists (BACKLOG).

5. **Writes.** The package writes nothing to redstring stores. It reads through
   the public ports only, and never fetches content. Redstring's rule that
   extraction writes no store, and that projections do the writing, is kept.

6. **Tenancy.** `build` takes a `tenant_id`, and every read carries it. Tests
   use two tenants whose ids collide, so a key compared on id alone fails.

7. **Passages are chunks.** A passage is a caller-supplied `StoredChunk`
   seen through the builder. No LLM-generated pages. The paper's graph has
   two edge families, entity-relation and entity-passage, and chunks supply the
   second.

8. **Embeddings.** Passage and query embeddings come from the caller, through
   redstring's existing `EmbeddingProvider`. No new `TextEncoder` port.

## Consequences

- `redstring` is only a dependency of the builder. The model, losses,
  curriculum and loop are testable without a store.
- The contract test fails if any other module imports redstring.
- Adding a store port later means a new ADR, not an edit here.
- Redstring needs no upstream change for the builder, except exporting
  `reciprocal_rank_fusion` (see `docs/plan.md`).

## Glossary

- **Wiki graph**: the `WikiGraph` built for one tenant at one time.
- **Passage**: a chunk linked to one or more entities.
- **Seed**: an entity or passage hit that starts induced-subgraph retrieval.
- **Round**: one retrieval-generation iteration of the reflection loop, indexed t.
- **Budget**: the maximum number of rounds B.
- **Final flag**: the generator's per-round signal that evidence is sufficient.
- **Evidence policy**: GROUNDED (Reject, evidence only, abstention allowed) or
  OPEN (may also use parametric knowledge). A generator setting, not a loop state.
