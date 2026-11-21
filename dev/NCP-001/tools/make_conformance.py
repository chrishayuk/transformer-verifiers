"""Conformance cases for NCP-001, from a seed: the corners real activations don't reach. Writes cases.tsv, inputs and expected bits.
Expected bits come from refcheck.gemv.seq_bits, the isolated checker's program. Inputs stay inside the contracts' domain."""
import os, sys
import numpy as np
from refcheck import gemv

out, seed = sys.argv[1], int(sys.argv[2])
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(seed)
ROWS = [1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65]
COLS = [32, 64, 96, 128, 1024]
SCALES = [0x0000, 0x8000, 0x0001, 0x8001, 0x03ff, 0x83ff, 0x0400, 0x3c00, 0xbc00, 0x7bff, 0xfbff]


def blocks(n, k, family):
    b = bytearray()
    for _ in range(n * (k // 32)):
        if family == "subnormal_scale":
            d = int(rng.choice([0x0001, 0x0002, 0x8001, 0x00e3, 0x03fc, 0x03ff, 0x83ff]))
        elif family == "edge_scale":
            d = int(rng.choice(SCALES))
        elif family in ("underflow", "subnormal_x"):
            d = int(rng.choice([0x0001, 0x0003, 0x0400, 0x3c00]))
        else:
            d = int(rng.integers(0x0400, 0x5000)) | int(rng.choice([0, 0x8000]))
        codes = rng.choice([-128, -127, -1, 0, 1, 127], 32) if family == "edge_codes" else rng.integers(-128, 128, 32)
        b += d.to_bytes(2, "little") + codes.astype(np.int8).tobytes()
    return bytes(b)


def activation(k, family):
    m = rng.normal(0, 1, k)
    if family == "wide":
        m = m * 2.0 ** rng.integers(-60, 40, k)
    elif family == "underflow":
        m = m * 2.0 ** -120
    elif family == "subnormal_x":
        # Binary32 subnormals and signed zeros, written directly.
        bits = rng.integers(0, 1 << 23, k, dtype=np.uint32) | (rng.integers(0, 2, k, dtype=np.uint32) << 31)
        bits[rng.integers(0, k, max(1, k // 8))] = 0x80000000
        return bits
    elif family == "tiny_large":
        # Large and small alternating: where a fused multiply-add or a reordered sum shows.
        m = m * np.where(np.arange(k) % 2 == 0, 2.0 ** 30, 2.0 ** -30)
    return m.astype(np.float32).view(np.uint32).copy()


FAMILIES = ["ordinary", "subnormal_scale", "edge_scale", "edge_codes", "wide", "underflow", "subnormal_x", "tiny_large"]
rows = []
for family in FAMILIES:
    for n in ROWS:
        for k in COLS:
            if n * k > 65 * 128 and k == 1024 and n not in (1, 3, 32, 33):
                continue
            cid = f"{family}-{n}x{k}"
            b, x = blocks(n, k, family), activation(k, family)
            want = gemv.seq_bits(b, x, n, k)
            if not all(gemv.check_seq(b, x, want, n, k).status == "satisfied" for _ in [0]):
                continue  # outside the contracts' domain: not a fair question
            for ext, data in (("blocks", b), ("x", x.astype("<u4").tobytes()), ("want", want.astype("<u4").tobytes())):
                with open(f"{out}/{cid}.{ext}", "wb") as f:
                    f.write(data)
            rows.append(f"{cid}\t{n}\t{k}\t{out}/{cid}.blocks\t{out}/{cid}.x\n")
with open(f"{out}/cases.tsv", "w") as f:
    f.writelines(rows)
print(len(rows), "cases from seed", seed)
