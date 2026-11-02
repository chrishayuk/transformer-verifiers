"""Storage compatibility and timing, baseline against candidate. Development only (D15).

Compatibility: each binary on the other's container. Execution code did not change, so each dump must be bit-identical to
the dump the same container gave with its own binary.
Timing: the two binaries on their own containers, alternating, so that load affects both. The first pair is discarded.
"""
import hashlib
import json
import os
import statistics
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import larql_verify as L  # noqa: E402
from refcheck import ingest as I  # noqa: E402

NEW_EXE = os.path.expanduser("~/chris-source/larql-q8-encoder/target/release/larql")
NEW_C = os.path.expanduser("~/chris-models/q8enc-ad82acba/qwen3-0.6b-q8_0.vindex3")
OLD_EXE, OLD_C = L.LARQL, L.CONTAINER
BASE, CAND = os.path.join(HERE, "runs", "suite-v1"), os.path.join(HERE, "runs", "candidate-ad82acba", "suite-v1")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(exe, cont, manifest, d):
    dump = os.path.join(d, "x.f32")
    t = time.perf_counter()
    rec = I.run(exe, cont, manifest, dump, timeout=3600)
    wall = time.perf_counter() - t
    assert rec["exit_status"] == 0, rec.get("stderr")
    assert "FusedKQuant" in rec["stdout"] and "FusedBf16" in rec["stdout"]
    meta = json.load(open(I.sidecar_path_for(dump)))
    return {"sha": sha(dump), "wall": wall, "ms_per_position": meta["ms_per_position"], "stdout": rec["stdout"]}


out = {"compatibility": {}, "timing": {}}
with tempfile.TemporaryDirectory(dir=os.path.join(HERE, "build")) as d:
    for cid in ("short-2", "prose-en", "repetition"):
        m = json.load(open(os.path.join(BASE, cid, "tokens.json")))
        old_on_new = run(OLD_EXE, NEW_C, m, d)
        new_on_old = run(NEW_EXE, OLD_C, m, d)
        out["compatibility"][cid] = {
            "old_binary_on_new_container_equals_candidate_dump": old_on_new["sha"] == sha(os.path.join(CAND, cid, "larql.f32")),
            "new_binary_on_old_container_equals_baseline_dump": new_on_old["sha"] == sha(os.path.join(BASE, cid, "larql.f32")),
        }
        print(cid, out["compatibility"][cid], flush=True)
    for cid, reps in (("prose-en", 8), ("structured-table", 5)):
        m = json.load(open(os.path.join(BASE, cid, "tokens.json")))
        o, n = [], []
        for i in range(reps + 1):
            a = run(OLD_EXE, OLD_C, m, d)
            b = run(NEW_EXE, NEW_C, m, d)
            if i:
                o.append(a)
                n.append(b)
        out["timing"][cid] = {"n_tokens": len(m["token_ids"]), "pairs": reps,
                              "baseline_ms_per_position": [x["ms_per_position"] for x in o],
                              "candidate_ms_per_position": [x["ms_per_position"] for x in n],
                              "baseline_median": statistics.median(x["ms_per_position"] for x in o),
                              "candidate_median": statistics.median(x["ms_per_position"] for x in n),
                              "baseline_wall_median": statistics.median(x["wall"] for x in o),
                              "candidate_wall_median": statistics.median(x["wall"] for x in n)}
        print(cid, {k: v for k, v in out["timing"][cid].items()}, flush=True)
json.dump(out, open(os.path.join(HERE, "runs", "candidate-ad82acba", "compat-and-timing.json"), "w"), indent=1)
