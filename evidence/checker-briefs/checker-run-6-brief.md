You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md in this repository, and all its rules still apply, with one change.

**The protocol is now a fixed snapshot.** Read it from `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/1bfc341/PROTOCOL.md` (sha256 `79795f1889a56b4d6ec34c0558a0f11add329b6f55f5df42789656dc9569c237`; verify it first). The live `../protocols/` path that BRIEF.md names is no longer readable by this session. Phase 1 rules still apply.

## This run: implement decision revision D5
Read the snapshot's section "Decision revision D5 (2026-10-31)" in full, then implement both rules:

1. **AMB-018, source-key ownership.**
   - The reader rejects a container in which a representation of one logical object and a representation of a different object yield the same HF key under SPEC §10.1, across every representation the container declares in `index.json`. It also rejects two stored tensors within one representation that yield the same key.
   - This applies whether or not the objects are executed together.
   - Not prohibited: several representations of one object sharing a key, shared storage, identical content under distinct keys, and declared reuse.
   - This replaces your AMB-018 reading of "executed set plus each uniform encoding". Mark that reading superseded.
2. **AMB-019, non-finite upstream elements.**
   - Inside a block whose stored scale is in T2's domain, an element whose upstream value is NaN, +inf or −inf is outside T2's domain at element level. Report it per tensor by class (`nan`, `inf`, `-inf`), never counted as within T2 or exceeding it.
   - Its error is non-finite in the floating-point statistics, written as strings in the canonical report.
   - Integer counts are normative.
   - Mark your earlier reading (counted as exceeding) superseded.
   - Your D4 note on bit-identical tensors holding inf or NaN is a separate open question. Do not change that behaviour in this run.

## Constraints
- **Inputs:** work from the snapshot's rule text only. You have no hidden cases.
- **Tests:** unit-test both rules on synthetic data:
  - a cross-object collision between different encodings, which must be rejected;
  - one object with two representations sharing keys, which must be accepted;
  - identical content under distinct keys, which must be accepted;
  - each non-finite upstream class inside an in-domain block, with exact counts.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update AMBIGUITIES.md (AMB-018 and AMB-019 decided by D5, rule quoted, old readings superseded) and README.md.
- **Commit:** one clear message, no attribution trailers. If the commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the test count and result;
- the commit hash;
- any new ambiguity.
