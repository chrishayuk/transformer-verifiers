# B3 revision 3: author notes

## Authorship and status

- **Author:** the B3 specification author (a Claude subagent with read access to LARQL source). It is not the reference-checker agent, and did not act as one.
- **Deliverable:** `evidence/B3/rev3/SPEC.md`, a complete revision 3 of the VINDEX3 container specification. It is a DRAFT. It is not admitted, and `specs/vindex3-container/SPEC.md` was not touched.
- **Why:** decision revision D2 of `protocols/LARQL-VERIFY-001/PROTOCOL.md` (OQ11) needs the computation-relevant execution-surface fields specified, so that the checker can compare the container's declared configuration with the pinned upstream `config.json` without reading LARQL.
- **Nothing committed.**

## Inputs verified before starting

| Input | Check | Result |
|---|---|---|
| SPEC revision 2, `specs/vindex3-container/SPEC.md` | SHA-256 | `3c4feb5e01f2c262e06e1f8579754921089cda46038f17c63cfd42f9d0c5fe50`, as expected |
| LARQL worktree `/Users/christopherhay/chris-source/larql-l1-2536bb79` | `git rev-parse HEAD`; `git status --short` | `2536bb79b199b1115445678e3e82c400b0b3fd07`; empty |
| Fresh container `system_graph.json` | SHA-256 | `05fcec4c45167c2f8f424c35b8c39acb06cc92716f11e0ffbec341e110d66f57`, as expected |
| Upstream `config.json` (HF snapshot `c1899de2…`) | SHA-256 | `660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd` |

Nothing in the LARQL worktree was modified, built or run. `/Users/christopherhay/chris-source/larql` was not read. The container and the HF snapshot were read only.

## Method

1. Read SPEC revision 2 in full, with `evidence/B3/AUTHOR-NOTES.md`, `CHECK.md`, `ADMISSION.md` and the D2 section of the protocol.
2. Read the fresh container's `system_graph.json` and `index.json`, and the upstream `config.json`.
3. **Format side.** Read the serde types that `system_graph.json` deserialises into (component, execution surface, per-layer policy, and the `larql-models` enums they embed), to get each field's JSON type, tag form, default and absence rule.
4. **Writer side.** Traced how each surface value is produced at encode time: `config.json` parser → architecture trait defaults and the Qwen overrides → resolved inventory → surface builder and per-layer table builder.
5. **Consumer side.** Traced `vindex3 exec --backend production-q8`: `open_component_in` → `plan_component_ops` (closure, then plan construction) → prepared operands → the production CPU backend's norm, attention, FFN, embedding and head entry points, for both the batch path and the decode step.
6. Checked every **(observed)** value in §17 mechanically against the container and `config.json` with a scratch Python script (run with `-I`, outside the repository). All 18 assertions held. The script also listed every key present under `C.execution`, its sub-objects and `C.attention[0]`; every one is covered by §17.
7. Wrote §17 and the small edits listed in the revision history, then re-diffed against revision 2 to confirm that no normative statement of revision 2 changed.

## Files read

LARQL worktree, all read-only. `VX` = `crates/larql-vindex/src/format/vindex3`, `LM` = `crates/larql-models/src`.

