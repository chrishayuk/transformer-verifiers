# OQ2: undefined-domain scan of the pinned upstream checkpoint

**Question (PROTOCOL D1, OQ2).** In ggml `facdc44a` `quantize_row_q8_0_ref` (`src/ggml-quants.c:276-299`),
`y[i].qs[j] = roundf(x0)` converts a float to `int8_t`. C11 6.3.1.4 makes that undefined when the value is
non-finite or outside [−128, 127]. Does any block of the pinned upstream checkpoint reach that conversion?

**Answer: no.** Zero blocks in any class, in the 196 decoder projections and in all 311 tensors. Every element of
every tensor has a defined reference encoding.

## Inputs and method

- Checkpoint: `Qwen/Qwen3-0.6B` at `c1899de2…`, `model.safetensors` sha256 `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`, verified by the script
  before use. All 311 tensors are BF16, widened exactly to f32 (`bits << 16`).
- Blocks: 32 consecutive elements along each tensor's last dimension (SPEC rev 2 §8.4). Every last dimension
  (128, 1024, 2048, 3072) is a multiple of 32.
- Arithmetic, per block, in IEEE binary32 with round-to-nearest-even and subnormals kept: `amax` by the loop's
  `MAX(a,b) = (a) > (b) ? (a) : (b)` over `fabsf` (blocks with a NaN would be recomputed with the sequential
  semantics; there are none), `d = amax/127.0f`, `id = d ? 1.0f/d : 0.0f`, `x0 = x*id`. The conversion is defined
  iff −128.5 < x0 < 127.5, since `roundf` rounds half away from zero; NaN fails the test.
- Bulk arithmetic is numpy float32. For every tensor, the block with the smallest non-zero amax and the block
  with the largest |x0| are re-encoded with the exact-rational model (`e1/ggmlref.py`, `lib/exactfp.py`), and
  amax, d, id and every x0 must match bit for bit: 622 blocks checked, all equal.
- The id overflow threshold is derived exactly (bisection over f32 bit patterns with exact rationals), not from
  numpy.
- Script: `oq2/scan_upstream.py`. Raw per-tensor output: `oq2/results.json` (deterministic; two runs give the same
  sha256). No checker code, log or output was used. Only upstream weights are touched, so this file and the script
  may be published.

## Counts

Blocks, with undefined-conversion elements in parentheses. (a) contains a NaN; (b) contains ±inf; (c) finite with
amax > 0 and id = inf or some roundf(x0) outside [−128, 127] or non-finite.

| Set | Tensors | Blocks | Elements | (a) NaN | (b) ±inf | (c) finite | Undefined, any class |
|---|---|---|---|---|---|---|---|
| Decoder projections (SPEC §11.3, Q8_0 under the default policy) | 196 | 13,762,560 | 440,401,920 | 0 (0) | 0 (0) | 0 (0; id overflow 0) | 0 |
| All tensors | 311 | 23,488,512 | 751,632,384 | 0 (0) | 0 (0) | 0 (0; id overflow 0) | 0 |

Per tensor, every count is 0 in all 311 tensors (`per_tensor` in `results.json`). There are no NaN or inf elements
at all, and no block with amax = 0.

## Margins

| Quantity | Projections (196) | All (311) |
|---|---|---|
| Smallest non-zero amax | 0.00171661376953125 (`0x3AE10000`, `model.layers.21.self_attn.k_proj.weight`) | same |
| Largest amax | 1.234375 (`model.layers.27.mlp.up_proj.weight`) | 192.0 (`model.layers.27.post_attention_layernorm.weight`) |
| Largest \|x0\| | 127.00000762939453 | 127.00000762939453 |
| Largest \|roundf(x0)\| | 127 | 127 |

- **id overflow threshold (exact).** id = RN(1/RN(amax/127)) is finite iff amax ≥ `0x02FE0004`
  ≈ 3.732195e-37 (d₃₂ = `0x00200001`, an f32 subnormal). For
  `0x00000040` ≤ amax ≤ `0x02FE0003` the id is +inf, and every x0 is ±inf or NaN
  (undefined). For amax ≤ `0x0000003F` (63 × 2⁻¹⁴⁹), d rounds to +0 and id = 0, which
  is defined (all codes 0).
