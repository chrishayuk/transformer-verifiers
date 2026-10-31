# LARQL-VERIFY-001 freeze review, snapshot 8d2ca58

**Scope.** Commit `8d2ca580c4a7295c6a4ebfd0c3295955a5c28348` of transformer-verifiers. HEAD was confirmed equal to it, with a clean tree. Also read: reviewer repo (HEAD `e5814e8`), checker repo (`checker/`, HEAD `4bc93d3`, clean) and LARQL `2536bb79` (clean). Everything was read only. No checker run, LARQL run, model run or network access.

## Verdict: **REVISE AND RE-REVIEW**

- **Why not READY.** None of G1–G4 is satisfied, and READY requires all four.
- **Why not BLOCKED.** I found no unfixable defect. Each gap below can be closed by a protocol edit, adopting a mechanism that has already been drafted, or a bounded piece of evidence work. The open core ambiguities (AMB-012, AMB-014) can be settled by an admitted source or an owner decision.

## Gates

| Gate | State | Evidence and reason |
|---|---|---|
| G1 freeze integrity | **Not satisfied** | `evidence/B1/SETUP.md` gives the B1 state: there is no `FREEZE.sha256`, no `freeze/LARQL-VERIFY-001` tag, and no named human reviewer. No tamper test has been run against the remote; the local self-test is explicitly not evidence. The approval record that SETUP.md itself makes a condition of B1 acceptance ("Open B1 acceptance issue") is not adopted. `PROTOCOL.md` B1 still requires a protected branch and required checks, which the owner chose not to use, and the text was never amended. `tools/freeze_verify.py` checks only this repository, but the checker, the corpora and the held-out part live elsewhere. |
| G2 independence | **Not satisfied** | Roles are documented (`PROTOCOL.md` "Roles and independence"). Checker-side isolation is built and plausible (`isolation/checker-settings.json` sha `b78f15d4…`, `evidence/ISOLATION.md`). But `larql/TRUST-BOUNDARY.md` items 1 and 2 are still listed as open and are not resolved or explicitly accepted, and the residual risks in ISOLATION.md are "not closed". Reviewer-to-checker separation is not enforced (focus area 4). Checker run briefs for runs 4–11 are not preserved. |
| G3 re-audit at freeze SHA | **Not satisfied** | No freeze SHA is named. Baseline in PROTOCOL.md and `draft.json` still says "pinned at freeze; audit at ff364ba6". `evidence/L1/AUDIT.md` re-checks 8 items at `2536bb79`, but `larql/CAPABILITIES.md` is still the `ff364ba6` audit and has not been re-checked row by row. Its line references have already drifted: L1 gives `verify.rs:23-33`, CAPABILITIES gives `:22-32`. The remaining-work table still lists L1 as Open. |
| G4 numerical contract | **Not satisfied** | Subject, encoding, backend, environment and T1/T2/T4 are fixed. Open items: 1) the T3 pilot text still names SmolLM2-135M (`PROTOCOL.md:244`, `draft.json:55`), and the amendment is not adopted; 2) the c/k ladder rule is ambiguous (see focus area 1); 3) T3's stated rationale ("LARQL's summation order (Accelerate)") contradicts the G3 evidence; 4) core ambiguities AMB-014 (LARQL logit-dump layout, no admissible source) and AMB-012 (container digest definition) are undecided; 5) the trusted-base table does not match what is actually trusted (focus area 2); 6) the LARQL SHA is not pinned, and ggml is still "recorded at freeze" although `facdc44a` is vendored. |
| G5 corpora frozen | **Not satisfied** | Synthetic checker-validation seals exist. I reproduced the rev 7 digest `850ed7a2…` from git objects: 2993 files, tree `633986d7…`. There is no E2/E3 logit corpus, no sealed held-out part, and no pilot corpus. |
| G6 mutation suite frozen | **Not satisfied** | Reviewer `mutations/RECIPES.json` (30 rows) and `RECIPES_D1.json` (6 rows) exist but are not frozen. There is no row for the A3 laws (S5, IP1–IP3), so by the protocol's own rule ("a guarantee with no row is not tested") those guarantees would be untested. |
| G7 Stage B domain | **Not satisfied** | Not written. |
| G8 acceptance review | **Not satisfied** | This review is the G8 exercise. It closes only with READY. |
| G9 split decision | **Not satisfied** | Not decided. |

