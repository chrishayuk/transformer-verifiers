# LARQL VINDEX3 Container: Byte-Level Specification (Q8_0 Qwen3-0.6B profile)

| Field | Value |
|---|---|
| Document | LARQL-VERIFY-001 workstream B3, container specification |
| Status | DRAFT. Not admitted. A third party must check it against emitted files before it is trusted |
| Describes | The files written by LARQL at commit `2536bb79b199b1115445678e3e82c400b0b3fd07` |
| Subject | Qwen/Qwen3-0.6B, official BF16 safetensors, HF commit `c1899de289a04d12100db370d81485cdf75e47ca` |
| Pipeline | `larql vindex3 encode` followed by `larql vindex3 represent --encoding Q8_0` (default role policy), consumed by `larql vindex3 exec --backend production-q8 --representation-source stored` |
| Author | A spec-author subagent with read access to LARQL source (see `evidence/B3/AUTHOR-NOTES.md`) |

## 0. Conventions

The key words MUST, MUST NOT, REQUIRED, SHALL, SHOULD, SHOULD NOT and MAY are to be read as in RFC 2119.

- "Reader" means an independent program that reads a container to locate and identify tensors.
- "Writer" means LARQL at the commit above.
- Bracketed tags such as `[S12]` refer to the Sources appendix (Appendix A). The body can be read without them.
- All integers in binary framing are little-endian. All JSON is UTF-8 (in practice ASCII). Hex digests are 64 lowercase hexadecimal characters with no prefix [S9][S31].
- "Byte offset" always means a 0-based offset from the first byte of the named file, unless the text says "payload-relative".
- This document describes only container framing. It does not describe Q8_0 arithmetic, how any value decodes to a float, numerical tolerances, or reference execution semantics. Those belong to ggml (`block_q8_0`) and gguf-py. Where the container stores a field with a numerical meaning, this document gives its name and byte position only.
- Where a statement was confirmed by inspecting the existing container `/Users/christopherhay/chris-models/qwen3-0.6b.vindex3`, it is marked **(illustration)**. That container has no recorded upstream revision, predates this commit, and holds BF16 only. It is not evidence for the Q8_0 container, which is to be built fresh later.
- Where a value is computed from the code rather than observed in a file, it is marked **(computed)**.

## 1. Pipeline and the variant it selects

### 1.1 Steps

1. **Encode.** `larql vindex3 encode <ARTIFACT> --output <SRC>` reads the HF checkpoint and writes a canonical BF16 container at `<SRC>` [S1][S2]. The exact form of `<ARTIFACT>` (a local directory or `hf://Qwen/Qwen3-0.6B@<rev>`) is **UNDETERMINED** (see §16). It changes only identity strings (§5.2 `model`, §6 `artifact`) and never tensor bytes, shapes, names or order.
2. **Represent.** `larql vindex3 represent <SRC> --output <OUT> --encoding Q8_0` writes a new container at `<OUT>` [S3][S4]. This profile passes no other flags. In particular: no `--include-role`, no `--protect`, no `--protect-layers`, no `--object`, no `--deployment`, no `--moments`, no `--plugin`. `--encoding` defaults to `NVFP4`, so `--encoding Q8_0` MUST be given explicitly [S4].
3. **Execute.** `larql vindex3 exec <OUT> --backend production-q8 --representation-source stored ...` reads `<OUT>` [S5][S6].

The container this document specifies is `<OUT>`.

### 1.2 Variants and which one this pipeline uses

| Variant point | Options in the format | This pipeline |
|---|---|---|
| Container shape | graph shape (`system_graph` set) or legacy bank shape (`moe_manifest` set, LYRW files) [S7] | **Graph shape.** The bank shape is out of scope. A reader for this profile MUST reject a container whose `index.json` has no `system_graph` |
| Authority | `canonical` (archival, keeps source bytes) or `derived` (`--deployment`, drops replaced source bytes) [S8][S10] | **Canonical / archival.** `authority` is absent from `index.json`, which means `canonical` |
| Target encoding | `NVFP4`, `Q4_K`, `Q6_K`, `Q8_0`, or a plugin encoder label [S11] | **`Q8_0`** |
| Role policy | default, or default widened with `--include-role` [S12] | **Default** (§11) |
| Protections | none, or `--protect`/`--protect-layers` exceptions [S12] | **None**. The precision map is named `r0-uniform` [S13] |
| Encoder recipe | `kquant-larql-native` (default build) or `kquant-ggml-reference` (build with the `larql-vindex/reference-encoder` feature) [S14][S15] | Default build: `kquant-larql-native`. Which build L1 uses is **UNDETERMINED** (§16). The recipe never changes the byte layout, only which valid values are chosen |
| Auxiliary reference table | present only when an FP8 weight has a scale sibling [S16] | **Absent** |
| Attestation table | named by `index.json` when present [S17] | **Absent** |

## 2. File and directory layout

`<OUT>` is a directory. Paths below are relative to it. A reader MUST resolve every path relative to the container root, and MUST reject any path that is absolute or contains a `..` component.

| Path | Purpose | Tensor data? | Required for locating tensors? |
|---|---|---|---|
| `index.json` | Root authority. Format version, the representation directory (representation id → segment file, sizes, hashes, codec identity), segment key list, precision map [S8] | No | **Yes** |
| `system_graph.json` | The system graph: components, execution surface, logical objects, source bindings (HF prefixes), and the representations each object has [S18][S19] | No | **Yes**, for the HF-key mapping (§10) and the tied-head facts (§12) |
| `segments/target.decoder_stack.bin` | Canonical BF16 segment of the decoder stack: 308 tensors, all BF16 [S2] | **Yes** | Yes, if a reader wants the BF16 source values |
| `segments/target.decoder_stack@Q8_0.bin` | Compiled Q8_0 pack of the decoder stack: 308 tensors, 196 `Q8_0` and 112 `BF16` carried verbatim [S20] | **Yes** | **Yes**. This is what `production-q8` executes for the decoder |
| `segments/target.embedding.bin` | Canonical BF16 token embedding, 1 tensor | **Yes** | **Yes** |
| `segments/target.final_norm.bin` | Canonical BF16 final RMSNorm weight, 1 tensor | **Yes** | **Yes** |
| `segments/target.output_head.bin` | Canonical BF16 output projection (`lm_head`), 1 tensor | **Yes** | **Yes** |
| `candidate.json` | Compilation provenance sidecar: source-container identity, precision map, per-compiled-tensor seals (source and target SHA-256, absolute target offset and length), resolved decisions, binding digest [S21][S22] | No | No. Informative only (§13.4) |
| `tokenizer.json`, `tokenizer_config.json`, `generation_config.json` | Capability snapshot copied verbatim from the checkpoint [S23][S24] | No | No |
| `special_tokens_map.json`, `chat_template.jinja`, `moe_manifest.json` | Copied only if the source has them. The Qwen3-0.6B snapshot has none of them, so they are absent [S23][S24] | No | No |

Notes:

- The four canonical `segments/*.bin` files are hard links to (or byte copies of) the files in `<SRC>`. Their bytes are identical to `<SRC>`'s [S25].
- A segment file's name is `segments/<object id>.bin` for a canonical representation and `segments/<object id>@<encoding>.bin` for a compiled one. The `@` is a literal byte 0x40 in the filename [S26][S20]. A reader MUST NOT derive a path from this convention. It MUST use `index.json` `representations.<id>.segment` (§5).
- `config.json`, `vocab.json`, `merges.txt` and the source `model.safetensors` are **not** in the container.
- `index.json` is written after every segment and after `system_graph.json` [S27][S28]. A directory with segments but no `index.json` is an incomplete write and MUST be rejected.

## 3. Common encodings

