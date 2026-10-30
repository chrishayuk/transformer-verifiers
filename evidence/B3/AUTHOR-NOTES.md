# B3 author notes: VINDEX3 container specification

## Authorship

- **Author:** a spec-author subagent (Claude, run as a delegated agent for the B3 workstream). It may read LARQL source. It is not the reference-checker agent and must not become it.
- **Deliverable:** `specs/vindex3-container/SPEC.md`.
- **Source of truth:** clean detached worktree `/Users/christopherhay/chris-source/larql-l1-2536bb79` at `2536bb79b199b1115445678e3e82c400b0b3fd07`. Checked with `git rev-parse HEAD`; `git status --short` was empty. Nothing in it was modified, built or run. `/Users/christopherhay/chris-source/larql` was not read.
- **Status:** DRAFT. The author does not declare B3 satisfied. A third party must check the specification against files LARQL emits at this commit.

## Method

1. Read the LARQL source end to end along the pipeline: CLI `encode` → `encode_graph_with_sources` → `write_segment`; CLI `represent` → `compile_inner`; CLI `exec` → `open_component_in` → `OperandStore::open_in` → production selection → weight loading.
2. Read the existing container `/Users/christopherhay/chris-models/qwen3-0.6b.vindex3` read-only, as **illustration only**. It has no recorded upstream revision, predates this commit, and is BF16 only, with no Q8_0 pack. I used it to confirm framing (u64 LE length, compact JSON, trailing space padding, 16-byte payload start), byte-wise name sort order, contiguity, `index.json` and `system_graph.json` shape, and the two-copy tied head.
3. Read the HF safetensors header and hashed the `lm_head.weight` and `model.embed_tokens.weight` payloads. They are byte-identical, SHA-256 `8f29acf519434862d95613b2b4f6b9d14933a5e4d16baebf8ac0b33b410acfb6`.
4. Computed the expected `@Q8_0` decoder segment header with a scratch script (`/private/tmp/claude-501/-Users-christopherhay-chris-source-transformer-verifiers/96e4e0bb-6846-4b77-902a-0f72bc762d13/scratchpad/predict.py`). It applies LARQL's rules (byte-wise sort, compact serialisation, Q8_0 length = rows·(K/32)·34, space padding) to the illustration's BF16 header. As a check, the script reproduced the illustration's BF16 header bytes exactly. Every value in SPEC §9 marked "(computed)" comes from it. None of those values has been observed in a real Q8_0 file.

## Files read

LARQL worktree (paths relative to `crates/`):

