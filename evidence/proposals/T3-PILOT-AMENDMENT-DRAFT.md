# Proposed amendment: the T3 pilot (draft, not in force)

**Status: DRAFT,** for the protocol owner and the freeze reviewer (G4, G8). It changes nothing until it is adopted into
PROTOCOL.md through the freeze procedure.
- **Phase 1 limit:** preparing the method does not authorise running the pilot. The pilot is part of the frozen
  procedure and runs in Phase 3, after the freeze and before any measurement on the subject.
- **Author:** the coordinating session, 2026-10-31.

## Why amend

The current text (PROTOCOL.md, "The pilot for T3") fixes the form `|LARQL − ref₃₂| ≤ max(c·|ref₃₂ − ref₆₄|,
k·ulp₃₂(ref₆₄))`, a ladder for c and k, and a pilot checkpoint. Phase 1 has since established specific arithmetic
differences between LARQL and the reference (D7 arithmetic assumptions, `evidence/D2-FIELD-ASSESSMENT.md` §8):
1. **RoPE sine and cosine:** binary32, from a binary64 angle in LARQL; binary32 throughout in ref₃₂. Near position
   40,960 the binary32 angle has an ulp of about 0.004 rad.
2. **RoPE inverse frequency:** computed by different routes, `θ^(−2i/d)` against `1/θ^(2i/d)`.
3. **Score scale:** binary32 in LARQL, binary64 in ref₆₄.
4. **RMSNorm epsilon:** `f64(f32(1e-6))` in LARQL, binary64 `1e-6` in ref₆₄.
5. **Summation order:** LARQL's is unknown (Accelerate), the reason for the factor c.

A pilot that does not exercise these differences at the positions E2 will use would fit c and k to a computation with
different rounding behaviour. Four gaps follow.

## Proposed changes

1. **The pilot's arithmetic profile must match the subject's.**
   - **The SmolLM2-135M problem:** it is a Llama-family model with no QK norm, a different RoPE θ and a different
     head_dim, so it does not exercise differences 1–4 the way Qwen3-0.6B does.
   - **Proposed:** the pilot uses the protocol's existing fallback, a declared corpus **on the subject**, disjoint from
     the sealed held-out part, run after the freeze and discarded afterwards. This is already allowed text. The change
     makes it the primary route, not the fallback.
   - **Alternative, if the owner prefers a different checkpoint:** a Qwen3-architecture checkpoint, with QK norm,
     split-half RoPE and a θ and head_dim that give comparable angle magnitudes. Its D2 comparability must be
     established under D7 before it is used.
2. **Positions must cover E2's range.**
   - The pilot corpus's sequence lengths reach at least the maximum position in the E2 corpus, with positions sampled
     across the whole range, the longest included.
   - Pilot positions are reported in bands (for example 0–511, 512–4095, 4096–max), so position-dependent growth is
     visible.
   - c and k are still chosen by the single preregistered rule over all pilot logits. The bands are for reporting,
     not separate tolerances.
3. **Saturation needs a preregistered outcome.**
   - **The gap:** if no ladder value passes (some pilot logit fails at c = 32, k = 64), the current text says nothing.
   - **Proposed:** the ladder is not extended. T3 is recorded as **"not determinable at the preregistered ladder"**,
     a Phase 3 finding with the failing logits' positions and bands reported. E2 is then reported against no T3
     verdict (like T4), and T3 is not widened after the fact.
   - **The owner may instead preregister a longer ladder now,** before the freeze, but not after seeing pilot output.
4. **What the pilot may inspect, as an auditable gate check:**
   - only its own declared corpus;
   - never the sealed held-out part;
   - never any E2 measurement corpus logits.

   The pilot run record names the corpus hash. A G1 tamper test covers changing the pilot corpus or the ladder after
   the freeze.

## Expected behaviour, so a reviewer can check the form is sensible

- **Difference 1 makes LARQL's RoPE more accurate than ref₃₂'s at long positions.** So `|LARQL − ref₃₂|` there is
  roughly ref₃₂'s own table error, which `|ref₃₂ − ref₆₄|` also measures. The ratio should be near 1, inside c ≥ 2.
- **A position where ref₃₂ and ref₆₄ agree closely by accident,** while LARQL differs through summation order, is what
  the `k·ulp₃₂` floor is for.
- **None of this is a measurement.** The pilot decides.

## Not proposed

- No change to the form of T3, to the ladder values, or to the "pilot data never enter any reported result" rule.
- No running of anything in Phase 1.
