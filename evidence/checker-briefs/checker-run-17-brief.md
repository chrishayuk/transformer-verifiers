You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/d544bf1/PROTOCOL.md` (sha256 `f53e24513835a49f26eb81376280b2b90059263f8101c7611ea153d7b143661a`), and verify that hash first. Phase 1 rules apply in full.

## This run: the Q8_0 GEMV reference (D15 clarification 3)

Read "Decision revision D15", including clarification 3, in full. Your specification is `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/d544bf1/Q8_0-GEMV-SPEC.md` (sha256 `c3b439c011a50ce06d04ba92bc5458f05863123b409045b1be2d555a19468e78`). Verify that hash, and read all of it. It is the only requirements document for this work.

**Existing `refcheck/` files must not change.** Each must stay byte-identical to commit `078d384`. Add new files only. You may reuse `refcheck/q8_0.py` by importing it. If you find an existing file needs changing, make no change: stop and report it.

## Deliverables

### 1. `refcheck/gemv.py`

Takes raw bytes, with no file format or container involved:

- `seq_bits(blocks, x_bits, n, k)`: section 3's program, returning each row's result as its 32-bit pattern.
- `check_seq(blocks, x_bits, y_bits, n, k)` and `check_b1(blocks, x_bits, y_bits, n, k)`.

Each check returns a result holding: `status` (`satisfied`, `violated` or `could_not_evaluate`), `reasons`, rows checked, rows violating, and the first violating row. `check_b1` also reports the worst `|y − y*| / B`, computed exactly and then given as a decimal string, and that row's number.

Requirements:

- **The summation has to be truly sequential.** Library sum routines may be pairwise, which is a different program. Confirm whatever you use has section 3's order and rounding, with a test that tells them apart.
- **`check_b1`'s verdict has to equal exact rational arithmetic.** Compute `y*`, `S` and `B` exactly. If you use a faster path, show that it can't change a verdict.
- Refuse malformed input: lengths that don't match, `k` not a multiple of 32, `k` zero or too large. `n = 0` is not `satisfied`: nothing was measured, so it is `could_not_evaluate`.

### 2. Positive tests

Against the reference's own `seq_bits`, and independently against exact rational arithmetic on small cases:

- ordinary values;
- every kind of scale: zero, negative zero, subnormal, smallest and largest normal, largest finite;
- codes including -128 and 127;
- subnormal `x`, wide exponent ranges, products that underflow;
- exact cancellation, where `y*` is 0;
- both sides of the domain: just inside and just outside `Ω`, and an infinite or NaN scale or `x`;
- a sign-of-zero case.

Write at least one case by hand, with its expected bits worked out without using the code under test.

### 3. Deliberately faulty implementations

In `tests/` only, never in `refcheck/`. Each computes a wrong result, written to section 3's interface. For each one, test that `SEQ` fails on inputs you choose. Record what `B1` does on them.

| Fault | `SEQ` | `B1` |
|---|---|---|
| Wrong stride between rows | Must fail | Must fail |
| Last block of each row dropped | Must fail | Must fail |
| Subnormal scales flushed to zero | Must fail | Must fail on an input you choose |
| One flipped code | Must fail | Must fail on an input you choose |
| Sign of one row flipped | Must fail | Must fail |
| Lowest bit of one output flipped | Must fail | Record which |
| Sum in reverse order | **Must fail** | **Must pass** on inputs where the order matters |
| Scale factored out of each block, as `d·Σ(q·x)` | **Must fail** | **Must pass, if it does: see below** |
| Pairwise summation | **Must fail** | **Must pass, if it does: see below** |
| Accumulate in binary64, round at the end | **Must fail** | **Must pass, if it does: see below** |

The last four show that `SEQ` and `B1` measure different things. Section 5's derivation covers only section 3's program, so "must pass" for the last three is an expectation, not a result: if one of those exceeds `B1`, that isn't a defect in the bound. Record it and keep the test recording what happens. A fault that escapes where the table says it must fail is a finding: report it, and don't weaken the table.

### 4. Numerical diagnostics

Add `tests/test_gemv_diagnostics.py`, on synthetic data, using seeded generators, at `k` = 32, 1,024 and 3,072, with a few rows each: for several input families, section 3's program against exact arithmetic, reporting the worst `|y − y*| / B` for each. Print the table in your final report. Keep the runtime reasonable.

### 5. Search for a counterexample to `B1`

Try to break the inequality with section 3's own program, in the regions where the derivation is thinnest: products near the subnormal boundary, many terms in the underflow range, large cancellation, and the top of the domain near `Ω`. Report what you tried and how many cases.

Finding none doesn't establish the bound. Say so. **If you find one, follow section 6: record it and stop that line of work. Do not change the bound, constants, domain or program.**

## Tests: synthetic only

**Never** invoke a real LARQL binary, never read LARQL source or kernels, and never touch a real container, real logits, development outputs or held-out data. Clarification 2's real-stdout exception does not apply to this work. Don't guess what any real implementation does: nothing outside the specification is an input.

## Constraints

- **Scope:** new files in `refcheck/` and `tests/`, `AMBIGUITIES.md`, and README lines describing the new module and coverage.
- **Ambiguity:** choose the fail-closed reading and record it.
- **Language:** results are measurements. Don't describe anything as proved.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report

Include:
- the changes, file by file;
- the fault table, with what actually happened in each cell;
- the diagnostics table;
- the counterexample search: what was tried, how many cases, and the outcome;
- the test counts before and after;
- confirmation that every existing `refcheck/` file is byte-identical to `078d384`, with the command you used;
- the commit hashes;
- any new ambiguity.
