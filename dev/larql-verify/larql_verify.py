"""larql-verify: one real model through the complete verifier (development only, decision revision D15).

Nothing this produces is blind acceptance evidence for LARQL-VERIFY-001. Ingestion here is `content_valid` only, never
`execution_authenticated`: this runner is not independently controlled Phase 3 custody.

Two commands:

  report   one model, one report: E1 once, then E2, E3 and the f64 diagnostic for every case of a prompt suite.
  compare  one case, the first N tokens of the snapshot's LICENSE: E2 and E3 only (the diagnostic ladder).

Stages:
  1. identities: upstream snapshot (pinned hashes), container (per-file hashes from evidence/L1), LARQL executable;
  2. container integrity: the validating reader, digests checked;
  3. configuration: pinned config.json against the container (the D2/D7 comparator and gate);
  E1 (report only): every executed tensor of the container against the BF16 checkpoint. Q8_0 tensors are a lossy
     reconstruction, reported against the T2 bound; unquantised tensors are exact storage, reported as bit identity;
  per case:
  4. reference on the decoded Q8_0 weights (E2 side) and on the BF16 checkpoint (E3 side), f32;
  5. LARQL production-q8 through refcheck.ingest (run, verify, extract);
  6. E2 (LARQL vs reference on the same decoded weights), E3 (LARQL vs the BF16 reference), and, for context only,
     the reference-only quantisation drift (decoded-Q8_0 reference vs BF16 reference);
  7. f64 diagnostic (report only): a native-f64 reference on the decoded Q8_0 weights, and how far LARQL and the f32
     reference each are from it. Descriptive only: no threshold, and T3 is not used.

Verdict: MEASURED, INCOMPLETE or EXECUTION_ERROR. No thresholds.

Run with the checker's pinned interpreter in isolated mode:
  ../../checker/.venv/bin/python -I larql_verify.py report
  ../../checker/.venv/bin/python -I larql_verify.py compare --n-tokens 16
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REFCHECK_COMMIT = "e505afc"
VENDOR = os.path.join(HERE, "vendor", f"refcheck-{REFCHECK_COMMIT}")
sys.path.insert(0, VENDOR)

import numpy as np  # noqa: E402

from refcheck import config_compare as CC  # noqa: E402
from refcheck import container as C  # noqa: E402
from refcheck import e1 as E1  # noqa: E402
from refcheck import gate as G  # noqa: E402
from refcheck import harness as H  # noqa: E402
from refcheck import ingest as I  # noqa: E402
from refcheck import metrics as M  # noqa: E402
from refcheck import q8_0 as Q8  # noqa: E402
from refcheck import t3 as T3  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SNAPSHOT = os.path.expanduser(
    "~/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca")
CONTAINER = os.path.expanduser("~/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3")
CONTAINER_HASHES = os.path.join(REPO, "evidence", "L1", "container-q8_0.sha256")
LARQL = os.path.expanduser("~/chris-source/larql-l1-2536bb79/target/release/larql")
LARQL_COMMIT = "2536bb79b199b1115445678e3e82c400b0b3fd07"
L1_BASELINE_BINARY_SHA256 = "4d80dd42c4b50dd83c35d4a3c2d273e12a95d31dd4816c51ca2323dfc8462322"
TEXT_SOURCE = "LICENSE"  # a pinned file of the upstream snapshot; the token ladder uses nested prefixes of it
DEFAULT_SUITE = os.path.join(HERE, "prompts", "suite-v1.json")

MEASURED, INCOMPLETE, EXECUTION_ERROR = "MEASURED", "INCOMPLETE", "EXECUTION_ERROR"
_SEVERITY = {MEASURED: 0, INCOMPLETE: 1, EXECUTION_ERROR: 2}

# No development overrides. DO-1 (the `representation:` line) was retired when the checker moved to e505afc
# (D15 clarification 1); refcheck.ingest is used exactly as pinned.
DEV_OVERRIDES_APPLIED: list = []

DESIGNATION = ("DEVELOPMENT ONLY (D15). Not blind acceptance evidence for LARQL-VERIFY-001. "
               "Ingestion is content_valid only, not execution_authenticated.")
KL_DIRECTION = ("D_KL(P_reference || P_candidate), nats; candidate is LARQL (E2, E3, f64 LARQL) or the f32 reference "
                "(drift: decoded-Q8_0 against BF16; f64 ref32: f32 against f64)")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return dt.datetime.now().strftime("%H:%M:%S")


def check_container_files(root, listing):
    """Every file in the L1 hash list, and no other regular file."""
    want = {}
    with open(listing) as f:
        for line in f:
            digest, name = line.split(None, 1)
            want[os.path.normpath(name.strip())] = digest
    have = {}
    for d, _, files in os.walk(root):
        for fn in files:
            have[os.path.relpath(os.path.join(d, fn), root)] = None
    problems = [f"missing {k}" for k in want if k not in have]
    problems += [f"unexpected {k}" for k in have if k not in want]
    for k, digest in want.items():
        if k in have and sha256_file(os.path.join(root, k)) != digest:
            problems.append(f"sha256 mismatch {k}")
    return {"files": len(want), "problems": problems, "ok": not problems}


def tokenizer():
    from tokenizers import Tokenizer

    return Tokenizer.from_file(os.path.join(SNAPSHOT, "tokenizer.json"))


def token_ids(n):
    with open(os.path.join(SNAPSHOT, TEXT_SOURCE), encoding="utf-8") as f:
        ids = tokenizer().encode(f.read(), add_special_tokens=False).ids
    if len(ids) < n:
        raise SystemExit(f"{TEXT_SOURCE} gives only {len(ids)} tokens; {n} requested")
    return [int(t) for t in ids[:n]]


def case_token_ids(case):
    """Token ids of one suite case: a snapshot-file prefix, or the case's text (repeated if it says so)."""
    if "source" in case:
        if case["source"] != TEXT_SOURCE:
            raise SystemExit(f"case {case['id']}: unknown source {case['source']!r}")
        return token_ids(int(case["n_tokens"]))
    text = case.get("separator", "").join([case["text"]] * int(case.get("repeat", 1)))
    ids = [int(t) for t in tokenizer().encode(text, add_special_tokens=False).ids]
    if not ids:
        raise SystemExit(f"case {case['id']}: no tokens")
    return ids