- **Little-endian everywhere.** The segment header length is a u64 LE [S29]. BF16 tensor payloads are the safetensors bytes copied verbatim, so each BF16 element is 2 bytes, little-endian, in bfloat16 bit layout [S30]. Q8_0 payloads are ggml `block_q8_0` blocks (§8.4).
- **JSON.** `index.json`, `system_graph.json` and `candidate.json` are pretty-printed JSON. Segment headers are compact JSON followed by space padding (§4). A reader MUST parse them as JSON and MUST NOT depend on key order, whitespace or indentation. Unknown keys MUST be ignored unless this document says otherwise (§14).
- **Digests.** SHA-256 as 64 lowercase hex characters [S9][S31].

## 4. Segment file byte layout

Every `.bin` file listed in `index.json.representations` is one segment with this layout [S29]:

```text
offset 0                 : u64 LE  H   (header length in bytes, padding included)
offset 8                 : H bytes     header = compact JSON object, then 0..15 bytes of 0x20 (space)
offset 8+H  (= P)        : payload     tensor payloads concatenated in header-table order
end of file              : P + payload_bytes
```

### 4.1 Header length and padding

- `H` is the byte length of the JSON text **plus** the trailing padding [S32].
- The writer appends `pad = (16 - (8 + J) mod 16) mod 16` ASCII spaces (0x20) after the `J`-byte JSON text, so that `P = 8 + H` is a multiple of 16 [S32]. Padding is therefore 0 to 15 bytes.
- A reader MUST treat bytes `8 .. 8+H` as a JSON document that may carry trailing whitespace. A conforming JSON parser accepts the padding.
- A reader MUST NOT require `P mod 16 == 0`. LARQL defines 16 as the writer's alignment and 4 bytes as the execution minimum, and accepts segments aligned only to 4 [S33]. This pipeline's writer always produces `P mod 16 == 0`. A reader SHOULD report `P mod 4 != 0` as a defect.
- LARQL rejects `H > 268435456` (256 MiB) as corrupt [S34]. A reader MUST reject it too.
- **(illustration)** In the BF16 container the decoder-stack header is `H = 31448` (`P = 31456`); the embedding and output-head headers are `H = 152` (`P = 160`); the final-norm header is `H = 136` (`P = 144`). The decoder-stack header ends in 8 spaces.

### 4.2 Header JSON schema

The header is a JSON object [S35]:

| Key | JSON type | Meaning |
|---|---|---|
| `schema` | integer (u32) | Segment header schema. MUST equal `1` [S36] |
| `representation` | string | The representation id this segment holds, `"<object id>@<encoding>"`. MUST equal the key under which `index.json.representations` lists this segment [S37] |
| `tensors` | array of tensor entries | The tensor table. Array order is payload order |

Tensor entry [S35]:

| Key | JSON type | Meaning |
|---|---|---|
| `name` | string | Tensor name relative to the logical object (§10). Unique within the table |
| `dtype` | string | Representation label of **this tensor's** bytes. Exact strings for this profile: `"BF16"` or `"Q8_0"` (§8) |
| `shape` | array of non-negative integers | Logical shape in elements, outermost first. For `Q8_0` tensors this is still the element shape, not a byte or block shape [S20] |
| `offset` | integer (u64) | Payload-relative byte offset of the tensor's first byte |
| `len` | integer (u64) | Byte length of the tensor's payload |

The writer emits keys in the order shown, with no other keys. A reader MUST ignore unknown keys.

### 4.3 Table order and contiguity

- The table is sorted ascending by `name`, comparing names as byte strings (Rust `String` ordering, i.e. lexicographic over UTF-8 bytes) [S38]. Because `'.'` (0x2E) sorts before `'0'` (0x30), layer `1.` sorts before `10.`. Decoder layers therefore appear in the order `0, 1, 10, 11, ..., 19, 2, 20, ..., 27, 3, 4, 5, 6, 7, 8, 9` **(illustration: observed)**.
- Offsets are contiguous with no gaps or padding between tensors: `offset[0] = 0` and `offset[i] = offset[i-1] + len[i-1]` [S39]. The sum of all `len` equals the payload size.
- Individual tensor offsets have **no** alignment guarantee beyond what the lengths imply. A Q8_0 tensor's offset may be any even number.
- The file's total length MUST equal `P + Σ len` and MUST equal `P + index.json.representations.<id>.payload_bytes`. LARQL's inspector reports a mismatch as a defect [S40].

A reader MUST verify: `schema == 1`; the table names are unique; offsets are contiguous as above; every `offset + len <= payload length`; the file length rule holds. A reader MUST reject a segment that fails any of these.

### 4.4 Locating a tensor's bytes in a segment

```text
absolute_start = 8 + H + entry.offset
absolute_end   = absolute_start + entry.len        (exclusive)
```

## 5. `index.json`

### 5.1 Role

`index.json` is the root authority. A reader MUST start from it, and MUST find segments only through `representations.<id>.segment`. LARQL never globs the `segments/` directory [S8][S41].

### 5.2 Top-level schema

Fields for this profile. Fields marked "absent" are omitted from the file when empty or default [S8].

| Key | JSON type | Required | Value in this profile |
|---|---|---|---|
| `version` | integer (u32) | MUST | `4`. The sole format-generation discriminator [S42] |
| `model` | string | MUST | The artifact name the encoder recorded. It depends on how encode was invoked (§16): the checkpoint path's file stem for a local path, or the repo's last path component for `hf://` [S43][S44]. **(illustration)** `"Qwen3-0.6B"`. A reader MUST NOT depend on it |
| `family` | string | MUST | `"qwen3"`: the checkpoint's `model_type` [S45] |
| `hidden_size` | integer | MUST | `1024` |
| `num_layers` | integer | MUST | `28` |
| `moe_manifest` | string | absent | Absent. A reader for this profile MUST reject its presence |
| `system_graph` | string | MUST | `"system_graph.json"`: path of the system graph relative to the root [S46] |
| `auxiliary_references` | string | absent | Absent. If present, it names a reference table that this profile does not cover; a reader MUST reject it |
| `representation_attestations` | string | absent | Absent. If present, a reader MAY ignore it for locating tensors |
| `representations` | object: representation id → RepresentationEntry (§5.3) | MUST | Exactly five entries (§9.2) |
| `profiles` | array of `{ "name": string, "selects"?: object }` | MUST | `[{"name":"exact"}]` [S47]. Not needed to locate tensors |
| `variants` | object | absent | Absent (empty catalogue) |
| `segments` | object: segment key → integer | MUST | Segment key = segment path without the `.bin` suffix, value `1` (one physical file). This profile has five keys: `segments/target.decoder_stack`, `segments/target.decoder_stack@Q8_0`, `segments/target.embedding`, `segments/target.final_norm`, `segments/target.output_head` [S26][S48] |
| `authority` | string, `"canonical"` or `"derived"` | absent | Absent, which means `"canonical"` [S10]. A reader for this profile MUST reject `"derived"` |
| `precision_map` | object (§5.4) | MUST in this profile | The precision program the pack was compiled under [S13] |
| `derived_from_model` | string | absent | Absent (present only on derived images) |
| any other key | any | — | Preserved by LARQL [S49]. A reader MUST ignore it |

### 5.3 RepresentationEntry

The key is the representation id `"<object id>@<encoding>"` [S50]. The value is an object [S51]:

| Key | JSON type | Present on | Meaning |
|---|---|---|---|
| `object` | string | all | Logical object id (a `system_graph.json` object `id`) |
| `encoding` | string | all | Representation encoding label: `"BF16"` (canonical) or `"Q8_0"` (compiled pack). It is per object, **not** per tensor: a `Q8_0` pack also holds `BF16` tensors (§8.1) |
| `segment` | string | all | Segment file path, relative to the root |
| `tensor_count` | integer | all | Number of entries in that segment's tensor table. MUST equal it [S40] |
| `payload_bytes` | integer (u64) | all | Size of the payload region (excludes the 8-byte prefix and the header) |
| `payload_sha256` | string (hex) | all | SHA-256 over the payload region only (§13) |
| `segment_sha256` | string (hex) | all | SHA-256 over the whole segment file as written (§13) |
| `compiled_from` | string | compiled only | The representation id the pack was compiled from: `"target.decoder_stack@BF16"` [S52] |
| `codec` | object (CodecIdentity, §8.3) | compiled only | The decode contract of the pack's compiled tensors [S53] |
| `source_representation_digest` | string (hex) | compiled only | The `payload_sha256` of the representation in `compiled_from` [S52] |
| `encoder` | object `{ "algorithm": string, "revision": integer, "source"?: string }` | compiled only | Which encoder chose the values. It does not affect layout. A mismatch is never a reason to reject [S54] |

The keys `compiled_from`, `codec`, `source_representation_digest` and `encoder` are absent (not `null`) on the four canonical BF16 entries [S51][S55].

### 5.4 `precision_map`

```json
{ "name": "r0-uniform",
  "encoding": "Q8_0",
  "roles": ["decoder-linear", "recurrence-projection", "recurrence-control", "expert-weight"] }
```

| Key | JSON type | Meaning |
|---|---|---|
| `name` | string | `"r0-uniform"` when there are no protections [S13] |
| `encoding` | string | The encoding eligible tensors take |
| `roles` | array of string | Role names (§11) the program compiles. Every other role stays at source precision [S56] |
| `exceptions` | array | Absent in this profile (no `--protect`) |

The precision map is a policy statement. A reader MUST NOT use it to decide a tensor's representation. The per-tensor `dtype` in the segment header is authoritative for that (§8.1, §15).

## 6. `system_graph.json` (fields needed by a reader)

LARQL refuses any graph whose `schema` is not `6` [S57]. Top-level object [S19]:

| Key | JSON type | Meaning |
|---|---|---|
| `schema` | integer | MUST equal `6` |
| `components` | array of Component | Here exactly one, `id` `"target"`, `role` `"primary_text"` |
| `objects` | array of LogicalObject | Here exactly four, sorted by `id` |
| `edges` | array | Here empty |

Component fields used by this document: `id`, `role`, `num_layers` (28), `hidden_size` (1024), and `execution.head` (HeadSurface: `vocab_size` 151936 and `head_reuses_embedding` true) [S58] **(illustration)**. A reader MAY ignore the rest of the component, which describes execution semantics.

LogicalObject [S59]:

| Key | JSON type | Meaning |
|---|---|---|
| `id` | string | `"<component>.<kind>"`, e.g. `"target.decoder_stack"` |
| `component` | string | `"target"` |
| `kind` | string | One of `"decoder_stack"`, `"embedding"`, `"final_norm"`, `"output_head"` in this profile [S60] |
| `source_bindings` | array of `{ "artifact": string, "tensor_prefix": string, "tensors": integer, "bytes": integer }` | Where the object's tensors came from in the source checkpoint. Exactly one binding per object in this profile |
| `representations` | array of `{ "encoding": string, "fidelity": "canonical" \| "approximate" }` | Materialisations. Element 0 is the canonical one [S61]. After `represent`, `target.decoder_stack` has `[{"encoding":"BF16","fidelity":"canonical"},{"encoding":"Q8_0","fidelity":"approximate"}]` and the other three objects have only the BF16 entry [S62] |

`represent` rewrites `system_graph.json`, adding the `Q8_0` entry and changing nothing else [S62].

## 7. Locating a tensor: the reader algorithm

To find logical tensor `(object, name)` in the representation that `production-q8 --representation-source stored` executes:

1. Read `index.json`. Check `version == 4` and the other rules in §14.
2. Read `system_graph.json` (the path is `index.json.system_graph`). Check `schema == 6`.
3. Pick the representation id. If `"<object>@Q8_0"` is a key of `index.json.representations`, use it. Otherwise use `"<object>@" + E`, where `E` is the `encoding` of element 0 of that object's `representations` in `system_graph.json`. This is exactly the selection rule of the LARQL operand store when the backend asks for `Q8_0` and the source is `stored` [S63][S64]. For this profile the result is `target.decoder_stack@Q8_0`, `target.embedding@BF16`, `target.final_norm@BF16` and `target.output_head@BF16`.
4. Let `entry = index.json.representations[id]`. If `entry.codec` is present, check it (§8.3).
5. Open `entry.segment`, parse the header (§4), and check it (§4.3), including `header.representation == id`.
6. Find the table entry with `name == name`. If it is absent, the tensor does not exist in that representation, and a reader MUST report an error. It MUST NOT fall back to another representation silently.
7. The bytes are file range `[8 + H + offset, 8 + H + offset + len)`. Their representation is the entry's `dtype` (§8).

To read canonical BF16 source values instead, use `"<object>@BF16"` in step 3.

## 8. Tensor metadata and payload layouts

### 8.1 Where the representation type is stated

The representation of each tensor's bytes is **its own `dtype` field in the segment header**. In a compiled pack, a compiled tensor has `dtype` equal to the target encoding (`"Q8_0"`), and a carried tensor keeps its source `dtype` (`"BF16"`) and its source bytes unchanged [S20]. The representation-level `encoding` (§5.3) does not decide any single tensor's representation. A reader MUST dispatch on the per-tensor `dtype`.

Exact `dtype` strings in this profile:

| `dtype` | Byte length of a tensor of shape `[d0, ..., dn-1]` | Layout |
|---|---|---|
| `"BF16"` | `2 × Π di` | §8.2 |
| `"Q8_0"` | `(Π_{i<n-1} di) × (dn-1 / 32) × 34` | §8.4 |

A reader MUST reject any other `dtype` in this profile, and MUST reject a tensor whose `len` disagrees with this table.

### 8.2 BF16 tensors

- Bytes are the source safetensors payload, copied verbatim with no cast, transpose, reshape or reordering [S30][S65].
- The element order is the safetensors order: row-major (C order) over `shape`, with the last dimension contiguous. A 1-D tensor of length `n` is `n` consecutive 2-byte elements.
- **(computed, by the safetensors convention)** A 2-D weight `[R, K]` stores row `r` at payload-relative bytes `[2·K·r, 2·K·(r+1))`.

### 8.3 Q8_0 codec identity (in `index.json`)

The compiled pack's `codec` field is [S53][S66]:

```json
{ "family": "Q8_0", "revision": 1, "group_elems": 32,
  "element": "ggml-q8_0", "group_scale": "in-block",
  "tensor_scale": "in-block", "layout": "ggml-block-34" }
```

| Key | Type | Value | Meaning |
|---|---|---|---|
| `family` | string | `"Q8_0"` | Representation family. Equals the `dtype` of the pack's compiled tensors |
| `revision` | integer | `1` | ABI revision of LARQL's K-quant packs [S67] |
| `group_elems` | integer | `32` | Elements per block |
| `element` | string | `"ggml-q8_0"` | The element grid is ggml's Q8_0 |
| `group_scale` | string | `"in-block"` | The scale lives inside each block |
| `tensor_scale` | string | `"in-block"` | No tensor-level scale outside the blocks |
| `layout` | string | `"ggml-block-34"` | Each block is a 34-byte ggml block |

LARQL admits a pack only if this object is **exactly equal** to the identity its build implements, field by field. Otherwise it refuses the pack [S68][S64]. A reader MUST do the same: reject a `Q8_0` pack whose `codec` differs from the object above in any field, and reject a `Q8_0`-dtype tensor in a representation that has no `codec`.