## Minimum changes (numbered)

### G1
1. **Adopt the signed approval record already drafted** (`~/chris-source/transformer-verifiers-approvals-draft`):
   - the key is created and held by the owner, with its fingerprint recorded offline;
   - the verifier refuses a freeze tag with no approval binding protocol ID + commit SHA + **SHA-256 of `FREEZE.sha256`**. Binding the manifest hash, not only the commit's SHA-1, removes the dependence on git SHA-1.
   - Name the human reviewer in `evidence/B1/SETUP.md`.
2. **Amend PROTOCOL.md's B1 and G1 text to the model actually chosen:** tag plus signed approval, unprotected `main`, advisory CODEOWNERS and advisory CI. Add one operational rule: every Phase 3 run starts from a checkout that the tagged verifier reports VERIFIED, with a valid approval, and that output is stored in the run record. Correct SETUP.md's stale "Private remote" row.
3. **Make the manifest bind every frozen artefact outside this repo,** and check those bindings at Phase 3 run time:
   - checker commit and `requirements.lock` hash;
   - corpus seal digests, including a hash commitment to the held-out part;
   - A4 suite digest;
   - pilot corpus and pilot record digest;
   - LARQL SHA and container digest;
   - ggml `SHA256SUMS`.

   The pinned checker (`4bc93d3`, not pushed) and the seals exist only on the local machine. Publish them, or at least their hashes, somewhere timestamped off-host.
4. **Run tamper tests 1–10 on the real remote, as a non-admin token, before the review:**
   - Test 10 is "an unapproved or new `freeze/*` tag is rejected". Note that the ruleset as described blocks update and delete but not *creation*.
   - Use a rehearsal protocol ID and rehearsal approval under the same ruleset and verifier, so this does not wait for the real freeze.
   - Record commit hashes and verifier outputs.
5. **Name the agent or agents that will execute Phase 3,** and record that they run like the checker does: no `gh` token, no push rights, no network. SETUP.md states that any agent on this host can use the owner's admin login, and the coordinating session has used it to push.

### G2
6. **Update TRUST-BOUNDARY.md items 1–2 to resolved or accepted,** with the owner's written acceptance of each residual risk:
   - same OS user;
   - unsandboxed Claude process;
   - the protocol and SPEC §17 carry LARQL execution detail into the checker;
   - possible pretraining exposure of the checker model to the public LARQL source.
7. **Isolate the reviewer side by mechanism for every Stage A hidden artefact** (held-out logit corpus, A4 suite). The authoring session must not be able to read `transformer-verifiers/checker/` or `transformer-verifiers-eval/`, and scoring runs in a separate session. Alternatively, extend the log review to every read of checker source for every corpus revision cited as evidence. Revisions 2–6 are unreviewed today.
8. **Preserve each checker run's brief verbatim** as evidence (runs 4–11 are missing; the `checker-run-*.log` files are final summaries only), and have a party other than the coordinating session scan them for LARQL-derived content.

### G3
9. **Name the freeze LARQL SHA in Baseline** (PROTOCOL.md and draft.json). Re-check every row of CAPABILITIES.md at that SHA, with updated `path:line` references. Update the remaining-work table: L1, and B3, which is admitted at revision 4 but still listed as "Open" and "pending".

