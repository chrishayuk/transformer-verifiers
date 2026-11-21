"""NCP-001 Phase 3: one candidate, one evaluation, on the hidden set. Rules are in PROTOCOL.md and don't change after results.

  final.py <candidate id> <out.json> [wall clock limit in seconds, default 24 hours] [--resume]

Pausable and resumable. `touch ~/chris-models/ncp001/PAUSE` stops it at the next stage or block-pair boundary (never mid-measurement)
and it continues when the file is removed. Paused time doesn't count against the wall clock limit. After a stop, a crash or a
signal, `--resume` skips every completed stage and continues the benchmark after the last recorded block pair. It refuses if the
candidate, the binaries, or the workload changed since the run began. Resume never changes a verdict rule or a score.

An infrastructure failure or a timeout is `inconclusive`, never a verdict about the kernel. A crash counts against the
candidate only if the baseline survives the same command. <out.json> is rewritten after each stage.
"""
import json, os, re, shutil, signal, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate as E  # noqa: E402
import numpy as np

H, PLAIN = E.H, E.PLAIN
W = f"{H}/hidden/workload"
S = E.SCRATCH


class Infrastructure(Exception):
    pass


def exec_run(binary, ids, logits, *more):
    return E.sh([binary, "vindex3", "exec", E.C8, "--backend", "production-q8", "--representation-source", "stored", "--tokens", ",".join(map(str, ids)), "--logit-dump", logits, *more], PLAIN)


def outcome(r):
    k = r.get("kernel_default_threads")
    if r["failures"]:
        return "rejected"
    if r.get("infrastructure_error") or not k or k["blocks_not_quiet"]:
        return "inconclusive"
    if k["improvement"] >= 0.10 and k["ci95_improvement"][0] > 0:
        return "success"
    if k["ci95_improvement"][1] < 0.10:
        return "no_improvement"
    return "inconclusive"


def run(r, cid, save):
    hb, lb, base_h, base_l = f"{H}/bin/harness-{cid}", f"{H}/bin/larql-{cid}", f"{H}/bin/harness-baseline", f"{H}/bin/larql-baseline"
    for f in (hb, lb):
        if not os.path.exists(f):
            raise Infrastructure(f"no binary {f}")
    tokens = json.load(open(f"{W}/tokens.json"))
    x = f"{S}/final.logits"
    done = r.setdefault("completed", [])

    def mark(name):
        done.append(name)
        save()

    def journal(name):
        return f"{r['journal_base']}.{name}.jsonl"

    def stage(name):
        E.pause_point(name)
        r["stages"].append([name, round(time.time() - r["started"], 1)])
        save()
        print(f"{time.strftime('%H:%M:%S')} {name}", file=sys.stderr, flush=True)

    def candidate_run(ids, *more):
        q = exec_run(lb, ids, x, *more)
        if q.returncode and exec_run(base_l, ids, x, *more).returncode:
            raise Infrastructure("the baseline fails the same command: " + E.tail(q, 300))
        return q

    for threads in (None, 1):
        if f"conformance {threads or 'default'}" in done:
            continue
        stage(f"conformance {threads or 'default'}")
        bad = E.conformance(hb, f"{H}/hidden/conform", threads)
        if bad and bad[0].startswith("the kernel crashed"):
            again = E.conformance(base_h, f"{H}/hidden/conform", threads)
            if again and again[0].startswith("the kernel crashed"):
                raise Infrastructure("the baseline crashes on the same conformance cases")
        r[f"conformance_{threads or 'default'}"] = {"differing": len(bad), "first": bad[:5]}
        if bad:
            r["failures"].append("conformance")
        mark(f"conformance {threads or 'default'}")
    r.setdefault("logits", {})
    for p, ids in tokens.items():
        if f"logits {p}" in done:
            continue
        stage(f"logits {p}")
        q = candidate_run(ids)
        same = q.returncode == 0 and open(x, "rb").read() == open(f"{W}/{p}.logits", "rb").read()
        r["logits"][p] = same
        if not same:
            r["failures"].append(f"logits {p}")
        mark(f"logits {p}")
    if "capture and SEQ" not in done:
        capture_and_seq(r, tokens, candidate_run, stage, mark)
    if r["failures"]:
        return
    bench(r, base_h, hb, base_l, lb, stage, mark, journal, exec_run, x, tokens, save)


def capture_and_seq(r, tokens, candidate_run, stage, mark):
    stage("capture")
    wit = f"{S}/final-witness"
    shutil.rmtree(wit, ignore_errors=True)
    q = candidate_run(tokens["code-rust"], "--gemv-witness", wit, "--gemv-witness-max-operands", "400")
    if q.returncode:
        r["failures"].append("capture")
        return
    m = json.load(open(f"{wit}/witness.json"))
    stage(f"SEQ and B1 on {len(m['records'])} operations")
    judged = E.judge_all(wit, m["records"], all_b1=True)
    r["seq"] = {"operations": len(judged), "not_satisfied": sum(j["seq"].status != "satisfied" for j in judged), "rows_violating": sum(j["seq"].rows_violating for j in judged)}
    r["b1"] = {"operations": len(judged), "satisfied": sum(j["b1"].status == "satisfied" for j in judged), "worst_ratio": max(float(j["b1"].worst_ratio) for j in judged if j["b1"].worst_ratio not in (None, "inf"))}
    if r["seq"]["not_satisfied"]:
        r["failures"].append("seq")
    mark("capture and SEQ")


