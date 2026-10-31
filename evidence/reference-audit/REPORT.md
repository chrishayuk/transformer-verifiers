# Reference-forward audit: report (transcription)

**Transcription.** The harness refused the auditor's own write of `REPORT.md`. This is the auditor's returned report,
extracted verbatim from its hand-back in the session transcript by the coordinating session. Nothing was edited.

- **Auditor:** an independent subagent. It is not the checker author. It read checker code, so it never authors hidden
  cases.
- **Audit repository:** `~/chris-source/transformer-verifiers-refaudit`, commit `13f9cb3`.
- **Checker audited:** `4bc93d3`.
- **Spot-checked by the coordinating session:** the `results/*.json` values for r2048 and r4096 (ref64 against the
  independent forward, ref32 against ref64) and the f64 dtype-trace header. They match the report. The auditor's tool
  log (92 calls) shows no LARQL, hidden-corpus or network access, and writes only to its own repository.

---

## Reference-forward audit of LARQL-VERIFY-001: ref32 and ref64 at checker `4bc93d3`

**I found no material defect.** ref64 matches my independent float64 forward to within binary64 rounding on the real upstream weights, out to 4096 positions, at every layer. A dtype trace shows no float32 anywhere in ref64. ref32 is a real float32 run of the same computation. One minor finding needs action before freeze: at long positions, the T3 yardstick is mostly ref32's own float32 RoPE angle error (m1).

**`REPORT.md` was not written.** The harness refused writing a `.md` report file from this subagent, and I did not get around that with a shell write. The full report text is below, ready to save as `REPORT.md`.

- **Audit repo:** `/Users/christopherhay/chris-source/transformer-verifiers-refaudit`
- **Commit:** `13f9cb3`, after `bd3d309`. No attribution trailers.
- **What is committed:** code in `audit/`, results in `results/*.json`, and three re-run scripts (`run_all_ref.sh`, `run_all_mine.sh`, `run_determinism.sh`).
- **Not committed:** large arrays live in `out/`, which git ignores.

---

# Report

## Setup and rules followed
- **Software:** transformers 5.5.0, torch 2.14.0 (Accelerate BLAS, no MKLDNN, 12 threads), numpy 2.4.2 (Accelerate), mpmath 1.3.0, all from `checker/.venv`.
- **Host:** Apple M3 Max.
- **Untouched:** no LARQL source, binary, container or logit dump; no hidden-corpus repo; no network. `checker/` and the main repo were not modified; the checker was only imported read-only, with `python -I`.
- **Inputs:** synthetic token ids only.
  - Seeded random ids below 151643: r16, r128, r512, r2048, r4096.
  - A repeated random block (rep1024).
  - An arithmetic ramp (ramp64).
  - No tokenizer, no text.

## Independence
- **My forward** is `audit/qwen3_np.py`: numpy and mpmath only, written from the mathematical definition in its docstring.
  - `run_mine.py` asserts that neither torch nor transformers is loaded.
  - Weights are read by my own safetensors parser (`audit/st_np.py`), which widens BF16 by bit placement.
  - RoPE cos/sin come from the exact angle in mpmath at 40 digits, rounded once.
  - The score scale 1/√d is computed in mpmath and rounded once.
  - It has a non-BLAS matmul option.
- **Ground truth for tiny models:** `audit/mp_forward.py`, a separate 50-digit mpmath forward.
- **Read as documentation only:** `transformers/models/qwen3/modeling_qwen3.py`, `AttentionInterface.get_interface` in `modeling_utils.py`, and the checker files.
- **Disclosure:** I also saw the checker's own `tests/test_harness.py::np_forward` while surveying the checker. I did not copy it. My forward differs in its RoPE tables, scale handling, cached schedule and options.
- **Shared-assumption risk:** both codes could share a wrong convention. I tested the conventions against a source independent of both: the trained weights (check 4b).

## Per check

### 0. Upstream pin
- All 9 files match the Baseline table in size and SHA-256.
- The file holds 311 tensors, all BF16.
- `lm_head.weight` is present and bit-identical to the embedding.
- The checker's `load_upstream` and my numpy reader give bit-identical float32 weights for all 311 tensors.

