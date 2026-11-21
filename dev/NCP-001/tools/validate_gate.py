"""Before any agent runs: known-bad kernels must be rejected, and an unchanged copy must pass at a ratio near 1.0."""
import json, os, subprocess, sys
H = os.path.expanduser("~/chris-models/ncp001")
K = f"{H}/build/crates/larql-compute/src/cpu/kquant_gemv.rs"
src = open(K).read()
LOOP = "acc += ((c as i8 as f32) * d) * xs[j];"
FAULTS = {
    "reverse-blocks": lambda s: s.replace("for b in 0..per_row {", "for b in (0..per_row).rev() {"),
    "fused-mul-add": lambda s: s.replace(LOOP, "acc = ((c as i8 as f32) * d).mul_add(xs[j], acc);"),
    "binary64-acc": lambda s: s.replace("let mut acc = 0.0f32;", "let mut acc = 0.0f64;").replace(LOOP, "acc += ((c as i8 as f64) * d as f64) * xs[j] as f64;").replace("    acc\n}", "    acc as f32\n}"),
    "flush-subnormal-x": lambda s: s.replace(LOOP, "let v = if xs[j].is_subnormal() { 0.0 } else { xs[j] }; acc += ((c as i8 as f32) * d) * v;"),
    "last-rows-wrong": lambda s: s.replace("*slot = row_dot(blocks, x, chunk * CHUNK_ROWS + i, per_row);", "*slot = row_dot(blocks, x, chunk * CHUNK_ROWS + i, per_row) + if n % 33 == 0 && chunk > 0 { 1.0 } else { 0.0 };"),
    "copy-aa": lambda s: s,
}
os.makedirs(f"{H}/validate", exist_ok=True)
results = []
for name, f in FAULTS.items():
    text = f(src)
    if name != "copy-aa" and text == src:
        sys.exit(f"{name} changed nothing")
    p = f"{H}/validate/{name}.rs"
    open(p, "w").write(text)
    out = subprocess.run([f"{H}/venv/bin/python", "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluate.py"), p, f"validate-{name}"], capture_output=True, text=True)
    r = json.loads(out.stdout) if out.returncode == 0 else {"candidate": name, "CRASH": out.stderr[-600:]}
    results.append(r)
    print(json.dumps({k: r.get(k) for k in ("candidate", "passed", "failed_at", "seq", "dev", "CRASH")})[:520], flush=True)
json.dump(results, open(f"{H}/validate/results.json", "w"), indent=1)
