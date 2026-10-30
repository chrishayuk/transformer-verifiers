# LARQL capabilities: what it can and cannot establish

This audit was read-only, against `/Users/christopherhay/chris-source/larql` at HEAD `ff364ba6` on 2026-10-30.
Paths are relative to that repo. Each entry needs re-checking against the SHA the protocol is frozen against.

## Capability matrix

| # | Capability | Verdict | Evidence | What actually exists |
|---|---|---|---|---|
| 1 | VINDEX3 keeps observation separate from intervention, and measurement separate from acceptance | TRUE | `docs/vindex3/observation-and-intervention.md:25-30,61`; `docs/vindex3/representation.md:76`; `docs/measure-plan-1.md:139-162` | An evidence-kind table. Explicit statements that "an intervention is not a causal attribution", "a smaller pack is not evidence of acceptable behavior", and "nothing is judged" |
| 2 | LQL | TRUE | `crates/larql-lql/docs/spec.md` | DESCRIBE/WALK/SELECT/INFER/TRACE/INSERT/COMPILE. Mostly runs against the V2 format |
| 3 | Inference of modified models | TRUE, with caveats | `AGENTS.md:176-177`; `vindex3 exec --backend production-nvfp4` | LQL patch overlays plus COMPILE, or packs produced by `vindex3 represent`. Not pure Rust: uses BLAS (`crates/larql-compute/Cargo.toml:23-31`) and Metal shaders |
| 4 | Activation capture | TRUE | `crates/larql-cli/src/commands/primary/vindex3_cmd/observe.rs:58-168` | `observe --record`, `--heads`, a lens, `--capture/--capture-out` |
| 5 | Head and carrier interventions | TRUE, narrow | `observe.rs:146`; `observation-and-intervention.md:54-55` | Carriers: zero, add, replace. Heads: zero, scale, replace, on **CPU softmax decode only** (no MLA, conv-QKV, batch prefill or Metal) |
| 6 | Representation compiler | TRUE | `vindex3 represent`; status.md:16; commit `47d8869d` | NVFP4, K-quant and plugin encodings. A propose / compile / measure / cut loop (AUTO-REP-1b) |
| 7 | CPU/Metal parity | TRUE for kernels and fragments only | `crates/larql-compute-metal/tests/` (~40 tests), e.g. `test_lowering_attention_parity.rs:466` | Tolerance ~1e-4, with negative controls. **No CPU-vs-Metal logit gate at whole-model level** |
| 8 | Cross-architecture invariants | PARTIAL | `crates/larql-models/src/architectures/` (27 modules); `docs/arch-conformance/README.md`; `Makefile:944` | 117 checkpoints swept for plans and admission only (no forward pass). The cross-arch benchmark measures speed only. **No invariants programme** |
| 9 | Measurement receipts | TRUE | `crates/larql-inference/src/vindex3/record.rs:362`; `docs/v3-stream-1-run-record.md:77-113` | A `Receipt` holding the event-log SHA-256, a provenance fingerprint, a completeness flag, drop counts, and the intervention counts declared and applied. `vindex3 measure` writes `report.json`, `positions.jsonl` and `receipt.json` |
| 10 | Publishing verification | **GAP, fails closed** | `docs/model-publishing.md:236`; `docs/vindex-factory.md:110`; `crates/larql-factory/src/build/stages/verify.rs:20-24`; commit `d8a7d730` | `larql verify` checks checksum integrity only. `spec.verify.reconstruction` and `spec.verify.logit_match` are marked unsupported, so recipe build refuses at preflight. Nothing has been built to verify them |

## Exact checks available today

These are candidate test oracles for Stage A. Each one is a LARQL self-check, so the independent checker must reproduce
it from outside LARQL rather than trust it (see [TRUST-BOUNDARY.md](TRUST-BOUNDARY.md)).

| Check | Tolerance | Source |
|---|---|---|
| Observation does not change logits | bit-identical | `docs/v3-obs-1-carrier-observation.md:49,104`; run recorder S5 |
| Replaying a record reproduces it | bit-identical, floats included (S2) | `docs/v3-stream-1-run-record.md` |
| Receipt hash recomputes and catches tampering | a 1-byte tamper is detected (S6) | same |
| IP1: a no-op intervention matches a run with no intervention | bit-identical | `docs/v3-intervene-1-carrier-intervention.md:111-205` |
| IP2: the target address holds exactly the declared value | bit-identical | same |
| IP3: logits before the intervened position are unchanged | bit-identical | same |
| The per-head sum reconstructs the attention write | 1e-6 to 1e-4, depending on model and law | `docs/v3-intervene-2-head-intervention.md:33,137-171` |
| MEASURE-PLAN-1 W3 matches an independent numpy computation | 1e-9 nats per position | `docs/measure-plan-1.md` |
| MEASURE-PLAN-1 refuses bad inputs | refusals `NullArmNotZero`, `ProtectedOperandChanged`, `SealMismatch`, `CorpusNotForThisModel` | same |
| Codec decode matches the reference dequantizer; candidate logits match the control | bit-exact | `docs/represent-codec-contract.md:145,281` |
| Metal kernels | ~1e-4, with negative controls | `crates/larql-compute-metal/tests/` |

**Not available:** a numerical reconstruction bound measured against the upstream checkpoint, and logit match measured
against an upstream reference implementation.

## Narrowest external interface

| Step | CLI |
|---|---|
| Encode | `vindex encode <ckpt or hf://…> --output m.vindex3` |
| Integrity (hashes only) | `vindex verify` |
| Ops | `larql vindex3 ops` |
| Forward pass | `larql vindex3 exec m.vindex3 --tokens … --backend production --logit-dump out` |
| Capture | `larql vindex3 observe m.vindex3 --backend production --prompt "…" --record run.jsonl [--heads] [--capture … --capture-out …]` |
| Intervene | `… observe … --intervene decl.json` |
| Hashed result | the receipt line in `run.jsonl` (`log_sha256`, `provenance_fingerprint`); `receipt.json` from `vindex3 measure` |

The Rust surface is `larql_inference::vindex3`: `Vindex3Runtime`, `LogitsSession`, `Vindex3Session`, `RunRecorder`,
`Receipt`. The Python bindings in `crates/larql-python/src/session.rs` mention vindex3, but their coverage was not
checked.

## LARQL's existing freeze discipline

LARQL already freezes research "forecasts", for example `docs/represent/forecasts/continuation-window-1.json`. Each
forecast records:

- the freeze date and the main SHA it was frozen against
- `question`, `baseline` and `production_semantics_frozen`
- `acceptance` and `falsified_if`
- `anti_cheat`
- `secondary_observations_not_acceptance`
- `scope.in` / `scope.out`
- `waves`
- an `immutability` line

Results go in sibling `*-notes.json` and `*-records.json` files.

**Weakness:** forecasts carry no content hash, and we found no CI check that they stay unchanged. Immutability rests
on convention and git history alone. `scripts/check_contract_index.py` exists, but we did not confirm what it checks.