The codec applies to those tensors in the pack whose `dtype` equals `codec.family`. The pack's carried `BF16` tensors are not governed by it.

### 8.4 Q8_0 tensors: row orientation and block placement

For a `Q8_0` tensor with `shape = [d0, ..., dn-1]` (n ≥ 1) [S69][S70][S71]:

- **Row length** `K = dn-1` (the last, innermost dimension). `K` MUST be a multiple of 32. The writer refuses to compile a tensor whose row length is not, and carries it in its source dtype instead [S69].
- **Row count** `R = Π_{i<n-1} di` (1 for a 1-D tensor). Rows are in row-major order over the leading dimensions.
- **Blocks per row** `B = K / 32`. **Row stride** `S = B × 34` bytes. Rows are contiguous with no padding between rows or blocks, and no per-tensor header or trailer.
- **Tensor length** `len = R × S`.
- **Block `b` of row `r`** (0 ≤ r < R, 0 ≤ b < B) occupies payload-relative bytes
  `[offset + (r·B + b)·34, offset + (r·B + b)·34 + 34)`
  and covers source elements `r·K + 32·b ... r·K + 32·b + 31` of the row-major flattening.
- **Block contents:** Q8_0 block, 34 bytes, layout per ggml `block_q8_0`. This document does not describe the block's internal fields or how they decode.

For the weights of this subject, `shape = [out_features, in_features]`, as in the HF `nn.Linear` convention. A row is one output feature, and blocks run along the input dimension. No tensor is transposed (§10.3).

## 9. Contents of the Q8_0 Qwen3-0.6B container

### 9.1 Logical objects

| Object id | `kind` | HF `tensor_prefix` | Tensors | Representations in `index.json` |
|---|---|---|---|---|
| `target.decoder_stack` | `decoder_stack` | `model.layers` | 308 | `@BF16` (canonical), `@Q8_0` (compiled) |
| `target.embedding` | `embedding` | `model.embed_tokens` | 1 | `@BF16` only |
| `target.final_norm` | `final_norm` | `model.norm` | 1 | `@BF16` only |
| `target.output_head` | `output_head` | `lm_head` | 1 | `@BF16` only |

The binding prefixes come from the graph builder's group classification [S72] **(illustration)**. 308 + 1 + 1 + 1 = 311, which equals the checkpoint's tensor count. Every HF tensor appears exactly once per representation of its object.

### 9.2 `index.json.representations` (expected)

| Id | `segment` | `tensor_count` | `payload_bytes` |
|---|---|---|---|
| `target.decoder_stack@BF16` | `segments/target.decoder_stack.bin` | 308 | 880,932,864 **(illustration)** |
| `target.decoder_stack@Q8_0` | `segments/target.decoder_stack@Q8_0.bin` | 308 | 468,056,064 **(computed)** |
| `target.embedding@BF16` | `segments/target.embedding.bin` | 1 | 311,164,928 **(illustration)** |
| `target.final_norm@BF16` | `segments/target.final_norm.bin` | 1 | 2,048 **(illustration)** |
| `target.output_head@BF16` | `segments/target.output_head.bin` | 1 | 311,164,928 **(illustration)** |

The hashes of the fresh container are **UNDETERMINED** until it is built.

### 9.3 Single-tensor segments

| Segment | Table entry |
|---|---|
| `target.embedding@BF16` | `{"name":"weight","dtype":"BF16","shape":[151936,1024],"offset":0,"len":311164928}` |
| `target.output_head@BF16` | `{"name":"weight","dtype":"BF16","shape":[151936,1024],"offset":0,"len":311164928}` |
| `target.final_norm@BF16` | `{"name":"weight","dtype":"BF16","shape":[1024],"offset":0,"len":2048}` |

**(illustration)** These do not change under `represent`.

### 9.4 Decoder-stack tensors

Each layer `L` in 0..27 has 11 tensors. The table below is for the `@Q8_0` pack **(computed)**. In the `@BF16` segment every tensor is `BF16`, with `len = 2 × elements`.

| Relative name | Shape | `dtype` in `@Q8_0` | `len` in `@Q8_0` | Offset within the layer group in `@Q8_0` |
|---|---|---|---|---|
| `L.input_layernorm.weight` | [1024] | BF16 | 2,048 | 0 |
| `L.mlp.down_proj.weight` | [1024, 3072] | Q8_0 | 3,342,336 | 2,048 |
| `L.mlp.gate_proj.weight` | [3072, 1024] | Q8_0 | 3,342,336 | 3,344,384 |
| `L.mlp.up_proj.weight` | [3072, 1024] | Q8_0 | 3,342,336 | 6,686,720 |
| `L.post_attention_layernorm.weight` | [1024] | BF16 | 2,048 | 10,029,056 |
| `L.self_attn.k_norm.weight` | [128] | BF16 | 256 | 10,031,104 |
| `L.self_attn.k_proj.weight` | [1024, 1024] | Q8_0 | 1,114,112 | 10,031,360 |
| `L.self_attn.o_proj.weight` | [1024, 2048] | Q8_0 | 2,228,224 | 11,145,472 |
| `L.self_attn.q_norm.weight` | [128] | BF16 | 256 | 13,373,696 |
| `L.self_attn.q_proj.weight` | [2048, 1024] | Q8_0 | 2,228,224 | 13,373,952 |
| `L.self_attn.v_proj.weight` | [1024, 1024] | Q8_0 | 1,114,112 | 15,602,176 |

A layer group in `@Q8_0` is 16,716,288 bytes. Layer groups appear in the byte-sorted order of §4.3. **(computed)** The header JSON is 31,408 bytes plus 8 bytes of padding, so `H = 31,416`, `P = 31,424`, and the file is 468,087,488 bytes.

This table is informative, for cross-checking. A reader MUST take offsets and lengths from the header, not from this table.

## 10. Mapping LARQL names to Hugging Face keys

### 10.1 Rule

For a tensor with relative name `n` in object `o`, the HF safetensors key is

```text
hf_key = p + "." + n
```

where `p` is the `tensor_prefix` of the only element of `o.source_bindings` in `system_graph.json` [S73][S74].

This is exact for this profile, because each object has exactly one binding. The encoder strips the longest dot-segment prefix common to all of an object's bindings, then strips any leading `.` [S73][S75]. With one binding, that prefix is the binding's `tensor_prefix`. Membership is "the name equals the prefix, or starts with the prefix followed by `.`", and the longest covering prefix wins across objects [S76][S77]. A reader MUST reject an object with more than one binding under this profile, since the inverse is then not guaranteed to be unique.

The rule holds for both representations of an object: a compiled pack keeps each tensor's relative name [S20].

### 10.2 Complete mapping for Qwen3-0.6B

| Object | LARQL relative name | HF key |
|---|---|---|
| `target.decoder_stack` | `L.input_layernorm.weight` | `model.layers.L.input_layernorm.weight` |
| `target.decoder_stack` | `L.post_attention_layernorm.weight` | `model.layers.L.post_attention_layernorm.weight` |
| `target.decoder_stack` | `L.self_attn.q_proj.weight` | `model.layers.L.self_attn.q_proj.weight` |
| `target.decoder_stack` | `L.self_attn.k_proj.weight` | `model.layers.L.self_attn.k_proj.weight` |
| `target.decoder_stack` | `L.self_attn.v_proj.weight` | `model.layers.L.self_attn.v_proj.weight` |
| `target.decoder_stack` | `L.self_attn.o_proj.weight` | `model.layers.L.self_attn.o_proj.weight` |
| `target.decoder_stack` | `L.self_attn.q_norm.weight` | `model.layers.L.self_attn.q_norm.weight` |
| `target.decoder_stack` | `L.self_attn.k_norm.weight` | `model.layers.L.self_attn.k_norm.weight` |
| `target.decoder_stack` | `L.mlp.gate_proj.weight` | `model.layers.L.mlp.gate_proj.weight` |
| `target.decoder_stack` | `L.mlp.up_proj.weight` | `model.layers.L.mlp.up_proj.weight` |
| `target.decoder_stack` | `L.mlp.down_proj.weight` | `model.layers.L.mlp.down_proj.weight` |
| `target.embedding` | `weight` | `model.embed_tokens.weight` |
| `target.final_norm` | `weight` | `model.norm.weight` |
| `target.output_head` | `weight` | `lm_head.weight` |

