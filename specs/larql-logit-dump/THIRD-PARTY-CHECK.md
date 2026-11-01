# AMB-014 third-party check: LARQL logit-dump specification

| Field | Value |
|---|---|
| Role | **Third-party checker** of the logit-dump specification for LARQL-VERIFY-001 (decision AMB-014, PROTOCOL D12). Not the spec author and not the reference checker |
| Date | 2026-10-31 |
| Spec checked | `specs/larql-logit-dump/SPEC.md`, revision 1, commit `0e6de8f`, SHA-256 `48fe2666b5f0d11f7e274641a46eba80859838db3dbf88c484cc7a1b6afe1150`. I did not edit it |
| LARQL | Clean worktree `/Users/christopherhay/chris-source/larql-l1-2536bb79`, `HEAD` = `2536bb79b199b1115445678e3e82c400b0b3fd07`. `git status --porcelain` was empty before and after. I did not modify it |
| Build | `CARGO_TARGET_DIR=~/chris-source/logit-dump-check/target cargo build --release --offline` (rustc/cargo 1.98.0, the pinned toolchain). Exit 0 in 3m46s with no network. Default features (`gpu`, `research`). Binary `target/release/larql`, SHA-256 `ae6902f2e6a78c0c79b9bcbcc439859b5cd4d73ca0830013652ece3f8e0f315e`. This is **not** the subject binary: it was built separately, so its hash is not a pin |
| Host | Apple M3 Max, macOS (Darwin 27.0.0), `hw.perflevel0.l2cachesize` = 16 MiB, 12 performance cores |
| Fixture | A random, seeded, **non-subject** Qwen3-architecture checkpoint built by `make_fixture.py`. It has 2 layers, hidden 256, intermediate 512, 4 query heads, 2 KV heads, head_dim 64, vocab 20000, tied embeddings (stored twice, like the subject's `lm_head`), `max_position_embeddings` 128, `rope_theta` 1e6, and all weights BF16. `model.safetensors` SHA-256 is `af09ea60…c282`. It was encoded with `vindex3 encode` and then `vindex3 represent --encoding Q8_0`, both under `env -i PATH HOME`. The result has the same shape as the subject's container: `target.decoder_stack` is compiled to Q8_0, and the embedding, final norm and output head are preserved whole as BF16. The Q8_0 container's `index.json` SHA-256 is `0002936b…af76` |
| Not touched | The Qwen3-0.6B subject, its containers (`~/chris-models/…`) and Qwen3-1.7B. No LARQL run used any real model, and no real-model logits were produced. I did not read `checker/`, `~/chris-source/transformer-verifiers-reviewer`, `~/chris-source/transformer-verifiers-refaudit` or `evidence/freeze-review/`. Only the subject's `config.json` and `generation_config.json` were opened, as a template for the fixture's config keys |
| Scripts and raw output | Repository `~/chris-source/logit-dump-check`, commits `d53d34c` and `00e071d`. Contents: `make_fixture.py`; `accept.py` (the D12 procedure); `failure_modes.sh` with its log `records/failure_modes.log`; `layout_check.py`; `ref_forward.py`; per-run records `records/*.json`; `MANIFEST.sha256` (binary, fixture, containers, every dump) |

## Verdict

**ACCURATE WITH CORRECTIONS.**

Every normative statement about the dump file holds on emitted files: its bytes, shape, row and column order, sidecar, completeness and failure behaviour. None was refuted. The corrections are about exit codes, flags the parser does not reject, and when the stdout lines that the fail-closed rule relies on are printed. None of them changes the byte format. The D12 acceptance procedure accepted every conforming run and rejected every failure mode tried. The dump was bit-identical across repeated runs and across worker counts 1, 4 and 12.

## Corrections required for admission (not applied)

1. **C1, §7.2.1, exit status of argument-parser rejections.** The spec says every error "on this path" exits with status 1 after printing `Error: <message>`. That is true for errors returned from `run_exec` (`MAIN:455-459`). It is not true for clap rejections. `Cli::parse_from` (`MAIN:378`) exits the process itself with **status 2**, before any weight is loaded or any file is touched. Observed: `--logit-dump` with `--generate` gives exit 2 and the message "the argument '--logit-dump <LOGIT_DUMP>' cannot be used with '--generate <GENERATE>'". A repeated `--backend` also gives exit 2. The trampoline refusal also returns 2 (`trampoline.rs:57`). *Correction:* say that exit status is 0 on success, 1 for errors the command returns, and 2 for clap or trampoline refusals. A reader requires 0 and MUST NOT give any meaning to a particular non-zero value.
2. **C2, §2.2, generate-only flags are accepted and ignored alongside `--logit-dump`.** `--speculate`, `--stop-at-eos`, `--residency-curve` and `--profile` are declared `requires = "generate"` (`CLI/args.rs:245, 251, 259, 329`). Without `--logit-dump`, `--speculate 2` is rejected with exit 2. With `--logit-dump` present, clap does **not** enforce the requirement. Observed: `--speculate 2 --profile --stop-at-eos --residency-curve` exits 0, writes a dump bit-identical to the run without them, and writes a normal sidecar. `--repeat`, `--warmup`, `--unquiet-ok` and `--expert-access` (`requires = "residency_curve"`, `CLI/args.rs:266-283`) are presumably affected the same way, but I did not test them. The run is unaffected, but these flags are silently accepted. *Correction:* add a table row listing these flags as "accepted without error and ignored on this path (observed); MUST NOT be passed". The harness rule should be "exactly the conforming argument list" rather than "none of the forbidden flags". §2.2.1 (no flag selects positions) remains true. `--help` lists exactly these 22 `exec` flags (OI-14 below).
3. **C3, §7.3.2, when the acceptance lines are printed.** `runtime compile:`, `stored precision:` and `projection plans:` are printed only if the run succeeded **and** the backend asked for a stored representation (`report_representation_work` returns early when `want.is_none()`, `CLI/exec.rs:158`). `projection plans:` also needs at least one plan with calls (`CLI/exec.rs:199, 208`). The `representation:` line likewise needs `want` (`CLI/exec.rs:95`). Observed: `--backend production` gives exit 0, a complete dump and a sidecar whose `engine` is identical (OI-16), but **none** of these four lines. Under `production-q8`, `want` is `Q8_0`, so the lines appear on success, and the spec's conclusion holds. *Correction:* state both conditions. Add that the `representation:` line is printed **even when the run later fails** (observed on every mid-run and post-load failure). So the line's presence is not evidence of success.
4. **C4, §8.1.2, add the observed boundary cases.**
   - An out-of-range id at position k > 0 left **exactly k complete rows**: ids `1,2,3,20000,5` produced a 240,000-byte file (3 × 80,000), exit 1, no sidecar. So the destructor flush does happen.
   - An out-of-range id at position 0 leaves a **0-byte** dump file, because the file is created before the first step.
   - A missing output directory fails after weights are loaded, with exit 1 and no file. Its message, "No such file or directory (os error 2)", does not name the path.

   *Correction:* add these as observed informative notes. The normative rule (reject anything not exactly `4·N·V` with exit 0) is unchanged.
5. **C5, §11.3 and the PROTOCOL "Baseline" acceptance check, host dependence of the head's projection plan (informative).** The production plan for a BF16 matrix is chosen by size against the host's L2 (`crates/larql-vindex/src/format/vindex3/opplan/exec/cpu/physical/projection.rs:207-209`, threshold from `hw.perflevel0.l2cachesize`, `:541-549`). A matrix whose **f32 image fits in L2** runs `BlasF32`, whatever `LARQL_CPU_MAX_FORMAT` says. The `bf16` cap matters only when the BF16 image is at least L2 (`:218`). Observed: my first fixture (V = 10000, head 10.24 MB as f32, below the 16 MiB L2) ran the head as `BlasF32`. The acceptance procedure correctly **rejected** that run, and I enlarged the fixture to V = 20000 (20.48 MB as f32). For the subject, the head's f32 image is about 622 MB, far above any L2, so `FusedBf16` is expected and the Baseline rule is sound. *Correction (informative):* note in §11.3 that the plan depends on the host's L2 size, so the `projection plans:` check is a per-host observation, and a fixture used to test the procedure needs a head larger than L2. On this fixture, unsetting `LARQL_CPU_MAX_FORMAT` changed no value (bit-identical dump), because the head's BF16 image (10.24 MB) is below L2. Only the sidecar's `max_format_env` showed the difference.

## Per-section results

`CLI/`, `EX/`, `MAIN` and `CONT` are as defined in SPEC §0. "Fixture" means an observed run, recorded in `records/`.

| § | Statement | Result | Source evidence | Fixture evidence |
|---|---|---|---|---|
| 1 | `--logit-dump` → `run_teacher_force`; fresh session and KV; one `step` per token from position 0; no prefill | **Confirmed** | `CLI/exec.rs:80-131, 214-246`; `CLI/teacher_force.rs:39-134`; `EX/decode/steps.rs:139-142`; `EX/decode/run.rs:43, 674`; `production-q8` is not a lowered arm (`CLI/prepare.rs:174`, `None`) | stderr shows `weights resident … layers 0..2 of 2` and then per-position progress. **Prefix property:** the dump of the first 8 ids is bit-identical to the first 8 rows of the 200-id dump (`records/prefix8.json`, `records/long200a.json`) |
| 2.1 | Conforming invocation | **Confirmed** with C2 | — | `accept.py` uses exactly that argv under `env -i` |
| 2.2 | Flag table; `--bank` silently overrides; `--dump-layers`/`--resume`/`--generate` rejected | **Confirmed**, with C1 (exit 2) and C2 (accepted generate-only flags) | `CLI/args.rs:181-331`; `CLI/exec.rs:222-246` | `--bank` + `--dump-dir` + `--logit-dump`: exit 0, **no** dump and **no** sidecar at the `--logit-dump` path, `<dump-dir>/b0.f32` written, and stdout is the bank's (`banked 1 entries…`). `--bank` without `--dump-dir`: exit 1, "--bank requires --dump-dir". `--generate`: exit 2 |
| 2.2.2 | KV provider always `row/v1` | **Confirmed** (source) | `CLI/teacher_force.rs:54` passes `None`; `CONT:29-56, 125-134` | — |
| 2.3 | Token parsing: split on `,`, trim (Unicode), drop empty items, `u32::from_str`; failure aborts before load; ids ≥ V refused at their step | **Confirmed** | `CLI/exec.rs:506-518`; `EX/prepared/accessors.rs:313-318` | `+5,007,9`, ` 5 , 7 ,9 ` and `5,7,9,` each give a dump bit-identical to `5,7,9`. `5,,9` runs as N=2. `5,<NBSP>7` is accepted (Unicode trim). `5,+,9`, `5,-1`, `0x10`, `5 7` and `4294967296` exit 1 before loading, with no file. `,,` gives "--tokens is empty", exit 1. Id 20000 = V gives "token id 20000 is outside the embedding table", exit 1. Id 19999 = V−1 executes |
| 2.4 | No BOS/EOS/template inserted | **Confirmed** | `CLI/teacher_force.rs:68-70` | N rows for N ids in every run. Row i's argmax equals input id i at 200/200 positions (with tied embeddings, each position predicts its own token), so no token was inserted or shifted |
| 3 | Two files; sidecar path = `with_extension("meta.json")`; dump created after load and before steps; sidecar written last, not atomically; nothing deleted | **Confirmed** | `CLI/teacher_force.rs:53-66, 94-132` | `x.f32` gives `x.meta.json`. The 0-byte file on a failure at position 0 shows creation before the first step. Stale-file runs below show that nothing is ever deleted |
| 4 | No header; LE binary32; `[N, V]` row-major; size `4·N·V`; V from first row = head `shape[0]` | **Confirmed** | `CLI/teacher_force.rs:66-84`; `EX/prepared/accessors.rs:199-206` | `layout_check.py`: 8 × 20000 → 640,000 bytes exactly. Read as LE f32 at offset 0, every row correlates ≥ 0.99990 with an independent float64 forward. Offsets 4, 8 and 16 give \|corr\| < 0.02. The big-endian reading is garbage. Every complete run had size = 4·N·V |
| 5 | Column j = token id j, no permutation or truncation | **Confirmed** | `EX/production/plan_backend.rs:319-342`; `EX/cpu/executor.rs:254-272`; `EX/cpu/kernels.rs:93-101` | Per row, argmax(dump) = argmax(reference) at 200/200 positions. Rolling the columns by 1, or reversing them, gives \|corr\| < 0.015 |
| 6 | No identifiers anywhere; row i = position i = logits after tokens 0..i; row N−1 present | **Confirmed** | `CLI/teacher_force.rs:96-132`; `EX/kv.rs:389-404`; `EX/backend/step_calls.rs:107-125` | Stdout and sidecar contain no ids. Row i matches reference position i (corr ≥ 0.99991), while row 150 against reference row 151 gives −0.04. The prefix property holds bitwise |
| 7.1 | Sidecar text and fields; engine string identical for `production` and `production-q8`; env value unescaped | **Confirmed** | `CLI/teacher_force.rs:112-131` | The sidecar text matches the §7.1 template byte for byte, with the three timings checked by regex, 2-space indent and a trailing LF. Values: `draft_depth: null`, `executed_layers: [0, 2]`, `model_layers: 2`, `positions: N`, `vocab: 20000`, `max_format_env: "bf16"`. `--backend production` also gives `vindex3-production-larql-compute`. With `LARQL_CPU_MAX_FORMAT='bf"16'` the run exits 0 and the sidecar is **invalid JSON** |
| 7.2 | Exit statuses | **Confirmed except clap (C1)** | `MAIN:356-370, 455-459` | Success 0; returned errors 1; clap refusals 2. Signals: SIGKILL 137, SIGTERM 143, SIGINT −2 (killed by signal) |
| 7.3 | Stdout lines and order; acceptance lines only on success | **Confirmed**, with C3 | `CLI/teacher_force.rs:96-104, 132`; `CLI/exec.rs:94-102, 155-211` | The good-run stdout has exactly the §7.3 lines in order: `representation: Q8_0  source: stored  objects from a compiled pack: 1/4`, `engine:`, `positions: 8  vocab: 20000`, `teacher-forced …`, `wrote [8, 20000] f32 to …`, `wrote provenance to …`, `runtime compile: 0 tensor(s)  — served entirely from stored bytes`, `projection plans: FusedBf16 8 calls 0.08 GB, FusedKQuant 112 calls 0.01 GB`. On failures only the `representation:` line appears |
| 8.1 | Failure behaviour: before create, nothing touched; mid-run, partial rows and old sidecar survives; signal, unflushed | **Confirmed**, with C4 | as cited | **Parse failure** after a good run, no deletion: dump and sidecar hashes unchanged. **Mid-run failure** after a good run, no deletion: dump truncated to 160,000 bytes (2 complete rows), and the **old sidecar survives** with `positions: 4`. **SIGKILL/SIGTERM/SIGINT** at about 1.5 s on N=4000: sizes 63,676,416, 66,797,568 and 75,194,368, each a multiple of 8192, each ending mid-row (remainders 76,416, 77,568 and 74,368 of 80,000), no sidecar |
| 8.2-8.3 | Completeness only from exit status, stdout, sidecar and size together; harness deletes first | **Confirmed**, and implemented (below) | — | — |
| 9 | No position selection; all positions written | **Confirmed** | `CLI/args.rs:181-331`; `--help` | `--help` lists no position, stride or range flag |
| 10 | Computes at and beyond `max_position_embeddings`; no table, no clamp | **Confirmed on the fixture** (not at subject scale) | `EX/kernels.rs:147-158`; `EX/production.rs:302-311` | With `max_position_embeddings` = 128 and N = 200: exit 0, accepted, all finite. Positions 128-199 correlate ≥ 0.99994 with the independent float64 forward using unbounded RoPE. That is no worse than positions 0-127 (≥ 0.99991). No refusal, clamp or wrap. The resource figures for N = 40,960 were not tested |
| 11 | Values written bit for bit as computed | **Confirmed** (source); consistent with the fixture | `CLI/teacher_force.rs:82-84` | Not separable from computation by observation. NaN/inf preservation was not exercised, because no non-finite values occurred. C5 applies to §11.3 |
| 12 | Sidecar not byte-reproducible; dump independent of thread counts | **Confirmed** | `EX/cpu/executor.rs:56, 183-195, 245-272`; `KQ:58-109` | See Determinism below. The sidecars differ run to run only in the timing fields |

## Open items settled by the fixture

| OI | Result |
|---|---|
| OI-4 | Mid-run error: the file ends on a **row boundary** (k complete rows). Signal: the file ends at a multiple of **8192** bytes, mid-row. Both observed on toolchain 1.98.0. These remain standard-library behaviour, so a reader still rejects anything not exactly 4·N·V |
| OI-6 | Observed: `draft_depth: null`, `executed_layers: [0, L]`, `model_layers: L` for L = 2. `--draft-depth 2` (= L) records `draft_depth: 2` and `executed_layers: [0, 2]` with a dump **bit-identical** to the full run, so only the sidecar shows the flag was passed. `--draft-depth 1` records `[0, 1]`. The subject value 28 remains expected, not observed |
| OI-7 | **Closed for the format:** byte layout, shape, order and size were checked against emitted files and an independent forward |
| OI-9 | **Closed on the fixture:** bit-identical at `LARQL_CPU_WORKERS`/`RAYON_NUM_THREADS` = 1, 4 and 12. At 12 and 4 the head was split across the executor pool, because 10.24 MB ≥ the 4 MiB `MIN_SPLIT_BYTES` and 20000 rows exceed the worker count. FusedKQuant ran on rayon in every case. This shows the property for this binary and these shapes, not the subject's |
| OI-10 | **Confirmed:** every listed lenient case behaves as the spec says, and so does a non-breaking space. `5,,9` silently runs a shorter sequence. `+5,007,9` runs the same sequence, so only a canonical-string check catches it. A lone `+` is rejected |
| OI-11 | **Confirmed:** `--bank` wins, exits 0, writes nothing at the `--logit-dump` path, and prints no `positions:`/`wrote [` lines |
| OI-13 | **Confirmed:** a `"` in `LARQL_CPU_MAX_FORMAT` gives an invalid-JSON sidecar with exit 0 |
| OI-14 | **Closed:** `vindex3 exec --help` lists `--component --tokens --dump-layers --resume --backend --plugin --lowering --representation --representation-source --generate --speculate --stop-at-eos --residency-curve --repeat --warmup --unquiet-ok --expert-access --bank --dump-dir --logit-dump --draft-depth --profile`. That equals `CLI/args.rs:181-331` plus `CLI/plugins.rs:36-57`. See C2 for the generate-only flags |
| OI-16 | **Confirmed:** `--backend production` writes the same `engine` string. On this fixture its dump differs from `production-q8`'s, as expected |
| OI-5, OI-15 | Behaviour beyond the declared context was observed on the fixture (it computes, see §10). Classification remains a protocol decision |
| OI-1, -2, -3, -8, -12 | Not settled by a fixture. OI-2 and OI-3 were reproduced as described |

## D12 acceptance procedure (validated)

`accept.py` (in `~/chris-source/logit-dump-check`) does the following.

**Before the run:** it deletes the dump and sidecar and confirms both are absent. It also requires that the dump's stem contains no `.`.

**The run:** it builds the canonical `--tokens` string from the harness's own id list and runs the exact conforming argv under `env -i` with the Baseline variables only.

**It records:**
- the token-id SHA-256 (little-endian uint32, in order) and the SHA-256 of the exact `--tokens` string;
- the full argv and environment;
- the exit status, and the full stdout and stderr;
- the binary's SHA-256;
- the container identity: the SHA-256 of every file plus a manifest digest;
- the dump's and sidecar's SHA-256 and size.

**Fail-closed checks:**
- the environment is exactly the Baseline set;
- the argument list has no flag beyond the conforming set;
- `--tokens` is the canonical string of the recorded ids;
- exit status is 0;
- stdout contains the `engine:` line, `positions: N  vocab: V`, `wrote [N, V] f32 to OUT` and `wrote provenance to SIDECAR`;
- the `representation: Q8_0  source: stored` line is present, with `runtime compile: 0`;
- the `projection plans:` line is present and lists only `FusedKQuant` and `FusedBf16`;
- the sidecar parses as JSON, has the expected key set, the values `engine`, `draft_depth = null`, `executed_layers = [0, L]`, `model_layers = L`, `positions = N`, `vocab = V`, `max_format_env = "bf16"`, and was modified after the run started;
- the dump was modified after the run started, and its size is exactly 4·N·V.

**Accepted (ACCEPT):**
- `good1` (N=8);
- `long200a` and `long200b` (N=200, beyond the fixture's max positions);
- `prefix8`.

**Rejected (REJECT), each with the failing checks recorded in `records/`:**

| Case | Failing checks (main ones) |
|---|---|
| Out-of-range id at position 3 | exit 1; stdout lines; sidecar; size (3 of 5 rows) |
| `5,,9` for intended `5,0,9` | non-canonical `--tokens`; `positions` 2 ≠ 3; sidecar `positions`; size |
| `+5,007,9` and `5,7,9,` (runs as the right sequence) | non-canonical `--tokens` only |
| Stale, mid-run failure, deletion skipped | pre-run absence; exit 1; stdout; sidecar not from this run; size |
| Stale, parse failure, deletion skipped (old dump and sidecar fully intact) | pre-run absence; non-canonical tokens; exit 1; stdout; **sidecar and dump not from this run** (mtime) |
| Stale, parse failure, with deletion | exit 1; no files at all |
| `--bank` override | forbidden flag; no `positions:`/`wrote` lines; no dump; no sidecar |
| `--draft-depth 1` | forbidden flag; sidecar `draft_depth`, `executed_layers` |
| `--speculate 2` (C2: exit 0, identical dump) | flag beyond the conforming set only |
| `LARQL_CPU_MAX_FORMAT` empty | environment; sidecar `max_format_env` |
| `LARQL_CPU_MAX_FORMAT='bf"16'` | environment; sidecar not valid JSON |
| A second `--backend` | clap exit 2 and everything downstream |
| Worker counts 1 and 4 | environment only (the dumps are bit-identical to the accepted one) |
| First fixture, V = 10000 (head ran `BlasF32`, C5) | `projection plans:` check only (`records-v1-V10000/good1.json`) |

**Lesson for the harness.** In the stale cases with deletion skipped, only exit status, stdout and modification time distinguish an intact old dump and sidecar from a new success. Pre-run deletion is the primary guard and must be kept. The modification-time check must have no slack: a 1-second tolerance in my first draft let a sidecar written 0.5 s earlier pass that one check (the run was still rejected on exit status and stdout). Also, a SIGINT sent to a background job of a non-interactive shell is ignored by POSIX job-control rules. The harness should signal the process directly, as `subprocess.send_signal` does.

## Determinism

| Run | Environment | Dump SHA-256 |
|---|---|---|
| `long200a` | Baseline (12/12) | `3d62cefda47e2d47c1c6b11ae2947838db5f60d8e2e87bd479f9604f750c7927` |
| `long200b` | Baseline (12/12) | identical |
| `long200w4` | `LARQL_CPU_WORKERS=4`, `RAYON_NUM_THREADS=4` | identical |
| `long200w1` | `LARQL_CPU_WORKERS=1`, `RAYON_NUM_THREADS=1` | identical |

All four dumps (N=200, 16,000,000 bytes) are bit-identical. All four ran `FusedBf16 200 calls 2.05 GB, FusedKQuant 2800 calls 0.25 GB`. The sidecars differ only in `prepare_s`, `steps_s` and `ms_per_position`, as §12.1 says.

## Limits of this check

- The fixture is not the subject. The subject-specific values (V = 151936, 28 layers, head `FusedBf16` on this host, and the KV and dump sizes at N = 40,960) are confirmed only as consequences of the confirmed code paths, not by observation.
- I built the binary myself from the pinned commit. The subject run's binary must be identified by its own hash.
- The independent float64 forward (`ref_forward.py`) was written from the Qwen3 architecture for this check, only to fix the axes. It is not a numerical reference, and the agreement (correlation about 0.9999, max abs about 0.4 against the Q8_0 decoder) is not a tolerance claim.

## Confirmation of revision 2

| Field | Value |
|---|---|
| Date | 2026-11-01 |
| Revision checked | `specs/larql-logit-dump/SPEC.md` revision 2, commit `bd603c1`, SHA-256 `eb6407d8bc54309311e0a4c7b1f20e6fc70d94ce708c175ba125d0931f1e339f`. I compared it with revision 1 (`0e6de8f`) using `git diff 0e6de8f bd603c1`. I did not edit it |
| Re-runs | `~/chris-source/logit-dump-check`, commit `8ac4338`, with the same binary, fixture and rules as before. `failure_modes.sh` §8 is new. The LARQL worktree is still clean |

### Verdict

**REMAINING DEFECTS (D1–D4); the rest is confirmed.** C1, C3 and C4 are applied correctly and completely. No statement about the byte format changed: §3, §4, §5 and §7.1 are textually unchanged, and §6 only gains a fixture note. C2 and C5 each contain one wrong statement, and §8.3 does not yet require two checks that its own fixture note claims. One attribution is overstated (M1).

### 1. C1–C5

| | Result |
|---|---|
| C1 (§7.2) | **Confirmed.** Status 2 for clap rejections and for the trampoline refusal; a reader requires 0 and gives no meaning to particular non-zero values. The citations `MAIN:371-376`, `MAIN:378` and `trampoline.rs:54-56` are correct. The constant `= 2` is at line 56 |
| C2 (§2.2) | **Defect D1.** The new row states that `--repeat`, `--warmup`, `--unquiet-ok` and `--expert-access` are, "by the same mechanism", not rejected when `--logit-dump` is present. **Observed (re-run, `failure_modes.sh` §8):** each of the four, passed alone with `--logit-dump`, is **rejected with exit 2** ("the following required arguments were not provided: --generate, --residency-curve"). They are accepted (exit 0, dump bit-identical) only together with `--residency-curve`. The mechanism: clap skips the `requires` check of an argument whose required argument conflicts with `--logit-dump` (`--residency-curve`, `--speculate`, `--stop-at-eos` and `--profile` all require `--generate`). It still enforces `requires = "residency_curve"`, because `--residency-curve` conflicts with nothing. *Fix:* "the four `residency_curve`-dependent flags are rejected (exit 2) unless `--residency-curve` is also passed, in which case they are accepted and ignored (third-party fixture)". The new §2.2.0 exact-argv rule is correct, sufficient and unaffected. The claim that `run_teacher_force` returns before any code reading these flags is correct: they are read only at `CLI/exec.rs:250-261` and in `lowered/run.rs:105-116` |
| C3 (§7.3) | **Confirmed.** The print conditions, the citations (`CLI/exec.rs:94-102, 155-180, 195-210`) and the `production`/`production-q8` distinction match the source and my runs. The new §7.3.4 (a missing `projection plans:` line fails the check) is right |
| C4 (§8.1) | **Confirmed.** All four observed bullets and the signal note in §8.1.5 match my records. They are correctly tagged **[I]** |
| C5 (§11.4) | **Defect D2.** "a fixture used to test the acceptance procedure needs a head whose **BF16** image is at least the host's L2" is wrong. What the procedure's positive path needs is an **f32 image** of at least L2: that is the condition at `projection.rs:207-209`, which selects `FusedBf16` over `BlasF32`. My accepted fixture shows this: V = 20000, H = 256, a BF16 head of 10.24 MB, **below** the 16 MiB L2, ran `FusedBf16` and was accepted. A BF16 image of at least L2 is needed only to make the bf16 cap visible in `projection plans:` (`FusedQ8` without the cap, `:218`). *Fix:* "needs a head whose f32 image is at least the host's L2 (so it runs `FusedBf16`, not `BlasF32`). A BF16 image of at least L2 is additionally needed if the fixture must show the cap's effect. On the third party's fixture (BF16 head below L2), removing the cap changed no value." The rest of §11.4 is correct (155,582,464 elements; about 622 MB as f32 and about 311 MB as BF16) |

### 2. Attributions labelled "(third-party fixture)"

I checked every one against `records/` and `records/failure_modes.log`. These are correct:
- §2.3.3, §6.3, §7.2.1, §7.2.3, §7.3.1, §7.3.3, §8.1.2 (four bullets), §8.1.5, §10.2.6, §11.4 (the observed `BlasF32` rejection), §12.3;
- OI-4, -5, -6, -7, -9, -10, -11, -13, -14, -16.

Exceptions:
- the C2 row's claim about the four untested flags (D1). It is not attributed to me, but it is now refuted;
- **M1 (minor), the §8.3 [I] note.** It says "In the stale cases only exit status, stdout and a no-slack modification-time check distinguished old files from a new success". That holds only for the stale case where deletion was skipped and the old dump and sidecar were **intact** (a parse failure after a good run). In the mid-run stale case, size and `positions` also failed. *Fix:* "In the stale case with deletion skipped and the old files intact, …".

### 3. Byte format

**Confirmed unchanged:**
- no header, little-endian binary32, [N, V] row-major, size 4·N·V, V from the first row;
- the vocabulary order;
- row i = position i;
- the sidecar template and keys;
- the file paths and the order in which they are written.

### 4. §8.3 reader procedure against what `accept.py` enforced

| Condition | `accept.py` | Rev 2 §8.3 | Assessment |
|---|---|---|---|
| Delete dump and sidecar before the run, and confirm absent | yes | §8.3.1 MUST (unchanged) | Matches |
| Exact conforming argv | yes ("no flags beyond the conforming set") | §2.2.0, §8.3.3.6 | Matches, and sufficient |
| `representation: Q8_0  source: stored` | yes (prefix match, exactly one such line) | §8.3.3.5 | Matches |
| `runtime compile: 0 tensor(s)` | yes | §8.3.3.5 | Matches |
| `projection plans:` present, only `FusedKQuant`/`FusedBf16` | yes | §8.3.3.5, §7.3.4 | Matches |
| exit 0; `positions:` and `wrote [` lines; sidecar fields; size 4·N·V | yes | §8.3.3.1-4 | Matches |
| **Canonical `--tokens`** (the string equals the canonical form of the recorded ids) | yes | §2.3.4 is only **SHOULD**; not in §8.3 | **Defect D3.** None of §8.3.3.1-6 rejects `+5,007,9` or `5,7,9,`: exit 0, `positions == 3`, size correct. Yet the §8.3 note says a procedure "implementing these checks" rejected non-canonical `--tokens`. It was my extra check that did. D12 requires the recorded token sequence and the command arguments to be consistent. *Fix:* make §2.3.4 a MUST, and add to §8.3.3 "the recorded `--tokens` string is exactly the canonical form of the recorded id list". Otherwise drop that case from the note |
| **Modification time with zero tolerance** (dump and sidecar `mtime` ≥ run start) | yes (slack removed after my first draft) | mentioned only in the [I] note; not a condition | **Defect D4 (minor).** With §8.3.1 (delete and confirm absent) the check is redundant, so the procedure is sufficient without it. It was, however, the only extra signal in the intact-stale case. *Fix:* add as §8.3.3.7 (SHOULD) "the dump and sidecar modification times are not earlier than the run's start, with no tolerance", or state in the note that §8.3.1 makes it redundant |
| Environment exactly the Baseline set | yes | not in §8.3 (required by PROTOCOL "Baseline"; only `max_format_env` is checked via the sidecar) | Advisory: add a cross-reference in §8.3.2 ("record the full environment; a run outside the Baseline set is rejected") |
| `engine:` stdout line, sidecar `engine`, sidecar key set, `wrote provenance to` line | yes | no | Advisory only. Redundant given the exact argv and the other checks |

**Sufficiency:** with D3 applied, conditions §8.3.1 and §8.3.3.1-6 reject every failure mode in my check, and the reject set does not depend on the advisory checks. Each failure mode is caught by at least one listed condition:
- an out-of-range id: exit status and size;
- `5,,9`: `positions` and size;
- `+5,007,9` and `5,7,9,`: D3;
- stale files: §8.3.1, then exit status;
- `--bank`, `--draft-depth`, `--speculate`, `--residency-curve …`: exact argv;
- a missing or malformed cap: the sidecar's `max_format_env`, or invalid JSON;
- a repeated flag: exit status;
- the `BlasF32` head: `projection plans:`.

### Remaining defects to fix before admission

1. **D1 (§2.2 C2 row):** the four `residency_curve`-dependent flags are rejected (exit 2) unless `--residency-curve` is also passed.
2. **D2 (§11.4 C5):** the fixture needs an f32 head image of at least L2, not a BF16 image.
3. **D3 (§2.3.4, §8.3):** require the canonical `--tokens` string, or drop the claim from the §8.3 note.
4. **D4 (§8.3, minor):** make the zero-tolerance modification-time check a SHOULD condition, or state that it is redundant given §8.3.1.

Also: M1 (wording in the stale-case note), and the advisory environment cross-reference.