- `larql-cli/Cargo.toml`
- `larql-cli/src/main.rs` (grep only: binary and subcommand wiring)
- `larql-cli/src/commands/primary/vindex3_cmd/args.rs`
- `larql-cli/src/commands/primary/vindex3_cmd/mod.rs` (grep)
- `larql-cli/src/commands/primary/vindex3_cmd/represent.rs`
- `larql-cli/src/commands/primary/vindex3_cmd/prepare.rs`
- `larql-cli/src/commands/primary/vindex3_cmd/exec.rs` (partial)
- `larql-cli/src/commands/primary/vindex3_cmd/verify_encode.rs` (run_encode)
- `larql-vindex/Cargo.toml`
- `larql-vindex/src/format/generation.rs`
- `larql-vindex/src/format/checksums.rs` (sha256_file)
- `larql-vindex/src/format/filenames.rs` (grep)
- `larql-vindex/src/format/vindex3/mod.rs`
- `larql-vindex/src/format/vindex3/index.rs`
- `larql-vindex/src/format/vindex3/inspect.rs`
- `larql-vindex/src/format/vindex3/shape.rs` (partial)
- `larql-vindex/src/format/vindex3/verify.rs` (lines 1-200)
- `larql-vindex/src/format/vindex3/verify_system/payload.rs` (header)
- `larql-vindex/src/format/vindex3/profile.rs` (partial)
- `larql-vindex/src/format/vindex3/encode/mod.rs`
- `larql-vindex/src/format/vindex3/encode/segment.rs`
- `larql-vindex/src/format/vindex3/encode/checkpoint.rs` (partial)
- `larql-vindex/src/format/vindex3/encode/source/mod.rs` (partial)
- `larql-vindex/src/format/vindex3/artifact/ingest.rs` (partial)
- `larql-vindex/src/format/vindex3/artifact/resolve.rs` (partial)
- `larql-vindex/src/format/vindex3/graph/mod.rs` (partial)
- `larql-vindex/src/format/vindex3/graph/object.rs` (partial)
- `larql-vindex/src/format/vindex3/graph/build.rs` (partial)
- `larql-vindex/src/format/vindex3/graph/build/components.rs` (partial)
- `larql-vindex/src/format/vindex3/graph/surface.rs` (HeadSurface)
- `larql-vindex/src/format/vindex3/represent/report_types.rs`
- `larql-vindex/src/format/vindex3/represent/pipeline.rs`
- `larql-vindex/src/format/vindex3/represent/compile.rs`
- `larql-vindex/src/format/vindex3/represent/policy.rs` (lines 1-420)
- `larql-vindex/src/format/vindex3/represent/plan_roles.rs` (lines 1-194)
- `larql-vindex/src/format/vindex3/represent/kquant.rs`
- `larql-vindex/src/format/vindex3/represent/map.rs` (partial)
- `larql-vindex/src/format/vindex3/represent/nvfp4_pack.rs` (CodecIdentity, EncoderRecipe)
- `larql-vindex/src/format/vindex3/represent/candidate_authority.rs` (lines 1-260)
- `larql-vindex/src/format/vindex3/represent/candidate_authority/producer.rs`
- `larql-vindex/src/format/vindex3/represent/compiler.rs` (partial)
- `larql-vindex/src/format/vindex3/represent/state/resolved.rs` (partial)
- `larql-vindex/src/format/vindex3/represent/codec/registry.rs` (admit)
- `larql-vindex/src/format/vindex3/represent/codec/geometry.rs` (RowGeometry)
- `larql-vindex/src/format/vindex3/represent/codec/codecs/kquant.rs` (grep and partial)
- `larql-vindex/src/format/vindex3/represent/codec/codecs/float.rs` (partial)
- `larql-vindex/src/format/vindex3/represent/physical.rs` (grep)
- `larql-vindex/src/format/vindex3/opplan/build.rs` (lines 660-796)
- `larql-vindex/src/format/vindex3/opplan/exec/operands.rs` (lines 1-330)
- `larql-vindex/src/format/vindex3/opplan/exec/operands/open.rs`
- `larql-vindex/src/format/vindex3/opplan/exec/requirements.rs` (lines 1-80)
- `larql-vindex/src/format/vindex3/opplan/exec/weights/load.rs`
- `larql-vindex/src/format/vindex3/opplan/exec/quantise.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/production/select.rs`
- `larql-vindex/src/format/vindex3/opplan/exec/production/plan_backend.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/realization/selection.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/realization/refusal.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/prepared/loading.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/cpu/physical.rs` (partial)
- `larql-vindex/src/format/vindex3/opplan/exec/cpu/physical/projection.rs` (partial)
- `larql-models/src/inventory/tensors.rs` (partial)
- `larql-models/src/config/architecture/tensor_keys.rs` (partial)
- `../docs/vindex3-format.md` (lines 1-480)
- `larql-vindex/docs/vindex3-format-spec.md` (lines 310-360, plus grep)

Outside LARQL, all read-only:

- `/Users/christopherhay/chris-models/qwen3-0.6b.vindex3/`: `index.json`, `system_graph.json`, and the headers of all four segments. Illustration only.
- `/Users/christopherhay/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca/`: the `model.safetensors` header, three tensor payloads (for hashing), and `config.json` (grep `tie`).
- `/Users/christopherhay/chris-source/transformer-verifiers/protocols/LARQL-VERIFY-001/draft.json` and `PROTOCOL.md` (grep for the pipeline commands).

## UNDETERMINED items

