# larql-verify report: repetition-probe-v1

**DEVELOPMENT ONLY (D15). Not blind acceptance evidence for LARQL-VERIFY-001. Ingestion is content_valid only, not execution_authenticated.**

- Created: 2026-11-02T21:13:48.626930+00:00
- refcheck: `e505afcf2d81c0262cd1d75ac0a5dd8429a84c5a`; LARQL `2536bb79`, binary `4d80dd42c4b50dd83c35d4a3c2d273e12a95d31dd4816c51ca2323dfc8462322`
- Suite: `prompts/repetition-probe-v1.json` sha256 `6151d9a117fea040eaf3f452ba50f0d52f4fc2d4c77eb58b611afa447cdef0ce`
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
| rep-the-96 | control | 96 | MEASURED | 0.00183 | 0.000113 | 4.62e-08 | 0 | 2.82 | 0.108 | 16/16 | 0.0016 | 0.000233 | 6.6 |
| rep-cat-96 | other word | 96 | MEASURED | 4.67e-05 | 7.44e-06 | 2.83e-11 | 0 | 1.97 | 0.0563 | 1/1 | 4.82e-05 | 1.94e-05 | 4.7 |
| rep-seven-96 | other word | 96 | MEASURED | 0.000399 | 5.02e-05 | 8.61e-10 | 0 | 2.23 | 0.0705 | 0/0 | 0.000547 | 0.000213 | 3.1 |
| rep-zh-96 | other word | 96 | MEASURED | 4.21e-05 | 7.7e-06 | 2.62e-11 | 0 | 1.63 | 0.0366 | 0/0 | 3.64e-05 | 2.27e-05 | 2.3 |
| rep-dash-96 | other word | 96 | MEASURED | 0.000154 | 9.5e-06 | 3.55e-10 | 0 | 1.96 | 0.0502 | 1/1 | 0.000175 | 2.51e-05 | 5.5 |
| cycle-2 | longer unit | 96 | MEASURED | 0.000177 | 7.12e-06 | 4.87e-10 | 0 | 1.98 | 0.0528 | 0/0 | 0.000186 | 1.19e-05 | 4.6 |
| cycle-8 | longer unit | 96 | MEASURED | 0.000177 | 8.17e-06 | 4.87e-10 | 0 | 1.98 | 0.0528 | 1/1 | 0.000186 | 5.68e-05 | 4.4 |
| the-then-prose | persistence | 93 | MEASURED | 0.00183 | 7.55e-05 | 4.62e-08 | 0 | 1.98 | 0.0557 | 9/9 | 0.0016 | 0.000233 | 5.2 |
| rep-the-384 | length | 384 | MEASURED | 0.00183 | 0.000102 | 4.62e-08 | 0 | 3.09 | 0.11 | 87/87 | 0.0016 | 0.000233 | 5.6 |
