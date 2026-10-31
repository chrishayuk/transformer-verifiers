"""OQ2: scan the pinned upstream checkpoint for Q8_0 blocks whose reference encoding is undefined.

ggml facdc44a, src/ggml-quants.c:276-299, quantize_row_q8_0_ref:

    amax = MAX(amax, fabsf(v))            MAX(a,b) = (a) > (b) ? (a) : (b)    (ggml-impl.h:40)
    d    = amax / 127                     f32
    id   = d ? 1.0f/d : 0.0f              f32
    x0   = x * id                         f32
    y.qs[j] = roundf(x0)                  float -> int8_t: undefined (C11 6.3.1.4) unless the
                                          integral value roundf(x0) lies in [-128, 127]

Blocks: 32 consecutive elements along each tensor's last dimension (SPEC rev 2 §8.4), BF16
widened exactly to f32 (bits << 16).

Classes (a block may be in both (a) and (b); (c) is disjoint from both):
  (a) the block contains a NaN
  (b) the block contains +inf or -inf
  (c) a finite block with amax > 0 where id overflows to inf, or any roundf(x0) is outside
      [-128, 127] or non-finite

Arithmetic: numpy float32 for the bulk (IEEE binary32 RNE, subnormals kept; numpy does not set
FTZ/DAZ). roundf range test: roundf(x0) in [-128, 127]  <=>  -128.5 < x0 < 127.5 (roundf rounds
half away from zero), which is false for NaN. Cross-checks with the exact-rational model
(e1/ggmlref.py, lib/exactfp.py): every tensor's smallest-nonzero-amax block and largest-|x0|
block are re-encoded exactly, and must match the numpy amax, d, id and x0 bit patterns. The id
overflow threshold is derived exactly, not from numpy.

Run: <python with numpy> -I oq2/scan_upstream.py [model.safetensors]
Writes oq2/results.json. Deterministic (no randomness, fixed tensor order = safetensors header
order sorted by key).
"""
import hashlib
import json
import os
import sys
from fractions import Fraction

import numpy as np

R = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(R, "..", "lib"))
sys.path.insert(0, os.path.join(R, "..", "e1"))
from exactfp import F32, decode, encode, div, rnd, from_int  # noqa: E402
import ggmlref  # noqa: E402

DEFAULT = os.path.expanduser(
    "~/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B/snapshots/"
    "c1899de289a04d12100db370d81485cdf75e47ca/model.safetensors")
PIN_SHA = "f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b"
PROJ = ("self_attn.q_proj.weight", "self_attn.k_proj.weight", "self_attn.v_proj.weight",
        "self_attn.o_proj.weight", "mlp.gate_proj.weight", "mlp.up_proj.weight",
        "mlp.down_proj.weight")
CHUNK = 1 << 20  # blocks per chunk


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def is_projection(key):
    """SPEC rev 2 §11.3: the 196 decoder-linear tensors that the default policy compiles."""
    if not key.startswith("model.layers."):
        return False
    rest = key[len("model.layers."):]
    L, _, name = rest.partition(".")
    return L.isdigit() and name in PROJ


def exact_id_threshold():
    """Smallest positive f32 amax whose id = RN(1/RN(amax/127)) is finite, found exactly.

    id is non-increasing in amax for amax > 0, so bisection over positive f32 bit patterns works.
    """
    one, c127 = from_int(1), from_int(127)

    def id_finite(bits):
        a = decode(bits, F32)
        d = rnd(div(a, c127), F32)
        if d.kind == "zero":
            return None  # id = 0 (defined) -- below the f32 resolution of amax/127
        i = rnd(div(one, d), F32)
        return i.kind != "inf"

    lo, hi = 1, 0x7F7FFFFF  # lo: not finite (or d == 0), hi: finite
    assert id_finite(hi) and not id_finite(lo)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if id_finite(mid):
            hi = mid
        else:
            lo = mid
    d_hi = rnd(div(decode(hi, F32), c127), F32)
    # amax values for which d rounds to 0 (then id = 0, all codes 0, defined)
    zlo, zhi = 1, hi
    while zhi - zlo > 1:
        mid = (zlo + zhi) // 2
        if rnd(div(decode(mid, F32), c127), F32).kind == "zero":
            zlo = mid
        else:
            zhi = mid
    zero_d_max = zlo if rnd(div(decode(zlo, F32), c127), F32).kind == "zero" else None
    return {"amax_min_finite_id_bits": "0x%08X" % hi,
            "amax_min_finite_id": float(decode(hi, F32).value()),
            "amax_max_overflowing_id_bits": "0x%08X" % lo,
            "amax_max_overflowing_id": float(decode(lo, F32).value()),
            "d32_at_threshold_bits": "0x%08X" % encode(d_hi, F32),
            "amax_max_with_d_zero_bits": None if zero_d_max is None else "0x%08X" % zero_d_max,
            "note": "positive f32 amax in [smallest subnormal, amax_max_overflowing_id] gives "
                    "d != 0 with 1/d overflowing to +inf (undefined conversions), except amax "
                    "values whose d rounds to +0 (id = 0, defined)"}


