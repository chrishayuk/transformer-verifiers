# B3 third-party check: VINDEX3 container specification

| Field | Value |
|---|---|
| Role | **Third-party checker** for LARQL-VERIFY-001 workstream B3. Not the spec author, not the reference-checker agent |
| Date | 2026-10-30 |
| Spec checked | `specs/vindex3-container/SPEC.md`, SHA-256 `47c2a304bffdc21bb17017aed248ee74f5827099c2d8b962a766dec888964ef0` (verified before starting; not edited) |
| Container checked | `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3` (LARQL `2536bb79`). All 11 files match `evidence/L1/container-q8_0.sha256` (`shasum -c`: 11/11 OK) |
| Key file hashes | `index.json` `7f3ba8e5da50276e501e7694c46c0a3c9c9d7530596656376cc9597f05fec490`; `segments/target.decoder_stack@Q8_0.bin` `f7f68e997657e9f28394af937a10adbdceee7ccd4fc56839ad49f1190eb6573e`; `system_graph.json` `05fcec4c45167c2f8f424c35b8c39acb06cc92716f11e0ffbec341e110d66f57` |
| Upstream | `Qwen/Qwen3-0.6B@c1899de289a04d12100db370d81485cdf75e47ca` `model.safetensors` (311 BF16 tensors) |
| Tools | `checker/.venv/bin/python -I` (numpy 2.4.2, gguf 0.18.0), read-only. ggml `block_q8_0` from `inputs/ggml-facdc44a…/src/ggml-common.h:251-256` |
| Scripts / raw output | `evidence/B3/check/check_spec.py`, `evidence/B3/check/phaseA_stdout.json`, `evidence/B3/check/phaseA_results.json` (every individual assertion) |

## Verdict

**ADMIT WITH CORRECTIONS.** Phase A found no false layout statement. Every tensor's bytes were located and identified using only rules the spec states, and every check passed. The corrections below are provenance updates, omissions and points of precision. None changes the layout model.

## Phase A: spec only

The parser was written from SPEC.md alone. During Phase A no LARQL source, LARQL docs or `AUTHOR-NOTES.md` were opened. Phase A read only the container's own files, the upstream safetensors, gguf-py and ggml-common.h. The run took about 14 s and exited 0. A first run had one failure, and it was a bug in my test, not in the container. I had compared the embedding and output-head headers byte for byte after substituting the names. The names differ in length (21 vs 23 bytes), so the §4.1 padding also differs (5 vs 3 spaces). I fixed the test to compare the parsed headers and reran.

