"""Baseline against candidate: the arrays that must be identical, and the measurements side by side. Development only (D15).
Usage: compare_candidate.py <candidate suite dir> [--json out]"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "runs", "suite-v1")
ATTR = os.path.join(HERE, "runs", "attribution-v1")
CAND = os.path.abspath(sys.argv[1])
b, c = json.load(open(os.path.join(BASE, "report.json"))), json.load(open(os.path.join(CAND, "report.json")))


def h(p):
    s = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            s.update(chunk)
    return s.hexdigest()


out = {"verdict": c["verdict"], "baseline_verdict": b["verdict"], "cases": {}, "identity": {}}
ident = {"tokens": 0, "bf16_reference_same_as_baseline": 0, "decoded_reference_same_as_attribution_G": 0, "dump_differs_from_baseline": 0}
for cid, cc in c["cases"].items():
    bb = b["cases"][cid]
    bd, cd, ad = os.path.join(BASE, cid), os.path.join(CAND, cid), os.path.join(ATTR, cid)
    ident["tokens"] += cc["token_ids_sha256"] == bb["token_ids_sha256"]
    ident["bf16_reference_same_as_baseline"] += h(f"{bd}/ref_bf16_f32.npy") == h(f"{cd}/ref_bf16_f32.npy")
    ident["decoded_reference_same_as_attribution_G"] += h(f"{cd}/ref_q8_0_f32.npy") == h(f"{ad}/ref_G_f32.npy")
    ident["dump_differs_from_baseline"] += h(f"{bd}/larql.f32") != h(f"{cd}/larql.f32")
    out["cases"][cid] = {"n": cc["n_tokens"], "verdict": cc["verdict"], "ingestion": cc["ingestion"], "larql_seconds": [bb["larql_seconds"], cc["larql_seconds"]]}
    for k in ("E2", "E3", "reference_quantisation_drift"):
        out["cases"][cid][k] = {f: [bb[k][f], cc[k][f]] for f in ("max_abs_diff_max", "rms_diff_mean", "kl_mean", "kl_max", "n_top1_disagree")}
        out["cases"][cid][k]["non_comparable"] = cc[k]["non_comparable_indices"]
    for w in ("larql_vs_f64", "ref32_vs_f64"):
        out["cases"][cid][w] = {"max": [bb["f64"][w]["max_abs_diff"]["max"], cc["f64"][w]["max_abs_diff"]["max"]],
                                "median": [bb["f64"][w]["max_abs_diff"]["median"], cc["f64"][w]["max_abs_diff"]["median"]],
                                "top1": cc["f64"][w]["n_top1_disagree"]}
    out["cases"][cid]["ratio_median"] = [bb["f64"]["ratio_larql_over_ref32"]["median"], cc["f64"]["ratio_larql_over_ref32"]["median"]]
out["identity"] = ident
out["e1"] = {"baseline": b["e1"]["lossy_q8_0"], "candidate": c["e1"]["lossy_q8_0"], "exact_baseline": b["e1"]["exact_storage"]["all_bit_identical"], "exact_candidate": c["e1"]["exact_storage"]["all_bit_identical"]}
print(json.dumps(out, indent=1, sort_keys=True))