def headline(summary):
    """The four numbers per comparison, taken from metrics.aggregate."""
    if summary is None or summary.get("aggregate_status") != M.AGGREGATE_COMPUTED:
        return None
    return {
        "max_abs_diff_max": summary["max_abs_diff"]["max"],
        "max_abs_diff_median": summary["max_abs_diff"].get("q0.5"),
        "rms_diff_max": summary["rms_diff"]["max"],
        "rms_diff_mean": summary["rms_diff"]["mean"],
        "kl_max": summary["kl"]["max"],
        "kl_mean": summary["kl"]["mean"],
        "top1_agreement": summary["top1_agreement"],
        "n_top1_disagree": summary["n_top1_disagree"],
        "n_comparable_positions": summary["n_comparable_positions"],
        "non_comparable_indices": summary["non_comparable_indices"],
    }


def stage(report, name, **fields):
    report["stages"][name] = fields
    tag = report.get("case_id") or (f"n={report['n_tokens']}" if "n_tokens" in report else "preflight")
    print(f"[{now()}] {tag} {name}: {fields.get('status')}", flush=True)


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=str)


# --------------------------------------------------------------------------------------------------------------------
# Preflight: identities, container integrity, configuration. Shared by both commands.

class Context:
    """What every case needs, established once: the verified identities, the open container, the authority and the
    configuration comparison."""

    files = c = auth = cmp_ = exe_sha = container_digest = None


def preflight(report):
    """Stages 1 to 3. Returns (Context, None) or (None, (verdict, reason))."""
    ctx = Context()
    try:
        ctx.files = H.verify_snapshot(SNAPSHOT)
        snap = {"status": "verified", "files": len(ctx.files)}
    except Exception as e:  # noqa: BLE001
        snap = {"status": "failed", "error": str(e)}
    cont = check_container_files(CONTAINER, CONTAINER_HASHES)
    ctx.exe_sha = sha256_file(LARQL) if os.path.exists(LARQL) else None
    ctx.container_digest = H.container_sha256(CONTAINER)
    stage(report, "identities",
          status="verified" if snap["status"] == "verified" and cont["ok"] and ctx.exe_sha else "failed",
          snapshot=snap, container_files=cont, container_sha256=ctx.container_digest,
          executable={"path": LARQL, "sha256": ctx.exe_sha, "larql_commit": LARQL_COMMIT,
                      "matches_l1_baseline_binary": ctx.exe_sha == L1_BASELINE_BINARY_SHA256})
    if report["stages"]["identities"]["status"] != "verified":
        return None, (INCOMPLETE, "an identity check failed")

    try:
        ctx.c = C.open_container(CONTAINER)
        stage(report, "container_integrity", status="verified", warnings=[str(w) for w in ctx.c.warnings],
              quantised_tensors=len(H.container_quantised_keys(ctx.c)), executed_tensors=len(ctx.c.hf_key_map()))
    except Exception as e:  # noqa: BLE001
        stage(report, "container_integrity", status="failed", error=repr(e))
        return None, (INCOMPLETE, "the container reader refused the container")

    ctx.auth = CC.Authority.pinned(os.path.join(SNAPSHOT, "config.json"))
    ctx.cmp_ = CC.compare_configuration(CC.evidence_from_container(CONTAINER), ctx.auth, subject=True)
    stage(report, "configuration", status=ctx.cmp_["status"], reasons=ctx.cmp_.get("reasons", []),
          mismatched_fields=ctx.cmp_.get("mismatched_fields"), unresolved_fields=ctx.cmp_.get("unresolved_fields"),
          unresolved_assumptions=ctx.cmp_.get("unresolved_assumptions"))
    if ctx.cmp_["status"] != CC.COMPARABLE:
        return None, (INCOMPLETE, "configuration not comparable")
    return ctx, None