| # | Check | Result | Assertions | Counts / key figures |
|---|---|---|---|---|
| 1 | Framing, header length, alignment, padding, tiling, file sizes | **PASS** | 99 / 0 failed | 5 segments. H: decoder@BF16 31448, decoder@Q8_0 31416, embedding 152, output_head 152, final_norm 136. Padding 8/8/5/3/0 spaces, equal to `(16-(8+J) mod 16) mod 16` in every case. P mod 16 = 0 for all. Headers are compact JSON (byte-equal re-serialisation), with keys `schema, representation, tensors` and entry keys `name, dtype, shape, offset, len` in that order. Offsets are contiguous from 0. Σlen = payload = `payload_bytes` with no trailing bytes. File size = P + `payload_bytes` for all 5 (Q8_0 file 468,087,488). Names unique and byte-sorted; layer order `0,1,10..19,2,20..27,3..9`. The file inventory is exactly the spec's §2 list (no optional files). The 4 canonical segments are hard links to / identical with `<SRC>` |
| 2 | Name, shape, representation from the container alone | **PASS** | 2256 / 0 | decoder@Q8_0: **196 `Q8_0` + 112 `BF16`**. decoder@BF16: 308 `BF16`. embedding, final_norm, output_head: 1 `BF16` each. Overall 619 tensor entries across the 5 segments: 196 Q8_0 and 423 BF16. The §7-selected set has 311: 196 Q8_0 and 115 BF16. Every `len` matches the §8.1 formula. Every Q8_0 row length is a multiple of 32. §9.3 single-tensor entries and the §9.4 table (names, shapes, dtypes, lens, group offsets, 16,716,288-byte groups) match exactly. Nothing had to be guessed to identify a tensor |
| 3 | Mapping to HF keys | **PASS** | 1869 / 0 | Rule `tensor_prefix + "." + name`. Each object has exactly 1 binding. Injective within each representation. Both the §7-selected set and the canonical set are a bijection with all 311 upstream keys (0 missing, 0 extra). All shapes equal upstream, all upstream dtypes BF16. Each upstream key is covered by exactly one prefix |
| 4 | BF16 bytes identical to upstream | **PASS** | 423 / 0 | 308 (decoder@BF16) + 112 (norms in decoder@Q8_0) + embedding + final_norm + output_head = 423 tensors, all byte-identical |
| 5 | Q8_0 layout | **PASS** | 196 / 0 | Each tensor was sliced as `[R, B·34]` per §8.4 and decoded with `gguf.quants.dequantize(…, Q8_0)`. Decoded shape `[R, K]` correct for 196/196. Pass rule: correlation with upstream > 0.99 in the stated orientation, and \|corr\| < 0.5 for every alternative. Alternatives: blocks along dim 0 (transpose), compare with Wᵀ (square tensors), rows rolled by 1, random row permutation, blocks rolled by 1 within the row, byte shifts of +2, +34 and −34. **Minimum stated-orientation correlation over all 196 tensors: 0.99997.** Every alternative stayed below 0.5 for every tensor. No reconstruction-error statistics were computed |
| 6 | Integrity values | **PASS** | 211 / 0 | `segment_sha256` 5/5 and `payload_sha256` 5/5 recomputed and equal. For all 4 canonical representations, `payload_sha256` equals SHA-256 of the upstream tensor bytes concatenated in segment order (§13.1). `source_representation_digest` = decoder@BF16 `payload_sha256`. Informative check: `candidate.json` `ledger.sealed` has 196 seals for the 196 Q8_0 tensors, and all 196 agree on `object`, `tensor`, `encoding`, absolute `target_offset` = P + offset, `target_len`, and re-hashed `target_hash` and `source_hash` |
| 7 | Tied embeddings §12(a)–(c) | **PASS** | 8 / 0 | (a) Two logical objects, `target.embedding` (`model.embed_tokens`) and `target.output_head` (`lm_head`); `head_reuses_embedding: true`. (b) Two physical files, distinct inodes, 311,165,088 bytes each; `segment_sha256` differ; the parsed headers differ only in `representation`. (c) Payloads byte-identical; both `payload_sha256` = `8f29acf5…acfb6`, which equals my hash of both upstream tensors; neither object compiled, so there is no `@Q8_0` for either |
| 8 | Versioning and rejection rules against the field values present | **PASS** | 59 / 0 | `version` 4; `system_graph` present; `moe_manifest`, `authority`, `auxiliary_references`, `representation_attestations`, `variants`, `derived_from_model` absent; no unknown top-level keys; graph `schema` 6, one component, 4 objects sorted, `edges` empty; graph and representation objects coherent; canonical entries carry no compiled-only keys; `codec` exactly equals §8.3; `precision_map` exactly equals §5.4; `segments` map = paths minus `.bin`; segment `schema` 1 ×5; only `BF16`/`Q8_0` dtypes. §7 step 3 selects `decoder_stack@Q8_0` and `{embedding,final_norm,output_head}@BF16`. None of rules §14.1–10 fires on this container |

Scope note: Phase A checked the rules only against the values present (the positive path). No mutated containers were built to show that each rejection fires. The Q8_0 alternatives in check 5 are the negative controls for layout. §12(d) (load-time behaviour of the executor) is about execution, not the container, and was not checked.

### Phase A: statements found wrong

None. Every checkable statement about the container's bytes, fields and counts holds for this container, including every value marked **(computed)** (H = 31,416, P = 31,424, payload 468,056,064, file 468,087,488, the §9.4 table). The **(illustration)** values are also reproduced exactly by the fresh container's canonical segments (H = 31448/152/152/136, payload sizes).

### Phase A: statements found ambiguous or insufficient (had to guess)

