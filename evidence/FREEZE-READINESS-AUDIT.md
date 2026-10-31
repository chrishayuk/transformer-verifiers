# LARQL-VERIFY-001: freeze-readiness audit

**What this is:** evidence for the freeze review (PROTOCOL.md, "Freeze decision"), not approval. It records, gate by
gate, what exists in the repositories and what does not. It contains no verdict and no preferred outcome.

- **Prepared by:** the coordinating session, 2026-10-31.
- **Protocol state:** the review snapshot is the commit that adds this file.
- **Its scope is facts with their evidence paths.** Where a statement is the coordinating session's own reading
  rather than a recorded fact, it says so.

## Phase 1 checker validation (the evidence base)

| Item | Where |
|---|---|
| Decision revisions D1–D10 and their clarifications | PROTOCOL.md, `draft.json` `decision_revisions` |
| Checker audits and pins (runs 4–11; current pin `4bc93d3`) | `evidence/CHECKER-PUBLICATION.md`, `evidence/checker-run-*.log` |
| Hidden-corpus seals (revisions 1–7) and scoring runs 1–8, aggregates only | `evidence/REVIEWER-CORPUS-SEAL.md` |
| Checker isolation mechanism and re-tests (parts 1–10) | `evidence/ISOLATION.md`, `evidence/isolation-test-*.log` |
| D2 field assessment; AMB-022 mapping audit | `evidence/D2-FIELD-ASSESSMENT.md`, `evidence/AMB-022-MAPPING-AUDIT.md` |
| B3 container specification and its admission | `specs/vindex3-container/SPEC.md` (revision 4), `evidence/B3/` |
| OQ2 upstream scan | `evidence/OQ2/` |
| L1 baseline audit | `evidence/L1/` |
| B1 freeze-lock setup | `evidence/B1/SETUP.md`, `tools/freeze_verify.py`, `.github/workflows/freeze.yml` |
| Proposed T3 pilot amendment (not in force) | `evidence/proposals/T3-PILOT-AMENDMENT-DRAFT.md` |

**Latest scoring results, from the public aggregates:**

| Run | What it scored | Result |
|---|---|---|
| Run 7 | D2 comparability, checker `e232720` | 20/20 complete passes, 5/5 negative field checks |
| Run 8 | D6 and aggregates, checker `4bc93d3` | 125/125 tensors, 7/7 aggregation cases, 0 `checker_error` |

**Earlier failures are preserved:** the run 2 BF16 failures and the run 6 P3 failures, among others.

**Recorded limitations:**
- AMB-028, AMB-029 and AMB-030f;
- min/max/mean as the only scored distribution summaries (D10 clarification 2);
- reviewer questions 38 and the rest of 41, open, with no case depending on them.

## Gates

| Gate | State in the repositories | Evidence |
|---|---|---|
| **G1 freeze integrity** | **Built:** a verifier that takes its manifest and code from the immutable tag `freeze/<PROTOCOL>`, a CI workflow, and a server-side tag ruleset `freeze-tags` (no bypass, tested on a throwaway pattern). **Owner's choice:** `main` is unprotected and CODEOWNERS review is not required; the trust anchor is the tag. **Not done:** no `FREEZE.sha256` manifest for this protocol; no `freeze/LARQL-VERIFY-001` tag; the nine tamper tests have not been run against the real remote; no named human reviewer is recorded in `evidence/B1/SETUP.md`. **Remote:** 50 local commits not pushed (`origin/main` is at `89fb0c5`); the repository is public | `evidence/B1/SETUP.md` |
| **G2 independence** | **Roles** are documented. **Checker isolation** is enforced by settings, a sandbox and immutable protocol snapshots, re-tested at each snapshot change. **Reviewer and checker** are kept apart. **Isolation incident:** earlier checker clones sat in the reviewer workspace; the access log was reviewed and the clones moved out (part 10). **TRUST-BOUNDARY.md item 2** ("how to enforce isolation") is addressed by that mechanism. Whether it is accepted is the reviewer's judgement | `evidence/ISOLATION.md`, `larql/TRUST-BOUNDARY.md` |
| **G3 re-audit at the freeze SHA** | **L1 audit** at LARQL `2536bb79`, a clean worktree, with a headline finding: the LM head is silently re-quantised unless `LARQL_CPU_MAX_FORMAT=bf16`, which the Baseline now pins. **The freeze SHA is not yet named**, and PROTOCOL.md's remaining-work table lists L1 as Open. **CAPABILITIES.md** has not been re-checked as a whole at a named freeze SHA | `evidence/L1/AUDIT.md`, `evidence/L1/BASELINE.md`, `larql/CAPABILITIES.md` |
| **G4 numerical contract** | **Fixed:** subject, encoding, backend and environment (Baseline), T1–T4, the E1/E2/E3 definitions, and the D7 arithmetic assumptions. **The T3 pilot** form and ladder are in PROTOCOL.md. A proposed amendment covers the arithmetic profile, position coverage, saturation and the protected pilot record, with a single candidate checkpoint (Qwen3-1.7B, pinned revision) and the disjoint-subject-corpus fallback. **The amendment is not adopted** | PROTOCOL.md "Tolerance rules", "The pilot for T3"; `evidence/proposals/T3-PILOT-AMENDMENT-DRAFT.md` |
| **G5 corpora frozen** | **Built and sealed:** the hidden synthetic checker-validation corpora. **Not found:** an E2/E3 logit corpus with a sealed held-out part (A2 logit-match details) | `evidence/REVIEWER-CORPUS-SEAL.md` |
| **G6 mutation suite frozen** | **Hidden A4 recipes** exist in the reviewer repository (`mutations/RECIPES.json`, `RECIPES_D1.json`). **Not frozen** for Stage A | reviewer repository `mutations/` |
| **G7 Stage B domain** | Not written | n/a |
| **G8 acceptance review** | This review | n/a |
| **G9 split decision** | Not decided | n/a |

## Constraints still in force

- **The checker has not been run** on LARQL's Qwen3 container or on its logit dumps.
- **The T3 pilot has not been run.**
- **No Phase 1 measurement is Stage A evidence.**

## Corrections after freeze review 1 (2026-10-31)

Freeze review 1 (`evidence/freeze-review/REVIEW-1-8d2ca58.md`) returned **REVISE AND RE-REVIEW** on snapshot
`8d2ca58`. It found these statements in the audit above inaccurate or incomplete. They are kept as written and
corrected here:
- **Unpushed commits:** there were 52 at `8d2ca58`, not 50.
- **"Reviewer and checker are kept apart":** only the checker-to-reviewer direction is enforced, by mechanism.
- **"The access log was reviewed":** only for revision 7's author, and only for the clone folders.
- **TRUST-BOUNDARY item 2:** still listed as open there.
- **G1:** omits the approval-record requirement in `evidence/B1/SETUP.md`.
- **G4:** called "fixed" without noting:
  - the unpinned LARQL and ggml SHAs;
  - the SmolLM2-135M pilot text still in force;
  - T3's "Accelerate" rationale, which the L1 audit contradicts;
  - the undecided AMB-012 and AMB-014.
- **B3:** PROTOCOL.md and `draft.json` still show it as open or pending.
- **Isolation re-tests:** the later ones probe fewer paths, and they are the checker session's own reports.
- **The remote:** `evidence/B1/SETUP.md`'s table still says "Private remote".
