# Proposed decision revision D11: readiness revision after freeze review 1 (draft, not in force)

**Status: PROPOSED.** The owner approved its stated direction on 2026-10-31, including the top-rung saturation rule,
"subject to checking the actual draft". It is still pending line-by-line review, and is not in force.
- **Approval:** for the protocol owner to approve, change or reject, item by item.
- **Effect:** nothing here is in force until it is appended to PROTOCOL.md.
- **Next review:** the next freeze review is held on a new immutable snapshot, after the owner-held items (below) also
  exist.
- **Prepared by:** the coordinating session, 2026-10-31.
- **Responds to:** freeze review 1 (`evidence/freeze-review/REVIEW-1-8d2ca58.md`, verdict REVISE AND RE-REVIEW on
  `8d2ca58`) and the owner's instruction of 2026-10-31.
- **Preserved:** snapshot `8d2ca58`, the review, D1–D10, every seal and every scoring run.

**Not in this draft, because it belongs to independent workstreams now running:**
- the reference-forward audit;
- the E2/E3 corpus;
- the owner-held items listed at the end.

---

## 1. B1/G1: the tag-and-approval model (review changes 1–4)

This replaces the B1 requirement that the protected *branch* be the boundary. That requirement was not adopted: on
2026-10-30 the freeze owner chose a public repository with an unprotected `main`
(`evidence/B1/SETUP.md`). The text below makes the protocol match the mechanism actually chosen, and closes the gaps
review 1 found.

- **The trust anchor is the immutable tag `freeze/LARQL-VERIFY-001`, plus a signed approval record.** The branch is
  not the anchor.
- **The approval record** is a file committed with the frozen tree, `freeze/APPROVAL-LARQL-VERIFY-001.md`, signed
  with the named human reviewer's key (an SSH- or GPG-signed commit or tag). It binds:
  - the protocol id;
  - the frozen commit SHA;
  - the SHA-256 of `FREEZE.sha256`;
  - the verdict of the freeze review it relies on, and that review's snapshot;
  - the reviewer's name.

  `tools/freeze_verify.py` refuses a tag whose commit does not carry a valid approval record matching all of those.
- **Who may create the tag.** The ruleset on `refs/tags/freeze/*` restricts **creation**, not only update and deletion,
  to the freeze owner's identity. Review 1 noted that the ruleset as recorded blocks update and deletion only.
- **The named human reviewer** is recorded in `evidence/B1/SETUP.md` before the freeze.
- **Every Phase 3 run starts with a recorded verifier pass.** The verifier is taken from the tag
  (`git show freeze/LARQL-VERIFY-001:tools/freeze_verify.py`) and run against the working tree used for the run. Its
  output and exit status go into that run's record. A run without a recorded pass is invalid.
- **The tamper tests become ten.** They are the nine existing tests, plus **test 10: creating a `freeze/*` tag from a
  token that is not the freeze owner's.** It must be rejected by the ruleset.
  - **How they run:** on the real remote, from a non-admin token, against a *rehearsal* tag pattern (for example
    `freeze-rehearsal/*`) with the same ruleset and verifier logic, so the real tag is created only once.
  - **The evidence:** for each test, the commit hashes and the CI run or ruleset rejection that decided it, plus one
    legitimate pass.
- **A residual risk, accepted in writing by the owner, not hidden:** the owner's admin token can edit the ruleset
  itself. The boundary therefore depends on no research or Phase 3 agent holding that token (item 9 below).

## 2. A cross-repository freeze manifest (review change 3)

`FREEZE.sha256` lists by path and SHA-256 every frozen file in this repository: the protocol, `draft.json`, the
SPEC, `tools/`, `.github/`, `isolation/` and `evidence/`.

It also contains an **external bindings** block, one line per item, each naming its repository and immutable
identifier:

| Item | Bound by |
|---|---|
| Checker | repository, commit SHA, tree SHA, SHA-256 of `requirements.lock` |
| Reviewer corpora | each seal: commit, tree, file count, digest (revisions 1–7) |
| E2/E3 pilot set | its own seal digest |
| E2/E3 held-out set | its own seal digest; contents never disclosed before the run |
| A4 mutation suite | its seal digest (G6) |
| LARQL | the baseline commit SHA (the freeze SHA) |
| Container | its digest under the definition decided for AMB-012 |
| Upstream checkpoint | HF commit and the nine per-file SHA-256s (Baseline) |
| ggml | commit `facdc44a` (Q8_0 reference) |
| T3 route | the route chosen, and for Qwen3-1.7B its HF revision and per-file SHA-256s |
| Reference-forward audit | its repository commit |

- **Off-machine publication.** The freeze owner publishes the SHA-256 of `FREEZE.sha256` and the tagged commit at a
  timestamped location outside this machine, chosen by the owner, and records it in the approval record. A pushed
  signed tag on the public remote is acceptable if the owner chooses it.
- **The verifier checks the in-repository files.** The external bindings are checked at the start of each Phase 3 run
  by re-hashing each named artefact. A mismatch makes the run invalid.

## 3. Verbatim checker briefs (review change 8)

- **From now on:** every brief given to the reference-checker agent is committed verbatim under
  `evidence/checker-briefs/` before the run starts.
- **Runs 4–11:** their briefs are preserved there as they stand (`92fad3f`).
- **Runs 1–3:** their briefs were not kept as separate files. This is recorded as a gap. Their content is only in the
  coordinating session's transcript.
- **Reviewer and auditor briefs:** briefs to hidden-corpus authors, freeze reviewers and auditors are kept the same
  way.

## 4. Stale status rows (review change 9, the editorial part)

| Location | Now says | Proposed |
|---|---|---|
| PROTOCOL.md remaining-work table, B3 | Open | **Admitted, revision 4** (`specs/vindex3-container/SPEC.md`, sha256 `8f3f7c2b…`, `evidence/B3/ADMISSION.md`). The third-party check is recorded there |
| Trusted-base table, container specification row | "pending B3" | admitted revision 4, document SHA-256 above |
| Remaining-work table, L1 | Open | **Audited at LARQL `2536bb79`** (`evidence/L1/AUDIT.md`). The freeze SHA is not yet named. `CAPABILITIES.md` is not yet re-checked at it (owner-held, item 13) |
| Remaining-work table, B1 | Open | Partly built: tag ruleset active; manifest, approval record, tag creation restriction and tamper tests outstanding |
| `evidence/B1/SETUP.md`, first table | "Private remote" | public remote, by the owner's choice (the update section of the same file) |
| `draft.json` `open_decisions` and `pre_freeze_gates` | as the above | kept consistent with the table |

## 5. The T3 amendment, with review 1's five corrections

`evidence/proposals/T3-PILOT-AMENDMENT-DRAFT.md` is adopted with the changes below. **Route selection stays open.**
Qwen3-1.7B is adopted only after the profile check in 5.6, on the owner's instruction.

### 5.1 What T3 claims (correction d, and the owner's statement)
- **What it is:** T3 is an **empirically calibrated agreement criterion**. It is **not** a mathematically certified
  floating-point bound.
- **Calibration absorbs shared deviation.** c and k are chosen from LARQL's own deviations on the pilot. Any deviation
  that LARQL shows on both the pilot and the subject is absorbed into c and k and cannot be detected by T3. A
  systematic LARQL error that is the same on both routes is invisible to T3.
- **What T3 can detect:** deviations on the subject that exceed what the pilot exhibited.
- **What remains for systematic errors:** E1, the A3 self-check laws, the A4 fault matrix and the reference-forward
  audit. T3 is not one of them.
- **Required wording:** every Stage A report states the above, and also names the route: "calibrated on an
  independent checkpoint of the same architecture" or "calibrated to this subject".
