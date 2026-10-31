# LARQL VINDEX3 Container: Byte-Level Specification (Q8_0 Qwen3-0.6B profile)

| Field | Value |
|---|---|
| Document | LARQL-VERIFY-001 workstream B3, container specification |
| Status | DRAFT. Not admitted. A third party must check it against emitted files before it is trusted |
| Revision | 4 (see Revision history). Revision 3 (SHA-256 `6350e07cff89fb04321ec49ea2e82b14d3893dc7a279d4fd2c899c8db1860a22`) was admitted. Revision 3 added §17, the computation-relevant fields of the `system_graph.json` execution surface, for decision revision D2 of the protocol. This revision adds one normative statement to §17.5, the RoPE rotation formula, and corrects one informative citation (§17.8 N2, S155). It changes no other normative statement |
| Upstream configuration (§17 only) | `~/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca/config.json`, SHA-256 `660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd`. It is not in the container (§2) |
| Observed container | `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`, encoded at LARQL `2536bb79` from the local HF snapshot path with a default build (no `reference-encoder` feature). `index.json` SHA-256 `7f3ba8e5da50276e501e7694c46c0a3c9c9d7530596656376cc9597f05fec490`; `system_graph.json` `05fcec4c45167c2f8f424c35b8c39acb06cc92716f11e0ffbec341e110d66f57`; `segments/target.decoder_stack@Q8_0.bin` `f7f68e997657e9f28394af937a10adbdceee7ccd4fc56839ad49f1190eb6573e` |
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
- This document describes only container framing. It does not describe Q8_0 arithmetic, how any value decodes to a float, numerical tolerances, or reference execution semantics. Those belong to ggml (`block_q8_0`) and gguf-py. Where the container stores a field with a numerical meaning, this document gives its name and byte position only. **Exception (revision 3):** §17 gives the meanings of the execution-surface fields of `system_graph.json`, for comparing a declared configuration only (see the next bullet).
- **Revision 3 addition.** §17 is the one place this document says what execution-surface values mean. It says so only as far as is needed to compare the configuration the container declares against an upstream `config.json`: which operation each field parameterises, and in what unit or encoding. It still describes no kernel, accumulation order, precision or tolerance. Its subsection §17.8 is informative only.
- Where a statement was confirmed by inspecting the existing container `/Users/christopherhay/chris-models/qwen3-0.6b.vindex3`, it is marked **(illustration)**. That container has no recorded upstream revision, predates this commit, and holds BF16 only. It is not evidence for the Q8_0 container.
- Where a value was observed in the fresh Q8_0 container `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3` (see the header table), it is marked **(observed)**. Every value revision 1 marked **(computed)** was confirmed by observation there, and is now marked **(observed)**.
- **(observed in code)** (revision 4) marks a statement of what LARQL's executor does that was established by reading the cited source at the commit above, not by observing a container or a run.

## 1. Pipeline and the variant it selects

### 1.1 Steps

1. **Encode.** `larql vindex3 encode <ARTIFACT> --output <SRC>` reads the HF checkpoint and writes a canonical BF16 container at `<SRC>` [S1][S2]. For the observed container, `<ARTIFACT>` was the local HF snapshot directory, so the recorded artifact name is its stem `c1899de289a04d12100db370d81485cdf75e47ca` (§16, U1 closed). The form of `<ARTIFACT>` (a local directory or `hf://Qwen/Qwen3-0.6B@<rev>`) changes only identity strings (§5.2 `model`, §6 `artifact`) and never tensor bytes, shapes, names or order.
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
| Encoder recipe | `kquant-larql-native` (default build) or `kquant-ggml-reference` (build with the `larql-vindex/reference-encoder` feature) [S14][S15] | Default build: `kquant-larql-native`. **(observed)** The fresh container records `{"algorithm":"kquant-larql-native","revision":1}` with no `source` (§16, U3 closed). The recipe never changes the byte layout, only which valid values are chosen |
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
- **JSON.** `index.json`, `system_graph.json` and `candidate.json` are pretty-printed JSON. Segment headers are compact JSON followed by space padding (§4). A reader MUST parse them as JSON and MUST NOT depend on key order, whitespace or indentation. Unknown keys MUST be ignored unless this document says otherwise (§14). (Revision 3: for a configuration comparator, §17.1 says otherwise.)
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
- Individual tensor offsets have **no** alignment guarantee beyond what the lengths imply. A Q8_0 tensor's offset may be any even number. **(observed)** In this container every tensor offset is a multiple of 16, because every tensor length here is. That is incidental, not a guarantee: a reader MUST NOT assume more than 2-byte alignment of a tensor offset.
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
| `model` | string | MUST | The artifact name the encoder recorded. It depends on how encode was invoked (§16): the checkpoint path's file stem for a local path, or the repo's last path component for `hf://` [S43][S44]. **(observed)** `"c1899de289a04d12100db370d81485cdf75e47ca"`. A reader MUST NOT depend on it |
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