def exact_check(block_bits_u32, np_amax, np_d, np_id, np_x0):
    """Re-encode one block exactly and compare with numpy's f32 results (bit patterns)."""
    xs = [decode(int(b), F32) for b in block_bits_u32]
    q = ggmlref.quantize_block(xs)

    def bits(v):
        return None if v.is_nan() else encode(v, F32)
    got = (int(np.float32(np_amax).view(np.uint32)), int(np.float32(np_d).view(np.uint32)),
           int(np.float32(np_id).view(np.uint32)))
    exp = (bits(q["amax"]), bits(q["d32"]), bits(q["id"]))
    assert got == exp, ("amax/d/id mismatch", got, exp)
    for x0n, x0e in zip(np_x0, q["x0"]):
        if x0e.is_nan():
            assert np.isnan(x0n)
        else:
            assert int(np.float32(x0n).view(np.uint32)) == encode(x0e, F32)
    return q


def scan_tensor(raw_u16):
    """raw_u16: 1-D uint16 BF16 payload (last dim multiple of 32). Returns stats dict."""
    nb = raw_u16.size // 32
    st = dict(blocks=nb, elements=int(raw_u16.size), nan_elements=0, inf_elements=0,
              a_blocks=0, a_elements_undefined=0, b_blocks=0, b_elements_undefined=0,
              c_blocks=0, c_elements_undefined=0, c_id_overflow_blocks=0,
              amax_zero_blocks=0, min_nonzero_amax=None, min_nonzero_amax_block=None,
              max_abs_x0=0.0, max_abs_x0_block=None, max_abs_code=0, max_amax=0.0)
    min_amax = np.float32(np.inf)
    for s in range(0, nb, CHUNK):
        e = min(nb, s + CHUNK)
        u = raw_u16[s * 32:e * 32].astype(np.uint32) << 16
        x = u.view(np.float32).reshape(-1, 32)
        isnan = np.isnan(x)
        isinf = np.isinf(x)
        st["nan_elements"] += int(isnan.sum())
        st["inf_elements"] += int(isinf.sum())
        bnan = isnan.any(axis=1)
        binf = isinf.any(axis=1)
        ax = np.abs(x)
        amax = ax.max(axis=1)  # exact for NaN-free blocks (max of non-negative values)
        if bnan.any():  # MAX(a,b) sequential semantics: recompute those blocks exactly
            for bi in np.nonzero(bnan)[0]:
                q = ggmlref.quantize_block([decode(int(b), F32) for b in u.reshape(-1, 32)[bi]])
                a = q["amax"]
                amax[bi] = np.nan if a.is_nan() else np.uint32(encode(a, F32)).view(np.float32)
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            d = amax / np.float32(127.0)
            idv = np.where(d != 0, np.float32(1.0) / np.where(d != 0, d, np.float32(1.0)),
                           np.float32(0.0)).astype(np.float32)
            x0 = x * idv[:, None]
        undef = ~((x0 > np.float32(-128.5)) & (x0 < np.float32(127.5)))
        nund = undef.sum(axis=1)
        finite_blk = ~(bnan | binf)
        cblk = finite_blk & (amax > 0) & (np.isinf(idv) | (nund > 0))
        st["a_blocks"] += int(bnan.sum())
        st["a_elements_undefined"] += int(nund[bnan].sum())
        st["b_blocks"] += int(binf.sum())
        st["b_elements_undefined"] += int(nund[binf].sum())
        st["c_blocks"] += int(cblk.sum())
        st["c_elements_undefined"] += int(nund[cblk].sum())
        st["c_id_overflow_blocks"] += int((finite_blk & (amax > 0) & np.isinf(idv)).sum())
        st["amax_zero_blocks"] += int((finite_blk & (amax == 0)).sum())
        fin = finite_blk & (amax > 0)
        if fin.any():
            st["max_amax"] = max(st["max_amax"], float(amax[fin].max()))
            am = np.where(fin, amax, np.float32(np.inf))
            j = int(np.argmin(am))
            if am[j] < min_amax:
                min_amax = am[j]
                st["min_nonzero_amax_block"] = s + j
            ab = np.where(fin[:, None], np.abs(x0), np.float32(0)).max(axis=1)
            k = int(np.argmax(ab))
            if float(ab[k]) > st["max_abs_x0"]:
                st["max_abs_x0"] = float(ab[k])
                st["max_abs_x0_block"] = s + k
            xf = x0[fin]
            r = np.where(xf < 0, -np.floor(-xf.astype(np.float64) + 0.5),
                         np.floor(xf.astype(np.float64) + 0.5))
            st["max_abs_code"] = max(st["max_abs_code"], int(np.abs(r).max()))
    if np.isfinite(min_amax):
        st["min_nonzero_amax"] = float(min_amax)
        st["min_nonzero_amax_bits"] = "0x%08X" % int(np.float32(min_amax).view(np.uint32))
    # exact cross-checks
    for key in ("min_nonzero_amax_block", "max_abs_x0_block"):
        bi = st[key]
        if bi is None:
            continue
        u = raw_u16[bi * 32:(bi + 1) * 32].astype(np.uint32) << 16
        x = u.view(np.float32)
        am = np.abs(x).max()
        dd = am / np.float32(127.0)
        with np.errstate(divide="ignore", over="ignore"):
            ii = np.float32(1.0) / dd if dd != 0 else np.float32(0.0)
            xx = x * ii
        exact_check(u, am, dd, ii, xx)
    st["exact_crosschecks"] = 2 if st["max_abs_x0_block"] is not None else 0
    return st


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    digest = sha256(os.path.realpath(path))
    assert digest == PIN_SHA, "model.safetensors sha256 %s != pinned %s" % (digest, PIN_SHA)
    with open(path, "rb") as f:
        n = int.from_bytes(f.read(8), "little")
        hdr = json.loads(f.read(n))
    hdr.pop("__metadata__", None)
    mm = np.memmap(path, dtype=np.uint8, mode="r", offset=8 + n)
    per = {}
    for key in sorted(hdr):
        t = hdr[key]
        assert t["dtype"] == "BF16", (key, t["dtype"])
        s, e = t["data_offsets"]
        shape = t["shape"]
        assert shape[-1] % 32 == 0, (key, shape)
        raw = np.frombuffer(mm[s:e], dtype="<u2")
        st = scan_tensor(raw)
        st["shape"] = shape
        st["projection"] = is_projection(key)
        per[key] = st
        print("%-50s blocks=%9d a=%d b=%d c=%d minamax=%s" % (key, st["blocks"], st["a_blocks"],
              st["b_blocks"], st["c_blocks"], st["min_nonzero_amax"]), file=sys.stderr)

    def total(keys):
        T = {k: sum(per[t][k] for t in keys) for k in
             ("blocks", "elements", "nan_elements", "inf_elements", "a_blocks", "a_elements_undefined",
              "b_blocks", "b_elements_undefined", "c_blocks", "c_elements_undefined",
              "c_id_overflow_blocks", "amax_zero_blocks", "exact_crosschecks")}
        T["tensors"] = len(keys)
        mins = [(per[t]["min_nonzero_amax"], t) for t in keys if per[t]["min_nonzero_amax"] is not None]
        m = min(mins)
        T["min_nonzero_amax"] = m[0]
        T["min_nonzero_amax_bits"] = per[m[1]]["min_nonzero_amax_bits"]
        T["min_nonzero_amax_tensor"] = m[1]
        mx = max((per[t]["max_abs_x0"], t) for t in keys)
        T["max_abs_x0"] = mx[0]
        T["max_abs_x0_tensor"] = mx[1]
        T["max_abs_code"] = max(per[t]["max_abs_code"] for t in keys)
        T["max_amax"] = max(per[t]["max_amax"] for t in keys)
        T["max_amax_tensor"] = max((per[t]["max_amax"], t) for t in keys)[1]
        T["undefined_blocks_any_class"] = T["a_blocks"] + T["b_blocks"] + T["c_blocks"]  # upper bound if a and b overlap
        return T

    proj = [k for k in per if per[k]["projection"]]
    assert len(proj) == 196 and len(per) == 311, (len(proj), len(per))
    thr = exact_id_threshold()
    out = {"checkpoint": os.path.realpath(path), "sha256": digest,
           "ggml": "facdc44a67da17df4433adcc468b424f48e9ded2 src/ggml-quants.c:276-299",
           "id_overflow_threshold": thr,
           "totals": {"projections_196": total(proj), "all_311": total(sorted(per))},
           "per_tensor": per}
    for name, T in out["totals"].items():
        amin = Fraction(T["min_nonzero_amax"])
        athr = Fraction(thr["amax_min_finite_id"])
        T["margin_min_amax_over_threshold"] = float(amin / athr)
        T["margin_log2"] = float(np.log2(float(amin)) - np.log2(float(athr)))
    with open(os.path.join(R, "results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(out["totals"], indent=1, sort_keys=True))
    print(json.dumps(thr, indent=1))


if __name__ == "__main__":
    main()
