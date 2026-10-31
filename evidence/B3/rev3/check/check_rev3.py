#!/usr/bin/env python3
"""Third-party check of SPEC revision 3, §17, against the emitted container and the upstream config.json.

Independent of the author's scratch script. Reads only:
  - the container's index.json, system_graph.json and segment headers (never payloads),
  - the pinned upstream config.json.
Uses stdlib and numpy only (numpy for binary32 rounding). Writes raw results as JSON.

Usage: python -I check_rev3.py <container_dir> <config.json> <out.json>
"""
import hashlib
import json
import math
import re
import struct
import sys

import numpy as np

CONTAINER, CONFIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

results = []


def check(group, name, ok, observed=None, expected=None):
    results.append({"group": group, "assertion": name, "pass": bool(ok),
                    "observed": observed, "expected": expected})


def f32(x):
    return float(np.float32(x))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jtype(v):
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return "null"


MISSING = object()


def get(obj, path):
    cur = obj
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return MISSING
        cur = cur[p]
    return cur


inputs = {
    "system_graph.json": sha256(f"{CONTAINER}/system_graph.json"),
    "index.json": sha256(f"{CONTAINER}/index.json"),
    "config.json": sha256(CONFIG),
}
check("inputs", "system_graph.json sha256", inputs["system_graph.json"] ==
      "05fcec4c45167c2f8f424c35b8c39acb06cc92716f11e0ffbec341e110d66f57", inputs["system_graph.json"])
check("inputs", "index.json sha256", inputs["index.json"] ==
      "7f3ba8e5da50276e501e7694c46c0a3c9c9d7530596656376cc9597f05fec490", inputs["index.json"])
check("inputs", "config.json sha256", inputs["config.json"] ==
      "660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd", inputs["config.json"])

raw_graph = open(f"{CONTAINER}/system_graph.json").read()
G = json.loads(raw_graph)
I = json.load(open(f"{CONTAINER}/index.json"))
U = json.load(open(CONFIG))

# ---------------------------------------------------------------- §17.1 terms
check("17.1", "index.json.system_graph names system_graph.json", I.get("system_graph") == "system_graph.json",
      I.get("system_graph"))
comps = G["components"]
targets = [c for c in comps if c.get("id") == "target"]
check("17.1", "exactly one component", len(comps) == 1, len(comps))
check("17.1", "exactly one component with id 'target'", len(targets) == 1, len(targets))
C = targets[0]
X = C.get("execution", MISSING)
A = C.get("attention", MISSING)
NL = C["num_layers"]


def row(group, base, path, typ, expected=MISSING, absent=False, allowed=None, binary32=False):
    """One table row. base is 'C' or 'X'."""
    root = C if base == "C" else X
    v = get(root, path)
    full = f"{base}.{path}"
    if absent:
        check(group, f"{full} absent", v is MISSING, None if v is MISSING else v, "absent")
        return
    check(group, f"{full} present", v is not MISSING, None if v is MISSING else "present")
    if v is MISSING:
        return
    t = jtype(v)
    ok_t = (t == typ) or (typ == "number" and t in ("number", "integer"))
    check(group, f"{full} JSON type {typ}", ok_t, t, typ)
    if allowed is not None:
        check(group, f"{full} in enumeration", v in allowed, v, allowed)
    if binary32:
        check(group, f"{full} is exactly a binary32 value", f32(v) == v, v)
    if expected is not MISSING:
        check(group, f"{full} observed value", v == expected and jtype(v) == jtype(expected) or
              (typ == "number" and v == expected), v, expected)
    return v


