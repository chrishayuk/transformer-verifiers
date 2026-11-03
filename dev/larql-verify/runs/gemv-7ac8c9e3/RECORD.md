# First Q8_0 matvec measurement, 2026-11-03

**MEASURED, not PROVED.** Development only (D15): nothing here is blind acceptance evidence. `Q8_0_GEMV_B1` is experimental, and its guarantee is pending.

**The subject.** LARQL `7ac8c9e3` (PR #693, not merged), release build, binary `4d9eab5c…`, macOS on Apple silicon. Container `q8enc-ad82acba`, `production-q8`, `Direct` arm, 16 tokens. First call on each of 196 Q8_0 operands, of 3,136 calls observed.

**The judge.** `refcheck.gemv` at checker `f599589` (run 17), written in isolation from `specs/q8_0-gemv/SPEC.md` revision 1. Results: `results.json`, from `gemv_run_witness.py`.

| | Result |
|---|---|
| `Q8_0_GEMV_SEQ` | Satisfied on 196 of 196 operations |
| `Q8_0_GEMV_B1` | Satisfied on 196 of 196 |
| Rows, weights | 344,064 rows, 440,401,920 weights, evaluated exactly |
| Worst `\|y − y*\| / B` | 0.0461 (`27.mlp.gate_proj.weight`, row 774) |

**Capture checks.** Logit dump on vs off bit-identical (`5d7f418f…`). Witness calls equal the engine's ledger, 3,136. Captured bytes equal the container's through `refcheck.container`, 196 of 196.

**Controls on real data** (`0.self_attn.q_proj.weight`, from `gemv_controls.py`):

| Change | `SEQ` | `B1` |
|---|---|---|
| None | Satisfied | Satisfied |
| Lowest bit of one output | Violated, 1 row | Satisfied |
| Sign of one output | Violated, 1 row | Violated, 1 row |
| One code in the blocks | Violated, 1 row | Violated, 1 row |
| One scale exponent bit | Violated, 1 row | Violated, 1 row |
| Two output rows swapped | Violated, 2 rows | Violated, 2 rows |
| Reverse-order sum of the same inputs | Violated, 1,966 of 2,048 rows | Satisfied |
| Binary64 accumulate, rounded at the end | Violated, 1,944 of 2,048 rows | Satisfied |

The two worst rows were recomputed exactly by separate code that doesn't use `refcheck`, and they agree to 14 digits.

**Limits.**
- One model, one machine, 16 tokens, and the first call on each operand. These are ordinary activations, so they don't reach subnormal or overflow regions: the checker's synthetic tests cover those, not this run.
- A witness is the engine's report: `y` is right for that `x` and those bytes, not shown to have come from the production kernel.
- `SEQ`'s order comes from LARQL's kernel. Passing it shows the kernel does what it declares.
- `B1`'s derivation is on paper, and the 196 satisfied results don't establish the bound.

## After two fresh-context reviews: the final capture code, 2026-11-03

**LARQL `140916ae` (PR #693), same model, tokens and machine.** Capture on vs off: logits bit-identical, and identical to the `7ac8c9e3` run. All 196 records' `blocks`, `x` and `y` digests equal the preserved witness's. Through `larql-verifier operator` at `a8508875` (PR #695): `SEQ` satisfied on 196 of 196, `B1` satisfied on 196 of 196, 344,064 rows, worst ratio 0.0461. `be04905b` then changes only Windows behaviour and documentation. The preserved witness stays at `~/chris-models/gemv-7ac8c9e3/`. The faulty-kernel results in `gemv-negative-controls/` were captured with `7ac8c9e3`, not rerun with this code.
