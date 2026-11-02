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

## Checker run 8: 2026-10-31, `ab38748` (decision revision D8). Audited and pinned, NOT pushed

**The run:** snapshot `19ab645` (PROTOCOL.md `1e79ae8b…`, verified by the checker), settings `25fa1d9a…`. Log:
`checker-run-8.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 310c174`) | Clean: 1 commit, no trailers, lockfile unchanged, environment matches (0 bad RECORD files), no new imports |
| Scope | Q24: `numconv.inv_sqrt_binary64` computes the exact `1/√h` with integer arithmetic only (no `pow`, `sqrt` or float division; checked by an AST test and by a test that makes those functions raise). Q23: structured `unresolved_reasons` (field, site, what cannot be established). The sliding-window scope text. Also outside the brief: `synth.py` fixtures now write the exact scale, so no fixture depends on the platform's `pow`. Accepted, because it removes a platform dependence and changes no verdict |
| Tests, rerun by the publisher with `-W error` | 392, OK (373 before) |
| AMB-025 failure path | Exercised. `test_a_refused_construction_gives_no_logits_and_no_metrics` gives a tied config a differing head: construction is refused, the gate returns `invalid_comparison`, and there is no `metrics` key. Separate pin tests cover shared storage and differing heads |

**Pin.** `ab38748` is the checker that corpus revision 4 (the 33 D2 cases) is sealed against and scored against.

**New items (AMB-026), for the protocol owner:**
- **A stand-in with no `head_dim`:** the scale is unresolved rather than taken from the class default.
- **A stand-in with `attention_multiplier` or `query_pre_attn_scalar`:** the scale stays unresolved.
- **`readback.py:393`:** compares the reference's own `scaling` attribute with `float(hd) ** -0.5`. That is the
  pinned transformers' own computation on the reference side, not the container's declared value, so D8 does not
  cover it. It was left unchanged.

## Checker run 9: 2026-10-31, `688d8e3` and `147a24e` (decision revision D9 and clarification 1). Audited and pinned, NOT pushed

**The run:** snapshot `db08851` (PROTOCOL.md `63cae151…`, verified by the checker), settings `3f848cca…`. Log:
`checker-run-9.log`. D9 clarification 2 (`6360a4c`) was committed after this snapshot, and is not in the run's inputs.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh ab38748`) | Clean: 2 commits, no trailers, lockfile unchanged, environment matches (0 bad RECORD files), no new imports |
| Exception handling | Compliant with D9. Every broad `except Exception` returns `checker_error` (comparator, read-back, pins, construction, decode), commented "never as a refusal". The deliberate refusals (`ComparatorError`, `PinError`, `HarnessError`, `ComparisonInvalid`) are caught by name. Expected refusals are explicit checks in `authority_refusals`, run before any reference construction |
| Reason schema | `{category, field, key_path?, site?, message}`. Must-be-absent keys are `contradiction`; unknown keys are `unresolved` (SPEC §17.1). `key_path` is built while the keys are walked |
| Tests, rerun by the publisher with `-W error` | 427, OK (392 before) |
| AMB-023 | Logits were byte-identical at 1, 2, 4 and 8 threads (4 layers, 1024 wide, f32 and f64), so there is no thread pin. Counts are recorded. Limits: one host, one size |

**Pin.** `147a24e` is the D9 checker that corpus revision 5 is to be sealed and scored against.

**Not implemented (expected):** clarification 2's question 27 fallback, where a layer with no `geometry` object
inherits from `X.attention`. This checker compares absent geometry as missing, so it reports it as unresolved. Any
revision 5 case whose expectation depends on question 27 is therefore pending under D3. It is not scored against this
pin.

**New: AMB-027, for the protocol owner:**
- Categories on the reference side: a read-back difference, a failed pin and the weight-tie refusal are
  `contradiction`; an unmapped read-back key is `unresolved`; a stand-in on the subject is `unsupported`.
- Unprobed key types surface as `checker_error`.
- `rope_parameters: null` counts as declared.