# ---------------------------------------------------------------- §17.2
g = "17.2"
row(g, "C", "num_layers", "integer", 28)
row(g, "C", "hidden_size", "integer", 1024)
check(g, "C.attention is array", isinstance(A, list), jtype(A) if A is not MISSING else None)
check(g, "len(C.attention) == C.num_layers == 28", len(A) == NL == 28, len(A))
check(g, "X present (object)", isinstance(X, dict))
row(g, "X", "attention.num_q_heads", "integer", 16)
row(g, "X", "attention.num_kv_heads", "integer", 8)
row(g, "X", "attention.head_dim", "integer", 128)
for L, p in enumerate(A):
    gm = p.get("geometry", MISSING)
    check(g, f"C.attention[{L}].geometry present", isinstance(gm, dict))
    check(g, f"C.attention[{L}].geometry.head_dim == 128 (integer)",
          gm.get("head_dim") == 128 and jtype(gm.get("head_dim")) == "integer", gm.get("head_dim"))
    check(g, f"C.attention[{L}].geometry.num_kv_heads == 8 (integer)",
          gm.get("num_kv_heads") == 8 and jtype(gm.get("num_kv_heads")) == "integer", gm.get("num_kv_heads"))
    check(g, f"C.attention[{L}].geometry keys == {{head_dim, num_kv_heads}}",
          set(gm) == {"head_dim", "num_kv_heads"}, sorted(gm))
row(g, "X", "ffn.intermediate_size", "integer", 3072)
row(g, "X", "ffn.intermediate_size_by_layer", None, absent=True)
row(g, "X", "head.vocab_size", "integer", 151936)
row(g, "X", "context_length", "integer", 40960)

# upstream correspondences §17.2
check(g, "num_layers == upstream num_hidden_layers", C["num_layers"] == U["num_hidden_layers"],
      C["num_layers"], U["num_hidden_layers"])
check(g, "hidden_size == upstream hidden_size", C["hidden_size"] == U["hidden_size"])
check(g, "num_q_heads == upstream num_attention_heads", X["attention"]["num_q_heads"] == U["num_attention_heads"])
check(g, "X num_kv_heads == upstream num_key_value_heads", X["attention"]["num_kv_heads"] == U["num_key_value_heads"])
check(g, "X head_dim == upstream head_dim", X["attention"]["head_dim"] == U["head_dim"])
check(g, "intermediate_size == upstream intermediate_size", X["ffn"]["intermediate_size"] == U["intermediate_size"])
check(g, "vocab_size == upstream vocab_size", X["head"]["vocab_size"] == U["vocab_size"])
check(g, "context_length == upstream max_position_embeddings", X["context_length"] == U["max_position_embeddings"])

# cross-facts: index.json and shapes
check(g, "index.json.hidden_size == C.hidden_size", I["hidden_size"] == C["hidden_size"])
check(g, "index.json.num_layers == C.num_layers", I["num_layers"] == C["num_layers"])
check(g, "index.json.family == upstream model_type", I["family"] == U["model_type"], I["family"], U["model_type"])


def header(seg):
    with open(f"{CONTAINER}/{seg}", "rb") as fh:
        H = struct.unpack("<Q", fh.read(8))[0]
        return json.loads(fh.read(H))


