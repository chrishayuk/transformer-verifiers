# Freeze-readiness review: LARQL-VERIFY-001, gates G1–G4

Independent reviewer, 2026-10-30. This review is read-only. LARQL is at HEAD `ff364ba638b8`.

## Snapshot check

`shasum -a 256 -c SNAPSHOT.sha256` passed for all five files: AUDIT.md, CAPABILITIES.md, PROTOCOL.md, TRUST-BOUNDARY.md and draft.json. PROTOCOL.md is `6cf73afd…`; draft.json is `18878341…`. This verdict applies only to those hashes.

## Verdict: **REVISE AND RE-REVIEW**

None of G1–G4 is satisfied. Every gap can be repaired without a redesign.

I did not choose BLOCKED. The core ambiguities are fixable:

- The Q8_0 block decode is settled by an authoritative external source: ggml's reference, `ggml-quants.c`, and gguf-py 0.18.0 `gguf.quants.Q8_0`.
- The container framing, the tensor naming and the role policy are not ambiguities in a public spec. They are LARQL's own format, and it has no spec. Only LARQL can be the authority for its own container. That authority has to be published and made admissible (see C3). Until then, any checker would have to read LARQL source, which breaks G2.

## Gate-by-gate

| Gate | Status | Basis |
|---|---|---|
| **G1** Freeze integrity | **REPAIRABLE GAP** (nothing exists) | transformer-verifiers is not a git repo (`git rev-parse`: "not a git repository"). There is no manifest and no check outside the agent's write scope. The template it cites does not enforce anything: `ai-math-researcher/tools/manifest_check.py:8-18` checks only that outputs exist and parse, and the root `FREEZE.sha256` fails today (`./README.md: FAILED`). The tamper tests are a plan. Nothing has been run. |
| **G2** Independence | **REPAIRABLE GAP** | The roles are documented. Isolation has not been demonstrated. Format knowledge needed for A1, E2 and E3 exists only inside LARQL: segment framing (`format/vindex3/encode/segment.rs:1-14`, a code comment; `docs/vindex3-format.md` §6.1 has no byte layout), the relative-name → HF-key mapping (`verify.rs:6-8` calls it unsolved), the role policy that decides which tensors are Q8_0 (`represent/policy.rs:280-294`), and dtype labels. The protocol bans "LARQL's own documentation", so even a LARQL-written spec is currently inadmissible. There is also no outside way to get LARQL's decode (see A1 below). |
| **G3** Re-audit | **REPAIRABLE GAP** | The audit's facts hold (see the spot-check table). But the tree is dirty, so no clean freeze SHA exists. CAPABILITIES.md still carries the rows the audit marked WRONG ("reference dequantizer" and `--backend production`). PROTOCOL cites `verify.rs:20-24`; the refusal is at `:22-32`. |
| **G4** Numerical contract | **REPAIRABLE GAP** | The protocol does not fix a subject. The baseline still proposes gemma3-4b-it plus a second family, and NVFP4 plus a K-quant (PROTOCOL:92-95, draft.json:10-11), against G4's "one checkpoint, one encoding". The Qwen3-0.6B / Q8_0 proposal exists only in AUDIT.md. Its upstream weights are not local. All tolerances are "TBD". The audit's reconstruction bound is unsound for LARQL's actual encoder (below). |
| **A0** Analytic cases | **SATISFIABLE**, list needs editing | Exact derivation is easy for Q8_0: the decode `q·d` is an exact f32 product. The protocol's generic boundary list is mostly vacuous for Q8_0 and should be replaced by the format-specific list below. |
| **E1** | **Defined; tolerance missing** | Well-defined against upstream bf16 (bf16 → f32 is exact). It still needs a per-format tolerance rule and an encoder model (see C5). |
| **E2** | **Ill-defined as written; runnable only after changes** | It needs (i) an independent decode of the pack, which depends on G2; (ii) the checker loading those weights into a reference Qwen3 forward pass; (iii) matched execution mode. LARQL can only emit teacher-forced, one-token, KV-cached decode (`teacher_force.rs:66-71`), so A2's "both prefill and decode" cannot be met. The value of the tolerance multiplier `c` needs a pilot, and the protocol has no pilot provision. |
| **E3** | **Defined; acceptance conflated** | A2 "Accept when every metric within tolerance" (PROTOCOL:159) makes model acceptability a Stage A pass condition. That contradicts the two-verdicts section (PROTOCOL:47-49). The same conflation is in A1 (PROTOCOL:110-113). |