- Format types: `VX/graph/component.rs`; `VX/graph/surface.rs`; `VX/graph/policy.rs`; `VX/graph/roles.rs` (NormPlacement); `LM/config/norm.rs`; `LM/config/position.rs` (lines 1-395); `LM/config/activation.rs` (partial); `LM/config/experts.rs` (partial); `LM/config/residual_topology.rs` (partial).
- Writer: `VX/graph/surface/linear_mla.rs` (lines 140-426); `VX/graph/build/components.rs` (grep and partial); `VX/graph/build/tables.rs` (lines 16-96); `LM/inventory/resolved.rs` (lines 1-360); `LM/detect/parser.rs` (lines 95-240, 295-330, 410-440); `LM/detect/parser/rope_scaling.rs` (lines 25-55); `LM/config/architecture/attention.rs`; `LM/config/architecture/norms.rs` (lines 1-160); `LM/config/architecture/position.rs` (lines 1-90, 230-395); `LM/config/architecture/tensor_keys.rs` (lines 30-60); `LM/config/architecture/feed_forward.rs` (lines 14-125); `LM/config/architecture/shared.rs` (grep); `LM/architectures/qwen.rs` (lines 1-190); `LM/detect/registry/construct.rs` (lines 1-40).
- Consumer: `crates/larql-cli/src/commands/primary/vindex3_cmd/exec.rs` (partial); `.../prepare.rs` (lines 160-260); `.../teacher_force.rs` (grep); `crates/larql-inference/src/vindex3/runtime.rs` (lines 80-150); `VX/opplan/ops.rs`; `VX/opplan/layer.rs` (grep and lines 179-210); `VX/opplan/build.rs` (lines 205-520, 657-730); `VX/opplan/build/construct.rs` (lines 1-300, 460-500, 600-740); `VX/opplan/build/shapes.rs` (lines 85-125, grep); `VX/opplan/build/layer_closure.rs` (lines 195-212); `VX/opplan/exec/attention_ops.rs` (lines 1-260); `VX/opplan/exec/layer_exec.rs` (lines 60-200, 330-370); `VX/opplan/exec/decode/run.rs` (lines 160-240, 300-340); `VX/opplan/exec/prepared.rs` (lines 246-271); `VX/opplan/exec/prepared/loading.rs` (lines 70-100, 150-360); `VX/opplan/exec/prepared/accessors.rs` (lines 160-345); `VX/opplan/exec/production.rs` (lines 125-484); `VX/opplan/exec/production/plan_backend.rs` (lines 60-345); `VX/opplan/exec/production/select.rs` (lines 20-260); `VX/opplan/exec/production/helpers.rs` (lines 195-284); `VX/opplan/exec/kernels.rs` (lines 147-175); `VX/opplan/exec/kv.rs` (lines 40-85); `VX/opplan/exec/backend/calls.rs` (lines 406-426); `crates/larql-compute/src/residual.rs` (lines 56-78, 130-152, 243-265).
- Greps for `score_scale`, `declared_norm_eps`/`qk_norm_eps`, `context_length`, `ProductionQ8`, `vocab_size` and `hidden` across `VX/opplan`, `crates/larql-inference/src/vindex3` and the CLI `vindex3_cmd`.

Outside LARQL: the files in the inputs table, plus `evidence/B3/check/` (listing only).

transformers and torch source were **not** read. §17 therefore makes no claim about what the reference implementation computes. Where a field has no upstream key, §17.7 says the comparator compares it against the pinned reference's behaviour, which the harness fixes, and leaves that behaviour unstated.

## What revision 3 changes

See the revision 3 row of the revision history in `SPEC.md`. In short:

- a new §17 (normative §17.1 to §17.7, informative §17.8);
- new sources S110 to S152, with abbreviations `LM` and `LC`;
- §16 U5 marked partly closed;
- the §8.2 "(computed)" leftover (finding E1) re-marked **(observed)**;
- two additive pointer sentences, in §0 and §6;
- the header table and revision history updated.

No normative statement of revision 2 changed. One rule is affected in scope only: §3 says unknown keys "MUST be ignored unless this document says otherwise". §17.1 says otherwise, for a configuration comparator only, under `C.execution` and `C.attention[L]`. The tensor-reader rule is unchanged.

## Findings

### Revision 2 normative statements