hs = X["attention"]["head_dim"]
nq = X["attention"]["num_q_heads"]
nk = X["attention"]["num_kv_heads"]
hid = C["hidden_size"]
inter = X["ffn"]["intermediate_size"]
voc = X["head"]["vocab_size"]
expect_layer = {
    "self_attn.q_proj.weight": [nq * hs, hid],
    "self_attn.k_proj.weight": [nk * hs, hid],
    "self_attn.v_proj.weight": [nk * hs, hid],
    "self_attn.o_proj.weight": [hid, nq * hs],
    "self_attn.q_norm.weight": [hs],
    "self_attn.k_norm.weight": [hs],
    "mlp.gate_proj.weight": [inter, hid],
    "mlp.up_proj.weight": [inter, hid],
    "mlp.down_proj.weight": [hid, inter],
    "input_layernorm.weight": [hid],
    "post_attention_layernorm.weight": [hid],
}
for rep in ("target.decoder_stack@BF16", "target.decoder_stack@Q8_0"):
    hd = header(I["representations"][rep]["segment"])
    names = {t["name"]: t["shape"] for t in hd["tensors"]}
    layers = sorted({int(n.split(".")[0]) for n in names})
    check(g, f"{rep}: layer indices are 0..num_layers-1", layers == list(range(NL)), [layers[0], layers[-1], len(layers)])
    bad = []
    for L in range(NL):
        for suf, shp in expect_layer.items():
            n = f"{L}.{suf}"
            if names.get(n) != shp:
                bad.append((n, names.get(n), shp))
    check(g, f"{rep}: all 28x11 per-layer shapes match §17.2 formulas", not bad and len(names) == NL * 11,
          {"mismatches": bad[:5], "tensor_count": len(names)})
    biases = [n for n in names if "bias" in n]
    check("17.4", f"{rep}: no bias tensors in decoder stack", not biases, biases)
    qk = [L for L in range(NL) if f"{L}.self_attn.q_norm.weight" in names and f"{L}.self_attn.k_norm.weight" in names]
    check("17.4", f"{rep}: q_norm and k_norm present at all 28 layers", len(qk) == NL, len(qk))
for obj in ("target.embedding@BF16", "target.output_head@BF16"):
    hd = header(I["representations"][obj]["segment"])
    check(g, f"{obj} shape == [vocab_size, hidden_size]", hd["tensors"][0]["shape"] == [voc, hid], hd["tensors"][0]["shape"])
hd = header(I["representations"]["target.final_norm@BF16"]["segment"])
check(g, "target.final_norm shape == [hidden_size]", hd["tensors"][0]["shape"] == [hid], hd["tensors"][0]["shape"])

# ---------------------------------------------------------------- §17.3
g = "17.3"
EPS_EXP = 9.999999974752427e-7
for site in ("pre", "final_norm"):
    ns = get(X, f"norm.{site}")
    check(g, f"X.norm.{site} keys == {{kind, eps, weight_offset}}", isinstance(ns, dict) and set(ns) == {"kind", "eps", "weight_offset"},
          sorted(ns) if isinstance(ns, dict) else None)
    row(g, "X", f"norm.{site}.kind", "string", "rms_norm", allowed=["rms_norm", "layer_norm"])
    e = row(g, "X", f"norm.{site}.eps", "number", EPS_EXP)
    check(g, f"X.norm.{site}.eps == f64(f32(upstream rms_norm_eps))", e == f32(U["rms_norm_eps"]), e, f32(U["rms_norm_eps"]))
    check(g, f"X.norm.{site}.eps != upstream rms_norm_eps (binary64)", e != U["rms_norm_eps"], e, U["rms_norm_eps"])
    row(g, "X", f"norm.{site}.weight_offset", "number", 0.0, binary32=True)
check(g, "spec's stated eps value equals f64(f32(1e-6))", EPS_EXP == f32(1e-6), repr(f32(1e-6)))
check(g, "raw text: eps written as 9.999999974752427e-7 (serde shortest form) at both sites",
      raw_graph.count('"eps": 9.999999974752427e-7') == 2, raw_graph.count('"eps": 9.999999974752427e-7'))
row(g, "X", "norm.post", None, absent=True)
row(g, "X", "norm.placement", "string", "pre_only", allowed=["pre_only", "pre_post", "post_only", "pre_mixer"])
check(g, "X.norm keys subset of {pre, post, final_norm, placement}",
      set(X["norm"]) <= {"pre", "post", "final_norm", "placement"}, sorted(X["norm"]))

