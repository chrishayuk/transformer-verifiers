You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md, with the protocol read from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/6f28db9/PROTOCOL.md` (sha256 `2fac79c0348d159df4df8657bc8de7763c73cc2695929f0e5afa39da33a52365`; verify it first). Phase 1 rules apply in full.

## This run: the final, narrow comparability correction
Read the snapshot's "Decision revision D9" in full, especially clarifications 2 and 3 at its end. Implement exactly three things:

1. **Question 27, geometry fallback (clarification 2).** A layer with **no** `geometry` object inherits `head_dim` and `num_kv_heads` from `X.attention` (SPEC §17.2), so it compares as those values. A **present but incomplete** `geometry` object does not inherit: each missing value is `unresolved`. Test both cases.
2. **Reason-field schema v1 (question 34, clarification 3).**
   - Every reason's `field` must be one of the canonical identifiers in the protocol's table, spelled exactly. Your own path stays in `site` or `key_path`.
   - Each primary field may be accompanied only by its listed derived findings.
   - Publish the table, marked "schema v1", in README.md, with how each identifier is reported.
   - Add a test that every `field` the comparator can emit is in the table, and that derived findings appear only with their primary field.
3. **Reference-side categories (AMB-027, clarification 3).**
   - Apply the category table.
   - A pin failure is `contradiction` only when it shows a real conflict with the declared contract. A pin that cannot be evaluated (a software exception, missing infrastructure) is `checker_error`.
   - Keep `rope_parameters: null` counted as declared.
   - Test a pin conflict and a pin that cannot be evaluated.

## Constraints
- **Scope:** change nothing else. The comparability gate is otherwise frozen in scope. D6 and the aggregate interface remain out of scope.
- **Inputs:** no hidden cases. Never read LARQL source, and never look for the real container.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update AMBIGUITIES.md (AMB-021 and AMB-027 decided, and Q34) and README.md.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the field identifiers you emit, against the schema table;
- the test count and result;
- the commit hashes;
- any new ambiguity.
