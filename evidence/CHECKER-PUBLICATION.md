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