- **A1. `source_bindings[].tensors` and `.bytes` (§6).** The spec gives their JSON types but not what they mean. I guessed "number of source tensors under the prefix" and "their total source byte size", and the guess matched (308/880,932,864, 1/311,164,928, 1/2,048, 1/311,164,928). Nothing in locating or mapping depends on them. *Correction:* state the meaning and say a reader MAY cross-check `tensors` against the canonical `tensor_count` and `bytes` against the canonical `payload_bytes`.
- **A2. §12(b) "different `segment_sha256` because the header names differ".** This is true but incomplete. The headers also differ in padding length (5 vs 3 spaces) because the names differ in length. A reader that compares raw headers after substituting the names, as my first draft did, gets a false mismatch. *Correction:* "…because the header `representation` strings differ (and so, by §4.1, does the padding length). The parsed headers are otherwise equal."
- **A3. §4.3 "A Q8_0 tensor's offset may be any even number."** This is correct as a general statement. In this profile every tensor length is a multiple of 16, so all 196 Q8_0 offsets are ≡ 0 mod 16. *Correction:* keep the rule (readers MUST NOT assume more than 2-byte alignment) and add "(observed: all offsets in this container are multiples of 16; this is incidental, not a guarantee)".

### Phase A: omissions a spec-only reader needs

- **O1. Pinned definition of `block_q8_0`.** §8.4 hands the block's internals to "ggml `block_q8_0`" without naming a ggml revision. Decoding needs that definition: f16 `d` at block bytes 0–1, then `int8 qs[32]` at bytes 2–33 (`ggml-common.h:251-256` at `facdc44a…`). *Correction:* cite the pinned ggml revision and file/line as the normative reference for block contents. The arithmetic can still be left out. This also closes F2 for readers.
- **O2. Stale provenance.** The status line, §0 ("to be built fresh later"), §9.2/§9.4 "(computed)", and §16 U1–U3 predate the fresh container. *Correction:* cite the fresh container (path and the hashes above) as the observation. Mark §9 values "observed". Record the digests from `index.json`. Close **U1**: encode was given the local snapshot directory, so `model` and `source_bindings[].artifact` = `"c1899de289a04d12100db370d81485cdf75e47ca"`. Replace the §5.2 illustration `"Qwen3-0.6B"` with that value. Close **U2**: observed values equal the computed ones. Close **U3**: `encoder` = `{"algorithm":"kquant-larql-native","revision":1}` with no `source`, i.e. the default build.

## Phase B: diagnosis (after Phase A was recorded)

I then read `evidence/B3/AUTHOR-NOTES.md` and LARQL at `/Users/christopherhay/chris-source/larql-l1-2536bb79`. `git rev-parse HEAD` = `2536bb79b199b1115445678e3e82c400b0b3fd07`. Both were read-only.

- **No Phase A failure needed explaining.** The one first-run failure was in my test (A2 above). It is explained by the §4.1 padding rule alone, and no source was needed.
- **A1 confirmed from source.** `crates/larql-vindex/src/format/vindex3/graph/build/tables.rs:185-190` sets `tensors: group.tensors` and `bytes: group.bytes` from the source tensor group, with the expert-bank carve adjustment at lines 239-271, which does not apply to this subject. My guess matches the code. This is a spec omission, not a container defect.
- **§14 "LARQL's segment reader does not check `schema`" confirmed.** `encode/segment.rs:245-263` (`read_segment_header`) checks only the 256 MiB bound and that the header parses as JSON. The spec's extra requirement (rule 6) is correct as a reader rule and matches the container (`schema: 1` ×5).
- **The author notes say "Tensor offsets within a Q8_0 pack are only 2-byte aligned".** For this subject that is too pessimistic: all observed offsets are 16-aligned (A3). It is in the notes, not the spec, so the spec needs no change beyond the optional note in A3.
- **U1–U3** are settled by the container itself (O2). The author could not observe them because the container did not exist yet. The spec is not wrong about them.
- **Spec or container wrong?** Neither, for layout. The container matches the spec. The open items are editorial and completeness gaps in the spec.

## Corrections required for admission (not applied)

1. **O2:** update provenance to the fresh container, mark §9 values observed, record the digests, close U1 (`model`/`artifact` = snapshot hash, which replaces the "Qwen3-0.6B" illustration), U2 and U3 (`kquant-larql-native` rev 1).
2. **O1:** name the pinned ggml revision and `ggml-common.h:251-256` as the normative `block_q8_0` reference (f16 `d`, then 32 × int8).
3. **A1:** define `source_bindings[].tensors` and `.bytes` (source tensor count and source byte total; optional cross-check).
4. **A2:** §12(b): say the padding length also differs, and that the parsed headers are equal apart from `representation`.
5. **A3** (optional): §4.3: note that the observed offsets are 16-aligned in this profile, incidentally, while keeping the 2-byte assumption normative.
