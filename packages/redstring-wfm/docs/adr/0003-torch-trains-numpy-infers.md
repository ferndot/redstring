# ADR 0003: Torch trains, NumPy infers

Status: accepted. Resolves the training-backend question in `docs/plan.md`
and BACKLOG W1. Amends the plan's original "NumPy core, optional torch
trainer last" (decision 2 in the plan's table).

## Context

Slices 5-6 need gradients for the three losses and the curriculum. NumPy has
no autograd, so the choices were hand-derived backward passes for Eq 3-6 and
the losses, or torch autograd for training.

## Decision

- **Training uses torch** (autograd). The losses and both curriculum phases
  are implemented against torch.
- **Inference uses NumPy.** The forward pass of Eq 3-6 is written in NumPy and
  is the reference implementation. It is the oracle the torch forward is checked
  against, and it is what the reflection loop calls at query time.
- Torch lives in its own optional extra and is not imported on the default
  path. A NumPy-only install can load a checkpoint and run inference.

## Consequences

- The torch and NumPy forward passes must agree. A test loads the same
  parameters into both and compares outputs to a stated tolerance. This is the
  one place a tolerance is allowed; slice 9's bit-exact partition check is
  separate.
- Gradients are checked against torch's own autograd only for the torch path.
  The NumPy oracle does not need gradients, which removes the hand-derivation
  burden the NumPy-only option carried.
- Adds a heavy optional dependency. It stays out of the default import path, so
  `import redstring_wfm` works without torch.
- Changes slice 5 and 10 in `docs/plan.md`: slice 10 (the optional torch
  trainer) is no longer optional; it is the training path.
