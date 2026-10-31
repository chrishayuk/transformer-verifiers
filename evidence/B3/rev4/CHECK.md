# B3 third-party check: VINDEX3 container specification, revision 4 draft

| Field | Value |
|---|---|
| Role | **Third-party checker** for LARQL-VERIFY-001 workstream B3. Not the spec author, not the reference-checker agent, not the reviewer |
| Date | 2026-10-31 |
| Draft checked | `evidence/B3/rev4/SPEC.md`, SHA-256 `8f3f7c2b50eac2cb3a9172599a7e4ce21792f62169559fa64764d6a3ade85a8f` (verified before starting; not edited) |
| Admitted base | `specs/vindex3-container/SPEC.md` (revision 3), SHA-256 `6350e07cff89fb04321ec49ea2e82b14d3893dc7a279d4fd2c899c8db1860a22` (verified; not edited) |
| Container | `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`, read only. 11/11 files match `evidence/L1/container-q8_0.sha256` |
| LARQL source | `/Users/christopherhay/chris-source/larql-l1-2536bb79`, HEAD `2536bb79b199b1115445678e3e82c400b0b3fd07`, `git status --porcelain` empty. Read only; nothing built or run. `/Users/christopherhay/chris-source/larql` not read |
| Reference implementation | **Not consulted** (`transformers`/`torch` not read), as instructed. This check confirms the spec against LARQL's code only. Whether the reference rotates the same way is the reviewer's question |
| Script / raw output | `evidence/B3/rev3/check/check_rev3.py` (SHA-256 `1e1c964c269393aa562b99a627bee2e3fec134d48a3c887855435d06a3bdfbc1`) rerun unchanged → `evidence/B3/rev4/check/rev4_stdout.json` (`981b4c32…`), `rev4_results.json` (`8b1118c2…`). Both are byte-identical to the rev 3 corrected-draft run |

## Verdict

**ADMIT.** The diff has exactly the six reported hunks, 25 changed lines. The only new normative text is the §17.5 rotation paragraph. The formula is confirmed term by term against `rope_rotate` and the code that calls it:
- the sign of each sine term;
- which half each output goes to;
- that both outputs use the unrotated pair;
- per-head chunking of Q and K;
- the order after the QK norm and the query scale;
- the absolute 0-based position, on both the batch and the decode paths.

The informative precision sentence is also correct. The B1 fix points at the right lines. On the container, `position.kind` is `"rope"` at all 28 layers.

One advisory point (D1) concerns the range of a citation. It is not a condition of admission.

## Check 1: diff from revision 3

`diff specs/vindex3-container/SPEC.md evidence/B3/rev4/SPEC.md`: 6 hunks, 25 changed lines (`<`/`>`).

| # | Lines (rev 3 → rev 4) | Section | Content | Class |
|---|---|---|---|---|
| 1 | 7c7 | Header, Revision row | "4 … Revision 3 (SHA-256 `6350e07c…`) was admitted … adds one normative statement to §17.5 … corrects one informative citation" | Metadata. The hash is correct |
| 2 | 27a28 | §0 | Defines the marker **(observed in code)**: established by reading the cited source at the pinned commit, not by observing a container or a run | Convention (no RFC 2119 keyword) |
| 3 | 638a640-653 | §17.5, after "How the writer resolves `position`" | "The rotation for `kind: "rope"` (revision 4) (observed in code)": definitions, the five-line formula, the sign/direction/unrotated-inputs/`p = 0` paragraph, and a precision and other-kinds paragraph | **New normative text** (formula and slice/order/position statement); precision sentence marked informative |
| 4 | 720c735 | §17.8 N2 | `LARQL_KQUANT_EXEC` now cited at its definition `projection.rs:436` and read `:501`; `CLI/prepare.rs:214-224` described as a comment | Informative citation fix (B1) |
| 5 | 888c903-904 | Appendix A | S155 extended with the two `projection.rs` lines; new S156 | Addition |
| 6 | 896c912-913 | Revision history | Row 3 "(this file)" → `6350e07c…` (correct); new row 4. It matches hunks 1-5 | Editorial |

There is nothing outside these hunks. No revision 2 or 3 statement changed. The only new normative statement is in hunk 3 (§17.5). Hunk 2 defines a marker; hunk 4 is in informative §17.8.

## Check 2: the §17.5 formula against LARQL `2536bb79`

`VX` = `crates/larql-vindex/src/format/vindex3`.

### The kernel: `VX/opplan/exec/kernels.rs:147-158`

```rust
pub fn rope_rotate(head: &mut [f32], position: usize, theta: f64) {
    let half = head.len() / 2;
    for i in 0..half {
        let inv_freq = theta.powf(-2.0 * i as f64 / head.len() as f64);
        let angle = position as f64 * inv_freq;
        let (sin_t, cos_t) = (angle.sin() as f32, angle.cos() as f32);
        let x0 = head[i];
        let x1 = head[half + i];
        head[i] = x0 * cos_t - x1 * sin_t;
        head[half + i] = x0 * sin_t + x1 * cos_t;
    }
}
```

