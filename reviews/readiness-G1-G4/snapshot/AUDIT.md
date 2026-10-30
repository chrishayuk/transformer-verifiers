# Readiness audit: LARQL-VERIFY-001, gates G1 to G4

Read-only audit, 2026-10-30. Paths are relative to `larql/` unless stated otherwise.

## G3. Re-audit at the candidate freeze commit

- `git rev-parse HEAD` gives `ff364ba638b8…`, so HEAD has not moved. `git log ff364ba6..HEAD -- crates/larql-factory crates/larql-vindex docs/represent* docs/model-publishing.md` is empty. `d8a7d730` is an ancestor of HEAD.
- **The working tree is dirty: 26 entries.** Two files are modified (`crates/larql-demos/Cargo.toml`, `docs/README.md`). The rest are untracked gw-car-1b files in `bench/`, `docs/`, `scripts/` and an example. None are in the relevant areas, but a freeze must pin a clean tree.

| CAPABILITIES row | Verdict | Evidence |
|---|---|---|
| 1 Observation/intervention separation | CONFIRMED | `docs/vindex3/observation-and-intervention.md:25-30`, `representation.md:76` |
| 2 LQL | CONFIRMED (exists) | `crates/larql-lql/docs/spec.md` |
| 3 Modified-model inference | CONFIRMED | BLAS is OpenBLAS on Linux and **Accelerate on macOS** (`crates/larql-compute/Cargo.toml:23-31`) |
| 4 Activation capture | CONFIRMED | `observe.rs` is 690 lines |
| 5 Head interventions are CPU softmax decode only | CONFIRMED | `observation-and-intervention.md:54-55` |
| 6 Representation compiler | CONFIRMED | `47d8869d`. The compilable K-quants are only `Q4_K, Q6_K, Q8_0` (`represent/kquant.rs` `COMPILABLE`) |
| 7 Metal parity | CONFIRMED, count CHANGED | 78 test files, not ~40 |
| 8 Cross-arch | CONFIRMED | the matrix is plans and admission only |
| 9 Receipts | CONFIRMED | `crates/larql-inference/src/vindex3/record.rs:360-367` |
| 10 Publishing verification gap | CONFIRMED | `verify.rs:23-32` **always** returns `Err`, called from `build/mod.rs:35`. `docs/model-publishing.md:235-237`, `docs/vindex-factory.md:110` |
| 10, omission | CHANGED | `larql vindex3 verify` (`vindex3_cmd/mod.rs:36-39`, `docs/vindex3-format.md:370-410`) re-hashes source payload against encoded payload. This proves byte-equivalence for **canonical (lossless)** representations. It does not cover compiled packs |
| "Codec decode matches reference dequantizer, bit-exact" | **WRONG as cited** | See below |
| Interface: `exec … --backend production --logit-dump` | **WRONG / incomplete** | See below |
| `scripts/check_contract_index.py` | RESOLVED | See below |

**What the "reference dequantizer" actually is.**

- `represent-codec-contract.md:145` is about bf16-zlib logits being bit-exact to a raw-bf16 control (a lossless codec).
- `:281` (FP8) says the decode is "bit-exact to `fp8_finegrained::dequantize_into`, the transcription of upstream's `Fp8Dequantize`". That reference is **LARQL code** (`crates/larql-models/src/quant/fp8_finegrained.rs`).
- Neither line is about NVFP4 or K-quants.
- "Reference path" and "reference oracle" (`:40`, `:269`) mean the codec's own `decode_rows()`.

**Where the dequantizers live.**

- The codec wrappers are in `crates/larql-vindex/src/format/vindex3/represent/codec/codecs/{kquant,nvfp4,mxfp4,fp8_block,bf16_zlib,vq8_shared,…}.rs`.
- They delegate to `crates/larql-models/src/quant/{nvfp4.rs, mxfp4.rs, fp8_finegrained.rs, ggml/{legacy,q4_k,q6_k,q5_k,q3_k}.rs}`. For example, `kquant.rs:240` calls `ggml::dequantize`, and `codecs/nvfp4.rs:171` calls `nvfp4::dequantize_into`.
- Further copies exist in `crates/larql-compute/src/cpu/ops/q4_common/dequant.rs`, `crates/larql-inference/src/vindex/dequant.rs` and `crates/larql-compute/src/kquant_forward/dequant.rs`.
- The **K-quants are checked against llama.cpp golden bytes** (`represent/kquant_conformance_tests.rs:1-30`, `fixtures/ggml_kquant_golden.json`).
- The same file records that **LARQL's encoder does not reproduce ggml's bytes: Q8_0 differs in 10 of 544 bytes, Q4_K in 94 of 288** (`:197-205`).
- The NVFP4 tests are self-round-trips only (`crates/larql-models/src/quant/tests/nvfp4.rs`).
- A precedent for shared misreading: `TYPE_Q8_0` and `TYPE_Q5_0` were once swapped (`ggml/fixtures/ggml_type_table.gen.c:10-13`).

