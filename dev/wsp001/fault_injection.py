"""Fault injection for the WSP-001 checkers: a permanent regression suite (the fixture builder shares no code with the checkers).
Each mutant is a clone of a known-good edited container with ONE deliberate fault, resealed where needed so the fault is
semantic and not merely a digest mismatch. Both checkers are run on every mutant, plus the unmutated container as a control.

  fault_injection.py <good edited container> <original container> <manifest> <work dir>

<original container> must be the exact container the edit was written against (the native ledger names its index digest).
Each fault is rejected by at least one checker, and the reason is printed so a fault cannot pass for the wrong reason.
"""
import hashlib, json, os, shutil, struct, subprocess, sys
import numpy as np

CHK = os.path.dirname(os.path.abspath(__file__))
BLK = 34

def sha(path, start=0):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(start)
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()

def hdr(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n)), 8 + n

def tinfo(path, name):
    h, p = hdr(path)
    t = next(x for x in h["tensors"] if x["name"] == name)
    return t, p + t["offset"]

def clone(src, dst):
    subprocess.run(["cp", "-cR", src, dst], check=True)

def reseal(m, bf=True, q8=True, link_pack=True, candidate=True):
    idx = json.load(open(f"{m}/index.json"))
    for rid, r in idx["representations"].items():
        enc_q = "compiled_from" in r
        if (enc_q and not q8) or (not enc_q and not bf):
            continue
        path = f"{m}/{r['segment']}"
        _, p = hdr(path)
        r["payload_sha256"], r["segment_sha256"] = sha(path, p), sha(path)
    if bf and link_pack:
        b = idx["representations"]["target.decoder_stack@BF16"]
        idx["representations"]["target.decoder_stack@Q8_0"]["source_representation_digest"] = b["payload_sha256"]
    json.dump(idx, open(f"{m}/index.json", "w"), indent=2)
    if candidate and bf:
        cand = json.load(open(f"{m}/candidate.json"))
        b = idx["representations"]["target.decoder_stack@BF16"]
        for r in cand["source"]["identity"]["semantic"]["representations"]:
            if r["segment"] == b["segment"]:
                r["payload_sha256"], r["segment_sha256"] = b["payload_sha256"], b["segment_sha256"]
        json.dump(cand, open(f"{m}/candidate.json", "w"))

def bf16_f32(bits): return (np.uint32(bits) << np.uint32(16)).view(np.float32)
def put16(path, off, bits):
    with open(path, "r+b") as f:
        f.seek(off); f.write(np.uint16(bits).tobytes())
def get16(path, off):
    with open(path, "rb") as f:
        f.seek(off); return int(np.frombuffer(f.read(2), dtype=np.uint16)[0])

