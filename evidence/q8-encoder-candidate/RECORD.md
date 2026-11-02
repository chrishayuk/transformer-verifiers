# Q8_0 encoder candidate

**DEVELOPMENT ONLY (D15).** Not blind acceptance evidence. This does not reopen the blind-subject campaign, and it closes no
gate. Ingestion is `content_valid` only. The L1 baseline stays as it was: LARQL `2536bb79`, binary `4d80dd42…`, its container
(per-file hashes rechecked after this work, all matching) and every record in `dev/larql-verify/runs/suite-v1`.

| Item | Baseline | Candidate |
|---|---|---|
| LARQL commit | `2536bb79` | `ad82acba` (one commit on `2536bb79`) |
| Worktree | `~/chris-source/larql-l1-2536bb79` | `~/chris-source/larql-q8-encoder`, branch `fix/q8-0-encoder-f16-rounding` |
| Binary sha256 | `4d80dd42…` | `bbbfd238b2596f85b32aa00f7e16df6a74c036107d8f2238343e5a75e3de3563` |
| Container | `~/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3` | `~/chris-models/q8enc-ad82acba/qwen3-0.6b-q8_0.vindex3` |
| Container digest (AMB-012) | | `b815b284b8458fde80435aeda8901162c24b58f0d771a0427789fbe2eb3ff607` |
| Per-file hashes | `evidence/L1/container-q8_0.sha256` | `container-q8_0.sha256` here |
| Report | `runs/suite-v1` | `runs/candidate-ad82acba/suite-v1` |

## The change

`quantize_q8_0` stores its f16 scale through a new `half::f32_to_f16_nearest`: IEEE round to nearest, ties to even, subnormals
kept. `half::f32_to_f16` is unchanged, because Q4_0 and `encode_f16` also use it. Decoders and the format are unchanged.

**Left alone, as out of scope, with the same family of behaviour:**
- `half::f32_to_f16` still truncates and flushes: legacy Q4_0 and the public `encode_f16`.
- `larql-compute` `q4_common/f16.rs` keeps subnormals but truncates: the Q4_K and Q6_K scales.
- `tq.rs` has its own `f32_to_f16_le`, not examined here.

## Conformance

| Check | Result |
|---|---|
| The conversion against ggml's `GGML_FP32_TO_FP16`, all 2^32 f32 bit patterns | 0 differences, including 16,777,214 NaN patterns |
| Golden blocks from pinned ggml (`ggml_shim/gen_q8_golden.py`): subnormal, tie, carry, boundary, overflow | 27 of 27 byte-identical |
| LARQL's existing llama.cpp golden fixture | Q8_0 went from 10/544 bytes differing to 0. The test now asserts this for Q8_0 |
| Candidate container against ggml's encoder on the real weights (`bytes-vs-ggml.json`) | 196 of 196 Q8_0 tensors byte-identical |
| Other 115 tensors against the baseline container | All byte-identical |
| LARQL tests: `larql-models`, `larql-compute`, `larql-vindex`, `--lib` | 1,109, 904 and 5,423 passed, 0 failed |

**Excluded from the golden blocks:** non-finite inputs, and amax so small that 1/d overflows f32, where ggml casts NaN to int8.
That is undefined behaviour in C, so there is no single ggml answer to conform to. LARQL's behaviour there is unchanged.

## E1, E2, E3 and f64 (12 cases, 4,033 positions, no overrides, all `MEASURED`)

| Measure | Baseline | Candidate |
|---|---:|---:|
| Q8_0 elements over T2 | 57,634 | **0** |
| Zero-scale blocks | 1,118 | **0** |
| Worst error / T2 bound | 2,040 | 0.952 |
| Max \|Δw\| | 0.00772 | 0.00485 |
| Rel. Frobenius, largest tensor | 0.818% | 0.581% |
| BF16 tensors bit-identical | 115 of 115 | 115 of 115 |
| E2 top-1 differences | 0 | 0 |
| E2 max \|Δlogit\| | 1.83e-3 | 9.75e-4 |
| E2 KL max (nats) | 4.6e-8 | 1.9e-8 |
| E3 KL mean (nats) | 0.003759 | 0.003589 |
| E3 RMS mean | 0.1198 | 0.1189 |
| E3 max \|Δlogit\| | 2.82 | 2.70 |
| E3 top-1 differences | 83 | 87 |

**Success here is numerical conformance.** Top-1 agreement with BF16 is not better, as the attribution predicted, and that is
not the criterion.

**Cross-checks that had to hold, and did:**
- The candidate's decoded-weight reference is bit-identical to the attribution's reference on ggml's encoding, in 12 of 12
  cases. The simulated-weights path and the real container agree exactly.
- The BF16 reference is bit-identical to the baseline's in 12 of 12 cases.
- LARQL's dump differs from the baseline in 12 of 12 cases, so the change reached execution.

E2 now covers real blocks with subnormal scales, on LARQL's own kernels. E2 is an agreement between two implementations on the
same weights, not a proof. It is one model and one development suite.

The f64 ratio is broadly unchanged (`comparison.json` in the run directory): LARQL stays about 3 to 5 times further from f64
than the f32 reference, outside `long-2048`. The fix does not address that, and was not meant to. The repeated-word case's
LARQL distance from f64 falls from 3.8e-4 to 2.6e-4, and it remains the highest. Its mechanism is still not established.

## Storage and compatibility

| Check | Result |
|---|---|
| File list and every file size | Same as the baseline |
| Files that differ | `segments/target.decoder_stack@Q8_0.bin`, `index.json`, `candidate.json` (digests and the source path) |
| A second encode | Identical, except `candidate.json`'s `locator_hint`, the source path, as at L1 |
| Baseline binary on the candidate container | Dump bit-identical to the candidate's: 3 of 3 cases |
| Candidate binary on the baseline container | Dump bit-identical to the baseline's: 3 of 3 cases |
| Encode wall time (`represent`) | 8.4 s, same as the baseline's log |

## Timing

Alternating runs, first pair discarded (`compat-and-timing.json`). Median ms per position:

| Case | Pairs | Baseline | Candidate |
|---|---:|---:|---:|
| `prose-en`, 149 tokens | 8 | 62.8 | 63.3 |
| `structured-table`, 311 tokens | 5 | 74.8 | 78.7 |

The ranges overlap, and these are few runs on a machine that is not otherwise controlled. One candidate run was an outlier at
432.4, which the median sets aside; it was not investigated. **No difference is resolved, and a difference of a few percent
would not be.** Peak memory was not measured. Tensor sizes are unchanged.
