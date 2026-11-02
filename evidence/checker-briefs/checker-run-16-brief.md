You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/5d1b1f1/PROTOCOL.md` (sha256 `411a6922dc1e434bcf2f11a637e678a51fc41998260c01d16c07f520e43c4447`), and verify that hash first. Phase 1 rules apply in full, except for the one exception below.

## This run: tests and records only (D15 clarification 2)

Read "Decision revision D15", including clarification 2, in full, and your own AMB-033 (d) and AMB-034.

**`refcheck/` must not change.** The commit that ends this run must have the same `refcheck` tree as `e505afc`. Check it with `git rev-parse HEAD:refcheck`, which must print `e82a4425ab4b57cb18212e19fdf9e0c57936b00e`. If you find a change to `refcheck/` is needed, make none: stop and report it.

### Item 1: the intermittent test

`tests/test_ingest.py`, `Substitution.test_a_record_from_a_different_run`, fails intermittently. It fails in about half of runs, at both `c2070c3` and `e505afc`. Your AMB-034 (d) gives a diagnosis, which you must confirm by reproducing the failure and reading its message, not assume.

Repair the test's fixture so that its result no longer depends on timing:

- **The test must still require every refusal code it requires today.** Do not drop one, and do not widen what is accepted.
- **Not allowed:** a retry, a skip, an `expectedFailure`, a sleep, removing or loosening an assertion, or catching the failure.
- **Check for the same weakness.** Other tests in the file may assume that two stub runs produce different sidecars or hashes. Check them, and fix any that have this defect in the same way. List what you checked.
- **Evidence.** Run `test_ingest.py` at least 20 times before the repair and at least 20 times after it, and report the failure counts of both.
- **History.** Do not rewrite the history. Keep AMB-034 (d) as written, and add a dated note after it: what the cause was, the failure counts, and the repair.

### Item 2: AMB-034, the other exact-match stdout lines

The one exception to "tests are synthetic only": `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/5d1b1f1/REAL-STDOUT-FIXTURES.json` (sha256 `b68901ab5a8fd15ef070d965b3cdf15a43102174d2792db80c5d5d175f113df1`) holds the stdout of three real development runs. Verify the hash, copy the file to `tests/fixtures/real_stdout.json` unchanged, and have the test verify that digest, so a changed fixture fails.

Write tests that, for each fixture:

- verify the stdout against the fixture's `stdout_sha256`;
- pass the real stdout, N, V and output paths through the pinned stdout check (`_check_stdout`), and assert that no reason is raised;
- change each line that AMB-033 (d) reads exactly, one at a time, and assert the existing refusal code for that line: `engine:`, `positions:`, the two `wrote` lines, and `runtime compile:`;
- for `runtime compile:`, keep the real suffix accepted, and refuse a different tensor count.

The fixture paths are data only. Do not open them, or anything else they point to.

If the pinned code refuses a real fixture, do not change the reading and do not change `refcheck/`. Stop and report the refused line and code.

Then update AMB-034 (c): for each line it lists, say what the real fixtures show. State what they do not show: three runs of one binary on one machine, whose output paths have no spaces or other unusual characters.

## Tests: synthetic otherwise

- **Never** invoke a real LARQL binary, never read LARQL source, and never touch the real container, real logits, development outputs or held-out data. The fixture file is the only real output you may read.

## Constraints

- **Scope:** `tests/`, `AMBIGUITIES.md`, and README lines about test counts or coverage. Nothing else.
- **Ambiguity:** choose the fail-closed reading and record it.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report

Include:
- the changes, file by file;
- the confirmed cause of the flake, with the failure message;
- the failure counts before and after;
- which other tests you checked for the same weakness;
- each new test and its result;
- the test counts before and after;
- the output of `git rev-parse HEAD:refcheck`;
- the commit hashes;
- any new ambiguity.