def build(good, orig, man, work):
    man = json.load(open(man)); e = man["edits"][0]
    cols, row, delta, tname = e["cols"], e["row"], e["delta"], e["tensor"]
    BFp = lambda m: f"{m}/segments/target.decoder_stack.bin"
    Qp = lambda m: f"{m}/segments/target.decoder_stack@Q8_0.bin"
    def elem(m, t, r, c, path=None):
        tt, base = tinfo(BFp(m), t); return base + (r * tt["shape"][1] + c) * 2
    def oldbits(c): return get16(BFp(orig), elem(orig, tname, row, c))
    mutants = {}
    def trunc(m):
        for c in cols:
            f32 = bf16_f32(oldbits(c)) + np.float32(delta)
            put16(BFp(m), elem(m, tname, row, c), int(f32.view(np.uint32) >> 16))
        reseal(m, q8=False)
    mutants["wrong rounding (truncate, not RNE)"] = ("patch", trunc)
    def wrongcoord(m):
        o = elem(m, tname, row, cols[0]); put16(BFp(m), o, oldbits(cols[0]))
        n = elem(m, tname, row, cols[0] - 1); put16(BFp(m), n, get16(BFp(orig), n) + 0); 
        f32 = bf16_f32(get16(BFp(orig), n)) + np.float32(delta); put16(BFp(m), n, int(((f32.view(np.uint32).astype(np.uint64) + 0x7FFF + ((f32.view(np.uint32) >> 16) & 1)) >> 16)))
        reseal(m, q8=False)
    mutants["off-by-one coordinate (col 199 instead of 200)"] = ("patch", wrongcoord)
    def dropped(m):
        put16(BFp(m), elem(m, tname, row, cols[-1]), oldbits(cols[-1])); reseal(m, q8=False)
    mutants["dropped element (col 207 left unedited)"] = ("patch", dropped)
    def extra(m):
        c = 205; o = elem(m, tname, row, c); v = bf16_f32(get16(BFp(m), o)) + np.float32(delta)
        b = v.view(np.uint32).astype(np.uint64); put16(BFp(m), o, int((b + 0x7FFF + ((b >> 16) & 1)) >> 16)); reseal(m, q8=False)
    mutants["extra neighbouring edit (col 205, the block maximum)"] = ("patch", extra)
    def wrongtensor(m):
        for c in cols:
            put16(BFp(m), elem(m, tname, row, c), oldbits(c))
            o = elem(m, "25.mlp.down_proj.weight", row, c); v = bf16_f32(get16(BFp(m), o)) + np.float32(delta)
            b = v.view(np.uint32).astype(np.uint64); put16(BFp(m), o, int((b + 0x7FFF + ((b >> 16) & 1)) >> 16))
        reseal(m, q8=False)
    mutants["right coordinates, wrong tensor (layer 25)"] = ("patch", wrongtensor)
    def wrongdelta(m):
        for c in cols:
            o = elem(m, tname, row, c); v = bf16_f32(oldbits(c)) + np.float32(delta * 2)
            b = v.view(np.uint32).astype(np.uint64); put16(BFp(m), o, int((b + 0x7FFF + ((b >> 16) & 1)) >> 16))
        reseal(m, q8=False)
    mutants["wrong delta (2x)"] = ("patch", wrongdelta)
    def staledigest(m):
        i = json.load(open(f"{m}/index.json")); o = json.load(open(f"{orig}/index.json"))
        i["representations"]["target.decoder_stack@BF16"] = o["representations"]["target.decoder_stack@BF16"]
        json.dump(i, open(f"{m}/index.json", "w"), indent=2)
    mutants["edit present but catalogue digests stale"] = ("patch", staledigest)
    # pack faults (BF16 stays correct)
    def stalepack(m):
        shutil.copyfile(Qp(orig), Qp(m)); reseal(m, bf=False, link_pack=False)
        i = json.load(open(f"{m}/index.json")); o = json.load(open(f"{orig}/index.json"))
        i["representations"]["target.decoder_stack@Q8_0"]["source_representation_digest"] = o["representations"]["target.decoder_stack@Q8_0"]["source_representation_digest"]
        json.dump(i, open(f"{m}/index.json", "w"), indent=2)
    mutants["stale Q8_0 pack (from the original), honest digest chain"] = ("pack", stalepack)
    def stalepack_lying(m):
        shutil.copyfile(Qp(orig), Qp(m)); reseal(m, bf=False, link_pack=False)
    mutants["stale Q8_0 pack, digest chain edited to hide it"] = ("pack", stalepack_lying)
    def flipcode(m):
        t, base = tinfo(Qp(m), "10.mlp.up_proj.weight"); o = base + 2 + 5
        with open(Qp(m), "r+b") as f:
            f.seek(o); v = f.read(1)[0]; f.seek(o); f.write(bytes([(v + 1) & 255]))
        reseal(m, bf=False, link_pack=False)
    mutants["one code flipped in an unrelated tensor"] = ("pack", flipcode)
    def badscale(m):
        t, base = tinfo(Qp(m), tname); o = base + (row * (t["shape"][1] // 32) + 6) * BLK
        with open(Qp(m), "r+b") as f:
            f.seek(o); v = f.read(1)[0]; f.seek(o); f.write(bytes([v ^ 1]))
        reseal(m, bf=False, link_pack=False)
    mutants["edited block's scale wrong (1 ulp)"] = ("pack", badscale)
    def unrequant(m):
        t, base = tinfo(Qp(m), tname); to, bo = tinfo(Qp(orig), tname)
        o = (row * (t["shape"][1] // 32) + 6) * BLK
        with open(Qp(orig), "rb") as f:
            f.seek(bo + o); blob = f.read(BLK)
        with open(Qp(m), "r+b") as f:
            f.seek(base + o); f.write(blob)
        reseal(m, bf=False, link_pack=False)
    mutants["edited block not re-quantised (original bytes)"] = ("pack", unrequant)
    def norm(m):
        t, base = tinfo(Qp(m), "3.input_layernorm.weight"); 
        with open(Qp(m), "r+b") as f:
            f.seek(base + 10); v = f.read(1)[0]; f.seek(base + 10); f.write(bytes([v ^ 4]))
        reseal(m, bf=False, link_pack=False)
    mutants["preserved (norm) tensor altered in the pack"] = ("pack", norm)
    def packdigest(m):
        with open(Qp(m), "r+b") as f:
            t, base = tinfo(Qp(m), "10.mlp.up_proj.weight"); f.seek(base + 9); v = f.read(1)[0]; f.seek(base + 9); f.write(bytes([v ^ 1]))
    mutants["pack bytes changed, catalogue digest not updated"] = ("pack", packdigest)
    def cand(m):
        c = json.load(open(f"{m}/candidate.json")); o = json.load(open(f"{orig}/candidate.json"))
        c["source"] = o["source"]; json.dump(c, open(f"{m}/candidate.json", "w"))
    mutants["candidate.json carries the original's digests"] = ("pack", cand)
    # faults aimed at the native ledger (weight_patches.json); only built when the container has one
    def ledger(m, change):
        path = f"{m}/weight_patches.json"
        l = json.load(open(path)); change(l); json.dump(l, open(path, "w"), indent=2)
    if os.path.exists(f"{good}/weight_patches.json"):
        mutants["ledger: an edit's new value is not what is stored"] = ("ledger", lambda m: ledger(m, lambda l: l["edits"][0].__setitem__("new_bits", l["edits"][0]["new_bits"] ^ 1)))
        mutants["ledger: names another source container"] = ("ledger", lambda m: ledger(m, lambda l: l["source"].__setitem__("index_sha256", "0" * 64)))
        mutants["ledger: result digest is stale"] = ("ledger", lambda m: ledger(m, lambda l: l["result"]["canonical"].__setitem__("payload_sha256", "1" * 64)))
        mutants["ledger: delta does not match its bits"] = ("ledger", lambda m: ledger(m, lambda l: l["edits"][0].__setitem__("delta_bits", l["edits"][0]["delta_bits"] ^ 1)))
        mutants["ledger: an edit dropped"] = ("ledger", lambda m: ledger(m, lambda l: l["edits"].pop()))
        mutants["ledger: an edit that was never made"] = ("ledger", lambda m: ledger(m, lambda l: l["edits"].append(dict(l["edits"][0], col=l["edits"][0]["col"] + 40))))
        mutants["ledger: deleted while the index still names it"] = ("ledger", lambda m: os.remove(f"{m}/weight_patches.json"))
    return mutants

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    fails = [l[5:].strip()[:70] for l in p.stdout.splitlines() if l.startswith("FAIL")]
    if p.returncode and not fails:
        fails = ["(checker error) " + (p.stderr.strip().splitlines() or ["?"])[-1][:60]]
    return p.returncode, fails

def main(good, orig, man, work):
    os.makedirs(work, exist_ok=True)
    exact = lambda m: run(["python3", "-I", f"{CHK}/check_weight_patch_exact.py", orig, m, man])
    coh = lambda m: run(["python3", "-I", f"{CHK}/check_representation_coherence.py", m, orig])
    print(f"{'CONTROL (unmutated)':<62} exact={'PASS' if exact(good)[0]==0 else 'FAIL'}  coherence={'PASS' if coh(good)[0]==0 else 'FAIL'}", flush=True)
    rows = []
    for name, (kind, fn) in build(good, orig, man, work).items():
        m = f"{work}/m-{abs(hash(name)) % 10**8}"
        if os.path.exists(m): shutil.rmtree(m)
        clone(good, m); fn(m)
        e, c = exact(m), coh(m)
        caught = (e[0] != 0) or (c[0] != 0)
        rows.append((name, e[0] != 0, c[0] != 0, caught))
        reason = (e[1] or c[1] or ["-"])[0]
        print(f"{name:<62} exact={'REJECT' if e[0] else 'miss  '}  coherence={'REJECT' if c[0] else 'miss  '}  {'CAUGHT' if caught else '*** NOT CAUGHT ***'}\n      reason: {reason}", flush=True)
        shutil.rmtree(m)
    print(f"\n{sum(r[3] for r in rows)} of {len(rows)} faults rejected by at least one checker")
    return 0 if all(r[3] for r in rows) else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
