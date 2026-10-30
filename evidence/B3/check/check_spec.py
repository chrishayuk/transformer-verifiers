#!/usr/bin/env python
"""B3 third-party check, Phase A: a VINDEX3 reader written from SPEC.md alone.

Usage: python -I check_spec.py <container_dir> <upstream model.safetensors> [out.json]

Every rule below cites the SPEC.md section it implements. Nothing here was
derived from LARQL source or the spec author's notes. Read-only on all inputs.
Layout check for Q8_0 reports correlations only (no reconstruction-error stats).
"""
import hashlib
import json
import os
import struct
import sys
from collections import Counter, OrderedDict

import numpy as np
from gguf.quants import dequantize
from gguf.constants import GGMLQuantizationType

ROOT = sys.argv[1]
UPSTREAM = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else None

results = OrderedDict()   # check id -> {"pass": bool, "detail": ...}
notes = []                # guesses / observations
failures = []


def record(cid, ok, **detail):
    results.setdefault(cid, {"pass": True, "items": []})
    if not ok:
        results[cid]["pass"] = False
        failures.append((cid, detail))
    results[cid]["items"].append(dict(ok=bool(ok), **detail))


def safe_path(rel):
    # §2: resolve relative to root; reject absolute or '..' components
    if os.path.isabs(rel) or ".." in rel.split("/"):
        raise ValueError(f"unsafe path {rel!r}")
    return os.path.join(ROOT, rel)


