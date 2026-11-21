"""Does each later gate catch a bad kernel by itself, with the earlier ones switched off? Validation only."""
import json, os, subprocess
H = os.path.expanduser("~/chris-models/ncp001")
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = [("reverse-blocks", "unit_tests", "conformance"), ("fused-mul-add", "unit_tests", "conformance"), ("binary64-acc", "unit_tests", "conformance"),
         ("reverse-blocks", "unit_tests,conformance", "logits"), ("binary64-acc", "unit_tests,conformance", "logits"), ("fused-mul-add", "unit_tests,conformance", "logits"),
         ("reverse-blocks", "unit_tests,conformance,logits", "seq"), ("binary64-acc", "unit_tests,conformance,logits", "seq"), ("fused-mul-add", "unit_tests,conformance,logits", "seq")]
out = []
for name, skip, expect in CASES:
    env = {**os.environ, "NCP001_VALIDATE_SKIP": skip}
    p = subprocess.run([f"{H}/venv/bin/python", "-I", f"{HERE}/evaluate.py", f"{H}/validate/{name}.rs", f"layer-{name}"], capture_output=True, text=True, env=env, timeout=7200)
    r = json.loads(p.stdout) if p.returncode == 0 else {"failed_at": "CRASH", "feedback": p.stderr[-300:]}
    line = {"fault": name, "skipped": skip, "failed_at": r["failed_at"], "expected": expect if expect != "logits" or name != "flush-subnormal-x" else "conformance-or-later", "seq": r.get("seq"), "feedback": r["feedback"][:110]}
    out.append(line); print(json.dumps(line), flush=True)
json.dump(out, open(f"{H}/validate/layers.json", "w"), indent=1)
