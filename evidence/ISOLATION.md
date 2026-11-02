# Reference-checker isolation (Phase 1)

Set up 2026-10-30 by the coordinating session, which is not the reference-checker agent. The user chose the
mechanism: a separate Claude Code session with sandboxing.

## Mechanism

- **Launcher:** `isolation/launch-checker.sh`. It starts Claude Code in `checker/`, with:
  - `--settings isolation/checker-settings.json`, a settings file outside the workspace that the checker cannot
    write and that overrides anything in the workspace
  - `--strict-mcp-config`, so no MCP servers are loaded
  - `GH_TOKEN`, `GITHUB_TOKEN` and `HF_TOKEN` unset
  - `TMPDIR` set inside the workspace
- **Reads:** for both the file tools and every sandboxed shell command, the whole home directory, `/private/tmp`,
  `/private/var/folders` and `/Volumes` are denied. Only these are re-allowed:
  - `checker/`
  - `protocols/LARQL-VERIFY-001/`
  - `inputs/`: ggml at `facdc44a`, with `SHA256SUMS`
  - the pinned Qwen3-0.6B HF cache entry
  - the uv Python runtime
  - `~/.gitconfig`
  - the checker session's own Claude temp directory

  This allow-list design is needed because LARQL text exists in many places a deny list would miss: worktrees under
  `/private/tmp`, Claude transcripts and subagent outputs, and a cargo checkout.
- **Network:** none (`allowedDomains: []`, strict). LARQL's repository is public, so any network access could fetch
  its source.
- **Writes:** the protocol, `inputs/`, `isolation/` and the HF cache are denied.
- **Other restrictions:** WebFetch, WebSearch, `gh`, `git push` and `git remote` are denied. Unsandboxed commands and
  bypass-permissions mode are disabled. claude.ai connectors are off.
- **Separate git history:** `checker/` is its own git repository, ignored by the parent, so the parent's history
  (which contains LARQL-derived documents) cannot be read through `git show`.
- **Dependencies:** `checker/requirements.lock`, hash-pinned. numpy 2.4.2, safetensors 0.7.0, torch 2.14.0,
  transformers 5.5.0, gguf 0.18.0. No LARQL package is installed.

## Tests (headless `claude -p` through the launcher, model sonnet)

| # | Attempt | Result |
|---|---|---|
| 1 | `head` LARQL source in the main checkout | BLOCKED (sandbox) |
| 2 | Read tool on LARQL source | BLOCKED (blockReadsOutsideWorkingDirectories) |
| 3 | `head` `transformer-verifiers/larql/CAPABILITIES.md` | BLOCKED (sandbox) |
| 4 | list `~/.claude/projects` (transcripts) | BLOCKED |
| 5 | list `/private/tmp` (worktrees, task outputs) | BLOCKED |
| 6 | list `~/.cargo/git/checkouts` | BLOCKED |
| 7 | `curl` LARQL README from GitHub | BLOCKED (network denied by sandbox proxy) |
| 8 | `git log` in the parent repo | BLOCKED |
| 9 | append to `PROTOCOL.md` | BLOCKED (denyWrite) |
| 10 | `gh auth status` | BLOCKED (permission deny) |
| 11 | read `PROTOCOL.md` | allowed, as intended |
| 12 | import `gguf.quants.Q8_0` from the venv | allowed |
| 13 | read the pinned Qwen3 `config.json` | allowed |
| 14 | read vendored `ggml-common.h` | allowed |
| 15 | write, read and delete a file in `checker/`; `git status` and `git log` in `checker/` | allowed, after allowing the session's own temp directory and setting `TMPDIR` |
| 16 | list `/private/tmp/claude-501`; read another session's task outputs | BLOCKED |

## Residual risks, not closed by this mechanism

- **Same OS user.** The checker session runs as the same macOS user. The boundary is Claude Code's sandbox and
  permission layer, not the operating system's user separation. A Docker container or a separate user would be
  stronger.
- **Unsandboxed tools.** The Claude Code process itself is not sandboxed; only its tools are restricted. Any tool
  added to the session later must be checked against this policy.
- **The protocol is readable.** `PROTOCOL.md` describes some LARQL behaviour, for example the `half.rs` conversion and
  CLI flags. It is the checker's requirements document and is admitted on purpose. It contains no LARQL decoder code.
- **B3 is not admitted yet.** The B3 container specification will be added to the allow-list only after its
  third-party check.
- **Changes after these tests.** Any change to the isolation files after these tests requires rerunning them.

## Part 3: after admitting the B3 specification

The settings file was re-tested at sha256 `a4cc2006…`.

- **SPEC.md readable:** both through the shell (hash `3c4feb5e…` matches) and through the Read tool.
- **SPEC.md not writable:** blocked through the shell (`denyWrite`) and through the Edit tool (permission deny).
- **Still blocked:**
  - `evidence/B3/AUTHOR-NOTES.md` (shell) and `evidence/B3/CHECK.md` (Read tool)
  - the fresh container under `~/chris-models/l1-2536bb79`
  - both LARQL trees, and `larql/CAPABILITIES.md`
  - GitHub over the network
  - editing `isolation/checker-settings.json`
