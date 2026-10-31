# AMB-022 read-back mapping audit

| Field | Value |
|---|---|
| Role | **Independent reviewer** for LARQL-VERIFY-001, auditing for the protocol owner. Not the reference checker, not the spec author |
| Date | 2026-10-31 |
| Subject | `refcheck/readback.py` `MAPPING` (43 entries) and `compare_readback`, checker commit **`310c174`**, extracted with `git -C checker archive 310c174 \| tar -x` into the scratch directory. The live checker tree was not used and the checker repository was not modified |
| Decisions | PROTOCOL.md D7 and D8 (`19ab645`). D7: read-back normalisation is allowed "as an explicit mapping only … never a licence to ignore a real difference" |
| Also read (extracted copy) | `AMBIGUITIES.md` AMB-022 (and AMB-023 to AMB-025 for context), `refcheck/d7.py`, `refcheck/harness.py` (`build_model`, `reference_run`), `refcheck/pins.py` (dtype pin), `refcheck/config_compare.py` (`Authority`, `reference_resolution`, `expected_spans`) |
| Library source | transformers 5.5.0 and torch 2.14.0 under `checker/.venv/lib/python3.12/site-packages/` |
| Not read | the reviewer repository and hidden cases, `evidence/decisions/`, LARQL source |
| Executed | `checker/.venv/bin/python -I` with the extracted copy on `sys.path`. Tiny randomly initialised Qwen3 stand-ins (hidden 64, 4 layers, vocab 256) were constructed and read back. No forward pass, no real weights. Script: `<scratch>/amb022/controls.py`, raw output `<scratch>/amb022/out.jsonl` |

Abbreviations: `rb` = `refcheck/readback.py` at `310c174`; `hz` = `refcheck/harness.py`; `pn` = `refcheck/pins.py`. Library paths: `T/` = `transformers/`; `cq3` = `T/models/qwen3/configuration_qwen3.py`; `mq3` = `T/models/qwen3/modeling_qwen3.py`; `cu` = `T/configuration_utils.py`; `mru` = `T/modeling_rope_utils.py`; `mu` = `T/modeling_utils.py`.

## 0. How the mapping is used (affects every judgement below)

- **Production path.** `hz:464-468` (`reference_run`) builds the reference from the authority's own `plain` dict and refuses any other `config_dict`. `d7.assess_reference` then reads the model back (`rb:157-194`) and compares it with **the same** authority (`rb:237-304`). So in production the read-back tests whether transformers 5.5.0 *interpreted* the authority as the mapping says. It cannot see a difference the library did not create.
- **Direction.** `compare_readback` iterates over the **read-back's** keys (`rb:249`) and over `MAPPING` entries missing from the read-back (`rb:289-291`). It never iterates over the authority's keys. An authority key the library silently drops (generation parameters at `cu:275-277`, `rope_scaling`/`rope_theta` at `mru:706, :715`, `torch_dtype` at `cu:241`) is never compared by the read-back itself. Only the build-from-authority rule makes that safe.
- **Rules as implemented** (`rb:257-286`):
  - `equal`: type-aware exact equality;
  - `equal_or_default`: equality, or the stated default when the authority omits the key;
  - `fixed`: the read-back is compared with a constant, never with the authority;
  - `ignored`: recorded, not compared, and exempt from the "missing" check;
  - `pin`: delegated to `pins.py`;
  - `derived`: bespoke functions at `rb:307-369`, plus the module checks at `rb:371-498`.

## 1. Entry-by-entry classification

Classes:
- **(i)** exact identity;
- **(ii)** representation-only normalisation, or a non-computational entry, with the semantics justified from the library source;
- **(iii)** a default insertion or transformation that could conceal a real mismatch.

Ranks:
- **A** accept;
- **R** record explicitly;
- **C** correct before freeze;
- **X** critical.

### 1.1 Config keys (36)

