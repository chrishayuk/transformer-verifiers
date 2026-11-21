"""NCP-001's evaluator: the one path every candidate takes. Frozen before any agent runs. Run with the verifier's venv.

  evaluate.py <kernel.rs> <candidate id>   prints one JSON object

Gates, cheapest first, stopping at the first failure. Only a candidate that passes all of them is timed:
  build, kernel unit tests, bad geometry, conformance (twice: default threads, one thread), production build,
  capture on the pinned prompt, logits bit-identical to baseline, Q8_0_GEMV_SEQ on all 196 operations, B1 on 12 reported.
"""
import hashlib, json, multiprocessing, os, re, shutil, statistics, subprocess, sys, time

import numpy as np

H = os.path.expanduser("~/chris-models/ncp001")
sys.path.insert(0, f"{H}/build/verifier")
from refcheck import gemv  # noqa: E402

KERNEL = "crates/larql-compute/src/cpu/kquant_gemv.rs"
C8 = os.path.expanduser("~/chris-models/q8enc-ad82acba/qwen3-0.6b-q8_0.vindex3")
TOKENS = "9707,1879,13,576,374,264,1273,315,279,5333,323,1181,2550,9963,11,8365"
ENV = {"PATH": f"{os.path.expanduser('~/.cargo/bin')}:/usr/bin:/bin", "HOME": os.environ["HOME"], "RUSTUP_TOOLCHAIN": "1.98.0"}
PLAIN = {"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"]}
SKIP = set(filter(None, os.environ.get("NCP001_VALIDATE_SKIP", "").split(",")))  # gate validation only. The orchestrator refuses to run with it set
SCRATCH = f"{H}/scratch"  # the only evaluator directory a candidate process can write to or read back from
QUIET_IDLE = 85.0  # percent idle over 3 s: at most about 2.4 of 16 cores busy
B1_OPS = [f"{l}.{op}.weight" for l in (0, 13, 27) for op in ("self_attn.q_proj", "mlp.up_proj", "mlp.gate_proj", "mlp.down_proj")]


BOX = []  # set by evaluate(): every process that compiles or links candidate code runs under candidate.sb