- **Hashes unchanged after the test:** SPEC.md and the settings file.

## Settings change after part 3

`checker-settings.json` gained `"attribution": {"commit": "", "pr": ""}`, the user's no-trailer preference, and is
now sha256 `d05ce78f…`. Attribution does not affect isolation. The run started before this change (checker run 1)
used `a4cc2006…`.

## Part 4: immutable protocol snapshot (2026-10-31)

The protocol owner asked for each checker session to read a fixed protocol snapshot, not the live `PROTOCOL.md`. That
removes the risk of a protocol change reaching a session mid-run.
- **The snapshot:** `isolation/snapshots/1bfc341/` holds `PROTOCOL.md` (sha256 `79795f18…`) and `draft.json`
  (`f839c18b…`), copied from commit `1bfc341` (D1–D5), with `SHA256SUMS`. It sits under `isolation/`, which the
  checker cannot write.
- **The settings change:** the checker's read access to `protocols/LARQL-VERIFY-001` (both `additionalDirectories`
  and the sandbox `allowRead`) is replaced by the snapshot directory. Settings are now sha256 `6f293a60…` (were
  `d05ce78f…`).
- **Every later checker run** names the snapshot it reads. A new snapshot directory, and this re-test, are needed
  each time the snapshot changes.

**Re-test, run as the checker role** (`isolation-test-4.log`):

| Probe | Result |
|---|---|
| Snapshot `PROTOCOL.md`, shell and Read tool | Allowed; hash `79795f18…` matches |
| Live `protocols/LARQL-VERIFY-001/PROTOCOL.md`, shell and Read tool | Blocked |
| Write to the snapshot (shell `touch`, Edit tool) | Blocked |
| `evidence/decisions/` draft records | Blocked |
| SPEC revision 3 | Allowed; hash `6350e07c…` |
| Reviewer repository | Blocked |
| GitHub over the network | Blocked |

The snapshot and settings hashes were unchanged after the test.

## Part 5: protocol snapshot 723d5ff (2026-10-31)

The snapshot moves to `isolation/snapshots/723d5ff/` (D1–D7; `PROTOCOL.md` `edd3933f…`, `draft.json` `465b5f0a…`).
Settings are now sha256 `a8f65afa…`; the only change is the snapshot path.

**Re-test** (`isolation-test-5.log`):
- **Allowed:** the new snapshot (hash matches) and SPEC revision 4 (`8f3f7c2b…`).
- **Blocked:** the old snapshot, the live protocol (shell and Read tool), writes to the snapshot, the reviewer's
  `evidence/D2-FIELD-ASSESSMENT.md`, the real container, and the reviewer repository.

## Part 6: protocol snapshot 19ab645 (2026-10-31)

The snapshot moves to `isolation/snapshots/19ab645/` (D1–D8; `PROTOCOL.md` `1e79ae8b…`, `draft.json` `82abec65…`).
Settings are now sha256 `25fa1d9a…`; the only change is the snapshot path.

**Re-test** (`isolation-test-6.log`):
- **Allowed:** the new snapshot (hash matches) and SPEC revision 4.
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, the reviewer repository, and the real
  container.

## Part 7: protocol snapshot db08851 (2026-10-31)

The snapshot moves to `isolation/snapshots/db08851/` (D1–D9 plus the D9 clarification; `PROTOCOL.md` `63cae151…`,
`draft.json` `591a9a36…`). Settings are now sha256 `3f848cca…`; the only change is the snapshot path.

**Re-test** (`isolation-test-7.log`):
- **Allowed:** the new snapshot (hash matches).
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, `evidence/AMB-022-MAPPING-AUDIT.md`, the
  reviewer repository, and the real container.

## Part 8: protocol snapshot 6f28db9 (2026-10-31)

The snapshot moves to `isolation/snapshots/6f28db9/` (D1–D9 with clarifications 1–3; `PROTOCOL.md` `2fac79c0…`,
`draft.json` `5d2d13f8…`). Settings are now sha256 `9bb1b621…`; the only change is the snapshot path.

**Re-test** (`isolation-test-8.log`):
- **Allowed:** the new snapshot (hash matches).
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, the reviewer repository, and the real
  container.

## Part 9: protocol snapshot c972d62 (2026-10-31)

The snapshot moves to `isolation/snapshots/c972d62/` (D1–D10; `PROTOCOL.md` `8595bd28…`, `draft.json` `bf5b9455…`).
Settings are now sha256 `b78f15d4…`; the only change is the snapshot path.

**Re-test** (`isolation-test-9.log`):
- **Allowed:** the new snapshot (hash matches).
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, the reviewer repository, and the real
  container.

## Part 10: checker clones moved out of the reviewer workspace (2026-10-31, D10 clarification 1)