def bench(r, base_h, hb, base_l, lb, stage, mark, journal, exec_run, x, tokens, save):
    done = r["completed"]
    if "kernel, default threads" not in done:
        stage("kernel, default threads")
        pairs, idles, noisy, equal = E.bench_blocks(base_h, hb, f"{W}/cases.tsv", 8, 30, 6 * 3600, journal=journal("kernel-default"))
        r["kernel_default_threads"] = {**E.summarise(pairs), "min_idle": min(idles), "blocks_not_quiet": noisy, "outputs_identical": equal}
        if not equal:
            r["failures"].append("heldout output")
        mark("kernel, default threads")
    if "kernel, one thread" not in done:
        stage("kernel, one thread")
        pairs, idles, noisy, equal = E.bench_blocks(base_h, hb, f"{W}/cases.tsv", 4, 15, 6 * 3600, {**PLAIN, "RAYON_NUM_THREADS": "1"}, journal=journal("kernel-one-thread"))
        r["kernel_one_thread"] = {**E.summarise(pairs), "min_idle": min(idles), "blocks_not_quiet": noisy}
        mark("kernel, one thread")
    if "end to end" not in done:
        stage("end to end")
        ids, ms = tokens["code-rust"], r.setdefault("e2e_pairs", [])
        for i in range(len(ms), 6):
            E.pause_point(f"end-to-end pair {i + 1} of 6")
            got = {}
            for key, binary in ([("a", base_l), ("b", lb)] if i % 2 == 0 else [("b", lb), ("a", base_l)]):
                E.wait_quiet(6 * 3600)
                out = exec_run(binary, ids, x)
                got[key] = float(re.search(r"\((\d+(?:\.\d+)?) ms/position\)", out.stdout + out.stderr).group(1))
            ms.append(got)
            save()
        ratios = [m["b"] / m["a"] for m in ms]
        r["end_to_end"] = {"pairs": ms, "median_ratio": float(np.median(ratios)), "improvement": 1 - float(np.median(ratios)), "range_improvement": [1 - max(ratios), 1 - min(ratios)]}
        mark("end to end")


def binary_hashes(cid):
    return {n: E.file_sha256(f"{H}/bin/{n}") for n in (f"harness-{cid}", f"larql-{cid}", "harness-baseline", "larql-baseline")}


def main():
    args = [a for a in sys.argv[1:] if a != "--resume"]
    resume = "--resume" in sys.argv[1:]
    cid, path = args[0], args[1]
    limit = int(args[2]) if len(args) > 2 else 24 * 3600
    E.PAUSE_FILE = f"{H}/PAUSE"
    if resume:
        r = json.load(open(path))
        if r["candidate"] != cid or r["binary_sha256"] != binary_hashes(cid) or r["wall_limit_s"] != limit:
            sys.exit("refusing to resume: the candidate, its binaries, or the limit differ from the run in " + path)
        for k in ("infrastructure_error", "outcome", "elapsed_s"):
            r.pop(k, None)
        r["resumes"] = r.get("resumes", 0) + 1
    else:
        if os.path.exists(path):
            sys.exit(f"{path} exists: pass --resume to continue it, or move it aside. A finished run isn't overwritten.")
        r = {"candidate": cid, "started": time.time(), "wall_limit_s": limit, "failures": [], "stages": [], "completed": [], "resumes": 0,
             "binary_sha256": binary_hashes(cid)}
    r["journal_base"] = path
    used, t0, paused = float(r.get("active_s", 0.0)), time.time(), [0.0]

    def active():
        return used + time.time() - t0 - paused[0]

    def save():
        r["active_s"] = round(active(), 1)
        with open(path + ".tmp", "w") as f:
            json.dump(r, f, indent=1)
        os.replace(path + ".tmp", path)

    def stop(signum, _frame):
        raise Infrastructure(f"stopped by signal {signum}: the wall clock limit or an operator. Continue with --resume")

    def on_resume(seconds):
        paused[0] += seconds
        signal.alarm(max(1, int(limit - active())))

    E.ON_RESUME = on_resume
    for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    if limit - used < 1:
        sys.exit("the wall clock limit is already used up")
    signal.alarm(int(limit - used))
    os.makedirs(S, exist_ok=True)
    save()
    try:
        run(r, cid, save)
    except BaseException as e:
        r["infrastructure_error"] = f"{type(e).__name__}: {e}"[:1500]
    signal.alarm(0)
    r["elapsed_s"] = round(active(), 1)
    r["outcome"] = outcome(r)
    save()
    print(json.dumps({k: r.get(k) for k in ("outcome", "failures", "infrastructure_error", "elapsed_s", "resumes", "kernel_default_threads", "kernel_one_thread", "end_to_end", "seq", "b1", "logits")}))


if __name__ == "__main__":
    main()
