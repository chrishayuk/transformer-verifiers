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

## Push 3: 2026-10-30, `2e8fd34` (checker run 3: native-f64 default, real checkpoint)

**The run:** the same settings as push 2, `--model sonnet`. Log: `checker-run-3.log`. The checker staged its changes,
but its `git commit` was refused by the permission layer, and it stopped without trying another route. **The
publisher made the commit with the checker's own message** after reviewing the staged diff: harness defaults
`"upstream"` → `"native"`, docstring, AMBIGUITIES, NEEDS, README and one test. The commit body records this.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 6517535`) | Clean: no trailers, lockfile unchanged, environment matches with 0 bad RECORD files, no new import kinds |
| Tests, rerun by the publisher | 177, OK, **none skipped**: the real-checkpoint test now runs |
| `verify_snapshot` on the re-acquired checkpoint (the checker's own run) | All 9 files pass, by size and SHA-256 |
| Real Qwen3-0.6B, upstream weights, 7 tokens | f32 total 12.09 s, native f64 total 12.65 s, mostly model build. Max \|ref32 − ref64\| = 3.99e-5 over 7 × 151,936 logits (harness sanity figure only; not the T3 pilot) |

## Checker run 4: 2026-10-31, `cd49069` (decision revision D1). Audited and pinned, NOT pushed

**The run:** the same settings (`d05ce78f…`), `--model sonnet`, from the brief that implements D1 (PROTOCOL.md
`81398e6`).
- **First attempt** (`checker-run-4.log`): headless mode had no edit permission. The checker read the D1 text and its
  code, planned the change, and stopped without trying another route. Nothing was written.
- **Second attempt** (`checker-run-4b.log`): the same session, continued with `--permission-mode acceptEdits` and
  `git add`/`git commit` allowed. The sandbox and deny rules were unchanged.
- **Inputs:** the checker worked from the published rule text only. It has never seen a reviewer case.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 2e8fd34`) | Clean: 1 new commit, no trailers, lockfile unchanged, environment matches (20,103 RECORD files, 0 bad), same two `.pth` hooks, no new import kinds (stdlib `json` only) |
| Tests, rerun by the publisher with `-W error` | 193, OK (177 before) |
| Changes | `e1.py` OQ1 domain classes and per-class counts; `metrics.py` OQ6 `non_comparable`; `container.py` OQ12 ownership check across the executed set and each encoding; tests; AMB-010 and AMB-017 marked decided by D1 |

**Pin.** `cd49069` is the revised checker for the next scoring run. It is pinned **before** any corpus revision 2
case is scored, so revision 2 is scored blind against it. Any later checker change needs a new pin, and its scoring
must name it.

**New ambiguities that need a protocol-owner decision:**
- **AMB-018:** which sets of representations are "compared together" under OQ12. The checker chose the executed set
  plus each uniform encoding.
- **AMB-019:** how non-finite E1 statistics are represented, and whether a NaN or infinite element error inside an
  in-domain block counts as exceeding T2. The checker counts it as exceeding.

## Checker run 5: 2026-10-31, `3337645` (decision revision D4, part A1). Audited and pinned, NOT pushed

**The run:** the same settings (`d05ce78f…`), `--model sonnet`, `--permission-mode acceptEdits`, with `git add`/`git
commit` allowed. It was briefed on D4's first bullet only (PROTOCOL.md `f80b7a4`). D5 was held uncommitted until this
run ended, so it was never exposed. Log: `checker-run-5.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh cd49069`) | Clean: 1 new commit, no trailers, lockfile unchanged, environment matches (20,103 RECORD files, 0 bad), no new imports |
| Scope | D4 A1 only: `refcheck/e1.py` (statistics for every tensor; a shared `_rel_frobenius`; `null` relative Frobenius error plus `zero_reference_norm` when ‖upstream‖ = 0), its tests, README, and an AMB-019 note. No reader, metric or D2 change |
| Tests, rerun by the publisher with `-W error` | 200, OK (193 before) |

**Pin.** `3337645` is the checker to be scored blind against the fresh D4 cases of corpus revision 3. Its pin comes
before that corpus is sealed. Scoring run 3 (the metric cases) uses `cd49069`, as D4 requires. This change doesn't
touch metric code.