- **Fixed in advance:** the ladder, the input selection, the selection rule and the failure outcome are fixed before
  any pilot result is observed.

### 5.2 A deterministic selection rule (correction a)
- **The candidates:** the 15 pairs (c, k), with c ∈ {2, 4, 8, 16, 32} and k ∈ {4, 16, 64}.
- **The order:** by c ascending, then by k ascending: (2,4), (2,16), (2,64), (4,4), …, (32,64).
- **Selection:** the selected pair is the first in this order under which every pilot logit passes.
- **The margin step** is the **immediate successor of the selected pair in this same preregistered order** (owner's
  ruling, 2026-10-31). For example, (2,16) follows (2,4), and (4,4) follows (2,64). The final pair is that successor.
- **If the selected pair is (32, 64),** it has no successor. The outcome is `not_determinable_at_preregistered_ladder`.
  (32, 64) is never accepted silently as the final threshold, and the ladder is never extended after pilot results are
  seen (owner's ruling).
- **No pair passes:** the outcome is `not_determinable_at_preregistered_ladder`, unchanged from the amendment.
- **Fixed before any pilot result:** the order, the tie-breaking (none is needed in a total order) and the successor
  rule.

### 5.3 Pilot run conditions (correction b)
The pilot runs under the subject's conditions, all of them:
- the Baseline environment;
- the backend and representation source;
- the run-acceptance rule (`projection plans:` shows only `FusedKQuant` and `FusedBf16`);
- the host machine;
- the KV-cached one-token schedule;
- the LM-head binding: a stored head consumed as stored, with the bf16 cap.

A pilot run that fails any of these is invalid and is rerun under the same rule. It is never adjusted.

### 5.4 Pilot corpus separation (correction c)
- **Commitment:** the pilot corpus is part of the freeze. Its own seal digest is in the external bindings, together
  with its tokenization, ordering, positions and selection procedure.
- **Construction:** it is built by the independent corpus author without access to the held-out set's contents, and is
  disjoint from it (no shared documents, and a stated n-gram overlap bound).
- **Under the fallback route,** the pilot corpus is the declared subject-side pilot set, and is discarded after
  calibration as before.

### 5.5 The arithmetic rationale, corrected (correction e)
T3's "Reason" cell in PROTOCOL.md says LARQL's summation order is unknown (Accelerate). That is inconsistent with the
L1 audit (`evidence/L1/AUDIT.md`, item 2). On the pinned path:
- **The Q8_0 GEMV** accumulates sequentially per row in f32, in block order, with no FMA.
- **The LM head** (`FusedBf16`) uses NEON 4×4-lane FMA accumulators.
- **Attention scores, softmax and value mixing** are scalar f32 loops.
- **BLAS/Accelerate is not reached.** The run-acceptance rule excludes `BlasF32`.

The proposed reason: "LARQL's accumulation order on the pinned path is known (L1 audit), but differs from the
reference's, whose torch/BLAS order is unspecified. A γₙ-style factor c on the reference's own f32-against-f64
difference is the a priori **form**. The **values** of c and k are fixed by the pilot."

**What differs between Qwen3-1.7B and the subject.** Both have hidden size and head_dim fixed by the config. The
products whose length differs are:

| Product | Qwen3-0.6B | Qwen3-1.7B |
|---|---|---|
| q/k/v, gate and up projections (input length) | 1024 | 2048 |
| o_proj (input length) | 2048 | 2048 |
| down_proj (input length) | 3072 | 6144 |
| LM head (input length) | 1024 | 2048 |

Longer f32 accumulations tend to give larger LARQL-against-ref₃₂ deviations relative to |ref₃₂ − ref₆₄|, but not
uniformly. The expected effect is a **looser**, less sensitive T3 on the subject, not a more conservative one. The
amendment's wording ("plausibly makes c more conservative") is replaced by this.

### 5.6 The Qwen3-1.7B profile check (the owner's condition; checked 2026-10-31 from public metadata, no weights downloaded)

| Property | Result |
|---|---|
| Configuration | `Qwen3ForCausalLM`; head_dim 128, θ 1e6, no RoPE scaling, rms_norm_eps 1e-6, 16 q / 8 kv heads, 28 layers, max positions 40,960, sliding window null, tied embeddings, bfloat16. Equal to the subject except hidden size (2048 against 1024) and intermediate size (6144 against 3072) |
| Tokenizer files | `tokenizer.json` (LFS SHA-256 `aeb13307…`), `tokenizer_config.json`, `vocab.json` and `merges.txt` are byte-identical to the subject's (same LFS SHA-256 or git blob ids at both pinned revisions) |
| Weights | 311 tensors, all BF16, in **two shards** (`model-00001-of-00002`, 3,441,185,608 bytes; `model-00002-of-00002`, 622,329,984 bytes, holding only `lm_head.weight`). An explicit `lm_head.weight` [151936, 2048] ships beside `model.embed_tokens.weight`, as for the subject |
| Not yet known | Whether its `lm_head.weight` payload is byte-identical to `model.embed_tokens.weight`, as the subject's is (L1). That needs the weights |
| Not yet known | Whether LARQL's planner accepts a two-shard checkpoint, and whether SPEC revision 4 covers the resulting container without a new revision (the amendment's feasibility preconditions) |
| Not yet known | Its weight and activation value ranges against the subject's. This affects how often the f32 rounding regimes differ, and needs the weights; activations need a model run. **Proposed:** weight statistics only (no model run) are computed by someone other than the checker, after downloading the pinned revision. Activation ranges are not examined before the freeze |

