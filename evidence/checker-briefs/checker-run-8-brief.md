You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md, with the protocol read from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/19ab645/PROTOCOL.md` (sha256 `1e79ae8bec1942b7cbaaac37620c78c8d3a09a50a69322354c80a944f9943984`; verify it first). Phase 1 rules apply in full.

## This run: bring the D7 comparator into line with decision revision D8
Read the snapshot's section "Decision revision D8" in full. Then make exactly these changes:

1. **Q24, score scale.**
   - The expected declared score scale must be the exact mathematical `1/√head_dim`, rounded once, correctly (round-to-nearest-even), to the SPEC-declared type of `X.attention.score_scale` (binary64, SPEC §17.4).
   - Compute it **without** the platform's `pow`, `sqrt` or float division, using exact rational or integer arithmetic. `config_compare.py` currently uses `float(head_dim) ** -0.5`; replace that.
   - Unit-test it against independently known correctly rounded values for several head dims. Include a case where `1/math.sqrt(h)` is not correctly rounded, for example h = 32 or 128. Also test that nothing depends on the platform's `pow`.
   - Keep execution precision separate: no binary32 conversion in the configuration comparison.
2. **Q23, unresolved assumptions.**
   - Any unresolved assumption must produce status `invalid_comparison`, with a structured reason per affected field: the field, the site, and what cannot be established. Check that the comparator already does this, and fix it if not.
   - Expected values for fields with no configuration key are derived from the stand-in authority through the reference's documented semantics. For example, the score scale comes from the stand-in's `head_dim`.
3. **Sliding windows.** A non-null authority `sliding_window` stays unresolved, giving `invalid_comparison`, as an explicit scope limitation (D8). Make sure the reason text says so.

## Constraints
- **Scope:** change nothing else. No D6 or aggregate work.
- **Inputs:** no hidden cases. Never read LARQL source or look for the real container.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update AMBIGUITIES.md and README.md where relevant.
- **Commit:** one clear commit, no attribution trailers. If the commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the test count and result;
- the commit hash;
- any new ambiguity.
