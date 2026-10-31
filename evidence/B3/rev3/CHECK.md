# B3 third-party check: VINDEX3 container specification, revision 3 draft

| Field | Value |
|---|---|
| Role | **Third-party checker** for LARQL-VERIFY-001 workstream B3. Not the spec author, not the reference-checker agent |
| Date | 2026-10-31 |
| Draft checked | `evidence/B3/rev3/SPEC.md`, SHA-256 `2d5258798b6a9b5373e1d346fbbfe99fb087a64cab26aee0d7558f694f93f4aa` (verified before starting; not edited) |
| Admitted base | `specs/vindex3-container/SPEC.md` (revision 2), SHA-256 `3c4feb5e01f2c262e06e1f8579754921089cda46038f17c63cfd42f9d0c5fe50` (verified; not edited) |
| Author notes | `evidence/B3/rev3/AUTHOR-NOTES.md`, SHA-256 `3946d77206550fdfd661064084689c346c36caa2ed73f93f349c86c952e954c4` |
| Container checked | `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`, read only. All 11 files match `evidence/L1/container-q8_0.sha256` (`shasum -a 256 -c`: 11/11 OK). `system_graph.json` `05fcec4c45167c2f8f424c35b8c39acb06cc92716f11e0ffbec341e110d66f57`; `index.json` `7f3ba8e5da50276e501e7694c46c0a3c9c9d7530596656376cc9597f05fec490` |
| Upstream configuration | `~/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca/config.json`, SHA-256 `660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd` (verified) |
| LARQL source | `/Users/christopherhay/chris-source/larql-l1-2536bb79`, HEAD `2536bb79b199b1115445678e3e82c400b0b3fd07`, `git status --porcelain` empty. Read only; nothing built or run. `/Users/christopherhay/chris-source/larql` not read |
| Tools | `checker/.venv/bin/python -I`, used as an interpreter only (stdlib + numpy). `refcheck` not imported; nothing under `checker/` read |
| Script / raw output | `evidence/B3/rev3/check/check_rev3.py` (SHA-256 `7edaa0f656e69eb1c1bc4789ab67c39ca31a49448a78d3f7df8ad7d09fc87cf5`), `check/rev3_stdout.json` (`2eb2b3ea…`), `check/rev3_results.json` (`ad5baa9b…`, every assertion) |

## Verdict

**ADMIT WITH CORRECTIONS.** No normative statement of revision 2 changed. Every normative §17 claim I tested against the emitted `system_graph.json`, `index.json`, the segment headers and the upstream `config.json` held: 605 assertions, 0 failures. Every key present under the execution surface and under the 28 per-layer attention entries is covered by §17, and every key §17 says must be absent is absent. All 23 consumption claims in §17.8 are confirmed by the cited code. None is refuted. The corrections below fix one internal inconsistency, one gap in the unknown-key rule, and one incomplete informative citation. None changes a value, a type or a comparison rule.

### Corrections

- **C1 (§0, internal consistency).** The revision 2 bullet "This document describes only container framing. It does not describe … reference execution semantics … Where the container stores a field with a numerical meaning, this document gives its name and byte position only" is unchanged, and §17 now contradicts it: §17 states the RMSNorm formula, the RoPE pairing and angle, the span semantics and the FFN combine. The new revision 3 bullet sets up the exception but does not amend the old one. *Fix:* qualify the old bullet with "except §17 (revision 3), which gives meanings for comparison only". This changes no rule; it makes the old sentence true again.
- **C2 (§17.1 unknown keys, completeness).** The rule covers keys under `X` and under each `C.attention[L]` only. LARQL's `Component` type has one more optional field, `perception` (`VX/graph/component.rs`, after `execution`). §17 does not mention it, so a comparator neither requires it to be absent nor flags it. No LARQL struct uses `deny_unknown_fields`, so `exec` silently ignores any unknown key anywhere in the graph. *Fix:* extend the §17.1 rule to keys directly on `C` other than `id`, `role`, `source_artifact`, `num_layers`, `hidden_size`, `attention` and `execution`, and state that `C.perception` MUST be absent in this profile. It is absent in the container. For a `primary_text` component, `exec` does not read it today (it is consulted only under `role: Perception`, `VX/graph/build/components.rs:242-253`).
- **C3 (§17.8, informative citation).** The row for `X.attention.attention_bias`/`qkv_bias` cites `exec/production.rs:473-484` for "production adds a bias only when one is bound". Those lines add the Q/K/V biases only. The output-projection bias is added at `VX/opplan/exec/production/helpers.rs:19`. *Fix:* add that citation. The claim itself is right.