**Invalid comparisons.** PROTOCOL:148 rejects mismatched comparisons explicitly, which is good. Two problems remain:

- The precondition list omits things that change arithmetic:
  - the container digest
  - the backend arm
  - the `LARQL_*` environment variables: 275 distinct `"LARQL_*"` literals exist in `crates/`, and the sidecar records only `LARQL_CPU_MAX_FORMAT`
  - thread count
  - which tensors are quantised
- LARQL's sidecar records no token IDs, no config and no digest (`teacher_force.rs:112-131`). The checker's harness must therefore supply and record all of these. The protocol does not say so.

## Spot-checks (performed myself)

| # | Audit claim | Result | Evidence |
|---|---|---|---|
| 1 | HEAD = `ff364ba6`; tree dirty, 26 entries; `d8a7d730` is an ancestor | CONFIRMED | `git rev-parse HEAD` → `ff364ba638b8…`; `git status --porcelain \| wc -l` → 26 (2 M, 24 untracked gw-car-1b files); `merge-base --is-ancestor` OK |
| 2 | "Reference dequantizer" is mis-cited: `:145` is about bf16-zlib, `:281` is LARQL's own FP8 code | CONFIRMED | `docs/represent-codec-contract.md:145` (raw-bf16 control); `:281` "bit-exact to `fp8_finegrained::dequantize_into`" = `crates/larql-models/src/quant/fp8_finegrained.rs:216` |
| 3 | LARQL's Q8_0 encoder differs from ggml in 10 of 544 bytes | CONFIRMED, and I traced the cause | `represent/kquant_conformance_tests.rs:197-205`. The represent path uses `larql_models::quant::ggml::quantize_q8_0` (`kquant.rs:200-203` → `q4_common/mod.rs:52` → `quantize.rs:50-73`). That calls `half.rs:43-60` `f32_to_f16`, which **truncates** the mantissa (`mant >> 13`) and **flushes to ±0** any value below the f16 normal range. ggml and gguf-py round to nearest-even and keep subnormals (`d.astype(np.float16)`). |
| 4 | `--backend production` silently manufactures Q8 above L2 size; capped only by `LARQL_CPU_MAX_FORMAT=bf16` | CONFIRMED | `opplan/exec/cpu/physical.rs:478` (`elements*BF16_BYTES >= compact_threshold_bytes() && q8_permitted()`); `:797-806` (sysctl `hw.perflevel0.l2cachesize`); `:684-689` (cap). The arm is further switched by `LARQL_CPU_ARITHMETIC` (`:243,265`) and `LARQL_KQUANT_EXEC` (`:693,757`). |
| 5 | Logit dump: no prefill path, no container digest | CONFIRMED | `vindex3_cmd/teacher_force.rs:66-71` (one `session.step(token)` per position); sidecar `:112-131` holds engine, layers, positions, vocab, timings and `max_format_env` only. Token IDs are not recorded either. |
| 6 | `manifest_check.py` does not hash; root `FREEZE.sha256` fails | CONFIRMED | `tools/manifest_check.py:8-18`; `shasum -c` → `./README.md: FAILED` |
| 7 | `check_supported` always returns `Err` | CONFIRMED | `crates/larql-factory/src/build/stages/verify.rs:22-32` |
| 8 | Q8_0 GEMV accumulates in f32, element by element, blocks in order | CONFIRMED | `crates/larql-compute/src/cpu/kquant_gemv.rs:90-97` |
| 9 | Compilable K-quants are Q4_K, Q6_K, Q8_0 | CONFIRMED | `represent/kquant.rs:109` |
| 10 | Qwen3-0.6B upstream not local; container has no revision | CONFIRMED | `~/.cache/huggingface/hub` has only Qwen3-4B and Qwen3.8-27B; `qwen3-0.6b.vindex3/index.json` has no revision field |
| 11 | Q8_0 bound `\|w−q·d₁₆\| ≤ d₁₆(½+127·2⁻¹¹) + 127·2⁻²⁵` | **REFUTED for LARQL's encoder**; nearly right for ggml's | See below |