def sha256_range(path, start, end=None, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(start)
        remaining = None if end is None else end - start
        while True:
            n = chunk if remaining is None else min(chunk, remaining)
            if n == 0:
                break
            b = f.read(n)
            if not b:
                break
            h.update(b)
            if remaining is not None:
                remaining -= len(b)
    return h.hexdigest()


# ---------------------------------------------------------------- upstream
def load_safetensors_header(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        hdr = json.loads(f.read(n))
    hdr.pop("__metadata__", None)
    return 8 + n, hdr


UP_BASE, UP_HDR = load_safetensors_header(UPSTREAM)
UP_MM = np.memmap(UPSTREAM, dtype=np.uint8, mode="r")


def up_bytes(key):
    s, e = UP_HDR[key]["data_offsets"]
    return UP_MM[UP_BASE + s: UP_BASE + e]


def bf16_to_f32(u8):
    u16 = np.frombuffer(u8.tobytes() if not u8.flags.c_contiguous else u8, dtype="<u2")
    return (u16.astype(np.uint32) << 16).view(np.float32)


# ---------------------------------------------------------------- index (§5, §14)
idx_path = safe_path("index.json")
record("8.versioning", os.path.isfile(idx_path), rule="§14.1 index.json present")
index = json.load(open(idx_path))
record("8.versioning", isinstance(index, dict) and "version" in index, rule="§14.1 object with version")
record("8.versioning", index.get("version") == 4, rule="§14.2 version==4", value=index.get("version"))
record("8.versioning", isinstance(index.get("system_graph"), str), rule="§14.3 system_graph present",
       value=index.get("system_graph"))
record("8.versioning", "moe_manifest" not in index, rule="§14.3 moe_manifest absent")
record("8.versioning", index.get("authority", "canonical") == "canonical" and "authority" not in index,
       rule="§1.2/§14.9 authority absent (canonical)")
record("8.versioning", "auxiliary_references" not in index, rule="§14.9 auxiliary_references absent")
for k in ("representation_attestations", "variants", "derived_from_model"):
    record("8.versioning", k not in index, rule=f"§5.2 {k} absent")
record("8.versioning", index.get("family") == "qwen3", rule="§5.2 family", value=index.get("family"))
record("8.versioning", index.get("hidden_size") == 1024 and index.get("num_layers") == 28,
       rule="§5.2 hidden_size/num_layers")
record("8.versioning", index.get("profiles") == [{"name": "exact"}], rule="§5.2 profiles")
record("8.versioning", isinstance(index.get("model"), str), rule="§5.2 model is string (not depended on)",
       value=index.get("model"))
known_top = {"version", "model", "family", "hidden_size", "num_layers", "moe_manifest", "system_graph",
             "auxiliary_references", "representation_attestations", "representations", "profiles",
             "variants", "segments", "authority", "precision_map", "derived_from_model"}
extra_top = sorted(set(index) - known_top)
record("8.versioning", True, rule="§5.2 unknown top-level keys (ignored)", value=extra_top)
PM_EXPECT = {"name": "r0-uniform", "encoding": "Q8_0",
             "roles": ["decoder-linear", "recurrence-projection", "recurrence-control", "expert-weight"]}
record("8.versioning", index.get("precision_map") == PM_EXPECT, rule="§5.4 precision_map exact",
       value=index.get("precision_map"))

reps = index["representations"]
record("8.versioning", len(reps) == 5, rule="§5.2 exactly five representations", value=sorted(reps))

# ---------------------------------------------------------------- graph (§6)
graph = json.load(open(safe_path(index["system_graph"])))
record("8.versioning", graph.get("schema") == 6, rule="§14.4 graph schema==6", value=graph.get("schema"))
comps = graph.get("components", [])
record("8.versioning", len(comps) == 1 and comps[0].get("id") == "target"
       and comps[0].get("role") == "primary_text", rule="§6 one component target/primary_text")
c0 = comps[0]
record("8.versioning", c0.get("num_layers") == 28 and c0.get("hidden_size") == 1024, rule="§6 component dims")
head = c0.get("execution", {}).get("head", {})
record("8.versioning", head.get("vocab_size") == 151936 and head.get("head_reuses_embedding") is True,
       rule="§6 execution.head", value=head)
objs = graph.get("objects", [])
ids = [o["id"] for o in objs]
record("8.versioning", len(objs) == 4 and ids == sorted(ids), rule="§6 four objects sorted by id", value=ids)
record("8.versioning", graph.get("edges") == [], rule="§6 edges empty")
objmap = {o["id"]: o for o in objs}
for o in objs:
    record("8.versioning", o["id"] == f'{o["component"]}.{o["kind"]}', rule="§6 id = component.kind", obj=o["id"])
    record("8.versioning", len(o["source_bindings"]) == 1, rule="§10.1 exactly one binding", obj=o["id"])
    r = o["representations"]
    record("8.versioning", r[0] == {"encoding": "BF16", "fidelity": "canonical"}, rule="§6 element 0 canonical",
           obj=o["id"])
    exp = [{"encoding": "BF16", "fidelity": "canonical"}]
    if o["id"] == "target.decoder_stack":
        exp.append({"encoding": "Q8_0", "fidelity": "approximate"})
    record("8.versioning", r == exp, rule="§6 representations after represent", obj=o["id"], value=r)

# §14.5 graph <-> representations coherence
rep_objs = {v["object"] for v in reps.values()}
record("8.versioning", rep_objs == set(objmap), rule="§14.5 graph objects == representation objects")
for rid, e in reps.items():
    record("8.versioning", rid == f'{e["object"]}@{e["encoding"]}', rule="§5.3 id = object@encoding", id=rid)
    gencs = [x["encoding"] for x in objmap[e["object"]]["representations"]]
    record("8.versioning", e["encoding"] in gencs, rule="graph lists this encoding", id=rid)

# §5.3 compiled-only keys
COMPILED_KEYS = ("compiled_from", "codec", "source_representation_digest", "encoder")
CODEC = {"family": "Q8_0", "revision": 1, "group_elems": 32, "element": "ggml-q8_0",
         "group_scale": "in-block", "tensor_scale": "in-block", "layout": "ggml-block-34"}
for rid, e in reps.items():
    if e["encoding"] == "BF16":
        record("8.versioning", not any(k in e for k in COMPILED_KEYS), rule="§5.3 canonical has no compiled keys",
               id=rid)
    else:
        record("8.versioning", e.get("compiled_from") == "target.decoder_stack@BF16", rule="§5.3 compiled_from",
               id=rid)
        record("8.versioning", e.get("codec") == CODEC, rule="§8.3/§14.8 codec exactly equal", id=rid,
               value=e.get("codec"))
        enc = e.get("encoder", {})
        record("8.versioning", isinstance(enc.get("algorithm"), str) and isinstance(enc.get("revision"), int),
               rule="§5.3 encoder shape (informative)", value=enc)

# §5.2 segments map
seg_keys_expected = {e["segment"][:-4]: 1 for e in reps.values() if e["segment"].endswith(".bin")}
record("8.versioning", index.get("segments") == seg_keys_expected, rule="§5.2 segments map = paths minus .bin",
       value=index.get("segments"))

# §7 step 3 selection
selected = {}
for oid, o in objmap.items():
    rid = f"{oid}@Q8_0" if f"{oid}@Q8_0" in reps else f'{oid}@{o["representations"][0]["encoding"]}'
    selected[oid] = rid
record("8.versioning", selected == {"target.decoder_stack": "target.decoder_stack@Q8_0",
                                    "target.embedding": "target.embedding@BF16",
                                    "target.final_norm": "target.final_norm@BF16",
                                    "target.output_head": "target.output_head@BF16"},
       rule="§7 step 3 selection", value=selected)

# §2 file inventory
all_files = sorted(os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(ROOT) for f in fs)
expected_files = sorted(["index.json", "system_graph.json", "candidate.json", "tokenizer.json",
                         "tokenizer_config.json", "generation_config.json"] + [e["segment"] for e in reps.values()])
record("1.framing", all_files == expected_files, rule="§2 file inventory", value=all_files)

# ---------------------------------------------------------------- segments (§4, §8)
DT_BYTES = {}
segs = {}
for rid, e in sorted(reps.items()):
    path = safe_path(e["segment"])
    fsize = os.path.getsize(path)
    with open(path, "rb") as f:
        H = struct.unpack("<Q", f.read(8))[0]
        record("1.framing", H <= 268435456, rule="§4.1 H<=256MiB", id=rid, H=H)
        raw = f.read(H)
    P = 8 + H
    text = raw.decode("utf-8")
    J = len(text.rstrip(" ").encode())
    pad = raw[J:]
    exp_pad = (16 - (8 + J) % 16) % 16
    record("1.framing", set(pad) <= {0x20} and len(pad) == exp_pad and len(pad) <= 15,
           rule="§4.1 space padding formula", id=rid, J=J, pad=len(pad), expected_pad=exp_pad)
    record("1.framing", P % 16 == 0, rule="§4.1 P%16==0 (writer)", id=rid, P=P)
    record("1.framing", P % 4 == 0, rule="§4.1 P%4==0", id=rid)
    # parse preserving key order
    hdr = json.loads(text, object_pairs_hook=OrderedDict)
    compact = json.dumps(hdr, separators=(",", ":"), ensure_ascii=False)
    record("1.framing", compact.encode() == raw[:J], rule="§3 header is compact JSON (informative)", id=rid)
    record("1.framing", list(hdr.keys()) == ["schema", "representation", "tensors"],
           rule="§4.2 header keys/order", id=rid, keys=list(hdr.keys()))
    record("1.framing", hdr.get("schema") == 1, rule="§4.2 schema==1", id=rid)
    record("1.framing", hdr.get("representation") == rid, rule="§4.2 representation==key", id=rid,
           value=hdr.get("representation"))
    tens = hdr["tensors"]
    record("1.framing", len(tens) == e["tensor_count"], rule="§5.3 tensor_count", id=rid, n=len(tens))
    names = [t["name"] for t in tens]
    record("1.framing", len(set(names)) == len(names), rule="§4.3 unique names", id=rid)
    record("1.framing", names == sorted(names, key=lambda s: s.encode()), rule="§4.3 byte-sorted", id=rid)
    keyorders = Counter(tuple(t.keys()) for t in tens)
    record("1.framing", list(keyorders) == [("name", "dtype", "shape", "offset", "len")],
           rule="§4.2 entry keys/order", id=rid, value=[list(k) for k in keyorders])
    cur = 0
    contiguous = True
    for t in tens:
        if t["offset"] != cur:
            contiguous = False
        cur = t["offset"] + t["len"]
    payload = fsize - P
    record("1.framing", contiguous, rule="§4.3 contiguous offsets from 0", id=rid)
    record("1.framing", cur == payload == e["payload_bytes"], rule="§4.3 Σlen == payload == payload_bytes, no trailing",
           id=rid, sum_len=cur, payload=payload, payload_bytes=e["payload_bytes"])
    record("1.framing", fsize == P + e["payload_bytes"], rule="§4.3 file length", id=rid, file_size=fsize)
    record("1.framing", all(t["offset"] + t["len"] <= payload for t in tens), rule="§4.3 offset+len<=payload", id=rid)
    segs[rid] = dict(path=path, H=H, P=P, tensors=tens, size=fsize, J=J, pad=len(pad))

# §4.1 / §9.4 stated header sizes
H_STATED = {"target.decoder_stack@BF16": 31448, "target.embedding@BF16": 152, "target.output_head@BF16": 152,
            "target.final_norm@BF16": 136, "target.decoder_stack@Q8_0": 31416}
for rid, h in H_STATED.items():
    record("1.framing", segs[rid]["H"] == h, rule="§4.1/§9.4 stated H value", id=rid, H=segs[rid]["H"], stated=h)
record("1.framing", segs["target.decoder_stack@BF16"]["pad"] == 8, rule="§4.1 BF16 decoder header ends in 8 spaces")
record("1.framing", segs["target.decoder_stack@Q8_0"]["J"] == 31408 and segs["target.decoder_stack@Q8_0"]["pad"] == 8,
       rule="§9.4 Q8 header JSON 31408 + 8 pad")
record("1.framing", segs["target.decoder_stack@Q8_0"]["size"] == 468087488, rule="§9.4 Q8 file size")
for rid, pb in {"target.decoder_stack@BF16": 880932864, "target.decoder_stack@Q8_0": 468056064,
                "target.embedding@BF16": 311164928, "target.final_norm@BF16": 2048,
                "target.output_head@BF16": 311164928}.items():
    record("1.framing", reps[rid]["payload_bytes"] == pb, rule="§9.2 payload_bytes", id=rid)

# §4.3 layer order illustration
q8 = segs["target.decoder_stack@Q8_0"]["tensors"]
layer_order = []
for t in q8:
    L = t["name"].split(".")[0]
    if not layer_order or layer_order[-1] != L:
        layer_order.append(L)
exp_order = sorted([str(i) for i in range(28)], key=lambda s: (s + ".").encode())
record("1.framing", layer_order == exp_order, rule="§4.3 layer order 0,1,10,..", value=layer_order)

# ---------------------------------------------------------------- 2. representation from container
def expected_len(dtype, shape):
    n = int(np.prod(shape)) if shape else 1
    if dtype == "BF16":
        return 2 * n
    if dtype == "Q8_0":
        K = shape[-1]
        R = int(np.prod(shape[:-1])) if len(shape) > 1 else 1
        return R * (K // 32) * 34
    return None


dtype_counts = {}
for rid, s in segs.items():
    c = Counter()
    for t in s["tensors"]:
        c[t["dtype"]] += 1
        record("2.identify", t["dtype"] in ("BF16", "Q8_0"), rule="§8.1/§14.10 dtype allowed", id=rid,
               name=t["name"], dtype=t["dtype"])
        record("2.identify", all(isinstance(d, int) and d >= 0 for d in t["shape"]), rule="§4.2 shape ints",
               id=rid, name=t["name"])
        if t["dtype"] == "Q8_0":
            record("2.identify", t["shape"][-1] % 32 == 0, rule="§8.4 K%32==0", id=rid, name=t["name"])
            record("2.identify", reps[rid].get("codec") == CODEC, rule="§8.3 Q8_0 tensor needs codec", id=rid,
                   name=t["name"])
        record("2.identify", t["len"] == expected_len(t["dtype"], t["shape"]), rule="§8.1 len formula", id=rid,
               name=t["name"], len=t["len"])
    dtype_counts[rid] = dict(c)
record("2.identify", dtype_counts["target.decoder_stack@Q8_0"] == {"Q8_0": 196, "BF16": 112},
       rule="§2/§11.3 Q8 pack 196 Q8_0 + 112 BF16", value=dtype_counts["target.decoder_stack@Q8_0"])
record("2.identify", dtype_counts["target.decoder_stack@BF16"] == {"BF16": 308}, rule="§2 BF16 decoder 308 BF16")
# Q8_0 offsets parity claim (§4.3 "any even number")
q8_offsets_mod = Counter(t["offset"] % 34 for t in q8 if t["dtype"] == "Q8_0")
record("2.identify", all(t["offset"] % 2 == 0 for t in q8), rule="§4.3 offsets even",
       value={"Q8_0 offset mod 16": dict(Counter(t["offset"] % 16 for t in q8 if t["dtype"] == "Q8_0"))})

# §9.3 single-tensor entries
for rid, ent in {"target.embedding@BF16": {"name": "weight", "dtype": "BF16", "shape": [151936, 1024], "offset": 0,
                                           "len": 311164928},
                 "target.output_head@BF16": {"name": "weight", "dtype": "BF16", "shape": [151936, 1024], "offset": 0,
                                             "len": 311164928},
                 "target.final_norm@BF16": {"name": "weight", "dtype": "BF16", "shape": [1024], "offset": 0,
                                            "len": 2048}}.items():
    record("2.identify", [dict(t) for t in segs[rid]["tensors"]] == [ent], rule="§9.3 table entry", id=rid)

# §9.4 informative table
REL = [("input_layernorm.weight", [1024], "BF16", 2048, 0),
       ("mlp.down_proj.weight", [1024, 3072], "Q8_0", 3342336, 2048),
       ("mlp.gate_proj.weight", [3072, 1024], "Q8_0", 3342336, 3344384),
       ("mlp.up_proj.weight", [3072, 1024], "Q8_0", 3342336, 6686720),
       ("post_attention_layernorm.weight", [1024], "BF16", 2048, 10029056),
       ("self_attn.k_norm.weight", [128], "BF16", 256, 10031104),
       ("self_attn.k_proj.weight", [1024, 1024], "Q8_0", 1114112, 10031360),
       ("self_attn.o_proj.weight", [1024, 2048], "Q8_0", 2228224, 11145472),
       ("self_attn.q_norm.weight", [128], "BF16", 256, 13373696),
       ("self_attn.q_proj.weight", [2048, 1024], "Q8_0", 2228224, 13373952),
       ("self_attn.v_proj.weight", [1024, 1024], "Q8_0", 1114112, 15602176)]
ok94 = True
for gi, L in enumerate(exp_order):
    for j, (rn, sh, dt, ln, off) in enumerate(REL):
        t = q8[gi * 11 + j]
        if (t["name"], t["shape"], t["dtype"], t["len"], t["offset"]) != (f"{L}.{rn}", sh, dt, ln,
                                                                           gi * 16716288 + off):
            ok94 = False
record("2.identify", ok94, rule="§9.4 informative table (names, shapes, dtypes, len, group offsets)")

# ---------------------------------------------------------------- 3. HF mapping (§10)
mapping = {}  # (rid, name) -> hf key
for rid, s in segs.items():
    obj = objmap[reps[rid]["object"]]
    p = obj["source_bindings"][0]["tensor_prefix"]
    keys = []
    for t in s["tensors"]:
        k = p + "." + t["name"]
        mapping[(rid, t["name"])] = k
        keys.append(k)
        present = k in UP_HDR
        record("3.mapping", present, rule="§10.1 key exists upstream", id=rid, name=t["name"], key=k)
        if present:
            record("3.mapping", UP_HDR[k]["shape"] == t["shape"], rule="§10 shape matches upstream", id=rid, key=k)
            record("3.mapping", UP_HDR[k]["dtype"] == "BF16", rule="upstream dtype BF16", key=k)
    record("3.mapping", len(set(keys)) == len(keys), rule="§10 injective within representation", id=rid)
    b = obj["source_bindings"][0]
    if reps[rid]["encoding"] == "BF16":
        record("3.mapping", b["tensors"] == len(s["tensors"]) and b["bytes"] == reps[rid]["payload_bytes"],
               rule="binding tensors/bytes == canonical segment (unspecified field semantics)", id=rid)
# per selected set and per canonical set: bijection with upstream
for label, rids in {"selected(§7)": list(selected.values()),
                    "canonical": [r for r in reps if r.endswith("@BF16")]}.items():
    ks = [mapping[(r, t["name"])] for r in rids for t in segs[r]["tensors"]]
    record("3.mapping", len(ks) == len(set(ks)) == 311 and set(ks) == set(UP_HDR),
           rule="§9.1/§10.2 bijection with 311 upstream keys", set=label, n=len(ks), upstream=len(UP_HDR),
           missing=sorted(set(UP_HDR) - set(ks)))
# §10.1 covers / longest-prefix: each upstream key owned by its object's prefix
prefixes = {oid: o["source_bindings"][0]["tensor_prefix"] for oid, o in objmap.items()}
own_ok = True
for k in UP_HDR:
    cov = [oid for oid, p in prefixes.items() if k == p or k.startswith(p + ".")]
    if len(cov) != 1:
        own_ok = False
record("3.mapping", own_ok, rule="§10.1 each upstream key covered by exactly one prefix")

# ---------------------------------------------------------------- 4. BF16 bytes
bf16_counter = Counter()
for rid, s in segs.items():
    mm = np.memmap(s["path"], dtype=np.uint8, mode="r")
    for t in s["tensors"]:
        if t["dtype"] != "BF16":
            continue
        a = mm[s["P"] + t["offset"]: s["P"] + t["offset"] + t["len"]]
        ub = up_bytes(mapping[(rid, t["name"])])
        same = a.shape == ub.shape and np.array_equal(a, ub)
        bf16_counter[rid] += 1
        record("4.bf16", same, rule="§8.2 bytes identical to upstream", id=rid, name=t["name"])
    del mm
results["4.bf16"]["counts"] = dict(bf16_counter)

# ---------------------------------------------------------------- 5. Q8_0 layout (correlation only)
Q8T = GGMLQuantizationType.Q8_0


def corr(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    a -= a.mean()
    b -= b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


s = segs["target.decoder_stack@Q8_0"]
mm = np.memmap(s["path"], dtype=np.uint8, mode="r")
rng = np.random.default_rng(0)
q8_corr = []
alt_max = {}
for t in s["tensors"]:
    if t["dtype"] != "Q8_0":
        continue
    sh = t["shape"]
    K = sh[-1]
    R = int(np.prod(sh[:-1]))
    B = K // 32
    start = s["P"] + t["offset"]
    raw = np.array(mm[start: start + t["len"]])
    blocks = raw.reshape(R, B * 34)  # §8.4: row r, block b at (r*B+b)*34
    D = dequantize(blocks, Q8T)
    shape_ok = D.shape == (R, K)
    W = bf16_to_f32(up_bytes(mapping[("target.decoder_stack@Q8_0", t["name"])])).reshape(R, K)
    c_stated = corr(D, W)
    alts = {}
    # (a) transpose: decode the same bytes as if blocks ran along dim 0 (rows of length R)
    if R % 32 == 0:
        Dt = dequantize(raw.reshape(K, (R // 32) * 34), Q8T).T
        alts["transpose_blocks"] = corr(Dt, W)
    # (a') stated decode compared against the transposed upstream (only meaningful if square)
    if R == K:
        alts["vs_W_T"] = corr(D, W.T)
    # (b) row permutation: rows rolled by one, and a random permutation
    alts["row_roll1"] = corr(D, np.roll(W, 1, axis=0))
    alts["row_perm"] = corr(D, W[rng.permutation(R)])
    # (c) block permutation within each row
    alts["block_roll1"] = corr(D.reshape(R, B, 32), np.roll(W.reshape(R, B, 32), 1, axis=1))
    # (d) byte-offset shifts: start the slice 2 bytes and one block (34 bytes) late / early
    for sh_b in (2, 34, -34):
        st = start + sh_b
        rr = np.array(mm[st: st + t["len"]])
        if rr.size == t["len"]:
            Ds = dequantize(rr.reshape(R, B * 34), Q8T)
            Ds = np.nan_to_num(Ds, nan=0.0, posinf=0.0, neginf=0.0)
            alts[f"byte_shift_{sh_b:+d}"] = corr(Ds, W)
    ok = shape_ok and c_stated > 0.99 and all(abs(v) < 0.5 for v in alts.values())
    q8_corr.append(c_stated)
    for k, v in alts.items():
        alt_max[k] = max(alt_max.get(k, -1.0), abs(v))
    record("5.q8_layout", ok, name=t["name"], shape_ok=shape_ok)
del mm
results["5.q8_layout"]["min_stated_corr"] = min(q8_corr)
results["5.q8_layout"]["n"] = len(q8_corr)
results["5.q8_layout"]["all_alternatives_below"] = 0.5 if max(alt_max.values()) < 0.5 else None

# ---------------------------------------------------------------- 6. integrity (§13)
payload_hash = {}
for rid, e in reps.items():
    sg = segs[rid]
    seg_h = sha256_range(sg["path"], 0)
    pay_h = sha256_range(sg["path"], sg["P"])
    payload_hash[rid] = pay_h
    record("6.integrity", seg_h == e["segment_sha256"], rule="§13.1 segment_sha256", id=rid)
    record("6.integrity", pay_h == e["payload_sha256"], rule="§13.1 payload_sha256", id=rid)
    if e["encoding"] == "BF16":
        h = hashlib.sha256()
        for t in sg["tensors"]:
            h.update(up_bytes(mapping[(rid, t["name"])]).tobytes())
        record("6.integrity", h.hexdigest() == e["payload_sha256"],
               rule="§13.1 canonical payload_sha256 == sha256(upstream bytes in segment order)", id=rid)
qe = reps["target.decoder_stack@Q8_0"]
record("6.integrity", qe["source_representation_digest"] == reps["target.decoder_stack@BF16"]["payload_sha256"]
       == payload_hash["target.decoder_stack@BF16"], rule="§13.2 source_representation_digest")
# §13.4 candidate.json seals (informative cross-check)
cand = json.load(open(safe_path("candidate.json")))
sealed = cand.get("ledger", {}).get("sealed", {})
srcseg = segs["target.decoder_stack@BF16"]
srctab = {t["name"]: t for t in srcseg["tensors"]}
qtab = {t["name"]: t for t in s["tensors"]}
nseal_ok = 0
for key, seal in sealed.items():
    obj, name = key.split("\u0001")
    qt = qtab[name]
    st = srctab[name]
    ok = (obj == seal["object"] == "target.decoder_stack" and seal["tensor"] == name and seal["encoding"] == "Q8_0"
          and seal["target_offset"] == s["P"] + qt["offset"] and seal["target_len"] == qt["len"]
          and seal["target_hash"] == sha256_range(s["path"], s["P"] + qt["offset"], s["P"] + qt["offset"] + qt["len"])
          and seal["source_hash"] == sha256_range(srcseg["path"], srcseg["P"] + st["offset"],
                                                  srcseg["P"] + st["offset"] + st["len"]))
    nseal_ok += ok
    record("6.integrity", ok, rule="§13.4 candidate seal", key=name)
results["6.integrity"]["candidate_seals"] = {"n": len(sealed), "ok": nseal_ok,
                                             "q8_tensors": sum(1 for t in s["tensors"] if t["dtype"] == "Q8_0")}
# §12 measured upstream hash
results["6.integrity"]["upstream_embed_sha256"] = hashlib.sha256(up_bytes("model.embed_tokens.weight").tobytes()).hexdigest()
results["6.integrity"]["upstream_lm_head_sha256"] = hashlib.sha256(up_bytes("lm_head.weight").tobytes()).hexdigest()

# ---------------------------------------------------------------- 7. tied embeddings (§12)
er, hr = "target.embedding@BF16", "target.output_head@BF16"
record("7.tied", "target.embedding" in objmap and "target.output_head" in objmap
       and objmap["target.embedding"]["source_bindings"][0]["tensor_prefix"] == "model.embed_tokens"
       and objmap["target.output_head"]["source_bindings"][0]["tensor_prefix"] == "lm_head",
       rule="§12(a) two logical objects with distinct bindings")
record("7.tied", head.get("head_reuses_embedding") is True, rule="§12(a) head_reuses_embedding true")
record("7.tied", reps[er]["segment"] != reps[hr]["segment"]
       and os.stat(segs[er]["path"]).st_ino != os.stat(segs[hr]["path"]).st_ino
       and segs[er]["size"] == segs[hr]["size"], rule="§12(b) two physical files (distinct inodes)")
a = np.memmap(segs[er]["path"], dtype=np.uint8, mode="r")[segs[er]["P"]:]
b = np.memmap(segs[hr]["path"], dtype=np.uint8, mode="r")[segs[hr]["P"]:]
record("7.tied", np.array_equal(a, b), rule="§12(c) payloads byte-identical")
record("7.tied", reps[er]["payload_sha256"] == reps[hr]["payload_sha256"]
       and reps[er]["payload_sha256"].startswith("8f29acf5") and reps[er]["payload_sha256"].endswith("acfb6"),
       rule="§12 payload_sha256 equal, = 8f29acf5…acfb6")
record("7.tied", reps[er]["segment_sha256"] != reps[hr]["segment_sha256"], rule="§12(b) segment_sha256 differ")
# Compare parsed headers minus `representation`. Raw bytes also differ in padding, because the names'
# lengths differ (J=147 vs 149, so pad=5 vs 3). That is expected under §4.1.
def _hdr(sg):
    with open(sg["path"], "rb") as f:
        f.seek(8)
        d = json.loads(f.read(sg["H"]))
    d.pop("representation")
    return d
record("7.tied", _hdr(segs[er]) == _hdr(segs[hr]),
       rule="§12(b) parsed headers differ only in representation name")
record("7.tied", all(t["dtype"] == "BF16" for t in segs[er]["tensors"] + segs[hr]["tensors"])
       and "target.embedding@Q8_0" not in reps and "target.output_head@Q8_0" not in reps,
       rule="§12(c)/(d) neither compiled")

# ---------------------------------------------------------------- 1b. hard links to source (§2 note)
src_root = os.path.join(os.path.dirname(ROOT.rstrip("/")), "qwen3-0.6b.vindex3")
if os.path.isdir(src_root):
    for rid, e in reps.items():
        if e["encoding"] != "BF16":
            continue
        sp = os.path.join(src_root, e["segment"])
        same = os.path.exists(sp) and (os.stat(sp).st_ino == os.stat(segs[rid]["path"]).st_ino
                                       or sha256_range(sp, 0) == e["segment_sha256"])
        record("1.framing", same, rule="§2 canonical segments hard-linked/identical to <SRC>", id=rid)

# ---------------------------------------------------------------- summary
summary = OrderedDict()
for cid, r in results.items():
    items = r["items"]
    summary[cid] = dict(pass_=r["pass"], checks=len(items), failed=sum(1 for i in items if not i["ok"]),
                        **{k: v for k, v in r.items() if k not in ("pass", "items")})
print(json.dumps(dict(dtype_counts=dtype_counts, summary=summary,
                      header_sizes={k: dict(H=v["H"], P=v["P"], J=v["J"], pad=v["pad"], size=v["size"])
                                    for k, v in segs.items()},
                      extra_top_level_keys=extra_top,
                      failures=failures[:50]), indent=1, default=str))
if OUT:
    json.dump(dict(results=results, summary=summary, failures=failures), open(OUT, "w"), indent=1, default=str)