Advisory, not required for admission:

- **A1 (§17.6).** The writer's rule is `!has_lm_head() || tie_word_embeddings != Some(false)` (`LM/config/architecture/tensor_keys.rs:54`). `has_lm_head()` is `true` by default (`:33-35`), and Qwen3 does not override it, so §17.6's "stores `true` unless `tie_word_embeddings` is declared exactly `false`" is correct for this profile. Saying "for this family" would stop the sentence being read as a general rule.
- **A2 (§0/§3).** "Comparator" is defined only in §17.1, and the §3 unknown-key sentence points to §14 only. A pointer from §3 to §17.1 would help.

## Check 1: diff from revision 2

`diff specs/vindex3-container/SPEC.md evidence/B3/rev3/SPEC.md` gives 10 hunks, 241 changed lines (656 → 885 lines, net +229). Every changed line:

| Rev 2 → rev 3 lines | Section | Change | Class |
|---|---|---|---|
| 7c7 | Header, Revision row | "2 … applies those corrections" → "3 … Revision 2 (SHA-256 `3c4feb5e…`) was admitted … adds §17 … changes no normative statement of revision 2" | Pointer / metadata |
| 7c8 (new row) | Header | Upstream configuration (§17 only): `config.json` path and SHA-256 `660db3b7…` (matches) | Addition |
| 23a25 | §0 | New bullet: §17 is the one place execution-surface meanings are given; §17.8 informative | Addition (see C1) |
| 216c218 | §6 | Appends "(Revision 3: a program that compares … reads the fields specified in §17.)" | Pointer |
| 263c265 | §8.2 | "(computed, by the safetensors convention)" → "(observed)", citing the check. The statement is unchanged | Marker fix (closes rev-2 finding E1) |
| 531c533 | §16 U5 | Marked "PARTLY CLOSED (revision 3)", with the remaining scope stated | Status / pointer (not normative) |
| 532a535-593, 533a595-718 | New §17 | 183 lines: §17.1-§17.8 (diff splits the insertion at one blank line) | Addition |
| 536c721 | Appendix A preamble | Adds abbreviations `LM`, `LC` and the rule for unprefixed paths in §17.8 | Addition |
| 649a835-877 | Appendix A | Sources S110-S152 (43 rows) | Addition |
| 656c884 | Revision history, row 2 | "(this file)" → rev 2's SHA-256 `3c4feb5e…` (correct) | Pointer |
| 656c885 (new row) | Revision history, row 3 | Rev 3 change list. It matches the hunks above exactly | Addition |

**Normative statements of revision 2: unchanged.** No hunk touches §1-§5, §7, §8.1, §8.3-§15, or any rejection or layout rule. The only hunks inside revision 2's sections are a pointer (§6), a marker (§8.2), a status cell (§16) and the header/§0 additions. §0 is the one place where the meaning, though not the text, of a revision 2 sentence is affected (C1).

**§3 "unknown keys ignored unless this document says otherwise" and §17.1.** §3 (line 79) obliges a *reader*, which §0 defines as a program that locates and identifies tensors. §17.1's rule is addressed to the *comparator* and covers only keys under `X` and `C.attention[L]`. It says explicitly that the §3 rule "does not extend to the comparison". It adds no obligation on a reader, and does not touch the other unknown-key rules (segment headers, §4.2 line 122; `index.json`, §5.2 line 168 and §14 line 503). **It changes scope only for a configuration comparator.** Confirmed. Its coverage is narrower than it could be (C2).

## Check 2: §17 normative claims against the emitted files

The script is my own and was written from the draft alone. It reads only `index.json`, `system_graph.json`, the five segment headers (no payloads) and `config.json`. Run: `python -I check_rev3.py <container> <config.json> rev3_results.json`. Exit 0.

