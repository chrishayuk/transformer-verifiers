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
./vendor.sh                     # export refcheck from checker/ at c2070c3 (read-only; checker/ is never modified)
../../checker/.venv/bin/python -I larql_verify.py compare --n-tokens 16
```

LARQL is built at `2536bb79` in `~/chris-source/larql-l1-2536bb79` with `cargo build --release --locked -p larql-cli`.
The rebuild on 2026-11-01 reproduced the L1 baseline binary exactly: `4d80dd42…`.

## Development overrides

| ID | What | Why | Resolution |
|---|---|---|---|
| DO-1 | Accepts the stdout line `representation: Q8_0  source: stored  objects from a compiled pack: 1/4`, exactly that string and no other | Checker `c2070c3` requires whole-line equality with `representation: Q8_0  source: stored` (AMB-033). The admitted spec §8.3.3.5 requires stdout to *contain* it. Pinned LARQL always appends the count (`exec.rs:97`), and the third-party fixture recorded the same suffix (`THIRD-PARTY-CHECK.md` §7.3). Without DO-1, every real run is refused | Owner decision. The checker needs the spec's reading and a hidden test with the real line. The stub was written from the spec text, so it never printed the suffix |

Every override that is applied is recorded in `report.json` under `stages.ingestion.dev_overrides`.
