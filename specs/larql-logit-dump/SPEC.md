# LARQL Logit Dump: Byte-Level Specification (`vindex3 exec --logit-dump`, Qwen3-0.6B Q8_0 profile)

| Field | Value |
|---|---|
| Document | LARQL-VERIFY-001, decision AMB-014, logit-dump output contract |
| Status | **DRAFT, not admitted; requires third-party confirmation of corrections.** Revision 1 was checked by a third party (verdict ACCURATE WITH CORRECTIONS, `specs/larql-logit-dump/THIRD-PARTY-CHECK.md`, commit `4bce40d`). Revision 2 applied its corrections C1–C5; the third party confirmed C1, C3 and C4 and found defects D1–D4 and M1 ("Confirmation of revision 2", commit `bc063f2`). This revision fixes those; a third party must confirm them before admission |
| Revision | 3 (see Revision history and §14). Revision 2 was commit `bd603c1`, SHA-256 `eb6407d8bc54309311e0a4c7b1f20e6fc70d94ce708c175ba125d0931f1e339f`. Revision 1 was commit `0e6de8f`, SHA-256 `48fe2666b5f0d11f7e274641a46eba80859838db3dbf88c484cc7a1b6afe1150` |
| Describes | The files written by `larql vindex3 exec ... --logit-dump <OUT>` at LARQL commit `2536bb79b199b1115445678e3e82c400b0b3fd07` (clean worktree `/Users/christopherhay/chris-source/larql-l1-2536bb79`) |
| Profile | `--backend production-q8 --representation-source stored`, CPU, on the Q8_0 container of Qwen/Qwen3-0.6B (HF `c1899de289a04d12100db370d81485cdf75e47ca`) described by `specs/vindex3-container/SPEC.md` (B3), under the environment pinned in `protocols/LARQL-VERIFY-001/PROTOCOL.md` "Baseline" |
| Method | The author read source only and did not build or run LARQL. Revision 2 additionally cites the third-party check's observations on a non-subject Qwen3-architecture fixture (2 layers, V = 20000), built from the pinned commit by the third party. Those observations are labelled **(third-party fixture)** and are the third party's evidence, not the author's. No subject logits were produced by anyone |
| Author | A specification-author subagent with read access to LARQL source. Not the reference checker. It did not read `checker/`, the hidden-corpus repository, `evidence/freeze-review/` or the refaudit repository |

## 0. Conventions

