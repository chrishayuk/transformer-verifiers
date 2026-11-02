"""Is the candidate container's Q8_0 byte-identical to pinned ggml's encoder, and is everything else unchanged?

Development only (D15). Usage: check_candidate_bytes.py <candidate container> [baseline container]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import attribute_encoder as A  # noqa: E402
import larql_verify as L  # noqa: E402
from refcheck import container as C  # noqa: E402
from refcheck import harness as H  # noqa: E402

cand = C.open_container(sys.argv[1])
base = C.open_container(sys.argv[2] if len(sys.argv) > 2 else L.CONTAINER)
Wu = H.load_upstream(L.SNAPSHOT)
encode = A.ggml_encoder()
q = H.container_quantised_keys(cand)
assert q == H.container_quantised_keys(base)
cm, bm = cand.hf_key_map(), base.hf_key_map()
assert sorted(cm) == sorted(bm)
out = {"q8_tensors": len(q), "q8_differ_from_ggml": [], "q8_differ_from_baseline": 0, "other_tensors": 0, "other_differ_from_baseline": []}
for k in cm:
    raw = cand.read_bytes(cm[k])
    if k in q:
        if raw != encode(Wu[k]):
            out["q8_differ_from_ggml"].append(k)
        out["q8_differ_from_baseline"] += raw != base.read_bytes(bm[k])
    else:
        out["other_tensors"] += 1
        if raw != base.read_bytes(bm[k]):
            out["other_differ_from_baseline"].append(k)
print(json.dumps(out, indent=1))
sys.exit(1 if out["q8_differ_from_ggml"] or out["other_differ_from_baseline"] else 0)