- **The finding:** the reviewer repository held git-ignored clones of the pinned checkers used in scoring runs 1–7,
  under `scoring/run-N/checker-src`.
- **The access check:** the revision 7 corpus author's tool-call log has 38 calls. The only call touching those
  folders listed `scoring/run-7` and read its `RULES.md`. None opened, searched or grepped a clone. The author's
  declaration is kept.
- **The move:** all seven clones were moved, unchanged, to `~/chris-source/transformer-verifiers-eval/run-N/checker-src`:

  | Run | Clone at |
  |---|---|
  | 1 | `2e8fd34` |
  | 2, 3 | `cd49069` |
  | 4 | `3337645` |
  | 5 | `ab38748` |
  | 6 | `147a24e` |
  | 7 | `e232720` |

  No tracked file in the reviewer repository changed.
- **From now on,** the pinned checker for scoring is placed there only after the corpus is sealed.

## Part 11: protocol snapshot e056903 (2026-10-31)

The snapshot moves to `isolation/snapshots/e056903/` (D1–D10 and D12; D11 is a proposal and not in the protocol):
`PROTOCOL.md` `99a391a6…`, `draft.json` `a3d417b8…`. Settings are now sha256 `33c9cf16…`; the only change is the
snapshot path.

**Re-test** (`isolation-test-11.log`):
- **Allowed:** the new snapshot (hash matches).
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, the reviewer repository and the real
  container.
- **Blocked, new probes:** the reference-audit repository, and the unadmitted logit-dump specification.

## Part 12: protocol snapshot 7f1b246, with the admitted logit-dump specification (2026-11-01)

The snapshot moves to `isolation/snapshots/7f1b246/`. It holds:
- D1–D10, and D12 with clarifications 1–2: `PROTOCOL.md` `76504d78…`, `draft.json` `82b7bc89…`;
- the admitted logit-dump specification revision 3, copied in as `LARQL-LOGIT-DUMP-SPEC.md` `5ad44e33…`.

Settings are now sha256 `c61f3ea9…`; the only change is the snapshot path.

**Re-test** (`isolation-test-12.log`):
- **Allowed:** the new snapshot, and the specification copy inside it (both hashes match).
- **Blocked:** the old snapshot, the live protocol, writes to the snapshot, the reviewer repository, the real
  container and the reference-audit repository.
- **Blocked, new probes:** the third-party check report, the fixture repository, and the LARQL worktree.

## Part 13: protocol snapshot 932de33 (2026-11-01)

The snapshot moves to `isolation/snapshots/932de33/`. It holds:
- D1–D10, D12 with clarifications 1–3, and D13: `PROTOCOL.md` `78f49789…`, `draft.json` `37c2104a…`;
- the admitted logit-dump specification, `LARQL-LOGIT-DUMP-SPEC.md` `5ad44e33…`.

Settings are now sha256 `fb08761d…`; the only change is the snapshot path.

**Re-test** (`isolation-test-13.log`):
- **Allowed:** the new snapshot and its specification copy.
- **Blocked:** everything blocked in part 12.
- **Blocked, new probe:** the separate evaluation directory.

## Part 14: protocol snapshot 8b3663a (2026-11-01)

The snapshot moves to `isolation/snapshots/8b3663a/`. It holds:
- D1–D15, with D15 clarification 1 (DO-1): `PROTOCOL.md` `927c0cb9…`, `draft.json` `125e4ad3…`;
- the admitted logit-dump specification, `LARQL-LOGIT-DUMP-SPEC.md` `5ad44e33…`, unchanged.

Settings are now sha256 `22829887…`; the only change is the snapshot path.

**Re-test** (`isolation-test-14.log`):
- **Allowed:** the new snapshot and its specification copy.
- **Blocked:** everything blocked in part 13.
- **Blocked, new probes:** the development harness `dev/larql-verify/`, its real-run records, and the T3 calibration
  review repository.

## Part 15: protocol snapshot 5d1b1f1 (2026-11-02)

The snapshot moves to `isolation/snapshots/5d1b1f1/`. It holds:
- D1–D15, with D15 clarification 2 (checker maintenance 16): `PROTOCOL.md` `411a6922…`, `draft.json` `6e97a9cb…`;
- the admitted logit-dump specification, `LARQL-LOGIT-DUMP-SPEC.md` `5ad44e33…`, unchanged;
- **new:** `REAL-STDOUT-FIXTURES.json` `b68901ab…`, the stdout of three real development runs, which clarification 2
  admits as the one exception to synthetic-only tests. It holds no logits, weights or token ids.

Settings are now sha256 `d9a158e9…`; the only change is the snapshot path.

**Re-test** (`isolation-test-15.log`):
- **Allowed:** the new snapshot, its specification copy and the fixture file; the pinned ggml source in `inputs/`, as before.
- **Blocked:** everything blocked in part 14, with the previous snapshot now blocked too, and writing to the new snapshot.
- **Blocked, new probes:** the development baseline `runs/suite-v1` and the attribution results `runs/attribution-v1`.
