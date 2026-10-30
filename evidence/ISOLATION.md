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
