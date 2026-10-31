You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/e056903/PROTOCOL.md` (sha256 `99a391a6f0f00d799a5c95b0cd5324547f465bdc3ca23b0fce3323414bff265c`), and verify that hash first. Phase 1 rules apply in full.

## This run: the T3 evaluator and the f64 guard (D12)
Read "Decision revision D12" in full, then the T3 row of "Tolerance rules", D1's OQ6, and D10 with its clarifications. An independent audit of your reference forward found no material defect, but noted two gaps. This run closes them and nothing else.

1. **T3 evaluator.** Add a public, documented function that, given (c, k), evaluates |LARQL − ref₃₂| ≤ max(c·|ref₃₂ − ref₆₄|, k·ulp₃₂(ref₆₄)) for every vocabulary logit at every evaluated position.
   - **Inputs:** candidate (LARQL) logits, binary32; ref₃₂ logits, binary32; ref₆₄ logits, binary64. Each comes with its run record, plus a list of preregistered evaluated positions (row indices into full arrays), and optionally a band specification. A positions list must be explicit; there is no silent default to "all".
   - **Refusal before any verdict.** The function refuses incomplete or inconsistent triples with explicit reasons. That includes:
     - a missing array or record;
     - shape or vocabulary mismatch;
     - different token ids or token-id hash;
     - positions out of range or not matching the records;
     - container identity mismatch for E2;
     - configuration mismatch;
     - wrong dtypes;
     - ref₃₂ not f32;
     - ref₆₄ not native f64;
     - a D7 gate that did not pass on either reference run.

     Reuse `check_comparable` for the candidate-to-reference conditions where it fits. A refusal is never a T3 verdict, and never a pass.
   - **Non-finite values.** A position where any of the three has NaN or ±inf is `non_comparable` (D1 OQ6). It is excluded from the counts, listed by index, and never a pass.
   - **Exact decision.** Decide the inequality exactly: rational arithmetic on the exact binary32 and binary64 values, or binary64 only where you prove it exact. Rounding must never flip a verdict. Test values at and next to the boundary.
   - **`ulp₃₂`.** Use D12's proposed definition exactly. Record it as an ambiguity entry noting that it awaits owner confirmation.
   - **Output.** A documented structure with:
     - per-position pass/fail and the worst ratio;
     - counts of logits passing and failing;
     - comparable and non-comparable position counts and indices;
     - an overall verdict that is a pass only if every evaluated logit at every comparable position passes and at least one position is comparable;
     - the same summary per band, and per native (≤ 32,767) and extended (≥ 32,768) class.

     An empty comparable set gets an explicit status, never a pass.
2. **The f64 guard (audit finding m3).** A requested native-f64 run must never execute outside the f64 patch context. Today a model built by `build_model` and decoded outside `native_dtype_patches(True)` silently gets float32 islands. Make that path refuse or raise, and test it. Do not change ref₃₂ or ref₆₄ numerics.

## Constraints
- **Scope:** change nothing else. No choice of c or k, no reading of any LARQL dump format, no change to the reference numerics, the comparability gate or the existing metrics.
- **Inputs:** synthetic triples only. Never read LARQL source, and never look for LARQL logits, the real container or any held-out data.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Records:** update AMBIGUITIES.md and README.md, including the evaluator's field names and statuses.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the evaluator's signature, output fields and statuses;
- the refusal reasons;
- how exactness is achieved;
- the test counts before and after;
- the commit hashes;
- any new ambiguity.
