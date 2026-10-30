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