# --------------------------------------------------------------------------------------------------------------------
# E1: weight reconstruction, once per model.

def _quantiles(values):
    v = np.asarray([x for x in values if x is not None], dtype=np.float64)
    if not v.size:
        return None
    return {"min": float(v.min()), "median": float(np.median(v)), "max": float(v.max())}


def t2_attribution(ctx, Wu):
    """Where the T2 exceedances come from. T2 is derived from ggml's reference encoder, and PROTOCOL.md records that it
    is expected to be exceeded because LARQL's encoder truncates the f16 scale and flushes below the f16 normal range to
    zero. This splits the measured exceedances by stored-scale class, and applies T2 to a counterfactual: the same
    weights through a ggml-style encoder (d = amax/127 in f32, q = roundf(x/d), d stored round-to-nearest-even f16).
    The counterfactual is simulated here; it is not a run of ggml and it does not change any weight used elsewhere."""
    out = {"zero_scale": {"blocks": 0, "blocks_over_t2": 0, "elements_over_t2": 0, "max_amax": 0.0},
           "nonzero_scale": {"blocks": 0, "blocks_over_t2": 0, "elements_over_t2": 0, "worst_error_over_t2_bound": 0.0},
           "ggml_style_counterfactual": {"blocks_over_t2": 0, "elements_over_t2": 0, "zero_scale_blocks": 0,
                                         "worst_error_over_t2_bound": 0.0}}
    z, nz, cf = out["zero_scale"], out["nonzero_scale"], out["ggml_style_counterfactual"]
    for k, r in ctx.c.hf_key_map().items():
        if r.dtype != "Q8_0":
            continue
        raw = ctx.c.read_bytes(r)
        x32 = Wu[k].astype(np.float32).reshape(-1, Q8.QK8_0)
        x = x32.astype(np.float64)
        d = E1.block_scales_f64(raw)
        bound = E1.t2_bound_from_scale(d)[:, None]
        err = np.abs(x - Q8.dequantize_q8_0(raw).astype(np.float64).reshape(x.shape))
        over = err > bound
        zero = d == 0
        z["blocks"] += int(zero.sum())
        z["blocks_over_t2"] += int(over[zero].any(axis=1).sum())
        z["elements_over_t2"] += int(over[zero].sum())
        if zero.any():
            z["max_amax"] = max(z["max_amax"], float(np.abs(x[zero]).max()))
        nz["blocks"] += int((~zero).sum())
        nz["blocks_over_t2"] += int(over[~zero].any(axis=1).sum())
        nz["elements_over_t2"] += int(over[~zero].sum())
        if (~zero).any():
            nz["worst_error_over_t2_bound"] = max(nz["worst_error_over_t2_bound"],
                                                  float((err[~zero] / bound[~zero]).max()))
        d32 = np.abs(x32).max(axis=1) / np.float32(127)
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = np.where(d32 > 0, np.float32(1) / d32, np.float32(0)).astype(np.float32)
        v = x32 * inv[:, None]
        q = np.clip(np.sign(v) * np.floor(np.abs(v) + np.float32(0.5)), -128, 127)
        d16 = d32.astype(np.float16).astype(np.float64)
        b16 = E1.t2_bound_from_scale(d16)[:, None]
        e16 = np.abs(x - q.astype(np.float64) * d16[:, None])
        cf["blocks_over_t2"] += int((e16 > b16).any(axis=1).sum())
        cf["elements_over_t2"] += int((e16 > b16).sum())
        cf["zero_scale_blocks"] += int((d16 == 0).sum())
        cf["worst_error_over_t2_bound"] = max(cf["worst_error_over_t2_bound"], float((e16 / b16).max()))
    return out