### 1. ref64 against my f64 forward
- **How ref64 was run:** through `harness.reference_run(..., "f64", "upstream", authority=Authority.pinned(...))`. The D7 status was `pass` in every run.
- **Hidden states:** captured by forward hooks on the embedding, each of the 28 layers and the final norm (30 sites). Hooks were attached by wrapping `harness.build_model`, and are bit-transparent (check 3).
- **Results, KV-cached one-token schedule on both sides:**

| Input | max \|Δlogit\| | row-relative L2 (logits) | worst hidden site, row-relative L2 | top-1 agreement |
|---|---|---|---|---|
| r16 | 4.1e-14 | 4.6e-15 | 2.9e-15 | 1.0 |
| ramp64 | 3.4e-14 | 3.1e-15 | 3.2e-15 | 1.0 |
| r128 | 6.2e-14 | 4.4e-15 | 4.3e-15 | 1.0 |
| r512 | 9.2e-14 | 1.2e-14 | 1.4e-14 | 1.0 |
| rep1024 | 4.2e-13 | 1.3e-14 | 6.9e-14 | 1.0 |
| r2048 | 4.3e-13 | 4.6e-14 | 5.5e-14 | 1.0 |
| r4096 | 1.5e-12 | 1.4e-13 | 1.7e-13 | 1.0 |

- **Element-wise relative difference:** at most 6.5e-10 over logits with \|logit\| ≥ 1e-3. These are logits near zero.
- **Why this is binary64 rounding:**
  - My own full-sequence and cached schedules differ from each other by 2–5e-13.
  - My BLAS and non-BLAS matmuls differ by 6.4e-14.
  - The f32 discrepancy scaled by eps64/eps32 ≈ 1.9e-9 predicts the same order.
- **The growth at 4096 is fully explained.**
  - It comes from ref64's binary64 RoPE angle rounding, which grows as position × rounding of w.
  - Rerunning my forward with ref64's own RoPE route (its inverse frequencies as data, angle in binary64) brings ref64 against mine at r4096 down from 1.5e-12 to 2.2e-13.
- **No difference beyond binary64 rounding.**
- **Prefill against cached inside the reference:** f64 differs by ≤ 3.0e-13 (r16, r512, r2048). ref64 prefill against my full-sequence forward (r2048) is 4.7e-13.

### 2. AMB-013: native f64 throughout
- **Method:** a `TorchDispatchMode` wrapped around `harness.decode_logits` inside a real `reference_run` (3 steps, real weights).
- **f64 run:** 12,689 float64 tensor operands, 0 float32, 0 bf16/f16.
  - These run in float64: pow, mean, rsqrt, mul (RMSNorm and QK-norm), cos, sin, cat (RoPE), matmul and linear, softmax (with no dtype argument), silu and embedding.
  - The `inv_freq` and `original_inv_freq` buffers are float64.
  - RMSNorm runs the patched forward.
  - The patched eager attention is the function actually dispatched: `get_interface("eager", default)` returns the module global, looked up at call time.
  - Scalars reaching the ops: the scale `0.08838834764831845` (bits `0x3fb6a09e667f3bcd`), the epsilon `1e-06` as binary64, the RoPE `attention_scaling` 1.0, and the mask fill −DBL_MAX.
- **f32 run:** 14,399 float32 operands, 0 float64.
- **No float32 intermediate or downcast was found in ref64.**
- **Limit:** the trace sees ops, not the inside of kernels (assumption a6).

### 3. ref32
- **Error by position on r2048** (max \|Δlogit\| against my f64 forward as truth):

| Positions | ref32 | My f32 forward, exact RoPE table rounded to f32 | My f32 forward imitating upstream's binary32 RoPE angle | That imitation against ref32 |
|---|---|---|---|---|
| 0–15 | 1.2e-5 | 1.0e-5 | 1.2e-5 | 1.4e-5 |
| 128–511 | 8.0e-5 | 2.1e-5 | 7.6e-5 | 1.9e-5 |
| 1024–2047 | 2.8e-4 | 2.4e-5 | 2.7e-4 | 2.3e-5 |

