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

## Scoring run 2 (2026-10-31): partial, aggregates only

The full results are in the reviewer repository (`scoring/run-2/`). They stay sealed from the checker.

- **Checker:** `cd49069`, pinned before corpus revision 2 was sealed. Not modified.
- **Corpus:** `492b9a4`, unchanged.
- **Decision revisions:** D1 and D2. The partial-scoring rules of D3 were followed.
- **Order of commits:** the eligibility list and the pass/fail rules first (`f9226a3`), then the metric error
  analysis (`0fb4d6a`), then the run (`83162f3`). One pass; nothing was rerun.

| | Eligible | Pass | Fail | Error |
|---|---|---|---|---|
| A0 | 28 | 28 | 0 | 0 |
| E1 | 24 | 24 | 0 | 0 |
| Containers | 87 | 82 | 5 | 0 |
| **Total** | **139** | **134** | **5** | **0** |

- **Excluded (pending, not passed): 114.**
  - 48 metric cases (pending the tolerance decision; 25 of them also diagnostic only)
  - 34 held real-container recipes
  - 13 ambiguous containers
  - 10 D2 synthetic cases
  - 9 diagnostic-only cases
  - None depend on AMB-018 or AMB-019.
- **The five failures share one cause:** the reviewer's rule required error statistics (maximum absolute error,
  relative Frobenius) for BF16 tensors as well. The checker reports BF16 tensors by bit-equality only. Every other
  predicted quantity matched exactly, including the D1 OQ1 class counts.
  - **Diagnosis:** an ambiguity in A1. It is unsettled whether A1's error statistics apply to unquantised tensors,
    whose T1 check is bit-exactness. It is not a numerical checker defect.
  - **The failures stand.** Once the rule is decided, these cases need fresh replacements before they count, because
    the decision comes after this result was seen.
- **Metric error analysis:**
  - max |Δ| and top-1: the D1 tolerances are justified.
  - KL (absolute part) and RMS Δ: too tight unless the protocol requires pairwise or compensated summation. Under a
    free summation order, the worst-case bounds are about 1e-10 (KL) and 8.5e-12 relative (RMS Δ).
- **This is Phase 1 information, not Stage A evidence.**