def run_e1(ctx, Wu, out_dir):
    """refcheck.e1.e1_report over every executed tensor; the full report is written to e1.json, a summary returned."""
    t = time.perf_counter()
    rep = E1.e1_report(ctx.c, lambda k: Wu[k], {k: tuple(v.shape) for k, v in Wu.items()})
    with open(os.path.join(out_dir, "e1.json"), "w") as f:
        f.write(E1.canonical_json(rep))
    tens = rep["tensors"]
    q = {k: v for k, v in tens.items() if v["dtype"] == "Q8_0"}
    u = {k: v for k, v in tens.items() if v["dtype"] != "Q8_0"}
    tot = rep["total"]
    worst_rel = max(q.items(), key=lambda kv: kv[1]["rel_frobenius"] or 0.0, default=(None, None))
    unq_dtypes = {}
    for v in u.values():
        unq_dtypes[v["dtype"]] = unq_dtypes.get(v["dtype"], 0) + 1
    summary = {
        "status": "measured" if rep["coverage"]["ok"] else "coverage_problem",
        "seconds": round(time.perf_counter() - t, 1),
        "coverage": rep["coverage"],
        "upstream_nonfinite": tot["n_upstream_nonfinite"],
        "lossy_q8_0": {
            "what": "Q8_0 reconstruction of BF16 weights: lossy by design, reported against T2, which PROTOCOL.md expects "
                    "this encoder to exceed (a model-acceptability finding; the bound is not widened)",
            "n_tensors": len(q),
            "max_abs_error": tot["max_abs_error"],
            "worst_error_over_t2_bound": tot["worst_ratio"],
            "n_elements_exceeding_t2": tot["n_exceed_t2"],
            "n_blocks_exceeding_t2": tot["n_blocks_exceed_t2"],
            "zero_scale_blocks": tot["zero_scale_blocks"],
            "rel_frobenius": _quantiles(v["rel_frobenius"] for v in q.values()),
            "worst_rel_frobenius_tensor": worst_rel[0],
            "n_tensors_bit_identical": sum(bool(v["bit_identical"]) for v in q.values()),
            "decode_matches_gguf_py": tot.get("gguf_all_bit_identical"),
            "t2_attribution": t2_attribution(ctx, Wu),
        },
        "exact_storage": {
            "what": "tensors the container stores unquantised: expected bit-identical to the checkpoint",
            "n_tensors": len(u),
            "dtypes": unq_dtypes,
            "all_bit_identical": tot["unquantised_all_bit_identical"],
            "not_bit_identical": sorted(k for k, v in u.items() if not v["bit_identical"]),
        },
        "full_report": "e1.json",
    }
    return summary


# --------------------------------------------------------------------------------------------------------------------
# One case: E2, E3, drift and (optionally) the f64 diagnostic.

def _logsoftmax64(x):
    m = x.max(axis=1, keepdims=True)
    z = x - m
    return z - np.log(np.exp(z).sum(axis=1, keepdims=True))


def _distance_from_f64(r64, lr64, x):
    """Per-position distances of an f32 logit array `x` from the f64 reference, all in binary64."""
    x64 = np.asarray(x, dtype=np.float64)
    d = x64 - r64
    max_abs = np.abs(d).max(axis=1)
    rms = np.sqrt((d * d).mean(axis=1))
    kl = (np.exp(lr64) * (lr64 - _logsoftmax64(x64))).sum(axis=1)
    top1 = np.argmax(x64, axis=1) == np.argmax(r64, axis=1)
    return max_abs, {
        "max_abs_diff": {"max": float(max_abs.max()), "median": float(np.median(max_abs))},
        "rms_diff_mean": float(rms.mean()),
        "kl": {"mean": float(kl.mean()), "max": float(kl.max())},
        "n_top1_disagree": int(np.count_nonzero(~top1)),
    }


def f64_diagnostic(ref64, ref32, larql):
    """How far LARQL and the f32 reference (both on the decoded Q8_0 weights) each sit from a native-f64 reference on
    the same weights. Computed here in binary64, because refcheck.metrics compares float32 arrays only. KL is
    D(P_f64 || P_x). Per position, the ratio is max|LARQL - f64| / max|ref32 - f64|. Descriptive only: no threshold."""
    r64 = np.asarray(ref64, dtype=np.float64)
    lr64 = _logsoftmax64(r64)
    eL, larql_d = _distance_from_f64(r64, lr64, larql)
    eR, ref32_d = _distance_from_f64(r64, lr64, ref32)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(eR > 0, eL / eR, np.where(eL > 0, np.inf, 1.0))
    fin = ratio[np.isfinite(ratio)]
    return {
        "larql_vs_f64": larql_d,
        "ref32_vs_f64": ref32_d,
        "ratio_larql_over_ref32": {
            "median": float(np.median(fin)) if fin.size else None,
            "max": float(fin.max()) if fin.size else None,
            "n_positions_larql_further": int(np.count_nonzero(eL > eR)),
            "n_positions": int(eL.size),
            "n_infinite": int(np.count_nonzero(~np.isfinite(ratio))),
        },
        "per_position_max_abs": {"larql": eL.tolist(), "ref32": eR.tolist()},
    }


