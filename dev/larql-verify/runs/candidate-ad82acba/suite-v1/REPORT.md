# larql-verify report: suite-v1

**DEVELOPMENT ONLY (D15). Not blind acceptance evidence for LARQL-VERIFY-001. Ingestion is content_valid only, not execution_authenticated.**

- Created: 2026-11-02T22:52:13.428316+00:00
- refcheck: `e505afcf2d81c0262cd1d75ac0a5dd8429a84c5a`; LARQL `ad82acba`, binary `bbbfd238b2596f85b32aa00f7e16df6a74c036107d8f2238343e5a75e3de3563`
- Suite: `prompts/suite-v1.json` sha256 `4d0fdaa4c8fcb43c4f823f617680bbda2aa7a60ea51dff57ba89ce094c828b44`
- KL: D_KL(P_reference || P_candidate), nats; candidate is LARQL (E2, E3, f64 LARQL) or the f32 reference (drift: decoded-Q8_0 against BF16; f64 ref32: f32 against f64)
- Verdict: **MEASURED** (E1 and every case measured)

## Preflight

- identities: verified
- container_integrity: verified
- configuration: comparable

## E1: weight reconstruction

- E1 coverage: complete
- E1 Q8_0 (lossy, 196 tensors): max |Δw| 0.00485, worst error / T2 bound 0.952, elements over T2 0, rel. Frobenius min/median/max 0.00536 / 0.00546 / 0.00581 (worst model.layers.16.mlp.down_proj.weight), decode = gguf-py: True
- E1 T2 by cause: zero-scale (flushed) blocks 0 with 0 elements over, max amax 0; non-zero-scale blocks over 0 of 13762560 with 0 elements over, worst ratio 0.952
- E1 T2 counterfactual, ggml-style encoder on the same weights: 0 elements over, worst ratio 0.952, 0 zero-scale blocks
- E1 exact storage (115 tensors, {'BF16': 115}): all bit-identical: True

## Per case: E2, E3 and the f64 diagnostic

E2: LARQL against the f32 reference on the same decoded Q8_0 weights. E3: LARQL against the f32 reference on the BF16 checkpoint; drift is the same comparison with the decoded-Q8_0 reference in LARQL's place. f64: max |Δlogit| of LARQL and of the f32 reference from a native-f64 reference on the decoded weights; the ratio is per position, LARQL's distance over the f32 reference's, median over positions.

| case | kind | n | verdict | E2 max|Δ| | E2 RMS | E2 KL max | E2 top-1 ≠ | E3 max|Δ| | E3 KL max | E3/drift top-1 ≠ | f64: LARQL max|Δ| | f64: ref32 max|Δ| | f64 ratio med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prose-en | natural language | 149 | MEASURED | 0.000116 | 1e-05 | 2.03e-10 | 0 | 2.26 | 0.058 | 6/6 | 0.000113 | 2.88e-05 | 4.3 |
| code-python | code | 228 | MEASURED | 0.000134 | 9.93e-06 | 1.31e-10 | 0 | 2.31 | 0.0443 | 2/2 | 0.000221 | 9.51e-05 | 4.3 |
| code-rust | code | 182 | MEASURED | 0.000121 | 1.12e-05 | 2.92e-10 | 0 | 2.7 | 0.0979 | 0/0 | 0.00012 | 3.27e-05 | 4.4 |
| structured-json | structured | 248 | MEASURED | 0.000133 | 9.19e-06 | 1.59e-10 | 0 | 2.38 | 0.0754 | 1/1 | 9.45e-05 | 6.33e-05 | 3.9 |
| structured-table | structured | 311 | MEASURED | 0.000741 | 1.02e-05 | 1.5e-10 | 0 | 2.09 | 0.0583 | 4/4 | 0.000207 | 0.000625 | 3.1 |
| multilingual | natural language | 99 | MEASURED | 0.000175 | 1.21e-05 | 1.31e-09 | 0 | 1.96 | 0.0535 | 4/4 | 0.000178 | 2.29e-05 | 4.7 |
| arithmetic | numbers | 220 | MEASURED | 0.000263 | 9.42e-06 | 9.61e-10 | 0 | 2.37 | 0.0833 | 1/1 | 0.00026 | 7.56e-05 | 3.6 |
| chat-template | chat | 106 | MEASURED | 0.000196 | 1.39e-05 | 9.8e-10 | 0 | 1.74 | 0.0561 | 4/4 | 0.000183 | 6.9e-05 | 4.3 |
| kv-copy | KV cache | 344 | MEASURED | 0.000169 | 1.13e-05 | 1.2e-09 | 0 | 2.21 | 0.0449 | 1/1 | 0.000178 | 0.000141 | 3.5 |
| repetition | KV cache | 96 | MEASURED | 0.000975 | 7.98e-05 | 1.34e-08 | 0 | 2.68 | 0.0878 | 17/17 | 0.000669 | 0.000364 | 5.8 |
| short-2 | edge | 2 | MEASURED | 5.44e-05 | 9.79e-06 | 4.8e-11 | 0 | 1.89 | 0.0479 | 0/0 | 4.71e-05 | 2.18e-05 | 3.1 |
| long-2048 | long sequence | 2048 | MEASURED | 0.000959 | 3.18e-05 | 1.93e-08 | 0 | 2.46 | 0.121 | 47/47 | 0.000333 | 0.00102 | 0.96 |
