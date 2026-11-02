# Encoder attribution and the repeated-word probe

**DEVELOPMENT ONLY (D15).** Not blind acceptance evidence. Reference-only for the encoder comparison: LARQL was not run on
any re-encoded weights, and no container was written. The baseline in `runs/suite-v1` was read and not changed.

## Weight sets

Each differs from the others only in its Q8_0 tensors. `G` is ggml's `quantize_row_q8_0_ref`, compiled unmodified from the
pinned source in `inputs/`.

| Set | Encoding | Elements over T2 | Zero-scale blocks | Worst error / bound | Max \|Δw\| | Rel. Frobenius, all Q8_0 |
|---|---|---:|---:|---:|---:|---:|
| L | LARQL's (the container's bytes) | 57,634 | 1,118 | 2,040 | 0.00772 | 0.5560% |
| F | L, flushed blocks fixed only | 21,899 | 0 | 1.05 | 0.00488 | 0.5484% |
| T | L, scale truncation fixed only | 35,735 | 1,118 | 2,040 | 0.00772 | 0.5553% |
| G | ggml's | 0 | 0 | 0.952 | 0.00485 | 0.5476% |

L and G have identical codes in all 13,762,560 blocks. Their scales differ in 6,701,025 blocks.

## Controls

All held:

- a reimplementation of LARQL's encoder reproduces the container's bytes for all 196 Q8_0 tensors;
- ggml's C encoder and gguf-py's Q8_0 agree byte for byte on all 196;
- this path on L reproduces the baseline reference logits bit for bit (`prose-en`, `repetition`, `short-2`).

`reference_run` accepts only the labels `upstream` and `container`, so it was called with `upstream`. For these weight
sets that label is not the weights' origin. The read-back and pins still ran and the gate passed.

## Logits against the BF16 reference, 12 cases, 4,033 positions

| Set | KL mean (nats) | KL max | RMS mean | Max \|Δ\| | Top-1 differences | Positions with lower KL than L |
|---|---:|---:|---:|---:|---:|---:|
| L | 0.003760 | 0.1404 | 0.1198 | 2.82 | 83 | n/a |
| F | 0.003719 | 0.1281 | 0.1191 | 2.82 | 83 | 2,198 |
| T | 0.003635 | 0.1337 | 0.1195 | 2.71 | 86 | 1,954 |
| G | 0.003589 | 0.1214 | 0.1189 | 2.70 | 87 | 2,191 |

The means are position-weighted, so `long-2048` dominates them. Against L itself, G has KL mean 9.4e-5, RMS mean 0.020
and 16 top-1 differences.

Replacing LARQL's encoder with ggml's removes every T2 exceedance and every zero-scale block, and lowers mean KL against
BF16 by 4.5%. The drift that remains belongs to Q8_0. Top-1 agreement does not improve: 83 differences become 87.
The largest single-case change is `repetition`, where T and G lower mean KL by about 15%.

This is one model and one development suite, and these are reference runs. LARQL's own execution on such weights was not
measured.

## Repeated-word probe (`runs/repetition-probe-v1`)

Exploratory: written after seeing the result. Median per-position max |Δlogit| from the f64 reference on the decoded
weights:

| Case | LARQL | f32 reference | Ratio |
|---|---:|---:|---:|
| ordinary prose, suite-v1 | 4.0e-5 | 9.3e-6 | 4.2 |
| `the` x 96 (control, dump bit-identical to the baseline) | 3.8e-4 | 5.9e-5 | 6.6 |
| `the` x 384 | 3.8e-4 | 6.6e-5 | 5.6 |
| `seven` x 96 | 3.5e-4 | 1.1e-4 | 3.1 |
| `-` x 96 | 4.4e-5 | 8.0e-6 | 5.5 |
| `cat` x 96 | 3.3e-5 | 6.7e-6 | 4.7 |
| `的` x 96 | 3.1e-5 | 1.3e-5 | 2.3 |
| `the cat` x 48 | 3.0e-5 | 6.8e-6 | 4.6 |
| a 7-word sentence x 12 | 3.2e-5 | 7.1e-6 | 4.5 |

- **Repetition alone does not cause it.** Three of the five repeated tokens and both cycles are ordinary.
- **It depends on the token.** `the` and `seven` are about nine times higher than the others.
- **Both computations rise.** The f32 reference rises with LARQL, by about 6 to 12 times.
- **It does not grow with length.** The error is flat by position, and is unchanged at 384 tokens.
- **It partly persists.** In `the-then-prose`, LARQL's median falls from 3.7e-4 to 1.0e-4 after the repetition stops, still
  above ordinary prose, over 33 positions.
- **It stays small in the output.** KL stays at or below 4.6e-8 nats, with no top-1 difference against the reference.

The mechanism is not established. Separating it needs intermediate activation capture, which is out of scope.

## The 2,048-token ratio

LARQL's median distance from f64 stays near 1e-4 across the sequence. The f32 reference's rises with position, from 2.4e-5
in the first 128 positions to 2.0e-4 in the last 512. The ratio falls from 4.4 to 0.5 because the reference degrades.
