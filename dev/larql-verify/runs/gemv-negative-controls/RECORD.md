# Faulty kernels through the production capture path, 2026-11-03

**MEASURED, not PROVED.** Development only (D15). `Q8_0_GEMV_B1` is experimental, and its guarantee is pending.

**Method.** `run.sh` applies one fault from `patch.py` to `q8_0_gemv` in a throwaway detached worktree of LARQL `7ac8c9e3`, builds it, and runs it through the real engine and capture on Qwen3-0.6B, container `q8enc-ad82acba`,
16 tokens, all 196 operands. `refcheck.gemv` judges each witness on that run's own `x`, `y` and bytes. Nothing was committed to LARQL, and the worktree is gone. Faulty witnesses aren't kept: `run.sh` regenerates them. Reference: tree `435ab23a…`, checker `f599589`, tested at `f2788f0`.

| Fault | What it does | Operations violating `SEQ` | Rows violating `SEQ` | Operations violating `B1` | Rows violating `B1` | Worst `B1` ratio | On tensor |
|---|---|---:|---:|---:|---:|---:|---|
| `reverse_blocks` | Blocks summed in reverse order | 196 | 332,177 | 0 | 0 | 0.01277 | 3.self_attn.o_proj.weight |
| `hoist_scale` | Scale factored out, `d·Σ(q·x)` | 196 | 330,838 | 0 | 0 | 0.01125 | 27.mlp.up_proj.weight |
| `binary64_acc` | Binary64 accumulation, rounded at the end | 196 | 330,412 | 0 | 0 | 0.0008624 | 8.self_attn.k_proj.weight |
| `unsigned_codes` | Codes read as unsigned | 196 | 344,064 | 196 | 344,063 | 1.083e+05 | 19.mlp.up_proj.weight |
| `wrong_last_element` | Last element of each block uses the wrong `x` | 196 | 344,064 | 196 | 341,831 | 3081 | 25.self_attn.v_proj.weight |
| `flush_subnormal_scale` | Subnormal scales flushed to zero | 46 | 204 | 45 | 203 | 1.062e+04 | 25.self_attn.q_proj.weight |

Each of 196 operations, 344,064 rows. The clean kernel: 0 and 0, worst `B1` ratio 0.0461 (`gemv-7ac8c9e3/RECORD.md`).

**Each fault reached the production kernel.** For all six: the logit dump differs from the clean run, the witness saw 3,136 calls on 196 operands, the same as the clean run, and each witness's `build_commit` names its fault. `SEQ` flagged each one.

**No fault escaped both contracts.**

| Outcome | Faults |
|---|---|
| Fails `SEQ`, passes `B1` on every row | `reverse_blocks`, `hoist_scale`, `binary64_acc` |
| Fails both | `unsigned_codes`, `wrong_last_element`, `flush_subnormal_scale` |
| Fails `B1` only | None |
| Escapes both | None |

**`flush_subnormal_scale` in detail** (`subn.py`, on the faulty witness alone). 1,118 blocks have subnormal scales, in 204 rows of 46 operations. `SEQ` flagged exactly those rows and operations: none outside them, none missed. `B1` flagged 203 of them, so one row lost a subnormal scale while staying inside the bound. That's this fault on this witness, not a guarantee that every subnormal defect must change every affected output.

**A correction in this analysis.** A first comparison of `y` across clean and faulty runs was invalid, because a faulty kernel changes downstream activations (`x` differed on 101 of 196 operations under this fault). Each operation is judged against its own `x`, so the contract locates a fault at the operations it affects, rather than everything downstream.

**What these results mean.**
- A `SEQ` violation doesn't mean less accurate. All three faults that pass `B1` have smaller worst ratios than the clean kernel. `binary64_acc` is about 50× smaller.
- `SEQ` measures conformance to a declared program, and `B1` measures distance from exact arithmetic. They shouldn't be merged into one word for "correct".

**Limits.** These faults are ones an author chose, so this isn't a measure of how many defects would be caught in general. One model, one machine, 16 tokens, and the first call on each operand. A faulty engine that also forged its witness wouldn't be caught, because a witness is the engine's own report.

**Clean witness.** Rerunning the preserved binary (`~/chris-models/gemv-7ac8c9e3/larql-7ac8c9e3`, `4d9eab5c…`) reproduced the witness exactly: all 589 files the same, `witness.json` `12a30c68…`, and the logits unchanged.
