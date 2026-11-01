You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md. Read the protocol from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/932de33/PROTOCOL.md` (sha256 `78f497892990d3ecb96160d5ccc042924ae91bc5cd4bd5cc78668c30b45c5968`), and verify that hash first. The admitted logit-dump specification is in the same snapshot as `LARQL-LOGIT-DUMP-SPEC.md` (sha256 `5ad44e331be364300597692ec69e1fd5aafb35190275cfdb488e4d1bb91ad2ec`). Phase 1 rules apply in full.

## This run: Phase 3 ingestion (D13, workstream 2)
Read these in full:
- "Decision revision D13";
- D12, with clarifications 1–3. Clarification 2 admits the specification and gives its scope; clarification 3 says a damaged dump is refused as a whole;
- the "Baseline" section: the command, the pinned environment and the run-acceptance rule;
- the admitted specification. Its §2 command surface, §3–§7 format and stdout, and §8.3 reader and acceptance procedure, including canonical `--tokens` and deleting both files first, are normative for this run.

Implement, in a new module (for example `refcheck/ingest.py`):

1. **A runner, for Phase 3.** It takes:
   - a path to a LARQL executable;
   - the container path;
   - the frozen token manifest: token ids and their SHA-256;
   - an output path.

   It then:
   - builds **exactly the conforming argv** from the specification and Baseline, with canonical `--tokens`, each flag once, nothing else;
   - deletes any old dump and sidecar, and confirms both are absent;
   - launches the process under exactly the pinned environment;
   - captures the exit status, stdout and stderr;
   - writes a **provenance record**. That record holds every item D12 lists: the token-id SHA-256, the full argv, the full environment, the exit status, the model and container identity, and the output file's SHA-256. It also holds the sidecar's SHA-256, the start and end times, and the stdout lines the specification's acceptance procedure needs.
2. **A verifier and extractor.** It takes:
   - the provenance record;
   - the dump and sidecar;
   - the frozen token manifest;
   - the expected container identity;
   - the preregistered positions.

   It **verifies everything before extracting any row**, under every condition of the specification's §8.3 reader procedure, and refuses the whole input with explicit reasons on any failure. That includes:
   - a non-zero exit;
   - a missing or wrong stdout line, including `projection plans:` showing only the kernels the Baseline permits;
   - argv that is not exactly conforming, or non-canonical tokens;
   - an environment that is not exactly the pinned set;
   - a size that is not exactly 4·N·V;
   - a sidecar that disagrees with the record (positions, vocab, layers, engine, `max_format_env`);
   - a file hash that disagrees with the record;
   - a token-id hash that disagrees with the frozen manifest;
   - a container identity mismatch;
   - modification times earlier than the run start;
   - positions out of range.

   Only then does it read the rows at the preregistered positions (little-endian f32, row i = position i, column j = token id j). It returns a candidate logit array and a candidate record that the existing T3 evaluator and `check_comparable` accept unchanged. That record binds the token ids, their hash, the positions, the container identity and the output hash, so it cannot be substituted from a different execution.
3. **Substitution resistance.** Show by test that each of these is refused:
   - a dump or sidecar from a different run;
   - a record from a different run;
   - a record whose token manifest differs;
   - a dump whose bytes were altered after the record was written.

## Tests: synthetic only
- Use a **stub executable** that you write, inside the checker tree. It imitates the specification's documented behaviour: good runs, a non-zero exit, a partial file ending on a row boundary and one ending mid-row, a stale file left in place, a missing stdout line, a `BlasF32` plan, a wrong sidecar, and ignored-but-accepted flags.
- **Never** invoke a real LARQL binary, never read LARQL source, and never touch the real container, real logits or held-out data.
- **Test one complete path:** stub run, then ingest, then `evaluate_t3` on synthetic references.

## Constraints
- **Scope:** change nothing else. No change to T3, `ulp₃₂`, the outcome rule, the reference numerics, the comparability gate, the metrics or the f64 guard.
- **Ambiguity:** where the specification leaves something open, choose the fail-closed reading, and record it in AMBIGUITIES.md.
- **Suite:** run `.venv/bin/python -I -m unittest discover -s tests -v`. Report the count before and after, honestly.
- **Records:** update README (a new section with the runner, the record fields, the verifier's refusal codes and the extractor's output) and AMBIGUITIES.md.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the provenance record fields;
- the refusal codes, each mapped to the specification clause it enforces;
- the extractor's output;
- the substitution tests;
- the test counts;
- the commit hashes;
- any new ambiguity.