## Checker run 10: 2026-10-31, `596cfe8`, `cb5a82a` and `e232720` (D9 clarification 3). Audited and pinned, NOT pushed

**The run:** snapshot `6f28db9` (PROTOCOL.md `2fac79c0…`, verified by the checker), settings `9bb1b621…`. Log:
`checker-run-10.log`. Clarification 4 (schema v1.1, `b838914`) postdates this snapshot and was not in its inputs.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 147a24e`) | Clean: 3 commits, no trailers, lockfile unchanged, environment matches (0 bad RECORD files), no new imports |
| Scope | Q27 geometry fallback (an absent object inherits; a present but incomplete one is `unresolved`); reason-field schema v1 (canonical `field`, a table copied in tests to catch drift, published in README); AMB-027 categories (a pin that cannot be evaluated is `checker_error`, a pin in real conflict is `contradiction`) |
| Soundness of derived-finding pruning | Checked by the publisher. `prune_derived` removes only reasons; the status comes from the **unpruned** rows (`mism` includes the shape rows), so pruning cannot turn an invalid comparison into `comparable`. Every branch of `_shape_finding` assigns at least one primary field, so a `shape_inventory` finding always has its primary and is never pruned alone |
| Tests, rerun by the publisher with `-W error` | 461, OK. The pinned predecessor `147a24e`, rerun from an extracted copy, has 427. The checker's report says "449 before", which is wrong; the change is 427 → 461 |

**Pin.** `e232720` is the checker that corpus revision 6 is sealed and scored against.

**New items, for the protocol owner:**
- **AMB-028:** schema v1 has no identifier for framing and identity checks (index version, graph schema, family,
  unreadable files) or for tensors not in the architecture. The checker reports these as `unknown_keys`, with the real
  location in `site` or `key_path`. The status is right, and the field identity is approximate.
- **AMB-029:** SPEC §17.2 states the geometry fallback per key, and the protocol applies it per object. The checker
  follows the protocol. This is over-strict if the SPEC reading was meant, and never accepts wrongly.

## Checker run 11: 2026-10-31, `fdee0cf`, `fe9b671` and `4bc93d3` (D10: D6 and metric aggregates). Audited and pinned, NOT pushed

**The run:** snapshot `c972d62` (PROTOCOL.md `8595bd28…`, verified by the checker), settings `b78f15d4…`. Log:
`checker-run-11.log`. A first launch did nothing (the brief was parsed as extra `--allowedTools` rules, and the checker
repository was unchanged). The run was relaunched with the brief on stdin.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh e232720`) | Clean: 3 commits, no trailers, lockfile unchanged, environment matches (0 bad RECORD files), no new imports |
| Scope | Only `refcheck/e1.py`, `refcheck/metrics.py`, their tests, README and AMBIGUITIES. The comparability gate is untouched |
| Exception and warning handling | One new `np.errstate(invalid="ignore")`, which quietens a signalling-NaN upstream value on conversion. It stays NaN and is counted. No new `except` |
| D6 | `numerical_metric_status` is `non_comparable_nonfinite` when any upstream element of the tensor is non-finite. The full-tensor metrics are then null, each with a reason. `upstream_nonfinite` gives `nan`/`+inf`/`-inf` counts. Bit identity is reported for every representation. Finite-subset diagnostics appear only as `finite_subset_*`. `absolute_frobenius_error` is published, with `err_frobenius` as an alias |
| Aggregates | `metrics.aggregate`: non-comparable positions appear only in the counts and indices, never in a rate's numerator or denominator. An empty comparable set is `aggregate_status: "empty_comparable_set"`, with null aggregates. An unknown status raises |
| Tests, rerun by the publisher with `-W error` | 476, OK (461 at `e232720`) |

**Pin.** `4bc93d3` is the checker that corpus revision 7 is sealed and scored against.

**New item, for the protocol owner: AMB-030.** It covers the checker's conventions where D6 is silent:
- Q8_0 bit identity against upstream, with the NaN payload caveat;
- `comparable` as the status of a finite tensor;
- the reason field, and the totals;
- (f) the per-block error distribution on a non-comparable tensor. It is left unchanged, so its top quantile can be
  inf while `max_abs_error` is null. D6 names only the full-tensor metrics. This is the one point that may need a
  ruling.