| Group | Pass / fail | What was asserted |
|---|---|---|
| inputs | 3 / 0 | SHA-256 of `system_graph.json`, `index.json`, `config.json` |
| §17.1 | 3 / 0 | `index.json.system_graph` names the graph; exactly one component; its `id` is `"target"` |
| §17.2 | 158 / 0 | `C.num_layers` 28, `C.hidden_size` 1024 (integers); `C.attention` has 28 elements; `X` present; `X.attention.num_q_heads` 16, `num_kv_heads` 8, `head_dim` 128; **at all 28 layers** `geometry` present with exactly `{head_dim: 128, num_kv_heads: 8}` (integers); `X.ffn.intermediate_size` 3072; `intermediate_size_by_layer` absent; `X.head.vocab_size` 151936; `X.context_length` 40960. Upstream: `num_hidden_layers`, `hidden_size`, `num_attention_heads`, `num_key_value_heads`, `head_dim`, `intermediate_size`, `vocab_size`, `max_position_embeddings` all equal. `index.json` `hidden_size`/`num_layers` equal; `index.json.family` `"qwen3"` = upstream `model_type`. Shapes: in both decoder segments (BF16, Q8_0), layer indices are exactly 0..27, and all 28 × 11 per-layer shapes equal the §17.2 formulas (q `[2048,1024]`, k/v `[1024,1024]`, o `[1024,2048]`, q/k-norm `[128]`, gate/up `[3072,1024]`, down `[1024,3072]`, two norms `[1024]`); embedding and output head `[151936,1024]`; final norm `[1024]` |
| §17.3 | 36 / 0 | `X.norm.pre` and `X.norm.final_norm` each have exactly `{kind, eps, weight_offset}`; `kind` `"rms_norm"`; `eps` = `9.999999974752427e-7` = `f64(f32(1e-6))` exactly, and ≠ `1e-6`; raw text writes `"eps": 9.999999974752427e-7` at both sites; `weight_offset` 0.0, exactly binary32; `X.norm.post` absent; `placement` `"pre_only"`; `X.norm` keys ⊆ {pre, post, final_norm, placement} |
| §17.4 | 34 / 0 | `score_scale` = `0.08838834764831845` = `math.pow(128, -0.5)`; `1/sqrt(128)` = `0.08838834764831843`; the stored value is exactly 1 ulp above it; both round to binary32 `0.0883883461356163`; upstream declares neither `attention_multiplier` nor `query_pre_attn_scalar`. `query_scale`, `logit_softcapping`, `qkv_bias`, `output_gate`, `sinks` absent. `attention_bias` `false` (boolean) = upstream. `qk_norm_scope` `"per_head"`; `qk_norm_weight_offset` 0.0 (binary32); `parameter_free_qk_norm` `{q,k,v: false}`. In both decoder segments: no bias tensors, and `q_norm` and `k_norm` at all 28 layers |
| §17.5 | 313 / 0 | **At all 28 layers:** `operator` `"softmax"`; `span` `"full"`; `window` absent; `position` exactly `{kind: "rope", theta: 1000000.0}`; theta = upstream `rope_theta`; `v_from_k` absent; `declared_span` absent; `geometry` = upstream `head_dim`/`num_key_value_heads`; no key outside the AttentionLayerPolicy list. Raw text has 28 × `"theta": 1000000.0`. Upstream preconditions for the resolution rules: `use_sliding_window` false and `sliding_window` null (rule 1 → not sliding); no `layer_types`; `rope_scaling` null; no `partial_rotary_factor`/`rope_parameters` |
| §17.6 | 36 / 0 | `ffn_type` `"gated"`; `activation` `"silu"` = map(upstream `"silu"`); `gate_policy` `{kind: "gated"}`; `moe` absent; `head_reuses_embedding` `true`, consistent with upstream `tie_word_embeddings: true`; `embed_scale`, `output_multiplier`, `final_logit_softcapping`, `embedding_norm` absent; `residual_topology` `{kind: "single_stream"}`; `residual_scale`, `residual_in_fp32` absent; the eight must-be-absent keys (`linear_attention`, `kda`, `kda_gate_lower_bound`, `kda_gate_form`, `kda_use_full_rank_gate`, `mla`, `mamba2`, `conv_qkv`) all absent |
| §17.7 | 19 / 0 | `output_head@BF16.payload_sha256` = `embedding@BF16.payload_sha256` (`8f29acf5…`); both objects present; D2's 16 keys all exist in `config.json`; the "Upstream value" column equals `config.json` for all 16, including type (`rope_theta` integer `1000000`, `rms_norm_eps` `1e-06`, three `null`s) |
| coverage | 3 / 0 | Every key present under `X`, recursively (40 paths), is listed in §17. Every key present under any `C.attention[L]`, recursively (`operator`, `span`, `position`, `position.kind`, `position.theta`, `geometry`, `geometry.head_dim`, `geometry.num_kv_heads`), is listed. The component's own keys are `id, role, source_artifact, num_layers, hidden_size, attention, execution` |
| **Total** | **605 / 0** | |