### G4
10. **Adopt the T3 amendment into PROTOCOL.md and draft.json,** replacing SmolLM2-135M, with these corrections:
    - **(a) An unambiguous ladder rule.** (c, k) pairs have no natural order: (4,64) and (8,4) can both be minimal. Declare the order, for example smallest c, then smallest k. Define the "one step up" margin when the minimal value is already the top rung (c=32 or k=64): either `not_determinable` or no margin.
    - **(b) Same conditions as the subject.** The pilot runs on the Baseline LARQL SHA, encoding and role policy, `production-q8`/`stored`, the `env -i` environment, the run-acceptance rule (FusedKQuant/FusedBf16 only) and the same host. Add a feasibility precondition that the candidate's head binding matches the subject's (explicit `lm_head` vs embedding reuse; L1 item 4).
    - **(c) The pilot corpus is frozen at the freeze.** It is content-hashed and in the manifest at the freeze, not merely "before it runs". It is built without access to the held-out part and declared disjoint from the E2 corpus at the token-sequence level.
    - **(d) Claim wording for both routes.** c and k are calibrated from LARQL-vs-reference behaviour, so any LARQL deviation shared by pilot and subject, up to the selected envelope, is absorbed. That means architecture-wide deviations for the 1.7B route, and subject-wide ones under the fallback. T3 detects only deviation beyond that envelope, and under the fallback, in effect only prompt-dependent deviation.
    - **(e) Correct "difference 5" and the T3 rationale.** Per `evidence/L1/AUDIT.md` item 2, Accelerate is not reached on the pinned path. LARQL's order is known: sequential f32, no FMA, for the Q8_0 GEMV, and 4×4-lane FMA for the BF16 head. The unknown order is torch's, on the reference side.
11. **Decide AMB-014 and AMB-012 in the protocol.**
    - AMB-014: the LARQL logit-dump layout and sidecar. The checker currently has no admissible source for it. Use a B3-style admitted, third-party-checked description, or protocol text.
    - AMB-012: the container digest definition.
12. **Make the trusted-base table match the real TCB** (focus area 2).
13. **Independently check the reference oracle.**
    - The reviewer, not the checker, derives selected reference logits: for example, an independent f64 (or mpmath) Qwen3 forward on tiny synthetic configurations, and a few positions on upstream weights, which Phase 1 allows.
    - Show that the checker's native ref64 agrees to near-f64 precision, and that ref32 equals stock transformers f32.
    - Record a review of `refcheck/f64_patch.py` (sha `9e696928…`) and the harness by someone other than their author.
14. **Freeze the Stage A output contract in the protocol:** field names, which distribution summaries are reported (min/max/mean per D10 clarification 2), and the quantile definition if quantiles are reported. Stage A scoring then needs no README-driven mapping.

### Before any Stage A run (G5–G9)
15. **Close G5–G9:**
    - E2/E3 corpus with a sealed held-out part, plus the pilot corpus;
    - freeze A4 with A3 rows added;
    - G7;
    - G9.

    State whether G5 and G6 must be closed before the freeze tag. They should be, since Anti-cheat makes the corpora and mutation suite manifest-protected.

## Findings by focus area

### 1. T3 pilot design
- **Differences 1–4: met on configuration.** Qwen3-1.7B as described has the same `head_dim` 128, θ 1e6, no scaling, eps 1e-6, QK norm and GQA 16/8. So RoPE angles, inverse frequencies, score scale and epsilon are identical to the subject's. I could not verify revision `70d244cc…` or its `config.json` offline (only lock files are in the HF cache). The values match my knowledge of the public config. **Minor:** verify them under the frozen procedure, as the amendment says.
- **Size difference: material for wording, acceptable in substance.**
  - The amendment cites only hidden size (2048 vs 1024). The MLP down projection contracts over `intermediate_size`, 6144 vs 3072, which it does not mention.
  - Longer sequential-f32 sums in LARQL, against blocked BLAS in torch, plausibly *raise* the selected c. That gives a looser and less sensitive T3 on the subject, not a safer one. "More conservative" should say so.
  - Acceptable if stated.
- **The rationale for difference 5 contradicts the G3 audit (Accelerate). Material,** because it is the stated reason for the form of T3 (change 10e).
- **Ladder rule ambiguity, two-dimensional order and top-rung margin. Material:** a preregistered rule must be deterministic (change 10a). The amendment's saturation rule covers only "nothing passes".
- **Self-calibration absorbs shared LARQL deviation. Material,** and not stated for either route (change 10d).
- **Separation from the held-out evaluation. Partly adequate.**
  - What the pilot may inspect is constrained.
  - Missing: the pilot corpus is not required to be frozen at the freeze, built without held-out access, or disjoint from the E2 corpus.
  - Missing: the pilot conditions (environment, run acceptance, head binding) are not tied to the subject's.
  - **Material** (changes 10b, 10c).