- **Longer and other inputs:** r4096 reaches 4.8e-4 at positions 2048–4095. ref32 has top-1 agreement 1.0 with the truth on every input.
- **ref32 is a real binary32 forward of the same computation.** An independent binary32 forward that forms its RoPE angle the way upstream f32 does reproduces ref32's error profile. It agrees with ref32 to within ordinary f32 noise (≤ 3.6e-5).
- **Tiny models:** ref32 is within 4–9 eps32 × max\|logit\| of the 50-digit truth.
- **Pins:** `pinned_runtime` sets the default dtype, matmul precision `highest` and deterministic algorithms. All were recorded in every run.
- **Threads and determinism (AMB-023), on the real model, r128:** f32 at 1, 4, 12 and 16 threads, a repeat run and a no-hooks run gave bit-identical logits. f64 at 1 and 12 threads, with and without hooks, was also bit-identical.
- **Schedule note:** prefill f32 is about 5× noisier than decode f32 (prefill against cached up to 2.1e-4 at r16).
  - The cause is Accelerate's sgemm, at about 1.1 u·Σ|terms| for M ≥ 2 rows, against sgemv at about 0.21 for M = 1. Both are within f32 bounds.
  - The harness only decodes, so ref32 is on the less noisy path.

### 4. RoPE
**a. Reference internals**
- **Position ids under the KV cache,** observed during a live `decode_logits` run of 12 steps:
  - the rotary module received positions 0, 1, …, 11;
  - the layer-0 cache length before each call was 0, 1, …, 11;
  - each step attended to t+1 keys;
  - the mask was all zeros.
- **Pairing and direction:** the table is `cat(freqs, freqs)` and `rotate_half` is `cat(−x2, x1)`. That is split-half pairing (i, i+64) with rotation (a cos − b sin, a sin + b cos).
- **Inverse frequency:**
  - f64: 22 of 64 values are 1 ulp off the correctly rounded θ^(−2i/d), because `1/base**e` rounds twice (m4).
  - f32: 24 of 64 values are 1 ulp off the correctly rounded binary32 value; maximum relative error 8.2e-8.
- **cos/sin against 40-digit values of the exact angle:**
  - f64: grows linearly with position, up to 3.8e-13 at position 4095 and 2.8e-12 at 40,959.
  - f32 as shipped: 7e-7 at short positions, 1.4e-4 at 1024–2047, 2.8e-4 by position 4095, 2.0e-3 at 40,959.
  - For comparison, a binary64 angle rounded to f32 (the route D7 declares for LARQL) gives 3.0e-8 at every position.

**b. Convention test against the weights**
- **Input:** a random block of 128 ids repeated 4 times. The model is scored on repeats 2–4, where every next token is fixed by the earlier copy.
- **The definition:** top-1 0.969, mean NLL 0.179 nats (chance is 11.93).
- **Each alternative collapses, with top-1 ≤ 0.005 and NLL 13.5–22:**
  - interleaved RoPE pairing;
  - reversed rotation direction;
  - no RoPE;
  - QK-norm after RoPE;
  - no QK-norm;
  - strided GQA mapping;
  - score scale 1/d;
  - (1+w) RMSNorm form.
- **RoPE base, at copy distance 1536:** θ = 1e6 is best (0.962 / 0.329). 1e5 gives 0.960 / 0.351, 1e7 gives 0.953 / 0.389, and 1e4 gives 0.433 / 5.12.

### 5. QK normalisation
- It runs per head over head_dim 128, before RoPE; keys are normalised before caching.
- The weights are the per-layer `q_norm` / `k_norm` vectors of length 128, applied as w·x̂.
- **Epsilon:**
  - ref64: binary64 `1e-6` on every norm module.
  - ref32: the same Python double added to an f32 tensor equals adding binary32 `9.999999974752427e-07` (0 mismatches in 1e6 trials), as D7 states.