def measure_case(ctx, report, ids, run_dir, W, Wu, f64):
    """Stages 4 to 7 for one token sequence. Writes into `report`; returns (verdict, reason)."""
    n = len(ids)
    manifest = {"token_ids": ids, "token_ids_sha256": T3.token_ids_sha256(ids)}
    report["token_ids_sha256"] = manifest["token_ids_sha256"]
    write_json(os.path.join(run_dir, "tokens.json"), manifest)
    qkeys = H.container_quantised_keys(ctx.c)

    # 4a. reference on the decoded container (E2 side)
    t = time.perf_counter()
    ref_q = H.reference_run(None, W, ids, "f32", "container", container_root=CONTAINER,
                            quantised_tensors=qkeys, authority=ctx.auth)
    gate_q = G.evaluate_gate(ctx.cmp_, ref_q.record, subject=True)
    stage(report, "reference_decoded_q8_0", status=gate_q.status, reasons=gate_q.reasons, errors=gate_q.errors,
          seconds=round(time.perf_counter() - t, 1))
    if gate_q.status == G.CHECKER_ERROR:
        return EXECUTION_ERROR, "the reference on the decoded weights raised a checker error"
    if not gate_q.comparable or ref_q.logits is None:
        return INCOMPLETE, "the decoded-weights reference is not comparable"
    np.save(os.path.join(run_dir, "ref_q8_0_f32.npy"), ref_q.logits)

    # 5. LARQL through the admitted ingestion path
    dump = os.path.join(run_dir, "larql.f32")
    t = time.perf_counter()
    rec = I.run(LARQL, CONTAINER, manifest, dump, timeout=3600)
    larql_seconds = round(time.perf_counter() - t, 1)
    if rec.get("exit_status") != 0 or rec.get("timed_out") or rec.get("launch_error"):
        stage(report, "larql_execution", status="failed", exit_status=rec.get("exit_status"),
              timed_out=rec.get("timed_out"), launch_error=rec.get("launch_error"),
              stderr_tail=(rec.get("stderr") or "")[-4000:], seconds=larql_seconds)
        return EXECUTION_ERROR, "LARQL did not complete"
    stage(report, "larql_execution", status="completed", seconds=larql_seconds,
          projection_plans=rec.get("stdout_lines", {}).get("projection_plans"),
          record=os.path.join(run_dir, "larql.run.json"))
    res = I.verify_and_extract(rec, dump, os.path.join(run_dir, "larql.meta.json"), manifest, ctx.container_digest,
                               list(range(n)), I.configuration_from_reference(ref_q.record),
                               expected_executable_sha256=ctx.exe_sha)
    binding = I.check_ingested(res["logits"], res["candidate_record"], res["positions"]) if res["status"] == "accepted" else None
    stage(report, "ingestion", status=res["status"], reasons=res.get("reasons"), error=res.get("error"),
          binding_problems=binding, property="content_valid" if res["status"] == "accepted" and not binding else None,
          execution_authenticated=False, dev_overrides=list(DEV_OVERRIDES_APPLIED))
    if res["status"] == "checker_error":
        return EXECUTION_ERROR, "ingestion raised a checker error"
    if res["status"] != "accepted" or binding:
        return INCOMPLETE, "ingestion refused the run"
    larql = res["logits"]

    # 6a. E2
    e2 = G.gated_compare(gate_q, ref_q.logits, larql)
    stage(report, "E2", status=e2["status"], reasons=e2.get("reasons"),
          headline=headline(e2.get("metrics", {}).get("summary")), summary=e2.get("metrics", {}).get("summary"),
          per_position=e2.get("metrics", {}).get("positions"))

    # 4b. reference on the BF16 checkpoint (E3 side)
    t = time.perf_counter()
    ref_u = H.reference_run(None, Wu, ids, "f32", "upstream", upstream_files=ctx.files, authority=ctx.auth)
    gate_u = G.evaluate_gate(ctx.cmp_, ref_u.record, subject=True)
    stage(report, "reference_bf16", status=gate_u.status, reasons=gate_u.reasons, errors=gate_u.errors,
          seconds=round(time.perf_counter() - t, 1))
    if gate_u.comparable and ref_u.logits is not None:
        np.save(os.path.join(run_dir, "ref_bf16_f32.npy"), ref_u.logits)
        e3 = G.gated_compare(gate_u, ref_u.logits, larql)
        stage(report, "E3", status=e3["status"], reasons=e3.get("reasons"),
              headline=headline(e3.get("metrics", {}).get("summary")), summary=e3.get("metrics", {}).get("summary"))
        drift = M.compare(ref_u.logits, ref_q.logits)
        stage(report, "reference_quantisation_drift", status="computed", note="context only: no LARQL involved",
              headline=headline(drift["summary"]), summary=drift["summary"])
    else:
        stage(report, "E3", status="not_computed", reasons=["the BF16 reference is not comparable"])
    del ref_u
    gc.collect()

    # 7. f64 diagnostic on the decoded weights
    if f64:
        t = time.perf_counter()
        ref64 = H.reference_run(None, W, ids, "f64", "container", f64_mode="native", container_root=CONTAINER,
                                quantised_tensors=qkeys, authority=ctx.auth)
        gate64 = G.evaluate_gate(ctx.cmp_, ref64.record, subject=True)
        secs = round(time.perf_counter() - t, 1)
        if gate64.comparable and ref64.logits is not None:
            np.save(os.path.join(run_dir, "ref_q8_0_f64.npy"), ref64.logits)
            stage(report, "f64_diagnostic", status="computed", seconds=secs, gate=gate64.status,
                  logits_dtype=str(np.asarray(ref64.logits).dtype),
                  note="diagnostic only: no threshold, T3 not used; native-f64 reference on the decoded Q8_0 weights",
                  **f64_diagnostic(ref64.logits, ref_q.logits, larql))
        else:
            stage(report, "f64_diagnostic", status="not_computed", seconds=secs, gate=gate64.status,
                  reasons=gate64.reasons, errors=gate64.errors)
        del ref64
        gc.collect()

    if e2["status"] != G.COMPARABLE:
        return INCOMPLETE, "E2 could not be computed"
    if report["stages"]["E3"]["status"] != G.COMPARABLE:
        return INCOMPLETE, "E2 measured; E3 could not be computed"
    if f64 and report["stages"]["f64_diagnostic"]["status"] != "computed":
        return INCOMPLETE, "E2 and E3 measured; the f64 diagnostic could not be computed"
    return MEASURED, "E2, E3 and the f64 diagnostic measured" if f64 else "E2 and E3 measured"