`L` ranges over the decimal integers 0..27, with no zero padding. That gives 28 × 11 + 3 = 311 keys, a bijection with the checkpoint's 311 keys.

### 10.3 Transformations

- **Encode (HF → `@BF16`)**: none. No tensor is transposed, fused, split, renamed beyond prefix stripping, reshaped or cast. `dtype` and `shape` are the safetensors header's verbatim, and the bytes are the safetensors payload verbatim [S30][S65][S78].
- **Represent (`@BF16` → `@Q8_0`)**: the 196 decoder projections are re-encoded from BF16 to Q8_0, with shape and name unchanged. The 112 decoder norm vectors are copied byte for byte [S20]. Nothing else changes. The source values the encoder reads are the `@BF16` segment's BF16 bytes, widened to f32 [S79]. How those values become Q8_0 blocks is out of scope.
- **Tied weights**: `model.embed_tokens.weight` and `lm_head.weight` are separate keys in the checkpoint, and they map to separate objects (§12).

## 11. Role policy for this subject

### 11.1 How a role is assigned

Each tensor gets one role [S80][S81]:

1. If the operation plan binds the tensor, the plan's role wins. For Qwen3, the plan binds `q/k/v/o_proj` and `gate/up/down_proj` as `decoder-linear` [S82].
2. Otherwise, a name rule applies. Any tensor whose shape does not have exactly 2 dimensions is `small-vector`. An object id containing `embedding` → `embedding`; containing `output_head` → `output-head`; containing `final_norm` → `norm`. Otherwise a name containing `norm` → `norm`, and so on [S80].

### 11.2 Default policy

The default compiles exactly the roles `decoder-linear`, `recurrence-projection`, `recurrence-control` and `expert-weight`, and preserves every other role [S83][S84]. A compiled role still requires a fitting shape: for Q8_0, a row length that is a multiple of 32 [S69][S85].

### 11.3 Result for Qwen3-0.6B

| Tensors | Count | Role | Representation that `production-q8` executes |
|---|---|---|---|
| `L.self_attn.{q,k,v,o}_proj.weight`, `L.mlp.{gate,up,down}_proj.weight` | 196 | `decoder-linear` | **Q8_0** in `target.decoder_stack@Q8_0` |
| `L.input_layernorm.weight`, `L.post_attention_layernorm.weight`, `L.self_attn.q_norm.weight`, `L.self_attn.k_norm.weight` | 112 | `small-vector` (1-D) | BF16, carried in `target.decoder_stack@Q8_0` |
| `target.embedding / weight` | 1 | `embedding` | BF16, `target.embedding@BF16` (no pack) |
| `target.output_head / weight` | 1 | `output-head` | BF16 as stored, `target.output_head@BF16` (no pack). See §12(d) for what the executor does with it at load |
| `target.final_norm / weight` | 1 | `small-vector` (1-D) | BF16, `target.final_norm@BF16` (no pack) |

All 196 row lengths (1024, 2048, 3072) are multiples of 32, so no eligible tensor is layout-refused. Objects with no compiled tensor get no pack: the writer records them as preserved and writes no `@Q8_0` segment for them [S86].

A reader does not need this section to identify representations. §8.1 is sufficient.

## 12. Tied embeddings

The checkpoint declares `tie_word_embeddings: true`, and it ships both `model.embed_tokens.weight` and `lm_head.weight`, whose payload bytes are identical (SHA-256 `8f29acf5…acfb6` for both, measured on the HF file).

**(a) Logical identity. No.** The container holds two distinct logical objects, `target.embedding` (bound to `model.embed_tokens`) and `target.output_head` (bound to `lm_head`), because the graph builder classifies the `lm_head` group as its own output-head object [S72]. The graph does record the tie: the component's head surface has `head_reuses_embedding: true` [S58][S87]. But that flag only means that a *missing* output-head object should be read as "reuse the embedding" [S88]. When an output-head object exists, the operation plan binds the head operand to it, and falls back to the embedding only if no output-head object exists [S89]. For this subject, the head operand is `target.output_head` / `weight`.

**(b) Physical storage. Two copies.** `segments/target.embedding.bin` and `segments/target.output_head.bin` each hold a full 311,164,928-byte BF16 matrix **(illustration: both present, same `payload_sha256`, different `segment_sha256` because the header names differ)**. Nothing in the format stores a single shared copy for this subject.

**(c) Numerical representation. Identical stored values, but not guaranteed by the format.** Under the default policy, neither object is compiled. Both stay BF16, copied verbatim from checkpoint payloads that are byte-identical, so both stored tensors decode to identical values. A reader can confirm this from the container alone: the two entries' `payload_sha256` values are equal. LARQL neither checks nor enforces this equality. A different checkpoint, or a policy that included `embedding` or `output-head`, could make them differ, because each object would be compiled or preserved independently [S84][S20].

**(d) Execution with `production-q8 --representation-source stored`.**
- **Stored representation consumed:** `target.output_head@BF16`, tensor `weight`. There is no `target.output_head@Q8_0`, so the store binds the canonical BF16 segment [S63]. The embedding lookup reads `target.embedding@BF16` (realisation `DecodedGather`) [S90].
- **What the executor does with it at load (from reading the code, not observed by a run):** the CPU production selector treats the head as an `OutputHead`-class projection over a BF16 source with 155,582,464 elements. Under the default environment (`LARQL_CPU_MAX_FORMAT` and `LARQL_CPU_ARITHMETIC` unset) and on any host whose L2 is smaller than the 311 MB BF16 image, it chooses `Requantise(FusedQ8)` [S91][S92][S93]. The loader then re-quantises the BF16 head at load into LARQL's internal Q8 residency (`quantise_q8`, 64-element blocks). That is **not** ggml Q8_0, and it is **not** stored in the container [S94][S95]. This path does not call the `stored` guard (`note_runtime_quantisation`), so `--representation-source stored` does not refuse it, and the run still reports `runtime compile: 0` [S96][S97]. The executor's own `projection plans:` output line is where a run reveals this [S97].
- **Consequence for a verifier:** the output projection that `production-q8` executes is a load-time derivative of `target.output_head@BF16`, not a container representation. A reference reconstruction from the container alone cannot reproduce it bit for bit without LARQL's internal quantiser, which is out of this document's scope. This is recorded as a discoverability failure (§15, item F4) and as a code/doc disagreement in the author notes.

## 13. Integrity

### 13.1 Digests in `index.json`

For each representation entry [S51][S98]:

| Field | Algorithm | Covers |
|---|---|---|
| `payload_sha256` | SHA-256, lowercase hex | Segment bytes `[P, EOF)`: the concatenated tensor payloads, in table order, excluding the 8-byte prefix, the header and its padding |
| `segment_sha256` | SHA-256, lowercase hex | Every byte of the segment file `[0, EOF)`: the 8-byte length prefix, the header including padding, and the payload |
| `source_representation_digest` (compiled pack only) | SHA-256, lowercase hex | Equals the `payload_sha256` of the `compiled_from` representation: here, the `@BF16` decoder payload |