- Confirmed by the tiny models and by the weights test.

### 6. Attention
- **Score scale (D8):**
  - The exact value 1/√128 rounds correctly to `0.08838834764831845`. I verified this with exact Fractions: (s ± ½ulp)² brackets 1/128.
  - `head_dim**-0.5` gives exactly that value, and it is the value that reaches `aten.mul` in ref64.
  - The f32 run uses a binary32 product with the scalar rounded to f32, `0.0883883461356163`. Over 2e6 values this matched exactly, and it is the same scale D8 records for LARQL.
  - Square root then division would give `0.08838834764831843`, one ulp low. The reference does not use that route.
- **Causal mask:** a closed-form tiny model (q = 0, so attention is uniform over the causal prefix) matches ref64 to 4.4e-16. Leaking one future token would move the logits by 1.15.
- **GQA:** query head h uses kv head ⌊h/2⌋. Confirmed by the weights test and by tiny models with 2:1 and 4:1 groups.
- **Softmax:** float64 in ref64, float32 in ref32.

### 7. Accumulation precision
- **Linear layers, against exact rationals at decode shapes:** torch f32 has error 0.19–0.25 u32·Σ|terms|; torch f64 has 0.20–0.27 u64·Σ|terms|. That means accumulation in the working type with a blocked order. ref32 does not accumulate in a wider type.
- **Real activations:** numpy and torch f64 matmuls are bit-identical to each other, with error / Σ|terms| ≤ 2.2e-15 against exact Fractions.
- **Removing Accelerate as a shared dependency:** my non-BLAS forward differs from my Accelerate forward by 6.4e-14 (r16).
- **Where summation order enters:** every BLAS call, the `mean` reductions and the softmax sum. Prefill uses GEMM and decode uses GEMV.

### 8. Tied head and final norm
- The tie is checked in every run: shared storage, and a bit-equal source.
- The head is applied after the final w-form RMSNorm with ε = 1e-6.
- My forward agrees at the final-norm site (site 29) and on the logits.
- Logits are not upcast: f32 in ref32, f64 in ref64.

### 9. Analytic checks
**50-digit mpmath forward** on three tiny models with dyadic weights. Max \|Δlogit\| against the truth:

| Model | ref64 native | ref64 "upstream" mode (f32 islands) | ref32 | Mine |
|---|---|---|---|---|
| hidden 16, 4q/2kv heads, head_dim 8, 2 layers, θ 1e6, n = 24 | 7.5e-15 | 1.8e-6 | 3.1e-6 | ≤ 8.6e-15 |
| hidden 16, 4q/2kv heads, head_dim 8, 3 layers, θ 1e4, n = 32 | 1.5e-14 | 4.6e-6 | 7.5e-6 | ≤ 1.8e-14 |
| hidden 32, 4q/1kv heads, head_dim 16, 2 layers, θ 1e6, n = 20 | 2.0e-14 | 6.7e-6 | 6.4e-6 | ≤ 3.0e-14 |

- That is 5.7–9.8 eps64 × max\|logit\| for ref64.
- The unpatched f64 mode is about as far from the truth as f32, which confirms AMB-013's rationale on independent ground truth.

**Closed form** (uniform causal attention): ref64 and mine match to 4.4e-16; ref32 to 3.2e-7.

### 10. Harness
- **Construction:** the model is built from the authority alone, with eager attention, strict loading, and a bit-for-bit check of every parameter.
- **Native patch:** active during both construction and decode. `rebuild_inv_freq_f64` replaces the registered buffer.
- **Decode:** fresh DynamicCache, explicit absolute positions asserted at every step, batch size 1, `inference_mode`.
- **Gate:** the D7 read-back and pins must pass before any metric is computed. Exercised on the real model in every run here.
- **Mitigated risks:** f64 "upstream" mode fails the f64_patch pin, and the patch file's hash is pinned.

## Findings

**Material: none.** The reference computes the Qwen3 forward of the pinned weights as the protocol specifies: ref64 native f64, ref32 upstream code in f32, KV-cached, one token per step, absolute positions.