**What remains before Qwen3-1.7B is adopted:** the three "not yet known" rows. The first and third need the weights;
the second needs the LARQL owner. If any blocks it, the fallback route applies (amendment).

## 6. The trusted computing base, complete (review change 12)

The trusted-base table is extended so that it lists what is actually trusted:

| Trusted item | Why it is trusted | How it is pinned or bounded |
|---|---|---|
| Upstream checkpoint | the definition of the subject | HF commit and nine per-file SHA-256s |
| ggml Q8_0 definition | the definition of the encoding | commit `facdc44a` |
| SPEC revision 4, including §17 execution semantics | container framing **and** the execution-surface fields the comparator reads | document SHA-256, third-party check (`evidence/B3/`) |
| `transformers` 5.5.0 and `torch` 2.14.0 | the reference implementation | `requirements.lock`, RECORD check in the audit |
| Checker-written oracle code: the f64 patch, runtime pins, read-back map, harness | it turns the library into ref₃₂/ref₆₄ and the D7 checks | checker commit; **the reference-forward audit** (running) |
| CPython 3.12.11 and the full locked dependency set | everything the checker runs on | `requirements.lock`, interpreter path in the isolation settings |
| torch's BLAS and the host | ref₃₂ is bit-reproducible only on one machine and thread configuration | host and thread settings recorded per run (AMB-016, AMB-023) |
| The reviewer's own tooling (`lib/exactfp.py`, generators, scorers) | expected values and scoring | reviewer commits and seals |
| The isolation layer | checker independence | settings SHA-256, snapshots, re-tests (`evidence/ISOLATION.md`) |
| The freeze layer | integrity of everything above after the freeze | tag, ruleset, approval record, verifier (section 1) |
| The coordinating session | it wrote briefs, ran audits and recorded aggregates | briefs kept verbatim (section 3); every record is checkable against the repositories |
| The human freeze owner and reviewer | approval | signed approval record |

## 7. The Stage A output contract (review change 14)

**What is frozen.** The checker's output fields that Stage A scoring consumes are frozen as a protocol contract, so
that Stage A scoring rules are not fitted to the checker's README after the fact. A later change to any of them needs
a new review.
- **Normative text:** checker `4bc93d3` `README.md`, sha256
  `56f00a4a2d9a94177a3798184d6cc3e2699387f54368cc041d3497a5784c367f`, sections 4 (E1), 5 (harness record and
  comparability), 6 (E2/E3 metrics and aggregate) and 7 (D7).