Component fields used by this document: `id`, `role`, `num_layers` (28), `hidden_size` (1024), and `execution.head` (HeadSurface: `vocab_size` 151936 and `head_reuses_embedding` true) [S58] **(illustration)**. A reader MAY ignore the rest of the component, which describes execution semantics. (Revision 3: a program that compares the container's declared model configuration with an upstream configuration reads the fields specified in §17.)

LogicalObject [S59]:

| Key | JSON type | Meaning |
|---|---|---|
| `id` | string | `"<component>.<kind>"`, e.g. `"target.decoder_stack"` |
| `component` | string | `"target"` |
| `kind` | string | One of `"decoder_stack"`, `"embedding"`, `"final_norm"`, `"output_head"` in this profile [S60] |
| `source_bindings` | array of `{ "artifact": string, "tensor_prefix": string, "tensors": integer, "bytes": integer }` | Where the object's tensors came from in the source checkpoint. Exactly one binding per object in this profile. `artifact`: the artifact name (here `"c1899de289a04d12100db370d81485cdf75e47ca"`, **(observed)**). `tensor_prefix`: the HF key prefix (§10). `tensors`: the number of source tensors under the prefix. `bytes`: the total byte size of those source tensors' payloads [S109]. A reader MAY cross-check `tensors` against the canonical representation's `tensor_count` and `bytes` against its `payload_bytes`. **(observed)** 308/880,932,864, 1/311,164,928, 1/2,048, 1/311,164,928 for decoder_stack, embedding, final_norm, output_head |
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
- **(observed)** A 2-D weight `[R, K]` stores row `r` at payload-relative bytes `[2·K·r, 2·K·(r+1))`. This follows from the safetensors convention, and the third-party check confirmed it on the fresh container (`evidence/B3/CHECK.md`, check 6 and finding E1).

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
- **Block contents:** Q8_0 block, 34 bytes, layout per ggml `block_q8_0`. The normative reference is ggml at commit `facdc44a67da17df4433adcc468b424f48e9ded2`, `src/ggml-common.h` lines 251-256: an f16 `d` (`ggml_half`) at block bytes 0-1, then `int8_t qs[32]` at block bytes 2-33. A copy is at `transformer-verifiers/inputs/ggml-facdc44a67da17df4433adcc468b424f48e9ded2/src/ggml-common.h`. This document does not describe how the block decodes.

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

### 9.2 `index.json.representations` (observed)

| Id | `segment` | `tensor_count` | `payload_bytes` |
|---|---|---|---|
| `target.decoder_stack@BF16` | `segments/target.decoder_stack.bin` | 308 | 880,932,864 **(observed)** |
| `target.decoder_stack@Q8_0` | `segments/target.decoder_stack@Q8_0.bin` | 308 | 468,056,064 **(observed)** |
| `target.embedding@BF16` | `segments/target.embedding.bin` | 1 | 311,164,928 **(observed)** |
| `target.final_norm@BF16` | `segments/target.final_norm.bin` | 1 | 2,048 **(observed)** |
| `target.output_head@BF16` | `segments/target.output_head.bin` | 1 | 311,164,928 **(observed)** |

**(observed)** Digests recorded in the fresh container's `index.json`:

| Id | `payload_sha256` | `segment_sha256` |
|---|---|---|
| `target.decoder_stack@BF16` | `4e76d1f1e8411d334b3db85d5b7c2b69dc7321d5d5e605140c2945c2b921ce9e` | `5956d8c415f1e00cfce17aac493d03c60f0a2b1f0847b21991501d7b2a1116de` |
| `target.decoder_stack@Q8_0` | `89b08854a357a607578122307b0f70b315cd11d1308fb28184363b19a8835074` | `f7f68e997657e9f28394af937a10adbdceee7ccd4fc56839ad49f1190eb6573e` |
| `target.embedding@BF16` | `8f29acf519434862d95613b2b4f6b9d14933a5e4d16baebf8ac0b33b410acfb6` | `89cf6366b1fd0564a29a3f120c6157436006222ef146d9dd40444e98fc86b433` |
| `target.final_norm@BF16` | `40983d5d6018627e0ea73b2f7650e67c42ab160ceb82404016799eaffdf9d078` | `8b48cd41cbe21f715108778c63d38052df5640cb2409289e639d69052acdb798` |
| `target.output_head@BF16` | `8f29acf519434862d95613b2b4f6b9d14933a5e4d16baebf8ac0b33b410acfb6` | `fc82adeef3fa167956cfa4db7f69ed31fe6beac8dc50668bea6495be3afd2145` |

### 9.3 Single-tensor segments

| Segment | Table entry |
|---|---|
| `target.embedding@BF16` | `{"name":"weight","dtype":"BF16","shape":[151936,1024],"offset":0,"len":311164928}` |
| `target.output_head@BF16` | `{"name":"weight","dtype":"BF16","shape":[151936,1024],"offset":0,"len":311164928}` |
| `target.final_norm@BF16` | `{"name":"weight","dtype":"BF16","shape":[1024],"offset":0,"len":2048}` |

**(illustration)** These do not change under `represent`.

### 9.4 Decoder-stack tensors

Each layer `L` in 0..27 has 11 tensors. The table below is for the `@Q8_0` pack **(observed)**. In the `@BF16` segment every tensor is `BF16`, with `len = 2 × elements`.

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

A layer group in `@Q8_0` is 16,716,288 bytes. Layer groups appear in the byte-sorted order of §4.3. **(observed)** The header JSON is 31,408 bytes plus 8 bytes of padding, so `H = 31,416`, `P = 31,424`, and the file is 468,087,488 bytes.

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

**(b) Physical storage. Two copies.** `segments/target.embedding.bin` and `segments/target.output_head.bin` each hold a full 311,164,928-byte BF16 matrix **(illustration: both present, same `payload_sha256`, different `segment_sha256` because the header `representation` strings differ, and so, by §4.1, does the padding length (5 versus 3 spaces, **(observed)**). The parsed headers are otherwise equal)**. Nothing in the format stores a single shared copy for this subject.

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
| U1. **CLOSED (revision 2).** Exact `vindex3 encode` invocation | Observed: encode was given the local HF snapshot directory, so `index.json.model`, `components[].source_artifact` and `source_bindings[].artifact` are `"c1899de289a04d12100db370d81485cdf75e47ca"` [S43] |
| U2. **CLOSED (revision 2).** Digests and header lengths of the fresh Q8_0 container | Observed in the fresh container: every value revision 1 computed (H = 31,416, P = 31,424, payload 468,056,064, file 468,087,488, the §9.4 table) holds. Digests are in §9.2 |
| U3. **CLOSED (revision 2).** Build features (`reference-encoder`) | Observed: `encoder` is `{"algorithm":"kquant-larql-native","revision":1}` with no `source`, i.e. the default build [S15] |
| U4. The realised LM-head kernel on the L1 host | Depends on the host's L2 size and on `LARQL_CPU_MAX_FORMAT`/`LARQL_CPU_ARITHMETIC` [S92][S93]. Determined by code reading only. Not run |
| U5. **PARTLY CLOSED (revision 3).** Full schema of `candidate.json` and of the `system_graph.json` component execution surface | Revision 3 specifies every execution-surface field that affects computation for this subject, and the keys that must be absent (§17). Still out of scope: `candidate.json`, and the parts of the surface this profile does not use (the recurrent, MLA, Mamba2, conv-QKV, mixture-of-experts and hyper-connection groups), beyond the requirement that they are absent (§17.7) |
| U6. Byte-exact `index.json` and `system_graph.json` text | Pretty-printed by `serde_json`. Readers must not depend on it |

## 17. Execution surface: computation-relevant fields (revision 3)

### 17.1 Purpose, scope and terms

This section specifies, for this profile, every field of `system_graph.json` that changes what a forward pass of the subject computes. It exists so that a program (the "comparator") can compare, field by field, the configuration the container declares against the pinned upstream `config.json` (header table), as decision revision D2 of LARQL-VERIFY-001 requires. §17.2 to §17.7 are normative. §17.8 is informative.

Terms:

- `G` is the parsed `system_graph.json`, found through `index.json.system_graph` (§5.2, §6).
- `C` is the element of `G.components` whose `id` is `"target"`. This profile has exactly one component (§6). A comparator MUST reject a graph with no such element, or with more than one component.
- `C.attention[L]` is element `L` of the array `C.attention`, for `L` in `0 .. C.num_layers - 1`.
- `X` is shorthand for `C.execution`, the component's execution surface [S110][S111].
- Paths are written as dotted JSON member names from `C` or `X`. "All `L`" means the statement holds for every element of `C.attention`.

**Where the values come from.** The writer resolves every value in this section once, at encode time, from the checkpoint's `config.json` and tensor names, and persists the resolved value. `config.json` itself is not in the container (§2) [S123][S127][S128]. A surface value is therefore LARQL's *resolution* of the upstream configuration, not a copy of it. Where the resolution changes a value's encoding (§17.3, `eps`) or folds several upstream keys into one value (§17.5), this section says so.

**Number encoding.** Integer-valued fields are JSON integers. Fields typed "binary64" are written by `serde_json` from an IEEE-754 binary64 value in shortest round-trip decimal form, sometimes with a trailing `.0`. A comparator MUST parse them as binary64. Fields typed "binary32" hold an IEEE-754 binary32 value, written in shortest round-trip form for binary32. A comparator MUST parse a binary32 field and round it to binary32 before comparing it.

**Unknown keys.** §3 lets a tensor reader ignore unknown keys. That rule does not extend to the comparison. A key under `X`, or under any `C.attention[L]`, that this section does not list can change the computation, so a comparator MUST NOT silently ignore it. The same holds for a key directly on `C` other than `id`, `role`, `source_artifact`, `num_layers`, `hidden_size`, `attention` and `execution`. A comparator MUST report each such key as an unresolved comparability assumption, in the sense of D2. In particular, `C.perception`, an optional field of the component schema [S110], MUST be absent in this profile, and a comparator MUST report its presence as a configuration mismatch.

**Absence.** In the tables, "Required" means the writer always emits the key, and LARQL fails to parse the graph without it. "Optional" means an absent key deserialises to the stated default, or, for a value with no default, to "absent". "Absent" has its own meaning per field, given in the table. It is never a licence to substitute a value from elsewhere.

### 17.2 Topology and shapes

| JSON path | JSON type | Unit / encoding | When absent | Meaning | **(observed)** | Upstream key | Sources |
|---|---|---|---|---|---|---|---|
| `C.num_layers` | integer | count of decoder layers | Required | Number of decoder layers in the component. `C.attention` has exactly this many elements. The `@BF16` and `@Q8_0` decoder segments hold layer indices `0 .. C.num_layers - 1` (§9.4) | `28` | `num_hidden_layers` | [S110][S127] |
| `C.hidden_size` | integer | elements | Required | Width of the residual-stream vector: the last dimension of the embedding and output-head matrices, the length of every decoder and final norm vector, and the input width of every Q/K/V/gate/up projection | `1024` | `hidden_size` | [S110][S127][S141] |
| `C.attention` | array of AttentionLayerPolicy (§17.5) | one element per layer, in layer order | Optional in the schema. LARQL refuses to plan a component whose array is absent or whose length differs from `C.num_layers` | Per-layer attention policy | 28 elements | see §17.5 | [S110][S116][S137] |
| `X` | object (ExecutionSurface) | — | Optional in the schema. LARQL refuses to plan a component without it | The execution surface | present | — | [S110][S111][S137] |
| `X.attention.num_q_heads` | integer | count of heads | Required within `X.attention` | Number of query heads. The query projection has `num_q_heads × head_dim` output rows (here `q_proj` is `[2048, 1024]`, §9.4) | `16` | `num_attention_heads` | [S112][S127][S141] |
| `X.attention.num_kv_heads` | integer | count of heads | Required within `X.attention` | Number of key/value heads (grouped-query attention). Query head `h` reads key/value head `h ÷ (num_q_heads ÷ num_kv_heads)`, integer division | `8` | `num_key_value_heads` | [S112][S127][S149] |
| `X.attention.head_dim` | integer | elements per head | Required within `X.attention` | Width of one attention head. Fixes the RoPE dimension, the QK-norm vector length under `per_head` scope, and (with the head counts) the Q/K/V/O shapes | `128` | `head_dim` | [S112][S127][S141] |
| `C.attention[L].geometry.head_dim` | integer | elements per head | Optional. Absent means layer `L` uses `X.attention.head_dim`. The writer always emits it | Layer `L`'s head width. Where present it is the authority for layer `L` | `128` for all `L` | `head_dim` | [S116][S126][S139] |
| `C.attention[L].geometry.num_kv_heads` | integer | count of heads | As above, defaulting to `X.attention.num_kv_heads` | Layer `L`'s key/value head count. Where present it is the authority for layer `L` | `8` for all `L` | `num_key_value_heads` | [S116][S126][S139] |
| `X.ffn.intermediate_size` | integer | elements | Optional in the schema (absent only on a wholly routed stack). In this profile it MUST be present. LARQL refuses to plan a dense FFN without it | Width of the dense FFN: the output rows of `gate_proj` and `up_proj`, the input columns of `down_proj` | `3072` | `intermediate_size` | [S113][S123][S138] |
| `X.ffn.intermediate_size_by_layer` | array of integer | elements, one per layer | Optional. Absent means every layer uses `X.ffn.intermediate_size`. MUST be absent in this profile | Per-layer dense FFN width | absent | no upstream counterpart | [S113][S139] |
| `X.head.vocab_size` | integer | rows | Required within `X.head` | Number of vocabulary rows in the embedding table and the output head. The writer would round it up to a declared padding multiple, which this subject does not declare | `151936` | `vocab_size` | [S58][S125][S140] |
| `X.context_length` | integer | positions | Optional. Absent means "not declared" | The declared extent of the programme. It does not change what is computed at any position below it | `40960` | `max_position_embeddings` (not a D2 field) | [S111][S123] |

The same facts appear elsewhere, and a comparator SHOULD check that they agree:

- `index.json.hidden_size` and `index.json.num_layers` (§5.2) equal `C.hidden_size` and `C.num_layers`.
- The tensor shapes (§9.3, §9.4): embedding and output head `[vocab_size, hidden_size]`; `q_proj` `[num_q_heads·head_dim, hidden_size]`; `k_proj` and `v_proj` `[num_kv_heads·head_dim, hidden_size]`; `o_proj` `[hidden_size, num_q_heads·head_dim]`; `q_norm` and `k_norm` `[head_dim]`; `gate_proj` and `up_proj` `[intermediate_size, hidden_size]`; `down_proj` `[hidden_size, intermediate_size]`; every other norm `[hidden_size]`. LARQL's planner refuses a container whose shapes disagree with these [S141][S140].

### 17.3 Normalisation

A NormSpec is the object `{ "kind": string, "eps": number, "weight_offset": number }`, all three required [S119]. The operation it denotes, for a vector `x` of length `n` and a stored weight vector `w`, is RMSNorm when `kind` is `"rms_norm"`: `y_j = x_j / sqrt(mean_j(x_j²) + eps) × (weight_offset + w_j)`. This document does not state the precision or order of that arithmetic.

| JSON path | JSON type | Unit / encoding | When absent | Meaning | **(observed)** | Upstream key | Sources |
|---|---|---|---|---|---|---|---|
| `X.norm.pre` | NormSpec | — | Required | The norm at the pre-attention site (`input_layernorm`) and, under `pre_only` placement, the pre-FFN site (`post_attention_layernorm`) | see the next three rows | — | [S114][S131] |
| `X.norm.pre.kind` | string: `"rms_norm"` or `"layer_norm"` | enumeration | Required | Norm family | `"rms_norm"` | no upstream counterpart | [S119][S131] |
| `X.norm.pre.eps` | number (binary64) | additive epsilon inside the square root | Required | Epsilon of the pre sites. **Encoding:** the writer reads `rms_norm_eps` as binary64, rounds it to binary32, and widens it back to binary64. So the stored value is `f64(f32(rms_norm_eps))`, never `rms_norm_eps` itself unless the latter is exactly representable in binary32 | `9.999999974752427e-7` | `rms_norm_eps` | [S119][S128][S131] |
| `X.norm.pre.weight_offset` | number (binary32) | added to each stored weight | Required | `0.0` means the stored weight is the multiplier itself | `0.0` | no upstream counterpart | [S119][S135] |
| `X.norm.final_norm` | NormSpec | — | Required | The final norm before the output head (`model.norm`). Encoded as `X.norm.pre` | `{"kind":"rms_norm","eps":9.999999974752427e-7,"weight_offset":0.0}` | `rms_norm_eps` (for `eps`) | [S114][S131] |
| `X.norm.post` | NormSpec | — | Optional. Absent means "unjudged". MUST be absent in this profile | Post-sublayer norms of a four-norm or post-norm stack | absent | no upstream counterpart | [S114][S137] |
| `X.norm.placement` | string: `"pre_only"`, `"pre_post"`, `"post_only"`, `"pre_mixer"` | enumeration | Optional in the schema. LARQL refuses to plan without it | Where the norms sit. `"pre_only"`: each layer computes `h ← h + Attn(N₁(h))`, then `h ← h + FFN(N₂(h))`, where `N₁` uses `input_layernorm.weight` and `N₂` uses `post_attention_layernorm.weight`, both with `X.norm.pre`. The writer decides it from the stack's norm tensor names, not from the family | `"pre_only"` | no upstream counterpart | [S117][S124][S142] |

**QK-norm epsilon.** The container stores no separate epsilon for the Q/K norms. In LARQL's model of the surface, the Q/K norms run at `X.norm.pre.eps` [S143]. A comparator MUST treat `X.norm.pre.eps` as the container's declaration of the QK-norm epsilon too.

### 17.4 Attention

| JSON path | JSON type | Unit / encoding | When absent | Meaning | **(observed)** | Upstream key | Sources |
|---|---|---|---|---|---|---|---|
| `X.attention` | object (AttentionSurface) | — | Optional in the schema; present iff some layer attends. MUST be present in this profile | What the attention operation reads | present | — | [S111][S112] |
| `X.attention.score_scale` | number (binary64) | dimensionless multiplier | Required within `X.attention` | Multiplier applied to each query·key dot product before the softmax. **Derivation:** when `config.json` declares neither `attention_multiplier` nor `query_pre_attn_scalar`, the writer stores `head_dim` raised to the power `-0.5`, computed in binary64 by `powf`. For `head_dim = 128` that is `0.08838834764831845`, one unit in the last place above `1 / sqrt(128)` computed by square root and division (`0.08838834764831843`). Both round to the same binary32 value, `0.0883883461356163` | `0.08838834764831845` | no upstream counterpart (derived from `head_dim`) | [S112][S130] |
| `X.attention.query_scale` | number (binary64) | multiplier on the query before RoPE | Optional. Absent means the operation does not exist, which differs from `1.0`. MUST be absent in this profile | Query pre-scale | absent | no upstream counterpart | [S112] |
| `X.attention.logit_softcapping` | number (binary32) | cap | Optional; absent means no softcap. MUST be absent in this profile | Attention-logit softcap | absent | no upstream counterpart | [S112] |
| `X.attention.attention_bias` | boolean | — | Optional. Absent means "undeclared", which is not "false" | Whether the Q, K, V and O projections each add a bias vector. Copied from `attention_bias` when the config declares it | `false` | `attention_bias` | [S112][S128][S130] |
| `X.attention.qkv_bias` | boolean | — | Optional. MUST be absent in this profile | Q/K/V biases without an output bias (Qwen2 form) | absent | no upstream counterpart in this config | [S112] |
| `X.attention.qk_norm_scope` | string: `"per_head"` or `"full_projection"` | enumeration | Required within `X.attention` | Read only when the stack holds `q_norm`/`k_norm` tensors. `"per_head"`: the RMS statistic is taken over each head's `head_dim` slice separately, and the one `[head_dim]` weight vector applies to every head. Applied to Q and K after projection and before RoPE | `"per_head"` | no upstream counterpart | [S112][S119][S142] |
| `X.attention.qk_norm_weight_offset` | number (binary32) | added to each stored QK-norm weight | Required within `X.attention` | As `weight_offset` in §17.3, for the Q/K norms | `0.0` | no upstream counterpart | [S112][S135] |
| `X.attention.parameter_free_qk_norm` | object `{ "q": boolean, "k": boolean, "v"?: boolean }` | flags | Optional. Absent means all `false`; an absent `v` means `false` | Whether Q, K or V is also RMS-normalised with no weight | `{"q":false,"k":false,"v":false}` | no upstream counterpart | [S112][S119] |
| `X.attention.output_gate`, `X.attention.sinks` | object | — | Optional. Absent means "no judgment". MUST be absent in this profile | Attention output gate; attention sinks | absent | no upstream counterpart | [S112] |

**Whether QK norms run** is not a flag. They run exactly when the decoder stack holds the `L.self_attn.q_norm.weight` and `L.self_attn.k_norm.weight` tensors. In this container all 28 layers hold both (§9.4) [S142].

### 17.5 Per-layer attention policy: positions and windows

AttentionLayerPolicy is the element type of `C.attention` [S116]:

| JSON path | JSON type | Unit / encoding | When absent | Meaning | **(observed)** | Upstream key | Sources |
|---|---|---|---|---|---|---|---|
| `C.attention[L].operator` | string: `"softmax"`, `"gated_delta"`, `"kda"`, `"mamba2"`, `"recurrent"`, `"mla"`, `"conv_qkv_attention"` | enumeration | Required | Which attention-class operator layer `L` runs. MUST be `"softmax"` for all `L` in this profile | `"softmax"` for all `L` | no upstream counterpart | [S116][S126] |
| `C.attention[L].span` | string: `"full"`, `"sliding"`, `"windowed"` | enumeration | Optional; absent only on a recurrence layer. LARQL refuses a softmax layer with no span | How far back layer `L` attends. `"full"`: query position `p` attends to every key position `0 .. p` (causal). `"sliding"` with `window = w`: to positions `max(0, p+1-w) .. p` | `"full"` for all `L` | derived from `sliding_window`, `use_sliding_window`, `max_window_layers` (and `layer_types` when declared); see below | [S116][S126][S130][S150] |
| `C.attention[L].window` | integer | positions | Optional. Absent on `"full"` and `"windowed"` layers | The sliding window size of a `"sliding"` layer | absent for all `L` | `sliding_window` | [S116][S126][S130] |
| `C.attention[L].position` | object, internally tagged by `"kind"` | see below | Required | How layer `L` encodes position | `{"kind":"rope","theta":1000000.0}` for all `L` | `rope_theta`, `rope_scaling` | [S116][S118][S132] |
| `C.attention[L].position.kind` | string | enumeration: `"rope"`, `"linear"`, `"llama3"`, `"yarn"`, `"partial_rope"`, `"m_rope"`, `"relative"`, `"none"` | Required | `"rope"` means unscaled rotary position embedding over the whole head. Pairing is split-half: dimension `i` rotates with dimension `i + head_dim/2`, for `i < head_dim/2`. The angle for pair `i` at position `p` is `p × theta^(-2i/head_dim)`. Every other kind carries a scaling or a different operator, and MUST NOT appear in this profile | `"rope"` for all `L` | `rope_scaling` (see below) | [S118][S132][S129] |
| `C.attention[L].position.theta` | number (binary64) | RoPE base frequency | Required when `kind` is `"rope"` | The base `theta` above | `1000000.0` for all `L` | `rope_theta` | [S118][S128] |
| `C.attention[L].geometry` | object `{ "head_dim": integer, "num_kv_heads": integer }` | — | See §17.2 | Layer `L`'s head geometry | `{"head_dim":128,"num_kv_heads":8}` for all `L` | `head_dim`, `num_key_value_heads` | [S116] |
| `C.attention[L].v_from_k` | boolean | — | Optional. Absent means `false`. MUST be absent or `false` in this profile | V is the raw K projection (no V operand) | absent | no upstream counterpart | [S116] |
| `C.attention[L].declared_span` | string | the checkpoint's `layer_types[L]`, verbatim | Optional. Absent when the config declares no `layer_types` | Recorded for comparison only. It does not decide `span` | absent for all `L` | `layer_types` (not declared by this config) | [S116][S126] |

**How the writer resolves `span` and `window`** for a softmax layer of this family, in this order [S130][S126][S127]:

1. If `use_sliding_window` is declared `false`, or `sliding_window` is absent or `null`, the layer is not sliding.
2. Otherwise, if `max_window_layers` is declared and `L ≥ max_window_layers`, the layer is not sliding.
3. Otherwise the layer is sliding only if the config's `layer_types[L]` says so; with no `layer_types`, it is not sliding.
4. A sliding layer gets `span: "sliding"` and `window: sliding_window`. A non-sliding layer gets `span: "full"` and no `window`.

**How the writer resolves `position`** for this family [S132][S129][S128]: `theta` is `rope_theta` (the writer would also accept `rope_parameters.rope_theta`, which this config does not have). A `rope_scaling` of `null`, or one with no `type`/`rope_type`, resolves to no scaling, giving `kind: "rope"`. A `yarn`, `llama3` or `linear` scaling gives `kind` `"yarn"`, `"llama3"` or `"linear"`. A declared `partial_rotary_factor` below 1 gives `"partial_rope"` or `"m_rope"`.

**The rotation for `kind: "rope"` (revision 4)** **(observed in code)** [S148][S156]. Let `d = head_dim` of layer `L` and `θ = C.attention[L].position.theta`. Let `p` be the 0-based position of the token in the sequence. The executor splits the query vector into `num_q_heads` consecutive head slices of `d` elements, and the key vector into `num_kv_heads` such slices. It rotates every slice independently, after the QK norm and after any query scale (§17.4). For one slice `x[0 .. d-1]` and each pair index `i` in `0 .. d/2 - 1`:

```text
φ_i(p)     = p · θ^(−2i/d)
a          = x[i]
b          = x[i + d/2]
x'[i]       = a · cos φ_i(p)  −  b · sin φ_i(p)
x'[i + d/2] = a · sin φ_i(p)  +  b · cos φ_i(p)
```

So the sine term is **subtracted** in the first-half output `x'[i]` and **added** in the second-half output `x'[i + d/2]`. Each pair `(x[i], x[i + d/2])` is rotated by the angle `+φ_i(p)` in the plane with `x[i]` on the first axis and `x[i + d/2]` on the second axis, counter-clockwise for a positive angle. Both outputs of a pair are computed from the unrotated `a` and `b`. At `p = 0` every angle is 0 and the slice is unchanged.

The executor computes `θ^(−2i/d)` and `φ_i(p)` in binary64, rounds `sin φ_i(p)` and `cos φ_i(p)` to binary32, and forms the products and sums in binary32. This sentence is informative: precision is arithmetic, outside this document (§0). The executor's other rotary kinds use the same sign convention with given inverse frequencies and an amplitude [S148]. They do not occur in this profile.

### 17.6 FFN, head and stack-wide fields

| JSON path | JSON type | Unit / encoding | When absent | Meaning | **(observed)** | Upstream key | Sources |
|---|---|---|---|---|---|---|---|
| `X.ffn` | object (FfnSurface) | — | Optional in the schema; present iff the programme runs an FFN. MUST be present in this profile | What the FFN operation reads | present | — | [S111][S113] |
| `X.ffn.ffn_type` | string: `"gated"` or `"standard"` | enumeration | Required within `X.ffn` | `"gated"`: `FFN(x) = down( act(gate(x)) ⊙ up(x) )`, with `gate_proj`, `up_proj`, `down_proj`, where `⊙` is the elementwise product | `"gated"` | no upstream counterpart | [S113][S120][S134] |
| `X.ffn.activation` | string: `"silu"`, `"gelu"`, `"gelu_tanh"`, `"relu"` | enumeration | Required within `X.ffn` | The nonlinearity `act` above. `"silu"` is `x·sigmoid(x)` | `"silu"` | `hidden_act`, through this map (case-insensitive): `silu`, `swish` → `"silu"`; `gelu` → `"gelu"`; `gelu_new`, `gelu_pytorch_tanh` → `"gelu_tanh"`; `relu` → `"relu"`. **Encode-time default:** when `hidden_act` is absent, or is a spelling not in this map, the writer stores `"silu"` | [S113][S120][S134] |
| `X.ffn.gate_policy` | object, internally tagged by `"kind"` | — | Optional. Absent means `{"kind":"gated"}` | How the gate combines with the up branch. `{"kind":"gated"}` is the plain `act(gate) ⊙ up`. Any other kind MUST NOT appear in this profile | `{"kind":"gated"}` | no upstream counterpart | [S113][S121] |
| `X.ffn.moe` | object | — | Optional; absent means dense. MUST be absent in this profile | Mixture-of-experts surface | absent | no upstream counterpart | [S113] |
| `X.head` | object (HeadSurface) | — | Optional in the schema; present iff the component owns an embedding or output-head object. MUST be present in this profile | What the embedding lookup and output head read | present | — | [S58][S125] |
| `X.head.head_reuses_embedding` | boolean | — | Optional. Absent means `false` | `true` means that a *missing* output-head object is read as "use the embedding matrix as the head" (§12(a)). **Encoding:** for this family the writer stores `true` unless `tie_word_embeddings` is declared exactly `false`. So an absent `tie_word_embeddings` also gives `true`. (The general rule is `true` when the architecture has no independent head, or `tie_word_embeddings` is not exactly `false`. Qwen3 has an independent head.) | `true` | `tie_word_embeddings` (indirect; see §17.7) | [S58][S133] |
| `X.head.embed_scale`, `X.head.output_multiplier`, `X.head.final_logit_softcapping`, `X.head.embedding_norm` | number or object | — | Optional. Absent means the operation does not exist, which differs from `1.0`. MUST be absent in this profile | Embedding scale; logit multiplier; final-logit softcap; weightless embedding norm | absent | no upstream counterpart | [S58] |
| `X.residual_topology` | object, internally tagged by `"kind"` | — | Optional. Absent means `{"kind":"single_stream"}` | `{"kind":"single_stream"}`: one residual vector, to which each sublayer output is added. Any other kind MUST NOT appear in this profile | `{"kind":"single_stream"}` | no upstream counterpart | [S111][S122] |
| `X.residual_scale`, `X.residual_in_fp32` | number; boolean | — | Optional. Absent means the operation or declaration does not exist. MUST be absent in this profile | Residual-branch multiplier; fp32 residual declaration | absent | no upstream counterpart | [S111] |

**Keys that MUST be absent from `X` in this profile**, besides those marked above: `linear_attention`, `kda`, `kda_gate_lower_bound`, `kda_gate_form`, `kda_use_full_rank_gate`, `mla`, `mamba2`, `conv_qkv` [S111]. Each names an operator this subject does not run. A comparator MUST report the presence of any of them as a configuration mismatch.

### 17.7 Correspondence with the D2 field list

For each D2 field, this table gives where the container represents it, the observed value, and the comparison a comparator MUST perform. "Upstream" means the pinned `config.json`. A comparator MUST NOT fill a missing container value from LARQL's defaults, and MUST NOT fill a missing upstream value from the container.

| D2 field | Upstream value | Container representation | **(observed)** | Comparison |
|---|---|---|---|---|
| `hidden_size` | `1024` | `C.hidden_size`; also `index.json.hidden_size` and the shapes in §17.2 | `1024` | Integer equality for each |
| `intermediate_size` | `3072` | `X.ffn.intermediate_size`; also the FFN shapes | `3072` | Integer equality; `X.ffn.intermediate_size_by_layer` absent |
| `num_hidden_layers` | `28` | `C.num_layers`; also `len(C.attention)` and `index.json.num_layers` | `28` | Integer equality for each |
| `num_attention_heads` | `16` | `X.attention.num_q_heads`; also `q_proj` rows ÷ `head_dim` | `16` | Integer equality |
| `num_key_value_heads` | `8` | `X.attention.num_kv_heads` **and** `C.attention[L].geometry.num_kv_heads` for all `L` | `8` everywhere | Integer equality at all 29 sites |
| `head_dim` | `128` | `X.attention.head_dim` **and** `C.attention[L].geometry.head_dim` for all `L`; also the `q_norm`/`k_norm` length | `128` everywhere | Integer equality at all 29 sites |
| `vocab_size` | `151936` | `X.head.vocab_size`; also the embedding and output-head shapes | `151936` | Integer equality |
| `hidden_act` | `"silu"` | `X.ffn.activation` | `"silu"` | Map the upstream spelling by the §17.6 table, then compare strings. An upstream spelling not in the table is a mismatch. Because the writer also stores `"silu"` for an absent or unknown `hidden_act`, `"silu"` in the container does not by itself show that upstream declared it |
| `attention_bias` | `false` | `X.attention.attention_bias` | `false` | Boolean equality. An absent container value is not `false`: it is an unresolved comparability assumption. The decoder stack also holds no bias tensors (§9.4) |
| `rms_norm_eps` | `1e-06` | `X.norm.pre.eps` and `X.norm.final_norm.eps` | `9.999999974752427e-7` (both) | Each container value MUST equal `f64(f32(upstream))` exactly. It MUST NOT be compared with the upstream binary64 value directly, which never matches here. Note that any two upstream values with the same binary32 rounding are indistinguishable in the container |
| `rope_theta` | `1000000` | `C.attention[L].position.theta` for all `L` | `1000000.0` everywhere | Binary64 equality at all 28 sites, with `kind == "rope"` |
| `rope_scaling` | `null` | **No direct field.** Represented only through `C.attention[L].position.kind` | `"rope"` everywhere | `null` corresponds to `kind == "rope"` at every layer. Any other `kind` at any layer is a mismatch against `null` |
| `sliding_window` | `null` | **No direct field.** Represented only through `C.attention[L].span` and `.window` | `"full"`, no `window`, everywhere | `null` corresponds to `span == "full"` and `window` absent at every layer. A non-null upstream window requires `window == sliding_window` on every layer whose `span` is `"sliding"` |
| `use_sliding_window` | `false` | **Not represented.** Its only effect is on the resolved `span` (§17.5, rule 1) | — | Not comparable directly. The container is consistent with `false`, and equally with any value when `sliding_window` is `null` |
| `max_window_layers` | `28` | **Not represented.** Its only effect is on the resolved `span` (§17.5, rule 2) | — | Not comparable directly. With `sliding_window` `null` it has no effect on the computation, and the container carries no trace of it |
| `tie_word_embeddings` | `true` | **No direct field.** Represented indirectly by `X.head.head_reuses_embedding`, together with the two separate objects `target.embedding` and `target.output_head` (§12) | `head_reuses_embedding: true`; both objects present; equal `payload_sha256` | For upstream `true`: `head_reuses_embedding` MUST be `true`, **and**, because this container has an output-head object, `index.json.representations["target.output_head@BF16"].payload_sha256` MUST equal that of `target.embedding@BF16` (§12(c)). `head_reuses_embedding` alone is not sufficient: the writer sets it whenever `tie_word_embeddings` is not exactly `false`, and the executor does not consult it when an output-head object exists (§17.8) |

**D2 fields with no representation in the container:** `use_sliding_window` and `max_window_layers` have no field and leave no trace beyond the resolved per-layer `span`. `rope_scaling`, `sliding_window` and `tie_word_embeddings` have no field of their own; they are represented only indirectly, as stated above.

**Computation-relevant fields with no upstream counterpart.** These fields are fixed by the architecture, not by `config.json`. A comparator compares them against the behaviour of the pinned reference implementation, which the harness fixes, not against `config.json`: `X.attention.score_scale` (derived from `head_dim`), `X.attention.qk_norm_scope`, `X.attention.qk_norm_weight_offset`, `X.attention.parameter_free_qk_norm`, `X.norm.pre.kind`, `X.norm.pre.weight_offset`, `X.norm.final_norm.kind`, `X.norm.final_norm.weight_offset`, `X.norm.placement`, `X.ffn.ffn_type`, `X.ffn.gate_policy`, `X.residual_topology`, `C.attention[L].operator`, the RoPE pairing implied by `kind: "rope"`, the QK-norm epsilon (§17.3), and the absence of every key §17.4 to §17.6 require to be absent.

### 17.8 Consumption by `vindex3 exec` (informative)

**This subsection is informative. It is not a format statement.** It records where LARQL's `exec` path, at commit `2536bb79`, reads each field above, and whether it uses the declared value. It is a pointer for a separate execution-path audit, which must confirm it independently. It was derived by reading code only; nothing was built or run. "Plan" means `opplan::plan_component_ops`, which `exec` runs before any arithmetic. "Production" means the CPU production backend that `--backend production-q8` selects [S6].

**General.** `exec` builds its operation plan from the container alone. It never reads a `config.json` [S136]. The plan copies the surface values into per-operation records [S115][S142]. The production backend reads those records [S146][S147].

| Field | Where exec reads it | Uses the declared value? |
|---|---|---|
| `C.num_layers`, `C.attention` length | Plan refuses unless the attention array has `C.num_layers` elements, and builds exactly `C.num_layers` layer records [S137, `opplan/build.rs:321-332`][S142, `build/construct.rs:101-102`] | Yes |
| `C.hidden_size` | Plan shape contracts for every operand [S138, `opplan/build.rs:359`][S141]. **At run time** the residual width is taken from the embedding tensor's `shape[1]`, not from `C.hidden_size` [S145, `exec/prepared/loading.rs:83`] | Declared value checked against shapes, then **the shape is used**. They agree whenever the plan closes |
| `X.attention.num_q_heads` | Shape contracts and every layer's attention record [S139, `opplan/build.rs:483`][S142, `build/construct.rs:620`] | Yes |
| `X.attention.num_kv_heads`, `X.attention.head_dim` | Used only for a layer whose `C.attention[L].geometry` is absent [S139, `opplan/build.rs:478-482`] | **Ignored for this container**: every layer carries `geometry`, which wins. The values agree here |
| `C.attention[L].geometry.*` | Layer `L`'s attention record and shape contracts [S139][S142, `build/construct.rs:620-622`]. Grouped-query mapping is query head `h` → KV head `h ÷ (num_q_heads ÷ num_kv_heads)` [S149, `exec/production/helpers.rs:227-232`] | Yes |
| `X.ffn.intermediate_size` | Shape contracts; each FFN record's width [S139, `opplan/build.rs:465-470`][S142, `build/construct.rs:288-300`] | Yes |
| `X.head.vocab_size` | Plan shape check of the embedding and output-head tensors [S140, `opplan/build.rs:682-703`]. **At run time** the logit count is the output-head tensor's `shape[0]` [S151, `exec/prepared/accessors.rs:199-201`] | Declared value checked against shapes, then **the shape is used** |
| `X.norm.pre` (kind, eps, weight_offset) | Pre-attention and pre-FFN norm records [S142, `build/construct.rs:472-476`, `:693`]. Production RMSNorm uses `eps` as given (binary64), inside a binary64 sum of squares [S145, `exec/prepared.rs:259-266`][S146, `exec/production/plan_backend.rs:77-92`][S152] | Yes. **The executed epsilon is `9.999999974752427e-7`, not `1e-6`**, because of the encode-time binary32 round trip (§17.3) |
| QK-norm epsilon (no field) | The layer record carries `declared_norm_eps = X.norm.pre.eps` [S142, `build/construct.rs:473`][S143]. Every attention call passes it as the QK-norm epsilon [S144: `exec/attention_ops.rs:126-197`, `exec/layer_exec.rs:330-370`, `exec/decode/run.rs:316-326`][S147, `exec/production.rs:276-293`] | **Substitution by design:** the QK norms run at the pre-norm epsilon. No separate value exists to ignore |
| `X.norm.final_norm` | Final-norm record [S142, `build/construct.rs:728-729`]; applied before the head [S151, `exec/prepared/accessors.rs:177-185`] | Yes |
| `X.norm.placement` | Plan refuses if absent, refuses `post_only`, and selects norm operands per placement [S137, `opplan/build.rs:229-320`][S142, `build/construct.rs:246-282`] | Yes |
| `X.norm.post` | Read only under `pre_post`/`post_only` [S137, `opplan/build.rs:301-320`] | Not read for `pre_only` |
| `X.attention.score_scale` | Attention record [S142, `build/construct.rs:624`]. Production multiplies each binary32 dot product by the scale **rounded to binary32** [S149, `exec/production/helpers.rs:238`] | Yes, at binary32 precision (`0.0883883461356163`) |
| `X.attention.query_scale`, `logit_softcapping` | Applied only when present [S147, `exec/production.rs:295-299`][S149, `exec/production/helpers.rs:239-242`] | Absent, so not applied |
| `X.attention.attention_bias`, `qkv_bias` | Plan binds bias operands only when `attention_bias` is `true` (or `qkv_bias` is `true` for Q/K/V) [S142, `build/construct.rs:217-227`]. Production adds a bias only when one is bound: Q/K/V at [S147, `exec/production.rs:473-484`], the output-projection bias at [S149, `exec/production/helpers.rs:19`] | Yes. Note: an **absent** `attention_bias` executes the same as `false` (no bias) |
| `X.attention.qk_norm_scope`, `qk_norm_weight_offset` | QK-norm record, built only when the stack holds `q_norm` tensors [S142, `build/construct.rs:228-236`]; production applies weighted RMS per head [S147, `exec/production.rs:230-247`, `:259-293`][S152] | Yes |
| `X.attention.parameter_free_qk_norm` | Production applies the weightless norm only when the flag is set [S147, `exec/production.rs:243-246`, `:457-468`] | Yes (all `false`) |
| `C.attention[L].span`, `.window` | Attention record [S142, `build/construct.rs:633-640`]; production's first readable key position comes from the span and window [S150, `exec/backend/calls.rs:406-408`, `exec/kv.rs:62-79`] | Yes. Note: a `"sliding"` span with no `window` would silently run as full attention [S150, `exec/kv.rs:66`]. Not reached here |
| `C.attention[L].position` | Attention record [S142, `build/construct.rs:641`]. For `kind: "rope"`, production computes the inverse frequency `theta^(-2i/d)` and the angle in binary64 and rounds sine and cosine to binary32 [S147, `exec/production.rs:303-311`][S148, `exec/kernels.rs:147-158`] | Yes. **Hard-coded, not declared:** the split-half pairing. No container field states it [S118, `config/position.rs:28-45`] |
| `X.ffn.ffn_type`, `X.ffn.activation`, `X.ffn.gate_policy` | FFN record [S142, `build/construct.rs:288-300`]; production dispatches `"silu"` with a gate to its fused SiLU-gate kernel, refuses exact `"gelu"` and `"relu"`, and refuses non-plain gate policies other than SiTU [S146, `exec/production/plan_backend.rs:179-200`][S147, `exec/production.rs:129-214`] | Yes |
| `X.head.head_reuses_embedding` | Consulted only when the component has **no** output-head object [S140, `opplan/build.rs:699-711`] | **Ignored for this container**: `target.output_head` exists, so the head operand is that object. See also §12(d): production re-quantises that BF16 head at load |
| `X.head.embed_scale`, `output_multiplier`, `final_logit_softcapping`, `embedding_norm` | Applied only when present [S146, `exec/production/plan_backend.rs:68-75`, `:319-342`][S151, `exec/prepared/accessors.rs:305-330`] | Absent, so not applied |
| `X.residual_topology` | Plan and loader branch on it [S137, `opplan/build.rs:268-283`] | Yes (`single_stream`) |
| `X.context_length` | **Not read** by the plan or by `exec` (no reference found under `opplan/` or the CLI `vindex3` commands) | **Ignored.** No position bound is enforced from it |
| `C.attention[L].operator` | Plan decides each layer's operator from operand evidence and the policy [S142, `build/construct.rs:477-619`] | Yes |

Further observations, from the third-party check (`evidence/B3/rev3/CHECK.md`, findings N1, N2, N3, N5, N6):

- **N1. Every projection width comes from the run-time `hidden`.** The Q/K/V and gate/up input widths, the o_proj and down output widths, and the embedding row stride all use the width taken from the embedding tensor's `shape[1]`, not `C.hidden_size` [S154, `exec/layer_exec.rs:336-366`, `exec/production/select.rs:64-67`, `exec/backend/plan_backend.rs:184`, `exec/production/plan_backend.rs:68-71`]. The plan's shape contracts force the two to agree.
- **N2. No configuration override is reachable on the vindex3 exec path.** `larql-compute` has run-time overrides for the norm epsilon, RoPE base, position divisor, frequency scaling and attention window [S155, `LC/residual.rs:48-52`, `LC/attention/block.rs:377-383`, `:483`]. Only the architecture-driven entry points reach them, and nothing under `VX/opplan`, the CLI `vindex3` commands or `crates/larql-inference/src/vindex3` references them. The kernels `exec` calls take every value as an argument. Environment variables that are read on the exec path select arithmetic, not configuration (for example `LARQL_KQUANT_EXEC`, defined at [S155, `VX/opplan/exec/cpu/physical/projection.rs:436`] and read at `:501`; `CLI/prepare.rs:214-224` is a comment describing it).
- **N3. LARQL ignores unknown graph keys.** No type under `VX/graph` or `LM/config` uses serde's `deny_unknown_fields`, so `exec` silently ignores any key it does not know, anywhere in the graph. `C.perception` is read only for a component whose `role` is perception [S153, `VX/graph/build/components.rs:242-253`]. This is why §17.1 makes the comparator report unknown keys.
- **N5. A missing final-norm op is skipped silently.** If the plan carries no final-norm op, the head reads the un-normalised vector [S151, `exec/prepared/accessors.rs:178-183`]. Not reached here: `target.final_norm` is present and shape-checked [S140, `opplan/build.rs:688`].
- **N6. The GQA division has no remainder check** on this path [S149, `exec/production/helpers.rs:227`]. Not reached here (16 ÷ 8 = 2).

Facts the executor uses that the container does not declare at all, listed for the audit: the split-half RoPE pairing; the QK-norm epsilon (shared with `X.norm.pre.eps`); the residual width and logit count taken from tensor shapes. Accumulation precision, softmax precision and kernel choice are arithmetic, outside this document (§0).

## Appendix A. Sources

All paths are relative to the LARQL worktree root `/Users/christopherhay/chris-source/larql-l1-2536bb79` at commit `2536bb79b199b1115445678e3e82c400b0b3fd07`. `VX` = `crates/larql-vindex/src/format/vindex3`. `CLI` = `crates/larql-cli/src/commands/primary/vindex3_cmd`. Revision 3 adds `LM` = `crates/larql-models/src` and `LC` = `crates/larql-compute/src`. In §17.8, a path given after an S-number without a prefix is relative to `VX/opplan` or to `LM`, as the S-number's row shows.

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
| S109 | `VX/graph/build/tables.rs:185-190` | `SourceBinding.tensors`/`.bytes` set from the source tensor group's count and byte total |
| S110 | `VX/graph/component.rs:103-136` | `Component` fields: `num_layers`, `hidden_size`, optional `attention` table, optional `execution` surface |
| S111 | `VX/graph/surface.rs:350-481` | `ExecutionSurface` fields; presence follows the programme; `context_length`; must-be-absent groups; `residual_topology` defaults to `single_stream` |
| S112 | `VX/graph/surface.rs:58-118` | `AttentionSurface` fields; absent `query_scale`/softcap means no operation; `attention_bias` absent means undeclared |
| S113 | `VX/graph/surface.rs:120-165` | `FfnSurface` fields; optional `intermediate_size`; `gate_policy` default |
| S114 | `VX/graph/surface.rs:293-318` | `NormSurface`: `pre`, optional `post`, `final_norm`, optional `placement` |
| S115 | `VX/opplan/ops.rs:24-128`, `VX/opplan/layer.rs:179-291` | Plan records: `NormOp`, `QkNormOp`, `AttentionOp`, `FfnOp`, `LayerPlan`, `EmbeddingOp`, `OutputOp` |
| S116 | `VX/graph/policy.rs:42-49`, `VX/graph/policy.rs:214-235`, `VX/graph/policy.rs:274-338`, `VX/graph/policy.rs:460-464` | `LayerOperator`, `AttentionSpan`, `AttentionLayerPolicy` (required `operator` and `position`; optional `span`, `window`, `geometry`, `v_from_k`, `declared_span`), `HeadGeometry` |
| S117 | `VX/graph/roles.rs:424-466` | `NormPlacement` variants and the meaning of `pre_only` |
| S118 | `LM/config/position.rs:28-45`, `LM/config/position.rs:69-203` | Split-half RoPE pairing constant; `PositionPolicy`, internally tagged by `kind` |
| S119 | `LM/config/norm.rs:5-37`, `LM/config/norm.rs:83-85`, `LM/config/norm.rs:110-151` | `NormType`, `NormSpec`; `norm_eps` reaches the surface through an f32 round trip; `ParameterFreeQkNorm`; `QkNormScope` |
| S120 | `LM/config/activation.rs:16-51`, `LM/config/activation.rs:233-241` | `Activation` variants and the HF-name map; `FfnType` |
| S121 | `LM/config/experts.rs:106-108`, `LM/config/experts.rs:188-194` | `ExpertGatePolicy`, tagged by `kind`; default `gated` |
| S122 | `LM/config/residual_topology.rs:88-97` | `ResidualTopology`, tagged by `kind` |
| S123 | `VX/graph/surface/linear_mla.rs:147-315` | Surface built from the resolved inventory: attention, FFN, norm and context-length fields |
| S124 | `VX/graph/surface/linear_mla.rs:321-393` | Norm placement judged from the stack's norm tensor names |
| S125 | `VX/graph/surface/linear_mla.rs:397-426` | Head surface: `vocab_size` (padding rule), `head_reuses_embedding` |
| S126 | `VX/graph/build/tables.rs:16-84` | Per-layer table: operator, span, window, position, geometry, `declared_span` |
| S127 | `LM/inventory/resolved.rs:171-217`, `LM/inventory/resolved.rs:235-328`, `LM/inventory/resolved.rs:329-342` | Per-layer resolution (sliding, window, position, geometry); execution resolution (score scale, norms, activation, bias, head reuse); topology (layers, hidden, heads, intermediate, vocab, context) |
| S128 | `LM/detect/parser.rs:133-149`, `LM/detect/parser.rs:163-169`, `LM/detect/parser.rs:183-192`, `LM/detect/parser.rs:228-233`, `LM/detect/parser.rs:301-305`, `LM/detect/parser.rs:316-321`, `LM/detect/parser.rs:418`, `LM/detect/parser.rs:423-426`, `LM/detect/parser.rs:432-434` | `config.json` keys read: `head_dim`, `num_key_value_heads`, `rope_theta`, `vocab_size`, `sliding_window`, `use_sliding_window`, `max_window_layers`, `tie_word_embeddings`, `rope_scaling`, `rms_norm_eps`, `attention_bias`, `hidden_act`, `max_position_embeddings` |
| S129 | `LM/detect/parser/rope_scaling.rs:25-54` | `rope_scaling` with no `type`/`rope_type` (including `null`) parses to no scaling |
| S130 | `LM/config/architecture/attention.rs:39-82`, `LM/config/architecture/attention.rs:100-112`, `LM/config/architecture/attention.rs:129-144`, `LM/config/architecture/attention.rs:191-196`, `LM/config/architecture/shared.rs:33-35` | Sliding resolution (`use_sliding_window`, `max_window_layers`, `layer_types`); per-layer geometry defaults; score scale = `head_dim^-0.5` by `powf`; `attention_bias` copied from the config |
| S131 | `LM/config/architecture/norms.rs:15-17`, `LM/config/architecture/norms.rs:40-43`, `LM/config/architecture/norms.rs:77-108`, `LM/config/architecture/norms.rs:138-148` | QK-norm scope default `per_head`; norm kind default RMS; pre and final NormSpec built from `norm_eps` cast to f32 |
| S132 | `LM/config/architecture/position.rs:17-20`, `LM/config/architecture/position.rs:39-41`, `LM/config/architecture/position.rs:58-62`, `LM/config/architecture/position.rs:256-369` | Per-layer position policy: unscaled `Rope { theta: rope_base }` when no scaling, no per-layer theta and no partial rotary |
| S133 | `LM/config/architecture/tensor_keys.rs:37-55` | `output_head_reuses_embedding` = not `tie_word_embeddings == Some(false)` |
| S134 | `LM/config/architecture/feed_forward.rs:14-52`, `LM/config/architecture/feed_forward.rs:113-116` | Activation from `hidden_act`, SiLU when absent or unjudged; `ffn_type` default gated |
| S135 | `LM/architectures/qwen.rs:15-38`, `LM/architectures/qwen.rs:122-140` | `qwen3` norm and QK-norm weight offsets are 0 |
| S136 | `crates/larql-inference/src/vindex3/runtime.rs:80-131` | `exec` opens and plans a component from the container's own contents |
| S137 | `VX/opplan/build.rs:229-332` | Plan requires the surface and placement; topology; refuses `post_only`; post-norm rule; attention table length |
| S138 | `VX/opplan/build.rs:358-418` | `hidden` from `C.hidden_size`; required surface groups; contradictory bias declarations |
| S139 | `VX/opplan/build.rs:463-517` | FFN width per layer; per-layer geometry wins over the surface; `num_q_heads` from the surface |
| S140 | `VX/opplan/build.rs:657-716` | Single-tensor objects checked against `[vocab_size, hidden]` and `[hidden]`; head falls back to the embedding only when no output-head object exists |
| S141 | `VX/opplan/build/shapes.rs:15`, `VX/opplan/build/shapes.rs:101-114`, `VX/opplan/build/shapes.rs:223-224`, `VX/opplan/build/layer_closure.rs:200-207` | Operand shape contracts; a mismatch is a closure defect |
| S142 | `VX/opplan/build/construct.rs:89-95`, `VX/opplan/build/construct.rs:101-105`, `VX/opplan/build/construct.rs:217-300`, `VX/opplan/build/construct.rs:472-476`, `VX/opplan/build/construct.rs:619-643`, `VX/opplan/build/construct.rs:689-699`, `VX/opplan/build/construct.rs:721-737` | Plan records built from the surface: norms, biases, QK norm, placement, FFN, attention, embedding, final norm, output |
| S143 | `VX/opplan/layer.rs:192-205` | `declared_norm_eps`: the declared norm epsilon, at which the QK norms also run |
| S144 | `VX/opplan/exec/attention_ops.rs:126-197`, `VX/opplan/exec/layer_exec.rs:330-370`, `VX/opplan/exec/decode/run.rs:316-326` | Attention calls pass `declared_norm_eps` as the QK-norm epsilon (batch and decode paths) |
| S145 | `VX/opplan/exec/prepared.rs:246-267`, `VX/opplan/exec/prepared/loading.rs:77-83`, `VX/opplan/exec/prepared/loading.rs:191-281`, `VX/opplan/exec/prepared/loading.rs:306-326` | Prepared norms carry the record's kind, eps and offset; run-time width from the embedding shape; final norm and head loaded |
| S146 | `VX/opplan/exec/production/plan_backend.rs:68-92`, `VX/opplan/exec/production/plan_backend.rs:179-200`, `VX/opplan/exec/production/plan_backend.rs:319-342` | Production embed, norm, FFN and output head |
| S147 | `VX/opplan/exec/production.rs:129-214`, `VX/opplan/exec/production.rs:230-311`, `VX/opplan/exec/production.rs:457-484` | Activation dispatch and gate-policy refusal; QK norm, query scale and RoPE; V norm and projection biases |
| S148 | `VX/opplan/exec/kernels.rs:147-158` | RoPE rotation: binary64 inverse frequency and angle, binary32 sine and cosine, split-half pairs |
| S149 | `VX/opplan/exec/production/select.rs:25-75`, `VX/opplan/exec/production/helpers.rs:199-268` | Projection, bias, norm and RoPE order; grouped-query mapping; score scale cast to binary32 |
| S150 | `VX/opplan/exec/backend/calls.rs:406-408`, `VX/opplan/exec/kv.rs:57-79` | Span and window select the readable key positions |
| S151 | `VX/opplan/exec/prepared/accessors.rs:165-209`, `VX/opplan/exec/prepared/accessors.rs:305-330` | Final norm then head; logit count from the head tensor's `shape[0]`; embedding lookup |
| S152 | `LC/residual.rs:56-78`, `LC/residual.rs:243-251` | RMSNorm kernels take `eps` as binary64 |
| S153 | `VX/graph/build/components.rs:242-253` | `Component.perception` consulted only under `role: Perception` |
| S154 | `VX/opplan/exec/layer_exec.rs:336-366`, `VX/opplan/exec/production/select.rs:64-67`, `VX/opplan/exec/backend/plan_backend.rs:184`, `VX/opplan/exec/production/plan_backend.rs:68-71` | Projection widths and embedding stride from the run-time `hidden` |
| S155 | `LC/residual.rs:48-52`, `LC/attention/block.rs:377-383`, `LC/attention/block.rs:483`, `VX/opplan/exec/cpu/physical/projection.rs:436`, `VX/opplan/exec/cpu/physical/projection.rs:501`, `CLI/prepare.rs:214-224` | `larql-compute` configuration overrides (architecture-driven paths only); an arithmetic switch (`LARQL_KQUANT_EXEC`) defined at line 436 and read at line 501, and the CLI comment describing it |
| S156 | `VX/opplan/exec/production.rs:302-311`, `VX/opplan/exec/production/select.rs:66-70`, `VX/opplan/exec/attention_ops.rs:225-231`, `VX/opplan/exec/decode/run.rs:316-331` | `kind: "rope"` applies the rotation to each `head_dim` slice of Q and K, after QK norm and query scale, at the token's position |

## Revision history

| Revision | SPEC.md SHA-256 | Changes |
|---|---|---|
| 1 | `47c2a304bffdc21bb17017aed248ee74f5827099c2d8b962a766dec888964ef0` | Initial draft, written before the fresh container existed |
| 2 | `3c4feb5e01f2c262e06e1f8579754921089cda46038f17c63cfd42f9d0c5fe50` | Applies the five corrections from the third-party check (`evidence/B3/CHECK.md`). **O2:** provenance updated to the fresh container `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`; §9 values marked observed; digests recorded; U1 (artifact name = snapshot hash), U2 and U3 (`kquant-larql-native` rev 1) closed; the §5.2 `model` example replaced. **O1:** ggml `facdc44a…` `src/ggml-common.h:251-256` named as the normative `block_q8_0` reference (§8.4). **A1:** `source_bindings[].tensors`/`.bytes` defined, with an optional cross-check (§6). **A2:** §12(b) notes the padding length differs and the parsed headers are otherwise equal. **A3:** §4.3 notes the observed 16-byte offset alignment while keeping the 2-byte assumption normative. No normative layout statement changed |
| 3 | `6350e07cff89fb04321ec49ea2e82b14d3893dc7a279d4fd2c899c8db1860a22` | For decision revision D2 (protocol OQ11). **Header:** revision line updated; new row naming the upstream `config.json` and its SHA-256. **§0:** one added bullet saying §17 is the only place execution-surface meanings are given, and that §17.8 is informative. **§6:** one added parenthetical pointing configuration comparators to §17. **§8.2:** the leftover "(computed, by the safetensors convention)" marker (check finding E1) becomes **(observed)**, citing the check; the statement itself is unchanged. **§16:** U5 marked partly closed, with the remaining scope stated. **New §17:** the computation-relevant fields of the `system_graph.json` execution surface for this profile (path, JSON type, encoding, absence rule, meaning, observed value, upstream key, sources); the keys that must be absent; the correspondence with every D2 field, including the D2 fields the container does not represent; and an informative account (§17.8) of where `vindex3 exec` reads each field. **Appendix A:** abbreviations `LM` and `LC`; new sources S110 to S152. **Corrections from the third-party check of the revision 3 draft (`evidence/B3/rev3/CHECK.md`):** C1, the §0 framing-only bullet now names §17 as an explicit exception; C2, §17.1's unknown-key rule also covers keys directly on `C`, and `C.perception` MUST be absent; C3, §17.8 cites the output-projection bias at `helpers.rs:19`; A1, §17.6 states the writer rule for `head_reuses_embedding` in full and marks the short form as this family's; A2, §3 points to §17.1; §17.8 gains the informative observations N1, N2, N3, N5 and N6; new sources S153 to S155. No normative statement of revision 2 changed |
| 4 | (this file) | For the D2 field assessment (`evidence/D2-FIELD-ASSESSMENT.md`), which found the RoPE rotation direction not stated. **Header:** revision line updated. **§0:** new marker **(observed in code)** defined. **§17.5:** new normative paragraph giving the exact rotation for `kind: "rope"` (pair indices, both outputs, the sign of each sine term, the angle, the slices it applies to and when), marked (observed in code), with an informative precision sentence. **§17.8 N2:** the `LARQL_KQUANT_EXEC` citation now points to its definition and read in `VX/opplan/exec/cpu/physical/projection.rs:436` and `:501` (advisory B1 of `evidence/B3/rev3/CHECK.md`). **Appendix A:** S155 extended; new source S156. No other normative statement changed |
