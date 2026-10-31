"""AMB-022 negative controls (independent reviewer). Runs the extracted checker 310c174 read-back on stand-in configs.
Mode S: reference built from X, authority X (the production path, harness.reference_run).
Mode C: reference built from BASE, authority X (does the comparison catch a reference/authority difference?)."""
import sys, json, copy
CK = sys.argv[1]; PINNED = sys.argv[2]
sys.path.insert(0, CK)
import numpy as np, torch
from refcheck import harness, d7, pins as P, config_compare as CC, readback

pinned = json.load(open(PINNED))
BASE = dict(pinned, hidden_size=64, intermediate_size=128, num_hidden_layers=4, num_attention_heads=4,
            num_key_value_heads=2, head_dim=16, vocab_size=256, max_window_layers=4)

def weights(cfg):
    rng = np.random.default_rng(0); h, i, v = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    q, kv, hd = cfg["num_attention_heads"], cfg["num_key_value_heads"], cfg["head_dim"]
    w = {"model.embed_tokens.weight": (v, h), "model.norm.weight": (h,)}
    for L in range(cfg["num_hidden_layers"]):
        p = f"model.layers.{L}."
        w.update({p+"self_attn.q_proj.weight": (q*hd, h), p+"self_attn.k_proj.weight": (kv*hd, h), p+"self_attn.v_proj.weight": (kv*hd, h),
                  p+"self_attn.o_proj.weight": (h, q*hd), p+"self_attn.q_norm.weight": (hd,), p+"self_attn.k_norm.weight": (hd,),
                  p+"mlp.gate_proj.weight": (i, h), p+"mlp.up_proj.weight": (i, h), p+"mlp.down_proj.weight": (h, i),
                  p+"input_layernorm.weight": (h,), p+"post_attention_layernorm.weight": (h,)})
        if cfg.get("attention_bias"):
            for n, s in (("q", q*hd), ("k", kv*hd), ("v", kv*hd), ("o", h)):
                w[p+f"self_attn.{n}_proj.bias"] = (s,)
    out = {k: rng.standard_normal(s).astype(np.float32) for k, s in w.items()}
    if not cfg.get("tie_word_embeddings", False):
        out["lm_head.weight"] = rng.standard_normal((v, h)).astype(np.float32)
    return out

def run(build_cfg, auth_cfg):
    auth = CC.Authority.synthetic_standin(json.dumps(auth_cfg), "AMB-022 audit negative control (independent reviewer)")
    try:
        with P.pinned_runtime("f32"):
            model, info = harness.build_model(build_cfg, weights(build_cfg), "f32", "native")
            rec = d7.assess_reference(model, auth, "f32", "native", info)
    except Exception as e:
        return "refused", [f"{type(e).__name__}: {e}"[:220]]
    return rec["status"], [r[:220] for r in rec["reasons"]]

def mod(**kw):
    c = copy.deepcopy(BASE)
    for k, v in kw.items():
        if v is DEL: c.pop(k, None)
        else: c[k] = v
    return c
DEL = object()

CONTROLS = [
    ("baseline (no change)", {}),
    ("rope_scaling linear (non-default rope_type)", {"rope_scaling": {"rope_type": "linear", "factor": 2.0}}),
    ("rope_scaling dict without type ({'factor': 2.0})", {"rope_scaling": {"factor": 2.0}}),
    ("extra rope_parameters key (partial_rotary_factor 0.5)", {"partial_rotary_factor": 0.5}),
    ("rope_parameters given directly, default, other theta", {"rope_parameters": {"rope_type": "default", "rope_theta": 10000.0}}),
    ("rope_theta changed (10000)", {"rope_theta": 10000}),
    ("rope_theta absent", {"rope_theta": DEL}),
    ("rope_scaling absent", {"rope_scaling": DEL}),
    ("use_sliding_window true, sliding_window 8, mwl 2", {"use_sliding_window": True, "sliding_window": 8, "max_window_layers": 2}),
    ("use_sliding_window false, sliding_window 8 (inert)", {"sliding_window": 8}),
    ("use_sliding_window absent", {"use_sliding_window": DEL}),
    ("max_window_layers changed (2), window null (inert)", {"max_window_layers": 2}),
    ("layer_types declared, layer 2 sliding, window null", {"layer_types": ["full_attention", "full_attention", "sliding_attention", "full_attention"]}),
    ("layer_types declared, all full (matches resolution)", {"layer_types": ["full_attention"] * 4}),
    ("attention_dropout 0.1", {"attention_dropout": 0.1}),
    ("attention_dropout absent", {"attention_dropout": DEL}),
    ("pad_token_id 5", {"pad_token_id": 5}),
    ("initializer_range 0.5", {"initializer_range": 0.5}),
    ("rms_norm_eps 1e-5", {"rms_norm_eps": 1e-5}),
    ("rms_norm_eps 1.0000000000000001e-6 (same binary64)", {"rms_norm_eps": 1.0000000000000001e-6}),
    ("hidden_act gelu", {"hidden_act": "gelu"}),
    ("attention_bias true", {"attention_bias": True}),
    ("tie_word_embeddings false", {"tie_word_embeddings": False}),
    ("head split 8x8 instead of 4x16 (same products)", {"num_attention_heads": 8, "num_key_value_heads": 4, "head_dim": 8}),
    ("unknown key attention_multiplier 0.5", {"attention_multiplier": 0.5}),
    ("unknown key query_pre_attn_scalar 64", {"query_pre_attn_scalar": 64}),
    ("chunk_size_feed_forward 4 (fixed key)", {"chunk_size_feed_forward": 4}),
    ("architectures LlamaForCausalLM (ignored key)", {"architectures": ["LlamaForCausalLM"]}),
    ("torch_dtype float32 (dtype -> pin)", {"torch_dtype": "float32"}),
    ("max_position_embeddings 128", {"max_position_embeddings": 128}),
    ("use_cache false", {"use_cache": False}),
    ("generation key temperature 0.7", {"temperature": 0.7}),
]

rows = []
for name, kw in CONTROLS:
    X = mod(**kw)
    s = run(X, X)
    c = run(BASE, X) if kw else ("n/a", [])
    rows.append({"control": name, "self": s, "cross": c})
    print(json.dumps(rows[-1]))
