# LARQL logit-dump specification: admission record

**Status: ELIGIBLE FOR ADMISSION, awaiting the protocol owner's admission.** Not yet given to the reference checker.

| Item | Value |
|---|---|
| Specification | `specs/larql-logit-dump/SPEC.md`, revision 3, commit `7043f02`, sha256 `5ad44e331be364300597692ec69e1fd5aafb35190275cfdb488e4d1bb91ad2ec` |
| Written from | LARQL `2536bb79` source only, by a specification author who is not the checker |
| Third-party check | `THIRD-PARTY-CHECK.md`: revision 1 ACCURATE WITH CORRECTIONS (`4bce40d`), revision 2 four defects (`bc063f2`), revision 3 **CORRECTIONS CONFIRMED** (`50b71a9`) |
| Fixture validation (D12) | A tiny non-subject Qwen3-shaped fixture, with LARQL built offline into a separate directory. Byte layout confirmed against an independent f64 forward. The D12 acceptance procedure accepted every conforming run and rejected every failure mode tried (partial, stale, lenient or non-canonical tokens, ignored flags, `--bank`, environment, `BlasF32` head). Dumps were bit-identical across runs and at 1, 4 and 12 workers. Fixture repository `~/chris-source/logit-dump-check` (`d53d34c`, `00e071d`, `8ac4338`) |
| Not run | The subject, its containers and Qwen3-1.7B. No real-model logits were produced |
| Isolation | The author's and the third party's tool logs were checked by the coordinating session: no checker, hidden corpus, reference audit or network access |
| Open items carried | OI-1 (no token ids in the dump; harness-supplied), OI-2/3 (stale files, no completeness marker; delete-first and fail-closed rules), OI-5 (extended positions: D12 stress experiment), OI-8 (platform maths library), OI-12 (non-finite values written unchecked; D1 OQ6 at comparison), OI-15 (resource-limited runs at large N; D12) |

Once admitted, the specification is added to the checker's protocol snapshot read-allow list, through a new snapshot and
an isolation re-test.