**My check of the bound** (numpy simulation, 20,000 blocks of 32 Gaussian values per scale):

- **Round-to-nearest f16, ggml/gguf encoder.** No violations at σ = 0.02, 2e-3, 1e-4 and 1e-6. A rigorous version needs an extra d₁₆·2⁻¹² term, because the ½ term is really d₃₂/2, not d₁₆/2. The correct bound is d₁₆(½ + 2⁻¹² + 127·2⁻¹¹), plus the subnormal term.
- **LARQL's truncating encoder.**
  - At σ = 0.02: 28 of 20,000 blocks violate the bound, worst ratio 1.05.
  - At σ = 0.05: 40 of 20,000, worst 1.05.
  - At σ = 2e-3: 19,940 of 20,000, worst ratio about 2045.
- **Why LARQL's encoder breaks it.**
  - Truncation doubles the scale term to 127·2⁻¹⁰.
  - Any block with amax < 127·2⁻¹⁴ ≈ 7.75e-3 gets d₁₆ = 0, so the whole block decodes to zero.

**What this means.** An E1 tolerance derived from the published spec will flag LARQL. Under the two-verdicts rule, that is a correct finding about LARQL, not a checker failure. However, the audit's "encoder model" assumption is exactly the kind of knowledge that lives only in LARQL source.

## A0 boundary cases for Q8_0

**Non-vacuous:**

- **Code extremes:** q = 127, q = −128 (−128 is valid in the format, though a conforming encoder never emits it), and q = 0.
- **Scale d:**
  - +0 and −0, which give signed-zero products and must be compared as bit patterns
  - the smallest and largest f16 subnormal
  - the smallest normal
  - 65504
  - a negative d (legal bits; never produced by an encoder)
  - +inf, giving ±inf, and NaN when q = 0
  - NaN
- **Layout:** little-endian f16 byte order, int8 sign interpretation, and block/row ordering.
- **Encoder-side only** (needed for E1 fixtures, not for decode):
  - rounding ties of x·(1/d): roundf rounds half away from zero; numpy's `round` rounds half to even
  - f16 rounding of d
  - amax = 0
  - d in the f16 subnormal range
  - d overflowing to inf
  - NaN or inf inputs

**Vacuous for Q8_0:**

- rounding ties in *decode*: the product is exact
- minimum or offset scales: Q8_0 has none
- sub-block scales and nibble order
- subnormal or non-finite *codes*: codes are int8
- saturation of codes under a conforming encoder: |x/d| ≤ 127 by construction

## Internal inconsistencies

1. **Baseline vs. G4.** The baseline names two subjects and two encodings, NVFP4 and a K-quant (PROTOCOL:92-95; draft.json:10-11). G4 requires one checkpoint and one encoding. The audit shows that NVFP4's pack layout is LARQL-only.
2. **A1/A2 vs. "Two separate verdicts".** A1 and A2 make tolerance compliance an acceptance condition, which contradicts PROTOCOL:47-49.
3. **A1's bit-identity requirement.** A1 requires "bit-identical to LARQL's decode", but LARQL exposes no decoded-weights artefact. The vindex3 subcommands (`vindex3_cmd/mod.rs`) include no tensor dump. For Q8_0 the decode is unique given the bytes. So the requirement is either redundant (checker decode vs. spec) or untestable from outside without a LARQL change.
4. **A2 corpus.** "Both prefill and decode" (PROTOCOL:156) cannot be met through LARQL's only logit interface.
5. **Backend.** The proposed backend "CPU `production`" (PROTOCOL:95; draft.json:13) does not bind a compiled pack, and it manufactures Q8 at load. It needs to be `production-q8` with a pinned environment.
6. **Banned documentation.** PROTOCOL:72 bans LARQL documentation as a source. For LARQL's proprietary container there is no other source, and the protocol does not acknowledge this.
7. **Tolerance timing.** "Tolerances before measurement" conflicts with the pilot that E2's `c` needs. Nothing provides for that pilot.

