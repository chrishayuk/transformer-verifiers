You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md in this repository, and all its rules still apply. Phase 1 rules still apply.

## This run: implement decision revision D4, part A1
Read `../protocols/LARQL-VERIFY-001/PROTOCOL.md`, section "Decision revision D4 (2026-10-31)", in full. Implement only its first bullet:

- **Every tensor gets error statistics.** The E1 report gives, for every tensor, unquantised (BF16) tensors included, the maximum absolute error and the relative Frobenius error against upstream, alongside the existing BF16 bit-mismatch count and bit-identical flag.
  - A bit-identical tensor with a non-zero reference norm reports both as zero.
  - A differing tensor has both computed from the values, never replaced by the mismatch count.
- **Zero reference norm, for any tensor, Q8_0 included.** When ‖upstream‖ = 0, report the relative Frobenius error as `null` with `zero_reference_norm: true`, together with the absolute Frobenius error.
  - Never report it as 0, and never as a computed 0/0 or x/0.
  - This supersedes any earlier convention, including the inf/inf behaviour recorded in AMB-019 (i). Note that in AMB-019; the rest of AMB-019 stays open.
- **Keep everything else as it is.** The existing keys, the D1 OQ1 counts and the canonical JSON stay unchanged, apart from the new fields.

## Constraints
- **Inputs:** work from the published rule text only. You have no hidden cases.
- **Out of scope:** the metric tolerances and the D2 bullets of D4; nothing to implement there.
- **Tests:** unit-test every change on synthetic data. Cover a bit-identical BF16 tensor, a differing BF16 tensor, a zero-norm tensor (BF16 and Q8_0), and a non-zero-norm tensor whose error is zero.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update README.md, and AMBIGUITIES.md where relevant.
- **Commit:** one clear message, no attribution trailers. If the commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the test count and result;
- the commit hash;
- any new ambiguity.