1. **U1. The encode invocation.** The protocol gives the `represent` and `exec` commands but not the `encode` command. The artifact argument (a local path or `hf://`) sets `index.json.model`, `system_graph.json` `components[].source_artifact` and `source_bindings[].artifact`, and `candidate.json` locator fields. A local path to the HF snapshot directory would record `c1899de289a04d12100db370d81485cdf75e47ca` as the model name. Tensor bytes, names, shapes and order are unaffected.
2. **U2. Fresh-container digests and observed Q8_0 header bytes.** No Q8_0 container exists (searched `~/chris-models` to depth 4). The SPEC §9 values marked "(computed)" are predictions: Q8_0 payload 468,056,064 bytes, header 31,416 bytes, payload start 31,424, file 468,087,488 bytes.
3. **U3. Build features at L1.** If L1 builds with `larql-vindex/reference-encoder`, the `encoder` field becomes `kquant-ggml-reference` with a `source` string, and the chosen values may differ. The layout does not change.
4. **U4. The realised LM-head kernel on the L1 host.** SPEC §12(d) is based on reading the code; nothing was run. The choice depends on the host's L2 size (sysctl `hw.perflevel0.l2cachesize` on macOS, otherwise a 16 MiB default) and on `LARQL_CPU_MAX_FORMAT` / `LARQL_CPU_ARITHMETIC`. The L1 auditor should read the `projection plans:` line of a real run.
5. **U5. Not fully specified:** the full schemas of `candidate.json` and of the `system_graph.json` component execution surface. Neither is needed to locate or identify tensors.
6. **U6. Byte-exact text of the JSON files.** Readers must not depend on it.
7. **U7. The "unsolved name mapping" comment in `verify.rs`.** The task brief cited it from an older commit. At `2536bb79` no occurrence of "unsolved" exists in `crates/larql-vindex/src` or `docs/`. What the code actually does, prefix stripping (`encode/mod.rs:472-541`), is specified in SPEC §10.

## Code/doc disagreements (code wins)

1. `crates/larql-vindex/src/format/vindex3/mod.rs:27-31` describes the layout as `index.json  schema 3`, `moe_manifest.json`, `routed/layer_000.lyrw`. The code writes `version` 4 (`generation.rs:86`), and `vindex3 encode` writes the graph shape with no `moe_manifest` (`encode/mod.rs:575-578`). The comment describes the legacy bank shape and the old schema.
2. `docs/vindex3-format.md` §6.1 and `larql-vindex/docs/vindex3-format-spec.md` §5.3 give the framing as `[u64 LE header length][header JSON][payload bytes]`. Neither mentions the trailing-space padding that aligns the payload to 16 bytes. The code adds it, and includes it in the length (`encode/segment.rs:133-158`). Neither document mentions compiled-pack segments (`<object>@<encoding>.bin`) or `candidate.json`.
3. `docs/vindex3-format.md` §6 says "one or more simple contiguous segments" per representation. The graph-shape encoder writes exactly one segment per representation, with segment-key count `1` (`encode/mod.rs:278-306`).
4. **`stored` does not mean "nothing is quantised at load".** `RepresentationSource::Stored` (`opplan/exec/operands.rs:219-232`) and the `--representation-source` help text (`CLI/args.rs:218-227`) say `stored` forbids manufacturing a representation: "the run fails naming any tensor that would be quantised". The code requantises the BF16 output head into the internal Q8 residency (`weights/load.rs:69-90` → `quantise.rs:76`) with no call to `note_runtime_quantisation`. The guard is called only on the MXFP4 and NVFP4 paths (`weights/load.rs:127-160`). So `stored` admits it, and `runtime compile:` still reports 0 (`CLI/exec.rs:161-169`). This is the most consequential finding for Stage A. It is a matter for L1, and possibly a LARQL defect, not a container-format question.
5. `opplan/build.rs:690-697` says "the container never gets a second copy of the matrix". That holds only when the checkpoint ships no `lm_head` group. Qwen3-0.6B ships `lm_head.weight`, so the container stores two copies. The comment is conditional, so this is a trap for readers rather than a strict contradiction.
6. `docs/vindex3-format.md` §8.0 calls the execution surface "graph schema v2". The code is `GRAPH_SCHEMA = 6` (`graph/mod.rs:103`). This is historical narrative, but a reader of the doc could reject or accept the wrong graph version.
7. The segment header carries `schema: 1` (`encode/segment.rs:24-25`), but `read_segment_header` never checks it (`encode/segment.rs:245-263`). The comment "Bump on any breaking change" implies a check the reader does not perform. SPEC §4.3 and §14 require independent readers to check it.

## Where the container fails the "discoverable from the container" requirement

