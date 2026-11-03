# Q8_0 matvec contract: design for review

**Status: draft, not implemented.** Written at LARQL `016f92d7`. Development workstream (D15): nothing here is blind acceptance evidence.

**The question moves** from "are these stored weights within a bound?" to "does this executed operation compute the intended result within a bound?"

## Scope of the first contract

**In:** LARQL's CPU direct arm for stored Q8_0, with an f32 activation. That is `FusedKQuant::project_rows` → `KQuant::gemv` → `q8_0_gemv`, on Qwen3-0.6B.

**Out for now, because each is a different operator or program:**

| Path | Why it's out |
|---|---|
| Metal `q8_0_grouped_experts` | Different program: accumulates `q*x`, multiplies by `d` per block, and combines lanes with `simd_sum`. Subnormal handling also needs checking. It's the natural second target |
| Q8_K activation arms (`FusedKQuantQ8k`, Metal `q8_qkv_proj`) | The activation is quantised, so it's lossy by declaration and needs its own contract |
| `Widen` arm | Decodes then runs the f32 path. A different kernel |
| Q4_K, Q6_K | Different encodings |

## Stage 1: numerical semantics (Part A, the part an isolated author may read)

**Part A contains nothing about LARQL's code**, so it can be handed to the isolated checker as it stands.

**Inputs.** A Q8_0 matrix of `n` rows and `k` columns, with `32 | k`. Each row is `k/32` blocks of 34 bytes: a little-endian f16 scale `d`, then 32 int8 codes `q`. An f32 vector `x` of length `k`.

**Weights.** `w_j = q_j · d_b`, where `b = ⌊j/32⌋`. Over all int8 codes and finite f16 scales this is exactly representable in f32: 8 and 11 significand bits fit in 24, and the result's lowest bit is at least 2⁻²⁴.

**Level 0, the ideal result.** Over the reals: `y*_i = Σ_j w_ij · x_j`.

**Level 1, the normative program.** Bit-for-bit, for each row:

```
acc = +0.0f32
for j in 0..k, ascending:  acc = acc + (w_j * x_j)      // each operation IEEE 754 binary32, round to nearest ties to even, no FMA, subnormals kept
y_i = acc
```

**Level 2, the bound.** With `u = 2⁻²⁴`, `γ_k = k·u / (1 − k·u)` and `S_i = Σ_j |w_ij · x_j|` over the reals:

```
|y_i − y*_i| ≤ γ_k · S_i + k · 2⁻¹⁵⁰ · (1 + γ_k)
```

**Domain.** All `d` finite, all `x_j` finite, `k·u < 1`, and `(1 + γ_k)·S_i < 2¹²⁸ − 2¹⁰³`, so that no product or partial sum can overflow. Outside the domain the answer is `could_not_evaluate`, never `satisfied`. So an f16 infinity scale is refused, and it should be counted.

**Why the bound has this form.** Each term is multiplied once and added at most `k−1` times, so it carries at most `k` factors of `(1+δ)`, giving `γ_k`. Only multiplication can underflow inexactly, by at most 2⁻¹⁵⁰, because addition is exact under gradual underflow. Level 2 holds for any summation order and with or without FMA, as long as arithmetic is IEEE with subnormals. So it survives a kernel rewrite, and it could cover Metal with different constants.

**Why two levels are needed**

| Level | Catches | Misses |
|---|---|---|
| 1, bit-exact | Any change to the arithmetic, however small | Says nothing about whether the program is right: a wrong program can be bit-exact to itself |
| 2, bound | A result that isn't numerically the intended one | Small errors: see below |

Level 2 is loose. From `matvec_bound_spike.py`, the sequential program against exact rationals:

| k | Worst error / bound, across five input families |
|---:|---:|
| 32 | 0.22 |
| 1,024 | 0.028 |
| 3,072 | 0.0037 |

The bound held on every row. That spike has few rows, uses codes −127 to 127, and is my own quick check of the formula, not a proof or the verifier. At k=3072 and ordinary inputs, the slack is about 1,000×, so a real small bug could sit inside the bound. That's why Level 2 alone isn't enough.

**An honest limit on Level 1.** The sequential order comes from LARQL's kernel. `w = q·d` is independently anchored in ggml, but ascending summation is just the order LARQL chose. So Level 1 is "the kernel still does exactly what it declares", a strong regression and determinism check. Level 2 is the claim that the answer is numerically right.

**Contract ids.** `Q8_0_GEMV_SEQ` (Level 1) and `Q8_0_GEMV_B1` (Level 2). Both keep `evidence_kind: numerical_measurement`, which is the only kind LQL accepts today.

## Stage 2: an independent executable reference

**Who writes it.** I've now read the kernel, so I shouldn't author the reference. Following the existing rule, it's written in the isolated checker from Part A alone, with its own tests, then copied unmodified into `verifier/refcheck/` with a new hash table.

