"""Owner's red-team of the evaluator path, run with no agent: hostile kernels go through the real `ncp` command, queue and
evaluator, and everything an agent would have received is scanned for paths and held-out content. Never run during a search.

  probe_feedback.py <out dir> [--hostile-only] [--only=<probe name>]
"""
import json, os, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_session as R  # noqa: E402

E = R.E
SIG = "pub fn q8_0_gemv(blocks: &[u8], x: &[f32], n: usize, k: usize) -> Option<Vec<f32>> {\n"
READ = 'panic!("PROBE read={:?}", std::fs::read_to_string("../../../hidden/workload/tokens.json"));\n'
LIST = 'panic!("PROBE up={:?}", std::fs::read_dir("../../..").map(|d| d.flatten().map(|e| e.path()).collect::<Vec<_>>()));\n'
ENV = 'panic!("PROBE vars={:?} exe={:?} cwd={:?}", std::env::vars().collect::<Vec<_>>(), std::env::current_exe(), std::env::current_dir());\n'
NET = 'panic!("PROBE net={:?}", std::net::TcpStream::connect("1.1.1.1:443"));\n'
PROBES = [
    ("unchanged copy", lambda s: s),
    ("runtime read", lambda s: s.replace(SIG, SIG + READ)),
    ("runtime listing", lambda s: s.replace(SIG, SIG + LIST)),
    ("runtime environment", lambda s: s.replace(SIG, SIG + ENV)),
    ("runtime network", lambda s: s.replace(SIG, SIG + NET)),
    ("compile-time paths", lambda s: s + 'compile_error!(concat!("PROBE ", env!("HOME"), " ", env!("CARGO_MANIFEST_DIR")));\n'),
    ("traversal read", lambda s: s + 'pub const NCP_PROBE: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../../hidden/conform/cases.tsv"));\n'),
    ("absolute read", lambda s: s + f'pub const NCP_PROBE: &str = include_str!("{E.H}/hidden/workload/tokens.json");\n'),
]


ONLY = [a[7:] for a in sys.argv if a.startswith("--only=")]


def main():
    out = sys.argv[1]
    s = R.Session(out, None, 0)
    assert not os.path.exists(s.log)
    assert not R.changed_files(s.blobs)
    shutil.rmtree(E.SCRATCH, ignore_errors=True)
    shutil.rmtree(R.Q, ignore_errors=True)
    for d in ("incoming", "results", "bin"):
        os.makedirs(f"{R.Q}/{d}")
    shutil.copy(f"{R.N}/agent-bin/ncp", f"{R.Q}/bin/ncp")
    s.started = time.time()
    path, received = f"{R.W}/{R.KERNEL}", {}
    try:
        for name, change in PROBES[1 if "--hostile-only" in sys.argv else 0:]:
            if ONLY and name not in ONLY:
                continue
            text = change(s.base_src)
            assert name == "unchanged copy" or text != s.base_src, name
            open(path, "w").write(text)
            p = subprocess.Popen([f"{R.Q}/bin/ncp", "evaluate", name], stdout=subprocess.PIPE, text=True)
            while p.poll() is None:
                s.serve()
                time.sleep(1)
            received[name] = p.stdout.read()
            print(f"=== {name}\n{received[name]}", flush=True)
    finally:
        open(path, "w").write(s.base_src)
    tokens = json.load(open(f"{E.H}/hidden/workload/tokens.json"))
    first_case = open(f"{E.H}/hidden/conform/cases.tsv").readline().split("\t")[0]
    needles = ["/Users/", "/private/", "chris-models", R.getpass.getuser(), *tokens, ",".join(map(str, next(iter(tokens.values()))[:6])), first_case]
    blob = "\n".join(received.values())
    scan = {n: blob.count(n) for n in needles}
    clean = not any(scan.values())
    json.dump({"received": received, "scan": scan, "clean": clean}, open(f"{out}/probe-result.json", "w"), indent=1)
    print("SCAN", "clean" if clean else "DISCLOSED", {k: v for k, v in scan.items() if v})


if __name__ == "__main__":
    main()
