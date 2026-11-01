You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/7f1b246/PROTOCOL.md` (sha256 `76504d789735b94e9c777c7b0275ea2bc046ee0fafa093f2c8a4998e855c5e7c`), and verify that hash first. Phase 1 rules apply in full.

## This run: correct the overall T3 outcome rule (D12 clarification 2)
Read D12 "Clarification 1" and "Clarification 2" in full.

Clarification 2 replaces the overall-verdict rule that your run 12 brief gave you. That rule came from the coordinating session's brief, not from the protocol, and it was wrong: non-comparable positions must not be allowed to leave a `pass`. Change exactly this in `refcheck/t3.py`:

1. **The overall T3 outcome**, and the same rule for every band and class summary:
   - **`pass`:** every evaluated position is comparable, and every logit satisfies T3.
   - **`fail`:** any comparable evaluated logit violates T3. This holds even if other positions are non-comparable; report the incomplete coverage alongside.
   - **`incomplete`:** no comparable violation, but one or more evaluated positions are non-comparable. Not a pass.
   - **`empty_comparable_set`:** no comparable position. Never a pass.
2. **Keep the per-position reasons** (`non_finite`, `ref64_above_binary32_range`). Record them in AMBIGUITIES.md: AMB-031a and AMB-031b are now decided by clarifications 1 and 2.
3. **Representability:** confirm that it is exactly |ref₆₄| > FLT_MAX, with FLT_MAX = (2 − 2⁻²³)·2¹²⁷, compared exactly on the binary64 value, and equality in range. Add a test at FLT_MAX exactly and at the next binary64 value above it, if you don't already have one.
4. **Confirm `ulp₃₂`** matches clarification 1 exactly. It should already.

## Constraints
- **Scope:** change nothing else. The snapshot now also contains the admitted logit-dump specification (`LARQL-LOGIT-DUMP-SPEC.md`). **Do not implement a reader for it in this run**; that is separate work.
- **Unchanged:** the reference numerics, the comparability gate, the metrics and the f64 guard.
- **Inputs:** synthetic data only. Never read LARQL source, and never look for LARQL logits, the real container or any held-out data.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Records:** update README section 8 and AMBIGUITIES.md.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes;
- the outcome values and when each applies;
- the test counts;
- the commit hashes;
- any new ambiguity.
