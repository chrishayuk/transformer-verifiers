# Independent T3 calibration review: report (transcription)

**Transcription.** The harness refused the reviewer's own `REPORT.md` write. This is its returned report, extracted
verbatim from its hand-back by the coordinating session. Nothing was edited.

- **Reviewer:** an independent subagent. It did not write T3, the pilot procedure or the checker.
- **Repository:** `~/chris-source/t3-calibration-review`, commit `21d630a`.
- **Spot-checked by the coordinating session:**
  - `results/sub_D1024_L4.json`: B0 worst ratio 7.9e7, and 0.63% of logits with ratio > 32;
  - `results/ladder_mc.json`: (2,64) selected in 199 of 200 trials, and the successor failing its own pilot in 200 of
    200;
  - `results/noise_scale_sub.json`: 317, 114, 39, 11.5 and 3.8 failing logits per position at (32,64), for noise
    scales 1 to 0.01.

  All match the report.
- **Tool log:** 69 calls. Writes only to its own repository, and no access to checker code, held-out or hidden
  corpora, LARQL, real weights or the network.

---

## Independent T3 calibration review, LARQL-VERIFY-001

**Verdict: NOT SUITABLE (as proposed).**

T3 cannot pass a correct implementation on this corpus, so the calibration cannot produce a verdict. This is not a matter of tuning c and k: the minimum fix changes the inequality itself, which D13 closed, so the owner would have to reopen it.

**Where things are:**
- **REPORT.md was not written.** The harness refused a subagent `.md` write. The report text is below.
- **Repository:** `/Users/christopherhay/chris-source/t3-calibration-review`, commit **`21d630a`** (after `114b519`). It holds the simulations in `sim/` and the results in `results/`. No trailers, nothing pushed.
- **Reviewed against:** `transformer-verifiers` at `be69254`. D11 §5 has not changed since the D11 draft was last edited.
- **Rules kept:** no LARQL, no checker code, no held-out or hidden corpora, no real weights, no network, no pilot.