# ---------------------------------------------------------------- §17.4
g = "17.4"
check(g, "X.attention present", isinstance(X.get("attention"), dict))
ss = row(g, "X", "attention.score_scale", "number", 0.08838834764831845)
check(g, "score_scale == head_dim ** -0.5 (binary64 pow)", ss == math.pow(U["head_dim"], -0.5), ss, math.pow(U["head_dim"], -0.5))
check(g, "1/sqrt(128) == 0.08838834764831843", 1.0 / math.sqrt(128) == 0.08838834764831843, repr(1.0 / math.sqrt(128)))
check(g, "score_scale is 1 ulp above 1/sqrt(128)", ss == math.nextafter(1.0 / math.sqrt(128), 1.0), repr(ss))
check(g, "f32(score_scale) == f32(1/sqrt(128)) == 0.0883883461356163",
      f32(ss) == f32(1.0 / math.sqrt(128)) == 0.0883883461356163, repr(f32(ss)))
check(g, "upstream declares neither attention_multiplier nor query_pre_attn_scalar",
      "attention_multiplier" not in U and "query_pre_attn_scalar" not in U)
row(g, "X", "attention.query_scale", None, absent=True)
row(g, "X", "attention.logit_softcapping", None, absent=True)
ab = row(g, "X", "attention.attention_bias", "boolean", False)
check(g, "attention_bias == upstream attention_bias", ab is U["attention_bias"], ab, U["attention_bias"])
row(g, "X", "attention.qkv_bias", None, absent=True)
row(g, "X", "attention.qk_norm_scope", "string", "per_head", allowed=["per_head", "full_projection"])
row(g, "X", "attention.qk_norm_weight_offset", "number", 0.0, binary32=True)
pf = row(g, "X", "attention.parameter_free_qk_norm", "object", {"q": False, "k": False, "v": False})
check(g, "parameter_free_qk_norm keys subset of {q,k,v}, all boolean",
      set(pf) <= {"q", "k", "v"} and all(isinstance(v, bool) for v in pf.values()), pf)
row(g, "X", "attention.output_gate", None, absent=True)
row(g, "X", "attention.sinks", None, absent=True)

# ---------------------------------------------------------------- §17.5
g = "17.5"
POS_KINDS = ["rope", "linear", "llama3", "yarn", "partial_rope", "m_rope", "relative", "none"]
OPS = ["softmax", "gated_delta", "kda", "mamba2", "recurrent", "mla", "conv_qkv_attention"]
LISTED_POLICY = {"operator", "span", "window", "position", "geometry", "v_from_k", "declared_span"}
for L, p in enumerate(A):
    check(g, f"[{L}].operator == 'softmax'", p.get("operator") == "softmax" and p.get("operator") in OPS, p.get("operator"))
    check(g, f"[{L}].span == 'full'", p.get("span") == "full", p.get("span"))
    check(g, f"[{L}].window absent", "window" not in p, p.get("window"))
    pos = p.get("position", {})
    check(g, f"[{L}].position keys == {{kind, theta}}", set(pos) == {"kind", "theta"}, sorted(pos))
    check(g, f"[{L}].position.kind == 'rope'", pos.get("kind") == "rope" and pos.get("kind") in POS_KINDS, pos.get("kind"))
    th = pos.get("theta")
    check(g, f"[{L}].position.theta == upstream rope_theta (binary64, number)",
          jtype(th) in ("number", "integer") and float(th) == float(U["rope_theta"]) and th == 1000000.0, th, U["rope_theta"])
    check(g, f"[{L}].v_from_k absent or false", p.get("v_from_k", False) is False, p.get("v_from_k"))
    check(g, f"[{L}].declared_span absent", "declared_span" not in p)
    check(g, f"[{L}].geometry.head_dim == upstream head_dim", p["geometry"]["head_dim"] == U["head_dim"])
    check(g, f"[{L}].geometry.num_kv_heads == upstream num_key_value_heads",
          p["geometry"]["num_kv_heads"] == U["num_key_value_heads"])
    check(g, f"[{L}] keys subset of listed AttentionLayerPolicy keys", set(p) <= LISTED_POLICY, sorted(set(p) - LISTED_POLICY))