**`check_contract_index.py`** checks only that each test named in `docs/represent-v1-contract-index.md` and `docs/optimizer-contract-index.md` **exists at the cited path**. It checks no hashes and no outcomes (`:1-18`). CI runs it (`.github/workflows/quality.yml:267`). It does nothing for forecast immutability.

**Interface corrections.**

- `--backend production` does not bind a compiled pack. That needs `production-q8|q6k|q4k|nvfp4` (`vindex3_cmd/mod.rs:91-130`).
- Worse, plain `production` **manufactures lossy Q8 at load** for any bf16 matrix ≥ the machine's L2 size. It reads `sysctl hw.perflevel0.l2cachesize` (16 MB on this M3 Max) (`opplan/exec/cpu/physical.rs:465-490, 798-806`). It is capped only by `LARQL_CPU_MAX_FORMAT=bf16` (`:667-690`).
- At least 40 `LARQL_*` environment variables (for example `LARQL_KQUANT_EXEC`, `LARQL_CPU_ARITHMETIC`, `LARQL_LMHEAD_Q8`) change the arithmetic. The logit-dump sidecar records only `LARQL_CPU_MAX_FORMAT` (`teacher_force.rs:112-131`).

## G4. Numerical contract

**Encode and execute today (CPU):** Q8_0, Q6_K and Q4_K (`--backend production-q8/q6k/q4k`, direct GEMV `represent/kquant.rs:285-308`) and NVFP4 (`production-nvfp4`). MXFP4, Q5_K, Q3_K and FP8 are decode or import only.

| Rank | Format | Public spec | Independent reimplementation |
|---|---|---|---|
| 1 | **Q8_0** | ggml block = f16 d + 32 int8. Third-party numpy decoder exists: `gguf` 0.18.0 `gguf.quants.Q8_0` is installed locally | Trivial. The decode `q·d` is exact in f32 (11-bit × 8-bit product) |
| 2 | Q6_K / Q4_K | `ggml-quants.c` is the only spec. gguf-py has dequantize but not quantize | Moderate. The 6-bit scale/min packing is fiddly |
| 3 | NVFP4 | E2M1/E4M3 semantics come from NVIDIA docs and the OCP FP8 spec. There is **no** formal standalone NVFP4 spec | The element math is public. **The pack layout is LARQL-only**: planar codes, scales and tensor-scale; nibble order (`represent/nvfp4_pack.rs:8-18`). It differs from GGML NVFP4 (`quant/nvfp4_ggml/mod.rs:11-21`) |
| 4 | MXFP4 | OCP MX v1.0 (formal) | Not compilable through `represent`. The two-stream layout is LARQL's |

**Local checkpoints.**

- In `~/.cache/huggingface/hub`: SmolLM2-135M (269 MB, rev `93efa2f0…`), SmolLM2-360M-Instruct (724 MB), gemma-3-1b-pt (2.0 GB), Llama-3.2-1B (2.5 GB), TinyLlama-1.1B.
- Also `~/chris-models/OLMo-2-0425-1B` (5.5 GB, **fp32**).
- In `~/chris-models`, containers include `qwen3-0.6b.vindex3` (1.4 GB, BF16, no upstream revision recorded in `index.json`), `olmo2-1b.vindex3` and `oute-mamba2attn-250m.vindex3`.
- `larql/data` is 5.6 MB of knowledge data with no weights.
- **The Qwen3-0.6B upstream weights are not local**; only lock files exist.

**Execution evidence.**

- LARQL runs `qwen3-0.6b` on ProductionBackend (`docs/represent/forecasts/continuation-mem-1.json:28`).
- OLMo-2 has a LARQL-written HF oracle (`scripts/olmo2_reference_oracle.py`). That is LARQL code, not independent.
- SmolLM2 appears only in plan matrices and declaration tests; no vindex3 exec is evidenced.

**Reference forward pass.** Feasible locally: Python 3.12.2, torch 2.14.0, transformers 5.5.0, numpy 2.4.2, safetensors 0.7.0, uv 0.8.14, and 128 GB RAM.