- **Fallback claim. Adequate as far as it goes** ("calibrated to this subject, not an externally validated bound"). It should add the detectability limit in change 10d. **Minor.**
- **Route choice at run time.** The route is fixed at freeze only as a conditional (feasibility failure falls back), and the label that applies must follow whichever route actually ran. **Minor.**

### 2. Exact trusted computing base
The TCB actually in use is wider than the trusted-base table in PROTOCOL.md. **Material**, because the table says "anything not listed is inadmissible".
- **(a) B3 SPEC revision 4 (`8f3f7c2b…`), including §17.** That section covers execution-surface meanings, the §17.5 rotation formula, and informative §17.8 LARQL arithmetic (an f32 score scale). The table still says "container framing only" and "(pending, B3)". D2/D7 authorise §17, but the table was not updated. The SPEC header still reads "DRAFT. Not admitted." **Minor cosmetic point;** changing it would change the hash.
- **(b) ggml `facdc44a`.** It is vendored, and its `SHA256SUMS` verifies, but the protocol still says "recorded at freeze". Provenance against upstream ggml could not be checked offline.
- **(c) Checker-authored oracle code:** the f64 patch, eight runtime pins, the 43-entry read-back map and the harness. These are trusted, and no independent check was found.
- **(d) Runtime:** CPython 3.12.11 (uv); the hash-locked transitive set (about 40 packages, including tokenizers and huggingface-hub); and torch's CPU BLAS and math library plus the host. ref32 is bit-reproducible only on one machine (AMB-016/023). Neither is pinned in Baseline.
- **(e) Reviewer tooling:** the exact-arithmetic helper library, generators and `score.py`. Trusted, and reviewed by no one else.
- **(f) Isolation and freeze layers:**
  - the Claude Code sandbox and permission layer;
  - the GitHub ruleset;
  - the owner's credentials;
  - the unadopted signing key;
  - git SHA-1.
- **(g) The coordinating session.** It audits and sometimes commits checker code (run 3), writes the briefs, and has read LARQL-derived material.
- **(h) No admitted source for LARQL's logit-dump format (AMB-014).**

### 3. Protected approval mechanism (B1/G1)
- **Tag anchoring is sound in principle.** The verifier takes its code and manifest from the tag, and CI runs the tagged copy. The verifier logic I read checks:
  - the manifest is not regenerated;
  - SHA-256 per listed file;
  - no symlinks;
  - no unlisted files under the roots;
  - the enforcement files are unchanged.

  It looked correct.
- **Material:** the verifier accepts *any* commit that `freeze/<P>` points at. Ruleset `freeze-tags`, as described, does not restrict creation. Any holder of the owner's token, which SETUP.md says every agent on the host can use, can create the tag first, and it then becomes immutable. The approval record that fixes this is drafted but not adopted (change 1).
- **Material:** PROTOCOL.md's B1 still demands branch protection and required checks. It must be amended or met (change 2). With `main` unprotected, CI is advisory, so the Phase 3 procedure must itself require a verifier pass (change 2).
- **Material:** the manifest cannot see the checker (a separate gitignored repo), the corpora or the held-out part (change 3). Tamper tests 1 and 8 (checker and its lockfile) are therefore not testable as built.
- **Not verifiable here:** the ruleset's existence and test, the repository being public, and the 51 unpushed commits. These are self-reports.

### 4. Independence of the numerical oracle
- **Checker isolation. Good, within same-user limits.**
  - Allow-list settings with no network and an immutable snapshot. The snapshot SHA256SUMS and the settings hash `b78f15d4…` match the records.
  - The re-tests (parts 4–9) probe a subset of paths. LARQL trees and network were last probed in part 3, and the logs are the checker session's own summaries. **Minor.**
- **Reference oracle has no independent check. Material.**
  - Every A0, E1, metric, D2 and D6 hidden case tests decode, reporting or comparability. None tests the forward pass that produces ref32 and ref64.
  - ref64's faithfulness rests entirely on checker-written `f64_patch.py`. On reading it, it does replace the three f32 islands (RMSNorm, eager softmax, RoPE) and rebuilds inv_freq in f64.
  - The "1.2e-15" figure is the checker's own.
  - TRUST-BOUNDARY recommends two references (change 13).