**Minor**
- **m1. At long positions, the T3 yardstick is mostly ref32's binary32 RoPE angle error.**
  - At positions 1024–2047, ref32's error is 2.8e-4, against 2.4e-5 for an f32 forward without that angle error: about 12×. By positions 2048–4095 ref32's error reaches 4.8e-4.
  - So |ref32 − ref64|, and with it T3, is roughly 10× more lenient past 1k positions. A real LARQL RoPE or attention error of that size could pass there, and a T3 pilot run on short sequences would not show it.
  - This is not a reference defect: D7 already lists the RoPE route difference.
  - **Recommendation before freeze:** report T3 results by position bucket, match the pilot's sequence-length mix to the corpus, or both.
- **m2. Pairing ref32 with ref64 for T3 is not implemented at `4bc93d3`.** No code evaluates T3 or ties a ref64 run to the ref32 run it serves as yardstick for. `check_comparable` only checks that the compared run is f32. Future code must require the same `container_sha256`, the same token ids, and a passing D7 gate for both runs, with ref64 in native mode.
- **m3. The f64 patch only acts inside its context.** A model from `build_model` decoded outside `native_dtype_patches(True)` silently gets f32 islands of about 1e-6, and no pin catches that. Only `reference_run` is safe. A guard or a documentation note would fix it.
- **m4. ref64's inverse frequencies are not correctly rounded** (1 ulp in 22 of 64). In the RoPE table this amounts to ≤ 3.8e-13 at position 4095 and 2.8e-12 at 40,959. It is negligible and normal binary64 behaviour, and it is the whole source of the 1.5e-12 at r4096.

**Assumptions** (trust that remains)
- **a1. Accelerate BLAS,** shared by ref32, ref64 and my BLAS runs. It is only partly removed: my non-BLAS run covered 16 positions, and the exact spot checks covered sampled rows.
- **a2. Transcendental functions** (cos, sin, exp, rsqrt in torch and numpy). The RoPE tables were checked against mpmath; exp and rsqrt only through end-to-end agreement.
- **a3. mpmath and Python `fractions`** as ground truth.
- **a4. This host and build:** IEEE binary32/binary64 with round-to-nearest-even and no flush-to-zero; the M3 Max; this torch build; these thread counts.
- **a5. The upstream weights are trusted by hash.** I verified their identity, not their provenance.
- **a6. Inside the kernels.** The dispatch trace cannot see inside kernels; that f64 ops run f64 kernels is supported by check 7, not proven.
- **a7. The Qwen3 definition itself:** w-form RMSNorm, per-head QK-norm before RoPE, split-half RoPE, SwiGLU, tied head. Without network access I could not consult the Qwen3 technical report. The evidence is the weights test.
- **a8. Coverage:** synthetic ids, n ≤ 4096 end to end. Positions up to 40,959 were checked only at the RoPE-table level.

## Files and scripts

Everything is in `/Users/christopherhay/chris-source/transformer-verifiers-refaudit`:

| Purpose | Files |
|---|---|
| My forward and its parts | `audit/qwen3_np.py`, `audit/mp_forward.py`, `audit/st_np.py`, `audit/inputs.py` |
| Run the reference and my forward | `audit/run_ref.py`, `audit/run_mine.py` |
| Compare runs | `audit/compare.py` |
| Per-check scripts | `audit/dtype_trace.py`, `rope_check.py`, `scalar_check.py`, `analytic.py`, `conventions.py`, `accum_probe.py`, `gemm_probe.py`, `exact_spot.py`, `f32_positions.py`, `rope_attr64.py` |
| Batch re-runs | `run_all_ref.sh`, `run_all_mine.sh`, `run_determinism.sh` |
| Results | `results/*.json` |

To re-run everything: `./run_all_ref.sh; ./run_all_mine.sh; ./run_determinism.sh`, then each `audit/*.py` with `checker/.venv/bin/python -I`.

**Commit:** `13f9cb3`.