None found wrong. Every revision 2 statement that touches the execution surface (§6's `execution.head` facts, §12(a)) agrees with what §17 specifies.

### Findings about the container and LARQL (also reflected in §17)

1. **The epsilon is stored after a binary32 round trip.** `rms_norm_eps = 1e-06` is stored, and executed, as `9.999999974752427e-7`, which is `f64(f32(1e-6))` (`LM/config/architecture/norms.rs:84-90`, `:143-148`; the type's own comment acknowledges it at `LM/config/norm.rs:83-85`). A comparator that tests binary64 equality with `config.json` will always report a mismatch. §17.7 specifies equality after binary32 rounding. Consequence: the container cannot distinguish upstream values that round to the same binary32.
2. **The score scale is `powf(head_dim, -0.5)` in binary64:** `0.08838834764831845`. That is 1 ulp above `1/sqrt(128)` computed by square root and division. Exec rounds it to binary32 before use, and both binary64 values give the same binary32. §17.4 states the derivation exactly.
3. **QK-norm epsilon is not a field.** Exec runs the Q/K norms at `norm.pre.eps` (`VX/opplan/layer.rs:192-205`). That is a design rule, not a defect, but D2 lists it as a value the container must declare in a specified place. §17.3 now makes `norm.pre.eps` that place, normatively.
4. **Duplicated head geometry.** `execution.attention.head_dim`/`num_kv_heads` and the 28 per-layer `geometry` objects state the same facts. Exec uses the per-layer values whenever they are present, which is always on a fresh encode, so the surface copies are not consumed for this container (`VX/opplan/build.rs:478-482`). §17.7 requires the comparator to check all 29 sites.
5. **`head_reuses_embedding` does not encode `tie_word_embeddings`.** It is `true` unless `tie_word_embeddings` is exactly `false`, so an absent key also gives `true`. Exec ignores it whenever an output-head object exists, which is the case here. The tie is realised only through byte-identical payloads in two separate objects (§12). §17.7 makes the payload equality part of the comparison.
6. **`hidden_act` is defaulted at encode time.** An absent or unrecognised `hidden_act` is stored as `"silu"` (`LM/config/architecture/feed_forward.rs:45-52`). So `"silu"` in a container does not prove upstream declared it. It does here: upstream says `"silu"`.
7. **`attention_bias` absent executes as `false`.** The surface keeps "undeclared" distinct from `false`, but exec binds biases only on `true`. §17.7 tells the comparator to treat an absent value as unresolved.
8. **`context_length` is not read by exec.** No position bound is enforced from `max_position_embeddings`. This is not a D2 field.
9. **Hard-coded, undeclared:** split-half RoPE pairing (`LM/config/position.rs:28-45`); residual width and logit count taken at run time from tensor shapes, not from the declared `hidden_size`/`vocab_size` (the plan checks that they agree).
10. **A `"sliding"` span with no `window` would run as full attention** (`VX/opplan/exec/kv.rs:66`). Not reachable for this subject.

### For the coordinator: D2 fields the container does not represent

- `use_sliding_window` and `max_window_layers` have **no field and leave no trace** beyond the resolved per-layer `span`. With `sliding_window: null` neither affects the computation, so the container is consistent with the upstream values but cannot confirm them.
- `rope_scaling`, `sliding_window` and `tie_word_embeddings` have **no field of their own**. They are represented only indirectly (`position.kind`; `span`/`window`; `head_reuses_embedding` plus equal payloads).

Whether "the effect is declared, the key is not" satisfies D2's "declared in a specified place" for the first two is a protocol decision, not a format one. I did not make it. §17.7 states exactly what is and is not represented.

### Possible concern, not verified (outside this document's scope)

LARQL resolves `max_window_layers` as "layers **below** the bound slide" (`LM/config/architecture/attention.rs:48-54`). I did not read the transformers Qwen3 source, so I cannot say whether the reference agrees. For this subject the question is moot, because `sliding_window` is `null` and no layer slides. It would matter for a checkpoint with a non-null window. An execution-path auditor should check it before relying on `span` for such a checkpoint.

## UNDETERMINED

1. **Whether an encode-time gate refuses an unrecognised `hidden_act`.** The surface builder stores `"silu"`. I did not trace the plan-comparison (`plan::compare`) or completeness gates far enough to say whether `vindex3 encode` refuses such a checkpoint first. It does not affect this subject.
2. **The comparison rules in §17.7 are the author's.** D2 requires the reviewer to confirm the mapping independently when building hidden cases. The comparator behaviour for fields with no upstream counterpart depends on the reference harness, which this document does not describe.
3. **§17.8 is code reading only.** No run confirmed any consumption path. The LM-head finding of revision 2 (U4, F4) still applies and is not restated.
4. **Remaining U5 scope.** `candidate.json`, and the surface groups this profile does not use (recurrent, MLA, Mamba2, conv-QKV, MoE, hyper-connection), are specified only as "must be absent".

## Draft digest

`evidence/B3/rev3/SPEC.md` SHA-256 is recorded in the coordinating session's hand-off. It is not stated here, because this file sits beside the draft and an edit to either would make a recorded hash stale.