**New ambiguity, recorded by the checker in AMB-019:** D4 does not say what a bit-identical tensor holding inf or NaN
reports. The checker reads "both are zero" literally: the error is 0, `rel_frobenius` is 0, and `ref_frobenius` is
non-finite.

## Checker run 6: 2026-10-31, `faaf587` (decision revision D5). Audited and pinned, NOT pushed

**The run:** the first run under the immutable protocol snapshot `isolation/snapshots/1bfc341/` (PROTOCOL.md
`79795f18…`), with settings `6f293a60…` (`ISOLATION.md` part 4), `--model sonnet`, `acceptEdits`, and `git add`/`git
commit` allowed. The checker verified the snapshot hash before starting. Log: `checker-run-6.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 3337645`) | Clean: 1 new commit, no trailers, lockfile unchanged, environment matches (20,103 RECORD files, 0 bad), no new imports |
| Scope | D5 only. `container.py`: ownership across every declared representation (AMB-018). `e1.py`: per-class counts of non-finite upstream elements in in-domain blocks, never within or exceeding (AMB-019). Tests, AMBIGUITIES.md, README. The D4 behaviour for bit-identical non-finite tensors is untouched, as briefed |
| Tests, rerun by the publisher with `-W error` | 211, OK (200 before) |

**Pin.** `faaf587` is the checker for scoring fresh D5 cases. Those cases are not yet built or sealed. The pin
precedes their seal.

**New point the checker recorded (in AMB-019, not decided):** a non-finite upstream element inside a block that is
itself outside T2's domain is already outside T2 through its block, so it is not counted by class.

## Checker run 7: 2026-10-31, `871b48b` and `310c174` (decision revision D7). Audited and pinned, NOT pushed

**The run:** snapshot `723d5ff` (PROTOCOL.md `edd3933f…`) and SPEC revision 4 (`8f3f7c2b…`), both verified by hash
by the checker. Settings `a8f65afa…`. Log: `checker-run-7.log`. It read no LARQL source, container or dump, and did
not run E2, E3 or T3.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh faaf587`) | Clean: 2 new commits, no trailers, lockfile unchanged, environment matches (20,103 RECORD files, 0 bad) |
| New imports | `torch` (locked, already used by the harness); stdlib `importlib` (the check that hub kernels are absent), `platform`, `decimal`, `fractions`, `contextlib` and others |
| Scope | D7: `config_compare.py` (comparator, type-aware exact equality via `numconv.py`), `readback.py` (explicit `MAPPING`, 43 entries), `pins.py` (eight runtime pins), `f64_patch.py` (pinned at sha256 `9e696928…`), `gate.py` (no metrics key unless the gate passes), harness integration, synthetic §17 surface. Tests: 88 + 72 new |
| Tests, rerun by the publisher with `-W error` | 373, OK (211 before) |

**Pin.** `310c174` is the D7 checker. Corpus revision 4 is not sealed against it, because D8 (score-scale rounding)
requires one more correction first. Revision 4 is to be sealed against the commit of that correction.

**Known non-compliance with D8, found in the audit:** the expected score scale is computed as `float(head_dim) **
-0.5`, the platform's `pow`. D8 requires the exact value rounded once. On this machine `pow` happens to give the
correctly rounded value for head_dim 16–256, which the coordinating session checked at 80 digits, while `1/sqrt`
misses on 6 of 10. So no outcome changes here, but the computation depends on the platform.

**New ambiguities, for the protocol owner:**
- **AMB-020:** the direction of sliding windows (the reference slides layers ≥ `max_window_layers`; SPEC §17.5 says
  LARQL slides those below). Not reached for the subject. A non-null authority window is treated as unresolved.
- **AMB-021:** twelve absent or unlisted value cases, for example absent per-layer geometry, which is treated as
  unresolved.
- **AMB-022:** the read-back mapping table, which needs review.
- **AMB-023:** thread counts are recorded, not asserted.
- **AMB-024:** the binary64 `1e-6` against `f64(f32(1e-6))` epsilon, already covered by D3 and D7.
- **AMB-025:** where the weight-tie pin is checked.