- The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be read as in RFC 2119.
- Every statement is tagged **[N]** (normative: a property of the format or of the writer's behaviour that a reader may rely on once this document is admitted) or **[I]** (informative: context, consequences, estimates, or advice that is not a property of the writer).
- Statements addressed to the **harness** (the operator process that invokes LARQL and hands files to the checker) are tagged **[N-H]**. They are normative for a conforming run, not properties of LARQL.
- "Writer" means LARQL at the commit above. "Reader" means an independent program that consumes the dump without reading LARQL code. `N` is the number of token ids supplied. `V` is the vocabulary width of a row.
- Citations are `path:line` at the pinned commit. Abbreviations:
  - `CLI/` = `crates/larql-cli/src/commands/primary/vindex3_cmd/`
  - `EX/` = `crates/larql-vindex/src/format/vindex3/opplan/exec/`
  - `MAIN` = `crates/larql-cli/src/main.rs`
  - `CONT` = `crates/larql-cli/src/commands/primary/continuation.rs`
  - `KQ` = `crates/larql-compute/src/cpu/kquant_gemv.rs`
  - `POS` = `crates/larql-models/src/config/position.rs`
- Where a value depends on the container (for example `V = 151936`), the value is taken from B3 revision 4 (`specs/vindex3-container/SPEC.md` §17.6, §17.7), which records it as **(observed)** in the pinned container. Those are marked **(from B3)**.
- **(third-party fixture)** marks a statement observed by the third party on its non-subject fixture, as recorded in third-party fixture evidence, `specs/larql-logit-dump/THIRD-PARTY-CHECK.md` at `4bce40d`. Such observations show the behaviour of the pinned code on that fixture and host; subject-specific values remain derived.
- Open items are numbered `OI-n` and collected in §13. Where the source leaves behaviour undefined or ambiguous, this document says so and does not resolve it.

## 1. What the writer is

1. **[N]** `--logit-dump <OUT>` selects one code path, `run_teacher_force` (`CLI/exec.rs:242-246`, `CLI/teacher_force.rs:39-134`). It is reached from `run_exec` → `with_plan_backend` → `run_on` for every non-lowered backend, including `production-q8` (`CLI/exec.rs:80-131, 214-246`).
2. **[N]** The path creates a fresh decode session over operands prepared once (`CLI/teacher_force.rs:53-55`) and a fresh continuation (KV) state from the CLI's default selection (`CLI/teacher_force.rs:54`; `CONT:35, 125-134`), then calls `session.step(token)` once for each supplied token, in order, starting at position 0 (`CLI/teacher_force.rs:68-72`; `EX/decode/steps.rs:140-142`).
3. **[N]** Each step computes exactly one position through the whole stack against the cached K/V of earlier positions and returns that position's logits (`EX/decode.rs:1-12`; `EX/decode/run.rs:43, 654-677`).
4. **[I]** This is a teacher-forced, one-token-at-a-time, KV-cached schedule. There is no prefill and no batched forward on this path (`CLI/teacher_force.rs:11-20, 68-93`). The batched traversal (`execute_plan_streaming`) is used only by the summary and `--dump-layers` paths (`CLI/exec.rs:247-275`), not by `--logit-dump`.

## 2. Command surface

### 2.1 The conforming invocation

**[N-H]** The conforming invocation for this profile is the one in `evidence/L1/AUDIT.md` "Exact commands", step 3:

```sh
env -i PATH=/usr/bin:/bin HOME="$HOME" \
  LARQL_CPU_MAX_FORMAT=bf16 LARQL_CPU_WORKERS=12 RAYON_NUM_THREADS=12 \
  "$B" vindex3 exec "$CONTAINER" \
    --backend production-q8 --representation-source stored \
    --tokens <id0,id1,...,idN-1> --logit-dump "$OUT"
```

### 2.2 Flags that affect the dump

| Flag | Effect on the dump | Conforming use | Source |
|---|---|---|---|
| `<CONTAINER>` (positional) | The container executed | The pinned Q8_0 container | `CLI/args.rs:183-184` |
| `--logit-dump <PATH>` | Selects this path; `<PATH>` is the dump file. Its sidecar path is derived from it (§3) | REQUIRED | `CLI/args.rs:300-309`; `CLI/exec.rs:242-246` |
| `--tokens <LIST>` | The token ids, in order (§2.3). The only token input of this path | REQUIRED | `CLI/args.rs:190-193`; `CLI/exec.rs:81, 505-518` |
| `--backend` | Numerical realisation. Default `reference` | `production-q8` | `CLI/args.rs:208-210` |
| `--representation-source` | `auto`, `stored` or `transient`. Default `auto` | `stored` | `CLI/args.rs:215-228` |
| `--component` | Component executed. Default `target` | omit (default) | `CLI/args.rs:186-188` |
| `--draft-depth <N>` | Executes only the first N layers, then the final norm and head. Changes every logit. Recorded in the sidecar | MUST NOT be passed | `CLI/args.rs:311-322`; `CLI/exec.rs:238-241`; `CLI/teacher_force.rs:119-122` |
| `--bank <JSONL>`, `--dump-dir <DIR>` | If `--bank` is given, the bank path runs **instead of** `--logit-dump`, which is then silently ignored. `--logit-dump` does not conflict with `--bank` at the argument parser | MUST NOT be passed | `CLI/exec.rs:222-234` (checked before line 242); `CLI/args.rs:293-298, 308` |
| `--dump-layers`, `--resume`, `--generate` | Rejected by the argument parser together with `--logit-dump` | MUST NOT be passed | `CLI/args.rs:308` |
| `--plugin`, `--lowering`, `--representation` | Change what is bound and which provider runs | MUST NOT be passed | `CLI/plugins.rs:36-57`; `evidence/L1/AUDIT.md` "Exact commands" |
| `--speculate`, `--stop-at-eos`, `--residency-curve`, `--profile` | Declared `requires = "generate"`. Because `--generate` conflicts with `--logit-dump`, the argument parser does **not** enforce that requirement when `--logit-dump` is present. These four are accepted without error and ignored on this path: `run_teacher_force` returns before any code that reads them (they are read only at `CLI/exec.rs:250-261` and in `CLI/lowered/run.rs:105-116`). **(third-party fixture)** `--speculate 2 --profile --stop-at-eos --residency-curve` with `--logit-dump` exits 0 with a dump bit-identical to the run without them | MUST NOT be passed | `CLI/args.rs:245, 251, 259, 329`; `CLI/args.rs:308`; `CLI/exec.rs:242-246` |
| `--repeat`, `--warmup`, `--unquiet-ok`, `--expert-access` | Declared `requires = "residency_curve"`. `--residency-curve` conflicts with nothing, so this requirement **is** enforced: passed with `--logit-dump` alone, each is **rejected with exit 2** (§7.2). Only if `--residency-curve` is also passed are they accepted and ignored, as in the row above. **(third-party fixture)** both behaviours observed | MUST NOT be passed | `CLI/args.rs:266-283` |

0. **[N-H]** The harness MUST pass **exactly** the conforming argument list of §2.1 (container, `--backend production-q8`, `--representation-source stored`, `--tokens`, `--logit-dump`) and nothing else, each flag once. Checking only for the absence of named forbidden flags is not sufficient, because some flags are accepted and silently ignored (row above) and a repeated flag is a parser error (§7.2).
1. **[N]** There is **no** flag for position selection, stride, a position range, a row subset or a vocabulary subset on this path. The complete set of `exec` flags is `CLI/args.rs:181-331`; none of them selects positions, and `run_teacher_force` takes no such parameter (`CLI/teacher_force.rs:39-47`). See §9.
2. **[N]** There is no flag selecting the continuation (KV) provider on this path. The provider is always the CLI's declared default, alias `row`, identity `row/v1` (`CLI/teacher_force.rs:54` passes `None`; `CONT:29-35, 47-56, 125-134`).
3. **[N]** There is no text-prompt input on this path. `exec` never tokenises (`CLI/exec.rs:10-15`; `CLI/args.rs:190-191`).

### 2.3 Token input

1. **[N]** `--tokens` is a single string. The writer splits it on `,`, trims ASCII/Unicode whitespace from each item, **drops empty items**, and parses each remaining item with Rust's `u32` parser (`CLI/exec.rs:506-512`).
2. **[N]** A parse failure, or an empty result, aborts the run before any weight is loaded and before any file is written (`CLI/exec.rs:81, 513-516`).
3. **[I]** Consequences of the parser: `"1,,2"` and `"1,2,"` both mean `[1, 2]`; an optional leading `+` and leading zeros are accepted (Rust `u32::from_str`); values above 4294967295, negative values, hexadecimal and internal spaces are rejected. See OI-10. **(third-party fixture)** all of these cases behaved as stated, and a non-breaking space is trimmed.
4. **[N-H]** The harness MUST pass the ids in **canonical form**: the recorded ids, in order, each rendered as unsigned decimal with no sign and no leading zeros (`0` itself is `0`), joined by single commas, with no whitespace, no empty items and no trailing comma. The harness MUST record the exact `--tokens` string it passed (§6), and MUST compare it byte for byte against the canonical rendering of its token manifest; any difference rejects the run (§8.3.3).
5. **[I]** Canonical form is needed because the writer's leniency (§2.3.3) lets a non-canonical string run without error, either as the intended sequence (`+5,007,9`, `5,7,9,`) or as a shorter one (`5,,9`). The other §8.3 checks catch only the second case.
6. **[N]** An id `t` is accepted by the parser even if `t >= V`. It is refused when its step runs: the embedding lookup returns an error if `t >= rows(embedding table)` (`EX/prepared/accessors.rs:313-318`). The run then fails (§8). **(from B3)** The embedding table of this container has 151936 rows, so ids `0 ..= 151935` are executable, including ids the tokenizer never emits.

### 2.4 BOS and chat template

1. **[N]** The writer inserts **no** BOS, EOS or other token. The sequence executed is exactly the parsed `--tokens` list, in order: `run_teacher_force` iterates over the parsed slice and nothing else (`CLI/exec.rs:81, 242-245`; `CLI/teacher_force.rs:68-70`; `EX/decode/steps.rs:140-142`; `EX/decode/run.rs:74-75` embeds the given id).
2. **[N]** The writer applies **no** chat template, because it never handles text (`CLI/exec.rs:10-15`).
3. **[N-H]** Nothing needs to be disabled. To run with a BOS id, or with a templated prompt, the harness puts those ids in `--tokens` itself, following the corpus's preregistered BOS and template policy.
4. **[I]** `larql run <container> [prompt]` with `--emit-ids` is a different command that tokenises text (`CLI/exec.rs:13-15`). It is not part of this profile and is not specified here.

## 3. Files written

1. **[N]** On success the writer produces exactly two files:
   - the **dump file** at the path given to `--logit-dump`, exactly as given (`CLI/teacher_force.rs:66`);
   - the **sidecar** at `Path::with_extension(<OUT>, "meta.json")` (`CLI/teacher_force.rs:130-131`).
2. **[N]** `with_extension` replaces the final extension of the file name, or appends one if there is none. Examples: `logits.f32` → `logits.meta.json`; `logits` → `logits.meta.json`; `a.b.f32` → `a.b.meta.json`.
3. **[N-H]** The harness SHOULD name the dump `<stem>.f32` with a stem that contains no `.`, so that the sidecar is `<stem>.meta.json` in the same directory.
4. **[N]** The dump file is created (or truncated, if it exists) with `File::create` **after** the weights are loaded and the session is built, and **before** the first step (`CLI/teacher_force.rs:53-55, 66`). The directory must already exist; the writer does not create it.
5. **[N]** The sidecar is written only after the dump file is complete and flushed, and after the stdout summary lines (`CLI/teacher_force.rs:94-104, 111-132`). It is written with `std::fs::write` (create or truncate, then write; not atomic).
6. **[N]** The writer never deletes either file. A sidecar left by an earlier run is not removed when a new run starts or fails (no removal exists in `CLI/teacher_force.rs` or `CLI/exec.rs:80-276`).

## 4. Dump file byte layout

1. **[N]** The dump file has **no header, no magic number, no version field, no footer, no padding and no checksum**. It is a bare array of IEEE 754 binary32 values (`CLI/teacher_force.rs:66, 82-84, 94`).
2. **[N]** Each value is written as `f32::to_le_bytes`, i.e. 4 bytes, **little-endian**, IEEE 754 binary32 bit pattern, unchanged (`CLI/teacher_force.rs:83`). NaN payloads, signed zeros, infinities and subnormals are preserved bit for bit; the writer does no check for non-finite values (none exists in `CLI/teacher_force.rs:68-93`).
3. **[N]** The logical shape is `[N, V]`, **row-major**: row `i` (0-based) is the `V` values of the logits returned by step `i`, in vocabulary order (§5), written contiguously; rows are written in step order (`CLI/teacher_force.rs:68-84`).
4. **[N]** Therefore value `(i, j)` is at byte offset `4·(i·V + j)`, for `0 ≤ i < N`, `0 ≤ j < V`, and a complete file is exactly `4·N·V` bytes.
5. **[N]** `V` is the same for every row of one file. The writer takes `V` from the first row and aborts the run if any later row has a different length (`CLI/teacher_force.rs:73-81`). `V` is the output-head tensor's `shape[0]` (`EX/prepared/accessors.rs:199-206`). **(from B3)** For this container `V = 151936`, so one row is 607,744 bytes.
6. **[N]** The shape is **not recorded in the dump file**. It is recorded in the sidecar (`positions`, `vocab`, §7) and printed on stdout (§7.3).

## 5. Vocabulary axis

1. **[N]** Column `j` of every row is the logit of token id `j`, for `j = 0 .. V−1`, in increasing token-id order with no gaps, no permutation and no truncation.
2. Basis for 1:
   - **[N]** The logits vector is `project_matrix(head, x, V, hidden)`, one output per row of the output-head matrix, followed by the optional per-element multiplier and softcap applied in place (`EX/production/plan_backend.rs:319-342`).
   - **[N]** The projection fills output element `o` from weight row `o`: in the serial case `out[o] = dot(row o, x)` (`EX/cpu/kernels.rs:93-101`); in the parallel case the output is cut into contiguous chunks, and chunk `i` covers rows starting at `i·rows`, so element order equals row order (`EX/cpu/executor.rs:254, 266-272`).
   - **[I]** Row `o` of the output-head tensor is token id `o`'s row, as in the upstream `lm_head.weight [151936, 1024]`. That the container stores the head with that row order is a container fact (B3 §8.2, §9.3, §12), not a property of the dump writer.
3. **[N]** `V` is the width of the model's head, not the tokenizer's vocabulary. Columns for ids the tokenizer never emits are present and are ordinary computed logits.

## 6. Token and position identifiers

1. **[N]** The dump file records **no** token ids, positions, row indices or any other identifier (§4.1).
2. **[N]** The sidecar records **no** token ids (`CLI/teacher_force.rs:112-129`). The stdout of the run prints no token ids either (`CLI/teacher_force.rs:96-104, 132`; `CLI/exec.rs:94-101, 155-211`).
3. **[N]** Row `i` is position `i`. Position `i` is the 0-based index of the token in the parsed `--tokens` list:
   - the session's position is the continuation state's counter, which starts at 0 for a fresh state (`EX/kv.rs:389-404`, `#[derive(Default)]`), is read at the start of each step (`EX/decode/run.rs:43`) and is set to `position + 1` at its end (`EX/decode/run.rs:674`);
   - each step consumes the next token (`CLI/teacher_force.rs:68-70`);
   - a step is refused unless the cached K/V ends exactly at its position (`EX/backend/step_calls.rs:107-125`), so no position is skipped or repeated.
   - **(third-party fixture)** the dump of the first 8 ids was bit-identical to the first 8 rows of a 200-id dump, and row `i` matched an independent forward at position `i` (not `i+1`).
4. **[N]** Row `i` holds the logits computed after consuming tokens `0 ..= i`, i.e. the distribution that predicts token `i+1` (`CLI/teacher_force.rs:19-20`). Row `N−1` is present: it predicts the token after the last supplied token and has no target in the sequence (`CLI/teacher_force.rs:32-38`). There are no prefill rows and no row before position 0.
5. **[N-H]** A reader establishes identifiers only externally. The harness MUST hand the checker, with each dump, the exact `--tokens` list (or the corpus record it was generated from and the means to regenerate it byte for byte), and the reader MUST take `N` from that list and check it against the sidecar and the file size (§8.3).

## 7. Sidecar and stdout

### 7.1 Sidecar content

**[N]** The sidecar is produced by a `format!` template, not by a JSON serialiser (`CLI/teacher_force.rs:112-129`). Its exact text is:

```text
{
  "engine": "<engine>",
  "draft_depth": <D>,
  "executed_layers": [<a>, <b>],
  "model_layers": <L>,
  "positions": <N>,
  "vocab": <V>,
  "prepare_s": <f.3>,
  "steps_s": <f.3>,
  "ms_per_position": <f.1>,
  "max_format_env": "<env>"
}
```

followed by one newline (0x0A), with 2-space indentation.

| Key | Value | Expected in this profile | Source |
|---|---|---|---|
| `engine` | `"vindex3-" + backend.name()` | `"vindex3-production-larql-compute"`. **The same string is written for `--backend production` and `--backend production-q8`**, so it does not identify the arm | `CLI/exec.rs:221`; `CLI/prepare.rs:37`; `EX/production.rs:50`; `EX/production/plan_backend.rs:48-56` |
| `draft_depth` | integer `N` under `--draft-depth N`, else the literal `null` | `null` | `CLI/teacher_force.rs:119-122` |
| `executed_layers` | `[start, end]` of the prepared image's half-open layer range `start..end` | `[0, 28]` (expected, not observed; OI-6) | `CLI/teacher_force.rs:57, 123-124`; `EX/prepared/accessors.rs:463-465` |
| `model_layers` | number of layers in the plan | `28` (expected) | `CLI/teacher_force.rs:125` |
| `positions` | `N`, the number of supplied tokens | `N` | `CLI/teacher_force.rs:126` |
| `vocab` | `V`, from the first row | `151936` **(from B3)** | `CLI/teacher_force.rs:67, 73-74, 115` |
| `prepare_s`, `steps_s`, `ms_per_position` | wall-clock timings, fixed-point decimals with 3, 3 and 1 fractional digits | informative only; vary run to run | `CLI/teacher_force.rs:56, 111, 116-117, 127` |
| `max_format_env` | the value of `LARQL_CPU_MAX_FORMAT`, or `""` if unset, **inserted without JSON escaping** | `"bf16"` | `CLI/teacher_force.rs:118, 128` |

1. **[N]** A reader MUST parse the sidecar as JSON and MUST NOT depend on whitespace or key order. **[I]** If `LARQL_CPU_MAX_FORMAT` contained `"` or `\`, the sidecar would not be valid JSON (OI-13); the pinned environment avoids this.
2. **[N]** The sidecar records no token ids, no digest of the dump, no container path or digest, no backend arm, no `--representation-source`, and no environment other than `LARQL_CPU_MAX_FORMAT` (`CLI/teacher_force.rs:112-129`).

### 7.2 Exit status

1. **[N]** Exit status 0 means the command returned success (`MAIN:455-459`). Errors returned by the command print `Error: <message>` on stderr and exit with status 1 (`MAIN:455-459`). Argument-parser (clap) rejections, such as conflicting or repeated flags, are reported by `Cli::parse_from` (`MAIN:378`), which exits the process itself with status **2** before any weight is loaded or any file is touched. The research-trampoline refusal also exits 2 (`MAIN:371-376`; `crates/larql-cli/src/trampoline.rs:54-56`). **(third-party fixture)** `--logit-dump` with `--generate`, and a repeated `--backend`, each exit 2.
2. **[N]** A reader MUST require exit status 0 and MUST NOT give any meaning to a particular non-zero value.
3. **[I]** A panic on the main worker thread propagates to `main`'s `expect` (`MAIN:356-362`); with Rust's default unwinding this ends the process with a non-zero status (101 by Rust convention). A signal (SIGINT, SIGTERM, SIGKILL) ends it with the signal's status. No signal handler is installed on this path (none found in `crates/larql-cli`). **(third-party fixture)** SIGKILL gave 137, SIGTERM 143, and SIGINT a killed-by-signal status.

### 7.3 Stdout lines

**[N]** On success, after the dump is flushed, the writer prints, in this order (`CLI/teacher_force.rs:96-104, 132`; `CLI/exec.rs:130, 155-181, 195-211`):

```text
engine: vindex3-production-larql-compute
positions: <N>  vocab: <V>
teacher-forced <N> positions in <s> s (<ms> ms/position)
wrote [<N>, <V>] f32 to <OUT>
wrote provenance to <OUT with extension meta.json>
runtime compile: <n> tensor(s)[  — served entirely from stored bytes]
[stored precision: ...]
projection plans: <plan> <calls> calls <GB> GB, ...
```

1. **[N]** The `representation: <want>  source: ...` line is printed before execution, and only when the backend requests a stored representation (`want` is `Some`) (`CLI/exec.rs:94-102`). It is therefore printed **also on runs that later fail**, and its presence is not evidence of success. **(third-party fixture)** it appeared on every mid-run and post-load failure.
2. **[N]** `runtime compile:` is printed only if (a) the whole run succeeded, including the sidecar write, **and** (b) the backend requests a stored representation (`want` is `Some`) (`CLI/exec.rs:130, 155-169`). `stored precision:` additionally requires at least one tensor bound at stored precision (`CLI/exec.rs:170-179`). `projection plans:` requires (a) and (b) and at least one projection plan with a non-zero call count in the executor's ledger (`CLI/exec.rs:180, 195-210`).
3. **[N]** Under `--backend production-q8`, `want` is `Q8_0` (`CLI/prepare.rs:88-102`; `evidence/L1/AUDIT.md` item 1), so on a successful run `runtime compile:` and `projection plans:` are printed. Under `--backend production`, `want` is `None` and **none** of `representation:`, `runtime compile:`, `stored precision:` or `projection plans:` is printed, even on success. **(third-party fixture)** observed for both backends.
4. **[N]** The run-acceptance check of PROTOCOL "Baseline" (only `FusedKQuant` and `FusedBf16` in `projection plans:`) can therefore be applied only to a successful `production-q8` run, and a reader MUST treat a missing `projection plans:` line as a failed check.
5. **[I]** Progress lines `  position <k>/<N>  (<s> s)` go to stderr every 32 positions and at the last one; `k` is a 1-based count (`CLI/teacher_force.rs:85-92`).

## 8. Completeness and failure

### 8.1 What exists after a failure

1. **[N]** **Failure before the dump file is created** (argument parsing, token parsing, container preparation, weight loading, session construction: `CLI/exec.rs:81-92`; `CLI/teacher_force.rs:53-55`): the writer creates, truncates and writes nothing. **Any dump file and sidecar already at those paths from an earlier run are left unchanged.**
2. **[N]** **Failure during the steps** (for example an out-of-range token id, `EX/prepared/accessors.rs:313-318`, or a vocabulary change, `CLI/teacher_force.rs:75-81`): the function returns early through `?`. The dump file then holds the rows completed so far: rows already pushed to the OS, plus the rows still in the write buffer, which the buffered writer's destructor attempts to flush on drop (`CLI/teacher_force.rs:66` uses `std::io::BufWriter`). No sidecar is written for this run, but **a sidecar from an earlier run at the same path survives** (§3.6). Exit status 1.
   - **[I] (third-party fixture)** An out-of-range id at position `k > 0` left exactly `k` complete rows (ids `1,2,3,20000,5` gave 240,000 bytes = 3 × 80,000), exit 1, no sidecar.
   - **[I] (third-party fixture)** An out-of-range id at position 0 left a **0-byte** dump file, because the file is created before the first step (§3.4).
   - **[I] (third-party fixture)** A missing output directory failed after the weights were loaded, with exit 1 and no file. The message, `No such file or directory (os error 2)`, does not name the path.
   - **[I] (third-party fixture)** After a good run, a mid-run failure without pre-run deletion truncated the dump to 2 complete rows and left the old sidecar (`positions: 4`) in place; a parse failure left the old dump and sidecar unchanged.
3. **[N]** **I/O failure while writing a row** (for example a full disk; `CLI/teacher_force.rs:83`): the file may end in the middle of a row.
4. **[N]** **Failure after the dump is complete:** if the sidecar write fails (`CLI/teacher_force.rs:131`), the dump file is complete but there is no new sidecar, and exit status is 1.
5. **[I]** **Interruption by a signal:** buffered data is not flushed. With the pinned toolchain (`rust-toolchain.toml`, channel 1.98.0), `BufWriter`'s default capacity is 8 KiB and each value is 4 bytes, so the file length at interruption is normally a multiple of 8192 bytes. A row (607,744 bytes) is not a multiple of 8192, so an interrupted file normally ends mid-row. This depends on standard-library internals and is not a property a reader may rely on (OI-4). **(third-party fixture)** SIGKILL, SIGTERM and SIGINT on an N = 4000 run each left a file whose size was a multiple of 8192 bytes and ended mid-row, with no sidecar.

### 8.2 Completeness markers

1. **[N]** The dump file contains no checksum, no row count and no end marker (§4.1).
2. **[N]** The only completion signals are external to the file: exit status 0 (§7.2); the stdout line `wrote [<N>, <V>] f32 to <OUT>` (§7.3); and the existence of a sidecar written by **this** run (§7.1). None of them alone is conclusive, because a sidecar from an earlier run can survive a failed run (§8.1.1, §8.1.2).

### 8.3 Reader and harness procedure

1. **[N-H]** Before each run, the harness MUST delete any existing file at the dump path and at its sidecar path, and MUST confirm both are absent.
2. **[N-H]** The harness MUST record the exit status, the full stdout and stderr, the full argv, the full environment and the exact `--tokens` string, and SHOULD compute its own SHA-256 of the dump file and the sidecar immediately after the run. A run whose environment is not exactly the pinned set is rejected under PROTOCOL "Baseline" ("Environment" and "Run acceptance"); the sidecar's `max_format_env` (§8.3.3.3) checks only one variable of that set.
3. **[N]** A reader MUST treat a dump as complete only if **all** of the following hold:
   1. exit status was 0;
   2. stdout contains `positions: <N>  vocab: <V>` and `wrote [<N>, <V>] f32 to <OUT>`, where `N` is the length of the recorded token list;
   3. the sidecar exists, parses as JSON, and has `positions == N`, `vocab == V`, `draft_depth == null`, `executed_layers == [0, model_layers]` and `max_format_env == "bf16"`;
   4. the dump file's size is exactly `4·N·V` bytes;
   5. stdout contains `representation: Q8_0  source: stored` and `runtime compile: 0 tensor(s)`, and the run passed the PROTOCOL "Baseline" acceptance check on the `projection plans:` line (a missing line fails it, §7.3.4);
   6. the harness confirmed, from its recorded argv, that the argument list was exactly the conforming one (§2.2.0);
   7. the recorded `--tokens` string is exactly the canonical rendering of the recorded id list (§2.3.4);
   8. (SHOULD) the modification times of the dump file and the sidecar are not earlier than the run's start, with no tolerance. This check is redundant when §8.3.1 was followed (both files deleted and confirmed absent before the run), and it does not replace §8.3.1.

   **[I] (third-party fixture)** A procedure implementing these checks accepted every conforming run and rejected every failure mode tried, including stale files with deletion skipped, `--bank`, `--draft-depth`, a silently ignored `--speculate`, wrong environment, non-canonical `--tokens`, and a host-dependent `BlasF32` head. In the stale case where deletion was skipped and the old dump and sidecar were intact (a parse failure after a good run), only exit status, stdout and a no-slack modification-time check distinguished the old files from a new success; in the mid-run stale case, size and `positions` also failed. Pre-run deletion (§8.3.1) is therefore the primary guard.
4. **[N]** A reader MUST reject a file whose size is not a multiple of `4·V`, and MUST NOT interpret a trailing partial row. A file of `4·k·V` bytes with `k < N` is an incomplete run and MUST be rejected as a whole; its first `k` rows MUST NOT be scored as a partial result unless the protocol says otherwise.
5. **[N]** For this profile, a reader SHOULD also require `V == 151936` **(from B3)**. A vocabulary-width mismatch with the reference makes the comparison invalid (PROTOCOL "A2 logit-match details").

## 9. Position-selective capture

1. **[N]** **LARQL does not support position-selective capture.** The `--logit-dump` path writes the logits of **every** stepped position, unconditionally, and has no flag or parameter that selects positions, a stride or a range (`CLI/teacher_force.rs:32-47, 68-84`; `CLI/args.rs:181-331`).
2. **[N]** Capture of all positions is therefore **the only conforming LARQL mode**. Every row `0 .. N−1` is computed and written.
3. **[I]** The owner's condition for selective capture (every preceding token executed, KV cache maintained) is met by construction, since LARQL computes and writes all positions. A harness or reader that scores only the preregistered positions does so by reading those rows from the complete file (§4.4). That is a reader operation, not a LARQL feature, and it requires the complete file (§8.3).
4. **[I]** Size consequence: a complete dump is `4·N·151936` bytes. For `N = 40,960` that is 24,893,194,240 bytes (about 24.9 GB) per sequence.

## 10. Maximum position behaviour

### 10.1 Answer

**[N]** For positions 32,768 to 40,959, and for positions at or beyond `max_position_embeddings` (40,960), LARQL **computes**. It does not refuse, clamp or wrap. Every position `p` is processed by the same code and the same formulas as `p = 0`. The only position-dependent bound in the code is the machine (`usize` range, memory).

### 10.2 Basis

1. **[N] No position limit is read on this path.** The container's context extent (`X.context_length`, from `max_position_embeddings`) is not referenced anywhere under `crates/larql-vindex/src/format/vindex3/opplan/`, `crates/larql-inference/src/` or `crates/larql-cli/src/` (search of the pinned tree; consistent with B3 §17.8, row `X.context_length`: "Ignored. No position bound is enforced from it"). Neither `parse_tokens` (`CLI/exec.rs:506-518`) nor `run_teacher_force` (`CLI/teacher_force.rs:39-93`) bounds `N`.
2. **[N] The position is an unbounded counter.** It is a `usize` incremented once per step (`EX/kv.rs:403`, `EX/decode/run.rs:43, 674`).
3. **[N] RoPE has no table.** For `kind: "rope"`, each step rotates every query and key head slice with `rope_rotate(head, position, theta)` (`EX/production.rs:302-311`). For pair `i` of a head of width `d`, it computes `inv_freq = theta^(−2i/d)` and `angle = position · inv_freq` in binary64, rounds `sin(angle)` and `cos(angle)` to binary32, and applies the split-half rotation in binary32 (`EX/kernels.rs:147-158`). There is no precomputed cos/sin table whose length could bound the position, and no reduction of `position` modulo anything. **(from B3)** Every layer of this container declares `{"kind":"rope","theta":1000000.0}` with no scaling (B3 §17.5, §17.7); with no declared scaling the policy resolves to unscaled `Rope { theta }` (`POS:257-263`; `crates/larql-models/src/config/architecture/position.rs:366`).
4. **[N] The KV cache is unbounded.** The `row/v1` provider appends each position's K and V rows to growable vectors with no capacity limit (`EX/kv.rs:389-410, 459-463`).
5. **[N] Attention reads every earlier position.** For a `"full"` span the first readable key position is 0 (`EX/kv.rs:74-79`), so the step at position `p` attends to keys `0 ..= p` (`EX/production/helpers.rs:228-234`). **(from B3)** All 28 layers are `"full"` (B3 §17.5).

6. **[I] (third-party fixture)** On a fixture with `max_position_embeddings = 128` and `N = 200`, the run exited 0, all values were finite, and positions 128–199 agreed with an independent float64 forward using unbounded RoPE as well as positions 0–127 did. No refusal, clamp or wrap was observed. This was not tested at subject scale, and the resource figures in §10.3.2 were not tested.

### 10.3 Consequences for the protocol

1. **[I]** Under the owner's ruling (D11 draft §12), LARQL does not refuse extended positions, so a LARQL run never yields an "unsupported comparison" on LARQL's side for that reason. Whether "computes by the same formula, with no declaration" counts as "explicitly defined and supported positional behaviour" is not a question the source answers: LARQL declares nothing about positions beyond the native context. See OI-5.
2. **[I]** A run at large `N` may fail for resource reasons (memory, disk, time). Such a failure is not a refusal by LARQL. Rough sizes for `N = 40,960`, from the B3 geometry (28 layers, 8 KV heads, head width 128): K and V together take 8,192 bytes per layer per position, about 9.4 GB in total, plus vector overhead; the dump is about 24.9 GB (§9.4). How a resource failure is classified is open (OI-15).
3. **[I]** LARQL forms the RoPE angle in binary64. An implementation that forms it in binary32 has an angle error that grows with the position (on the order of `p · 2^-24` radians for the lowest-index pair). This is a comparison concern for the reference, not a property of the dump, and is not evaluated here.

## 11. Precision of what is written

1. **[N]** The logits are computed as binary32 and written as the same binary32 values, bit for bit. There is no conversion, rounding, clipping, scaling or reordering between the computed vector and the file:
   - the head returns `Vec<f32>` (`EX/production/plan_backend.rs:319-342`; `EX/prepared/accessors.rs:169-209`);
   - the step returns it unchanged as `StepOutput.logits` (`EX/decode/run.rs:654-677`);
   - the writer writes each element's `to_le_bytes` (`CLI/teacher_force.rs:69-72, 82-84`).
2. **[N]** What is computed (for reference; arithmetic is outside the format):
   - the final norm is applied to the exit hidden state if the plan has one (`EX/prepared/accessors.rs:177-185`);
   - then the head projection gives one binary32 dot product per vocabulary row (`EX/production/plan_backend.rs:328`);
   - then, if declared, a binary32 multiplier and a softcap `cap·tanh(x/cap)` (`EX/production/plan_backend.rs:333-340`).
   **(from B3)** This container declares neither the multiplier nor the softcap (B3 §17.6), so neither is applied.
3. **[I]** With the pinned environment, the head runs `FusedBf16`: BF16 weights widened exactly to binary32, binary32 activation, NEON fused multiply-add in four 4-lane accumulators, then a horizontal sum and a scalar tail (`EX/cpu/kernels.rs:86-102, 701-751`). Without `LARQL_CPU_MAX_FORMAT=bf16`, the head is re-quantised and runs `FusedQ8` (`evidence/L1/AUDIT.md`, headline finding). That changes the values written, not the format; such a run is invalid under PROTOCOL "Baseline".
4. **[I] Host dependence of the head's kernel (C5).** For a BF16 matrix the production plan is chosen by size against the host's L2 cache size, read from `hw.perflevel0.l2cachesize` (`EX/cpu/physical/projection.rs:541-549`). A matrix whose **f32 image is smaller than L2** runs `BlasF32`, whatever `LARQL_CPU_MAX_FORMAT` says (`EX/cpu/physical/projection.rs:203-209`). The `bf16` cap matters only when the BF16 image is at least L2 (`EX/cpu/physical/projection.rs:218`). The subject's head has 155,582,464 elements, so its f32 image is about 622 MB and its BF16 image about 311 MB, far above any current L2; `FusedBf16` is therefore expected under the pin. The `projection plans:` check is nevertheless a per-host observation. A fixture used to test the acceptance procedure needs a head whose **f32** image is at least the host's L2, so that it runs `FusedBf16` rather than `BlasF32` (`EX/cpu/physical/projection.rs:207-209`). A BF16 image of at least L2 is additionally needed only if the fixture must show the cap's effect (`FusedQ8` without the cap, `EX/cpu/physical/projection.rs:218`). **(third-party fixture)** a fixture with a 10.24 MB BF16 head (20.48 MB as f32), on a 16 MiB-L2 host, ran `FusedBf16` and was accepted; removing the cap changed no value. **(third-party fixture)** a fixture with a 10.24 MB f32 head ran `BlasF32` on a 16 MiB-L2 host and was correctly rejected by the acceptance check.

## 12. Determinism and threads

1. **[N]** The dump contains no timing, thread or scheduling data (§4.1). The sidecar contains wall-clock timings (`prepare_s`, `steps_s`, `ms_per_position`), so **the sidecar is not byte-reproducible**, even when the dump is.
2. **[N]** On this path, thread parallelism is used only to split the rows of a matrix-vector product between workers. Each output element is computed entirely by one call on one thread, and no reduction crosses threads:
   - **output head and other executor-pool projections** (pool size from `LARQL_CPU_WORKERS`, `EX/cpu/executor.rs:384-398`): contiguous row partitions, `out[o] = bf16_dot(row o, x)` per row (`EX/cpu/executor.rs:254, 266-272`; `EX/cpu/kernels.rs:93-101`);
   - **stored Q8_0 projections** (`FusedKQuant`, library-owned threading, `EX/cpu/kernels.rs:413-444`; `EX/cpu/executor.rs:183-195`): rows in 32-row chunks on the rayon global pool (`RAYON_NUM_THREADS`), each row a sequential binary32 sum in a fixed order (`KQ:58, 67-109`);
   - **attention at a decode step:** a serial loop over heads and key positions (`EX/production/select.rs:215-251`; `EX/production/helpers.rs:228-266`);
   - **RoPE:** a serial loop (`EX/production.rs:302-311`; `EX/kernels.rs:147-158`).
3. **[I]** By inspection, then, the dump's values do not depend on `LARQL_CPU_WORKERS`, `RAYON_NUM_THREADS` or scheduling. This is a reading of the code. **(third-party fixture)** an N = 200 dump was bit-identical across two Baseline runs and at `LARQL_CPU_WORKERS`/`RAYON_NUM_THREADS` = 1, 4 and 12, with the head split across the executor pool at 4 and 12; the sidecars differed only in the timing fields (OI-9). The protocol pins both variables to 12 anyway.
4. **[I]** The values depend on the binary, the CPU architecture (the NEON path is chosen at compile time for aarch64, `EX/cpu/kernels.rs:701-713`) and the platform maths library used for `powf`, `sin` and `cos` in RoPE (OI-8).

## 13. Open items

| ID | Item | Why it is open |
|---|---|---|
| OI-1 | **No identifiers in the output.** Neither the dump, nor the sidecar, nor stdout records token ids. Row-to-position mapping rests on the harness's record of `--tokens` (§6.5) | Writer design; cannot be fixed by a reader |
| OI-2 | **Stale files survive.** A run that fails before `File::create` leaves an older dump and sidecar untouched; a run that fails mid-way leaves an older sidecar beside a new partial dump (§8.1) | Writer design; mitigated only by the harness deleting both files first (§8.3.1) |
| OI-3 | **No in-file completeness marker or checksum.** The sidecar is written after the dump but non-atomically. Completeness is inferred from exit status, stdout, sidecar and size together (§8.2, §8.3) | Writer design |
| OI-4 | **Truncation granularity (partly settled).** **(third-party fixture)** A mid-run error left a file ending on a row boundary (`k` complete rows); a signal left a multiple of 8192 bytes, mid-row (§8.1). Both observed at toolchain 1.98.0. They remain standard-library behaviour, not LARQL statements, so a reader still rejects anything not exactly `4·N·V` | Standard-library behaviour; the reader rule makes it irrelevant to acceptance |
| OI-5 | **"Defined and supported" at extended positions.** **(third-party fixture)** Computation beyond the declared context was observed on the fixture (§10.2.6). LARQL computes at every position by one formula, but declares no support for positions beyond the native context and enforces no limit. Whether that satisfies the owner's "explicitly defined and supported" condition is a protocol decision (§10.3.1) | The source defines behaviour by code but makes no support claim |
| OI-6 | **Expected sidecar values (partly settled).** **(third-party fixture)** `draft_depth: null`, `executed_layers: [0, L]`, `model_layers: L` observed for L = 2. `--draft-depth L` records `draft_depth: L` with a dump bit-identical to the full run, so only the sidecar shows the flag. The subject value L = 28 remains expected, not observed | Not observable without a subject run |
| OI-7 | **Closed for the format.** **(third-party fixture)** Byte layout, endianness, shape, row and column order and size were checked against emitted files and an independent forward (§4–§6). Subject-specific values (V = 151936, 28 layers) remain derived | — |
| OI-8 | **Platform maths library.** RoPE uses binary64 `powf`, `sin` and `cos` from the platform library. The values may change with the OS or library version even with the binary fixed | The source does not pin the maths library. The protocol may need to pin the OS build |
| OI-9 | **Closed on the fixture.** **(third-party fixture)** Dumps bit-identical at worker counts 1, 4 and 12 and across repeated runs (§12.3). This shows the property for that binary and those shapes, not for the subject's | Subject shapes not tested |
| OI-10 | **Lenient token parsing (confirmed; mitigated by the canonical-`--tokens` MUST, §2.3.4, §8.3.3.7).** **(third-party fixture)** Every listed case behaves as §2.3 says: `5,,9` silently runs N = 2; `+5,007,9` runs the same sequence as `5,7,9`, so only a canonical-string check catches it; a non-breaking space is trimmed | Writer design; mitigated by canonical harness input, the canonical-string check and `positions == N` |
| OI-11 | **`--bank` silently overrides `--logit-dump` (confirmed).** **(third-party fixture)** Exit 0, nothing written at the `--logit-dump` path, no `positions:`/`wrote [` lines | Writer design; mitigated by the exact-argv rule (§2.2.0) |
| OI-12 | **Non-finite logits are written without comment** (§4.2). Whether a NaN or infinity in a dump is a run failure or a scored value is not decided by the writer | Protocol decision |
| OI-13 | **Unescaped environment value in the sidecar (confirmed).** **(third-party fixture)** `LARQL_CPU_MAX_FORMAT='bf"16'` gave exit 0 and an invalid-JSON sidecar | Writer design; harmless under the pinned value `bf16` |
| OI-14 | **Closed.** **(third-party fixture)** `vindex3 exec --help` lists exactly the 22 flags of `CLI/args.rs:181-331` plus `CLI/plugins.rs:36-57`. Some of them are accepted and ignored with `--logit-dump` (§2.2, C2) | — |
| OI-15 | **Resource failures at large `N`.** Not tested by the fixture. A run near `N = 40,960` needs roughly 9.4 GB of KV state and writes about 24.9 GB (§9.4, §10.3.2). Whether a resource failure counts as an unsupported comparison, a harness failure or something else is not decided | Protocol decision |
| OI-16 | **The engine string does not identify the arm (confirmed).** **(third-party fixture)** `--backend production` writes the same `engine` string; it also prints no `representation:` line (§7.3.3) | Writer design; the harness archives the argv and stdout |

## 14. Changes against revision 1

| # | Section | Change |
|---|---|---|
| C1 | §7.2 | Exit status 2 for argument-parser (clap) rejections and the trampoline refusal, not 1. A reader requires 0 and gives no meaning to particular non-zero values |
| C2 | §2.2 | New row: `--speculate`, `--stop-at-eos`, `--residency-curve`, `--profile` (and the `residency_curve`-dependent flags) are accepted with `--logit-dump` and ignored; MUST NOT be passed. New §2.2.0: the harness passes exactly the conforming argv |
| C3 | §7.3 | Exact print conditions for `representation:`, `runtime compile:`, `stored precision:` and `projection plans:`; `representation:` also prints on runs that later fail; none print under `--backend production`; a missing `projection plans:` line fails acceptance |
| C4 | §8.1 | Observed boundary cases: `k` complete rows for a bad id at position `k`; 0-byte file for position 0; missing directory fails after load with no file; signal truncation at a multiple of 8192 bytes, mid-row |
| C5 | §11.4 | New informative note: the head's kernel depends on the host's L2 size; `FusedBf16` expected for the subject's ~622 MB f32 head, but the check is per host |
| — | Header, §0 | Revision 2 status; the **(third-party fixture)** label defined |
| — | §6, §8.3, §10.2.6, §12.3, §13 | Third-party fixture evidence added; reader procedure gains the stored-representation lines and the exact-argv condition; OI-4, -6, -7, -9, -10, -11, -13, -14, -16 updated or closed; OI-5 and OI-15 annotated. No byte-format statement changed |

### 14.1 Changes against revision 2

| # | Section | Change |
|---|---|---|
| D1 | §2.2 | The C2 row is split. `--speculate`, `--stop-at-eos`, `--residency-curve` and `--profile` (requires `--generate`, which conflicts with `--logit-dump`) are accepted and ignored. `--repeat`, `--warmup`, `--unquiet-ok` and `--expert-access` (requires `--residency-curve`) are rejected with exit 2 unless `--residency-curve` is also passed, and are then accepted and ignored. All MUST NOT be passed. The §2.2.0 exact-argv rule is unchanged |
| D2 | §11.4 | A fixture for testing the acceptance procedure needs a head whose f32 image is at least L2 (`projection.rs:207-209`); a BF16 image of at least L2 is needed only to show the cap's effect (`:218`) |
| D3 | §2.3.4, §2.3.5, §8.3.3.7 | Canonical `--tokens` is now a MUST, with its definition; the harness compares the argv string byte for byte with the canonical rendering of its token manifest; added as reader condition 7. OI-10 notes the mitigation |
| D4 | §8.3.3.8 | Zero-tolerance modification-time check added as a SHOULD condition, stated to be redundant when §8.3.1 is followed |
| M1 | §8.3 note | The stale-case sentence is limited to the case with deletion skipped and the old files intact |
| Advisory | §8.3.2 | The harness records the full argv and environment; cross-reference to the PROTOCOL "Baseline" rule that the environment is exactly the pinned set |
| — | Header | Revision 3 status. No byte-format statement changed |

## Revision history

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-10-31 | First draft, from LARQL source at `2536bb79` only. Not admitted |
| 2 | 2026-10-31 | Applies corrections C1–C5 of the third-party check (`THIRD-PARTY-CHECK.md`, `4bce40d`) and records its fixture evidence (§14). Not admitted; requires third-party confirmation of the corrections |
| 3 | 2026-11-01 | Fixes D1–D4, M1 and the advisory from the confirmation of revision 2 (`THIRD-PARTY-CHECK.md`, `bc063f2`) (§14.1). Not admitted; requires third-party confirmation of corrections |
