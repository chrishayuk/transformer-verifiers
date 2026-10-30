# Checker publication audits

The publisher (the coordinating session) inspects every batch of checker commits before pushing them to
`chrishayuk/transformer-verifiers-checker`. The checker session itself cannot push.

## Push 1: 2026-10-30, `64353c1` (deliverables 1–3, checker run 1)

**The run:** headless, through `isolation/launch-checker.sh`, with settings `a4cc2006…`. The model was the session
default, Claude Sonnet 5.5, as the commit trailers show. Full log: `checker-run-1.log`.

| Check | Result |
|---|---|
| `requirements.in` / `requirements.lock` unchanged since `3d4f7f6` | yes |
| Installed distributions match the lockfile (names and versions) | yes: none extra, none missing, no version mismatch |
| Installed files against each distribution's `RECORD` hashes | 20,103 checked, 0 mismatched or missing |
| Editable or local-path installs (`direct_url.json`) | none |
| Startup hooks | `distutils-precedence.pth` (setuptools, covered by its RECORD) and `_virtualenv.pth` → `_virtualenv.py` (written by uv when the coordinating session created the venv at 21:22; stdlib imports only, no file, exec or network calls). No `sitecustomize` or `usercustomize` |
| Imports in checker code | stdlib, `numpy`, `gguf`, and its own `refcheck` / test modules only |
| Tracked files | 15, all text, mode 100644. No executables, binaries or untracked files outside `.venv/`, `.tmp/` and `__pycache__/` |
| LARQL-specific strings | only values quoted from the admitted SPEC (e.g. the `kquant-larql-native` encoder label) and from the protocol. No LARQL code |
| Test suite, rerun by the publisher | 94 tests, OK |
| Commit trailers | the three new commits carry `Co-Authored-By: Claude Sonnet 5.5`, because the run started before the no-attribution setting. Left unchanged as provenance |

**Ambiguities the checker raised that need a decision outside the checker:**
- **AMB-001:** a NaN result's bit pattern depends on the CPU. The checker compares NaN as "is NaN". The A0 rule
  "equals the analytic expectation exactly" needs to say whether that is acceptable.
- **AMB-005:** the reader does not enforce the subject's tensor census. Coverage is left to E1.
- **AMB-008:** the executed LM head is not reconstructible from the container. The checker decodes the stored BF16
  head. This matches the pinned baseline.

## Push 2: 2026-10-30, `6517535` (deliverables 4–6, checker run 2)

**The run:** headless, with settings `d05ce78f…` (attribution off) and `--model sonnet`. Log: `checker-run-2.log`.
**The audit:** `tools/audit_checker.sh 64353c1`.

| Check | Result |
|---|---|
| New commits | 3. No attribution trailers |
| Lockfile | Unchanged |
| Installed environment | Matches the lockfile. 20,103 RECORD files, 0 bad. No direct-URL installs. Same two `.pth` hooks as push 1. No `customize` modules |
| New imports | `torch`, `transformers` (Qwen3 modeling), `safetensors` (all locked), plus stdlib `decimal`, `math`, `platform`, `shutil`, `copy`, `contextlib` and `time` |
| Files | All text, mode 100644 |
| LARQL strings | Only in AMBIGUITIES.md, quoting the protocol and spec |
| Tests, rerun by the publisher with `-W error` | 176, OK, 1 skipped: the real-checkpoint test (see below) |

**The real checkpoint was not exercised.** The pinned Qwen3-0.6B HF cache entry had disappeared by the time of this
run. The whole `models--Qwen--*` family went from `~/.cache/huggingface/hub` at about 22:56, after isolation test
part 3 had read from it. The checker's sandbox denies writes there, and no session transcript on this machine
contains a command that deleted it. **The cause is unknown.** The checker logged it as NEEDS N-001.
The L1 container encoded from that snapshot is intact.

**An ambiguity that needs a protocol-owner decision: AMB-013.** Upstream `transformers` Qwen3 forces float32 inside
RMSNorm, the attention softmax and the RoPE tables. An "f64" run built from the unpatched model code is therefore
mostly f32 at those points. Measured on a synthetic model, it differs from a true f64 forward by 1.2e-7, against
3.7e-7 for the f32 run and 1.2e-15 for a native f64 forward. This weakens `|ref32 − ref64|` as the T3 yardstick. The
checker implements both modes, with `upstream` as the default and `native` recommended.

**Follow-up (2026-10-30, ~23:20):**
- **N-001 resolved.** The freeze owner approved re-acquiring the checkpoint. It was re-downloaded at HF commit
  `c1899de2…` into the same cache path, and all nine files match the pinned SHA-256 hashes, so the restored input is
  byte-identical to the original. The cause of the deletion is still unknown.
- **AMB-013 decided:** native f64, recorded in PROTOCOL.md under "A2 logit-match details".
