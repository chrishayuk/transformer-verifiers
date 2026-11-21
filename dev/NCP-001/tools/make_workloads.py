"""Capture NCP-001's benchmark workloads with the baseline binary. Dev and held-out use different prompts and different layers."""
import json, os, shutil, subprocess, sys

H = os.path.expanduser("~/chris-models/ncp001")
SUITE = os.path.expanduser("~/chris-source/transformer-verifiers/dev/larql-verify/runs/suite-v1")
C8 = os.path.expanduser("~/chris-models/q8enc-ad82acba/qwen3-0.6b-q8_0.vindex3")
OPS = ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj", "mlp.up_proj", "mlp.gate_proj", "mlp.down_proj"]
SETS = {"dev": (["prose-en", "code-python"], [2, 10, 18, 26], f"{H}/workload-dev"),
        "heldout": (["code-rust", "structured-json", "multilingual", "arithmetic"], [5, 13, 21], f"{H}/hidden/workload")}


def tokens(prompt, n=32):
    return json.load(open(f"{SUITE}/{prompt}/tokens.json"))["token_ids"][:n]


for name, (prompts, layers, out) in SETS.items():
    os.makedirs(out, exist_ok=True)
    rows = []
    wanted = {f"{l}.{op}.weight" for l in layers for op in OPS}
    for p in prompts:
        ids = ",".join(map(str, tokens(p)))
        w = f"{out}/witness-{p}"
        subprocess.run([f"{H}/bin/larql-baseline", "vindex3", "exec", C8, "--backend", "production-q8", "--representation-source", "stored",
                        "--tokens", ids, "--logit-dump", f"{out}/{p}.logits", "--gemv-witness", w, "--gemv-witness-max-operands", "400"],
                       check=True, capture_output=True, env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"]})
        m = json.load(open(f"{w}/witness.json"))
        for r in m["records"]:
            if r["tensor"] in wanted:
                cid = f"{p}.{r['tensor']}"
                b = f"{out}/{r['tensor']}.blocks"
                if not os.path.exists(b):
                    shutil.copy(f"{w}/{r['blocks']['file']}", b)
                x = f"{out}/{cid}.x"
                shutil.copy(f"{w}/{r['x']['file']}", x)
                rows.append(f"{cid}\t{r['rows']}\t{r['columns']}\t{b}\t{x}\n")
        shutil.rmtree(w)
    with open(f"{out}/cases.tsv", "w") as f:
        f.writelines(rows)
    with open(f"{out}/tokens.json", "w") as f:
        json.dump({p: tokens(p) for p in prompts}, f)
    print(name, len(rows), "cases")