- **Required fields:**
  - **E1, per tensor:**
    - `numerical_metric_status`, `upstream_nonfinite`, `n_upstream_nonfinite`;
    - `bit_identical`, `n_bit_mismatches` (scored for unquantised tensors only);
    - `max_abs_error`, `absolute_frobenius_error`, `ref_frobenius`, `rel_frobenius`;
    - `null_metric_reasons`, `zero_reference_norm`;
    - for Q8_0: `n_within_t2`, `n_exceed_t2`, the ±0-scale block count, the D1 OQ1 outside-domain counts by scale
      class, and `nonfinite_upstream_in_t2_domain`.
  - **E1, totals:** `upstream_nonfinite`, `n_upstream_nonfinite`, `n_tensors_non_comparable_nonfinite`, and coverage
    (missing, extra and misshaped HF keys).
  - **D2:**
    - the status (`comparable`, `invalid_comparison`, `checker_error`);
    - reasons as `{category, field, key_path?, site?, message}`, with `field` drawn from reason-field schema v1.1.
  - **E2/E3, per position:** `status`, the per-side non-finite counts, `max_abs_diff`, `rms_diff`, `kl`, the top-1 ids
    and agreement.
  - **E2/E3, aggregate:** D10 clarification 1's minimum contract:
    - `aggregate_status`, `n_positions`, `n_comparable_positions`, `n_non_comparable_positions`,
      `non_comparable_indices`;
    - `max_abs_diff`, `rms_diff`, `kl` as {n, min, mean, max} over comparable positions;
    - `top1_agreement`.
  - **The run record:** the `check_comparable` reasons (empty means comparable), and the `record` fields listed in
    README section 5.
- **Not in the contract:**
  - quantiles (D10 clarification 2);
  - the block-level distributions (diagnostic, AMB-030f);
  - `finite_subset_*`;
  - `gguf_bit_identical`;
  - Q8_0 bit identity;
  - `comparable_set_empty`, `err_frobenius` and other aliases.
- **For Stage A scoring rules:** they map only these names. A name outside the contract is never scored.

## 8. G9: separate campaigns (proposed decision, the owner's)

