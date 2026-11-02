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

## Scoring run 3 (2026-10-31): partial, metric cases only, aggregates only

- **Checker:** `cd49069`, as D4 requires. Not modified.
- **Corpus:** `492b9a4`. **Decision revisions:** D1, D3, D4.
- **Order of commits:** the D4 tolerance confirmation (`abf8ab7`), then the eligibility list and rules (`32dfd31`),
  then the run (`21adaab`). One pass.

| Eligible | Pass | Fail | Error |
|---|---|---|---|
| 18 | 18 | 0 | 0 |

- **Tolerance confirmation:** the D4 values are confirmed for 18 of the 23 revision 2 metric cases. The other 5 have
  logits with |z| > 128, outside the a priori analysis. They stay pending and unexposed.
- **Observed margins:** KL errors are at most 2.3e-16, against tolerances of at least 2e-10. max |Δ| and top-1 are
  exact. All 12 `non_comparable` positions are reported correctly.
- **Not tested:** the aggregate rule (non-comparable positions left out of every aggregate). The checker exposes no
  aggregate function under the names fixed in advance.
- **Provenance note:** run 1 had already computed checker metric output on the 21 revision 1 metric cases, which are
  diagnostic. No output existed for any revision 2 metric case before this run.
- **Exposure:** these 18 cases are now exposed. A later checker revision needs fresh cases for these rules.

## Corpus revision 3: seal (2026-10-31)

| Item | Value |
|---|---|
| Commit | `11a89c8049c635516f8d5d9080b96249a7914070` (seal record in `1b5d554`) |
| Tree | `9d48679e64a41d0feac94de9e2bfe5267f5cb8ec` |
| Files | 1961 |
| Digest | `4bed58197a446242b70274bdfca1f733f33e2b625a36c5edc30ff74fce0fdc84`, reproduced by the coordinating session |
| Purpose | 4 fresh D4 containers: bit-identical BF16, BF16 with known differences, zero reference norms, and a mix with fresh D1 OQ1 blocks. Run 2's five exposed failures are diagnostic only for D4 |
| Checker to be scored against | `3337645`, pinned before this seal |

Not yet scored. Reviewer open question 22 must be decided first: whether A1 statistics are computed in binary64,
which revision 3's 1e-11 Frobenius tolerance assumes.

## Scoring run 4 (2026-10-31): corpus revision 3, aggregates only

- **Checker:** `3337645` (D4 A1), pinned before revision 3 was sealed. Not modified.
- **Corpus:** `11a89c8`. **Decision revisions:** D1, D3, D4, D6.
- **Order of commits:** the D6 A1 precision confirmation (`ccba011`), then the eligibility list and rules
  (`73d55da`), then the run (`8f81de3`). One pass.

| Eligible | Pass | Fail | Error | Excluded |
|---|---|---|---|---|
| 4 | 4 | 0 | 0 | 0 |

- **Result:** the BF16 reporting gap behind run 2's five failures is closed, shown on fresh blind cases:
  - every tensor's counts are exact;
  - max abs error is exact, or within 1 ulp where it is not an f64 value;
  - relative Frobenius error is within 1.6e-16;
  - all 7 zero-norm tensors report `null` with the flag, and the predicted absolute Frobenius error.
- **Run 2 is unchanged:** its five failures stay recorded as failures.
- **Field name:** checker `3337645` publishes the absolute Frobenius error as `err_frobenius`, not D6's
  `absolute_frobenius_error`, so the scorer mapped it by name, as D6 allows.

## Corpus revision 4 (in preparation, not sealed)

33 fresh hidden D2 comparability cases under D7 and SPEC revision 4 §17, each with a reviewer-written stand-in
authority and its provenance. They are built and not sealed. The seal follows the pin of the D7 checker.

## Corpus revision 4: seal (2026-10-31)

| Item | Value |
|---|---|
| Commit | `acbc9320b3da79175f998f2bdc98d57e3a8bfc80` (seal record in `7a18a71`) |
| Tree | `8537fce73f81d1640db719a70312ca2052474a9f` |
| Files | 2371 |
| Digest | `e68a35e6e6f8b72ffcdb270c00616b97dfc5ed099096951e9fc92781e5f1915c`, reproduced by the coordinating session |
| Content | 33 fresh D2 comparability cases (3 comparable, 27 mismatch, 3 unresolved), each with a reviewer-written stand-in authority |
| Checker | `ab38748`, pinned before this seal |

