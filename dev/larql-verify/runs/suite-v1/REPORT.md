# larql-verify report: suite-v1

**DEVELOPMENT ONLY (D15). Not blind acceptance evidence for LARQL-VERIFY-001. Ingestion is content_valid only, not execution_authenticated.**

- Created: 2026-11-02T19:41:43.236357+00:00
- refcheck: `e505afcf2d81c0262cd1d75ac0a5dd8429a84c5a`; LARQL `2536bb79`, binary `4d80dd42c4b50dd83c35d4a3c2d273e12a95d31dd4816c51ca2323dfc8462322`
- Suite: `prompts/suite-v1.json` sha256 `4d0fdaa4c8fcb43c4f823f617680bbda2aa7a60ea51dff57ba89ce094c828b44`
- KL: D_KL(P_reference || P_candidate), nats; candidate is LARQL (E2, E3, f64 LARQL) or the f32 reference (drift: decoded-Q8_0 against BF16; f64 ref32: f32 against f64)
- Verdict: **MEASURED** (E1 and every case measured)

## Preflight

- identities: verified
- container_integrity: verified
- configuration: comparable

## E1: weight reconstruction

- E1 coverage: complete
- E1 Q8_0 (lossy, 196 tensors): max |Δw| 0.00772, worst error / T2 bound 2.04e+03, elements over T2 57634, rel. Frobenius min/median/max 0.00537 / 0.00549 / 0.00818 (worst model.layers.21.self_attn.k_proj.weight), decode = gguf-py: True
- E1 T2 by cause: zero-scale (flushed) blocks 1118 with 35735 elements over, max amax 0.00772; non-zero-scale blocks over 21295 of 13761442 with 21899 elements over, worst ratio 1.05
- E1 T2 counterfactual, ggml-style encoder on the same weights: 0 elements over, worst ratio 0.952, 0 zero-scale blocks
- E1 exact storage (115 tensors, {'BF16': 115}): all bit-identical: True

## Per case: E2, E3 and the f64 diagnostic

E2: LARQL against the f32 reference on the same decoded Q8_0 weights. E3: LARQL against the f32 reference on the BF16 checkpoint; drift is the same comparison with the decoded-Q8_0 reference in LARQL's place. f64: max |Δlogit| of LARQL and of the f32 reference from a native-f64 reference on the decoded weights; the ratio is per position, LARQL's distance over the f32 reference's, median over positions.

| case | kind | n | verdict | E2 max|Δ| | E2 RMS | E2 KL max | E2 top-1 ≠ | E3 max|Δ| | E3 KL max | E3/drift top-1 ≠ | f64: LARQL max|Δ| | f64: ref32 max|Δ| | f64 ratio med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prose-en | natural language | 149 | MEASURED | 0.000102 | 8.92e-06 | 1.45e-10 | 0 | 2.26 | 0.0578 | 7/7 | 0.000105 | 2.28e-05 | 4.2 |
| code-python | code | 228 | MEASURED | 0.000351 | 9.93e-06 | 2.92e-10 | 0 | 2.31 | 0.0443 | 1/1 | 0.000279 | 8.36e-05 | 4.4 |
| code-rust | code | 182 | MEASURED | 0.000139 | 1.14e-05 | 1.39e-10 | 0 | 2.7 | 0.0976 | 1/1 | 0.000133 | 3.22e-05 | 4.5 |
| structured-json | structured | 248 | MEASURED | 0.000136 | 8.85e-06 | 9.77e-11 | 0 | 2.38 | 0.0755 | 1/1 | 0.000141 | 3.31e-05 | 4 |
| structured-table | structured | 311 | MEASURED | 0.0007 | 1.01e-05 | 3.03e-10 | 0 | 2.09 | 0.0583 | 4/4 | 0.000163 | 0.000575 | 3.1 |
| multilingual | natural language | 99 | MEASURED | 0.000138 | 1.06e-05 | 2.92e-10 | 0 | 1.96 | 0.0534 | 6/6 | 0.000137 | 4.07e-05 | 4.3 |
| arithmetic | numbers | 220 | MEASURED | 0.000605 | 1.03e-05 | 6.04e-10 | 0 | 2.38 | 0.0835 | 1/1 | 0.000479 | 0.000129 | 3.4 |
| chat-template | chat | 106 | MEASURED | 0.000193 | 1.39e-05 | 1.16e-09 | 0 | 1.69 | 0.054 | 4/4 | 0.000197 | 5.34e-05 | 4.8 |
| kv-copy | KV cache | 344 | MEASURED | 0.000432 | 1.15e-05 | 2.86e-10 | 0 | 2.25 | 0.0448 | 1/1 | 0.00047 | 0.000142 | 3.4 |
| repetition | KV cache | 96 | MEASURED | 0.00183 | 0.000113 | 4.62e-08 | 0 | 2.82 | 0.108 | 16/16 | 0.0016 | 0.000233 | 6.6 |
| short-2 | edge | 2 | MEASURED | 5.91e-05 | 1.01e-05 | 3.05e-11 | 0 | 1.89 | 0.0478 | 0/0 | 6.5e-05 | 1.24e-05 | 4.8 |
| long-2048 | long sequence | 2048 | MEASURED | 0.000879 | 3.26e-05 | 2.57e-08 | 0 | 2.44 | 0.14 | 41/41 | 0.000809 | 0.00111 | 1 |
