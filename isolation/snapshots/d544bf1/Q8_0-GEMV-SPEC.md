# Q8_0 matrix-vector product: numerical specification, revision 1

**Status: frozen before any reference is written.** Development only (protocol decision D15). Nothing measured against this
is blind acceptance evidence.

**Contract status**

| Contract | Status |
|---|---|
| `Q8_0_GEMV_SEQ` | A numerical measurement of agreement with the program in section 3 |
| `Q8_0_GEMV_B1` | **Experimental.** A numerical measurement against the inequality in section 4. Its guarantee is pending: section 5 is a paper derivation that no proof system has checked |

Neither contract proves anything about inputs that were not tried. Results are `MEASURED`, never `PROVED`.

## 1. Inputs

- `n ≥ 0` rows and `k ≥ 1` columns, with `k` a multiple of 32 and `k < 2²⁴`.
- `blocks`: exactly `n · (k/32) · 34` bytes, in row order, blocks in column order within a row. A block is a little-endian
  IEEE 754 binary16 scale `d`, then 32 signed int8 codes `q`. (Q8_0 as in ggml `block_q8_0`, `facdc44a`.)
- `x`: `k` IEEE 754 binary32 values, each given as its 32-bit pattern.
- `y`: `n` binary32 values, each given as its 32-bit pattern. This is the result under test.

## 2. Weights and the ideal result

For row `i` and column `j`, with `b = ⌊j/32⌋`:

    w_ij = q_ij · d_ib

Over all int8 codes and finite binary16 scales, `w_ij` is exactly representable in binary32. Its significand needs at most
8 + 11 = 19 bits, its lowest set bit is at least 2⁻²⁴, and its magnitude is at most 128 · 65504.

The ideal result, over the real numbers, is:

    y*_i = Σ_j w_ij · x_j

The arithmetic size of a row, over the real numbers, is:

    S_i = Σ_j |w_ij · x_j|

## 3. `Q8_0_GEMV_SEQ`: the declared program

For each row independently:

    acc = +0.0
    for j = 0, 1, …, k-1:
        acc = acc + (w_ij × x_j)
    result_i = acc

- `×` and `+` are each one IEEE 754 binary32 operation, rounded to nearest with ties to even.
- There is no fused multiply-add. Subnormal operands and results are kept, not flushed.
- The sum is in ascending `j`, with no reassociation.

`satisfied` means `y_i` has exactly the bit pattern of `result_i` for every row. That includes the sign of zero: `+0.0 + -0.0`
is `+0.0`.

## 4. `Q8_0_GEMV_B1`: the inequality

Constants, as exact rationals:

    u = 2⁻²⁴
    η = 2⁻¹⁵⁰
    γ_m = m·u / (1 − m·u)
    Ω = 2¹²⁸ − 2¹⁰³

The bound for a row is:

    B_i = γ_k · S_i + k · η · (1 + γ_k)

`satisfied` means `|y_i − y*_i| ≤ B_i` for every row, compared over the real numbers, with `y_i` read as the exact value of its
bit pattern. A verdict must be the same as exact rational arithmetic would give. A faster method may decide a row only where it
can show that it agrees.

**The domain, for both contracts.** A row is in the domain when all of these hold:

- every `d_ib` in the row is finite;
- every `x_j` is finite;
- `(1 + γ_k) · (S_i + k·η) < Ω`.

**Outside the domain the answer for the whole input is `could_not_evaluate`, with reasons.** It is never `satisfied`. A non-finite
`y_i` inside the domain is `violated`, not `could_not_evaluate`.

## 5. Why this inequality: a derivation, not a proof

This is a pen-and-paper argument for the program in section 3 under the assumptions below. It has not been checked by a proof
system. A counterexample would mean one of its steps or assumptions is wrong.

**Assumptions**

- A1. Each `×` and `+` is correctly rounded IEEE 754 binary32, to nearest, ties to even.
- A2. Subnormals are kept.
- A3. Section 3's order of operations.
- A4. The domain in section 4.
- A5. `k·u < 1`.

**Rounding model.** For a real `r` that rounds to a finite value, `fl(r) = r(1 + δ) + ε`, with `|δ| ≤ u`, `|ε| ≤ η`, and `δ·ε = 0`:
`ε` applies only where the result is in the subnormal range, and half the smallest subnormal 2⁻¹⁴⁹ is 2⁻¹⁵⁰.

**Step 1: products.** `w_j` is exact (section 2), so `p̂_j = fl(w_j · x_j) = p_j(1 + δ_j) + ε_j`, where `p_j = w_j · x_j`.

**Step 2: sums have no `ε`.** The sum of two binary32 values is an integer multiple of 2⁻¹⁴⁹. If it lies in the subnormal range it
is representable exactly. So `fl(a + b) = (a + b)(1 + α)` with `|α| ≤ u`, and no absolute term. The first addition, `+0.0 + p̂_0`,
is exact.

**Step 3: unroll.** With `ŝ` the final value:

    ŝ = Σ_j p̂_j · Π_{m ≥ max(j,1)} (1 + α_m)

So `p_j` carries `(1 + δ_j)` and at most `k−1` factors `(1 + α_m)`, which is at most `k` factors. `ε_j` carries at most `k−1` factors.

**Step 4: collect.** By the standard result (Higham, *Accuracy and Stability of Numerical Algorithms*, Lemma 3.1), a product of `m`
factors `(1 + δ)` with `|δ| ≤ u` and `m·u < 1` equals `1 + θ` with `|θ| ≤ γ_m`. So:

    |ŝ − y*| ≤ γ_k · Σ_j |p_j| + Σ_j |ε_j| · (1 + γ_{k−1})
             ≤ γ_k · S + k · η · (1 + γ_k)

The last step uses `γ_{k−1} ≤ γ_k`, which is slightly weaker than necessary. It is kept so the stated form doesn't change.

**Step 5: no overflow.** Steps 1 to 4 need every intermediate to round to a finite value, and round to nearest overflows exactly when
`|r| ≥ Ω`. Each `|p_j|`, and each exact partial sum formed before rounding, is at most `(1 + γ_k) · (S + k·η)` by the same unrolling,
which the domain keeps below `Ω`. A full proof must carry this by induction. It is the step of this derivation most in need of checking.

**What this does not cover.** A program other than section 3's. The argument is written for section 3, even though a similar one
applies to other summation orders. Any wider claim needs its own derivation.

## 6. Counterexamples and ambiguity

If a case in the domain has `y_i` from section 3's program and breaks section 4's inequality, it is a **counterexample**:

- Record the exact input bits, in the checker's `AMBIGUITIES.md` and as a test that shows the failure, and stop that line of work.
- **Do not change the bound, the constants, the domain or the program.** Only the protocol owner can issue a new revision.

Any other unclear passage: choose the fail-closed reading and record it.