check(g, "raw text: 28 occurrences of '\"theta\": 1000000.0'", raw_graph.count('"theta": 1000000.0') == 28,
      raw_graph.count('"theta": 1000000.0'))
# writer resolution rules against upstream
check(g, "upstream: use_sliding_window false and sliding_window null -> rule 1 -> not sliding",
      U["use_sliding_window"] is False and U["sliding_window"] is None)
check(g, "upstream: no layer_types declared (declared_span absent consistent)", "layer_types" not in U)
check(g, "upstream rope_scaling null -> kind 'rope'", U["rope_scaling"] is None)
check(g, "upstream: no partial_rotary_factor / rope_parameters", "partial_rotary_factor" not in U and "rope_parameters" not in U)

# ---------------------------------------------------------------- §17.6
g = "17.6"
check(g, "X.ffn present", isinstance(X.get("ffn"), dict))
row(g, "X", "ffn.ffn_type", "string", "gated", allowed=["gated", "standard"])
act = row(g, "X", "ffn.activation", "string", "silu", allowed=["silu", "gelu", "gelu_tanh", "relu"])
ACTMAP = {"silu": "silu", "swish": "silu", "gelu": "gelu", "gelu_new": "gelu_tanh",
          "gelu_pytorch_tanh": "gelu_tanh", "relu": "relu"}
check(g, "activation == map(upstream hidden_act)", ACTMAP.get(U["hidden_act"].lower()) == act, act, U["hidden_act"])
row(g, "X", "ffn.gate_policy", "object", {"kind": "gated"})
row(g, "X", "ffn.moe", None, absent=True)
check(g, "X.head present", isinstance(X.get("head"), dict))
hre = row(g, "X", "head.head_reuses_embedding", "boolean", True)
check(g, "head_reuses_embedding consistent with upstream tie_word_embeddings (true unless exactly false)",
      hre == (U.get("tie_word_embeddings") is not False), hre, U.get("tie_word_embeddings"))
for k in ("embed_scale", "output_multiplier", "final_logit_softcapping", "embedding_norm"):
    row(g, "X", f"head.{k}", None, absent=True)
row(g, "X", "residual_topology", "object", {"kind": "single_stream"})
row(g, "X", "residual_scale", None, absent=True)
row(g, "X", "residual_in_fp32", None, absent=True)
for k in ("linear_attention", "kda", "kda_gate_lower_bound", "kda_gate_form", "kda_use_full_rank_gate",
          "mla", "mamba2", "conv_qkv"):
    row(g, "X", k, None, absent=True)
emb = I["representations"]["target.embedding@BF16"]["payload_sha256"]
oh = I["representations"]["target.output_head@BF16"]["payload_sha256"]
check("17.7", "tie: output_head@BF16 payload_sha256 == embedding@BF16 payload_sha256", emb == oh, oh, emb)
check("17.7", "both target.embedding and target.output_head objects present",
      "target.embedding@BF16" in I["representations"] and "target.output_head@BF16" in I["representations"])

# ---------------------------------------------------------------- coverage
g = "coverage"
LISTED_X = {
    "context_length", "attention", "ffn", "norm", "head", "residual_topology", "residual_scale", "residual_in_fp32",
    "attention.num_q_heads", "attention.num_kv_heads", "attention.head_dim", "attention.score_scale",
    "attention.query_scale", "attention.logit_softcapping", "attention.attention_bias", "attention.qkv_bias",
    "attention.qk_norm_scope", "attention.qk_norm_weight_offset", "attention.parameter_free_qk_norm",
    "attention.parameter_free_qk_norm.q", "attention.parameter_free_qk_norm.k", "attention.parameter_free_qk_norm.v",
    "attention.output_gate", "attention.sinks",
    "ffn.intermediate_size", "ffn.intermediate_size_by_layer", "ffn.ffn_type", "ffn.activation", "ffn.gate_policy",
    "ffn.gate_policy.kind", "ffn.moe",
    "norm.pre", "norm.post", "norm.final_norm", "norm.placement",
    "norm.pre.kind", "norm.pre.eps", "norm.pre.weight_offset",
    "norm.final_norm.kind", "norm.final_norm.eps", "norm.final_norm.weight_offset",
    "head.vocab_size", "head.head_reuses_embedding", "head.embed_scale", "head.output_multiplier",
    "head.final_logit_softcapping", "head.embedding_norm",
    "residual_topology.kind",
}
LISTED_L = {"operator", "span", "window", "position", "position.kind", "position.theta", "geometry",
            "geometry.head_dim", "geometry.num_kv_heads", "v_from_k", "declared_span"}