def base_report(schema):
    return {
        "schema": schema,
        "designation": DESIGNATION,
        "created": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version()},
        "refcheck": json.load(open(os.path.join(VENDOR, "PIN.json"))),
        "kl_direction": KL_DIRECTION,
        "stages": {},
        "verdict": None,
    }


# --------------------------------------------------------------------------------------------------------------------
# compare: one LICENSE-prefix case, E2 and E3 (the diagnostic ladder; behaviour unchanged).

def compare(n, out_root):
    run_dir = os.path.join(out_root, f"n{n:04d}")
    os.makedirs(run_dir, exist_ok=True)
    report = base_report("larql-verify-dev-report/1")
    report.update(n_tokens=n, text_source=f"upstream snapshot {TEXT_SOURCE}, first {n} tokens, no special tokens")

    def finish(verdict, why):
        report["verdict"], report["verdict_reason"] = verdict, why
        write_json(os.path.join(run_dir, "report.json"), report)
        print_case(report)
        return report

    ctx, fail = preflight(report)
    if fail:
        return finish(*fail)
    W = H.container_weights(ctx.c)
    Wu = H.load_upstream(SNAPSHOT)
    return finish(*measure_case(ctx, report, token_ids(n), run_dir, W, Wu, f64=False))


# --------------------------------------------------------------------------------------------------------------------
# report: one model, one report.

def suite_report(suite_path, out_root, only, f64):
    with open(suite_path, "rb") as f:
        raw = f.read()
    suite = json.loads(raw)
    cases = [c for c in suite["cases"] if not only or c["id"] in only]
    if only and len(cases) != len(only):
        raise SystemExit(f"unknown case id(s): {sorted(set(only) - {c['id'] for c in suite['cases']})}")
    out_dir = os.path.join(out_root, suite["suite"])
    os.makedirs(out_dir, exist_ok=True)

    report = base_report("larql-verify-dev-suite-report/1")
    report.update(suite={"path": os.path.relpath(suite_path, HERE), "sha256": hashlib.sha256(raw).hexdigest(),
                         "name": suite["suite"], "cases_run": [c["id"] for c in cases]},
                  f64_diagnostic=f64, cases={})

    def finish(verdict, why):
        report["verdict"], report["verdict_reason"] = verdict, why
        write_json(os.path.join(out_dir, "report.json"), report)
        with open(os.path.join(out_dir, "REPORT.md"), "w") as f:
            f.write(render_markdown(report))
        print_suite(report)
        return report

    ctx, fail = preflight(report)
    if fail:
        return finish(*fail)
    W = H.container_weights(ctx.c)
    Wu = H.load_upstream(SNAPSHOT)

    try:
        report["e1"] = run_e1(ctx, Wu, out_dir)
    except Exception as e:  # noqa: BLE001
        report["e1"] = {"status": "checker_error", "error": repr(e)}
    print(f"[{now()}] E1: {report['e1']['status']}", flush=True)

    for case in cases:
        cid = case["id"]
        run_dir = os.path.join(out_dir, cid)
        os.makedirs(run_dir, exist_ok=True)
        ids = case_token_ids(case)
        crep = {"case_id": cid, "kind": case["kind"], "purpose": case["purpose"], "n_tokens": len(ids),
                "stages": {}}
        try:
            verdict, why = measure_case(ctx, crep, ids, run_dir, W, Wu, f64)
        except Exception as e:  # noqa: BLE001
            verdict, why = EXECUTION_ERROR, f"unexpected error: {e!r}"
        crep["verdict"], crep["verdict_reason"] = verdict, why
        write_json(os.path.join(run_dir, "report.json"), crep)
        report["cases"][cid] = case_summary(crep)
        print(f"[{now()}] {cid}: {verdict} ({why})", flush=True)
        gc.collect()

    verdicts = [c["verdict"] for c in report["cases"].values()]
    worst = max(verdicts, key=_SEVERITY.get, default=MEASURED)
    if report["e1"].get("status") != "measured" and worst == MEASURED:
        worst = INCOMPLETE if report["e1"].get("status") == "coverage_problem" else EXECUTION_ERROR
    why = {MEASURED: "E1 and every case measured",
           INCOMPLETE: "at least one stage could not be measured",
           EXECUTION_ERROR: "at least one stage failed to execute"}[worst]
    return finish(worst, why)


