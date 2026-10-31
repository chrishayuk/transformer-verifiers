# Hidden reviewer corpus: seal

A hash commitment to the independent reviewer's hidden cases, published without revealing them. The corpus lives in a
separate local repository, `~/chris-source/transformer-verifiers-reviewer`, which the checker session cannot read.

| Item | Value |
|---|---|
| Sealed on | 2026-10-30, after the reviewer's report and before any scoring |
| Commit | `8603fb7237851ea3a3a48a2630c6b3e2a9a51494` |
| Tree | `6177f6893ebf87e756c1842840e1718c255887b1` |
| Files | 1440 |
| Digest of `git ls-files` contents (see the digest method below) | `f67ca509e475a79c8e3a87b4b37f116adf328f12221236d0a18992aa17641e91` |
| Cases | 208: A0 28, E1 24 (+7 ambiguous), containers 94, mutations 30, metrics 21 (+4 ambiguous) |

Any scoring must name this commit. A change to the corpus after this seal is a new corpus, and must be sealed again
before it is used.

**Pre-freeze observation by the reviewer, recorded for transparency.** While targeting mutations at the real
container, the reviewer observed that the unmutated container already exceeds T2 in every tensor it examined. The
protocol predicts this for LARQL's truncating encoder (Tolerance rules, "T2 is expected to be exceeded"). T2 was fixed
before this observation and does not change. The observation is not Stage A evidence, and it was not given to the
checker.

## Scoring run 1 (2026-10-30): aggregates only

The full results are in the reviewer repository (`scoring/run-1/`, commit `2c3e289` and the transcription after it).
They stay sealed from the checker.

- **Checker:** `2e8fd34`.
- **Corpus:** `8603fb7`, unchanged (zero diff in the case directories).
- **Rules:** fixed in a commit made before the run.
- **Scope:** A0, E1, synthetic containers and metrics. The 30 real-container mutations are held until after the freeze.

| | Pass | Fail | Error |
|---|---|---|---|
| Unambiguous cases | 153 | 1 | 0 |

- **The one failure** is a corpus classification defect, not a checker defect. The checker took a defensible reading
  of an unspecified rule, and still refused the wrong model.
- **Ambiguous cases** (26 entries) were scored separately, and the readings the checker took are recorded.
- **Nothing was disclosed to the checker, so no case is burned.** The misclassified case is to be reclassified as
  ambiguous in the next corpus revision, which must be sealed again before it is used.
- **This is Phase 1 information, not Stage A evidence.**

## Digest method (clarified 2026-10-31)

For each path in `git ls-files` at the commit, in byte order of path, take the line
`<sha256 of the file contents>  <path>\n` (the `shasum -a 256` format). The digest is the SHA-256 of the concatenation
of those lines. That is `git ls-files -z | xargs -0 shasum -a 256 | shasum -a 256` in a clean checkout. The earlier
wording ("the sorted per-file SHA-256 list") left out that each line includes the path. The coordinating session
recomputed both seals from the git objects with this method: `f67ca509…` for revision 1 and `62b4e3d3…` for
revision 2, both exact.

## Corpus revision 2: seal (2026-10-31)

Built by a fresh reviewer session under decision revisions D1 and D2. It never read checker code, logs or outputs,
and it never read the real container. Revision 1 (`8603fb7`) and the scoring run 1 records are unchanged.

| Item | Value |
|---|---|
| Commit | `492b9a48d0ebe57bf54749e924844535c94b811f` (seal record in `3333c76`) |
| Tree | `8b800ba56415beaa8cd6bd16f510762bc3e6cd1b` |
| Files | 1802 |
| Digest | `62b4e3d3601ef6fed01acee6c12208d46fcd21391896a38678a5a7b0cb75cf34` |
| Decision revisions | D1 (`81398e6`), D2 (`a35841c`) |
| Checker it is to be scored against | `cd49069`, pinned before this seal (`CHECKER-PUBLICATION.md`) |

| Set | Rev 1 acceptance | Rev 1, now diagnostic only | Rev 2 acceptance (fresh) | Other |
|---|---|---|---|---|
| A0 | 28 | 0 | 0 | |
| E1 | 24 | 7 | 0 | |
| Containers | 92 | 2 | 8 | E1 parts of 2 cases diagnostic only |
| D2 synthetic | 0 | 0 | 9 | 1 ambiguous |
| Metrics | 0 | 25 | 23 | |
| Mutations (held until after the freeze) | | | | 34 |
| **Total (253)** | **144** | **34** | **40** | **35** |

- **Diagnostic only:**
  - every revision 1 case whose rule was decided after its run 1 outcome was visible (OQ1, OQ6, OQ12);
  - all 21 revision 1 metric cases, because the OQ5 provenance verdict is **not confirmed**. The records are
    consistent with independence but cannot show it. Fresh metric cases replace them.
- **D2 cases pending SPEC revision 3:** mismatches that need execution-surface fields wait for revision 3's admission.
  Until then they are unresolved comparability assumptions, and E2 cannot start.
- **OQ2:** the scan of the pinned upstream checkpoint found no block, in any of the 311 tensors, that reaches the
  reference encoder's undefined float-to-int8 conversion (`evidence/OQ2/`). E1 encoder cases in that domain are
  excluded from encoder-equivalence claims, recorded and not deleted.
