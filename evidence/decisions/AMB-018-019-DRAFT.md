# Draft decision records: AMB-018 and AMB-019

**Status: DRAFT, for the protocol owner.** Not in force. Written 2026-10-31 by the coordinating session, under the
D1 discipline:
- each proposal is argued from the protocol, SPEC revision 3 or the T2 derivation;
- the checker's current reading is listed separately and is not used as an argument.

**Not for the reviewer before scoring.** This file quotes the readings the checker took. The independent reviewer
must not read it until scoring run 2 is recorded.

---

## AMB-018. Which selections of representations are "compared together" (D1 OQ12)

**Ambiguity.** D1 OQ12: "Take the representations that are compared together, one per logical object. A reader MUST
reject a container in which two stored tensors there yield the same HF key." D1 does not list the selections.

**Passages.**
- D1 OQ12's own premise: "each source tensor key is owned by exactly one object. The encoder assigns each key to the
  longest covering prefix across objects".
- SPEC §10.1: the forward rule, and "the rule holds for both representations of an object".
- SPEC §10.2: the bijection.

**Readings.**
- **(a)** Only the selection SPEC §7 executes.
- **(b)** (a), plus each uniform encoding (all `@BF16`, all `@Q8_0`, over the objects that have it).
- **(c)** Ownership is per object, not per representation. For every pair of distinct objects, the HF keys derived
  from any representation of one are disjoint from those derived from any representation of the other. Within one
  representation, the keys are unique.

**Proposed: (c).**
- D1 grounds OQ12 in *object* ownership, and the encoder assigns keys to objects, not to representations. So a key
  claimed by two objects is a fault, whichever representations a given comparison happens to pick.
- (c) needs no list of comparisons. That list could grow (E1 against canonical, E2 executed, later campaigns), and
  under (a) or (b) the rule would change silently as it did.
- For this profile, (c) rejects everything (b) rejects. It also rejects a collision between one object's `@Q8_0` and
  another object's `@BF16` that no uniform selection contains.

**Checker's reading** (AMBIGUITIES.md): (b). The proposal is stricter, so adopting it means a checker change, to be
made from this published rule.

**Clarification or change.** A clarification of D1's stated premise. No scored case depends on it: the reviewer
excludes from run 2 any case whose verdict differs between the readings.

---

## AMB-019. A non-finite upstream element inside a block in T2's domain (D1 OQ1)

**Ambiguity.** OQ1 sorts *blocks* by stored scale. A block with a finite scale ≥ 0 is in T2's domain. But an element
of that block can have a NaN or ±inf **upstream** value, so its error is non-finite. The decoded value is always
finite there, since a finite int8 code times a finite f16 scale is finite.

**Passages.** The T2 derivation: ggml's reference encoder, whose input x is assumed finite (and OQ2: the reference
encoder is undefined on non-finite input). D1 OQ1: the domain is defined by the derivation's assumptions; "a non-finite
value is reported as non-finite, not dropped".

**Readings.**
- **(a)** The element counts as exceeding T2.
- **(b)** The element is outside T2's domain at element level. It goes in its own per-tensor count ("non-finite
  upstream elements"), never in the within or exceed counts, and its error appears as non-finite in the floating-point
  statistics.

**Proposed: (b).**
- T2's derivation assumes a finite input, as OQ1 already recognised for scales. An element with no derivation behind
  it can neither satisfy nor break the bound. Counting it as exceeding says the bound failed where it never applied.
- (b) applies OQ1's own reasoning at element level, and keeps the element visible.
- **Consequence for this subject:** none. The OQ2 scan (`evidence/OQ2/`) found no NaN or inf in any upstream tensor.

**Representation of non-finite statistics** (the rest of AMB-019):
- **Proposed:** the integer counts are normative. Non-finite floating-point summaries are written as the strings
  `"inf"`, `"-inf"` and `"nan"` in a canonical JSON report, and are compared by class.
- This follows D1 OQ1 ("reported as non-finite") and OQ4, which compares integers exactly and floating-point values
  only where a recipe predicts them.

**Checker's reading:** (a) for the element, and string encoding for the statistics. Adopting (b) changes one count.

**Clarification or change.** A clarification of OQ1's domain. No result on the subject can depend on it, because
there are no non-finite upstream elements.
