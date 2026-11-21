"""WEIGHT_PATCH_EXACT. Independent of the writer: numpy and the standard library only, no LARQL code, no shared helpers.

Given the ORIGINAL container, the EDITED container and the patch manifest, verify that every declared element changed to exactly
the declared value and that nothing else in the container changed.

  check_weight_patch_exact.py <original container> <edited container> <manifest.json>      exit 0 = all checks pass

BF16 rule (declared, not borrowed from the writer): new = round_to_nearest_even_to_8_significant_bits(float(old) + delta),
computed here with frexp and Python's round (ties to even), on exact binary64 sums.
"""
import hashlib, json, math, os, struct, sys
import numpy as np

CHUNK = 1 << 24  # elements per comparison chunk

def bf16_bits_of(x):
    """Nearest bfloat16 to x (finite), ties to even, as 16 bits. Pure arithmetic on the real number."""
    if x == 0.0:
        return 0x8000 if math.copysign(1, x) < 0 else 0
    sign = 0x8000 if x < 0 else 0
    sig, exp = math.frexp(abs(x))             # abs(x) = sig * 2**exp, 0.5 <= sig < 1
    q = round(sig * 256)                       # 8 significant bits; Python round() is ties-to-even
    if q == 256:                               # carry into the next binade
        q, exp = 128, exp + 1
    e = exp - 1 + 127                          # biased exponent of a normal bfloat16
    if not (1 <= e <= 254):
        raise ValueError("outside the normal bfloat16 range")
    return sign | (e << 7) | (q - 128)