**Logit dump.**

- The dump is raw little-endian f32 `[positions, vocab]` with no header. Row *i* predicts token *i+1* (`teacher_force.rs:19, 79-84`).
- It is accompanied by a `.meta.json` sidecar (engine, positions, vocab, layers).
- It can be read with `numpy.fromfile`, without LARQL.
- The sidecar has **no container digest**, so a dump from a different model is detectable only by provenance the checker supplies.
- It is teacher-forced decode one token at a time. **There is no prefill dump**, so A2's "prefill and decode" requirement cannot be met through this interface.

## G1. Freeze-integrity facts

- transformer-verifiers has no `*sha256*` or manifest file, and `git rev-parse` reports "not a git repository". Confirmed.
- **`ai-math-researcher/tools/manifest_check.py` does not check hashes.** It checks that the declared outputs exist, are non-empty and that any JSON parses (`:8-18`).
- The real freeze logic is `tools/new_campaign.py:89-96`. It writes `frozen.sha256` and `campaign.sha256` into the campaign directory, which `runner.py:199-205` checks with `shasum -c`.
- **The root `FREEZE.sha256` currently fails:** `shasum -a 256 -c` reports `./README.md: FAILED`. The repository was archived in `03f8993` without re-freezing, so nothing enforces it.
- What this mechanism misses:
  - The manifest and the files it covers sit in the same writable tree, so an agent can regenerate both.
  - Unlisted added files pass.
  - `shasum` follows symlinks, so retargeting a symlink to a file with identical bytes passes, and a listed path replaced by a symlink passes.
  - The checker (`runner.py`) verifies itself: an edited runner can skip the check.
  - Nothing runs outside the agent's process.
- **Candidate outside enforcement points:**
  - Put transformer-verifiers into git with a GitHub remote, a protected branch, CODEOWNERS on `protocols/`, and a CI workflow that recomputes the manifest from a signed or tagged commit.
  - Alternatively, use a pre-run hook in the user's `~/.claude/settings.json` (outside the project).
  - Or put the frozen tree on a read-only mount or under another OS user.
- larql has 23 workflows (`.github/workflows/`) and no local hooks (`.git/hooks` has samples only). Its CI protects larql, not this protocol.
- **Tamper tests G1 should require:**
  1. Edit a byte of each frozen class: protocol, tolerances, corpus, held-out part, mutation suite, checker.
  2. Regenerate the manifest after an edit.
  3. Add an unlisted file, for example a new tolerance override.
  4. Delete a listed file.
  5. Swap a file for a symlink, and retarget an existing symlink.
  6. Edit the check script or the hook configuration.
  7. Rename a file, so its path changes while its content stays the same.
  8. Change the checker's dependency lockfile.
  9. Change an environment variable that alters semantics (`LARQL_*`).

  Each test must be run by the agent role and must be blocked at the outside point.

## G2. Independence facts

- A checker with zero LARQL dependency is feasible for Q8_0. It would read the upstream safetensors, the ggml Q8_0 layout (or gguf-py) and transformers.
- **Documented only inside LARQL. These are the shared-misreading risks:**
  1. The segment framing: `[u64 LE header len][JSON header][payload]`, 16-byte alignment. It is described only in a code comment (`format/vindex3/encode/segment.rs:1-14, 53-72`). `docs/vindex3-format.md:311-345` is prose with no byte layout.
  2. The `index.json` and `system_graph.json` schemas.
  3. The relative tensor names and their mapping to HF keys. `verify.rs:6-8` calls this mapping the unsolved part.
  4. Row orientation, and blocking per row.
  5. Dtype labels.
  6. The NVFP4 and MXFP4 pack layouts.
  7. The `run.jsonl` event schema and the provenance-fingerprint algorithm (`docs/v3-stream-1-run-record.md` is prose; the algorithm lives in code at `exec/provenance.rs`).
  8. `measure` `receipt.json` (`docs/measure-plan-1.md:127-130`, prose).
- The receipt hash rule is documented well enough to reimplement: SHA-256 over the event lines, each followed by a newline (`record.rs:365-366`, R7).
- **The missing format docs are a blocker.** Without them, the checker author must read LARQL source, which breaks role isolation, or reverse-engineer the format, which is itself a finding.

## BLOCKERS

