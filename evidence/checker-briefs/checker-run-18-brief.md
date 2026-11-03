You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/d544bf1/PROTOCOL.md`, and the specification `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/d544bf1/Q8_0-GEMV-SPEC.md` (sha256 `c3b439c011a50ce06d04ba92bc5458f05863123b409045b1be2d555a19468e78`). Verify that hash first.

## This run: two boundary tests, tests only

**`refcheck/` must not change.** The commit that ends this run must have the same `refcheck` tree as `f599589`, which you can check with `git rev-parse f599589:refcheck` and `git rev-parse HEAD:refcheck`. If you find `refcheck/gemv.py` needs changing, make no change: stop and report it.

An audit changed `refcheck/gemv.py` in a scratch copy and found two changes your tests don't catch.

1. **`check_b1`'s comparison.** Changing `lhs > rhs` to `lhs >= rhs` passes every test. Section 4 says `≤`, so an error exactly equal to `B_i` is `satisfied`. Construct an input whose `y` makes `|y − y*|` exactly equal to `B`, or one unit past it, and test both sides. `y` can be any bit pattern here: it doesn't have to come from section 3's program.
2. **The domain's third condition.** Dropping `k·η`, so the check reads `(1 + γ_k)·S < Ω`, passes every test. Construct a row with `(1 + γ_k)·S < Ω ≤ (1 + γ_k)·(S + k·η)`, and assert `could_not_evaluate`.

Work out each construction exactly, without using the code under test. **An input might not exist:** `w` and `x` take limited values, so one of these exact conditions may be unreachable. If so, show why, record it in `AMBIGUITIES.md`, and don't add a test that passes for another reason.

For each test you add, check it does its job: in a scratch copy outside the repository's tracked files, apply the change above and confirm the new test fails.

## Constraints

- **Synthetic only.** Never invoke a real LARQL binary, or read LARQL source, real containers, real logits or development outputs.
- **Scope:** `tests/`, `AMBIGUITIES.md`, and README lines about coverage.
- **Section 6 still applies.** Do not change the bound, constants, domain or program.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests`. Report the count before and after.
- **Commit:** clear commits, no attribution trailers. Do not push.

## End with a report

The constructions, what each new test asserts, the mutation results, the test counts, the two `git rev-parse` outputs, and the commit hashes.
