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
| 7 | CPU/Metal parity | TRUE for kernels and fragments only | `crates/larql-compute-metal/tests/` (78 test files), e.g. `test_lowering_attention_parity.rs:466` | Tolerance ~1e-4, with negative controls. **No CPU-vs-Metal logit gate at whole-model level** |
| 8 | Cross-architecture invariants | PARTIAL | `crates/larql-models/src/architectures/` (27 modules); `docs/arch-conformance/README.md`; `Makefile:944` | 117 checkpoints swept for plans and admission only (no forward pass). The cross-arch benchmark measures speed only. **No invariants programme** |
| 9 | Measurement receipts | TRUE | `crates/larql-inference/src/vindex3/record.rs:362`; `docs/v3-stream-1-run-record.md:77-113` | A `Receipt` holding the event-log SHA-256, a provenance fingerprint, a completeness flag, drop counts, and the intervention counts declared and applied. `vindex3 measure` writes `report.json`, `positions.jsonl` and `receipt.json` |
| 10 | Publishing verification | **GAP, fails closed** | `docs/model-publishing.md:235-237`; `docs/vindex-factory.md:110`; `crates/larql-factory/src/build/stages/verify.rs:22-32`, called from `build/mod.rs:35`; commit `d8a7d730` | `larql verify` checks checksum integrity only. `spec.verify.reconstruction` and `spec.verify.logit_match` are marked unsupported: `check_supported` always returns `Err`, so recipe build refuses at preflight. Nothing has been built to verify them |
| 11 | Lossless re-encoding check | TRUE, canonical representations only | `larql vindex3 verify` (`vindex3_cmd/mod.rs:36-39`); `docs/vindex3-format.md:370-410` | Re-hashes the source payload against the encoded payload. This proves byte equivalence for **canonical (lossless)** representations. It does not cover compiled (lossy) packs |

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
| A lossless codec's logits match a raw-bf16 control | bit-exact | `docs/represent-codec-contract.md:145` (bf16-zlib) |
| FP8 decode matches LARQL's own transcription of upstream's `Fp8Dequantize` | bit-exact | `docs/represent-codec-contract.md:281`, against `crates/larql-models/src/quant/fp8_finegrained.rs:216`. **This is LARQL code checked against LARQL code**, not an external reference |
| K-quant decode matches llama.cpp golden bytes | bit-exact on decode | `represent/kquant_conformance_tests.rs:1-30`, `fixtures/ggml_kquant_golden.json`. The same file records that LARQL's **encoder** does not reproduce ggml's bytes: Q8_0 differs in 10 of 544 bytes and Q4_K in 94 of 288 (`:197-205`). The Q8_0 difference comes from `f32_to_f16` (`crates/larql-models/src/quant/half.rs:43-60`), which truncates the mantissa and flushes values below the f16 normal range to zero, where ggml rounds to nearest even |
| NVFP4 decode | self round-trip only | `crates/larql-models/src/quant/tests/nvfp4.rs`. No external reference |
| Metal kernels | ~1e-4, with negative controls | `crates/larql-compute-metal/tests/` |

**Not available:** a numerical reconstruction bound measured against the upstream checkpoint, and logit match measured
against an upstream reference implementation.

## Narrowest external interface

| Step | CLI |
|---|---|
| Encode | `vindex encode <ckpt or hf://…> --output m.vindex3` |
| Integrity (hashes only) | `vindex verify` |
| Ops | `larql vindex3 ops` |
| Forward pass | `larql vindex3 exec m.vindex3 --tokens … --backend production-q8 --representation-source stored --logit-dump out` (see the warnings below) |
| Capture | `larql vindex3 observe m.vindex3 --backend production --prompt "…" --record run.jsonl [--heads] [--capture … --capture-out …]` |

**Warnings about the forward-pass interface:**

- Plain `--backend production` does not bind a compiled pack; that needs `production-q8`, `-q6k`, `-q4k` or
  `-nvfp4` (`vindex3_cmd/mod.rs:91-130`).
- Plain `production` also **manufactures lossy Q8 at load** for any bf16 matrix at least as large as the machine's L2
  cache, read from `sysctl hw.perflevel0.l2cachesize` (`opplan/exec/cpu/physical.rs:465-490, 797-806`). Only
  `LARQL_CPU_MAX_FORMAT=bf16` caps this (`:684-689`).
- Many `LARQL_*` variables change the arithmetic, including `LARQL_CPU_ARITHMETIC` (`physical.rs:243,265`) and
  `LARQL_KQUANT_EXEC` (`:693,757`). The logit-dump sidecar records only `LARQL_CPU_MAX_FORMAT`, and no token IDs,
  config or container digest (`teacher_force.rs:112-131`).
- The dump is teacher-forced, one-token, KV-cached decode only (`teacher_force.rs:66-71`). There is no prefill dump.
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
