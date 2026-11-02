# larql-verify (development workstream, D15)

**DEVELOPMENT ONLY.** Under decision revision D15, Qwen3-0.6B is the development reference model and is retired as the
LARQL-VERIFY-001 blind subject. Nothing here is blind acceptance evidence. Ingestion here is `content_valid` only,
never `execution_authenticated`. There are no acceptance thresholds, and T3 is not used.

## What it does

`larql_verify.py report` is the single command: one model, one report. It writes `runs/<suite>/REPORT.md` and
`report.json`, `e1.json`, and one directory per case.

1. **Identities.** The upstream snapshot is checked against its pinned hashes. The container is checked file by file
   against `evidence/L1/container-q8_0.sha256`. The LARQL binary's hash is recorded and compared with the L1 baseline
   binary.
2. **Container integrity.** The validating reader opens the container, with every digest checked.
3. **Configuration.** The pinned `config.json` is compared with the container, using the comparator and gate.
4. **E1, once per model.** Every executed tensor of the container against the BF16 checkpoint, through `refcheck.e1`:
   - **exact storage:** unquantised tensors, reported as bit identity;
   - **lossy Q8_0:** max |Δw|, relative Frobenius error and the counts against T2. PROTOCOL.md expects this encoder to
     exceed T2, and the bound is not widened;
   - **T2 attribution:** exceedances split into flushed (zero-scale) and non-zero-scale blocks, and T2 applied to a
     simulated ggml-style encoding of the same weights. The simulation is not a run of ggml and changes no weight used
     anywhere else.
5. **Per case.** References and LARQL as below, then:
   - **E2:** LARQL against the f32 reference on the same decoded weights;
   - **E3:** LARQL against the f32 reference on the BF16 checkpoint;
   - **drift (context only):** the decoded-Q8_0 reference against the BF16 reference, with no LARQL involved;
   - **f64 diagnostic:** LARQL and the f32 reference, each against a native-f64 reference on the decoded weights,
     computed in the harness in binary64 because `refcheck.metrics` compares float32 only. It is descriptive: no
     threshold, and T3 is not used.

   LARQL runs `vindex3 exec --backend production-q8 --representation-source stored --logit-dump` through
   `refcheck.ingest`, which runs, verifies and extracts in the pinned environment.

Each comparison reports max |Δlogit|, RMS, D_KL(P_ref ‖ P_cand) in nats, top-1 disagreements and, for E2, E3 and drift,
the non-comparable positions. The verdict is `MEASURED`, `INCOMPLETE` or `EXECUTION_ERROR`.

Cases come from `prompts/suite-v1.json`: prose, code, structured data, several scripts, digits, the chat format with
special tokens, a repeated passage and a repeated word (long-range and degenerate attention over the KV cache), a
two-token edge case and a 2,048-token sequence. The suite was written for coverage of input kinds. It is not a
held-out or adversarial set.

`larql_verify.py compare --n-tokens N` is the diagnostic ladder: the first N tokens of the snapshot's `LICENSE`, E2 and
E3 only, in `runs/nNNNN/`.

## Running it

```sh
./vendor.sh                     # export refcheck from checker/ at e505afc (read-only; checker/ is never modified)
../../checker/.venv/bin/python -I larql_verify.py report                         # about 35 minutes
../../checker/.venv/bin/python -I larql_verify.py report --cases short-2,prose-en  # a subset
../../checker/.venv/bin/python -I larql_verify.py compare --n-tokens 16
```

LARQL is built at `2536bb79` in `~/chris-source/larql-l1-2536bb79` with `cargo build --release --locked -p larql-cli`.
The rebuild on 2026-11-01 reproduced the L1 baseline binary exactly: `4d80dd42…`.

## Encoder attribution

`attribute_encoder.py`, after `ggml_shim/build.sh`, runs the f32 reference on four encodings of the same weights, to
separate LARQL's encoder from Q8_0 itself. It does not run LARQL or write a container, and it does not change
`runs/suite-v1`. Results are in `runs/attribution-v1/REPORT.md`, along with the repeated-word probe, which is
`report --suite prompts/repetition-probe-v1.json`.

## Measuring another LARQL

`report` and `compare` measure the L1 baseline by default. `--larql`, `--larql-commit`, `--container` and
`--container-hashes` point them at something else, with `--out` keeping its results apart. The first use is the corrected
Q8_0 encoder: `evidence/q8-encoder-candidate/RECORD.md`, with results in `runs/candidate-ad82acba/`.

## The contract verifier

`larql-verifier contract --contract Q8_0_T2 --container <dir> --source <checkpoint>` answers one question with one JSON object
(`larql-verify-contract/1`). It is what LQL's `VERIFY REPRESENTATION` runs: set `LARQL_VERIFIER` to this file. The measurement
is `refcheck.e1`, against a checkpoint verified by its pinned hashes, so today it can only evaluate Qwen3-0.6B. Nothing in it
imports or runs LARQL, and it writes no file. On the two containers: the L1 baseline is `violated` with 57,634 elements over
T2, and `q8enc-ad82acba` is `satisfied` with 0. Those match E1 in `runs/suite-v1` and `runs/candidate-ad82acba`.

## Development overrides

**None are active.** The harness uses `refcheck` exactly as pinned, at checker `e505afc`.

| ID | What | Status |
|---|---|---|
| DO-1 | Accepted the real `representation:` line suffix `  objects from a compiled pack: 1/4`, which checker `c2070c3` refused (AMB-033 whole-line reading against spec §8.3.3.5's "contains") | **Retired 2026-11-02.** The checker was fixed under D15 clarification 1 (`e505afc`, audited and pinned). Corpus revision 9 is 79/79 across scoring runs 10 and 11. The 16-token diagnostic was rerun without overrides: ingestion accepted, the dump was bit-identical to the DO-1 run (`a42f7ff6…`), and the measurements were unchanged. The 128, 512 and 1,024-token rungs were then rerun on `e505afc` with no overrides: all three dumps and all reference arrays are bit-identical to the DO-1 runs (compared by SHA-256), and the E2, E3 and drift summaries are identical. The DO-1 records remain in git history at `da70566` |