- **Margin of the smallest non-zero amax to the threshold:** a factor of 4.5995e+33,
  that is 2^111.83, about 33.7 decimal orders of magnitude.
- **Margin of x0 to the range limit:** the largest |x0| is 127.00000762939453, against the undefined threshold of
  127.5. When id is finite, d₃₂ ≥ 2⁻¹²⁸ approximately, so its relative rounding error is at most about 2⁻²¹ and
  |x0| ≤ 127·(1 + 2⁻²⁰) approximately. So (c) can only arise through id overflow.
- **f16 overflow of d (OQ1, not OQ2).** The largest amax is 192.0, far below 127 × 65504 ≈ 8.32e6,
  so no upstream block gives d₁₆ = +inf under the reference encoder either.

## Consequence for the corpus

Under D1 (OQ2: "Each affected input needs either a defined rule, justified independently, or an explicit exclusion
from the guarantee it would test"): no upstream input of this subject is in the undefined domain, so no encoder
equivalence claim about the subject depends on it. The E1 encoder cases built in that domain
(`e1_input_pos_inf`, `e1_input_nan_first`, `e1_input_nan_last`, `e1_f32_subnormal_amax_id_overflow`) are marked
excluded from encoder-equivalence claims in corpus revision 2 (`e1/EXCLUSIONS.json`). They are kept, not deleted.

## Raw totals (JSON)

```json
{
 "id_overflow_threshold": {
  "amax_max_overflowing_id": 3.7321952364840257e-37,
  "amax_max_overflowing_id_bits": "0x02FE0003",
  "amax_max_with_d_zero_bits": "0x0000003F",
  "amax_min_finite_id": 3.73219546069178e-37,
  "amax_min_finite_id_bits": "0x02FE0004",
  "d32_at_threshold_bits": "0x00200001",
  "note": "positive f32 amax in [smallest subnormal, amax_max_overflowing_id] gives d != 0 with 1/d overflowing to +inf (undefined conversions), except amax values whose d rounds to +0 (id = 0, defined)"
 },
 "sha256": "f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b",
 "totals": {
  "all_311": {
   "a_blocks": 0,
   "a_elements_undefined": 0,
   "amax_zero_blocks": 0,
   "b_blocks": 0,
   "b_elements_undefined": 0,
   "blocks": 23488512,
   "c_blocks": 0,
   "c_elements_undefined": 0,
   "c_id_overflow_blocks": 0,
   "elements": 751632384,
   "exact_crosschecks": 622,
   "inf_elements": 0,
   "margin_log2": 111.82509615777121,
   "margin_min_amax_over_threshold": 4.599474458427929e+33,
   "max_abs_code": 127,
   "max_abs_x0": 127.00000762939453,
   "max_abs_x0_tensor": "model.norm.weight",
   "max_amax": 192.0,
   "max_amax_tensor": "model.layers.27.post_attention_layernorm.weight",
   "min_nonzero_amax": 0.00171661376953125,
   "min_nonzero_amax_bits": "0x3AE10000",
   "min_nonzero_amax_tensor": "model.layers.21.self_attn.k_proj.weight",
   "nan_elements": 0,
   "tensors": 311,
   "undefined_blocks_any_class": 0
  },
  "projections_196": {
   "a_blocks": 0,
   "a_elements_undefined": 0,
   "amax_zero_blocks": 0,
   "b_blocks": 0,
   "b_elements_undefined": 0,
   "blocks": 13762560,
   "c_blocks": 0,
   "c_elements_undefined": 0,
   "c_id_overflow_blocks": 0,
   "elements": 440401920,
   "exact_crosschecks": 392,
   "inf_elements": 0,
   "margin_log2": 111.82509615777121,
   "margin_min_amax_over_threshold": 4.599474458427929e+33,
   "max_abs_code": 127,
   "max_abs_x0": 127.00000762939453,
   "max_abs_x0_tensor": "model.layers.9.self_attn.v_proj.weight",
   "max_amax": 1.234375,
   "max_amax_tensor": "model.layers.27.mlp.up_proj.weight",
   "min_nonzero_amax": 0.00171661376953125,
   "min_nonzero_amax_bits": "0x3AE10000",
   "min_nonzero_amax_tensor": "model.layers.21.self_attn.k_proj.weight",
   "nan_elements": 0,
   "tensors": 196,
   "undefined_blocks_any_class": 0
  }
 }
}
```