| # | Key | Rule (`rb` line) | Class | Rank | Justification and source |
|---|---|---|---|---|---|
| 1 | `attention_bias` | equal (55) | i | A | Same name and boolean; read by `mq3:236-247` |
| 2 | `attention_dropout` | equal_or_default 0.0 (56) | ii | A | The default equals the class default `cq3:81`; an absent key builds the identical module (`cu:93-96`). Used only when training (`mq3:283`), and eval mode is pinned |
| 3 | `head_dim` | equal (57) | i | A | `mq3:230` |
| 4 | `hidden_act` | equal (58) | i | A | `mq3:79`. The module class is checked separately (#41) |
| 5 | `hidden_size` | equal (59) | i | A | — |
| 6 | `intermediate_size` | equal (60) | i | A | `mq3:75-78`; widths also enforced by strict `load_state_dict` (`hz:181-184`) |
| 7 | `layer_types` | derived (61-63; `rb:352-368`) | ii | **C** | Authority `layer_types` if declared, else `cq3:94`'s rule on the resolved window; this matches `cq3:91-97`. **Defect:** a declared `"sliding_attention"` with a resolved `sliding_window` of `None` is accepted, giving the expected span `("sliding", None)`. Control 13: the read-back **passes**; the run then fails only by a `TypeError` raised inside the cache pin (`pn:139` → `T/cache_utils.py:178`), not with a structured reason |
| 8 | `max_position_embeddings` | equal (64) | i | A | Read only for `max_seq_len_cached` (`mq3:91-92`), which only dynamic RoPE uses |
| 9 | `max_window_layers` | equal (65) | i | A | `cq3:94` |
| 10 | `model_type` | equal (66) | i | A | — |
| 11 | `num_attention_heads` | equal (67) | i | A | — |
| 12 | `num_hidden_layers` | equal (68) | i | A | — |
| 13 | `num_key_value_heads` | equal (69) | i | A | — |
| 14 | `rms_norm_eps` | equal (70) | i | A | Authority text converted to binary64 and compared exactly. Control 20 shows a one-ulp difference is caught |
| 15 | `rope_parameters` | derived (71-73; `rb:307-330`) | **iii** | **C** | `rope_type == "default"` ⇔ authority `rope_scaling: null` is justified (`mru:706-708, :742`; `mq3:96-100`). Only `{rope_theta, rope_type}` are allowed, and any other key is unmapped (`rb:118, :311-314`). **Defect:** the expected θ is always the authority's *top-level* `rope_theta` (`rb:326`). When the authority itself declares `rope_parameters`, transformers 5.5.0 takes θ from there and the top-level key only fills a gap (`mru:707, :715-716` `setdefault`). The mapping's claim "`rope_parameters['rope_theta']` is the authority's `rope_theta`" is then false. Control 5 (cross): a reference with θ = 10⁶ **passes** against an authority whose reference meaning is θ = 10⁴. In production it fails safe (control 5, self mode, is invalid), but the reason is reported as a value difference, not as an unsupported authority form |
| 16 | `sliding_window` | derived (74-76; `rb:333-349`) | ii | **R** | Same resolution as `cq3:87` (`null` unless `use_sliding_window` is true). Requires both authority keys, else invalid. **Scope:** it accepts a non-null authority window, either inert (`use_sliding_window: false`, control 10) or active (control 9). D8 says no case covers a non-null authority window and D7's window derivations are limited to `null`. The read-back does not enforce that limitation |
| 17 | `tie_word_embeddings` | equal (77) | i | A | The tie itself is the weight-tie pin (`hz:166-169`, AMB-025) |
| 18 | `use_cache` | equal_or_default True (78) | ii | A | Class default `cq3:73`. The harness passes `use_cache=True` and an explicit cache (`hz:225-235`), so the config value is never used |
| 19 | `use_sliding_window` | equal (79) | i | A | — |
| 20 | `vocab_size` | equal (80) | i | A | — |
| 21 | `bos_token_id` | equal_or_default None (81) | ii | A | Class default `cq3:83`. Not read in `mq3`'s forward; token IDs are supplied directly |
| 22 | `eos_token_id` | equal_or_default None (82) | ii | A | Class default `cq3:84`. Generation only |
| 23 | `pad_token_id` | equal_or_default None (83) | ii | A | Class default `cq3:82`. Used only as `nn.Embedding(padding_idx=…)` (`mq3:360, :363`), which affects only the gradient and the initial row (`torch/nn/modules/sparse.py:24-28`). Weights are loaded and checked bit for bit (`hz:181-187`) |
| 24 | `initializer_range` | equal_or_default 0.02 (84) | ii | A | Class default `cq3:71`. Read only by `_init_weights` (`mu:2291-2299`). Every parameter is then overwritten by a strict load and verified bit for bit (`hz:181-187`) |
| 25 | `dtype` | pin (86) | ii | **R** | Not compared. `config.dtype` is the file's load dtype (bfloat16 from `torch_dtype`, `cu:241-249`). The dtype pin asserts parameter dtypes, float buffer dtypes and torch's default dtype (`pn:89-101`) and records `config.dtype`. No forward code in `mq3` or `T/masking_utils.py` reads `config.dtype`. Delegation is correct, but D7 makes it a separate obligation and it should stay listed as such |
| 26 | `architectures` | ignored (87) | ii | A | The model class is fixed by the harness (`hz:179`, `Qwen3ForCausalLM._from_config`); `architectures` selects only `Auto*` classes. Control 28 |
| 27 | `_name_or_path` | ignored (88) | ii | A | Provenance string; never read in a forward |
| 28 | `transformers_version` | ignored (89) | ii | A | In `cu` it is used only for serialisation (`cu:965, :1000, :1014`) and versioned config-file selection on the hub (`cu:1296-1298`), not by `_from_config` or the forward |
| 29 | `id2label` | ignored (90) | ii | A | Used only by classification heads (`T/modeling_layers.py:102-105, :238-248`); `Qwen3ForCausalLM` has none |
| 30 | `label2id` | ignored (91) | ii | A | As #29 |
| 31 | `problem_type` | fixed None (92) | i | A | Constant identity. An authority setting another value fails (it reaches the read-back) |
| 32 | `is_encoder_decoder` | fixed False (93) | i | A | As #31 |
| 33 | `chunk_size_feed_forward` | fixed 0 (94) | i | A | `mq3` never chunks (no `apply_chunking_to_forward`), so non-zero is inert, but it is still refused (control 27, over-strict, harmless) |
| 34 | `output_attentions` | fixed False (95) | i | A | Output selection only |
| 35 | `output_hidden_states` | fixed False (96) | i | A | Output selection only |
| 36 | `return_dict` | fixed True (97) | i | A | Output container only |

### 1.2 Module-level entries (7)

| # | Key | Rule (`rb` line) | Class | Rank | Justification and source |
|---|---|---|---|---|---|
| 37 | `module:attn_per_layer` | derived (99-100; `rb:386-406`) | i | **R** | Per layer: `head_dim`, KV groups, projection widths, the four bias flags against `attention_bias`, Q/K-norm length, layer count. All are exact equalities with authority-derived integers. `scaling` is compared with `float(hd) ** -0.5`, the library's own expression (`mq3:232`). That checks construction, not D8's exactly rounded value. D8's exact rule applies to the container's declared scale, and `128**-0.5` is the correctly rounded value (D2 assessment row 17), so this is fine for the subject. Recorded because it is circular by design |
| 38 | `module:spans` | derived (101-102; `rb:408-427`) | ii | **C** | The module's `layer_type`/`sliding_window` against `expected_spans` of the authority resolution (D7: "spans from the reference"). It inherits #7's defect: `("sliding", None)` is accepted as an expected span |
| 39 | `module:norm_eps` | derived (103-104; `rb:429-441`) | i | A | Every input, post, Q-norm, K-norm and final-norm epsilon equals binary64(authority `rms_norm_eps`) (`mq3:248-249, :302-303, :367`) |
| 40 | `module:activation` | derived (105-106; `rb:443-453`) | ii | A | Accepts `SiLUActivation` or `SiLU` for `silu`/`swish` (`rb:116`). `T/activations.py:336-337` registers `silu → SiLUActivation` (`F.silu`, `:93-104`) and `swish → nn.SiLU`, the same function. Any other `hidden_act` is invalid (control 21) |
| 41 | `module:rope_table` | derived (107-108; `rb:455-476`) | ii | **R** | `rope_type == "default"`, `attention_scaling == 1.0` (`mq3:127`), `inv_freq` equal to the library's own formula (`mq3:130-131`) in the run dtype. This checks that the table was built from the authority's θ and `head_dim`. It is not an independent check of RoPE semantics; #43 and the D2 assessment cover those |
| 42 | `module:shapes` | derived (109; `rb:478-486`) | i | A | Embedding and head are `[vocab, hidden]` |
| 43 | `module:rope_convention` | derived (110-111; `rb:488-492`, probe `rb:135-154`) | i | A | Runs the library's `apply_rotary_pos_emb` on exact dyadic inputs (exact in binary32/64) and requires the SPEC rev 4 §17.5 output exactly; it also detects the opposite direction. An independent, non-circular check |

**Counts:** (i) **25** (15 `equal`, 6 `fixed`, 4 module); (ii) **17** (6 `equal_or_default`, 2 derived config keys, 5 `ignored`, 1 `pin`, 3 module); (iii) **1** (`rope_parameters`).

**Is anything computation-relevant ignored?**
- None of the five `ignored` keys, nor `dtype`, nor the six `fixed` keys can change a teacher-forced, eval-mode, eager forward of `Qwen3ForCausalLM` (sources above).
- Computation-relevant settings outside the mapping are each covered by a D7 pin: attention implementation, hub kernels, eval mode, cache class and positions, weight tie, and the f64 patch.
- What the read-back does not do is look at **authority** keys the library drops (§0). That is safe only because of `hz:467`.

## 2. Negative controls

**Method.** Base config = the pinned `config.json` with only the sizes shrunk (hidden 64, intermediate 128, 4 layers, 4/2 heads, head_dim 16, vocab 256, `max_window_layers` 4). Every other key is as pinned. Each control modifies the base and is run in two modes:
- **Self:** reference built from X, authority X. This is the production path (`hz:464-468`).
- **Cross:** reference built from the base, authority X. This asks whether a difference between what the reference holds and what the authority means is caught. It is not reachable through `reference_run`, but it is the only way to test the comparison logic itself.

**Expected outcomes.**
- **Self:** invalid when X is outside what the mapping or SPEC supports (label **(a) unsupported but valid**); pass when X is supported.
- **Cross:** invalid when X's meaning under the pinned reference differs from the base (label **(b) real contradiction**), or when X is unsupported (label (a)); pass only when the computation is identical and supported.

All runs used the f32 path. "invalid" below is `d7.assess_reference` status `invalid`.

| # | Control | Self: expected / actual | Cross: expected / actual | Verdict |
|---|---|---|---|---|
| 1 | baseline | pass / **pass** | — | OK |
| 2 | `rope_scaling: {rope_type: linear, factor: 2}` | invalid (a) / **invalid** (`rope_parameters.factor` unmapped; rope_type `differs`) | invalid (b) / **invalid** | OK. The self reason says "differs", not "unsupported" |
| 3 | `rope_scaling: {factor: 2}` (no type) | invalid (a) / **invalid** | invalid (a) / **invalid** | OK (conservative: the library treats it as default RoPE and ignores `factor`) |
| 4 | `partial_rotary_factor: 0.5` | invalid (a) / **invalid** (unmapped) | invalid (a) preferred / **pass** | Cross pass: Qwen3's default RoPE ignores the factor (`mq3:124-133`), so the reference computation is identical; the authority key is simply never examined (§0). Not a false acceptance of a reference difference. **R** |
| 5 | authority declares `rope_parameters: {default, θ=10000}` beside top-level `rope_theta: 1000000` | invalid (a) / **invalid** (reported as `rope_theta` differs) | invalid (b) / **pass** | **FAILED (cross).** The reference meaning of X is θ = 10⁴ (`mru:707, :715-716`); a θ = 10⁶ reference passed. **C** (see #15) |
| 6 | `rope_theta: 10000` | pass / **pass** | invalid (b) / **invalid** | OK |
| 7 | `rope_theta` absent | invalid (a) / **invalid** (library default 10000 refused) | invalid / **invalid** | OK |
| 8 | `rope_scaling` absent | invalid (a) / **invalid** | invalid (a) / **invalid** | OK (conservative) |
| 9 | `use_sliding_window: true, sliding_window: 8, max_window_layers: 2` | invalid (a), per D8 scope / **pass** | invalid (b) / **invalid** | **FAILED (self) against D8's scope:** the read-back accepts an active window. The library and mapping agree (layers 2-3 sliding), so this is not a hidden mismatch. **R/C** (§3) |
| 10 | `use_sliding_window: false, sliding_window: 8` (inert) | invalid (a) per D8, or explicitly accepted / **pass** | same / **pass** | Computation identical (`cq3:87`), but the authority window is non-null, outside D7/D8. **R** |
| 11 | `use_sliding_window` absent | invalid (a) / **invalid** | invalid / **invalid** | OK (conservative) |
| 12 | `max_window_layers: 2`, window null | pass / **pass** | invalid (b, by key) / **invalid** | OK (inert, but caught by `equal`) |
| 13 | `layer_types` declared, layer 2 `"sliding_attention"`, window null | invalid (a), structured / read-back **pass**, run **refused by `TypeError`** in `pn:139` (`DynamicCache` → `cache_utils.py:178`) | invalid (b) / **invalid** | **FAILED (self):** the read-back accepts an incoherent span `("sliding", None)`; the refusal is accidental and unstructured. **C** |
| 14 | `layer_types` declared, all full | pass / **pass** | pass / **pass** | OK |
| 15 | `attention_dropout: 0.1` | pass / **pass** | invalid (b, by key) / **invalid** | OK (inert in eval, `mq3:283`) |
| 16 | `attention_dropout` absent | pass / **pass** | pass / **pass** | OK (class default) |
| 17 | `pad_token_id: 5` | pass / **pass** | invalid (by key) / **invalid** | OK. Inert: `padding_idx` affects only gradient and initialisation (`sparse.py:24-28`), and weights are verified after loading |
| 18 | `initializer_range: 0.5` | pass / **pass** | invalid (by key) / **invalid** | OK. **Irrelevant** because it is read only by `_init_weights` (`mu:2291-2299`), and every parameter is overwritten by a strict load and compared bit for bit with its source (`hz:181-187`). The only buffer, `inv_freq`, is computed from θ and `head_dim`, not initialised |
| 19 | `rms_norm_eps: 1e-5` | pass / **pass** | invalid (b) / **invalid** | OK |
| 20 | `rms_norm_eps` one binary64 ulp above `1e-6` | pass / **pass** | invalid (b) / **invalid** | OK (no tolerance) |
| 21 | `hidden_act: gelu` | invalid (a) / **invalid** | invalid (b) / **invalid** | OK |
| 22 | `attention_bias: true` | pass / **pass** | invalid (b) / **invalid** | OK |
| 23 | `tie_word_embeddings: false` | pass / **pass** | invalid (b) / **invalid** (+ weight-tie pin) | OK |
| 24 | head split 8 × 8 instead of 4 × 16 | pass / **pass** | invalid (b) / **invalid** | OK (D3 Q16) |
| 25 | `attention_multiplier: 0.5` | invalid (a) / **invalid** (unmapped) | invalid (a) preferred / **pass** | Cross pass: Qwen3 ignores the key (`mq3:232`), so the reference computes the same. The LARQL writer would change its stored scale (SPEC §17.4), which the container comparator sees. **R** |
| 26 | `query_pre_attn_scalar: 64` | invalid (a) / **invalid** | invalid (a) preferred / **pass** | As 25. **R** |
| 27 | `chunk_size_feed_forward: 4` | invalid / **invalid** (fixed) | pass acceptable / **pass** | OK (not used by `mq3`) |
| 28 | `architectures: [LlamaForCausalLM]` | pass / **pass** | pass / **pass** | OK (harness fixes the class) |
| 29 | `torch_dtype: float32` | pass / **pass** | pass / **pass** | OK (dtype pin) |
| 30 | `max_position_embeddings: 128` | pass / **pass** | invalid (by key) / **invalid** | OK |
| 31 | `use_cache: false` | pass / **pass** | invalid (by key) / **invalid** | OK (the harness passes `use_cache=True`) |
| 32 | `temperature: 0.7` (generation key) | pass / **pass** | pass / **pass** | OK (popped at `cu:275-277`, generation only) |

**Label of every not-comparable outcome.**
- All self-mode invalids (controls 2, 3, 4, 5, 7, 8, 11, 21, 25, 26, 27) are **(a) unsupported but valid**: the reference was built from the authority, so no contradiction is possible.
- All cross-mode invalids (2, 3, 6, 7, 8, 9, 11, 12, 13, 15, 17-24, 30, 31) are **(b) a real contradiction** between the held reference and the authority. The exceptions are controls 3, 7, 8 and 11, which are (a) because the authority is also unsupported, and 12, 15, 17, 18, 30 and 31, which are contradictions in a key whose computational effect is nil.
- **The checker's reasons do not make this distinction.** Unsupported configurations are reported as `read-back differs: … expected '<absent>'` (controls 2, 7, 8, 11) or as `unmapped`, which reads like a value contradiction.

## 3. Verdict

**Class (iii) entries:** one.

- **#15 `rope_parameters` (correct before freeze).** The expected θ ignores an authority-declared `rope_parameters`. Demonstrated by control 5 (cross).
  - Not reachable as a false acceptance on the production path, because `hz:467` builds the reference from the authority, and self mode fails safe.
  - It would become critical if the read-back were ever reused against a reference not built from the authority.
  - **Remedy:** if the authority contains a `rope_parameters` key (or any 5.x-style RoPE key), report "unsupported authority form" (a). Otherwise derive the expected value with the library's own priority: `rope_parameters`, then top-level, then default, compared as the library resolves it. Add control 5 as a fixed regression case.

**Controls that passed when they should have failed:**

1. **Control 5, cross** (above). Correct before freeze.
2. **Control 13, self: the read-back accepts `"sliding_attention"` with a resolved window of `None` (#7, #38).** Correct before freeze.
   - **Remedy:** in `_expected_layer_types`/`expected_spans`, any `"sliding_attention"` with a resolved `sliding_window` of `None` is invalid (a), "sliding layer without a window".
   - Also: `reference_run`/`assess_reference` should convert any exception during pins or read-back into a structured `invalid` record (D8: "a structured reason naming each affected field"), not let a `TypeError` escape.
   - Also check that the container comparator never matches a container `span: "sliding"` with no `window` against an expected `("sliding", None)`. LARQL runs that span as full attention (SPEC §17.8).
3. **Controls 9 and 10, self: non-null authority `sliding_window` accepted (#16).** Correct before freeze, unless the owner accepts it explicitly.
   - D8 limits the campaign to `sliding_window: null`.
   - **Remedy:** either make a non-null authority `sliding_window` invalid (a), "outside the D7/D8 window scope", in the read-back and the comparator; or have the owner record that inert windows (`use_sliding_window: false`) are accepted. Control 10's computation really is identical (`cq3:87`).
4. **Controls 4, 25 and 26, cross** (`partial_rotary_factor`, `attention_multiplier`, `query_pre_attn_scalar`). Record explicitly.
   - They passed, but the pinned reference ignores these keys, so the reference computation is genuinely unchanged. No false acceptance of a reference difference.
   - **Remedy:** record in AMB-022 that the read-back does not examine authority keys, and that the guarantee rests on `hz:467` (build from the authority) together with the comparator's own authority-key audit. Optionally add an authority-side completeness pass: every authority key must be a mapped key, a known popped key (generation parameters, `torch_dtype`, `rope_scaling`, `rope_theta`), or rejected as (a).

**Ranked findings:**

- **Critical (false acceptance on the production path):** none found.
- **Correct before freeze:**
  - #15 `rope_parameters` authority-form defect (control 5);
  - #7/#38 sliding layer without a window accepted, and the unstructured crash (control 13);
  - non-null authority windows accepted against D8 scope (controls 9 and 10, #16), unless the owner explicitly accepts the inert case;
  - reasons that do not distinguish **(a) unsupported** from **(b) contradiction** (§2). Add a reason category to every `unmapped`/`differs` row: "authority form or value unsupported by the mapping or SPEC" versus "the reference holds X, the authority means Y".
- **Record explicitly:**
  - read-back direction and the reliance on `hz:467` (§0);
  - `dtype` delegated to the pin (#25);
  - circular construction checks for `scaling` and `inv_freq` (#37, #41), with the independent semantics carried by #43, the container comparator (D8 exact scale) and the D2 assessment;
  - the cross-mode passes of controls 4, 25 and 26;
  - the over-strict `fixed`/`equal_or_default` refusals of inert values. These are acceptable false invalids, never false passes.
- **Accept:** the remaining 36 entries — 24 class (i) and 12 class (ii), excluding #7, #15, #16, #25, #37, #38 and #41. The `equal_or_default` defaults (#2, #18, #21-#24) are the library's own class defaults (`cq3:71-84`) for keys with no effect on a teacher-forced, eval-mode forward. The `ignored` keys are non-computational. Absent `rope_theta`, `rope_scaling` and `use_sliding_window` correctly cause rejection.
