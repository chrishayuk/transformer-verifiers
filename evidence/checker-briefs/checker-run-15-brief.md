You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/8b3663a/PROTOCOL.md` (sha256 `927c0cb92b3a224910ad37d11067d4fb1131cd49afc1ea0586a49b64ad7e8697`), and verify that hash first. The admitted logit-dump specification is in the same snapshot as `LARQL-LOGIT-DUMP-SPEC.md` (sha256 `5ad44e331be364300597692ec69e1fd5aafb35190275cfdb488e4d1bb91ad2ec`). Phase 1 rules apply in full.

## This run: the `representation:` stdout line (D15 clarification 1, DO-1)

Read these in full:
- "Decision revision D15", including clarification 1;
- the admitted specification's §7.3 and §8.3.3.5;
- your own AMB-033 and README §9.

Clarification 1 is your source. It changes how `refcheck/ingest.py` reads one stdout line: `representation:`.

1. **The rule.** Accept the single `representation:` line when it begins with exactly `representation: Q8_0  source: stored`, and that text is followed either by the end of the line or by a space. Do not interpret anything after that space.
2. **What stays the same.** The line must still be present and appear only once, and its place in §7.3's order is unchanged. Every other stdout line keeps its current reading. Every refusal code and its clause mapping stays the same. A line that breaks the rule still gives `stdout_line_mismatch`.
3. **The stub.** Change `tests/stub_larql.py` so that, by default, its `representation:` line carries a suffix that starts with a space, as clarification 1 describes. Keep a way to print the bare line too.
4. **Tests.** Write at least these:
   - accepted: the bare line;
   - accepted: the line with the suffix `  objects from a compiled pack: 1/4`, plus another suffix value;
   - accepted: a complete stub run with the suffix, through ingest and then `evaluate_t3` on synthetic references;
   - refused, each with `stdout_line_mismatch` unless the existing code for that case is a different one: another representation (`Q4_K`, `BF16`); another source (`source: synthesized`, `source: transient`); a run-on source token (`source: storedX`); one space instead of two before `source:`; a tab or other non-space character directly after `stored`;
   - refused with their existing codes: the line missing; the line repeated, with and without the suffix; the line out of order.
5. **Records.** Update README §9 (the `stdout_line_mismatch` row and the text) and AMBIGUITIES.md. Record in AMB-033 that the whole-line reading of this line is superseded by clarification 1. Say whether any *other* exact-match line in AMB-033 is at risk of the same kind of mismatch, using only the specification. Do not change those lines' readings in this run.

## Tests: synthetic only
- **Never** invoke a real LARQL binary, never read LARQL source, and never touch the real container, real logits, development outputs or held-out data.

## Constraints
- **Scope:** change nothing else. Nothing in T3, `ulp₃₂`, the outcome rule, the reference numerics, the comparability gate, the metrics, the f64 guard, or any other ingestion check.
- **Ambiguity:** where clarification 1 leaves something open, choose the fail-closed reading, and record it in AMBIGUITIES.md.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the exact acceptance rule as you implemented it, with the code that does it;
- each new test and its result;
- the test counts before and after;
- the commit hashes;
- any new ambiguity, and your answer on the other exact-match lines.
