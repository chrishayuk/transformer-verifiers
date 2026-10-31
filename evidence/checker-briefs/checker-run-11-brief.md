You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/c972d62/PROTOCOL.md` (sha256 `8595bd28ded179f337af5a7829f5b1690c52816dc7ea85c5d686c3af6d3283b0`), and verify that hash first. Phase 1 rules apply in full.

## This run: the remaining checker requirements, D6 and metric aggregates
Read these parts of the snapshot in full: "Decision revision D10", "Decision revision D6", D1's OQ6, and D5's AMB-019. The comparability gate (D2, D7–D9) is feature-complete. **Do not change it.**

Implement exactly two things.

1. **D6, non-finite reconstruction reporting (A1, every stored representation, Q8_0 and unquantised alike).** For any tensor whose upstream values include NaN, +inf or −inf:
   - **Bit identity.** Keep `bit_identical` and `n_bit_mismatches`, comparing NaN payloads and infinity signs bit for bit. Where a representation already reports bit identity, keep it. If bit identity against upstream is not meaningful for a Q8_0 tensor, say how you handle that, and record it as an ambiguity rather than inventing a rule.
   - **Full-tensor metrics.** The maximum absolute error and the relative and absolute Frobenius errors are `null`, as is the reference norm, each with a stated reason. The numerical-metric status is `non_comparable_nonfinite`.
   - **Counts.** Report the per-class counts of non-finite upstream elements (`nan`, `+inf`, `−inf`), kept distinct.
   - **Finite-subset diagnostics.** Optional. If you report any, use only distinct `finite_subset_*` names, never the full-tensor names.
   - **What D5 keeps.** Its element-level T2 classification and integer counts stay. D6 replaces only D5's "non-finite in the floating-point statistics" wording for these tensors.
   - **Finite-upstream tensors are unchanged.** That includes a non-finite *decoded* value against finite upstream (D1 OQ1), still reported as non-finite. The statistics stay computed in binary64.
   - **Field name.** The absolute Frobenius error is published as `absolute_frobenius_error` (D6 question 22). If you currently use another name, publish this one, and either drop the old name or document it as an alias.
   - **A tensor-level status for finite tensors.** Give every tensor an explicit numerical-metric status. Choose and document the value for finite tensors.
2. **The metric aggregate interface (D1 OQ6, D6 question 21, D10).** Expose an explicit, public, documented aggregate interface over E2/E3 positions.
   - **Exclusion.** Non-comparable positions are excluded from every numerical aggregate.
   - **Never a success.** A non-comparable position is never counted as a successful comparison or an agreement, in any rate or count.
   - **Counts.** Report the total, comparable and non-comparable position counts.
   - **An empty comparable set,** for example an entirely non-comparable sequence, is represented explicitly. It must never be represented as a numerical value that could read as agreement (such as 0 error, or a top-1 rate of 1).
   - **Documentation.** README states which positions are included, how non-comparable ones are excluded, and how an empty comparable set is represented.
   - `metrics.compare` already has a summary. Make it, or a dedicated function, the documented interface. Test it on a mixture of comparable and non-comparable positions, on an entirely non-comparable input, and on the counts.

## Constraints
- **Scope:** change nothing else. No change to the comparability gate, T2, the decoder or the reason schema, and no new numerical model.
- **Inputs:** no hidden cases. Never read LARQL source, and never look for the real container or logit dumps.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly, with the count before your changes.
- **Records:** update AMBIGUITIES.md (record any new ambiguity) and README.md, including the output field names for both features.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the exact output field names and status values for D6, and for the aggregate interface;
- how an empty comparable set is represented;
- the test count before and after, and the result;
- the commit hashes;
- any new ambiguity.