For canonical representations, `payload_sha256` is computed while copying from the checkpoint. It therefore equals SHA-256 over the source tensors' safetensors payload bytes concatenated in segment order [S98][S99]. There is no per-tensor digest in `index.json` or in the segment header.

### 13.2 What a reader MUST check

A reader MUST verify `segment_sha256` against the whole file and `payload_sha256` against the payload region before trusting any tensor bytes, and MUST reject on any mismatch. LARQL's `inspect --verify` re-hashes only `segment_sha256` [S100]. Re-hashing `payload_sha256` is required here as an extra check, not as a description of LARQL. A reader SHOULD check that `source_representation_digest` of `target.decoder_stack@Q8_0` equals `payload_sha256` of `target.decoder_stack@BF16`.

### 13.3 What digests do not cover

No digest covers `index.json` or `system_graph.json` themselves. A relabelled `dtype` or `shape` over identical payload bytes leaves `payload_sha256` intact, though `segment_sha256` changes because it covers the header [S101]. No signature or MAC exists. The digests detect accidental corruption and are not an authenticity mechanism.

### 13.4 `candidate.json` (informative)

`candidate.json` records, for each compiled tensor, an `OperandSeal`: `object`, `tensor`, `encoding`, `source_hash` (SHA-256 of the tensor's bytes in the source `@BF16` segment), `target_hash` (SHA-256 of the tensor's bytes in the `@Q8_0` segment), `target_offset` (an **absolute** file offset, `P + offset`) and `target_len` [S102][S103]. These are under `ledger.sealed`, keyed `"<object>\u0001<tensor>"` [S104]. It also contains `source.locator_hint`, the source container's filesystem path, which makes the file's bytes non-reproducible across machines [S105]. A reader MAY use the seals as a per-tensor cross-check. It MUST NOT need `candidate.json` to locate or identify tensors. Its full schema is not specified here.

## 14. Versioning and rejection rules

A reader for this profile MUST reject the container if any of the following holds:

1. `index.json` is missing, is not a JSON object, or has no `version` field [S106].
2. `index.json.version != 4`. LARQL reads versions 3 and 4 as VINDEX3 and 1–2 as the older VINDEX2 generation, and refuses all others. This profile specifies version 4 only [S42][S107].
3. `system_graph` is absent, or `moe_manifest` is present (§1.2) [S7].
4. `system_graph.json` `schema != 6` [S57].
5. A graph object has no entry in `representations`, or a `representations` entry names an object absent from the graph [S40].
6. Any segment fails §4.3, or its `header.representation` differs from its key, or `tensor_count` differs from its table length, or the file length is not `P + payload_bytes` [S40].
7. A digest mismatch (§13.2).
8. A `Q8_0` pack whose `codec` is not exactly the object in §8.3, or a `Q8_0` tensor whose row length is not a multiple of 32, or a tensor whose `len` disagrees with §8.1 [S68][S69].
9. `authority == "derived"`, or `auxiliary_references` present (outside this profile).
10. A `dtype` other than `"BF16"` or `"Q8_0"`.

Versioning facts:

- `index.json.version` is the sole generation discriminator. LARQL never decides by sniffing filenames or directory shape [S108].
- The segment header has its own `schema` (currently 1). LARQL's segment reader does **not** check it [S34]. Rule 6 above requires it anyway.
- The graph has its own `schema` (currently 6), checked before the graph is parsed [S57].
- The codec has its own `revision` (currently 1), checked together with the other identity fields [S68].
- `index.json` keys this build does not know are preserved by LARQL on rewrite [S49]. A reader MUST ignore them.

## 15. Discoverability from the container

Requirement: every tensor's representation type and quantisation metadata must be discoverable from the container itself, without knowing the role policy in advance.

**Met:**

- **D1. Per-tensor representation type.** Each tensor's `dtype` in its segment header names it exactly (`"BF16"` or `"Q8_0"`) [S20][S35]. No role-policy knowledge is needed.
- **D2. Q8_0 block geometry.** Block size (32 elements), block byte size (34), the element grid (`ggml-q8_0`) and the in-block scale placement are stated by the pack's `codec` object in `index.json` [S53][S66].
- **D3. Which representation executes.** It follows from `index.json` alone by the rule in §7 step 3.
- **D4. HF key mapping.** It follows from `system_graph.json` `source_bindings[].tensor_prefix` (§10).

**Failures and partial failures:**

- **F1. Row orientation and element order are not declared.** No field states that `shape` is row-major, that the last dimension is the contiguous one, or that Q8_0 blocks run along the last dimension. These follow from convention (safetensors C order, ggml row blocking) and from LARQL's code [S70], not from the container.
- **F2. Endianness and scale type are not declared.** No field states little-endian, or that the in-block scale is IEEE f16. `"in-block"` and `"ggml-q8_0"` name ggml's definition by reference, and no ggml type number is stored.
- **F3. Codec scope is implicit.** The `codec` belongs to the representation, but a `Q8_0` pack mixes `Q8_0` and `BF16` tensors. That it applies only to tensors whose `dtype` equals `codec.family` is an inference, not a stated rule.
- **F4. The executed LM-head representation is not discoverable.** The container shows the head as BF16 (`target.output_head@BF16`). `production-q8` actually executes a LARQL-internal Q8 image manufactured from it at load (§12(d)). Nothing in the container records this. It depends on the host's L2 size and on `LARQL_*` environment variables.
- **F5. The tie is ambiguous.** `head_reuses_embedding: true` sits beside a separate `target.output_head` object. Which tensor the head uses (the output-head object) follows only from LARQL's plan-building rule [S89], not from an explicit field.
- **F6. Source precision of an unprotected tensor.** For a BF16 tensor inside the `Q8_0` pack, the container does not say *why* it is BF16 (protected role versus layout refusal). The `precision_map` gives the policy but needs the role classifier to apply. `candidate.json` records the decision per tensor (`Source` or `LayoutRefused`) [S106b], but it is not part of the reader's required path. This does not affect locating or identifying bytes.

## 16. UNDETERMINED

| Item | What was tried |
|---|---|
| U1. Exact `vindex3 encode` invocation (local snapshot path versus `hf://Qwen/Qwen3-0.6B@c1899de2…`). It decides `index.json.model`, `source_bindings[].artifact` and `candidate.json` contents | Read the protocol (`draft.json`, `PROTOCOL.md`), which states only the `represent` and `exec` commands. Read the naming rules [S43][S44]. A local path to the HF snapshot directory would record its stem `c1899de289a04d12100db370d81485cdf75e47ca` as the model name |
| U2. All digests and the observed header lengths of the fresh Q8_0 container | No Q8_0 container exists on disk (searched `~/chris-models` to depth 4). The values in §9 are computed by reproducing LARQL's header serialisation from the illustration's BF16 header, a method that reproduced that header's bytes exactly |
| U3. Build features used by L1 (whether `reference-encoder` is enabled), which decides the `encoder` field | The CLI's default features do not enable it [S15]. The L1 build command is not recorded |
| U4. The realised LM-head kernel on the L1 host | Depends on the host's L2 size and on `LARQL_CPU_MAX_FORMAT`/`LARQL_CPU_ARITHMETIC` [S92][S93]. Determined by code reading only. Not run |
| U5. Full schema of `candidate.json` and of the `system_graph.json` component execution surface | Out of the reader's path. Only the fields needed are specified |
| U6. Byte-exact `index.json` and `system_graph.json` text | Pretty-printed by `serde_json`. Readers must not depend on it |

## Appendix A. Sources

All paths are relative to the LARQL worktree root `/Users/christopherhay/chris-source/larql-l1-2536bb79` at commit `2536bb79b199b1115445678e3e82c400b0b3fd07`. `VX` = `crates/larql-vindex/src/format/vindex3`. `CLI` = `crates/larql-cli/src/commands/primary/vindex3_cmd`.

