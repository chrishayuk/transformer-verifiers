You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md, with the protocol read from the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/db08851/PROTOCOL.md` (sha256 `63cae151fb208522084075824d3192b5c28baa113233f9fc98b54d3355e8e25b`; verify it first). Phase 1 rules apply in full.

## This run: implement decision revision D9 and its clarification
Read the snapshot's section "Decision revision D9" in full, including the clarification at its end. Implement every rule in it. In summary:

1. **One status, three categories.** Every non-comparable D2 outcome is `invalid_comparison`. Each reason carries `category` (`unsupported`, `contradiction` or `unresolved`), `field`, and where it applies `key_path` and a `message`. Unsupported configurations are never worded as malformed or contradictory.
2. **Expected refusals versus checker errors.**
   - **Expected refusals** are detected by explicit checks **before** anything can raise. They are never inferred from an exception.
   - **Unexpected exceptions** (in the read-back, the pins or reference construction) produce a distinct status, `checker_error`, with the exception type and message, and no metrics. A `checker_error` must never be reported as, or satisfy, `invalid_comparison`. Do not catch exceptions broadly in order to report `invalid_comparison`.
3. **Unsupported for this campaign, detected before reference construction:**
   - an authority that declares `rope_parameters`;
   - a non-null authority `rope_scaling`;
   - an authority whose `layer_types` marks any layer sliding while `sliding_window` is null;
   - any non-null authority `sliding_window`, including one disabled by `use_sliding_window: false`.

   The sliding-layer-with-null-window case currently reaches a cache-pin exception; it must now be refused explicitly first.
4. **Unresolved:**
   - missing geometry, or other computation-relevant values, never inherited unless the admitted SPEC permits it;
   - a missing `head_dim`;
   - `attention_multiplier` or `query_pre_attn_scalar`.
5. **`key_path`** on every must-be-absent violation and every unknown-key report: the canonical path to the specific key, built from the parsed structure, never from message text. One reason per offending key when there are several. Document the field.
6. **Read-back limits:** record them in AMBIGUITIES.md and README:
   - the read-back checks one direction only, and the guarantee rests on the reference being built from the authority;
   - `dtype` is left to its pin;
   - the `scaling` and `inv_freq` checks confirm internal consistency only, and the RoPE convention probe is the independent check.
7. **Reproducibility settings** stay recorded. Pin one only where you can show it matters; no universal thread count.

## Constraints
- **Inputs:** no hidden cases. Never read LARQL source or look for the real container. D6 and the metric aggregate interface stay out of scope.
- **Tests:** unit-test every rule on synthetic data. Include:
  - each unsupported case, with its category and field;
  - a sliding layer with a null window refused before construction;
  - several forbidden keys giving several reasons with distinct `key_path`s;
  - an injected unexpected exception giving `checker_error`, not `invalid_comparison`.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update AMBIGUITIES.md (AMB-020, -021, -022, -023 and -026 as decided by D9) and README.md.
- **Commit:** clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the reason schema;
- the test count and result;
- the commit hashes;
- any new ambiguity.