def walk(o, prefix=""):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{prefix}{k}"
            out.append(p)
            out += walk(v, p + ".")
    return out


present_x = walk(X)
present_l = sorted({p for pol in A for p in walk(pol)})
unlisted_x = [p for p in present_x if p not in LISTED_X]
unlisted_l = [p for p in present_l if p not in LISTED_L]
check(g, "every key present under X (recursive) is listed in §17", not unlisted_x,
      {"present": present_x, "unlisted": unlisted_x})
check(g, "every key present under any C.attention[L] (recursive) is listed in §17", not unlisted_l,
      {"present": present_l, "unlisted": unlisted_l})
check(g, "C keys (informative): id, role, source_artifact, num_layers, hidden_size, attention, execution",
      set(C) == {"id", "role", "source_artifact", "num_layers", "hidden_size", "attention", "execution"}, sorted(C))
# corrected draft, §17.1 C2: keys directly on C, and C.perception
ALLOWED_C = {"id", "role", "source_artifact", "num_layers", "hidden_size", "attention", "execution"}
check("17.1-C2", "no key directly on C outside the seven listed", set(C) <= ALLOWED_C, sorted(set(C) - ALLOWED_C))
check("17.1-C2", "C.perception absent", "perception" not in C)
check("17.1-C2", "C.role == 'primary_text'", C.get("role") == "primary_text", C.get("role"))
# every D2 key exists upstream
D2 = ["hidden_size", "intermediate_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads",
      "head_dim", "vocab_size", "hidden_act", "attention_bias", "rms_norm_eps", "rope_theta", "rope_scaling",
      "sliding_window", "use_sliding_window", "max_window_layers", "tie_word_embeddings"]
check("17.7", "D2 lists 16 fields, all present as keys in upstream config.json", len(D2) == 16 and all(k in U for k in D2),
      [k for k in D2 if k not in U])
UP_VALS = {"hidden_size": 1024, "intermediate_size": 3072, "num_hidden_layers": 28, "num_attention_heads": 16,
           "num_key_value_heads": 8, "head_dim": 128, "vocab_size": 151936, "hidden_act": "silu",
           "attention_bias": False, "rms_norm_eps": 1e-06, "rope_theta": 1000000, "rope_scaling": None,
           "sliding_window": None, "use_sliding_window": False, "max_window_layers": 28, "tie_word_embeddings": True}
for k, v in UP_VALS.items():
    check("17.7", f"§17.7 'Upstream value' column for {k} == config.json", U[k] == v and type(U[k]) == type(v), U[k], v)

npass = sum(r["pass"] for r in results)
nfail = len(results) - npass
summary = {"inputs": inputs, "assertions": len(results), "pass": npass, "fail": nfail,
           "by_group": {}, "failures": [r for r in results if not r["pass"]],
           "present_keys_X": present_x, "present_keys_attention_L": present_l}
for r in results:
    s = summary["by_group"].setdefault(r["group"], {"pass": 0, "fail": 0})
    s["pass" if r["pass"] else "fail"] += 1
json.dump({"summary": summary, "results": results}, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: summary[k] for k in ("inputs", "assertions", "pass", "fail", "by_group", "failures")}, indent=1, default=str))
sys.exit(1 if nfail else 0)