1. **G1:** No manifest or outside check exists. The ai-math-researcher pattern is non-enforcing: `manifest_check.py` does not hash, and the root `FREEZE.sha256` currently FAILS.
2. **G1:** transformer-verifiers is not a git repository, so there is no external enforcement point.
3. **G2:** There is no public byte-level spec for the vindex3 segment, index, tensor naming or NVFP4 pack, or for the run.jsonl and provenance fingerprint.
4. **G3:** The working tree is dirty (26 entries), so "freeze at ff364ba6" is ambiguous.
5. **G3:** The CAPABILITIES "reference dequantizer" row is WRONG. It is LARQL's own code (FP8), and the lines are mis-cited for NVFP4 and K-quants.
6. **G3/G4:** The CAPABILITIES interface `--backend production` does not read packs, and it silently quantises large bf16 matrices to Q8 depending on L2 size. Of more than 40 environment variables that alter arithmetic, only one is recorded.
7. **G4:** The baseline proposes gemma3-4b plus NVFP4 and K-quant. NVFP4 cannot be checked independently, and G4 requires one model and one format.
8. **G4:** The proposed small subject (Qwen3-0.6B) has no local upstream checkpoint.
9. **G4:** The logit dump carries no container digest and has no prefill path.

## Proposed numerical subject and tolerance rules

**Subject.**

- Qwen/Qwen3-0.6B at a pinned revision, encoded `vindex3 represent --encoding Q8_0` (default role policy).
- Run with `exec --backend production-q8 --representation-source stored --logit-dump`, with `LARQL_CPU_MAX_FORMAT=bf16`, `LARQL_KQUANT_EXEC` pinned, and a fixed `LARQL_CPU_WORKERS`. The full environment is recorded.
- Reasons: it is the smallest model with evidenced LARQL CPU exec; it is the simplest format with a third-party decoder; and the Q8_0 GEMV accumulates in f32, element by element, block by block in order (`crates/larql-compute/src/cpu/kquant_gemv.rs:90-97`).
- Fallback without a download: OLMo-2-0425-1B (local, fp32, 1.5B parameters).

**Tolerance rules.**

- **(a) Decode equivalence. Fully a priori.**
  - Rule: the checker's decode must equal LARQL's f32 decode bit-for-bit for every element, comparing bit patterns, ±0 included.
  - Why bit-for-bit is required: f16→f32 and int8→f32 are exact, and an 11-bit × 8-bit product fits in 24 bits, so the decoded value is unique.
- **(b) Per-element reconstruction. A priori, given a stated encoder model.**
  - Rule: |w − q·d₁₆| ≤ d₁₆·(½ + 127·2⁻¹¹), plus a 127·2⁻²⁵ term in the f16 subnormal range.
  - This bound assumes round-to-nearest with d = amax/127 and d rounded to f16.
  - The ggml byte mismatch shows that encoder equality must not be the criterion.
  - Relative Frobenius error is reported. It is bounded by the same per-block terms.
  - A violation is a finding, not a tolerance to widen.
- **(c) Logits. Split into two parts.**
  - **(c1) Runtime equivalence.** Compare LARQL's logits with the checker's own forward pass over the *same* dequantized weights.
    - Rule: |Δ| ≤ c·|f32_ref − f64_ref| per position (floored at a declared f32 ulp multiple). c is fixed before measurement, and Accelerate's unknown summation order is covered by γₙ-style reasoning.
    - The form of the rule is a priori. **The value of c needs a pilot.**
  - **(c2) Quantization acceptability.** Compare with the bf16 upstream in f64, using KL, top-1 agreement and max |Δ|.
    - No a priori derivation exists. This is a model-acceptability outcome, and its threshold is a policy choice.
- **Pilot risk.** Any pilot must use a different checkpoint (for example SmolLM2-135M) or a declared, discarded corpus disjoint from the sealed held-out part. It must be recorded in the protocol before it is run. Otherwise it breaks "tolerances before measurement".

## Open questions only the user can answer

1. May the Qwen3-0.6B upstream checkpoint (~1.5 GB) be downloaded, or is OLMo-2-1B (local) the subject?
2. Will transformer-verifiers become a git repository with a GitHub remote and branch protection, and who is the human reviewer of the lock?
3. Is gguf-py an acceptable "third source" for decode, or must the checker be written purely from documentation?
4. Should LARQL publish byte-level format specs (segment, index, NVFP4 pack, run.jsonl) before the freeze? That would be a LARQL change outside this protocol.
5. Should the protocol amend its baseline to one Q8_0 encoding and defer NVFP4?
6. What policy threshold applies to (c2)? Or is it reported only?
7. Should the freeze be at a clean commit after the gw-car-1b work lands, or at `ff364ba6` with a clean checkout?