- **Reviewer-to-checker separation is not enforced. Material.**
  - The reviewer has no sandbox.
  - The live checker source is readable at `transformer-verifiers/checker/`, and scoring runs use its `.venv`.
  - Part 10 moved the clones to `transformer-verifiers-eval/`, which is equally readable.
  - The access check covers only the revision 7 author's 38 calls, and only the clone folders.
  - Revisions 2–6, which include revision 6, the basis of D10's "D2 feature-complete" claim, rest on declarations (change 7).
- **Briefs not preserved. Material for provenance.** Run briefs are inputs from a LARQL-aware session and are not preserved (change 8).
- **Seals reproduce,** but they are local, unpushed commitments. Their ordering against scoring rests on local commit order alone: run 8's seal, rules, field map and results span 21:51–21:59. **Minor** for Phase 1, **material** for G5 (change 3).

### 5. Scoring-rule independence (run 8, D10 clarification 2)
- **The N5 class 3 change mattered to the outcome but is sound. Minor.**
  - Under the draft (`scoring/next/RULES-REV7.md:63` together with "a required quantity that cannot be mapped fails"), all 70 Q8_0 tensors would have failed N5, because the README documents no class 3 count (`fieldmap.json` `class3_blocks: null`).
  - The relaxation was made after reading the README, and was disclosed.
  - It is justified by the text: D1 OQ1 requires class 2 counts by scale class, the T2 exceed count and the ±0-scale count, not a class 3 block count.
  - Partition completeness is still checked at element level: `n_within_t2` is mapped and scored exactly (`score.py:165`), alongside exceed and the class 2 elements.
- **The quantile point was not a change. Minor inaccuracy.** The draft already said a summary without a stated definition "is recorded, not scored" (`RULES-REV7.md:46-48`). D10 clarification 2's "two changes" overstates it.
- **Retroactive narrowing. Minor for Phase 1.** D10 clarification 2 narrowed question 40 to min/max/mean *after* run 8, because the checker's quantiles are undefined. It is labelled a limitation and cannot affect Stage A evidence.
- **Recurring pattern. Material for Stage A unless addressed.** Across runs 2–8, mappings and normalisations were fitted to the checker's published names, signatures and probe output after rules were drafted (for example run 6's `key_path` token normalisations). Each was disclosed and preceded scoring. For Stage A, the output contract should be frozen in the protocol so that nothing is fitted after the pin (change 14).

## Inaccurate or incomplete claims in `evidence/FREEZE-READINESS-AUDIT.md`
1. **"50 local commits not pushed".** Against the local `origin/main` ref (`89fb0c5`) there were 51 before the audit commit, and there are 52 at `8d2ca58`. Remote state is unverifiable offline.
2. **G2 "Reviewer and checker are kept apart".** Only checker-to-reviewer is enforced. The reviewer reads and runs the live checker and has no sandbox.
3. **G2 "the access log was reviewed".** Only the revision 7 author's log was reviewed, and only for the clone folders. The audit does not say that revisions 2–6 are unreviewed.
4. **G2 "TRUST-BOUNDARY item 2 is addressed by that mechanism".** TRUST-BOUNDARY.md still lists items 1 and 2 as open, and ISOLATION.md says its residual risks are "not closed".
5. **G1 omits the approval-record requirement.** SETUP.md itself makes it a condition of B1 acceptance, and it is not built or adopted. The audit also does not mention that the protocol's B1 text still requires branch protection.
6. **G4 "Fixed: subject, encoding, backend and environment".** True as far as it goes. The audit omits that the Baseline LARQL SHA and ggml commit are unpinned, that PROTOCOL.md's pilot text still names SmolLM2-135M, that T3's "Accelerate" rationale contradicts L1, and that core AMB-012 and AMB-014 are open.
7. **B3 listed as admitted (revision 4).** That is correct, but the audit does not note that PROTOCOL.md (remaining-work table, trusted base) and draft.json still say B3 is "Open"/"pending", nor that the admitted SPEC's header says "Not admitted".
8. **"Re-tested at each snapshot change".** The re-tests after part 3 cover a reduced probe set and are self-summaries by the checker session.
9. **Ruleset test and "the repository is public".** Both are reported as fact but cannot be checked here, and SETUP.md's own table still says "Private remote".