**Schema claims spot-checked against the serde types** (the "When absent" column): `AttentionSurface`, `FfnSurface`, `NormSurface`, `HeadSurface`, `ExecutionSurface` (`VX/graph/surface.rs:58-481`) and `AttentionLayerPolicy`/`HeadGeometry` (`VX/graph/policy.rs:274-338, 460-464`) agree with every Required/Optional/default statement in §17.2-§17.6. That covers, for example: `residual_topology` defaulting to `single_stream`; `head_reuses_embedding` defaulting to `false`; `gate_policy` defaulting to `gated`; `operator` and `position` required; `attention_bias` as `Option<bool>`. Writer derivations also agree: `eps` is `norm_eps() as f64` from an f32 (`LM/config/architecture/norms.rs:77-83`); the score scale is `scalar.powf(-0.5)` (`LM/config/architecture/shared.rs:33-35`, `attention.rs:135-144`); the sliding resolution order (`attention.rs:39-82`); the `hidden_act` map (`LM/config/activation.rs`, `HF_ACTIVATION_NAMES`) and the SiLU default for absent or unjudged names (`feed_forward.rs:45-52`).

## Check 3: §17.8 execution-path audit

Each row was confirmed by reading the cited file:line at `2536bb79`. Paths: `VX` = `crates/larql-vindex/src/format/vindex3`, `LM` = `crates/larql-models/src`, `LC` = `crates/larql-compute/src`. Backend: `--backend production-q8` resolves to `LoweringIdentity::cpu_production()` → `ProductionBackend` (`CLI/prepare.rs:209-229`, `VX/opplan/exec/lowering.rs:71-76, 226-231`). The plan is built from the container alone, and `config.json` is never opened (`crates/larql-inference/src/vindex3/runtime.rs:88-131`).

