You are the reference-checker agent for LARQL-VERIFY-001. Your standing brief is BRIEF.md, with one change: the protocol is the fixed snapshot `/Users/christopherhay/chris-source/transformer-verifiers/isolation/snapshots/723d5ff/PROTOCOL.md` (sha256 `edd3933fb1a862481bc6482241bc46896990d9d38c59b70453478290feb7cc5e`; verify it first). Phase 1 rules apply in full. In particular, you never see LARQL's Qwen3 container or logit dumps, and you do not run the T3 pilot.

## This run: implement decision revision D7, the reference-side D2 comparability check
Read the snapshot's sections "Decision revision D2", "D3" and "D7" in full. Also read SPEC revision 4 §17 (`../specs/vindex3-container/SPEC.md`, sha256 `8f3f7c2b…`), which is admitted for the execution-surface fields. Then build:

1. **A configuration comparator.**
   - Inputs: a container's `index.json`, its `system_graph.json` and its tensor shapes, plus an authority `config.json`. The authority is the pinned upstream file, or a stand-in passed explicitly and recorded as synthetic (D3 question 17).
   - It compares every computation-relevant field per SPEC §17.7 and D3's type-aware equality: the authority value is converted from its JSON text to the SPEC-declared type by round-to-nearest-even, then compared for exact equality, with no tolerance. That covers the D7 class 2 derivations, and the §17.1 rules on keys that must be absent and unknown keys.
   - Output: `comparable` or `invalid_comparison`, with a field-by-field table and any unresolved assumptions. A head-split mismatch is a mismatch even when the products are preserved (D3 question 16).
2. **Reference read-back.**
   - After the reference model is constructed, read back its effective configuration and compare it with the authority, through an **explicit, documented mapping of equivalent representations** (D7). Any unmapped or differing value makes the run invalid.
   - Build the expected per-layer spans from the reference's resolved `layer_types` and `sliding_window`.
3. **Reference runtime pins** (D7): set each one explicitly, assert it after construction, and record it in the run record.
   - eager attention;
   - explicit f32 and f64, with torch's default dtype pinned;
   - the AMB-013 f64 patch rebuilding the RoPE inverse-frequency table in f64, recorded by sha256;
   - weight tie: shared storage, and decoded head equals decoded embedding;
   - the `kernels` package not importable, and `use_kernels=False`;
   - DynamicCache from empty, with explicit absolute position ids;
   - eval mode;
   - float32 matmul precision, thread count and deterministic settings recorded.
4. **Gating.** E2 and E3 metrics are computed only after the comparator, the read-back and the pins all pass. Otherwise the result is `invalid_comparison` with no metrics.

## Constraints
- **Inputs:** work from the snapshot, SPEC revision 4, the pinned `config.json`, ggml, and the installed `transformers` and `torch`. No hidden cases. Never read LARQL source. Never look for the real container.
- **Tests:** test on synthetic containers you build from SPEC (with stand-in authorities), and on the upstream checkpoint (read-back and pins only). Include:
  - a matching control;
  - one mismatch per field class;
  - a head-split mismatch with equal products;
  - an unmapped read-back key;
  - each pin failing its assertion.
- **Out of scope:** D6 and the metric aggregate interface are a later run. Do not implement them here.
- **Suite:** run the full suite with `.venv/bin/python -I -m unittest discover -s tests -v` and report the count honestly.
- **Records:** update AMBIGUITIES.md and README.md.
- **Commit:** one or more clear commits, no attribution trailers. If a commit is refused, stop with the changes staged and say so. Do not push.

## End with a report
Include:
- the changes, file by file;
- the read-back mapping table;
- the test count and result;
- the commit hashes;
- any new ambiguity.