def case_summary(crep):
    s = crep["stages"]
    out = {"kind": crep["kind"], "n_tokens": crep["n_tokens"], "verdict": crep["verdict"],
           "verdict_reason": crep["verdict_reason"], "token_ids_sha256": crep.get("token_ids_sha256"),
           "ingestion": s.get("ingestion", {}).get("status"),
           "larql_seconds": s.get("larql_execution", {}).get("seconds")}
    for k in ("E2", "E3", "reference_quantisation_drift"):
        out[k] = s.get(k, {}).get("headline")
    f = s.get("f64_diagnostic")
    if f and f.get("status") == "computed":
        out["f64"] = {k: f[k] for k in ("larql_vs_f64", "ref32_vs_f64", "ratio_larql_over_ref32")}
    elif f:
        out["f64"] = {"status": f.get("status")}
    return out


# --------------------------------------------------------------------------------------------------------------------
# Output.

def fmt(x, p=3):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{p}g}"
    return str(x)


def print_case(r):
    s = r["stages"]

    def st(k):
        return s.get(k, {}).get("status", "not reached")

    print()
    print(f"larql-verify compare  (n_tokens={r['n_tokens']}, DEVELOPMENT ONLY, D15)")
    print(f"  Identities:               {st('identities')}")
    print(f"  Container integrity:      {st('container_integrity')}")
    print(f"  Configuration:            {st('configuration')}")
    print(f"  Reference (decoded Q8_0): {st('reference_decoded_q8_0')}")
    print(f"  LARQL execution:          {st('larql_execution')}")
    dov = [o["id"] for o in s.get("ingestion", {}).get("dev_overrides") or []]
    print(f"  Ingestion:                {st('ingestion')}  (content_valid only; not execution_authenticated)"
          + (f"  dev overrides: {', '.join(dov)}" if dov else ""))
    for k, label in (("E2", "E2  LARQL vs reference, same decoded weights"),
                     ("E3", "E3  LARQL vs reference, BF16 checkpoint"),
                     ("reference_quantisation_drift", "ctx reference Q8_0 vs reference BF16 (no LARQL)")):
        h = s.get(k, {}).get("headline")
        if h:
            print(f"  {label}")
            print(f"      max |dlogit|: {fmt(h['max_abs_diff_max'], 6)}   RMS (mean over positions): {fmt(h['rms_diff_mean'], 6)}")
            print(f"      KL ref||cand mean / max: {fmt(h['kl_mean'], 6)} / {fmt(h['kl_max'], 6)} nats")
            print(f"      top-1 agreement: {fmt(h['top1_agreement'], 6)} ({h['n_top1_disagree']} disagree of "
                  f"{h['n_comparable_positions']}); non-comparable positions: {h['non_comparable_indices']}")
    print(f"  Verdict: {r['verdict']}  ({r['verdict_reason']})")


def table_rows(r):
    rows = []
    for cid, c in r["cases"].items():
        e2, e3, dr = c.get("E2") or {}, c.get("E3") or {}, c.get("reference_quantisation_drift") or {}
        f = c.get("f64") or {}
        lf, rf = f.get("larql_vs_f64") or {}, f.get("ref32_vs_f64") or {}
        ratio = f.get("ratio_larql_over_ref32") or {}
        rows.append([
            cid, c["kind"], str(c["n_tokens"]), c["verdict"],
            fmt(e2.get("max_abs_diff_max")), fmt(e2.get("rms_diff_mean")), fmt(e2.get("kl_max")),
            f"{e2['n_top1_disagree']}" if e2 else "n/a",
            fmt(e3.get("max_abs_diff_max")), fmt(e3.get("kl_max")),
            f"{e3['n_top1_disagree']}/{dr['n_top1_disagree']}" if e3 and dr else "n/a",
            fmt((lf.get("max_abs_diff") or {}).get("max")), fmt((rf.get("max_abs_diff") or {}).get("max")),
            fmt(ratio.get("median"), 2),
        ])
    return rows


TABLE_HEAD = ["case", "kind", "n", "verdict",
              "E2 max|Δ|", "E2 RMS", "E2 KL max", "E2 top-1 ≠",
              "E3 max|Δ|", "E3 KL max", "E3/drift top-1 ≠",
              "f64: LARQL max|Δ|", "f64: ref32 max|Δ|", "f64 ratio med"]