**How it computes.**

- **Level 1:** a float32 simulation that must be sequential. NumPy's `add.reduce` is pairwise, so it can't be used.
- **Level 2:** `y*` and `S` exactly. Each product is exact in binary64, so `math.fsum` gives a correctly rounded sum. Anything within a small margin of the bound is re-decided with exact rationals, so rounding in the checker can't decide a verdict.

**Getting a real kernel output: the hard part.** The verifier must not run programs (`test_boundaries.py` enforces this), and today nothing exposes a kernel's inputs and outputs. I found only end-to-end logit dumps. Proposal:

1. **A capture in the engine, as its own LARQL PR.** A flag on `vindex3 exec`, such as `--op-witness <file>`, records at `FusedKQuant::project_rows`: tensor identity, arm, `x`, and `y` as raw bits, sampled by a limit. It only observes.
2. **Two sources of `x`.** Real activations from an actual inference, which test the path production really takes, and verifier-issued challenge vectors, which reach what real inputs don't: subnormals, wide exponent ranges, exact cancellation, and domain edges.
3. **The verifier judges a witness.** `larql-verifier contract --contract Q8_0_GEMV_SEQ --container … --witness …`, reading weights from the container's bytes itself. LQL orchestrates: run the engine, then run the verifier. It stays two programs that don't share code.

**What a witness doesn't prove.** It's LARQL's report of what LARQL did. The verifier checks that `y` is right for that `x` and those bytes, not that the production kernel really produced it. A capture off the real call site, with the check below, makes accidental divergence unlikely, but it won't stop a dishonest engine. This belongs on the same list as the verifier not being authenticated.

**Acceptance, in the same numerical style as the encoder fix**

| Check | Required result |
|---|---|
| Capture on versus off, same prompt | Logit dumps bit-identical, so the capture changes nothing |
| `q8_0_gemv` on Qwen3-0.6B, real and challenge vectors | `SEQ` satisfied and `B1` satisfied, all 196 tensors or a stated sample |
| Negative controls, on mutated kernels in a test harness only (never in production) | Must be detected: wrong stride, dropped block, flushed subnormal scale, one flipped code, one flipped output bit |
| Discrimination | Reversed summation order or a hoisted scale must fail `SEQ` and pass `B1`, showing the two levels measure different things |
| Metal, later and as a natural control | Expected to fail `SEQ`. `B1` is an open question, depending on subnormal handling |

Without negative controls a `satisfied` means little. The encoder work had a real one, the 57,634 elements. This contract has none yet, so they have to be built.

## Stage 3: a bounded-domain proof obligation

**No theorem-proving language.** One statement, written down, for a future backend to discharge:

> For all `k ≤ K`, all int8 `q`, all finite f16 `d` and all finite f32 `x` satisfying the domain above: the Level 1 program's result satisfies the Level 2 inequality.

This separates the claims cleanly:

- **Measurement** shows the kernel matches Level 1 on the inputs tried.
- **The obligation** would show Level 1 implies Level 2 on the whole domain.
- **Neither one alone** says the kernel is correct on all inputs. Together they'd still rest on Level 1 matching for inputs never tried.

The argument under "why the bound has this form" is a sketch, not a proof, and nothing in this workstream may be described as proved until a backend has checked it. LQL already refuses any evidence kind other than `numerical_measurement`, so a formal result can't be claimed by accident.

## Where this leads: representation plus execution

The two contracts compose. Over the reals, with `τ_j` the T2 bound on element `j`:

```
|y_i − Σ_j w_src,ij · x_j|  ≤  Σ_j τ_ij · |x_j|  +  γ_k · S_i + k · 2⁻¹⁵⁰ · (1 + γ_k)
```

So a satisfied `Q8_0_T2` and a satisfied `Q8_0_GEMV_B1` bound one operator's output against the **source** weights. That's the first statement here about what a circuit step computes relative to the original model. I'd report it as a derived number first, not a third contract. It's one operator, so it isn't a bound on a whole forward pass, which would need propagation through non-linear layers.

## Order of work

1. You agree the semantics and the decisions below.
2. Isolated checker run: reference from Part A, then audit, pin and copy into `verifier/`.
3. LARQL PR: the capture only, with the on/off bit-identical check.
4. Verifier PR: both contracts, witness input, and negative controls. The boundary gate keeps this separate from step 3.
5. Run on Qwen3-0.6B and report.
6. LQL statement last. It's a thin layer once the rest works.

## Decisions for you

1. **Both levels, or the bound only?** I recommend both, because the bound alone misses small bugs.
2. **Capture in the engine?** I recommend yes, because real activations on the real call site are the point. The alternative, a small harness calling `q8_0_gemv` directly, is simpler but doesn't show production reaches that code.
3. **CPU first, Metal second?** I recommend yes. Metal needs a confirmed floating-point model first.