- **Stage A** (empirical engineering verification of LARQL's Q8_0 Qwen3-0.6B execution) stays LARQL-VERIFY-001.
- **Stage B** (certified error bounds) becomes **LARQL-VERIFY-002**. **Stage C** (machine-checked proofs, Lean)
  becomes **LARQL-VERIFY-003**.
  - Each has its own frozen criteria, freeze review and acceptance.
  - Stage A's acceptance does not depend on either.
- **Record of the decision:** the owner proposed it 2026-10-31. It closes G9 once it is independently reviewed.

## 9. G7: the initial Stage B domain (proposed, for LARQL-VERIFY-002, subject to separate review)

- **The operation:** one Q8_0 matrix-vector product, y = W·x.
  - **W:** an m×n Q8_0 matrix. Blocks of 32, f16 scales finite and in T2's domain, so every scale is finite and ≥ 0.
  - **x:** a binary32 vector with finite entries, |xⱼ| ≤ X for a stated X, and n ≤ 6144.
- **Accumulation, as the L1 audit describes LARQL's kernel:**
  - binary32;
  - sequential per row in block order, as `acc += (q·d)·xⱼ`;
  - no FMA, with the product (q·d) rounded to binary32 before the multiply by xⱼ.
- **What is to be proved:** a bound on |ŷᵢ − yᵢ| in exact arithmetic, in two forms:
  - a γₙ-style form that holds for **any** summation order;
  - an order-specific form for the sequential order. Its sequential-order assumption is a stated, testable assumption
    about the kernel (TRUST-BOUNDARY item 4).
- **Out of scope:** activations, norms, attention, RoPE, softmax, any other format, Metal.
- **Format choice:** Q8_0 is chosen for continuity with Stage A. Under G7 that needs, and has, a stated reason. NVFP4 and
  Q4_K stay later options.

## 10. Reviewer–checker separation for Stage A hidden artefacts (review change 7)

- **The evidence so far:** the access-log review for revisions 2–6 is in `evidence/ACCESS-LOG-REVIEW-REV2-6.md`.
  - **What it found:** no direct implementation read by the authors of revisions 2–6.
  - **One exception:** the revision 1 scorer read implementation before writing its rules.
  - **Its limits:** they are stated there. It is not proof that prohibited access did not occur.
- **Proposed for Stage A:** hidden artefacts are built by an author running under a mechanism like the checker's
  isolation:
  - a sandbox with read allow-lists excluding `checker/` and any checker clone;
  - no network;
  - briefs kept verbatim;
  - one re-test recorded.

  Those artefacts are the E2/E3 held-out set, the frozen A4 suite and any freeze-time hidden rows.
- **The E2/E3 corpus author started today under written rules.** Its work is admitted only if its tool log shows no
  access to the excluded paths, or if it is rebuilt under the mechanism. **The owner chooses which.**

## 11. The E2/E3 corpus (owner's rulings of 2026-10-31)

- **Admission.**
  - **The corpus is kept, not rebuilt for lack of a sandbox.** It is admitted by its exact hashes only if a separate
    reviewer's admission check passes. That check covers:
    - the 46 sequences;
    - the provenance of the generator and its source pools;
    - disjointness;
    - the pinned tokenizer;
    - position selection;
    - the absence of checker or LARQL-output exposure.
  - **The author's clean tool log and the two valid seals are evidence, not admission.**
  - **A rebuild is required only if that check finds a material provenance or independence problem.**
  - **The check is running.** Its report will be `e2corpus/ADMISSION-REVIEW.md` in the reviewer repository.
- **Tokens:**
  - the subject's pinned tokenizer, with exact token ids stored in the corpus;
  - an explicit BOS token-id policy, with no automatic BOS insertion by either runtime;
  - no runtime chat template; any templating happens before sealing.
- **Held-out data:** it need not be wholly synthetic. Synthetic data is acceptable if generated and sealed
  independently. Its provenance and selection are frozen.
- **Phase 3 handover:** read-only and hash-verified, after the freeze, with separate permissions for the pilot and
  held-out sets, so that the pilot provably runs first.
- **Licences:** the licences of the model, tokenizer, corpus sources and reference code are recorded before anything
  is published.

## 12. Extended context and selective capture (owner's rulings of 2026-10-31)

- **The maximum position stays 40,959,** as an extended-context stress case. Results are reported in two classes:
  - **native-context evidence:** positions ≤ 32,767, within the configured native limit;
  - **extended-context evidence:** positions 32,768–40,959, reported separately.

  Both classes use the same preregistered T3 rule. A failure in the extended class is never described as a failure
  of the model's native-context contract.
- **Positional behaviour must be defined.** Extended positions are compared only where both implementations have
  explicitly defined and supported positional behaviour there. If either refuses those positions, the result is an
  unsupported comparison, never a numerical discrepancy. The logit-dump specification records LARQL's behaviour (§13).
- **Position-selective capture is permitted.**
  - **What is captured:** logits only at the preregistered evaluated positions, with the **whole vocabulary**
    compared at each.
  - **What is never skipped:** every preceding token is executed and the KV cache is maintained. Selective capture
    never changes the computation.
  - **"Every pilot logit" in T3** means every vocabulary logit at every preregistered pilot position.

## 13. AMB-012 and AMB-014 (owner's proposed resolutions, 2026-10-31)

- **AMB-012, container identity.**
  - **The proposal:** an unambiguous SHA-256 commitment over a canonical inventory of relative paths and raw file
    bytes. The inventory includes `index.json`, the system graph and every required segment. Its encoding, sorting,
    path normalisation and exclusion rules are published and frozen. The digest never relies only on hashes stored
    inside the container.
  - **Existing constructions, to be reconciled rather than silently replaced:**
    - **The checker's** (its AMB-012, `harness.container_sha256`): SHA-256 over the lines
      `<relative path>\0<size>\0<file sha256>\n`, one for every regular file, sorted by path.
    - **The L1 record** (`evidence/L1/container-q8_0.sha256`): a per-file `shasum` listing of the 11 files, including
      the informative `candidate.json` and `generation_config.json`.
    - **SPEC revision 4 §13:** per-segment digests inside `index.json`, with no digest of the whole container.
  - **Questions for the reconciler:** which construction is adopted, and which files are in or out of the inventory
    (for example, `candidate.json` is informative under SPEC §13.4).
  - **Who reconciles:** the independent reviewer, before the freeze.
- **AMB-014, logit-dump format.**
  - **A separate output contract** covers tensor shape, vocabulary ordering, token and position identifiers, dtype,
    endianness, framing and completeness.
  - **Who writes it:** a specification author who may read LARQL's producer code. That draft is in progress at
    `specs/larql-logit-dump/SPEC.md`, from LARQL `2536bb79`, without running LARQL.
  - **Before it is trusted:** a third party checks it.
  - **The checker** implements the admitted format without consulting LARQL code.
  - **Until that interface is independently reviewed,** no logit comparison is accepted as E2 evidence.

## 14. Freeze authorisation (owner's ruling, 2026-10-31)

The freeze is **not** authorised until the reference-forward audit and an independent readiness review are complete.
Drafting and testing the mechanisms below is authorised now. Gate closure still needs the independent evidence. The
remaining work is grouped into three deliverables:

| Deliverable | Contents |
|---|---|
| Independent numerical foundation | the reference-forward audit; an admitted logit-dump specification; an independent inspection of the T3 calibration procedure |
| Immutable experiment package | the admitted E2/E3 corpus, the pinned LARQL commit, the frozen A4 suite, the cross-repository manifest |
| Independent authorisation | a named human reviewer, the externally controlled signed approval, the ten tamper tests, restricted Phase 3 credentials |

- **If the reference-forward audit finds a genuine numerical error** in `f64_patch.py`, reference attention, KV
  caching or the harness, that component is repaired and revalidated before it is used as an oracle.
- **The second blind freeze review** is held on a new immutable snapshot once these exist.

---

## Owner-held items (not draftable by the coordinating session)

These close review 1's remaining changes. None may be done by the agent this protocol governs.

1. **The approval record.** Sign it, name the human reviewer, and choose the off-machine timestamp location.
2. **The tag ruleset.** Restrict tag creation to the owner.
3. **The ten tamper tests.** Run them on the real remote with a non-admin token, using a rehearsal pattern.
4. **Phase 3 agents.** Name them, and confirm they hold no `gh` token or push rights (review change 5).
5. **TRUST-BOUNDARY items 1–2.** Mark them resolved or accepted, accepting each residual risk in writing (review
   change 6).
6. **The LARQL freeze SHA.** Name it, and have `CAPABILITIES.md` re-checked at it by an auditor who is not the
   checker (review change 9).
7. **AMB-012 and AMB-014.** Proposed resolutions are in §13; AMB-012 needs independent reconciliation and AMB-014 a third-party-checked specification (review change 11). AMB-012 is how the container digest is defined. AMB-014 is
   that LARQL's logit-dump format has no admissible source.
8. **The A4 mutation suite (G6).** Freeze it, including rows for the A3 laws (S5, IP1–IP3). It is built by an
   independent author under section 10.
9. **Pushing.** This repository is public, and 52+ local commits are unpushed. Pushing publishes the Phase 1 evidence.
   The hidden corpus is in a separate repository and stays private.
