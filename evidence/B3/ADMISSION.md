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
