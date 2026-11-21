"""NCP-001: one continuous Claude Code session, and the evaluator beside it. The agent decides what to try and when. This
only serves `ncp evaluate`, keeps every candidate, and stops the session at the 20-candidate, 8-hour or US$120 limit.

  run_session.py [--out DIR] [--brief FILE] [--max-usd N] [--resume] [--launcher FILE] [--reserve-usd N]

Pausable and resumable. `touch ~/chris-models/ncp001/PAUSE` makes the runner finish any evaluation in progress, stop the agent
(its Claude session is saved by Claude Code), write STATE.json and exit with status 75. Remove the file and run it again with
--resume: the same session continues, with candidate count, agent hours, evaluation time and spend carried over, so a pause
or a crash never becomes a new budget. Agent time excludes the time spent stopped. A submission that was being evaluated when
the runner died is evaluated again from the saved bytes, and a finished evaluation whose reply never reached the agent is
replied to. Cost is only reported when a round ends, so an interrupted round's spend is unknown: --reserve-usd (default 5) is
charged for each interruption, which is an estimate, not a bound.

It takes one file and one message from the queue, as bytes. It never runs git or anything else in the agent's workspace.
"""
import argparse, difflib, getpass, hashlib, json, os, re, shutil, signal, stat, subprocess, sys, time, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if os.environ.get("NCP001_VALIDATE_SKIP"):
    sys.exit("refusing to run with gate validation switches set")
import evaluate as E  # noqa: E402

N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.expanduser("~/chris-source/ncp001-candidate")
Q = f"{W}/.ncp"
BUILD = f"{E.H}/build"
BASE = "bb15f826f18c2f9c2b16e7bee8a02dfafbfce8f0"
KERNEL = E.KERNEL
NOT_IN_WORKSPACE = ("verifier/", "docs/verification/", ".github/", "scripts/check_verifier_boundary.py")
MAX_CANDIDATES, MAX_AGENT_S, MAX_SOURCE_BYTES = 20, 8 * 3600, 1 << 20
PAUSE_FILE, EXIT_PAUSED, STATE_EVERY_S = f"{E.H}/PAUSE", 75, 30  # PAUSE is outside the candidate-writable scratch
GATES = [("Unit tests", "unit_tests"), ("Build", "build"), ("Bad geometry refused", "geometry"), ("Conformance", "conformance"), ("Production build", "production_build"),
         ("Capture", "capture"), ("Production logits", "logits"), ("SEQ", "seq"), ("Benchmark outputs", "bench_digest")]


def read_plain(path, limit=MAX_SOURCE_BYTES):
    """The bytes of a regular file, never following a link."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_size > limit:
            raise ValueError("not a regular file of acceptable size")
        return os.read(fd, limit + 1)
    finally:
        os.close(fd)


def baseline_blobs():
    out = subprocess.run(["git", "-C", BUILD, "ls-tree", "-r", BASE], capture_output=True, text=True, check=True).stdout
    blobs = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if not path.startswith(NOT_IN_WORKSPACE):
            blobs[path] = meta.split()[2]
    return blobs


def changed_files(blobs):
    """Tracked files that differ from the baseline, by hashing them here. The kernel is the one allowed difference."""
    changed = []
    for path, want in blobs.items():
        full = f"{W}/{path}"
        try:
            st = os.lstat(full)
            data = os.readlink(full).encode() if stat.S_ISLNK(st.st_mode) else open(full, "rb").read()
        except OSError:
            changed.append(path)
            continue
        if hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != want and path != KERNEL:
            changed.append(path)
    return changed


def sanitise(text):
    """Absolute paths and the user's name never reach the agent. The sandbox is what protects the held-out set: this removes accidental disclosure, and a deliberately encoded path would get past it."""
    text = re.sub(r"/(?:Users|private|var|tmp|Volumes|opt|Library|System|Applications|home|root)/[^\s`'\":,;)\]}>]*", "<path>", str(text))
    return text.replace(getpass.getuser(), "<user>")


