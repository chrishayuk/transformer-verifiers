# transformer-verifiers

Groundwork for verifying transformer computation, starting with the gap LARQL already has.

**Status: survey and draft protocol only.** Nothing here is frozen, and autonomous discovery is disabled
until the trust-boundary and acceptance review in
[`protocols/LARQL-VERIFY-001/PROTOCOL.md`](protocols/LARQL-VERIFY-001/PROTOCOL.md) is complete.

## Contents

| Path | What it is |
|---|---|
| [`survey/SURVEY.md`](survey/SURVEY.md) | Verifiers and checkers for transformers and LLM inference, by category, with guarantees and availability |
| [`survey/CLAIMS-CHECKED.md`](survey/CLAIMS-CHECKED.md) | Claims from the earlier brainstorm checked against primary sources |
| [`larql/CAPABILITIES.md`](larql/CAPABILITIES.md) | What LARQL can and cannot establish today, with file evidence |
| [`larql/TRUST-BOUNDARY.md`](larql/TRUST-BOUNDARY.md) | What a verifier must not take from LARQL, and the open trust problems |
| [`protocols/LARQL-VERIFY-001/PROTOCOL.md`](protocols/LARQL-VERIFY-001/PROTOCOL.md) | Draft protocol: independent checker (A), certified error bounds (B), a machine-checked theorem (C) |
| [`protocols/LARQL-VERIFY-001/draft.json`](protocols/LARQL-VERIFY-001/draft.json) | The same protocol in LARQL's forecast shape, `frozen: null` |

## Why start here

LARQL's model-publishing pipeline declares two guarantees, reconstruction accuracy and logit match, that
nothing enforces. `larql recipe build` refuses any recipe that asks for them
(`crates/larql-factory/src/build/stages/verify.rs`). In the literature we found no certified bound on how far
quantization moves a transformer's outputs. So this is both a real engineering gap and an open research one.

## Longer-term aim

A semiconductor-style verification stack for transformer computation graphs: equivalence checking, proven
numerical bounds, and verified components that compose. LARQL-VERIFY-001 is meant to be the first step towards
that, not the whole of it.

## Provenance of this material

- **When:** the survey and the LARQL audit were each a single research pass, made on 2026-10-30.
- **Re-check before freezing:**
  - LARQL file references are as of `larql` HEAD `ff364ba6`. Re-check them against the SHA the protocol is
    frozen against.
  - URLs and paper metadata come from web search. Items marked *unconfirmed* were not checked against a
    primary source.
