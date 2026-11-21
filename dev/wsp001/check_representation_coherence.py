"""REPRESENTATION_COHERENCE. Independent of the writer and of LARQL's encoder: the oracle is pinned ggml's own quantize_row_q8_0_ref
(loaded from the verifier's build), the BF16 source is read here, and nothing is imported from the container tooling.

  check_representation_coherence.py <container with a Q8_0 pack> [<original container with a Q8_0 pack>]     exit 0 = pass

Checks: (1) the digest chain BF16 payload -> Q8_0 `source_representation_digest`; (2) the pack's own digests; (3) every quantised
tensor in the pack is byte-identical to ggml's encoding of the container's BF16 weights; every other tensor is byte-identical to
its BF16 source; (4) against the original container: exactly which Q8_0 blocks differ.
"""
import ctypes, hashlib, json, os, struct, sys
import numpy as np

LIB = os.path.expanduser("~/chris-source/transformer-verifiers/dev/larql-verify/build/libggmlq8ref.dylib")
BLOCK = 34

def ggml_encode(x32):
    lib = ctypes.CDLL(LIB)
    f = lib.quantize_row_q8_0_ref
    f.restype = None
    f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64]
    x = np.ascontiguousarray(x32, dtype=np.float32).reshape(-1)
    out = np.zeros(x.size // 32 * BLOCK, dtype=np.uint8)
    f(x.ctypes.data, out.ctypes.data, x.size)
    return out

def segment(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        h = json.loads(f.read(n))
    return h, 8 + n

def sha(path, start=0):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(start)
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()

def tensors(path):
    h, payload = segment(path)
    mm = np.memmap(path, dtype=np.uint8, mode="r")
    return h, {t["name"]: (t, mm[payload + t["offset"]: payload + t["offset"] + t["len"]]) for t in h["tensors"]}, payload

def pack_view(container):
    idx = json.load(open(f"{container}/index.json"))
    q = next((r for r in idx["representations"].values() if "compiled_from" in r), None)
    return idx, q

def main(cont, orig=None):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed)
        print(("PASS " if passed else "FAIL ") + name + (f"  {detail}" if detail else ""), flush=True)
    idx, q = pack_view(cont)
    check("a compiled Q8_0 representation exists", q is not None and q["encoding"] == "Q8_0")
    if q is None:
        return 1
    bf = idx["representations"][q["compiled_from"]]
    _, bf_payload = segment(f"{cont}/{bf['segment']}")
    bf_digest = sha(f"{cont}/{bf['segment']}", bf_payload)
    check("BF16 catalogue payload digest equals the recomputed digest", bf["payload_sha256"] == bf_digest)
    check("Q8_0 source_representation_digest equals the recomputed BF16 payload digest (the pack derives from THIS source)",
          q["source_representation_digest"] == bf_digest)
    _, q_payload = segment(f"{cont}/{q['segment']}")
    check("Q8_0 catalogue payload and segment digests equal the recomputed digests",
          q["payload_sha256"] == sha(f"{cont}/{q['segment']}", q_payload) and q["segment_sha256"] == sha(f"{cont}/{q['segment']}"))
    cp = f"{cont}/candidate.json"
    if os.path.exists(cp):
        cand = json.load(open(cp))
        crep = next(r for r in cand["source"]["identity"]["semantic"]["representations"] if r["segment"] == bf["segment"])
        check("candidate.json's recorded source digests equal the catalogue's BF16 digests",
              crep["payload_sha256"] == bf["payload_sha256"] and crep["segment_sha256"] == bf["segment_sha256"])
    _, bt, _ = tensors(f"{cont}/{bf['segment']}")
    _, qt, _ = tensors(f"{cont}/{q['segment']}")
    check("the pack and the source carry the same tensor names", set(bt) == set(qt))
    quantised = bad = preserved = 0
    first_bad = None
    for name, (t, raw) in qt.items():
        st, sraw = bt[name]
        if t["dtype"] == "Q8_0":
            w = (np.asarray(sraw).view(np.uint16).astype(np.uint32) << 16).view(np.float32)
            quantised += 1
            if not np.array_equal(np.asarray(raw), ggml_encode(w)):
                bad += 1
                first_bad = first_bad or name
        else:
            preserved += 1
            if t["dtype"] != st["dtype"] or not np.array_equal(np.asarray(raw), np.asarray(sraw)):
                bad += 1
                first_bad = first_bad or name
    check("every quantised tensor equals ggml's encoding of the BF16 source and every other tensor equals its source, byte for byte",
          bad == 0, f"{quantised} quantised + {preserved} preserved checked, {bad} differ" + (f", first: {first_bad}" if bad else ""))
    if orig:
        _, oq = pack_view(orig)
        _, ot, _ = tensors(f"{orig}/{oq['segment']}")
        changed = []
        for name, (t, raw) in qt.items():
            ot_t, oraw = ot[name]
            if not np.array_equal(np.asarray(raw), np.asarray(oraw)):
                if t["dtype"] == "Q8_0":
                    rows, cols = t["shape"]
                    a = np.asarray(raw).reshape(rows, cols // 32, BLOCK)
                    b = np.asarray(oraw).reshape(rows, cols // 32, BLOCK)
                    for r, k in np.argwhere((a != b).any(axis=2)):
                        changed.append((name, int(r), int(k), bool((a[r, k, :2] == b[r, k, :2]).all()), int((a[r, k, 2:] != b[r, k, 2:]).sum())))
                else:
                    changed.append((name, "preserved tensor changed"))
        print("INFO blocks that differ from the original pack (tensor, row, block, scale unchanged, codes changed):", changed)
    print("\nREPRESENTATION_COHERENCE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
