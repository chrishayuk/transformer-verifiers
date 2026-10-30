# Trust-boundary analysis

The question for every verdict is: what has to be trusted for it to mean anything, and could the thing being checked
have influenced that?

## Principle

**The independent checker must not get its expected outputs or its numerical semantics only from LARQL.** It may
receive *from* LARQL only:

- the artefacts under test (encoded packs, logit dumps, run records)
- LARQL's *claims* about those artefacts

It must not receive:

- expected values
- reference dequantizers
- tolerance choices
- ideas of what "correct" means

## What is trusted and why

| Component | Role | Trusted? | Notes |
|---|---|---|---|
| Upstream checkpoint (safetensors from HF or the publisher) | Ground truth for the weights | Yes, pinned by content hash | It is the reference, so it cannot be checked against anything else. Pin a revision and hash every tensor file. |
| Reference forward pass (e.g. upstream `transformers` in float64 or float32) | Ground truth for logits | Partly | Independent of LARQL, but it is still software: record its version and precision. Better still, use two references that disagree only within a stated tolerance. |
| Numerical format specifications (for the first subject: ggml Q8_0, with gguf-py 0.18.0 as a cross-check) | Defines what decoding should produce | Yes, if taken from the published spec | The checker's dequantizer must be written from the spec, **not** ported from LARQL's code. Listed with pins in PROTOCOL.md under "Trusted base". |
| LARQL's published container specification | Says where the bytes are: segment framing, index, tensor table, names, role policy | **For framing only** | There is no other source for LARQL's own container. It never governs numerical semantics. Agreement on framing shows consistency with LARQL's document, not independent correctness, and is listed as a known limit. |
| LARQL encoder, decoder, runtime | System under test | **No** | |
| LARQL self-checks (S2, S5, S6, IP1–IP3, W3, codec bit-exactness) | Evidence LARQL produces about itself | **No** | The checker reproduces them from outside; agreement is evidence, not a premise. |
| LARQL receipts | Provenance | Trusted only for integrity | A receipt shows a log has not been altered. It does not show the log is correct. |
| Frozen protocol files | Acceptance criteria | Only once hash-enforced | See the next section. |
| The research agent | Proposes and implements | **No** | It must not be able to edit acceptance criteria, its corpora, or the checker it is judged by. |

## Open trust problems, to resolve before freezing

1. **Freeze integrity is a prerequisite, not a deliverable.** LARQL forecasts are immutable by convention only. For
   this protocol:
   - Frozen files are listed in a `FREEZE.sha256` manifest, following the `ai-math-researcher` pattern.
   - A check outside the agent's write scope (CI, or a pre-run hook) verifies the manifest.
   - **A human writes and reviews this mechanism.** The agent is never asked to build the lock it is held by.
2. **Who writes the checker. Decided on 2026-10-30:** three roles, recorded in PROTOCOL.md under "Roles and
   independence":
   - a reference-checker agent with no access to LARQL
   - a LARQL implementation agent
   - an independent reviewer who derives some expected results itself

   The checker does not have to be written by a human, but it must be developed and evaluated independently. What
   remains open is *how* to enforce workspace and dependency isolation (gate G2).
3. **Finite prompts versus universal claims.**
   - Logit match on a frozen corpus is an **empirical** result about that corpus.
   - Only Stage B makes claims over a specified input domain, and only Stage C makes machine-checked ones.
   - Every report states which kind of result it is.
4. **Accumulation order and other kernel details.** A rounding-error bound that assumes a particular summation order
   is only as good as that assumption. Prefer bounds that hold for **any** order (Higham's γₙ style). Where an
   order-specific bound is used, it becomes a stated, testable assumption about the kernel.
5. **CPU versus Metal.** Parity is established per kernel, not for a whole model. Stage A runs on one declared backend.
   Claims about the other backend are out of scope until there is a model-level parity gate.
6. **What "the same model" means.** Specify tokenizer identity, chat template, BOS handling and dtype of the
   reference run. Otherwise a logit mismatch can come from setup differences instead of from the encoding.