def report(n, r, remaining):
    lines = [f"Candidate {n:02d}"]
    stage = r.get("failed_at")
    if stage == "policy":
        lines.append("Policy: FAIL")
    else:
        stop = next((i for i, (_, g) in enumerate(GATES) if g == stage), None)
        for i, (name, _) in enumerate(GATES):
            lines.append(f"{name}: {'PASS' if stop is None or i < stop else 'FAIL' if i == stop else 'not run'}")
    if r.get("b1_reported"):
        b = r["b1_reported"]
        lines.append(f"B1 (reported, not a gate): {b['satisfied']} of {b['operations']} satisfied")
    if r.get("dev"):
        d = r["dev"]
        lines += [f"Kernel improvement: {d['improvement']:+.1%}", f"95% CI: [{d['ci95_improvement'][0]:+.1%}, {d['ci95_improvement'][1]:+.1%}]"]
        if d["blocks_not_quiet"]:
            lines.append(f"Warning: {d['blocks_not_quiet']} benchmark blocks ran without a quiet machine")
    if stage:
        lines.append(f"Rejected at: {stage}\n{sanitise(r.get('feedback', ''))[-1800:]}")
    lines.append(f"Candidates remaining: {remaining}")
    return "\n".join(lines) + "\n"


class Session:
    def __init__(self, out, brief, max_usd, launcher=None, reserve_usd=5.0):
        self.out, self.brief, self.max_usd = out, brief, max_usd
        self.launcher, self.reserve_usd = launcher or f"{N}/launch-agent.sh", reserve_usd
        self.state_path, self.session, self.retries, self.round_open, self.stop_reason = f"{out}/STATE.json", None, 0, False, None
        self.log, self.n, self.eval_s, self.spent = f"{out}/CANDIDATES.jsonl", 0, 0.0, 0.0
        self.blobs = baseline_blobs()
        self.base_src = subprocess.run(["git", "-C", BUILD, "show", f"{BASE}:{KERNEL}"], capture_output=True, text=True, check=True).stdout
        self.started = None

    def agent_s(self):
        return time.time() - self.started - self.eval_s if self.started else 0.0

    def note(self, **rec):
        with open(self.log, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def save_state(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"candidates": self.n, "evaluation_s": self.eval_s, "spent_usd": self.spent, "agent_s": self.agent_s(), "session": self.session,
                       "retries": self.retries, "round_open": self.round_open, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, indent=1)
        os.replace(tmp, self.state_path)

    def restore(self):
        """Counters from the last STATE.json, then the records. An open round's cost is unknown: the reserve is charged."""
        st = json.load(open(self.state_path))
        records = [json.loads(line) for line in open(self.log) if line.strip()]
        self.n = max([st["candidates"]] + [int(r["candidate"][1:]) for r in records if "candidate" in r])
        self.eval_s = max(st["evaluation_s"], sum(r.get("evaluation_s", 0) for r in records if "candidate" in r and "event" not in r))
        self.spent, self.session, self.retries = st["spent_usd"], st["session"], st["retries"]
        if st["round_open"]:
            self.spent += self.reserve_usd
            self.note(event="interrupted_round_reserve_charged", usd_charged=self.reserve_usd, usd=round(self.spent, 2), session=self.session)
        self.started = time.time() - st["agent_s"] - self.eval_s
        self.round_open = False  # the reserve is charged once
        self.save_state()
        return records

    def recover(self, records):
        """Finish what an interruption left half done. The build tree is restored first: an evaluation may have died with the kernel swapped in."""
        subprocess.run(["git", "-C", BUILD, "checkout", "-q", "--", KERNEL], check=True)
        started = {r["candidate"]: r for r in records if r.get("event") == "evaluation_started"}
        finished = {r["candidate"]: r for r in records if "candidate" in r and "event" not in r}
        for cid, rec in sorted(started.items()):
            if cid not in finished:
                t = time.time()
                rec = {k: v for k, v in rec.items() if k not in ("event", "message")}
                self.note(event="evaluation_resumed", candidate=cid, request=rec["request"])
                self.complete(rec["request"], cid, f"{self.out}/candidates/{cid}/kquant_gemv.rs", rec, started[cid]["message"], t)
            elif not os.path.exists(f"{Q}/results/{finished[cid]['request']}.txt"):
                rec = finished[cid]
                self.respond(rec["request"], report(int(cid[1:]), rec, MAX_CANDIDATES - int(cid[1:])))

    def respond(self, rid, text):
        d = f"{Q}/results"
        if os.path.islink(Q) or os.path.islink(d):
            raise RuntimeError("the agent replaced the results directory with a link")
        tmp = f"{d}/.{rid}"
        if os.path.lexists(tmp):
            os.unlink(tmp)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.rename(tmp, f"{d}/{rid}.txt")

    def serve(self):
        """Evaluates every request waiting, oldest first."""
        d = f"{Q}/incoming"
        if os.path.islink(Q) or os.path.islink(d):
            raise RuntimeError("the agent replaced the queue with a link")
        for rid in sorted(x for x in os.listdir(d) if not x.startswith(".")):
            full = f"{d}/{rid}"
            if not re.fullmatch(r"\d+-\d+", rid):
                self.note(event="ignored_queue_entry", name=rid[:80])
                shutil.rmtree(full, ignore_errors=True) if not os.path.islink(full) else os.unlink(full)
                continue
            t = time.time()
            try:
                src, message = read_plain(f"{full}/kernel.rs"), read_plain(f"{full}/message.txt", 8192).decode(errors="replace")
            except (OSError, ValueError) as e:
                self.note(event="malformed_submission", request=rid, error=str(e))
                self.respond(rid, f"That submission couldn't be read ({type(e).__name__}), and it didn't use a candidate.\n")
                shutil.rmtree(full, ignore_errors=True)
                continue
            shutil.rmtree(full, ignore_errors=True)
            if self.n >= MAX_CANDIDATES:
                self.note(event="submission_over_limit", request=rid, kernel_sha256=hashlib.sha256(src).hexdigest(), mechanism=message)
                self.respond(rid, f"Not evaluated: all {MAX_CANDIDATES} candidates are used. Finish with your summary.\n")
                continue
            self.n += 1
            self.evaluate_one(rid, src, message, t)

    def evaluate_one(self, rid, src, message, t):
        cid = f"c{self.n:02d}"
        d = f"{self.out}/candidates/{cid}"
        os.makedirs(d, exist_ok=True)
        path = f"{d}/kquant_gemv.rs"
        with open(path, "wb") as f:
            f.write(src)
        with open(f"{d}/patch.diff", "w") as f:
            f.writelines(difflib.unified_diff(self.base_src.splitlines(True), src.decode(errors="replace").splitlines(True), f"a/{KERNEL}", f"b/{KERNEL}"))
        rec = {"candidate": cid, "request": rid, "kernel_sha256": hashlib.sha256(src).hexdigest(), "mechanism": message, "submitted_after_agent_hours": round(self.agent_s() / 3600, 3)}
        self.note(event="evaluation_started", message=message, **rec)  # the bytes are saved above: a dead runner can redo this evaluation
        self.save_state()
        self.complete(rid, cid, path, rec, message, t)

    def complete(self, rid, cid, path, rec, message, t):
        changed = changed_files(self.blobs)
        if changed:
            rec.update(passed=False, failed_at="policy", files_changed=changed, feedback=f"Tracked files other than the kernel differ from the original: {changed[:10]}. Restore them.")
        else:
            try:
                rec.update(E.evaluate(path, cid))
            except subprocess.TimeoutExpired as e:
                rec.update(passed=False, failed_at="timeout", feedback=f"A step ran past its limit of {e.timeout} s.")
            except Exception:
                rec.update(passed=False, failed_at="evaluator_error", feedback="The evaluation failed before reaching a verdict.", traceback=traceback.format_exc()[-3000:])
        took = time.time() - t
        self.eval_s += took
        rec["evaluation_s"] = round(took, 1)
        self.note(**rec)
        self.respond(rid, report(int(cid[1:]), rec, MAX_CANDIDATES - int(cid[1:])))
        self.save_state()

    def round(self, prompt, session):
        cmd = [self.launcher, "-p", "--permission-mode", "acceptEdits", "--output-format", "stream-json", "--verbose", "--max-budget-usd", f"{self.max_usd - self.spent:.2f}"]
        if session:
            cmd += ["--resume", session]
        stream = f"{self.out}/session.jsonl"
        before = os.path.getsize(stream) if os.path.exists(stream) else 0
        self.round_open = True
        self.save_state()
        last_state = time.time()
        with open(stream, "ab") as out:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=out, text=True)
            p.stdin.write(prompt)
            p.stdin.close()
            while p.poll() is None:
                self.serve()
                if self.agent_s() > MAX_AGENT_S:
                    p.terminate()
                    p.wait(60)
                    self.note(event="stopped_at_8_agent_hours", candidates=self.n)
                    self.round_open = False
                    return None, None
                if self.stop_reason or os.path.exists(PAUSE_FILE):
                    # No evaluation is running here: serve() returned. Claude Code saves the session, and --resume continues it.
                    p.terminate()
                    try:
                        p.wait(60)
                    except subprocess.TimeoutExpired:
                        p.kill()
                    self.session = self.scan_session(stream, before) or session
                    self.stop_reason = self.stop_reason or "pause file"
                    return "stopped", self.session
                if time.time() - last_state > STATE_EVERY_S:
                    self.session = self.scan_session(stream, before) or session
                    self.save_state()
                    last_state = time.time()
                time.sleep(2)
        self.serve()
        self.round_open = False
        result, sid = None, session
        with open(stream, "rb") as f:
            f.seek(before)
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                sid = o.get("session_id") or sid
                if o.get("type") == "result":
                    result = o
        return result, sid

    def scan_session(self, stream, offset):
        sid = None
        with open(stream, "rb") as f:
            f.seek(offset)
            for line in f:
                try:
                    sid = json.loads(line).get("session_id") or sid
                except ValueError:
                    continue
        return sid

    def run(self, resumed=False):
        if resumed:
            prompt, session, retries = "Your session was paused or interrupted by the operator. Carry on where you were.", self.session, self.retries
            if session is None:
                prompt = open(self.brief).read()  # it never got far enough to have a session to continue
        else:
            self.started = time.time()
            prompt, session, retries = open(self.brief).read(), None, 0
        while True:
            result, session = self.round(prompt, session)
            self.session, self.retries = session, retries
            if result == "stopped":
                self.note(event="paused", reason=self.stop_reason, candidates=self.n, usd=round(self.spent, 2), agent_hours=round(self.agent_s() / 3600, 3), session=session)
                self.save_state()
                print(f"paused ({self.stop_reason}): {self.n} candidates, US${self.spent:.2f}, {self.agent_s() / 3600:.2f} agent hours. Remove {PAUSE_FILE} and run again with --resume")
                return EXIT_PAUSED
            if result is None:
                if session:
                    self.note(event="session_ended_without_result", candidates=self.n)
                break
            self.spent += float(result.get("total_cost_usd") or 0)
            self.save_state()
            sub, err = result.get("subtype"), result.get("is_error")
            base = {"candidates": self.n, "usd": round(self.spent, 2), "agent_hours": round(self.agent_s() / 3600, 3), "subtype": sub, "session": session}
            if not err and sub == "success":
                self.note(event="agent_stopped", agent_said=str(result.get("result")), **base)
                break
            if "budget" in str(sub) or self.spent >= self.max_usd:
                self.note(event="stopped_at_budget", **base)
                break
            if retries >= 3:
                self.note(event="stopped_after_session_errors", **base)
                break
            retries += 1
            self.note(event="session_error_resumed", detail=str(result.get("result"))[-500:], **base)
            prompt = "Your session was interrupted by an infrastructure error. Carry on where you were."
        self.save_state()
        print(f"session finished: {self.n} candidates, US${self.spent:.2f}, {self.agent_s() / 3600:.2f} agent hours")
        return 0


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default=N)
    a.add_argument("--brief", default=f"{N}/AGENT-BRIEF.md")
    a.add_argument("--max-usd", type=float, default=120.0)
    a.add_argument("--resume", action="store_true")
    a.add_argument("--launcher", default=None)
    a.add_argument("--reserve-usd", type=float, default=5.0)
    o = a.parse_args()
    s = Session(o.out, o.brief, o.max_usd, o.launcher, o.reserve_usd)
    if os.path.exists(PAUSE_FILE):
        sys.exit(f"{PAUSE_FILE} exists: remove it to run")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda signum, _f: setattr(s, "stop_reason", f"signal {signum}"))
    if o.resume:
        assert os.path.exists(s.log) and os.path.exists(s.state_path), "nothing to resume: no CANDIDATES.jsonl and STATE.json here"
        shutil.rmtree(E.SCRATCH, ignore_errors=True)
        os.makedirs(f"{Q}/incoming", exist_ok=True)
        os.makedirs(f"{Q}/results", exist_ok=True)
        records = s.restore()
        s.recover(records)
        sys.exit(s.run(resumed=True))
    assert not os.path.exists(s.log), f"{s.log} exists: a restart mustn't become a new search budget. Use --resume to continue it"
    assert not subprocess.run(["git", "-C", BUILD, "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip(), "the evaluator's build tree isn't clean"
    shutil.rmtree(E.SCRATCH, ignore_errors=True)  # nothing from an earlier run is left where a candidate can read it
    changed = changed_files(s.blobs)
    assert not changed, f"the workspace isn't at the baseline: {changed[:5]}"
    assert read_plain(f"{W}/{KERNEL}").decode() == s.base_src, "the kernel isn't the baseline"
    shutil.rmtree(Q, ignore_errors=True)
    os.makedirs(f"{Q}/incoming")
    os.makedirs(f"{Q}/results")
    os.makedirs(f"{Q}/bin")
    shutil.copy(f"{N}/agent-bin/ncp", f"{Q}/bin/ncp")
    os.makedirs(o.out, exist_ok=True)
    sys.exit(s.run())


if __name__ == "__main__":
    main()