| # | Claim (§17.8) | Evidence read | Result |
|---|---|---|---|
| 1 | `C.num_layers`/attention length: plan refuses unless equal; builds `num_layers` records | `VX/opplan/build.rs:321-332`; `build/construct.rs:101-102` | **Confirmed** |
| 2 | `C.hidden_size`: plan shape contracts; **run-time residual width from embedding `shape[1]`** | `build.rs:359` (`let hidden = component.hidden_size`) feeds `StackGeometry`; `exec/prepared/loading.rs:83` `let hidden = embedding.table.shape[1]` | **Confirmed.** Declared value checked, then the shape is used |
| 3 | `X.attention.num_q_heads` used | `build.rs:483`; `construct.rs:620` | **Confirmed** |
| 4 | Surface `num_kv_heads`/`head_dim` used only when a layer lacks `geometry`; **per-layer geometry wins** | `build.rs:477-482` (`attention_table[layer].geometry.map_or_else(‖ surface, ‖ g)`); `construct.rs:620-622` take `geometry.*` | **Confirmed.** Surface copies are not consumed for this container |
| 5 | `C.attention[L].geometry.*` used; GQA `h → h ÷ (q/kv)` | `construct.rs:620-622`; `exec/production/helpers.rs:227` `group = num_q_heads / num_kv_heads`, `:232` `kv_head = q_head / group` | **Confirmed** |
| 6 | `X.ffn.intermediate_size` used | `build.rs:423, 465-470` (`inter_for`); `construct.rs:288-296`; `exec/experts/dense.rs:364` `intermediate: op.intermediate_size` | **Confirmed** |
| 7 | `X.head.vocab_size` checked against shapes; **run-time logit count = head `shape[0]`** | `build.rs:682-703` (`expected [vocab, hidden]`); `exec/prepared/accessors.rs:201` `output.projection.shape[0]` | **Confirmed** |
| 8 | `X.norm.pre` used; **eps executed as binary64 `9.999999974752427e-7`** | `construct.rs:473-476` and `:693` (`norm_op(surface.norm.pre, …)` for both pre sites under `PreOnly`); `exec/prepared.rs:259-266` passes `self.op.eps`; `exec/production/plan_backend.rs:77-92` → `rms_norm_eps(…, call.eps)`; `LC/residual.rs:56-78`: f64 sum of squares, `(sq_sum/cols + eps).sqrt()`, eps as given | **Confirmed.** The stored f64(f32(1e-6)) is executed; no `1e-6` anywhere on the path |
| 9 | QK-norm eps = `X.norm.pre.eps` (no field) | `construct.rs:473` `declared_norm_eps: surface.norm.pre.eps`; `VX/opplan/layer.rs:192-205`; `exec/layer_exec.rs:336-366` and `exec/decode/run.rs:316-324` pass `layer.declared_norm_eps` as `qk_norm_eps`; `exec/attention_ops.rs:126-197` copies it into the call; `exec/production.rs:283, 292` → `rms_norm_qk_eps` → `LC/residual.rs:169-195` (f64) | **Confirmed.** Substitution by design: the QK norms run at the pre-norm epsilon |
| 10 | `X.norm.final_norm` used before head | `construct.rs:728-729`; `accessors.rs:177-185` | **Confirmed** (see new finding N5) |
| 11 | `X.norm.placement`: refuse absent, refuse `post_only`, select operands | `build.rs:229-240, 282-293`; `construct.rs:246-282` (`PreOnly → PostAttentionNorm` for the pre-FFN site) | **Confirmed** |
| 12 | `X.norm.post` read only under `pre_post`/`post_only` | `build.rs:301-320` | **Confirmed** |
| 13 | `score_scale` used, **rounded to binary32** | `construct.rs:624`; `exec/production/helpers.rs:238` `dot * call.score_scale as f32` | **Confirmed.** Executed multiplier `0.0883883461356163` |
| 14 | `query_scale`, `logit_softcapping` applied only when present | `exec/production.rs:295-299`; `helpers.rs:239-242` | **Confirmed** |
| 15 | Biases bound only on `attention_bias: true` (or `qkv_bias` for Q/K/V); **absent executes as `false`** | `construct.rs:219-227` (`== Some(true)`); `exec/production.rs:473-484` (Q/K/V); O bias at `exec/production/helpers.rs:19` | **Confirmed.** Citation incomplete (C3) |
| 16 | `qk_norm_scope`, `qk_norm_weight_offset`: QK-norm record only when `q_norm` tensors exist; per-head weighted RMS | `construct.rs:228-236` (`slot.contains_key(AttnQNorm)`); `exec/production.rs:230-293`; `LC/residual.rs:243-271` dispatches on scope | **Confirmed** |
| 17 | `parameter_free_qk_norm` applied only when set | `exec/production.rs:243-246, 457-468` | **Confirmed** |
| 18 | `span`/`window` select readable keys; sliding without window runs full | `construct.rs:633-641`; `exec/backend/calls.rs:406-408`; `exec/kv.rs:62-71` (`(Sliding, None) \| (Full, _) => Full`); `helpers.rs:228` uses `required_start` | **Confirmed** |
| 19 | `position` used; RoPE inv-freq and angle in f64, sin/cos to f32; **split-half pairing hard-coded** | `construct.rs:641`; `exec/production.rs:304-311`; `exec/kernels.rs:147-158` (`head[i]` with `head[half+i]`, `theta.powf(-2i/len)`); `LM/config/position.rs:28-45` `ROPE_PAIRING_INTERLEAVED = false` | **Confirmed** |
| 20 | `ffn_type`/`activation`/`gate_policy`: SiLU gated → fused kernel; exact `gelu`, `relu` refused; non-plain gates other than SiTU refused | `construct.rs:288-300`; `exec/production/plan_backend.rs:187-200`; `exec/production.rs:125-214` | **Confirmed** |
| 21 | **`head_reuses_embedding` ignored when an output-head object exists** | `build.rs:699-711`: `single(OutputHead, …).or_else(‖ head_reuses_embedding.then(embedding))`. The flag is consulted only in the `or_else` | **Confirmed.** The head operand here is `target.output_head` |
| 22 | `embed_scale`/`output_multiplier`/softcap/`embedding_norm` applied only when present | `exec/production/plan_backend.rs:68-75, 319-342`; `accessors.rs:300-330` | **Confirmed** |
| 23 | `residual_topology` branched on | `build.rs:268-283` | **Confirmed** |
| 24 | **`context_length` never read** by plan or exec | grep of `VX/opplan`, `CLI/vindex3_cmd`, `crates/larql-inference/src/vindex3`: no hits. Only readers are `VX/graph/surface/linear_mla.rs:191` (writer) and `VX/gguf/*` (GGUF export) | **Confirmed** |
| 25 | `operator` decided from operand evidence and policy | `construct.rs:477-619` | **Confirmed** |
| 26 | Exec never reads `config.json` | `runtime.rs:88-131`: `inspect_container` → `plan_component_ops` → `OperandStore::open_in`. `index.family` is carried for reporting only | **Confirmed** |