| Spec statement | Code | Result |
|---|---|---|
| `d = head_dim`, pairs `i ∈ 0 .. d/2 − 1` | `half = head.len()/2`; `for i in 0..half`. `head.len()` is `head_dim`, because the caller chunks by `call.head_dim` (below) | **Confirmed** |
| `φ_i(p) = p · θ^(−2i/d)` | `inv_freq = theta.powf(-2·i/len)`; `angle = position · inv_freq` (`:150-151`) | **Confirmed** |
| `a = x[i]`, `b = x[i + d/2]` | `x0 = head[i]`, `x1 = head[half + i]` (`:153-154`) | **Confirmed** |
| `x'[i] = a·cos φ − b·sin φ` (sine **subtracted** in the first half) | `head[i] = x0 * cos_t - x1 * sin_t` (`:155`) | **Confirmed** |
| `x'[i + d/2] = a·sin φ + b·cos φ` (sine **added** in the second half) | `head[half + i] = x0 * sin_t + x1 * cos_t` (`:156`) | **Confirmed** |
| Both outputs from the unrotated `a`, `b` | `x0`, `x1` are copied before either write. `:156` reads `x0`, not the updated `head[i]` | **Confirmed** |
| Rotation by `+φ`, counter-clockwise, with `x[i]` on the first axis | `[x0'; x1'] = [[cos, −sin], [sin, cos]] · [x0; x1]`, the standard counter-clockwise rotation matrix for angle `+φ` | **Confirmed** (follows from `:155-156`) |
| At `p = 0` the slice is unchanged | `angle = 0` → `sin_t = 0.0`, `cos_t = 1.0` exactly in f32, so `x0·1 − x1·0 = x0` and `x0·0 + x1·1 = x1` (for finite inputs) | **Confirmed** |

### Where it is called (S156)

| Spec statement | Code | Result |
|---|---|---|
| Q split into `num_q_heads` slices of `d`, K into `num_kv_heads` slices; each rotated independently | `VX/opplan/exec/production.rs:302-311`: under `PositionPolicy::Rope { theta }`, `for head in q.chunks_exact_mut(head_dim) { rope_rotate(head, position, theta) }`, and the same for `k`. `head_dim = call.head_dim` (`:259`). Q has `num_q_heads·head_dim` rows and K has `num_kv_heads·head_dim` (`production/select.rs:31-32, 64-66`) | **Confirmed** |
| After the QK norm and after any query scale | `condition_qk_in_place` (`production.rs:253-311`): `qk_norm_in_place(q…)`, then `(k…)` (`:276-293`), then `query_scale` (`:295-299`), then RoPE (`:302-311`). Called from `production/select.rs:66-70`, after the projections and biases (`:67-68`) and after `condition_v_in_place` (`:69`) | **Confirmed** |
| `p` = the token's 0-based position in the sequence | **Batch:** `production/plan_backend.rs:105` enumerates the inputs, and `project_position(&call, position, …)` passes the index. This path runs only with no KV cache or when the cache is at position 0 (`layer_exec.rs:335-368`), so the index is absolute. **Prefill into a non-empty cache:** `attention_ops.rs:225-231`, `base = kv.position()`, step at `base + offset`. **Decode:** `decode/run.rs:43` `position = self.kv.state().position()`, passed at `:330` into `AttentionStepCall::new(call, position, …)`; the step projects with `step.position` (`production/select.rs:225`) | **Confirmed** on all three paths. Citation ranges S156 `attention_ops.rs:225-231` and `decode/run.rs:316-331` are correct |
| `θ = C.attention[L].position.theta`; `d` = layer `L`'s `head_dim` | `construct.rs:641` `position: policy.position`; `construct.rs:620-622` take head geometry from the per-layer `geometry` (rev 3 check rows 4, 19) | **Confirmed** |

### The informative precision sentence

"`θ^(−2i/d)` and `φ_i(p)` in binary64; `sin`, `cos` rounded to binary32; products and sums in binary32." The code matches: `theta: f64`, `position as f64`, `angle.sin() as f32`, `angle.cos() as f32`, and `x0`, `x1`, `head: &mut [f32]` (`kernels.rs:150-156`). The exponent is computed as `(-2.0·i) / d` in f64. **Confirmed.**

### "Other rotary kinds use the same sign convention"

`rope_rotate_scaled` (`kernels.rs:165-177`) and `mrope_rotate_scaled` (`kernels.rs:249-267`) both compute `head[i] = x0·cos − x1·sin` and `head[half+i] = x0·sin + x1·cos`, with `cos` and `sin` multiplied by the amplitude. The partial-rotary paths apply `rope_rotate_scaled` to a prefix slice (`production.rs:405, 408`). **Confirmed.** See D1 about the citation.

**Refutations: none.**

## Check 3: the B1 fix

- `VX/opplan/exec/cpu/physical/projection.rs:436`: `pub const KQUANT_EXEC_ENV: &str = "LARQL_KQUANT_EXEC";`. **Correct.**
- `:501`: `KQuantExecution::from_env_value(std::env::var(KQUANT_EXEC_ENV).ok().as_deref())`. **Correct.**
- `CLI/prepare.rs:214-224` is the comment that describes `LARQL_KQUANT_EXEC=widen`, as the text now says.

B1 is resolved.

## Check 4: the emitted container

The rev 3 script, rerun unchanged, gives **608 / 0**, exit 0. The output is byte-identical to the rev 3 corrected-draft run. It includes:
- `C.attention[L].position.kind == "rope"` at all 28 layers: 28/28;
- `position` keys exactly `{kind, theta}`;
- `theta == 1000000.0` = upstream `rope_theta` at all 28: 28/28.

Revision 4 adds no other container-checkable value. The rotation formula is a statement about the executor, marked (observed in code).

## Advisory (not a condition of admission)

- **D1 (§17.5, last paragraph).** "The executor's other rotary kinds use the same sign convention … [S148]". S148 is `kernels.rs:147-158`, which covers only `rope_rotate`. The kernels that back this sentence are `kernels.rs:165-177` (`rope_rotate_scaled`) and `kernels.rs:249-267` (`mrope_rotate_scaled`). Two fixes are suggested:
  - add those ranges to S148 or to a new source;
  - extend the "This sentence is informative" marker to cover this sentence too, since it concerns kinds outside this profile.

  The claim itself is correct.