**Simulations, all on synthetic models:**
- **Sim A:** RoPE table error against mpmath, by band.
- **Sim B:** a Qwen3-style model at head_dim 128 and θ 1e6, one 40,960-token sequence, evaluated at the DESIGN.md §5 positions.
  - Routes: ref₆₄, ref₃₂ (upstream binary32 RoPE), ref₃₂ₐ (ref₃₂ with LARQL's RoPE route), and a LARQL-like route (binary64 angle, block-ordered accumulation).
  - Sizes: D256/V32768, D1024/F3072/L4/V151936 (subject-like), and D2048/F6144/L4/V151936 (1.7B-like).
  - Plus a fault sweep, a noise-scale sensitivity check and a per-position yardstick variant.
- **Sim C:** ladder mechanics.
- **Sim D:** how accumulation length affects the error ratio.

Sim A reproduces the audit's numbers: 2.65e-4 at position 4095 and 2.02e-3 at 40,959. Sim B's B1 yardstick inflation of 8–12× matches the audit's 12×.

## 1. Self-calibration

**1.1 MATERIAL, decisive: the ladder saturates.** The yardstick is per logit, the floor scales with each logit's own magnitude, and every logit must pass.
- **The cause:**
  - The ratio |LARQL−ref₃₂| / |ref₃₂−ref₆₄| is taken per logit. Its denominator is a continuous rounding error that passes through zero, so the ratio has a Cauchy-like tail: P(>c) ≈ 2s/(πc). Observed in B0: 0.0063, against 0.0054 predicted.
  - k·ulp₃₂(ref₆₄) scales with each logit's own magnitude, but logit errors are absolute. So the floor does nothing for |z| below about 2–4.
- **Failures at the top rung (32,64):**
  - **Subject-like model:** 262,979 logits fail (317 per position), and all 830 of 830 positions fail.
  - **1.7B-like model:** 294 per position.
  - **A candidate identical to ref₃₂ except the LM-head summation order** still has 752 failing logits, in 383 of 831 positions.
  - **A candidate differing only by the declared RoPE route:** 49,803 failing logits.
  - **Shrinking all noise to 0.1×** (roughly the real subject's level) still gives 39 per position, with 97% of positions failing. At 0.01× it is 3.8 per position, 76% failing.
- **Worst ratios:** 10⁵ to 10⁸.
- **Consequences:**
  - The pilot, at 1.45·10⁹ logits, returns `not_determinable` almost surely.
  - Any constants that were chosen would make a correct LARQL `fail` on the subject under the closed any-logit outcome rule.
  - The failure path is fail-safe, so there is no false pass. But T3 can never deliver a verdict.

**1.2 Detection, under the per-position variant R1 at c = 4.** Row ratios are given as median/maximum in B0 → B3, from the D1024 run.
- **Inverse frequency ×(1+1e-6):** detected in every band (11.9/63 … 21.3/42.8).
- **Score scale ×(1+1e-4):** 28.6/93.6 in B0, but **1.22/2.07 in B3, so it passes.** That error is 76× LARQL's honest error.
- **KV cache in bf16:** detected in every band (10.9/20.1 in B3).
- **A binary32 RoPE angle, as ref₃₂ forms it:** 0.0096/0.019 in B3. It passes at any c, although it is 107× LARQL's honest error. T3 rewards this bug class rather than merely absorbing it.

**1.3 MATERIAL: the D11 §5.1 claim is inaccurate.**
- "Detects deviations exceeding what the pilot exhibited" is wrong on two counts:
  - the margin step can tighten the tolerance (see 4.2);
  - detection is measured in units of c × the yardstick, per band, not in absolute terms.
- Anything below c × the yardstick is absorbed, whether or not the pilot showed it.
- E1, A3, A4 and the reference audit do **not** cover LARQL execution deviations in RoPE, the score scale, softmax, KV precision or accumulation:
  - E1 covers weights only;
  - A3 covers invariance laws;
  - A4's tolerance for A2 is T3 itself, so it is circular;
  - the audit covered the reference, not LARQL.

## 2. Long-position sensitivity

**The numbers by band.** ref₃₂'s RoPE table error (LARQL's is 3.0e-8 everywhere), the yardstick inflation over an f32 reference with accurate RoPE (RMS, D1024), and the yardstick as a multiple of LARQL's honest error:

| Band | ref₃₂ RoPE error | Yardstick inflation | Yardstick vs honest error |
|---|---|---|---|
| B0 (0–511) | 3.4e-5 | 1.7× | about 3.6× |
| B1 (512–4095) | 2.7e-4 | 9.9× | about 17× |
| B2 (4096–32767) | 2.0e-3 | 60× | about 88× |
| B3 (32768–40959) | 2.6e-3 | 95× | about 124× |

**What can pass undetected:**
- **RoPE frequency errors** grow with position, as the yardstick does. They are caught at the same relative size in every band, so the absolute size that passes grows about 40×.
- **Position-independent errors** (score scale, softmax, KV precision) can pass at roughly 3–10× honest in B0, 15–40× in B1, 90–250× in B2 and 120–500× in B3, for c = 2–4.

**MATERIAL: band and class verdicts are not enough.**
- A band `pass` does not show how loose that band was.
- The single selection rule is driven by B0, which holds 85% of positions.
- Required: preregister per-band reporting of the absolute envelope, the ratio distribution, and |LARQL−ref₆₄| against |ref₃₂−ref₆₄|, and qualify the claim per band.
- Separate c and k per band would be an improvement, not a minimum change: the inflation sits in the yardstick, not in c.

## 3. Representativeness of Qwen3-1.7B

- **MINOR: the size difference barely moves the ratio.**
  - A sequential GEMV row has, relative to the BLAS error: 5.86× at length 1024, 6.62× at 2048, 7.13× at 3072 and 7.14× at 6144.
  - End to end, LARQL's own error over the yardstick is 0.275 against 0.243 in B0 and equal in B1–B3.
  - So the pilot is looser by at most about 15%. The larger risk is trained activation statistics, which cannot be checked without weights.
- **Valid proxy for differences 1–4:** the RoPE tables depend only on θ, head_dim and position.
- **MATERIAL: the independence label overstates.** LARQL's systematic errors come from its code, not its weights. The 1.7B route therefore absorbs the same code-level deviations as the disjoint-subject-corpus fallback. The fallback is more representative and absorbs the same things.
- **MINOR:** the D11 §5.6 weight-statistics check has no preregistered criterion. It should be informational only, or get a criterion before the weights are seen.

## 4. The procedure

- **MATERIAL, ordering:** c-then-k favours **small c with large k**. Selection lands on (2,64) in 199 of 200 trials. k = 64 gives the top tokens the loosest tolerance: 1.2e-4 at |z| in [16,32).
- **MATERIAL, margin:** the margin is not a margin.
  - The successor of (c,64) is (2c,4), which cuts the floor 16×. It failed its own pilot in 800 of 800 determinable trials, and a correct candidate then failed on the subject with P = 1.0.
  - Successors of (c,4) or (c,16) change only k, which adds nothing to the binding c term.
- **Saturation outcome:** fail-safe and adequate, but it is the *expected* result of the present form.
- **MATERIAL, "every pilot logit passes":** one outlier among 1.45·10⁹ logits decides c. Even a true doubling margin gives about a 1/3 false-fail rate with Fréchet-like tails and equal sample sizes. A quantile rule cannot fix it while the subject's any-logit rule stays closed.
- **Separation from the held-out set:** adequate. Longest common substring 22 tokens, 13-gram overlap 0.072%, separate salts and seals.
- **Band coverage:** pilot and held-out match (8,083/962/378/113 against 8,083/959/378/114). MINOR: B3 comes from only two sequences.

## 5. Other points

- **MATERIAL:** a pass says LARQL is about as far from ref₃₂ as ref₆₄ is. It does not bound LARQL's error against ref₆₄. A complementary per-band report is needed.
- **MINOR:** the floor is backwards relative to the error structure: loosest for the top tokens, vanishing near zero.
- **MINOR:** under the current form, `failing_token_ids` would show scattered near-zero logits, which invites post-hoc explanation.

## Minimum changes, all needing the owner

1. **R1** (reopens the inequality D12/D13 closed): replace the per-logit yardstick with a per-position one: |LARQL_i − ref₃₂_i| ≤ max(c·max_j|ref₃₂_j−ref₆₄_j|, k·ulp₃₂(max_j|ref₆₄_j|)). The outcome rule and the exact decision procedure stay the same. On the synthetic data it selects (2,4) with a final pair of (4,4), and a correct candidate passes on held-back positions at all three sizes.
2. **R2:** the margin must dominate componentwise (the next c with the same k). The final pair must pass the pilot. Selecting c = 32 still gives `not_determinable`.
3. **R3:** correct D11 §5.1 as in 1.3.
4. **R4:** preregister the per-band reporting in section 2 and qualify the claim per band.
5. **R5:** the route label states that code-level deviations are absorbed under either route, and the weight-statistics check is informational only or criterion-bound.

Without R1, Stage A should state that it makes no T3 claim.

## Defensible claim wording for a T3 pass, after R1–R5

> On the sealed held-out corpus (N_B0/N_B1/N_B2/N_B3 evaluated positions), every logit LARQL produced lay within max(c·Y_p, k·ulp₃₂(M_p)) of a binary32 reference forward on the same decoded weights. Here Y_p is that reference's largest binary32-against-binary64 logit discrepancy at the same position, and M_p is the largest |logit|, with (c, k) = (…, …) calibrated by the preregistered ladder on [an independent Qwen3-architecture checkpoint | a disjoint subject corpus].
>
> This is an empirical agreement criterion on this corpus, not a certified floating-point bound and not a proof of execution equivalence.
>
> It cannot detect:
> - any LARQL deviation smaller than c·Y_p;
> - a deviation of LARQL's code path that is equally present in the calibration run, under either route.
>
> From about position 500 onward, Y_p is dominated by the reference's own binary32 RoPE-angle error. The measured envelope c·Y_p was [x] in positions 0–511, [x] in 512–4095, [x] in 4096–32767 and [x] in 32768–40959. A LARQL error below that envelope, including a binary32 formation of the RoPE angle, would not be detected in the longer bands.
>
> Positions 32,768–40,959 lie beyond the native context and are reported as a separate stress test.
>
> LARQL's own error against the binary64 reference, relative to the binary32 reference's error, was [ratio] by band.

**Limits of these simulations:**
- **Model size.** The models have 2–4 layers rather than 28, and their absolute noise is about 10× the real subject's. The findings rest on scale-free mechanisms (the ratio's tail, the binade-relative floor, the partial order of (c,k)) and on the noise-scale sensitivity check.
- **LARQL's accumulation.** I emulated it in block order. A strictly sequential GEMV is noisier (Sim D), which would only strengthen 1.1.
- **Precision of the counts.** The inequality was evaluated in binary64, not exactly, which is adequate for counts of this size.

Reproduction commands are in `sim/` (run from that directory). Results are in `/Users/christopherhay/chris-source/t3-calibration-review/results/` (for example `sub_D1024_L4.json`, `faults_D1024_table.txt`, `ladder_mc.json`, `rowlevel_alt.txt`, `rope_table.json`, `compare_sizes.json`, `dot_length.json`, `noise_scale_sub.json`).

**Commit: `21d630a`**
