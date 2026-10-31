# B3: admission of the container specification

| Item | Value |
|---|---|
| Admitted document | `specs/vindex3-container/SPEC.md`, revision 2, sha256 `3c4feb5e01f2c262e06e1f8579754921089cda46038f17c63cfd42f9d0c5fe50` |
| Written against | LARQL `2536bb79`, by a spec-author subagent (not the reference-checker agent, not the third-party checker) |
| Third-party check | `CHECK.md`: revision 1 ADMIT WITH CORRECTIONS (8/8 spec-only checks pass on the fresh container); revision 2 **ADMIT** (diff limited to the five corrections and two declared additions; no layout statement changed; Phase A rerun byte-identical) |
| Admitted on | 2026-10-30, by adding it to the checker session's read allow-list, write-denied (`isolation/checker-settings.json` sha256 `a4cc2006…`) |
| Isolation re-test | `../ISOLATION.md`, part 3 |

**Scope of admission:** container framing only, as the protocol's trusted base states. Numerical semantics come from
ggml `facdc44a` and gguf-py 0.18.0.

**Known limits, accepted:**
- **The spec is LARQL's account of its own format.** Agreement on framing shows consistency with this document, not
  independent correctness.
- **Its Sources appendix names LARQL file paths, lines and identifiers.** It contains no implementation code; a scan
  found no Rust code.
- **One paragraph describes executor behaviour:** the LM head re-quantised at load. It is there because B3 requirement
  (d) asks which representation the output projection consumes. It gives no detail of LARQL's internal quantiser
  beyond its 64-element block size.
- **Rejection rules were checked only against the values in this container.** No mutated containers were built.
  That belongs to the A4 fault matrix.
- **One cosmetic leftover** (a "(computed)" marker in §8.2) is to be fixed at the next revision. The checker's
  verdict says it is not a condition of admission.

**Gaps the spec records as findings about LARQL (§15):**
- F1: row-major order and block axis are not declared in the container
- F2: endianness and the f16 scale type are not declared
- F3: the per-representation `codec` field is implicitly scoped
- F4: the executed LM head is not recorded in the container
- F5: `head_reuses_embedding` is ambiguous
- F6: why a tensor stays BF16 is recorded only in `candidate.json`

## Revision 3 (2026-10-31)

| Item | Value |
|---|---|
| Admitted document | `specs/vindex3-container/SPEC.md`, revision 3, sha256 `6350e07cff89fb04321ec49ea2e82b14d3893dc7a279d4fd2c899c8db1860a22`. It replaces revision 2 (`3c4feb5e…`) at the same path |
| Written against | LARQL `2536bb79`, by the spec-author subagent (not the reference checker, not the third-party checker). Draft and notes: `evidence/B3/rev3/` |
| Third-party check | `evidence/B3/rev3/CHECK.md` (sha256 `421eed24…`). First draft (`2d525879…`): ADMIT WITH CORRECTIONS C1–C3, 605/605 assertions. Corrected draft (`6350e07c…`): **ADMIT**, 608/608 assertions; the diff is exactly the eight reported hunks; all 26 execution-path claims confirmed |
| Admitted on | 2026-10-31, by copying the checked draft to the path the checker session already reads. The settings are unchanged (`d05ce78f…`), so isolation is unchanged |

**Scope of admission:** container framing as before, plus §17. §17 gives the meanings of the execution-surface
fields of `system_graph.json`, for comparing a declared configuration only (D2). §17.8 is informative. It is evidence
for the execution-path audit, not a format rule.

**Known limits, accepted:**
- **Coverage of D2's 16 fields:**
  - 11 are declared directly. `rms_norm_eps` is stored as f64(f32(x)).
  - 3 are represented only indirectly: `rope_scaling`, `sliding_window` and `tie_word_embeddings`.
  - 2 have no field at all: `use_sliding_window` and `max_window_layers`.

  Whether the indirect and missing fields are enough for D2 is a protocol decision (D3), not part of admission.
- **What exec actually computes with** (§17.8, confirmed):
  - the split-half RoPE pairing is hard-coded;
  - the QK-norm epsilon is the pre-norm epsilon;
  - the residual, projection and logit widths come from tensor shapes;
  - the score scale is rounded to f32.

  Declared but not consumed for this container: the surface `num_kv_heads`/`head_dim`, `head_reuses_embedding` and
  `context_length`.
- **Advisory B1, not a condition of admission:** the S155 location for `LARQL_KQUANT_EXEC` is a describing comment.
  The definition is at `VX/opplan/exec/cpu/physical/projection.rs:436`.
- **Scoring:** corpus revision 2 and the pinned checker `cd49069` were built against revision 2. Revision 3 changes no
  revision 2 normative statement, so neither is affected.

## Revision 4 (2026-10-31)

| Item | Value |
|---|---|
| Admitted document | `specs/vindex3-container/SPEC.md`, revision 4, sha256 `8f3f7c2b50eac2cb3a9172599a7e4ce21792f62169559fa64764d6a3ade85a8f`. It replaces revision 3 (`6350e07c…`) |
| Why | The independent D2 field classification (`evidence/D2-FIELD-ASSESSMENT.md`) found that the RoPE rotation direction was the only computation-relevant item in class 3, with no specified source |
| Change | One normative addition to §17.5: LARQL's rotation for `kind: "rope"`, `x'[i] = a·cos φ − b·sin φ`, `x'[i+d/2] = a·sin φ + b·cos φ`, with `φ = p·θ^(−2i/d)`, per head slice, after the QK norm and the query scale, at the absolute position. Also the "(observed in code)" marker, the B1 citation fix, S155 and S156 |
| Third-party check | `evidence/B3/rev4/CHECK.md` (sha256 `c6cbbfb7…`): **ADMIT**. The diff is exactly six hunks, 25 lines. The formula is confirmed at `kernels.rs:153-156`, and the S156 citations are confirmed. No refutation. The rev 3 script still gives 608/608. The checker did not consult any reference implementation |
| Admitted on | 2026-10-31, with no checker session running. Settings unchanged (`6f293a60…`) |

**Advisory D1, not a condition of admission:** the sentence "other rotary kinds use the same sign convention" should
cite `kernels.rs:165-177` and `:249-267`, and be marked informative.

**Not established by admission:** that the reference rotates the same way. Comparing the formula with the reference
is a separate reviewer task.