def sh(cmd, env=ENV, cwd=None, timeout=3600, box=True):
    return subprocess.run((BOX if box else []) + cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def tail(p, n=1800):
    return (p.stderr + p.stdout)[-n:]  # stdout last: a failing test's message outlasts compiler warnings


def idle():
    out = sh(["top", "-l", "2", "-n", "0", "-s", "3"], PLAIN, box=False).stdout
    return float(re.findall(r"([\d.]+)% idle", out)[-1])


def wait_quiet(limit_s):
    started, v = time.time(), idle()
    while v < QUIET_IDLE and time.time() - started < limit_s:
        time.sleep(30)
        v = idle()
    return v, v >= QUIET_IDLE


def judge_one(a):
    w, r, all_b1 = a
    rd = lambda s: open(os.path.join(w, r[s]["file"]), "rb").read()  # noqa: E731
    x, y = np.frombuffer(rd("x"), dtype="<u4"), np.frombuffer(rd("y"), dtype="<u4")
    out = {"tensor": r["tensor"], "seq": gemv.check_seq(rd("blocks"), x, y, r["rows"], r["columns"])}
    if all_b1 or r["tensor"] in B1_OPS:
        out["b1"] = gemv.check_b1(rd("blocks"), x, y, r["rows"], r["columns"])
    return out


def judge_all(w, records, all_b1=False, timeout=3 * 3600):
    """Every record in worker processes, which are gone when this returns, however it returns."""
    with multiprocessing.Pool(10) as pool:
        return pool.map_async(judge_one, [(w, x, all_b1) for x in records]).get(timeout)


def conformance(bin_path, cases, threads):
    d = f"{SCRATCH}/conform"
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    env = dict(PLAIN)
    if threads:
        env["RAYON_NUM_THREADS"] = str(threads)
    p = sh([bin_path, "conform", f"{cases}/cases.tsv", d], env)
    if p.returncode:
        return ["the kernel crashed or refused valid geometry: " + tail(p, 300)]
    bad = []
    for line in open(f"{cases}/cases.tsv"):
        cid = line.split("\t")[0]
        if open(f"{d}/{cid}.y", "rb").read() != open(f"{cases}/{cid}.want", "rb").read():
            bad.append(cid)
    return bad


PAUSE_FILE = None  # set by final.py only. The session runner pauses at its own level. Outside SCRATCH, so candidate code can neither read nor write it
ON_RESUME = None  # called with the seconds spent paused, so a caller's wall clock can exclude them


def pause_point(label):
    """Blocks while PAUSE_FILE exists. Called between block pairs only, never in the middle of a measurement."""
    if not PAUSE_FILE or not os.path.exists(PAUSE_FILE):
        return 0.0
    t = time.time()
    print(f"{time.strftime('%H:%M:%S')} paused before {label}. Remove {PAUSE_FILE} to continue.", file=sys.stderr, flush=True)
    while os.path.exists(PAUSE_FILE):
        time.sleep(5)
    paused = time.time() - t
    print(f"{time.strftime('%H:%M:%S')} resumed after {paused:.0f} s", file=sys.stderr, flush=True)
    if ON_RESUME:
        ON_RESUME(paused)
    return paused


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bench_blocks(base, cand, cases, blocks, reps, quiet_limit, env=PLAIN, journal=None):
    """Counterbalanced: ABBA, BAAB, … Returns per-pair lists of case ratios and digest agreement.
    With a journal, each finished pair is recorded, and a rerun continues after the last recorded pair."""
    pairs, idles, noisy, digests_equal = [], [], 0, True
    if journal:
        identity = {"base": file_sha256(base), "cand": file_sha256(cand), "cases": file_sha256(cases), "blocks": blocks, "reps": reps, "env": sorted(env.items())}
        identity = json.loads(json.dumps(identity))  # as it reads back from the journal
        if os.path.exists(journal):
            lines = open(journal).read().split("\n")
            if json.loads(lines[0]).get("identity") != identity:
                raise RuntimeError(f"{journal} belongs to a different measurement (binaries, workload, blocks or repetitions differ). Remove it to start over.")
            kept = [lines[0]]
            for line in lines[1:]:
                try:
                    rec = json.loads(line)
                except ValueError:
                    break  # a torn last line: the process died mid-write
                kept.append(line)
                pairs.append(rec["pair"])
                idles += rec["idles"]
                noisy += rec["noisy"]
                digests_equal &= rec["equal"]
            with open(journal, "w") as f:
                f.write("\n".join(kept) + "\n")
        else:
            with open(journal, "w") as f:
                f.write(json.dumps({"identity": identity}) + "\n")
    for i in range(len(pairs), blocks):
        pause_point(f"block pair {i + 1} of {blocks}")
        order = [("a", base), ("b", cand)] if i % 2 == 0 else [("b", cand), ("a", base)]
        got, pair_idles, pair_noisy = {}, [], 0
        for key, binary in order:
            v, ok = wait_quiet(quiet_limit)
            pair_idles.append(v)
            pair_noisy += not ok
            out = f"{SCRATCH}/bench-{key}.tsv"
            p = sh([binary, "bench", cases, str(reps), out], env)
            if p.returncode:
                raise RuntimeError(tail(p, 400))
            got[key] = {f[0]: f[1:] for f in (l.rstrip("\n").split("\t") for l in open(out))}
        ratios, equal = {}, True
        for cid in got["a"]:
            ratios[cid] = int(got["b"][cid][0]) / int(got["a"][cid][0])
            equal &= got["a"][cid][3] == got["b"][cid][3]
        pairs.append(ratios)
        idles += pair_idles
        noisy += pair_noisy
        digests_equal &= equal
        if journal:
            with open(journal, "a") as f:
                f.write(json.dumps({"pair": ratios, "idles": pair_idles, "noisy": pair_noisy, "equal": equal}) + "\n")
                f.flush()
                os.fsync(f.fileno())
    return pairs, idles, noisy, digests_equal


def summarise(pairs, boot=4000, seed=20261103):
    """Median over cases of each case's median ratio. A percentile bootstrap resamples block pairs, then cases."""
    cases = sorted(pairs[0])
    table = np.array([[p[c] for c in cases] for p in pairs])
    point = float(np.median(np.median(table, axis=0)))
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(boot):
        t = table[rng.integers(0, table.shape[0], table.shape[0])][:, rng.integers(0, table.shape[1], table.shape[1])]
        stats.append(np.median(np.median(t, axis=0)))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return {"ratio": point, "improvement": 1 - point, "ci95_improvement": [float(1 - hi), float(1 - lo)],
            "pairs": len(pairs), "cases": len(cases)}


def evaluate(kernel, cid):
    BOX[:] = ["sandbox-exec", "-D", f"HOME={os.environ['HOME']}", "-f", os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidate.sb")]
    os.makedirs(SCRATCH, exist_ok=True)
    r = {"candidate": cid, "kernel_sha256": hashlib.sha256(open(kernel, "rb").read()).hexdigest(), "passed": False, "failed_at": None, "feedback": ""}
    target = f"{H}/build/{KERNEL}"
    shutil.copy(kernel, target)
    try:
        def fail(stage, why):
            r.update(failed_at=stage, feedback=why)
            return r

        p = sh(["cargo", "test", "-q", "--release", "--locked", "-p", "larql-compute", "kquant_gemv"], cwd=f"{H}/build", env={**ENV, "CARGO_TARGET_DIR": f"{H}/target-larql"})
        if p.returncode and "unit_tests" not in SKIP:
            return fail("unit_tests", tail(p))
        p = sh(["cargo", "build", "-q", "--release"], cwd=f"{H}/harness", env={**ENV, "CARGO_TARGET_DIR": f"{H}/target-harness"})
        if p.returncode:
            return fail("build", tail(p))
        hb = f"{H}/bin/harness-{cid}"
        shutil.copy(f"{H}/target-harness/release/ncp001-harness", hb)
        p = sh([hb, "refuse"], PLAIN)
        if p.returncode:
            return fail("geometry", "bad geometry wasn't refused, or empty input was: " + tail(p, 300))
        for threads in (None, 1):
            bad = conformance(hb, f"{H}/conform-dev", threads)
            if bad and "conformance" not in SKIP:
                return fail("conformance", f"{len(bad)} conformance cases differ from the declared program ({'one thread' if threads else 'default threads'}). "
                                           f"First: {bad[:5]}. Case names are family-rowsxcolumns.")
        p = sh(["cargo", "build", "-q", "--release", "--locked", "-p", "larql-cli"], cwd=f"{H}/build",
               env={**ENV, "CARGO_TARGET_DIR": f"{H}/target-larql", "LARQL_BUILD_COMMIT": f"bb15f826f18c2f9c2b16e7bee8a02dfafbfce8f0+{cid}"})
        if p.returncode:
            return fail("production_build", tail(p))
        lb = f"{H}/bin/larql-{cid}"
        shutil.copy(f"{H}/target-larql/release/larql", lb)
        w = f"{SCRATCH}/witness"
        shutil.rmtree(w, ignore_errors=True)
        logits = f"{SCRATCH}/logits.bin"
        p = sh([lb, "vindex3", "exec", C8, "--backend", "production-q8", "--representation-source", "stored", "--tokens", TOKENS,
                "--logit-dump", logits, "--gemv-witness", w, "--gemv-witness-max-operands", "400"], PLAIN)
        if p.returncode:
            return fail("capture", tail(p, 500))
        m = json.load(open(f"{w}/witness.json"))
        if (m["calls_observed"], len(m["records"])) != (3136, 196) or m["execution_arm"] != "Direct":
            return fail("capture", f"unexpected run: {m['calls_observed']} calls, {len(m['records'])} operands, {m['execution_arm']}")
        if open(logits, "rb").read() != open(f"{H}/baseline-logits.bin", "rb").read() and "logits" not in SKIP:
            return fail("logits", "the model's logits on the pinned prompt aren't bit-identical to the baseline's")
        judged = judge_all(w, m["records"])
        seq_bad = [j["tensor"] for j in judged if j["seq"].status != "satisfied"]
        r["seq"] = {"operations": len(judged), "not_satisfied": len(seq_bad), "rows_violating": sum(j["seq"].rows_violating for j in judged)}
        b1 = [j["b1"] for j in judged if "b1" in j]
        r["b1_reported"] = {"operations": len(b1), "satisfied": sum(x.status == "satisfied" for x in b1),
                            "worst_ratio": max((float(x.worst_ratio) for x in b1 if x.worst_ratio not in (None, "inf")), default=None)}
        if seq_bad:
            return fail("seq", f"Q8_0_GEMV_SEQ failed on {len(seq_bad)} of 196 recorded operations. First: {seq_bad[:3]}")
        pairs, idles, noisy, equal = bench_blocks(f"{H}/bin/harness-baseline", hb, f"{H}/workload-dev/cases.tsv", 4, 15, 1800)
        if not equal:
            return fail("bench_digest", "the output on the development workload isn't bit-identical to the baseline's")
        r["dev"] = {**summarise(pairs), "min_idle": min(idles), "blocks_not_quiet": noisy}
        r.update(passed=True, feedback=f"Passed every gate. Development kernel latency: {r['dev']['improvement']:+.1%} "
                                       f"(95% CI {r['dev']['ci95_improvement'][0]:+.1%} to {r['dev']['ci95_improvement'][1]:+.1%}), positive is faster.")
        return r
    finally:
        subprocess.run(["git", "checkout", "-q", "--", KERNEL], cwd=f"{H}/build")


if __name__ == "__main__":
    print(json.dumps(evaluate(sys.argv[1], sys.argv[2])))
