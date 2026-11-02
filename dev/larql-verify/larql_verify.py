"""larql-verify compare: one real model through the complete verifier (development only, decision revision D15).

Nothing this produces is blind acceptance evidence for LARQL-VERIFY-001. Ingestion here is `content_valid` only, never
`execution_authenticated`: this runner is not independently controlled Phase 3 custody.

Stages:
  1. identities: upstream snapshot (pinned hashes), container (per-file hashes from evidence/L1), LARQL executable;
  2. container integrity: the validating reader, digests checked;
  3. configuration: pinned config.json against the container (the D2/D7 comparator and gate);
  4. reference on the decoded Q8_0 weights (E2 side) and on the BF16 checkpoint (E3 side), f32;
  5. LARQL production-q8 through refcheck.ingest (run, verify, extract);
  6. metrics: E2 (LARQL vs reference on the same decoded weights), E3 (LARQL vs the BF16 reference), and, for
     context only, the reference-only quantisation drift (decoded-Q8_0 reference vs BF16 reference).

Verdict: MEASURED, INCOMPLETE or EXECUTION_ERROR. No thresholds; T3 is not used.

Run with the checker's pinned interpreter in isolated mode:
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
from refcheck import gate as G  # noqa: E402
from refcheck import harness as H  # noqa: E402
from refcheck import ingest as I  # noqa: E402
from refcheck import metrics as M  # noqa: E402
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

MEASURED, INCOMPLETE, EXECUTION_ERROR = "MEASURED", "INCOMPLETE", "EXECUTION_ERROR"

# No development overrides. DO-1 (the `representation:` line) was retired when the checker moved to e505afc
# (D15 clarification 1); refcheck.ingest is used exactly as pinned.
DEV_OVERRIDES_APPLIED: list = []


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


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


def token_ids(n):
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(os.path.join(SNAPSHOT, "tokenizer.json"))
    with open(os.path.join(SNAPSHOT, TEXT_SOURCE), encoding="utf-8") as f:
        ids = tok.encode(f.read(), add_special_tokens=False).ids
    if len(ids) < n:
        raise SystemExit(f"{TEXT_SOURCE} gives only {len(ids)} tokens; {n} requested")
    return [int(t) for t in ids[:n]]


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
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {name}: {fields.get('status')}", flush=True)


def compare(n, out_root):
    run_dir = os.path.join(out_root, f"n{n:04d}")
    os.makedirs(run_dir, exist_ok=True)
    report = {
        "schema": "larql-verify-dev-report/1",
        "designation": "DEVELOPMENT ONLY (D15). Not blind acceptance evidence for LARQL-VERIFY-001. "
                       "Ingestion is content_valid only, not execution_authenticated.",
        "created": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version()},
        "refcheck": json.load(open(os.path.join(VENDOR, "PIN.json"))),
        "n_tokens": n,
        "text_source": f"upstream snapshot {TEXT_SOURCE}, first {n} tokens, no special tokens",
        "kl_direction": "D_KL(P_reference || P_candidate), nats; candidate is LARQL (E2, E3) or the decoded-Q8_0 reference (drift)",
        "stages": {},
        "verdict": None,
    }

    def finish(verdict, why):
        report["verdict"] = verdict
        report["verdict_reason"] = why
        with open(os.path.join(run_dir, "report.json"), "w") as f:
            json.dump(report, f, indent=2, sort_keys=True, default=str)
        print_summary(report)
        return report

    # 1. identities
    try:
        files = H.verify_snapshot(SNAPSHOT)
        snap = {"status": "verified", "files": len(files)}
    except Exception as e:  # noqa: BLE001
        snap = {"status": "failed", "error": str(e)}
    cont = check_container_files(CONTAINER, CONTAINER_HASHES)
    exe_sha = sha256_file(LARQL) if os.path.exists(LARQL) else None
    container_digest = H.container_sha256(CONTAINER)
    stage(report, "identities",
          status="verified" if snap["status"] == "verified" and cont["ok"] and exe_sha else "failed",
          snapshot=snap, container_files=cont, container_sha256=container_digest,
          executable={"path": LARQL, "sha256": exe_sha, "larql_commit": LARQL_COMMIT,
                      "matches_l1_baseline_binary": exe_sha == L1_BASELINE_BINARY_SHA256})
    if report["stages"]["identities"]["status"] != "verified":
        return finish(INCOMPLETE, "an identity check failed")

    # 2. container integrity
    try:
        c = C.open_container(CONTAINER)
        stage(report, "container_integrity", status="verified", warnings=[str(w) for w in c.warnings],
              quantised_tensors=len(H.container_quantised_keys(c)), executed_tensors=len(c.hf_key_map()))
    except Exception as e:  # noqa: BLE001
        stage(report, "container_integrity", status="failed", error=repr(e))
        return finish(INCOMPLETE, "the container reader refused the container")

    # 3. configuration
    auth = CC.Authority.pinned(os.path.join(SNAPSHOT, "config.json"))
    cmp_ = CC.compare_configuration(CC.evidence_from_container(CONTAINER), auth, subject=True)
    stage(report, "configuration", status=cmp_["status"], reasons=cmp_.get("reasons", []),
          mismatched_fields=cmp_.get("mismatched_fields"), unresolved_fields=cmp_.get("unresolved_fields"),
          unresolved_assumptions=cmp_.get("unresolved_assumptions"))
    if cmp_["status"] != CC.COMPARABLE:
        return finish(INCOMPLETE, "configuration not comparable")

    ids = token_ids(n)
    manifest = {"token_ids": ids, "token_ids_sha256": T3.token_ids_sha256(ids)}
    report["token_ids_sha256"] = manifest["token_ids_sha256"]
    with open(os.path.join(run_dir, "tokens.json"), "w") as f:
        json.dump(manifest, f)

    # 4a. reference on the decoded container (E2 side)
    t = time.perf_counter()
    W = H.container_weights(c)
    ref_q = H.reference_run(None, W, ids, "f32", "container", container_root=CONTAINER,
                            quantised_tensors=H.container_quantised_keys(c), authority=auth)
    del W
    gc.collect()
    gate_q = G.evaluate_gate(cmp_, ref_q.record, subject=True)
    stage(report, "reference_decoded_q8_0", status=gate_q.status, reasons=gate_q.reasons, errors=gate_q.errors,
          seconds=round(time.perf_counter() - t, 1))
    if gate_q.status == G.CHECKER_ERROR:
        return finish(EXECUTION_ERROR, "the reference on the decoded weights raised a checker error")
    if not gate_q.comparable or ref_q.logits is None:
        return finish(INCOMPLETE, "the decoded-weights reference is not comparable")
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
        return finish(EXECUTION_ERROR, "LARQL did not complete")
    stage(report, "larql_execution", status="completed", seconds=larql_seconds,
          projection_plans=rec.get("stdout_lines", {}).get("projection_plans"),
          record=os.path.join(run_dir, "larql.run.json"))
    res = I.verify_and_extract(rec, dump, os.path.join(run_dir, "larql.meta.json"), manifest, container_digest,
                               list(range(n)), I.configuration_from_reference(ref_q.record),
                               expected_executable_sha256=exe_sha)
    binding = I.check_ingested(res["logits"], res["candidate_record"], res["positions"]) if res["status"] == "accepted" else None
    stage(report, "ingestion", status=res["status"], reasons=res.get("reasons"), error=res.get("error"),
          binding_problems=binding, property="content_valid" if res["status"] == "accepted" and not binding else None,
          execution_authenticated=False, dev_overrides=list(DEV_OVERRIDES_APPLIED))
    if res["status"] == "checker_error":
        return finish(EXECUTION_ERROR, "ingestion raised a checker error")
    if res["status"] != "accepted" or binding:
        return finish(INCOMPLETE, "ingestion refused the run")
    larql = res["logits"]

    # 6a. E2
    e2 = G.gated_compare(gate_q, ref_q.logits, larql)
    stage(report, "E2", status=e2["status"], reasons=e2.get("reasons"),
          headline=headline(e2.get("metrics", {}).get("summary")), summary=e2.get("metrics", {}).get("summary"),
          per_position=e2.get("metrics", {}).get("positions"))

    # 4b. reference on the BF16 checkpoint (E3 side)
    t = time.perf_counter()
    Wu = H.load_upstream(SNAPSHOT)
    ref_u = H.reference_run(None, Wu, ids, "f32", "upstream", upstream_files=files, authority=auth)
    del Wu
    gc.collect()
    gate_u = G.evaluate_gate(cmp_, ref_u.record, subject=True)
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

    if e2["status"] != G.COMPARABLE:
        return finish(INCOMPLETE, "E2 could not be computed")
    if report["stages"]["E3"]["status"] != G.COMPARABLE:
        return finish(INCOMPLETE, "E2 measured; E3 could not be computed")
    return finish(MEASURED, "E2 and E3 measured")


def fmt(x):
    return "n/a" if x is None else (f"{x:.6g}" if isinstance(x, float) else str(x))


def print_summary(r):
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
            print(f"      max |dlogit|: {fmt(h['max_abs_diff_max'])}   RMS (mean over positions): {fmt(h['rms_diff_mean'])}")
            print(f"      KL ref||cand mean / max: {fmt(h['kl_mean'])} / {fmt(h['kl_max'])} nats")
            print(f"      top-1 agreement: {fmt(h['top1_agreement'])} ({h['n_top1_disagree']} disagree of "
                  f"{h['n_comparable_positions']}); non-comparable positions: {h['non_comparable_indices']}")
    print(f"  Verdict: {r['verdict']}  ({r['verdict_reason']})")


def main():
    ap = argparse.ArgumentParser(prog="larql-verify")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("compare")
    p.add_argument("--n-tokens", type=int, required=True)
    p.add_argument("--out", default=os.path.join(HERE, "runs"))
    a = ap.parse_args()
    r = compare(a.n_tokens, os.path.abspath(a.out))
    sys.exit(0 if r["verdict"] == MEASURED else 1)


if __name__ == "__main__":
    main()