## Checker run 12: 2026-10-31, `1ff315e`, `1266d8d` and `1f82e64` (D12: T3 evaluator, f64 guard). Audited and pinned, NOT pushed

**The run:** snapshot `e056903` (PROTOCOL.md `99a391a6…`, verified by the checker), settings `33c9cf16…`. Brief:
`evidence/checker-briefs/checker-run-12-brief.md`, committed before the run. Log: `checker-run-12.log`. D12
clarification 1 (`bcd7613`, `ulp₃₂` confirmed) postdates the snapshot.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 4bc93d3`) | Clean: 3 commits, no trailers, lockfile unchanged, environment matches (0 bad RECORD files), no new imports |
| Scope | Only the new `refcheck/t3.py`, the guard in `refcheck/harness.py`, their tests, README and AMBIGUITIES. `f64_patch.py` and the reference numerics are unchanged |
| `ulp₃₂` against clarification 1 | Matches: 2⁻¹⁴⁹ for zero and the subnormal range, 2^(e−1−23) otherwise. The binade comes from `frexp`, which extracts the binary64 exponent exactly and is not a logarithm. It is computed from ref₆₄. A non-finite value, or \|x\| > FLT_MAX, makes the position non-comparable |
| Exactness | A binary64 filter decides only provably clear cases. Every other logit is decided with exact fractions; the proof is in the docstring, and it is tested at boundaries and against 16,000 all-fraction decisions per (c, k) |
| Exceptions | `evaluate_t3` maps an unexpected exception to `status: checker_error` with `verdict: null`, never a refusal or a verdict. The guard raises `F64PatchGuardError` (a `PinError`), which `reference_run` re-raises rather than recording. It fails loudly, never silently |
| Tests, rerun by the publisher with `-W error` | 514, OK (476 at `4bc93d3`) |

**Pin.** `1f82e64` is the checker that corpus revision 8 is sealed and scored against.

**For the owner, before revision 8 is sealed:**
- **AMB-031b, the overall verdict with non-comparable positions.** The checker returns `verdict: pass` when every
  logit at every comparable position passes, even if some evaluated positions are non-comparable. It lists those
  positions.
  - **This rule came from the run 12 brief written by the coordinating session,** not from the protocol. The brief
    said "a pass only if every evaluated logit at every comparable position passes and at least one position is
    comparable".
  - **D12 and D1 OQ6 say** a non-comparable position is "never a pass", and an untraced one falsifies Stage A. The
    hidden corpus, derived from the protocol alone, expects an overall verdict that is not a pass in that situation.
  - **The owner decides.** If it is "not a pass", the checker is corrected in a separate run.
- **AMB-031a / reviewer question 51, "beyond the binary32 finite range".** The checker and the corpus author, working
  independently, both read it as \|ref₆₄\| > FLT_MAX. Two hidden positions depend on the reading.

## Checker run 13: 2026-11-01, `b8d64ab` and `80608c3` (D12 clarification 2: the T3 outcome rule). Audited and pinned, NOT pushed

**The run:** snapshot `7f1b246` (PROTOCOL.md `76504d78…`, verified; the admitted logit-dump specification inside, not
implemented in this run), settings `c61f3ea9…`. Brief: `evidence/checker-briefs/checker-run-13-brief.md`. Log:
`checker-run-13.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 1f82e64`) | Clean: 2 commits, no trailers, lockfile unchanged, environment matches, no new imports |
| Scope | `refcheck/t3.py` (`summarise` and the definition string), its tests, README section 8, AMBIGUITIES. Nothing else |
| Outcome rule | `empty_comparable_set` when no evaluated position is comparable; otherwise `fail` on any comparable violation; otherwise `incomplete` if any evaluated position is non-comparable; otherwise `pass`. The same rule applies per band and class. `coverage_complete` is in every summary. Bands and classes with no evaluated position keep `no_evaluated_positions` |
| Representability | Non-comparable exactly when \|ref₆₄\| > FLT_MAX, compared on the binary64 value. FLT_MAX is asserted at import to equal (2 − 2⁻²³)·2¹²⁷. Tested at ±FLT_MAX (in range) and at ±(FLT_MAX + 2⁷⁵) (non-comparable) |
| `ulp₃₂` | Unchanged, and matches clarification 1. Tested at every power of two across both branches |
| Tests, rerun by the publisher with `-W error` | 519, OK (514 at `1f82e64`) |

**Pin.** `80608c3` is the checker that corpus revision 8 is sealed and scored against. `1f82e64` is preserved.

**New item, for the owner: AMB-032.**
- **The tension:** clarification 2 names "incomplete inputs" as a per-position reason, while D12 requires an incomplete
  triple to be refused before any verdict. The checker refuses at triple level, so no accepted triple can have a
  per-position incomplete input.
- **Why it is safe:** either reading avoids a false pass.
- **Still open:** the question becomes live with the future dump reader.

## Checker run 14: 2026-11-01, `6c92aa7` and `c2070c3` (D13 workstream 2: Phase 3 ingestion). Audited and pinned, NOT pushed

**The run:** snapshot `932de33` (PROTOCOL.md `78f49789…`; the admitted logit-dump specification `5ad44e33…` inside),
settings `fb08761d…`. Brief: `evidence/checker-briefs/checker-run-14-brief.md`. Log: `checker-run-14.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh 80608c3`) | Clean: 2 commits, no trailers, lockfile unchanged, environment matches, no new imports beyond the standard library (`subprocess`) |
| Scope | The new `refcheck/ingest.py`, `tests/stub_larql.py` (a stub written from the admitted specification), `tests/test_ingest.py`, README section 9, AMBIGUITIES. T3, `ulp₃₂`, the outcome rule, the reference numerics, the comparability gate, the metrics and the f64 guard are untouched |
| Runner | `subprocess.run` with an explicit environment, no shell, stdin closed, and a timeout. A timeout counts as a non-zero exit. A launch failure is recorded |
| Verifier | Every condition of the specification's §8.3, the Baseline plan rule, identity and hashes are checked before any row is read. It refuses the whole input with coded reasons, each mapped to a specification or protocol clause. An unexpected exception gives `checker_error`, never an acceptance |
| Extractor | Reads only the preregistered rows, from the bytes that were verified, with per-row hashes taken in the same pass. Unextracted rows are NaN, so they can never pass T3 |
| Tests, rerun by the publisher with `-W error` | 560, OK (519 at `80608c3`) |

**Pin.** `c2070c3` is the checker that the hidden ingestion corpus is sealed and scored against.

**New item, for the owner: AMB-033, the fail-closed readings.** The points that matter most:
- **(b)** The candidate's configuration fields, which LARQL never reports, are supplied as an input tied to the
  container hash and a D7-passing reference. On the candidate side they are asserted, not observed.
- **(j)** A consistently forged record claiming a different token sequence of the same length cannot be detected from
  the files. Protection rests on custody of the record (D11 draft §2a) and on T3 itself.
- **(h)** T3 takes full (N, V) arrays, so about 24.9 GB is held in memory at N = 40,960.
- **Strict matching** of stdout and sidecar, including the expected-not-observed 28 layers. A real-output detail could
  refuse every run, which is the safe direction. The first subject run must be checked against these choices.

## Checker run 15: 2026-11-02, `8c59122` and `e505afc` (D15 clarification 1: the `representation:` line, DO-1). Audited and pinned, NOT pushed

**The run:** snapshot `8b3663a` (PROTOCOL.md `927c0cb9…`; the admitted logit-dump specification `5ad44e33…` inside),
settings `22829887…`, `--model sonnet`, `acceptEdits`, `git add`/`git commit` allowed. Brief:
`evidence/checker-briefs/checker-run-15-brief.md`, committed before the run (`da47821`). Log: `checker-run-15.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh c2070c3`) | Clean: 2 commits, no trailers, lockfile unchanged, environment matches (20,103 RECORD files, 0 bad), no new imports |
| Scope | `refcheck/ingest.py`: +15/−1. The `representation` entry leaves the whole-line table and goes through `representation_line_ok` (`ln == REQUIRED or ln.startswith(REQUIRED + " ")`). Code, clause and message prefix are unchanged. Every other line, every other check, T3, the reference, the gate and the metrics are untouched. The stub prints the suffix by default. 11 new tests |
| Tests, rerun by the publisher with `-W error` | 571. Three full runs: OK, FAILED (1), OK |
| The failure | Always `Substitution.test_a_record_from_a_different_run`: 5 of 8 runs of `test_ingest.py` at `e505afc`, and **4 of 8 at `c2070c3`** (a read-only export, run by the publisher). It predates this run. The checker's diagnosis (AMB-034 (d)): two stub sidecars sometimes coincide, because their timing fields print to three decimals. This is a defect of the test fixture, not of the verifier. The run 14 record's "560, OK" was a passing draw. It is left for a later checker run, because this brief forbade other changes |

**Pin.** `e505afc` is the checker that corpus revision 9 is sealed and scored against (D15 clarification 1,
replacing `c2070c3`).

**For the owner: AMB-034.**
- "A space" means U+0020 only. A tab, a no-break space or `\r` after `stored` is refused.
- The checker lists the other exact-match lines that could mismatch real output, judged by the spec's text only:
  - `runtime compile:` is the highest risk;
  - then the two `wrote` lines, because of how paths are rendered;
  - then `engine:` and `positions:`.

  None is known to mismatch. The development runs accepted all of them on real output.
- The flaky substitution test above.

## Checker run 16: 2026-11-02, `b88757e` and `078d384` (D15 clarification 2: tests and records only). Audited and pinned, NOT pushed

**The run:** snapshot `5d1b1f1` (PROTOCOL.md `411a6922…`; `REAL-STDOUT-FIXTURES.json` `b68901ab…`), settings `d9a158e9…`,
`--model sonnet`, `acceptEdits`, `git add`/`git commit` allowed. Brief: `evidence/checker-briefs/checker-run-16-brief.md`,
committed before the run (`06d9ffb`). Log: `checker-run-16.log`.

| Check | Result |
|---|---|
| Audit (`tools/audit_checker.sh e505afc`) | 2 commits, no trailers, lockfile unchanged, worktree clean |
| `refcheck` tree | `e82a4425…`, identical to `e505afc`. The verifier did not change, so corpus revision 9's 79/79 still applies to it and is not rescored, and `dev/larql-verify` keeps its code (D15 clarification 2) |
| Scope | `tests/test_ingest.py` (the fixture repair), new `tests/test_real_stdout.py` (13 tests), `tests/fixtures/real_stdout.json`, `AMBIGUITIES.md`, `README.md` |
| The flake | The checker's own count: 17 of 24 runs of `test_ingest.py` before the repair, 0 of 24 after. Failure message: `'sidecar_sha256_mismatch' not found in {'dump_sha256_mismatch', 'modified_before_run_start'}`. The test requires every code it required before, and adds assertions of its fixture's premises |
| Tests, rerun by the publisher with `-W error` | 584. Five full runs, all OK. `test_ingest.py` 30 more runs, 0 failures |
| Mutation check, in a scratch export | With the sidecar hash check off, or the dump hash check off, the repaired test fails. With either modification-time check off alone it passes, because each gives the same code; with both off it fails (see below). Each of the `engine:`, `positions:` and two `wrote` readings altered: `test_real_stdout.py` fails |
| Real fixtures | All three accepted by the pinned code. No reading changed |

**Earlier records stay as written.** The run 15 entry, the failure counts at `c2070c3` and `e505afc`, and AMB-034 (d) are
unchanged. The run 14 record's "560, OK" remains what it was: a passing draw.

**A slip in the run.** The agent ran `git stash` by mistake, after both timing loops had finished, and restored it with
`git stash pop`. It disclosed this. The worktree and the committed result are consistent with its report.

**What the fixtures do not show.** Three runs of one binary on one machine, with ordinary output paths. AMB-034 (c) says so.