**Expectations re-derived under D8 before the seal,** with no checker output seen. The formerly ambiguous score-scale
case is now `invalid_comparison`: its container stores the square-root-route value, one ulp below the correctly
rounded `1/√32`.

## Scoring run 5 (2026-10-31): corpus revision 4, aggregates only

- **Checker:** `ab38748`. **Corpus:** `acbc932`. **Decision revisions:** D2, D3, D7, D8.
- **Order of commits:** the eligibility list and rules (`1e55631`), then the field mapping and adapter (`3cd8bc0`),
  then the run (`c093210`). One pass.

| Eligible | Status correct | Pass (mechanical) | Pass (after the preregistered hand review) | Fail | Error |
|---|---|---|---|---|---|
| 33 | **33** | 23 | 27 | 6 | 0 |

- **Verdicts:** the comparator gave the right `comparable` or `invalid_comparison` verdict on all 33 fresh blind cases.
- **Hand review:** applied after the run, from recorded outputs only, under a RULES clause fixed before the run
  (reported entries that duplicate an expected field's site). Both tallies are kept.
- **The six failures** show no checker defect:
  - **one case defect:** an extra key the checker rightly reported as unresolved;
  - **one scorer defect:** alias matching over path text;
  - **one ambiguity:** a non-null authority `rope_scaling`, unresolved or mismatch;
  - **three interface ambiguities:** must-be-absent mismatches do not name the offending key in a documented field.
- **The failures stand.** These cases are now exposed. Fresh cases and a fixed scoring adapter are needed for any
  re-test.
- **This is Phase 1 information, not Stage A evidence.**

## Corpus revision 5: seal (2026-10-31)

| Item | Value |
|---|---|
| Commit | `d28c344b766c9a7ab0f3d7ec4e78b17c49255896` (seal record in `bbc84af`) |
| Tree | `5d9ea859ce283463e7968751de00b34ccfe066dc` |
| Files | 2674 |
| Digest | `cc888ba1496c2720accbde4de96ad59b337a4a452f94744398fe14fee766191b`, reproduced by the coordinating session |
| Content | 24 fresh D9 cases: unsupported (7), unresolved (5), key identity (6), contradiction (2), controls (4), each with a stand-in authority. Status, category, field and key path are expected as separate properties |
| Checker | `147a24e`, pinned before this seal |

**Expectations re-derived under D9 clarification 2 before the seal,** with no checker output seen. The geometry-absent
case is now `comparable` (the question 27 fallback), and some derived fields are now optional.

## Scoring run 6 (2026-10-31): corpus revision 5, aggregates only

- **Checker:** `147a24e`. **Corpus:** `d28c344`. **Decision revisions:** D9 with clarifications 1 and 2.
- **Order of commits:** the eligibility list, rules and adapter (`13e2275`), then the field mapping (`a8b3e10`), then the
  run (`9f5f58d`). One pass. The structured adapter reads `category`, `field` and `key_path` only, which fixes the run 5
  path-text defect.

| P1 status | P2 category | P3 field identity | P4 key path | Complete passes | Tolerated | checker_error |
|---|---|---|---|---|---|---|
| 23/23 | 23/23 | 19/23 | 6/6 key-identity cases (9 paths) | **19/23** | 0 | 0 |

- **Excluded, pending:** 1. The geometry-absent case depends on clarification 2's question 27 fallback, which
  postdates the checker's snapshot.
- **The four failures are all on P3** and show no checker defect. Each comes from the reviewer's preregistered aliases
  or optional-field lists:
  - in three cases, the checker's field spelling `attention.score_scale` against the alias `score_scale`;
  - in one of those, an unlisted derived reason (`shapes.inventory`);
  - in the fourth, unlisted derived reasons (`rope_pairing`, `rope_rotation_direction`) on a RoPE kind mismatch.

  The mechanical result stands.
- **Right reason as well as right status:** the cases built for this purpose (for example a non-null `rope_scaling`
  meaning no scaling, a disabled window with everything else matching, a scale override with the same value) were
  refused for the expected reason and category.
- **This is Phase 1 information, not Stage A evidence.**

## Corpus revision 6: seal (2026-10-31)

| Item | Value |
|---|---|
| Commit | `093dcc9a83183b53e62b9c72d9fd8422f192931e` (seal record in `55b1259`) |
| Tree | `4a550d5c1f9ce6e74f1cdcc9ef3d8560c3bc5f5a` |
| Files | 2924 |
| Digest | `a417b304e2c3e7fc9e0836112d6f85ca77a66ffc6658d5abe2a190108cacd176`, reproduced by the coordinating session |
| Content | 20 fresh cases preregistered against reason-field schema v1.1 (the protocol table, not checker output): replacements for run 6's exposed field-identity classes, the question 27 geometry cases, 5 negative field-identity checks, and controls. 16 `invalid_comparison`, 4 `comparable` |
| Checker | `e232720`, pinned before this seal |

## Scoring run 7 (2026-10-31): corpus revision 6, aggregates only

- **Checker:** `e232720`. **Corpus:** `093dcc9`. **Decision revisions:** D9 with clarifications 1–4.
- **Rules:** fields matched exactly and case-sensitively; categories for derived findings preregistered per case.
- **Order of commits:** rules and adapter (`5df9386`), then the field mapping (`56f3953`), then the run (`d40fc29`). One
  pass.

| P1 status | P2 category | P3 field identity | P4 key path | Complete passes | Negative field checks | Tolerated | checker_error |
|---|---|---|---|---|---|---|---|
| 20/20 | 20/20 | 20/20 | 4/4 (16 n/a) | **20/20** | 5/5 | 0 | 0 |

- **Every case passed every property,** including the five cases where a non-permitted extra field was the tempting
  wrong answer.
- **Question 27:** the fallback behaved as expected in all four of its cases.
- **Exclusions:** none.
- **This is Phase 1 information, not Stage A evidence.**

## Corpus revision 7: seal (2026-10-31)

| Item | Value |
|---|---|
| Commit | `71198d678223475e70bbc46cd0f14a69a63976a9` (seal record in `0caf4f1`) |
| Tree | `633986d778fe32e97369d55354d63107ade2400f` |
| Files | 2993 |
| Digest | `850ed7a268d6244cbab5bdc655e7c8340d29c3f41ec174a0c21914885d5504ba`, reproduced by the coordinating session from the git objects |
| Content | Fresh cases for D6 and the metric aggregate contract, with expectations derived from the protocol under D10 clarification 1, never from checker output. The D6 cases are 5 synthetic containers holding 125 tensors: 11 with non-finite upstream values, 5 finite-upstream tensors whose decoded values are non-finite, and 109 finite controls. The aggregation cases are 7, with 42 positions, 25 of them comparable: a mixture, an entirely non-comparable sequence, two rate-flip traps, edge positions, a measured-zero-error case paired with the empty set, and an all-comparable control. Q8_0 bit identity is unscored, and non-finite block distributions are diagnostic only |
| Checker | `4bc93d3`, pinned before this seal |
| Isolation | The corpus author worked with no checker clone in its workspace once the clones were moved out (isolation part 10). Its access declaration and the tool-log review are recorded there |

## Scoring run 8 (2026-10-31): corpus revision 7, aggregates only

- **Checker:** `4bc93d3`, a clean clone in the separate evaluation directory
  (`~/chris-source/transformer-verifiers-eval/run-8/`). **Corpus:** `71198d6`, unchanged since the seal. **Decision
  revisions:** D10 with clarification 1.
- **Order of commits:** eligibility, rules and adapter (`3ccc013`), then the field mapping from the checker README
  (`39eff8f`), then the run (`e5814e8`). One pass. The scorer read only the README and the entry-point signatures.
- **Tallies:** recounted by the coordinating session from `RESULTS.json`.

**D6, 125 tensors** (11 with non-finite upstream values, 5 finite-upstream tensors with non-finite decodes, 109
finite controls)

| N1 status | N2 null metrics and reasons | N3 class counts | N4 BF16 bit identity | N5 Q8_0 inventory | N6 finite statistics | N7 non-finite decode | Complete |
|---|---|---|---|---|---|---|---|
| 125/125 | 11/11 | 125/125 | 55/55 | 70/70 | 109/109 | 5/5 | **125/125 tensors, 5/5 cases** |

**Aggregation, 7 cases** (42 positions, 25 comparable)

| Counts and indices | Non-comparable handling | Top-1 rate (comparable denominator) | Distribution coverage | Empty set against measured zero | Complete |
|---|---|---|---|---|---|
| 7/7 | 5/5, both rate-flip traps (2 n/a) | 6/6 (1 n/a, the empty case) | 6/6 (1 n/a) | 7/7 | **7/7** |

- **No `checker_error`, no exception, no exclusion.**
- **Unscored, as preregistered:** Q8_0 bit identity on the 4 tensors with non-finite upstream values, and the
  diagnostic block distributions of those tensors (D10 clarification 1).
- **Two rule changes from the draft.** They were made after the scorer read the published README, frozen in
  `3ccc013` before any case ran, and disclosed in its `RULES.md`. Both narrow what is scored:
  - **The Q8_0 class 3 block count:** scored only if documented, because no protocol clause requires it. It is not
    documented.
  - **Distribution quantiles:** not scored, because the README does not define them. Minimum, maximum and mean are
    scored.

## E2/E3 logit corpus: pilot and held-out seals (2026-10-31; admitted with recorded limitations, see below)

Built by an independent corpus author in the reviewer repository (`e2corpus/`). No model, LARQL or checker was run.
The coordinating session has not read the held-out contents.

| Set | Commit | Scope | Files | Digest |
|---|---|---|---|---|
| Pilot (declared) | `9facacb655d079cb03cf11905735f1d774409c72` (seal record `5673ba1`) | `e2corpus/pilot/` | 49 | `342f3978f587f0266aed618e1da24a030d8a5d1177ada822ab67bc853016143a` |
| Held-out (sealed) | same commit | `e2corpus/heldout/`, salt included | 50 | `0f74bb760407953fbb0710bb355bf2c0aa252123d1a058009e6331422b4af3ce` |

- **Digests:** both reproduced by the coordinating session from the git objects. The method is the usual one, with
  paths scoped to each directory.
- **Shape:**
  - 23 sequences and 130,543 tokens per set;
  - bands 0–511, 512–4095, 4096–32767 and 32768–40959;
  - 9,536 pilot and 9,534 held-out evaluated positions;
  - maximum position 40,959 (proposed; open question 45).
- **Disjointness, as reported by the author:**
  - 0 shared documents;
  - the longest common run is 22 tokens, under the preregistered bound of 32;
  - 0.07% of held-out 13-grams are also in the pilot, under a bound of 1%.
- **Isolation:** built under written rules, not a sandbox. Its tool log (38 calls) shows no access to the checker,
  its clones, the freeze review, the reference audit, LARQL or the network.
- **Admission:** under proposed D11 §10, admitting it or rebuilding it under a mechanism is the owner's decision.
- **Open questions:** 43–50 in the reviewer repository. They cover:
  - tokenization and BOS;
  - Qwen3-1.7B reuse;
  - the 40,959 maximum;
  - evaluated positions against "every pilot logit";
  - the bands;
  - the held-out handover;
  - natural-text contamination for E3;
  - licences.

### E2/E3 corpus admission (2026-10-31)

- **Who checked it:** an independent admission reviewer, not the corpus author. It read nothing under `checker/`
  beyond the venv interpreter, and ran no model or LARQL. The coordinating session checked its tool log (32 calls):
  clean.
- **How it checked:**
  - with its own verifier, on the git objects;
  - by a byte-exact rebuild of all 98 generated files from re-extracted pools and the sealed salt;
  - by its own reproduction of the keyed order and the positions;
  - by a direct reading of the author's tool log.
- **Its recommendation:** **ADMIT WITH RECORDED LIMITATIONS.** The report is `e2corpus/ADMISSION-REVIEW.md`, at
  reviewer repository commit `4db9ab2`.
- **The result:** under the owner's ruling of 2026-10-31 ("if these pass, admit the existing corpus by its exact
  hashes"), the corpus is **admitted by the exact digests above**: pilot `342f3978…`, held-out `0f74bb76…`.
- **All 8 checks passed:**
  - the seals;
  - the 46 sequences: they round-trip, carry no special tokens, and keep no BOS or EOS even with `add_special_tokens`;
  - the tokenizer hashes;
  - provenance;
  - disjointness: 0 shared documents, the longest common run 22 against a bound under 32, 13-gram overlap 0.0721%
    against a bound of 1%;
  - positions: 9,420 native and 114 extended in the held-out set, 9,423 and 113 in the pilot;
  - exposure;
  - conformity with the owner's rulings.
- **The recorded limitations, all minor:**
  - **F1:** the disjointness bounds were fixed during construction, which only the tool log shows.
  - **F2:** the held-out set was built three times with the same salt, after a structural fix seen only through
    manifest metadata.
  - **F3:** TinyStories is GPT-generated text, a caveat for E3.
  - **F4:** `DESIGN.md`'s isolation statement leaves out reads of the reviewer README and open questions, git log
    subjects, and a listing of `scoring/`.
  - **F5:** the checker venv could not be inspected for start-up hooks.
  - **F6:** synthetic documents are checked by rerunning their generator, not by a second implementation.
  - **F7:** `DESIGN.md` and `SEAL.md` describe questions as open that are now ruled on. Both files are outside the seals.
  - **F8:** the licence record has gaps: the WikiText version, share-alike terms, and the model licence.
  - **F9:** the code pool depends on the local CPython install, so `code.jsonl` should be archived with the freeze
    materials.
- **Still to do before the freeze:**
  - write the BOS policy out in words;
  - define the handover procedure (question 48);
  - complete the licence record.

## Corpus revision 8: seal (2026-11-01)

| Item | Value |
|---|---|
| Commit | `6403c82a78e3ade9c22b3d5deb1b018b28416940` (seal record in `4726e49`) |
| Tree | `908b3283ce09c2b8e521af1ed969ef508781d2b7` |
| Files | 3286 |
| Digest | `28af030c32a451a5ad118490dea42672ed52b3e1bd94b214d28043df86995ff6`, reproduced by the coordinating session from the git objects |
| Content | 43 fresh T3 cases: 9 verdict, 5 aggregate, 5 non-finite and representability, 1 selective-evaluation, 23 refusal. Expectations were derived from D12 and its clarifications 1–2, decided exactly with rationals, and cross-checked by a second route (1,455 logits, 0 mismatches). Outcomes are matched by documented meaning, never by literal label |
| Checker | `80608c3`, pinned before this seal |

## Scoring run 9 (2026-11-01): corpus revision 8 against checker 80608c3, aggregates only

- **Inputs:**
  - checker `80608c3`, a clean clone in the separate evaluation directory (`~/chris-source/transformer-verifiers-eval/run-9/`);
  - corpus `6403c82`, unchanged since the seal;
  - decision revision D12 with clarifications 1–3.
- **Order of commits:** eligibility, frozen rules and an adapter with a synthetic self-test (`779e08d`), then the
  README-derived field and outcome mapping (`d544446`), then the run (`0f578ee`). One pass, no rerun. The scorer read
  only the checker README and the `evaluate_t3` signature and docstring.
- **Tallies:** recounted by the coordinating session from `RESULTS.json`. All match.

| Tally | Result |
|---|---|
| Per-logit verdicts | 1455/1455 |
| — exactly on the boundary | 63/63 |
| — one binary32 step either side or off-grid | 129/129 |
| — logits where naive binary64 evaluation gives the wrong verdict | 6/6 (decided `fail`, correctly) |
| — c branch / k branch / tie | 109/109, 1334/1334, 12/12 |
| Counts | 20/20 evaluated cases |
| Non-comparable handling, including representability | 5/5 cases |
| Representability | ±FLT_MAX comparable; ±(FLT_MAX + 2⁷⁵) and other out-of-range values non-comparable (`ref64_above_binary32_range`), never a T3 failure |
| Empty comparable set, overall / empty band and class groups | 1/1, 72/72 |
| `incomplete`, overall / `fail` with incomplete coverage reported | 3/3, 1/1 |
| Refusals before any verdict (verdict null, no summary), reason present, preregistered condition code | 23/23 each |
| Band summaries / class summaries (native and extended separately) | 20/20, 20/20 |
| Overall outcome | 20/20 (`pass` 3, `fail` 13, `incomplete` 3, `empty_comparable_set` 1; 23 refused) |
| Selective evaluation (failing and non-finite values in non-evaluated rows ignored, including 40,960-row arrays) | 20/20 |
| **Complete-case pass** | **43/43** (verdict 9, aggregate 5, non-finite 5, selective 1, refusal 23) |
| `checker_error` / exclusions | 0 / none |

- **Rule specifics disclosed in the frozen rules** (made after reading the README, before the run):
  - **Records:** abstract records were translated into real harness records, run on synthetic non-corpus containers,
    with the sealed arrays substituted for their logits.
  - **Properties the harness cannot produce:** set in their documented record fields. One substitution: a native-f64
    record stands in for a bfloat16 ref₃₂. So those refusal cases show that the checker reads the documented fields.
    They do not show how it behaves on genuinely produced runs of those kinds.
  - **Refusal codes:** matched against a preregistered acceptable set.
  - **Per-logit verdicts:** derived from the documented failing-token list. No position exceeds that list's limit of 20.
- **Extra refusal codes:** four refusal cases also gave a second code, each following from a documented check. They
  were recorded and not scored.
- **Not exercised:** the f64 guard (audit m3), which is tested in the checker suite only (reviewer question 57).
- **Still open:** reviewer questions 52–56 and part of 58. No case depends on them.
- **The scorer's report:** the harness refused its own write. It was transcribed verbatim into the reviewer
  repository, `scoring/run-9/REPORT.md`.
- **What this is:** synthetic checker-correctness evidence for the T3 decision procedure. It is not Stage A evidence,
  and no LARQL logits were involved.

## Corpus revision 9: seal (2026-11-02)

| Item | Value |
|---|---|
| Commit | `3019654a4352d506b44c51cb17c4e16ba90f390e` (seal record in `4399a85`) |
| Tree | `c54f6aa302639c78e0861881b5bd48091028c72f` |
| Files | 3308 |
| Digest | `d4721b894e8787d751171becd90dda529864ebc4dbf0435baf0c1f7528aa316f`, reproduced by the coordinating session from the git objects |
| Content | 79 Phase 3 ingestion cases (13 accepted, 66 refused, 28 extracted rows). They include the 13 `d15_c1` representation-line cases: 4 accepted controls with the real suffix and other suffix forms, and 9 refusals. The substitution-resistance set has 14 cases. None of the 66 earlier expectations changed |
| Applies | Baseline, D12 with clarifications 1–3, D13, the D14 readings Q59–Q70, D15 clarification 1, admitted SPEC revision 3 |
| Reading-flagged | `ing9_r_out_of_order` (reviewer question 71, order), `ing9_r_suffix_trailing_space` (question 73, what "a space" admits). Both follow the fail-closed or literal reading and are reported separately |
| Independence | The reviewer's tool log was checked by the coordinating session: 27 + 6 calls, reading only snapshot `8b3663a` and the reviewer repository. It never read the checker, `dev/`, LARQL, the evaluation directory or the evidence logs |
| Checker | `e505afc`, pinned before this seal (D15 clarification 1 replaces `c2070c3`) |

## Scoring run 10 (2026-11-02): corpus revision 9 against checker e505afc, aggregates only

- **Inputs:** checker `e505afc`, a clean clone in `~/chris-source/transformer-verifiers-eval/run-10/`; corpus `3019654`,
  unchanged since the seal; D12 with clarifications 1–3, D13, the D14 readings and D15 clarification 1. The scorer's
  tool log was checked by the coordinating session: 50 calls, no checker source or tests, no `dev/`, no LARQL.
- **Order of commits:** eligibility, rules and adapter with a synthetic self-test (`6be96c1`), then the mapping and
  probe (`d59429a`), then the run (`f5b94f9`). One pass. Tallies were recounted from `RESULTS.json`; all match.

| Tally | Result |
|---|---|
| Refused cases, complete | **66/66**: rejection before extraction 66/66, reason 66/66, substitution resistance 14/14, `d15_c1` refusals 9/9, SHOULD-only cases from before D14 4/4 |
| Accepted controls | **0/13, not measured.** The scorer's adapter raised after `verify_and_extract` returned (a numpy array tested against a tuple), so no status or rows were captured. They are recorded as failing, as the rules require |
| `checker_error` / exclusions | 0 / none |

- **What this shows:** that the corrected checker refuses all 66 refusal cases with the right reasons, including the
  9 that clarification 1 must still refuse. It does **not** yet show that the checker accepts the real line form
  (`ing9_r_suffix_*`) or the 9 earlier controls. That half needs a separate scoring run, by the owner's decision.
- **Deviations** (disclosed in the run's `RULES.md`): the probe was run twice on non-corpus data, and the container
  identity, the token-digest width and two H-mode translations were derived through documented interfaces.
- **What this is:** synthetic checker-correctness evidence. Acceptance would mean `content_valid` only. No LARQL was
  involved.
