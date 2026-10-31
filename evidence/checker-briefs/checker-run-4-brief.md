You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md in this repository, and all its rules still apply. Phase 1 rules still apply: nothing here is Stage A evidence, and you do not see LARQL's container or logit dumps.

## This run: implement decision revision D1

The protocol owner has decided several ambiguities you logged. Read `../protocols/LARQL-VERIFY-001/PROTOCOL.md`, section "Decision revision D1 (2026-10-31)", in full. It is now part of your requirements. Then bring the checker into line with it:

1. **OQ1, T2's domain** (your AMB-010). Every Q8_0 block falls into exactly one of three classes: invalid under the format (the reader rejects it); valid but outside T2's domain (a negative finite, ±inf or NaN stored scale); and valid inside the domain (a finite d₁₆ ≥ 0, ±0 included).
   - The E1 report gives, per tensor, the blocks and elements outside T2's domain, by scale class (negative, +inf, −inf, NaN).
   - Those blocks stay in the inventory. They are never counted as within T2, and never in the T2 exceed count.
   - ±0-scale blocks keep their separate count.
   - The other E1 statistics include every block, and report a non-finite value as non-finite.
   - This replaces your current readings (|d₁₆| for a negative scale; every element exceeding for an infinite scale).
2. **OQ6, non-finite logits** (your AMB-017). A position with any ±inf or NaN logit on either side gets the explicit status `non_comparable`, with the side and the count of each class (+inf, −inf, NaN). It gets no metrics, and is left out of every aggregate. Check that no code path reports it as an agreement.
3. **OQ12, duplicate ownership of a source key.**
   - The reader must reject a container in which two stored tensors, in the representations compared together (one per logical object), yield the same HF key under SPEC §10.1.
   - It must not reject identical content under different keys, or declared logical sharing where no second stored tensor claims the key.
   - Make sure both behaviours are tested.
4. **OQ4, OQ5.** These are scoring rules, not checker behaviour. Your only obligation is that the E1 report is deterministic, and exposes the OQ1 counts and the existing counts as integers that a scorer can compare against a control.

## Constraints

- Work from the published rule text only. You have no hidden cases, and you must not try to find any.
- Do not start D2 work in this run. D2 depends on a container specification revision that has not been admitted.
- Update `AMBIGUITIES.md`: mark AMB-010, AMB-017 and any entry OQ12 touches as decided by D1, quoting the rule. Mark your old readings as superseded; do not delete them.
- Add or adjust unit tests for every change. Synthetic data only.
- Run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count and any failures honestly.
- Commit with a clear message and no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not look for another route. Do not push.

## End with a report

Include:
- what changed, file by file;
- the test count and result;
- the commit hash, or the staged state if the commit was refused;
- any new ambiguity you found, logged in AMBIGUITIES.md.