| Tag | Location | Supports |
|---|---|---|
| S1 | `CLI/args.rs:15-18`, `CLI/args.rs:398-426`, `CLI/verify_encode.rs:132-149` | `vindex3 encode` verb and arguments |
| S2 | `VX/encode/mod.rs:243-356` | Encode writes one segment per object, `system_graph.json`, then `index.json` |
| S3 | `CLI/args.rs:49`, `CLI/mod.rs:20`, `CLI/represent.rs:11-113` | `vindex3 represent` verb; default `RolePolicy` at line 16 |
| S4 | `CLI/args.rs:448-529` | Represent flags; `--encoding` default `NVFP4` at lines 458-461 |
| S5 | `CLI/args.rs:182-228`, `CLI/args.rs:110` | Exec flags; `ProductionQ8`; `--representation-source` |
| S6 | `CLI/prepare.rs:45-65`, `CLI/prepare.rs:71-81`, `CLI/prepare.rs:98-101` | Exec opens with `want = Q8_0` for `production-q8`; parses `stored` |
| S7 | `VX/shape.rs:60-70`, `VX/inspect.rs:130-135` | Graph shape versus legacy bank shape |
| S8 | `VX/index.rs:99-215` | `Vindex3Index` fields and serde skip rules |
| S9 | `VX/encode/segment.rs:189-194` | Digests written as `{:x}` lowercase hex |
| S10 | `VX/index.rs:87-95`, `VX/index.rs:179-180`, `VX/represent/pipeline.rs:443-455` | `authority` default `canonical`; set `derived` only under `--deployment` |
| S11 | `VX/represent/pipeline.rs:32-50`, `VX/represent/kquant.rs:108-122` | Target dispatch; compilable encodings |
| S12 | `VX/represent/report_types.rs:76-103`, `CLI/represent.rs:16-69` | `RepresentSpec`: roles, protections, deployment |
| S13 | `VX/represent/report_types.rs:118-127`, `VX/represent/pipeline.rs:478-483` | Map name `r0-uniform`; `precision_map` written to the index |
| S14 | `VX/represent/report_types.rs:220-249`, `VX/represent/nvfp4_pack.rs:398-418` | Encoder recipe by feature; `kquant-larql-native` and `kquant-ggml-reference` |
| S15 | `crates/larql-vindex/Cargo.toml:72-82`, `crates/larql-cli/Cargo.toml:23`, `crates/larql-cli/Cargo.toml:49-50` | `reference-encoder` off by default and not enabled by the CLI |
| S16 | `VX/encode/mod.rs:336-346`, `VX/encode/mod.rs:368-393` | Auxiliary reference table written only for FP8 scale siblings |
| S17 | `VX/index.rs:141-150`, `VX/opplan/exec/operands/open.rs:222-229` | Attestation table |
| S18 | `VX/encode/mod.rs:331-333`, `VX/encode/mod.rs:578` | `system_graph.json` written; index `system_graph` set |
| S19 | `VX/graph/mod.rs:103-116` | `SystemGraph` fields; `GRAPH_SCHEMA = 6` |
| S20 | `VX/represent/pipeline.rs:154-237` | Per-tensor plan: a compiled tensor's dtype becomes the encoding; a carried tensor keeps dtype, shape and bytes; names unchanged |
| S21 | `VX/represent/candidate_authority.rs:25-29`, `VX/represent/pipeline.rs:548-552` | `candidate.json` written |
| S22 | `VX/represent/compiler.rs:158-176`, `VX/represent/compiler.rs:470-479` | `CandidateIndex` fields; atomic write |
| S23 | `VX/encode/checkpoint.rs:37-43`, `VX/encode/checkpoint.rs:63-77`, `VX/artifact/ingest.rs:104-127` | Capability files copied at encode |
| S24 | `VX/represent/pipeline.rs:526-538` | Capability files and `moe_manifest.json` copied at represent |
| S25 | `VX/represent/pipeline.rs:427-442` | Canonical segments hard-linked or copied unchanged |
| S26 | `VX/encode/mod.rs:47-53`, `VX/encode/mod.rs:274-279` | `segments/`, `.bin`, `@`; canonical segment key and path |
| S27 | `VX/encode/mod.rs:329-349` | Graph, then index last |
| S28 | `VX/represent/pipeline.rs:540-544` | Index written last at represent |
| S29 | `VX/encode/segment.rs:3-14`, `VX/encode/segment.rs:166-170`, `VX/encode/segment.rs:245-263` | Framing `[u64 LE H][header][payload]`; reader computes `P = 8 + H` |
| S30 | `VX/encode/source/mod.rs:115-139` | Payload streamed verbatim from the safetensors shard |
| S31 | `crates/larql-vindex/src/format/checksums.rs:13-25` | `sha256_file` lowercase hex over the whole file |
| S32 | `VX/encode/segment.rs:133-158` | Header serialised compact; space padding to the 16-byte payload boundary, included in `H` |
| S33 | `VX/encode/segment.rs:27-49` | Writer alignment 16; execution minimum 4 |
| S34 | `VX/encode/segment.rs:245-263` | 256 MiB header bound; no `schema` check on read |
| S35 | `VX/encode/segment.rs:51-72` | `SegmentHeader` / `SegmentTensor` fields and order |
| S36 | `VX/encode/segment.rs:24-25`, `VX/encode/segment.rs:128-132` | `SEGMENT_HEADER_SCHEMA = 1` |
| S37 | `VX/inspect.rs:174-181` | `header.representation` must equal the directory id |
| S38 | `VX/encode/segment.rs:93-98`, `VX/encode/segment.rs:112` | Table sorted by relative name (`String::cmp`) |
| S39 | `VX/encode/segment.rs:113-127`, `VX/encode/segment.rs:174-187` | Offsets assigned contiguously; payloads written in table order |
| S40 | `VX/inspect.rs:152-207` | Directory and graph coherence; `tensor_count`; file length `P + payload_bytes` |
| S41 | `VX/index.rs:151-157` | The directory is the only route from representation to bytes |
| S42 | `crates/larql-vindex/src/format/generation.rs:1-13`, `crates/larql-vindex/src/format/generation.rs:67-86`, `crates/larql-vindex/src/format/generation.rs:107-111` | Version 4 current; 3..=4 read as VINDEX3 |
| S43 | `VX/artifact/resolve.rs:150-162` | Local artifact name = path stem |
| S44 | `VX/artifact/resolve.rs:236-250` | Remote artifact name = repo's last component |
| S45 | `VX/encode/mod.rs:562-574` | `family` = `model_type`; `model` = primary artifact name |
| S46 | `VX/index.rs:126-131`, `VX/encode/mod.rs:578` | `system_graph` filename |
| S47 | `VX/index.rs:241-242`, `VX/profile.rs:32`, `VX/profile.rs:49-55` | Profiles `[{"name":"exact"}]` |
| S48 | `VX/represent/pipeline.rs:258-262`, `VX/represent/pipeline.rs:472-474` | Pack segment key `segments/<object>@<enc>`, registered with value 1 |
| S49 | `VX/index.rs:204-214` | Unknown index fields preserved (`extra`) |
| S50 | `VX/encode/mod.rs:274-277`, `VX/represent/pipeline.rs:129` | Representation id `<object>@<encoding>` |
| S51 | `VX/index.rs:20-73` | `RepresentationEntry` fields |
| S52 | `VX/represent/pipeline.rs:388-409` | Pack entry: `compiled_from`, `source_representation_digest` |
| S53 | `VX/represent/pipeline.rs:401-405`, `VX/represent/kquant.rs:358-368` | Pack `codec` = `KQuant::codec_identity()` |
| S54 | `VX/index.rs:64-72`, `VX/represent/nvfp4_pack.rs:325-360` | Encoder recipe is not a refusal |
| S55 | `VX/encode/mod.rs:317-325` | Canonical entries carry no provenance or codec fields |
| S56 | `VX/represent/map.rs:102-135`, `VX/represent/map.rs:141-144` | `PrecisionMap` fields; unnamed roles stay source |
| S57 | `VX/inspect.rs:85-102`, `VX/inspect.rs:136-144` | Graph schema checked equal to 6 before parse |
| S58 | `VX/graph/surface.rs:320-348` | `HeadSurface` incl. `head_reuses_embedding` |
| S59 | `VX/graph/object.rs:93-124` | `LogicalObject`, `SourceBinding`, `Representation` |
| S60 | `VX/graph/object.rs:71-84` | Object kind names |
| S61 | `VX/encode/mod.rs:267-273`, `VX/opplan/exec/operands/open.rs:114-116` | Element 0 is the canonical representation |
| S62 | `VX/represent/pipeline.rs:485-520` | Graph gains a `Q8_0` `approximate` representation |
| S63 | `VX/opplan/exec/operands/open.rs:113-170` | Selection: pack if `<object>@<want>` exists, else canonical |
| S64 | `VX/opplan/exec/operands/open.rs:149-157` | Pack codec admitted at open |
| S65 | `crates/larql-models/src/inventory/tensors.rs:119-146` | `dtype`, `shape`, byte length taken verbatim from the safetensors header |
| S66 | `VX/represent/kquant.rs:66-72` | Q8_0: 32 elements, 34 bytes |
| S67 | `VX/represent/kquant.rs:371-377` | `KQUANT_REVISION = 1` |
| S68 | `VX/represent/codec/registry.rs:123-146` | Admission requires exact identity equality |
| S69 | `VX/represent/kquant.rs:134-186` | Row length (last dimension) must be a multiple of the block size; length = elements/32 × 34 |
| S70 | `VX/represent/codec/geometry.rs:22-36`, `VX/represent/codec/codecs/kquant.rs:61-63`, `VX/represent/codec/codecs/kquant.rs:128-134` | Rows = product of leading dimensions; k = last dimension; row stride `k/32·34`; row r at `r·row_bytes` |
| S71 | `VX/represent/kquant.rs:246-260`, `VX/represent/compile.rs:80-103` | Row bytes and "rows would share a scale" rule |
| S72 | `VX/graph/build.rs:116-155`, `VX/graph/build/components.rs:125-160` | Group classification: `embed_tokens`→embedding, `lm_head`→head, `norm`→final norm, `layers`→stack |
| S73 | `VX/encode/mod.rs:472-522` | Relative name = source name minus the common prefix, minus a leading `.` |
| S74 | `VX/graph/object.rs:107-116` | `SourceBinding.tensor_prefix` |
| S75 | `VX/encode/mod.rs:524-541` | Common dot-segment prefix |
| S76 | `VX/graph/object.rs:136-145` | `covers` at a segment boundary |
| S77 | `VX/graph/object.rs:148-171` | Longest covering prefix owns the tensor |
| S78 | `VX/encode/mod.rs:506-512` | Planned dtype, shape and len from the inventory |
| S79 | `VX/represent/pipeline.rs:287-308`, `VX/opplan/exec/operands.rs:319-330` | Pack source values loaded from the `@BF16` bytes (BF16 widening) |
| S80 | `VX/represent/policy.rs:204-276` | Name-based classifier |
| S81 | `VX/represent/report_types.rs:333-345` | Plan role first, classifier fallback |
| S82 | `VX/represent/plan_roles.rs:54-98` | Plan binds softmax q/k/v/o and dense gate/up/down as `decoder-linear` |
| S83 | `VX/represent/policy.rs:121-168` | Role names; default-policy roles |
| S84 | `VX/represent/policy.rs:278-314` | `RolePolicy::default` |
| S85 | `VX/represent/pipeline.rs:165-180` | Eligible tensor still needs `KQuant::plan` to succeed |
| S86 | `VX/represent/pipeline.rs:239-256` | Objects with no compiled tensor get no pack |
| S87 | `crates/larql-models/src/config/architecture/tensor_keys.rs:36-55` | `output_head_reuses_embedding` rule |
| S88 | `VX/graph/surface.rs:341-347` | The flag concerns a missing head object |
| S89 | `VX/opplan/build.rs:682-712` | Head operand = `OutputHead` object if present, else the embedding when tied |
| S90 | `VX/opplan/exec/realization/selection.rs:29-42` | Embed operation: `DecodedGather` |
| S91 | `VX/opplan/exec/production/plan_backend.rs:35-46`, `VX/opplan/exec/production/select.rs:291-406`, `VX/opplan/exec/realization/selection.rs:201-211` | Production selection; `OutputHead` class; size policy; `Requantise` form |
| S92 | `VX/opplan/exec/cpu/physical/projection.rs:186-244`, `VX/opplan/exec/cpu/physical/projection.rs:428-433`, `VX/opplan/exec/cpu/physical/projection.rs:541-549`, `VX/opplan/exec/cpu/physical.rs:34` | `choose_for`: FusedQ8 for streaming BF16; `LARQL_CPU_MAX_FORMAT`; L2 threshold |
| S93 | `VX/opplan/exec/cpu/physical.rs:144-264`, `VX/opplan/exec/realization/refusal.rs:378-402`, `VX/opplan/exec/production/select.rs:257-265`, `VX/represent/codec/codecs/float.rs:191-198` | Arithmetic arm default; requantise candidates offered for BF16 sources |
| S94 | `VX/opplan/exec/cpu/physical/projection.rs:21-25`, `VX/opplan/exec/weights/load.rs:69-90` | FusedQ8 → `WeightFormat::Q8` → `quantise_q8` |
| S95 | `VX/opplan/exec/quantise.rs:21`, `VX/opplan/exec/quantise.rs:65-108` | LARQL-internal Q8, 64-element blocks |
| S96 | `VX/opplan/exec/operands/open.rs:462-480`, `VX/opplan/exec/weights/load.rs:127-160` | `stored` guard called only on the MXFP4/NVFP4 paths |
| S97 | `CLI/exec.rs:161-211` | `runtime compile:` count and `projection plans:` line |
| S98 | `VX/encode/segment.rs:165-194` | Payload hash over the payload; file hash over prefix + header + payload |
| S99 | `VX/encode/mod.rs:288-316` | Canonical hashes computed while streaming from the source |
| S100 | `VX/inspect.rs:197-199`, `VX/inspect.rs:256-270` | `--verify` re-hashes `segment_sha256` only |
| S101 | `VX/verify_system/payload.rs:16-19` | Hashes cannot see a relabel |
| S102 | `VX/represent/compile.rs:286-298` | `OperandSeal` fields |
| S103 | `VX/represent/candidate_authority/producer.rs:104-146` | Seals: source and target range digests; absolute `target_offset` |
| S104 | `VX/represent/compile.rs:306-336` | Ledger key `object\u{1}tensor` |
| S105 | `VX/represent/candidate_authority/producer.rs:80-88` | `locator_hint` = source path |
| S106 | `crates/larql-vindex/src/format/generation.rs:271-287` | Missing `version` refused |
| S106b | `VX/represent/pipeline.rs:195-205`, `VX/represent/state/resolved.rs:53-64` | Per-tensor decision `Compiled`/`Source`/`LayoutRefused` recorded in the candidate |
| S107 | `crates/larql-vindex/src/format/generation.rs:222-238`, `VX/inspect.rs:115-123` | Unknown versions refused; VINDEX2 refused by the graph path |
| S108 | `crates/larql-vindex/src/format/generation.rs:3-5`, `crates/larql-vindex/src/format/generation.rs:224-227` | `version` is the sole discriminator |
