"""Encoder attribution (development only, decision revision D15): how much of the Q8_0 drift from the BF16 reference is
LARQL's encoder, and how much is Q8_0 itself?

Reference-only: LARQL is not run here and no container is written. The baseline in runs/suite-v1 is read and never
changed. Four weight sets differ only in the Q8_0 tensors; the same f32 reference runs on each:

  L  LARQL's encoding: the container's bytes (truncated f16 scale, flushed below the f16 normal range);
  F  L with only the flushed blocks replaced by ggml's blocks: the flush fixed, the truncation kept;
  T  ggml's encoding with the blocks L flushes kept flushed: the truncation fixed, the flush kept;
  G  ggml's encoding: quantize_row_q8_0_ref compiled unmodified from the pinned source in inputs/.

Controls, each of which must hold for the results to mean anything:
  - a reimplementation of LARQL's encoder reproduces the container's Q8_0 bytes exactly;
  - ggml's C encoder and gguf-py's Q8_0 agree byte for byte on these weights;
  - the path used here, on L, reproduces the baseline decoded-Q8_0 reference logits bit for bit.

refcheck's reference_run accepts only the weight-source labels "upstream" and "container". It is called with "upstream"
because the "container" label asserts a container digest these weights do not have. For F, T and G that label is not the
weights' origin; the report says so, and the run records are not kept as evidence.

Run with the checker's pinned interpreter in isolated mode, after ggml_shim/build.sh:
  ../../checker/.venv/bin/python -I attribute_encoder.py [--cases a,b]
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import larql_verify as L  # noqa: E402  (also puts the vendored refcheck on sys.path)
import numpy as np  # noqa: E402
from gguf.quants import Q8_0 as GgufQ8  # noqa: E402
from refcheck import e1 as E1  # noqa: E402
from refcheck import gate as G  # noqa: E402
from refcheck import harness as H  # noqa: E402
from refcheck import metrics as M  # noqa: E402
from refcheck import q8_0 as Q8  # noqa: E402
from refcheck import t3 as T3  # noqa: E402

BASELINE = os.path.join(HERE, "runs", "suite-v1")
BLOCK = Q8.BLOCK_BYTES
GGML_SOURCE = "inputs/ggml-facdc44a67da17df4433adcc468b424f48e9ded2/src/ggml-quants.c"
ENCODERS = ("F", "T", "G")
CONTROL_CASES = ("short-2", "prose-en", "repetition")


def ggml_encoder():
    lib = ctypes.CDLL(os.path.join(HERE, "build", "libggmlq8ref.dylib"))
    f = lib.quantize_row_q8_0_ref
    f.restype = None
    f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64]

    def encode(x32):
        x = np.ascontiguousarray(x32, dtype=np.float32).reshape(-1)
        out = np.zeros(x.size // Q8.QK8_0 * BLOCK, dtype=np.uint8)
        f(x.ctypes.data, out.ctypes.data, x.size)
        return out.tobytes()

    return encode


def larql_encoder_reimplemented(x32):
    """crates/larql-models/src/quant/ggml/quantize.rs:50-74 with half.rs:43-60: scale = amax/127, inv = 1/scale in f32,
    scale stored by truncating the mantissa and flushing below the f16 normal range, codes round(x*inv) clamped."""
    x = np.asarray(x32, dtype=np.float32).reshape(-1, Q8.QK8_0)
    d = np.abs(x).max(axis=1) / np.float32(127)
    with np.errstate(divide="ignore"):
        inv = np.where(d > 0, np.float32(1) / d, np.float32(0)).astype(np.float32)
    v = x * inv[:, None]
    q = np.clip(np.sign(v) * np.floor(np.abs(v) + np.float32(0.5)), -128, 127).astype(np.int8)
    bits = d.view(np.uint32)
    e16 = ((bits >> 23) & 0xFF).astype(np.int32) - 127 + 15
    d16 = np.where(e16 <= 0, 0, (e16.clip(0, 30) << 10) | ((bits & 0x7FFFFF) >> 13)).astype(np.uint16)
    out = np.empty((x.shape[0], BLOCK), dtype=np.uint8)
    out[:, :2] = d16.astype("<u2").reshape(-1, 1).view(np.uint8)
    out[:, 2:] = q.view(np.uint8)
    return out.tobytes()


def build_weight_sets(ctx, W, Wu):
    """The encodings of every Q8_0 tensor, their weight-level statistics, and the encoder controls."""
    encode_ggml = ggml_encoder()
    sets = {e: dict(W) for e in ENCODERS}
    stats = {e: {"elements_over_t2": 0, "blocks_over_t2": 0, "zero_scale_blocks": 0, "worst_error_over_t2_bound": 0.0,
                 "max_abs_error": 0.0, "sum_err2": 0.0} for e in ("L",) + ENCODERS}
    sum_ref2 = 0.0
    controls = {"larql_reimplementation_tensors_differing": [], "ggml_c_vs_gguf_py_tensors_differing": [],
                "n_q8_tensors": 0, "n_blocks": 0, "n_blocks_flushed_by_larql": 0, "n_blocks_codes_differ_l_vs_g": 0,
                "n_blocks_scale_differs_l_vs_g": 0}
    for k in H.container_quantised_keys(ctx.c):
        x32 = Wu[k]
        raw_l = ctx.c.read_bytes(ctx.c.hf_key_map()[k])
        controls["n_q8_tensors"] += 1
        if larql_encoder_reimplemented(x32) != raw_l:
            controls["larql_reimplementation_tensors_differing"].append(k)
        raw_g = encode_ggml(x32)
        if GgufQ8.quantize_blocks(np.asarray(x32, dtype=np.float32).reshape(-1, Q8.QK8_0)).tobytes() != raw_g:
            controls["ggml_c_vs_gguf_py_tensors_differing"].append(k)
        bl = np.frombuffer(raw_l, dtype=np.uint8).reshape(-1, BLOCK)
        bg = np.frombuffer(raw_g, dtype=np.uint8).reshape(-1, BLOCK)
        flushed = E1.block_scales_f64(raw_l) == 0
        controls["n_blocks"] += bl.shape[0]
        controls["n_blocks_flushed_by_larql"] += int(flushed.sum())
        controls["n_blocks_codes_differ_l_vs_g"] += int((bl[:, 2:] != bg[:, 2:]).any(axis=1).sum())
        controls["n_blocks_scale_differs_l_vs_g"] += int((bl[:, :2] != bg[:, :2]).any(axis=1).sum())
        bf = bl.copy()
        bf[flushed] = bg[flushed]
        bt = bg.copy()
        bt[flushed] = bl[flushed]
        raws = {"L": raw_l, "F": bf.tobytes(), "T": bt.tobytes(), "G": raw_g}
        x = np.asarray(x32, dtype=np.float64).reshape(-1, Q8.QK8_0)
        sum_ref2 += float((x * x).sum())
        for e, raw in raws.items():
            dec32 = Q8.dequantize_q8_0(raw)
            if e != "L":
                sets[e][k] = dec32.reshape(x32.shape)
            d = E1.block_scales_f64(raw)
            bound = E1.t2_bound_from_scale(d)[:, None]
            err = np.abs(x - dec32.astype(np.float64).reshape(x.shape))
            over = err > bound
            s = stats[e]
            s["elements_over_t2"] += int(over.sum())
            s["blocks_over_t2"] += int(over.any(axis=1).sum())
            s["zero_scale_blocks"] += int((d == 0).sum())
            s["worst_error_over_t2_bound"] = max(s["worst_error_over_t2_bound"], float((err / bound).max()))
            s["max_abs_error"] = max(s["max_abs_error"], float(err.max()))
            s["sum_err2"] += float((err * err).sum())
    for s in stats.values():
        s["rel_frobenius_all_q8"] = (s.pop("sum_err2") / sum_ref2) ** 0.5
    return sets, stats, controls


def reference(ctx, weights, ids):
    res = H.reference_run(None, weights, ids, "f32", "upstream", upstream_files=ctx.files, authority=ctx.auth)
    gate = G.evaluate_gate(ctx.cmp_, res.record, subject=True)
    if not gate.comparable or res.logits is None:
        raise RuntimeError(f"reference not comparable: {gate.status} {gate.reasons} {gate.errors}")
    return res.logits


def sha256_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def pooled(per_case):
    """Across cases, position-weighted."""
    n = sum(c["n"] for c in per_case.values())
    return {
        "n_positions": n,
        "max_abs_diff_max": max(c["max_abs_diff_max"] for c in per_case.values()),
        "rms_diff_mean": sum(c["rms_diff_mean"] * c["n"] for c in per_case.values()) / n,
        "kl_mean": sum(c["kl_mean"] * c["n"] for c in per_case.values()) / n,
        "kl_max": max(c["kl_max"] for c in per_case.values()),
        "n_top1_disagree": sum(c["n_top1_disagree"] for c in per_case.values()),
    }


def compact(summary):
    h = L.headline(summary)
    return {"n": h["n_comparable_positions"], "max_abs_diff_max": h["max_abs_diff_max"],
            "max_abs_diff_median": h["max_abs_diff_median"], "rms_diff_mean": h["rms_diff_mean"], "kl_mean": h["kl_mean"],
            "kl_max": h["kl_max"], "n_top1_disagree": h["n_top1_disagree"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="")
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "attribution-v1"))
    a = ap.parse_args()
    out_dir = os.path.abspath(a.out)
    os.makedirs(out_dir, exist_ok=True)
    baseline = json.load(open(os.path.join(BASELINE, "report.json")))
    cases = [c for c in baseline["cases"] if not a.cases or c in a.cases.split(",")]

    report = L.base_report("larql-verify-dev-encoder-attribution/1")
    report.update(baseline=os.path.relpath(BASELINE, HERE), ggml_source=GGML_SOURCE,
                  weight_source_label_note="reference_run was called with the label 'upstream' for every weight set; "
                                           "for L, F, T and G that label is not the weights' origin",
                  cases={})
    ctx, fail = L.preflight(report)
    if fail:
        raise SystemExit(f"preflight: {fail}")
    W = H.container_weights(ctx.c)
    Wu = H.load_upstream(L.SNAPSHOT)
    t = time.perf_counter()
    sets, weight_stats, controls = build_weight_sets(ctx, W, Wu)
    report.update(weights=weight_stats, encoder_controls=controls)
    print(f"[{L.now()}] encodings built in {time.perf_counter() - t:.0f}s: {json.dumps(controls)}", flush=True)
    print(json.dumps(weight_stats, indent=1), flush=True)
    if controls["larql_reimplementation_tensors_differing"] or controls["ggml_c_vs_gguf_py_tensors_differing"]:
        L.write_json(os.path.join(out_dir, "report.json"), report)
        raise SystemExit("an encoder control failed; nothing further is meaningful")
    del Wu
    gc.collect()

    logit_controls = {}
    totals = {e: {} for e in ("L",) + ENCODERS}
    deltas = {e: {} for e in ENCODERS}
    for cid in cases:
        base = os.path.join(BASELINE, cid)
        with open(os.path.join(base, "tokens.json")) as f:
            m = json.load(f)
        ids = m["token_ids"]
        if T3.token_ids_sha256(ids) != m["token_ids_sha256"]:
            raise SystemExit(f"{cid}: token manifest does not match its digest")
        R_u = np.load(os.path.join(base, "ref_bf16_f32.npy"))
        R_l = np.load(os.path.join(base, "ref_q8_0_f32.npy"))
        run_dir = os.path.join(out_dir, cid)
        os.makedirs(run_dir, exist_ok=True)
        if cid in CONTROL_CASES:
            logit_controls[cid] = sha256_array(reference(ctx, W, ids)) == sha256_array(R_l)
            print(f"[{L.now()}] {cid} control: path on L reproduces the baseline: {logit_controls[cid]}", flush=True)
            if not logit_controls[cid]:
                report["logit_controls"] = logit_controls
                L.write_json(os.path.join(out_dir, "report.json"), report)
                raise SystemExit("the logit control failed; nothing further is meaningful")
        s_l = M.compare(R_u, R_l)
        kl_l = np.array([p["kl"] for p in s_l["positions"]])
        top_u = R_u.argmax(axis=1)
        top_l = R_l.argmax(axis=1)
        crep = {"n_tokens": len(ids), "vs_bf16": {"L": compact(s_l["summary"])},
                "top1_positions_vs_bf16": {"L": np.where(top_l != top_u)[0].tolist()}, "vs_l": {}}
        totals["L"][cid] = crep["vs_bf16"]["L"]
        for e in ENCODERS:
            R_e = reference(ctx, sets[e], ids)
            np.save(os.path.join(run_dir, f"ref_{e}_f32.npy"), R_e)
            s_e = M.compare(R_u, R_e)
            kl_e = np.array([p["kl"] for p in s_e["positions"]])
            crep["vs_bf16"][e] = compact(s_e["summary"])
            crep["vs_bf16"][e]["n_positions_kl_lower_than_L"] = int((kl_e < kl_l).sum())
            crep["vs_bf16"][e]["kl_ratio_to_L_median"] = float(np.median(kl_e / kl_l))
            crep["top1_positions_vs_bf16"][e] = np.where(R_e.argmax(axis=1) != top_u)[0].tolist()
            crep["vs_l"][e] = compact(M.compare(R_l, R_e)["summary"])
            totals[e][cid] = crep["vs_bf16"][e]
            deltas[e][cid] = crep["vs_l"][e]
            print(f"[{L.now()}] {cid} {e}: KL mean {crep['vs_bf16'][e]['kl_mean']:.4g} (L {crep['vs_bf16']['L']['kl_mean']:.4g}), "
                  f"top-1 {crep['vs_bf16'][e]['n_top1_disagree']} (L {crep['vs_bf16']['L']['n_top1_disagree']})", flush=True)
            del R_e
            gc.collect()
        report["cases"][cid] = crep
        L.write_json(os.path.join(run_dir, "summary.json"), crep)
    report["logit_controls"] = logit_controls
    report["pooled_vs_bf16"] = {e: pooled(v) for e, v in totals.items()}
    report["pooled_vs_l"] = {e: pooled(v) for e, v in deltas.items()}
    report["verdict"] = "MEASURED"
    L.write_json(os.path.join(out_dir, "report.json"), report)
    print(json.dumps({"controls": controls, "logit_controls": logit_controls, "weights": weight_stats,
                      "pooled_vs_bf16": report["pooled_vs_bf16"], "pooled_vs_l": report["pooled_vs_l"]}, indent=1))


if __name__ == "__main__":
    main()
