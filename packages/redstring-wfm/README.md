# redstring-wfm

Wiki Foundation Model (arXiv 2609.18182) retrieval over a
[redstring](../../README.md) knowledge graph.

- Plan: [`docs/plan.md`](docs/plan.md)
- Decisions: [`docs/adr/`](docs/adr/)
- Deferred work: [`BACKLOG.md`](BACKLOG.md)

Only `redstring_wfm.build` imports `redstring`; the rest of the package works on
its own types (ADR 0001).

Run the tests from this directory:

    uv run pytest