def e1_lines(e):
    if not e or e.get("status") not in ("measured", "coverage_problem"):
        return [f"E1: {e.get('status') if e else 'not run'} {e.get('error', '') if e else ''}"]
    q, x = e["lossy_q8_0"], e["exact_storage"]
    rf = q["rel_frobenius"] or {}
    a = q["t2_attribution"]
    c = a["ggml_style_counterfactual"]
    return [
        f"E1 coverage: {'complete' if e['coverage']['ok'] else e['coverage']}",
        f"E1 Q8_0 (lossy, {q['n_tensors']} tensors): max |Δw| {fmt(q['max_abs_error'])}, worst error / T2 bound "
        f"{fmt(q['worst_error_over_t2_bound'])}, elements over T2 {q['n_elements_exceeding_t2']}, "
        f"rel. Frobenius min/median/max {fmt(rf.get('min'))} / {fmt(rf.get('median'))} / {fmt(rf.get('max'))} "
        f"(worst {q['worst_rel_frobenius_tensor']}), decode = gguf-py: {q['decode_matches_gguf_py']}",
        f"E1 T2 by cause: zero-scale (flushed) blocks {a['zero_scale']['blocks']} with {a['zero_scale']['elements_over_t2']} "
        f"elements over, max amax {fmt(a['zero_scale']['max_amax'])}; non-zero-scale blocks over "
        f"{a['nonzero_scale']['blocks_over_t2']} of {a['nonzero_scale']['blocks']} with "
        f"{a['nonzero_scale']['elements_over_t2']} elements over, worst ratio {fmt(a['nonzero_scale']['worst_error_over_t2_bound'])}",
        f"E1 T2 counterfactual, ggml-style encoder on the same weights: {c['elements_over_t2']} elements over, "
        f"worst ratio {fmt(c['worst_error_over_t2_bound'])}, {c['zero_scale_blocks']} zero-scale blocks",
        f"E1 exact storage ({x['n_tensors']} tensors, {x['dtypes']}): all bit-identical: {x['all_bit_identical']}"
        + (f"; not identical: {x['not_bit_identical']}" if x["not_bit_identical"] else ""),
    ]


def print_suite(r):
    s = r["stages"]
    print()
    print(f"larql-verify report  (suite {r['suite']['name']}, DEVELOPMENT ONLY, D15)")
    for k in ("identities", "container_integrity", "configuration"):
        print(f"  {k}: {s.get(k, {}).get('status', 'not reached')}")
    for ln in e1_lines(r.get("e1")):
        print("  " + ln)
    rows = table_rows(r)
    if rows:
        w = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(TABLE_HEAD)]
        print("  " + "  ".join(h.ljust(w[i]) for i, h in enumerate(TABLE_HEAD)))
        for row in rows:
            print("  " + "  ".join(v.ljust(w[i]) for i, v in enumerate(row)))
    print(f"  Verdict: {r['verdict']}  ({r['verdict_reason']})")


def render_markdown(r):
    s = r["stages"]
    out = [f"# larql-verify report: {r['suite']['name']}", "",
           f"**{r['designation']}**", "",
           f"- Created: {r['created']}",
           f"- refcheck: `{r['refcheck']['checker_commit']}`; LARQL `{LARQL_COMMIT[:8]}`, binary "
           f"`{(s.get('identities', {}).get('executable') or {}).get('sha256', 'n/a')}`",
           f"- Suite: `{r['suite']['path']}` sha256 `{r['suite']['sha256']}`",
           f"- KL: {r['kl_direction']}",
           f"- Verdict: **{r['verdict']}** ({r['verdict_reason']})", ""]
    out += ["## Preflight", ""] + [f"- {k}: {s.get(k, {}).get('status', 'not reached')}"
                                   for k in ("identities", "container_integrity", "configuration")] + [""]
    out += ["## E1: weight reconstruction", ""] + [f"- {ln}" for ln in e1_lines(r.get("e1"))] + [""]
    out += ["## Per case: E2, E3 and the f64 diagnostic", "",
            "E2: LARQL against the f32 reference on the same decoded Q8_0 weights. E3: LARQL against the f32 reference "
            "on the BF16 checkpoint; drift is the same comparison with the decoded-Q8_0 reference in LARQL's place. "
            "f64: max |Δlogit| of LARQL and of the f32 reference from a native-f64 reference on the decoded weights; "
            "the ratio is per position, LARQL's distance over the f32 reference's, median over positions.", ""]
    rows = table_rows(r)
    out.append("| " + " | ".join(TABLE_HEAD) + " |")
    out.append("|" + "---|" * len(TABLE_HEAD))
    out += ["| " + " | ".join(row) + " |" for row in rows]
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(prog="larql-verify")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("compare", help="one LICENSE-prefix case, E2 and E3")
    p.add_argument("--n-tokens", type=int, required=True)
    p.add_argument("--out", default=os.path.join(HERE, "runs"))
    p = sub.add_parser("report", help="one model, one report: E1, then E2, E3 and f64 for every suite case")
    p.add_argument("--suite", default=DEFAULT_SUITE)
    p.add_argument("--cases", default="", help="comma-separated case ids (default: all)")
    p.add_argument("--no-f64", action="store_true", help="skip the f64 diagnostic")
    p.add_argument("--out", default=os.path.join(HERE, "runs"))
    a = ap.parse_args()
    if a.cmd == "compare":
        r = compare(a.n_tokens, os.path.abspath(a.out))
    else:
        only = [x for x in a.cases.split(",") if x]
        r = suite_report(os.path.abspath(a.suite), os.path.abspath(a.out), only, not a.no_f64)
    sys.exit(0 if r["verdict"] == MEASURED else 1)


if __name__ == "__main__":
    main()