(Duplicated from SPEC §15.)

- **F1.** Row orientation, row-major element order, and "Q8_0 blocks run along the last dimension" are not declared by any field. They are conventions (safetensors C order, ggml row blocking) and LARQL code (`codec/geometry.rs:22-36`).
- **F2.** Endianness, and the fact that the in-block scale is f16, are not declared. `codec.element = "ggml-q8_0"` and `"in-block"` refer to ggml by name. No ggml type number is stored.
- **F3.** The `codec` belongs to the representation, but the Q8_0 pack mixes Q8_0 and BF16 tensors. Its scope (tensors whose `dtype == codec.family`) is implicit.
- **F4.** **The executed LM-head representation is not discoverable.** The container shows the head as BF16. `production-q8` executes a LARQL-internal Q8 image built at load, and the choice depends on the host and the environment. Nothing in the container records it.
- **F5.** `head_reuses_embedding: true` sits beside a separate `target.output_head` object. That the head reads the output-head object comes only from LARQL's plan rule (`opplan/build.rs:699-711`).
- **F6.** For a BF16 tensor inside the Q8_0 pack, the reason (protected role versus layout refusal) is recorded only in `candidate.json`, not in the reader's required files. This does not affect locating or identifying bytes.

Met: per-tensor representation type is in each tensor's `dtype`; Q8_0 block geometry is in `index.json` `codec`; the representation that executes follows from `index.json`; the HF key map follows from `system_graph.json`.

## Other observations for the reviewer

- `represent` copies capability files and `moe_manifest.json`, but not `auxiliary_references.json` or an attestation table (`represent/pipeline.rs:526-538`). A source container that had either would yield an output whose `index.json` names a file that is not there. That does not apply to this subject, which has neither.
- `candidate.json` embeds the source container's absolute path (`producer.rs:84`), so its bytes are machine-dependent. The rest of the container is deterministic given the inputs, except for the identity strings in U1.
- Tensor offsets within a Q8_0 pack are only 2-byte aligned (34-byte blocks after BF16 vectors). Only the payload start is 16-byte aligned.

## Revision 2 (applied after the third-party check)

The third-party check (`evidence/B3/CHECK.md`) of SPEC.md revision 1 (SHA-256 `47c2a304bffdc21bb17017aed248ee74f5827099c2d8b962a766dec888964ef0`) returned ADMIT WITH CORRECTIONS. All 8 spec-only checks passed on the fresh container `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`. I read that container read-only. As its author, I applied exactly the five requested corrections:

1. **O2.** Provenance now points to the fresh container; the §9 values are marked observed, and its digests are recorded in §9.2. U1 is closed: `model` and `artifact` are `c1899de289a04d12100db370d81485cdf75e47ca`, which replaces the `"Qwen3-0.6B"` example. U2 is closed: all computed values held. U3 is closed: `encoder` is `kquant-larql-native` rev 1 with no `source`. U4 to U7 are unchanged, because the container does not settle them. U7 appears only in these notes.
2. **O1.** §8.4 now names ggml `facdc44a67da17df4433adcc468b424f48e9ded2`, `src/ggml-common.h:251-256` (f16 `d`, then `int8_t qs[32]`), as the normative `block_q8_0` reference. It still describes no arithmetic.
3. **A1.** §6 now defines `source_bindings[].tensors` and `.bytes` as the source tensor count and byte total, with a MAY cross-check. I added a new source, S109 (`graph/build/tables.rs:185-190`).
4. **A2.** §12(b) now says the padding length also differs (5 versus 3 spaces) and that the parsed headers are otherwise equal.
5. **A3.** §4.3 now notes that the observed offsets are 16-aligned, incidentally, and keeps "MUST NOT assume more than 2-byte alignment" normative.

No normative layout statement changed. The F2 text in SPEC §15 was left as it was, as instructed, even though O1 now gives readers the pinned block definition. One earlier remark in these notes was too pessimistic: "Tensor offsets within a Q8_0 pack are only 2-byte aligned". It holds as the guarantee, but the observed offsets in this subject are 16-aligned. SPEC.md revision 2 SHA-256: `3c4feb5e01f2c262e06e1f8579754921089cda46038f17c63cfd42f9d0c5fe50`.