def read_segment(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        raw = f.read(n)
    return json.loads(raw), raw, 8 + n

def sha256_file(path, start=0):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(start)
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()

def main(orig, edit, manifest_path):
    man = json.load(open(manifest_path))
    results, ok = [], True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed)
        results.append({"check": name, "pass": bool(passed), "detail": detail})
        print(("PASS " if passed else "FAIL ") + name + (f"  {detail}" if detail else ""), flush=True)

    oi, ei = json.load(open(f"{orig}/index.json")), json.load(open(f"{edit}/index.json"))
    edited_objects = {e["object"] for e in man["edits"]}
    # 1. Every file outside the edited segments is byte-identical.
    seg_files = {ei["representations"][f"{o}@BF16"]["segment"] for o in edited_objects}
    same, differ = 0, []
    for root, _, files in os.walk(orig):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), orig)
            if rel in seg_files or rel in ("index.json", "weight_patch.json", "weight_patches.json") or rel.endswith("@Q8_0.bin") or rel == "candidate.json":
                continue
            p2 = os.path.join(edit, rel)
            if not os.path.exists(p2) or sha256_file(os.path.join(root, fn)) != sha256_file(p2):
                differ.append(rel)
            else:
                same += 1
    check("all files outside the edited segments are byte-identical", not differ, f"{same} identical" + (f", DIFFER: {differ}" if differ else ""))
    # 2. Catalogue: untouched BF16 representations unchanged; edited ones carry freshly recomputed digests.
    for rid, r in oi["representations"].items():
        if "compiled_from" in r:
            continue
        e = ei["representations"].get(rid)
        if r["object"] in edited_objects:
            _, _, payload = read_segment(f"{edit}/{r['segment']}")
            ok_digest = e and e["payload_sha256"] == sha256_file(f"{edit}/{r['segment']}", payload) and e["segment_sha256"] == sha256_file(f"{edit}/{r['segment']}")
            check(f"{rid}: catalogue digests equal the recomputed digests of the edited segment", ok_digest)
            check(f"{rid}: digests differ from the original's (the edit is visible)", e["payload_sha256"] != r["payload_sha256"])
        else:
            check(f"{rid}: catalogue entry unchanged", e == r)
    check("model identity field unchanged (the derivation is recorded separately)", oi["model"] == ei["model"])
    # 3. Segment header and tensor table identical; payload diff is exactly the declared elements.
    expected = {}
    for ed in man["edits"]:
        r = oi["representations"][f'{ed["object"]}@BF16']
        h, hraw, payload = read_segment(f"{orig}/{r['segment']}")
        h2, hraw2, payload2 = read_segment(f"{edit}/{r['segment']}")
        check(f"{ed['object']}: segment header bytes identical", hraw == hraw2 and payload == payload2)
        t = next(x for x in h["tensors"] if x["name"] == ed["tensor"])
        rows, cols = t["shape"]
        mo = np.memmap(f"{orig}/{r['segment']}", dtype=np.uint16, mode="r", offset=payload, shape=((os.path.getsize(f"{orig}/{r['segment']}") - payload) // 2,))
        me = np.memmap(f"{edit}/{r['segment']}", dtype=np.uint16, mode="r", offset=payload, shape=mo.shape)
        for c in ed["cols"]:
            idx = (t["offset"] // 2) + ed["row"] * cols + c
            old = int(mo[idx])
            oldv = float(np.array([old << 16], dtype=np.uint32).view(np.float32)[0])
            expected[(ed["object"], ed["tensor"], ed["row"], c)] = (idx, old, bf16_bits_of(oldv + float(np.float32(ed["delta"]))))
        # full-segment scan for every differing element
        actual = {}
        for s in range(0, mo.size, CHUNK):
            a, b = mo[s:s + CHUNK], me[s:s + CHUNK]
            for k in np.flatnonzero(a != b):
                actual[s + int(k)] = (int(a[k]), int(b[k]))
        want = {v[0]: (v[1], v[2]) for k, v in expected.items() if k[0] == ed["object"]}
        check(f"{ed['object']}: the set of changed elements equals the declared set", set(actual) == set(want),
              f"{len(actual)} changed, {len(want)} declared" + ("" if set(actual) == set(want) else f"; unexpected {sorted(set(actual)-set(want))[:5]}, missing {sorted(set(want)-set(actual))[:5]}"))
        wrong = {i: (want[i], actual[i]) for i in want if i in actual and want[i] != actual[i]}
        check(f"{ed['object']}: every changed element holds exactly the declared value", not wrong,
              f"{len(want) - len(wrong)} of {len(want)} exact" + (f"; first mismatch {next(iter(wrong.items()))}" if wrong else ""))
    # 4. The provenance record agrees with what was observed. The native ledger (weight_patches.json,
    #    schema weight-patches/v1) is checked field by field against the declared manifest and the observed bits;
    #    the prototype's sidecar (weight_patch.json) is accepted for the older containers.
    native, proto = f"{edit}/weight_patches.json", f"{edit}/weight_patch.json"
    if os.path.exists(native):
        rec = json.load(open(native))
        check("ledger schema is weight-patches/v1 with the declared rounding rule",
              rec["schema"] == "weight-patches/v1" and rec["rounding"] == "bf16-rne-of-exact-sum")
        seen = {(rec["target"]["object"], rec["target"]["tensor"], e["row"], e["col"]): (e["old_bits"], e["new_bits"]) for e in rec["edits"]}
        want_rec = {k: (v[1], v[2]) for k, v in expected.items()}
        check("ledger lists exactly the declared edits with the observed old and new bits", seen == want_rec)
        d_ok = all(e["delta_bits"] == int(np.float32(next(m["delta"] for m in man["edits"] if m["tensor"] == rec["target"]["tensor"])).view(np.uint32)) for e in rec["edits"])
        check("ledger delta bits equal the declared delta as an f32", d_ok)
        check("ledger names the source model and the source index digest of the ORIGINAL container",
              rec["source"]["model"] == oi["model"] and rec["source"]["index_sha256"] == sha256_file(f"{orig}/index.json"))
        canon = next(r for r in ei["representations"].values() if "compiled_from" not in r and r["object"] in edited_objects)
        check("ledger result digests equal the recomputed digests of the edited canonical segment",
              rec["result"]["canonical"]["payload_sha256"] == canon["payload_sha256"] == sha256_file(f"{edit}/{canon['segment']}", read_segment(f"{edit}/{canon['segment']}")[2]))
        check("ledger source canonical digests equal the ORIGINAL's",
              rec["source"]["canonical"]["payload_sha256"] == oi["representations"][rec["target"]["representation"]]["payload_sha256"])
    elif os.path.exists(proto):
        rec = json.load(open(proto))
        seen = {(e["object"], e["tensor"], e["row"], e["col"]): (e["old_bits"], e["new_bits"]) for e in rec["edits"]}
        want_rec = {k: (v[1], v[2]) for k, v in expected.items()}
        check("provenance record lists exactly the declared edits with the observed old and new bits", seen == want_rec)
        check("provenance record names the source model", rec["derived_from"]["model"] == oi["model"])
    else:
        check("provenance record present", False)
    print("\nWEIGHT_PATCH_EXACT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
