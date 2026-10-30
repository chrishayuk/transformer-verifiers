# Hidden reviewer corpus: seal

A hash commitment to the independent reviewer's hidden cases, published without revealing them. The corpus lives in a
separate local repository, `~/chris-source/transformer-verifiers-reviewer`, which the checker session cannot read.

| Item | Value |
|---|---|
| Sealed on | 2026-10-30, after the reviewer's report and before any scoring |
| Commit | `8603fb7237851ea3a3a48a2630c6b3e2a9a51494` |
| Tree | `6177f6893ebf87e756c1842840e1718c255887b1` |
| Files | 1440 |
| Digest of `git ls-files` contents (SHA-256 of the sorted per-file SHA-256 list) | `f67ca509e475a79c8e3a87b4b37f116adf328f12221236d0a18992aa17641e91` |
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