## Minimum changes to reach READY

### Blocking the freeze

| # | Change | Owner |
|---|---|---|
| B1 | Build the G1 lock and run the 9 tamper tests from AUDIT:104-115 as the agent role, with each test blocked at the outside point. The lock: put transformer-verifiers in git with a protected remote and CODEOWNERS, add a CI or out-of-project hook that recomputes `FREEZE.sha256` from a tagged commit, and name the human reviewer. | Human/user |
| B2 | Pick the subject and pin the freeze SHA. Decide whether Qwen3-0.6B may be downloaded or the subject is OLMo-2-1B. Pin the HF revision and per-file SHA-256. Pin a **clean** LARQL commit. | Human/user |
| B3 | Publish a byte-level spec for the vindex3 segment framing, `index.json`, tensor table, dtype labels, row orientation and Q8_0 blocking, the relative-name → HF-key map for the subject, and the role policy (which tensors are quantised). | LARQL change |
| B4 | Make the B3 spec admissible. Amend the "no LARQL documentation" rule: LARQL's published container spec is admissible *for container framing only*. It is never admissible for numerical semantics, which come from ggml / gguf-py, declared in the trusted base. | Protocol edit |
| B5 | Replace the baseline and backend with exactly one subject, Q8_0 only, and `--backend production-q8 --representation-source stored`. Pin `LARQL_CPU_MAX_FORMAT=bf16`, `LARQL_KQUANT_EXEC`, `LARQL_CPU_ARITHMETIC` and the worker count. Record the full `LARQL_*` environment. Apply the change in both PROTOCOL.md and draft.json. | Protocol edit |
| B6 | Write tolerance rules into the protocol. (a) Bit-exact decode against the spec. (b) An E1 per-element bound derived from the **ggml reference encoder**, in its corrected form d₁₆(½+2⁻¹²+127·2⁻¹¹) + 127·2⁻²⁵. The protocol should state in advance that LARQL's truncating, flush-to-zero encoder may exceed it, and that this would be a model-acceptability finding. (c1) The form of the E2 rule, plus a preregistered pilot on a different checkpoint to fix `c`. (c2) E3 is reported only, or given a policy threshold. | Protocol edit, plus a human decision on c2 |
| B7 | Restrict E2/E3 to teacher-forced KV-cached decode. Add container digest, token IDs, backend arm and environment to the preconditions, all recorded by the checker's harness. Drop "prefill" or mark it out of scope. | Protocol edit |
| B8 | Separate acceptance from tolerance in A1/A2, so tolerance exceedance is reported, not failed. Redefine A1's "bit-identical to LARQL's decode" as "decode of the stored bytes per spec", with LARQL agreement observed through E2 (or add a LARQL decoded-tensor dump). | Protocol edit (or LARQL change) |
| B9 | Replace A0's generic boundary list with the Q8_0 list above, marking the vacuous items. | Protocol edit |
| B10 | Correct CAPABILITIES.md: the reference-dequantizer row, the interface row, the Metal test count, and `vindex3 verify`. Also fix `verify.rs:20-24` → `:22-32`. | Protocol edit |

### Can wait until after the freeze (or G5–G9)

- A LARQL container digest and prefill path in the logit dump. The harness can record the digest instead.
- A LARQL-side fix or documentation of the truncating `f32_to_f16`. That is a finding to report, not a precondition.
- The Python binding coverage, and the NVFP4 and Q4_K follow-on subjects.
- G5–G9 as already listed.

After B1–B10, a new snapshot and a fresh review are required.
