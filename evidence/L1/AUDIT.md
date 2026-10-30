# L1 audit: LARQL 2536bb79, Qwen3-0.6B, Q8_0, `production-q8` + `stored`

| Field | Value |
|---|---|
| LARQL commit | `2536bb79b199b1115445678e3e82c400b0b3fd07` (merge of PR #657, committed 2026-10-01), clean detached worktree `/Users/christopherhay/chris-source/larql-l1-2536bb79` |
| Earlier audit re-verified | `ff364ba6` (committed 2026-09-26) |
| Subject | Qwen/Qwen3-0.6B, official BF16, HF commit `c1899de289a04d12100db370d81485cdf75e47ca` |
| Role | L1 auditor subagent. Not the reference-checker agent and not the B3 spec author. |
| Date | 2026-10-30 |
| Method | Read the source at the pinned commit only. Ran `--help`, a read-only `vindex3 plan` (output to scratch only), `sysctl`, and a header read plus byte hash of the snapshot's safetensors. No container, logit or model output was written. Release binary: `target/release/larql`, `Finished release profile` in `/Users/christopherhay/chris-source/l1-evidence/build.log` (default features `gpu`, `research`). |

All paths below are relative to `crates/` in the worktree unless they say otherwise. `exec/` means `larql-vindex/src/format/vindex3/opplan/exec/`.

## Headline finding (new, and it changes item 1)

**Under `--backend production-q8 --representation-source stored`, with the default environment, the LM head is re-quantised at load into LARQL's own internal Q8 format. Nothing refuses this and nothing reports it.**

1. This snapshot ships an explicit `lm_head.weight` (BF16, `[151936, 1024]`) beside `model.embed_tokens.weight`. The two have byte-identical payloads: both sha256 `8f29acf519434862d95613b2b4f6b9d14933a5e4d16baebf8ac0b33b410acfb6`. The planner therefore makes a separate `target.output_head` object (311,164,928 bytes, BF16) as well as `target.embedding`.
2. The default role policy compiles only `DecoderLinear`, `RecurrenceProjection`, `RecurrenceControl` and `ExpertWeight` (`larql-vindex/src/format/vindex3/represent/policy.rs:158-167, 284-293`). Both head objects classify as `Embedding` or `OutputHead` (`policy.rs:238-243`). They compile zero tensors, so they get no Q8_0 pack and stay canonical BF16 (`represent/pipeline.rs:239-256`).
3. At exec, the BF16 head goes to the production size policy: `exec/production/select.rs:370-385` calls `PhysicalProjectionPlan::choose_for` at `exec/cpu/physical/projection.rs:186-244`. The head has 155,582,464 elements, so its BF16 image (311 MB) is far above `hw.perflevel0.l2cachesize` = 16,777,216 on this machine (`projection.rs:541-549`). `q8_permitted()` is true unless `LARQL_CPU_MAX_FORMAT=bf16` (`projection.rs:428-433`). The plan becomes `FusedQ8`, of form `Requantise`.
4. The loader's `WeightFormat::Q8` arm runs `quantise_q8` (64-element blocks, f32 scales; `exec/quantise.rs:21`) **without calling `note_runtime_quantisation`** (`exec/weights/load.rs:69-90`). Compare the Mxfp4 and Nvfp4 arms at `load.rs:130` and `load.rs:157`. So the `stored` gate (`exec/operands/open.rs:468-480`) never fires. `exec` then prints `runtime compile: 0 tensor(s) — served entirely from stored bytes` (`larql-cli/src/commands/primary/vindex3_cmd/exec.rs:161-169`). The `--representation-source` help text says the opposite ("stored forbids manufacturing — the run fails naming any tensor").
5. The only visible trace is the `projection plans:` ledger line (`exec.rs:195-211`), which lists `FusedQ8`.
6. The same logic is present at `ff364ba6`, in `exec/production.rs:1017-1131` and `exec/weights/mod.rs`. This was not introduced since then; the earlier audit missed it.

**Fix by environment:** `LARQL_CPU_MAX_FORMAT=bf16`. The head then becomes `FusedBf16`: exact BF16 weights, f32 activation, f32 FMA (`kernels.rs:88-102, 701-751`). The cap does not touch the stored Q8_0 pack (`projection.rs:424-427`). This matches the default role policy's intent, which is to keep the head at source precision.

## Items 1–8

| # | Claim at ff364ba6 | Verdict at 2536bb79 | Evidence (`path:line`) |
|---|---|---|---|
| 1 | `production-q8` binds a compiled pack. Plain `production` does not, and manufactures Q8 above L2, capped by `LARQL_CPU_MAX_FORMAT=bf16`. | **CONFIRMED for the decoder linears. WRONG as "no substitution": the BF16 LM head is re-quantised at load** (see the headline finding). | Flag to enum: `larql-cli/src/commands/primary/vindex3_cmd/args.rs:110,210`. Enum to want: `prepare.rs:88-102` (`ProductionQ8 => Some("Q8_0")`; `Production => None`). Want plus source go to the opener: `prepare.rs:45-65`, then `larql-inference/src/vindex3/runtime.rs:99-131`. Per-object binding: `exec/operands/open.rs:102-209` (a pack is used if `<object>@Q8_0` exists; otherwise canonical). Provider: `prepare.rs:225-229` (same `cpu_production` provider as plain `production`). Selection: `exec/production/select.rs:291-357` (stored K-quant gives `Direct(FusedKQuant)`, or `Decode(BlasF32)` under `widen`). Load: `exec/weights/load.rs:201, 291-330` (stored blocks are bound and never decoded or re-encoded). GEMV: `exec/cpu/kernels.rs:413-445` → `represent/kquant.rs:285-295` → `larql-compute/src/cpu/kquant_gemv.rs:67-109`. Plain `production` on BF16: the size policy at `projection.rs:203-244` gives `BlasF32` below L2, then `FusedQ8`/`FusedBf16` at or above L2. L2 from `sysctl hw.perflevel0.l2cachesize`: `projection.rs:541-549`. Cap: `projection.rs:408-433`. The physical.rs code moved into `exec/cpu/physical/projection.rs`; it is semantically the same, apart from a new `choose_for_l2(l2_bytes)` seam. |
| 2 | The Q8_0 GEMV accumulates in f32, element by element, blocks in order. | **CONFIRMED (file unchanged since ff364ba6).** | `kquant_gemv.rs:94-109`: `acc += ((c as i8 as f32) * d) * xs[j]`, sequential per row, f32, no FMA (Rust does not contract). Rows are split across the rayon global pool in 32-row chunks (`kquant_gemv.rs:58, 76-86`). That changes only which thread computes a row, never the values. Scale decode: `larql-models/src/quant/half.rs:14-35`, which handles subnormals. **Kernels per class (with the pinned environment):** attention q/k/v/o and MLP gate/up/down use `FusedKQuant` → `q8_0_gemv`. The LM head (`target.output_head`, BF16) uses `FusedBf16` (NEON, 4×4-lane FMA accumulators, `kernels.rs:724-751`); with the cap unset it uses `FusedQ8` (re-quantised). The embedding (`target.embedding`, BF16) is an exact BF16→f32 widen-and-gather (`realization/selection.rs:30-42`). Norms and q/k-norm vectors are f32 glue. Attention scores, softmax and value mixing are scalar f32 loops (`exec/production/helpers.rs:228-266`). The KV cache is the `row/v1` provider, `Vec<Vec<f32>>`, exact (`exec/kv.rs:381, 408-409`; `larql-cli/src/commands/primary/continuation.rs:34`). **BLAS/Accelerate** is reached only through `BlasF32` (`kernels.rs:41-59` → `larql-compute/src/cpu/ops/moe/math.rs:78-90`, ndarray `dot` → `sgemv`). On this path that happens only for an f32-resident matrix, a BF16 matrix below L2 (none here), or `LARQL_KQUANT_EXEC=widen`. **It is not reached on the pinned path.** Check that `projection plans:` shows no `BlasF32`. |
| 3 | The `represent` Q8_0 encoder calls `larql-models/src/quant/half.rs` `f32_to_f16`, which truncates the mantissa and flushes below the f16 normal range to ±0. | **CONFIRMED (every file in the chain is unchanged since ff364ba6).** | `vindex3_cmd/represent.rs:111` → `represent/report_types.rs:358-365` → `represent/pipeline.rs:24, 287-319` (source loaded via `OperandSource::load`, an exact BF16 widen) → `encode_kquant`, `report_types.rs:230-238` (the non-`reference-encoder` build; that feature is declared only in `larql-vindex/Cargo.toml:82` and enabled by no dependent) → `KQuant::encode`, `represent/kquant.rs:199-221` → `larql_compute::cpu::ops::q4_common::quantize_q8_0`, a re-export of `larql-models/src/quant/ggml/quantize.rs:50-74`. That function computes `scale = amax/127`, `inv = 1/scale` (unrounded f32), and `f32_to_f16(scale)` from `half.rs:43-60`: truncation (`mant >> 13`), `exp16 <= 0 → ±0`. Codes are `(v*inv).round().clamp(-128,127)`. The quantisation uses the f32 scale while decode uses the truncated f16 scale. ggml's reference `quantize_row_q8_0_ref` rounds the scale to f16 with round-to-nearest-even, so **container bytes can differ from llama.cpp's Q8_0 bytes** in the scale, and any 32-block with `amax < 127 × 2^-14 ≈ 7.75e-3` gets scale 0 and **decodes to all zeros**. Note: `larql-compute/src/cpu/ops/q4_common/f16.rs:10-41` has a subnormal-correct `f32_to_f16`, but the Q8_0 path does not use it. |
| 4 | Tied embeddings. | **CHANGED premise: this snapshot is not physically tied.** | It declares `tie_word_embeddings: true` and also ships `lm_head.weight`, byte-identical to `embed_tokens`. The planner prefers an explicit head object and reuses the embedding only when none exists (`opplan/build.rs:699-711`). The plan shows `target.output_head` bound to `lm_head` and `target.embedding` bound to `model.embed_tokens`: two BF16 objects, two copies. `represent` (default policy) compiles neither (`policy.rs:238-243`, `pipeline.rs:239-256`). At exec the head consumes `target.output_head/lm_head.weight` as canonical BF16 bytes (`prepared/loading.rs:172, 314-322`). It runs `FusedBf16` with the pin, or a load-time internal Q8 without it. Because the two tensors are bit-identical, using `lm_head` matches HF's tied behaviour exactly. |
| 5 | Environment. | **CHANGED (more variables; worker variable confirmed as `LARQL_CPU_WORKERS`).** | See the environment table. The executor's own registry of settings is `exec/identity.rs:251-327`. |
| 6 | Logit dump: raw LE f32 `[positions, vocab]`, row i predicts token i+1, teacher-forced one token at a time, no prefill, sidecar records only `LARQL_CPU_MAX_FORMAT`. | **CONFIRMED (file unchanged since ff364ba6).** | `vindex3_cmd/teacher_force.rs:39-93`: a fresh `DecodeSession`, `session.step(token)` for each token from position 0, no prefill. `to_le_bytes` f32 is written for every position, including the last. The sidecar `<out>.meta.json` (`with_extension`, so `x.f32` → `x.meta.json`) at `teacher_force.rs:111-131` holds engine, draft_depth, executed_layers, model_layers, positions, vocab, timings and `max_format_env` only. It has no token IDs, digest, container path, backend arm or other environment. **Additional gap:** `engine` is `vindex3-production-larql-compute` for both `production` and `production-q8` (`exec/production.rs:50`; `production/plan_backend.rs:48-56`; `exec.rs:221`), so the sidecar cannot tell the arms apart. Token input: `--tokens` takes comma-separated u32 decimal IDs and is never tokenised (`args.rs:190-193`; `exec.rs:505-518`). An empty list is refused. `--bank <JSONL>` with `--dump-dir` is the alternative (`args.rs:290-297`). |
| 7 | `spec.verify.reconstruction` / `logit_match` are refused. | **CONFIRMED (file unchanged since ff364ba6).** | `larql-factory/src/build/stages/verify.rs:23-33`: `check_supported` always returns `Err` listing both (plus `from_hub` when set). Only the per-shard SHA256 check runs (`verify.rs:1-13, 35-47`). |
| 8 | Exact encode command. | **Two steps** (`vindex3 encode`, then `vindex3 represent`). | `vindex3 encode` → `verify_encode.rs:132-149` → `artifact::encode_from_specs`. A read-only `vindex3 plan` of the snapshot reports `admissible: true`, "40 representable … 0 blocking", so `--capability` is not needed (and the container is identical either way: `args.rs:422-425`). `vindex3 represent` takes `--encoding` (default **NVFP4**, so `Q8_0` must be given, exact and case-sensitive: `represent/kquant.rs:120-122`). Upstream revision: there is **no revision field for a local path** (`artifact/resolve.rs:76-90` returns `None` for `Origin::Local`). Incidentally, `index.model` and the graph's `source_artifact` are the path stem (`resolve.rs:158-162`, `encode/mod.rs:562-574`). For the snapshot path that stem is the commit hash `c1899de2…`, but the repo id `Qwen/Qwen3-0.6B` is recorded nowhere. Record repo and revision externally. Do not rename or copy the snapshot directory: that changes `index.model`. The pack records `compiled_from`, `source_representation_digest` and the encoder recipe `kquant_native_v1` (`index.rs:48-72`; `report_types.rs:246-249`). |

## Environment

Read sites are in `larql-vindex/src/format/vindex3/` unless stated otherwise.

| Variable | Read site | Effect on this path | Class | Pin |
|---|---|---|---|---|
| `LARQL_CPU_MAX_FORMAT` | `exec/cpu/physical/projection.rs:428-433` (per call); also logged at `vindex3_cmd/teacher_force.rs:128` | `bf16` stops the head being re-quantised (FusedQ8 → FusedBf16). Any other value, or none, leaves Q8 manufacture on. | changes arithmetic (via kernel/format selection) | **`bf16`** |
| `LARQL_KQUANT_EXEC` | `projection.rs:500-502` (per call) | `widen` decodes the Q8_0 pack to f32 and runs BLAS `sgemv`. Anything else is Direct (`q8_0_gemv`). | changes kernel selection and arithmetic | **unset** (Direct). Never `widen`. |
| `LARQL_CPU_ARITHMETIC` | `exec/cpu/physical.rs:258-263` (OnceLock); `exec/cpu/integer/q8_register.rs:227` | `bf16xq8`/`q8xq8`/`q4xq8` (`b` suffix too) put the head on an int8-activation arm. The K-quant pack ignores it (`projection.rs:305-308`). | changes arithmetic | **unset** (FloatActivation) |
| `LARQL_CPU_WORKERS` | `exec/cpu/executor.rs:384-398` | Executor pool size. Partitions are row-contiguous (`executor.rs:264-272`), so per-row values do not change by code reading. It is part of `ProcessArithmetic` (`identity.rs:89, 105`). | kernel scheduling (value-neutral by inspection, not by test) | **`12`** (= `hw.perflevel0.logicalcpu`) |
| `LARQL_CPU_Q4_CLASSES` | `physical.rs:229-233` | Only under `q4xq8`. | kernel selection | unset |
| `LARQL_CPU_ACT_BLOCK` | `exec/cpu/integer.rs:169` | Integer arms only. | arithmetic (inactive) | unset |
| `LARQL_CPU_ACT_CODE` | `integer.rs:242` | Integer arms; also gates the weight index in the Q8 loader (`load.rs:84-88`). | arithmetic (inactive) | unset |
| `LARQL_CPU_WEIGHT_INDEX` | `integer.rs:226` | Q8 residency index, only with asymmetric codes. | kernel selection (inactive) | unset |
| `LARQL_CPU_BIT_IDENTICAL` | `exec/cpu/integer/q8_register.rs:163` | Integer K2/K3 kernels. | arithmetic (inactive) | unset |
| `LARQL_CPU_STATIONARY` | `exec/cpu/stationary.rs:111` | Multi-position sweep only. Bit-identical per `identity.rs:270-275`. | kernel selection (inactive on 1-token steps) | unset |
| `LARQL_FFN_MULTI_POSITION` | `exec/batch_site.rs:516` | Multi-position FFN shape. Bit-identical per `identity.rs:264-269`. | kernel selection (inactive) | unset |
| `LARQL_F32_STAGE`, `_DIR`, `_MIN_BYTES` | `exec/weights/staged.rs:99, 112, 189` | Residency of f32 images only (for example the embedding gather table). | diagnostic/residency | unset |
| `LARQL_REPLAY_PROJECTIONS` | `vindex3_cmd/generate.rs:47` | `--generate` only. | diagnostic | unset |
| `LARQL_QKV_PACK`, `LARQL_LOWERED_*`, `LARQL_ABLATE_*` | `exec/metal_lowered/*` (registry `identity.rs:291-326`) | Metal lowered arms only. Ablations change outputs by design. | arithmetic (not on this path) | **must be unset** |
| `LARQL_MOE_LATENT_*` | `larql-compute/src/cpu/ops/moe/latent_mask.rs:49-78`; `larql-cli/src/main.rs:363-365` | MoE only; stats dump at exit. | diagnostic (not on this path) | unset |
| `LARQL_GGML_REVISION` | `represent/reference_encoder.rs:63` | Only in a `reference-encoder` build, which this binary is not. | encoder identity (not compiled) | unset |
| `LARQL_PLUGIN_RUSTC`, `_BUILD`, `_COMMIT` | `plugin.rs:63-67` (`env!`, build time) | Plugin ABI string, fixed at compile time. | none at run time | n/a |

**Encode path** (`vindex3 encode`, `vindex3 represent`): no `LARQL_*` variable is read on the native-encoder build. `RAYON_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` are not `LARQL_*`. The first affects `q8_0_gemv` row scheduling only; the second affects BLAS only, which is not reached. Pin `RAYON_NUM_THREADS=12` for scheduling reproducibility.

**Rule:** run every command under `env -i` with only the pins below, so no unlisted variable can leak in.

## Exact commands

```sh
B=/Users/christopherhay/chris-source/larql-l1-2536bb79/target/release/larql
SNAP=/Users/christopherhay/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca
OUT=<evidence dir>   # outside the snapshot; the containers must not already exist

# 1. Canonical BF16 container (records index.model = "c1899de289a04d12100db370d81485cdf75e47ca")
env -i PATH=/usr/bin:/bin HOME="$HOME" \
  "$B" vindex3 encode "$SNAP" --output "$OUT/qwen3-0.6b.vindex3"

# 2. Q8_0 pack, default role policy, archival (not --deployment)
env -i PATH=/usr/bin:/bin HOME="$HOME" \
  "$B" vindex3 represent "$OUT/qwen3-0.6b.vindex3" \
    --output "$OUT/qwen3-0.6b-q8_0.vindex3" --encoding Q8_0
```

Do not pass `--include-role`, `--protect`, `--protect-layers`, `--object`, `--moments`, `--plugin` or `--deployment`: each one changes the result. `represent` hard-links canonical segments (`args.rs:452-455`), so do not modify the step-1 container afterwards. Expected `represent` report: `target.decoder_stack` compiled. `target.embedding`, `target.output_head` and `target.final_norm` are listed as "preserved whole".

```sh
# 3. Teacher-forced logit dump
env -i PATH=/usr/bin:/bin HOME="$HOME" \
  LARQL_CPU_MAX_FORMAT=bf16 LARQL_CPU_WORKERS=12 RAYON_NUM_THREADS=12 \
  "$B" vindex3 exec "$OUT/qwen3-0.6b-q8_0.vindex3" \
    --backend production-q8 --representation-source stored \
    --tokens <id0,id1,...> --logit-dump "$OUT/logits.f32"
```

`--component` defaults to `target`. Do not pass `--representation`, `--lowering`, `--plugin` or `--draft-depth`. `--representation` and `--lowering` override the backend's want and provider (`prepare.rs:52-57, 392-402`).

**Acceptance check on stdout:**
- `representation: Q8_0  source: stored  objects from a compiled pack: 1/…`
- `runtime compile: 0 tensor(s)`
- a `projection plans:` line listing **only `FusedKQuant` and `FusedBf16`**

Reject the run if it lists `FusedQ8`, `Q8xQ8`, `BlasF32` or anything else. Archive stdout with the `.f32` and `.meta.json`, because the sidecar alone does not identify the arm or the tokens.

## Other risks: where executed weights can differ from the stored bytes

1. **The head is re-quantised at load** under default environment (headline). It is silent: `stored` does not gate the `WeightFormat::Q8` arm (`load.rs:69-90`), and `runtime compile: 0` is printed anyway. Mitigation: pin `LARQL_CPU_MAX_FORMAT=bf16` and check the ledger. The source fix would be to call `note_runtime_quantisation` in the Q8 and Q4 loader arms, or to refuse `Requantise` under `Stored` in `select_cpu_with`.
2. **`LARQL_KQUANT_EXEC=widen`** decodes the pack to f32 and runs BLAS. The weight values are the same, but the summation is different. Keep it unset.
3. **The encoder diverges from ggml.** The Q8_0 scale is truncated to f16, not rounded, and blocks with `amax < ~7.75e-3` flush to zero (item 3). The container is "LARQL Q8_0", not byte-equal to llama.cpp Q8_0. L2 should count zero-scale blocks in the pack.
4. **Sidecar provenance is thin.** It has no token IDs, digest, container or backend arm, and `engine` is identical for `production` and `production-q8`.
5. **Provenance.** The upstream repo and revision are not recorded for a local encode, except that the snapshot hash appears in `index.model` as the path stem.
6. **Two copies of the embedding and head** are stored. They are bit-identical here, so this is not a numerical risk. A reference that ties the weights is equivalent.
7. **Plugins and overrides.** `--plugin`, `--representation` and `--lowering` can change both what is bound and which provider runs. Forbid them in the protocol.
8. **Ordering differences against a PyTorch reference.** These are not weight substitutions. `FusedBf16` accumulates in 16 lanes with FMA. `q8_0_gemv` is sequential, multiply-then-add. Attention and softmax are scalar f32. These can move logits at f32 noise level.
