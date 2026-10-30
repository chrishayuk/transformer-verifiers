# L1: clean LARQL baseline

Recorded 2026-10-30 by the coordinating session. It is not the reference-checker agent, and it is not the L1
auditor, whose report is `AUDIT.md`. This file records what was built. It does not claim that L1 is met.

| Item | Value |
|---|---|
| LARQL commit | `2536bb79b199b1115445678e3e82c400b0b3fd07` (`origin/main`, 2026-10-30) |
| Worktree | `/Users/christopherhay/chris-source/larql-l1-2536bb79`, detached. `git status --porcelain` is empty before and after the build and encode |
| Build | `cargo build --release --locked -p larql-cli`, exit 0 (`build.log`) |
| Binary | `target/release/larql`, sha256 `4d80dd42c4b50dd83c35d4a3c2d273e12a95d31dd4816c51ca2323dfc8462322` |
| Upstream | Qwen/Qwen3-0.6B at `c1899de289a04d12100db370d81485cdf75e47ca` (hashes in PROTOCOL.md) |
| Encode | `env -i PATH=/usr/bin:/bin HOME=$HOME larql vindex3 encode <snapshot> --output qwen3-0.6b.vindex3`, then `… vindex3 represent qwen3-0.6b.vindex3 --output qwen3-0.6b-q8_0.vindex3 --encoding Q8_0`. Both exit 0 (`encode.log`) |
| Container | `/Users/christopherhay/chris-models/l1-2536bb79/qwen3-0.6b-q8_0.vindex3`, 1.9 GB, 11 files. Per-file SHA-256 in `container-q8_0.sha256`. The checker session cannot read it |
| Reproducibility | A second encode into a fresh directory was byte-identical in 10 of 11 files. `candidate.json` differs only in `locator_hint`, the absolute path of the source container. The freeze must therefore pin the container's path, or the manifest must exclude that field |

## Findings from the L1 audit, checked by the coordinating session

- **The LM head is silently re-quantised at load.** With `--backend production-q8 --representation-source stored`,
  but without `LARQL_CPU_MAX_FORMAT=bf16`, the BF16 LM head (311 MB, above the 16 MiB L2) is selected as `FusedQ8`.
  The loader then quantises it in `crates/larql-vindex/src/format/vindex3/opplan/exec/weights/load.rs:69-89`. The
  Q8 arm does not call `note_runtime_quantisation`, unlike the MXFP4 (`:130`) and NVFP4 (`:157`) arms, so `stored`
  does not refuse it, and `exec` still reports serving only stored bytes. The coordinating session confirmed the
  missing call by reading the file. It did not run exec. **This is a LARQL defect**, and it was already present at
  `ff364ba6`. The baseline pins `LARQL_CPU_MAX_FORMAT=bf16` and accepts a run only if `projection plans:` lists
  nothing but `FusedKQuant` and `FusedBf16`.
- **The Q8_0 encoder's f32 → f16 conversion truncates and flushes to zero** (`half.rs:43-60`). Unchanged from
  `ff364ba6`.
- **No physical tie.** The snapshot ships an explicit `lm_head.weight`, byte-identical to `embed_tokens`. Under the
  default role policy, both stay BF16 and are stored as separate objects.

## Still open for L1

- An auditor's review of this record and of `AUDIT.md`, as a second pair of eyes on the audit.
- Running LARQL's exec for E2 and E3 is a post-freeze step. It is done by an operator outside the checker session,
  because the checker cannot read or run LARQL. The operator hands the checker only the logit dumps and the recorded
  environment.

## LM-head reproduction (2026-10-30)

The defect was reproduced by running exec from outside the code, not only by reading it. The runs used
`--tokens 9707,11,1879` and no `--logit-dump`, so no logits from the subject were produced.

| Run | `projection plans:` | Log |
|---|---|---|
| Unpinned | `FusedQ8 1 calls 0.17 GB, FusedKQuant 420 calls 1.40 GB` | `repro-lmhead-unpinned.log` |
| `LARQL_CPU_MAX_FORMAT=bf16` | `FusedBf16 1 calls 0.31 GB, FusedKQuant 420 calls 1.40 GB` | `repro-lmhead-pinned.log` |

Both runs print "served entirely from stored bytes". Filed upstream as chrishayuk/larql#665. The fix is kept separate
from LARQL-VERIFY-001. The workaround is part of the pinned baseline, and the defect stays open.