**Refuted claims: none.**

### New findings (not stated in §17.8)

| # | Finding | Evidence | Effect on this container |
|---|---|---|---|
| N1 | **Every projection width also comes from the run-time `hidden`**, not only the residual stream: Q/K/V and gate/up input width, o_proj and down output width, and the embedding row stride all use `hidden = embedding.table.shape[1]`. This extends §17.8's "residual width" fact | `exec/layer_exec.rs:336-366` pass `hidden` into `AttentionCall.hidden`; `exec/production/select.rs:64-67` `project_matrix(…, call.hidden)`; `exec/backend/plan_backend.rs:184` `FfnCall.hidden`; `plan_backend.rs:68-71` embed | None. The plan's shape contracts force `shape[1] == C.hidden_size` |
| N2 | **No configuration value can be overridden at run time on this path.** larql-compute has `LARQL_NORM_EPS_OVERRIDE` (`LC/residual.rs:48-52`) and `forward_overrides` RoPE-base, position-divisor, frequency-scaling and attention-window overrides (`LC/attention/block.rs:377-383, 483`). They are reached only through the architecture-driven entry points. Nothing under `VX/opplan`, `CLI/vindex3_cmd` or `larql-inference/src/vindex3` references `forward_overrides`. The kernels exec calls (`rms_norm_eps`, `rms_norm_qk_eps`, `rms_norm_heads_eps`, `rope_rotate`, `geglu_silu_alloc`, `softmax_in_place_f32`) take every value as an argument. The environment variables that *are* read on the exec path select arithmetic, not configuration (for example `LARQL_KQUANT_EXEC=widen` per `CLI/prepare.rs:214-224`, the arithmetic-arm, Q4-class, worker and staging switches under `VX/opplan/exec/cpu/` and `exec/weights/`) | grep results above | None for configuration. These switches are arithmetic and outside §0's scope, but an E2 run should record the process environment, because they change what is computed numerically |
| N3 | **Unknown graph keys are silently ignored by LARQL.** No struct in `VX/graph` or `LM/config` uses `deny_unknown_fields` | grep: no hits | Supports §17.1's comparator rule. Motivates C2 |
| N4 | **`C.perception` is a schema field §17 does not mention** | `VX/graph/component.rs` (`Component.perception: Option<PerceptionComponent>`); read only under `role: Perception` (`VX/graph/build/components.rs:242-253`) | Absent here, and not read for `primary_text`. See C2 |
| N5 | **The final norm is skipped silently if the plan has no final-norm op** (`None => carrier`) | `accessors.rs:178-183` | Not reached: the `target.final_norm` object is present and shape-checked (`build.rs:688`). Same class as the "sliding without window" note |
| N6 | **GQA grouping is integer division** with no remainder check on this path | `helpers.rs:227` | Not reached (16 / 8 = 2). It would matter only for a non-divisible declaration |
| N7 | `head_reuses_embedding`'s writer rule has a second disjunct, `!has_lm_head()` | `LM/config/architecture/tensor_keys.rs:33-35, 54` | None for Qwen3 (`has_lm_head` true). See A1 |

**Computation-relevant values exec takes from somewhere other than a declared field**, all stated by the author and confirmed:
- the split-half RoPE pairing (hard-coded);
- the QK-norm epsilon (taken from `X.norm.pre.eps` by design);
- the residual width and logit count (taken from tensor shapes, N1 widens this to every projection width);
- the score scale (executed at binary32, not at the declared binary64).

