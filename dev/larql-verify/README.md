# larql-verify (development workstream, D15)

**DEVELOPMENT ONLY.** Under decision revision D15, Qwen3-0.6B is the development reference model and is retired as the
LARQL-VERIFY-001 blind subject. Nothing here is blind acceptance evidence. Ingestion here is `content_valid` only,
never `execution_authenticated`. There are no acceptance thresholds, and T3 is not used.

## What it does

`larql_verify.py compare --n-tokens N` takes one real model through the whole verifier and writes
`runs/nNNNN/report.json`:

1. **Identities.** The upstream snapshot is checked against its pinned hashes. The container is checked file by file
   against `evidence/L1/container-q8_0.sha256`. The LARQL binary's hash is recorded and compared with the L1 baseline
   binary.
2. **Container integrity.** The validating reader opens the container, with every digest checked.
3. **Configuration.** The pinned `config.json` is compared with the container, using the comparator and gate.
4. **Reference.** A f32 reference runs on the decoded Q8_0 weights, gated by the read-back and the pins.
5. **LARQL.** LARQL runs `vindex3 exec --backend production-q8 --representation-source stored --logit-dump` through
   `refcheck.ingest`, which runs, verifies and extracts in the pinned environment.
6. **Metrics, per comparison.** Each comparison reports max |Δlogit|, RMS, D_KL(P_ref ‖ P_cand) in nats, top-1
   agreement and the non-comparable positions:
   - **E2:** LARQL against the reference on the same decoded weights;
   - **E3:** LARQL against the f32 reference on the BF16 checkpoint;
   - **drift (context only):** the decoded-Q8_0 reference against the BF16 reference, with no LARQL involved.

The verdict is `MEASURED`, `INCOMPLETE` or `EXECUTION_ERROR`.

Tokens are the first N tokens of the snapshot's pinned `LICENSE`, with no special tokens. The ladder therefore uses
nested prefixes.

## Running it

```sh
./vendor.sh                     # export refcheck from checker/ at e505afc (read-only; checker/ is never modified)
../../checker/.venv/bin/python -I larql_verify.py compare --n-tokens 16
```

LARQL is built at `2536bb79` in `~/chris-source/larql-l1-2536bb79` with `cargo build --release --locked -p larql-cli`.
The rebuild on 2026-11-01 reproduced the L1 baseline binary exactly: `4d80dd42…`.

## Development overrides

**None are active.** The harness uses `refcheck` exactly as pinned, at checker `e505afc`.

| ID | What | Status |
|---|---|---|
| DO-1 | Accepted the real `representation:` line suffix `  objects from a compiled pack: 1/4`, which checker `c2070c3` refused (AMB-033 whole-line reading against spec §8.3.3.5's "contains") | **Retired 2026-11-02.** The checker was fixed under D15 clarification 1 (`e505afc`, audited and pinned). Corpus revision 9 is 79/79 across scoring runs 10 and 11. The 16-token diagnostic was rerun without overrides: ingestion accepted, the dump was bit-identical to the DO-1 run (`a42f7ff6…`), and the measurements were unchanged. The ladder runs at 128, 512 and 1,024 tokens used DO-1 on `c2070c3`; their committed records say so |