`X.attention.num_kv_heads`, `X.attention.head_dim` and `X.head.head_reuses_embedding` are declared but not consumed for this container. `X.context_length` is never consumed. I found no other substitution, default or hard-coded value on the path.

**Unverified (outside my inputs):** the author flags that LARQL treats layers **below** `max_window_layers` as sliding, and requires `layer_types` to mark a layer sliding (`LM/config/architecture/attention.rs:47-58`). I did not read the pinned `transformers` 5.5.0 Qwen3 source, so I cannot confirm or refute that the reference resolves the same way. For this subject it is moot: `sliding_window` is `null`, and both sides attend fully at every layer. For a hidden mismatch case that sets `use_sliding_window: true` with a non-null window, LARQL's resolution may differ from the reference's. The reviewer should check this before relying on `span` to expose such a case.

## Check 4: completeness against D2

"Direct" means §17 names a container field and gives a comparison rule. "Indirect" means it is represented only through another field's resolved value. "None" means there is no field and no trace.

| D2 field | Upstream | Representation in rev 3 | Where (§17.7) | Facts that limit the comparison |
|---|---|---|---|---|
| `hidden_size` | 1024 | **Direct** | `C.hidden_size`; also `index.json.hidden_size`, shapes | — |
| `intermediate_size` | 3072 | **Direct** | `X.ffn.intermediate_size`; shapes; `_by_layer` absent | — |
| `num_hidden_layers` | 28 | **Direct** | `C.num_layers`; `len(C.attention)`; `index.json.num_layers` | — |
| `num_attention_heads` | 16 | **Direct** | `X.attention.num_q_heads`; `q_proj` rows ÷ `head_dim` | — |
| `num_key_value_heads` | 8 | **Direct** | `X.attention.num_kv_heads` + 28 × `geometry.num_kv_heads` (29 sites) | Exec consumes only the per-layer copies |
| `head_dim` | 128 | **Direct** | `X.attention.head_dim` + 28 × `geometry.head_dim`; q/k-norm length | Exec consumes only the per-layer copies |
| `vocab_size` | 151936 | **Direct** | `X.head.vocab_size`; embedding/head shapes | Exec takes the logit count from the shape |
| `hidden_act` | `"silu"` | **Direct**, through a stated map | `X.ffn.activation` | The writer stores `"silu"` for an absent or unknown `hidden_act`, so `"silu"` does not prove a declaration |
| `attention_bias` | false | **Direct** | `X.attention.attention_bias` (optional; absent = undeclared) | Exec runs an absent value as `false` |
| `rms_norm_eps` | 1e-06 | **Direct, lossy encoding** | `X.norm.pre.eps`, `X.norm.final_norm.eps`, compared as `f64(f32(upstream))` | Upstream values with the same binary32 rounding are indistinguishable. Also the QK-norm epsilon by rule |
| `rope_theta` | 1000000 | **Direct** | 28 × `C.attention[L].position.theta`, with `kind == "rope"` | — |
| `rope_scaling` | null | **Indirect** | `C.attention[L].position.kind` (`"rope"` ⇔ no scaling) | No field of its own. A scaling dict with no `type`/`rope_type` also resolves to `"rope"` |
| `sliding_window` | null | **Indirect** | `C.attention[L].span` and `.window` | No field of its own. A non-null window with `use_sliding_window: false`, or with no sliding `layer_types`, gives the same container as `null` |
| `use_sliding_window` | false | **None** | — | No field; only effect is on the resolved `span` |
| `max_window_layers` | 28 | **None** | — | No field; only effect is on the resolved `span`. LARQL's direction is unverified against the reference (above) |
| `tie_word_embeddings` | true | **Indirect** | `X.head.head_reuses_embedding` **and** equal `payload_sha256` of `target.output_head@BF16` and `target.embedding@BF16` | No field of its own. The flag is `true` for an absent key too, and exec ignores it when a head object exists. Equal payload digests hold here (`8f29acf5…`) |

Summary: 11 direct (one of them lossy), 3 indirect, 2 with no trace. This agrees with the author's flags. Whether "indirect" or "none" satisfies D2's "declared in a specified place" is a protocol decision, and I have not made it.
