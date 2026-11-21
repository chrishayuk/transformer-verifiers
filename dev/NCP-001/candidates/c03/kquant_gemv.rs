//! The CPU's K-quant gemv — the stored block, multiplied where it lies.
//!
//! **Not [`crate::pipeline::quant_format::QuantFormat::Q8_0`].** That
//! name already exists in this crate and means a different thing: int8
//! codes with an EXTERNAL per-block f32 scale array, block 32. The
//! formats here are ggml's, whose scale is INSIDE the block — Q8_0 is
//! one f16 then 32 codes in 34 bytes. Two layouts sharing a name is how
//! a reader ends up passing one to the other's kernel, so this module
//! says `ggml` in its types and keeps its distance.
//!
//! Until this existed, a K-quant operand had exactly one execution
//! route: decode the whole matrix to f32 and run an f32 gemv over the
//! result. That is correct and it is what PARETO-1's rung A was measured
//! with, but it prices a Q8_0 model at **four bytes per weight**. On
//! Qwen3.8-27B the profiler put 97.3% of a decode token in `Projection`,
//! moving 97.4 GB of widened f32 per token where the artifact itself
//! holds the same information in 24.4 GB.
//!
//! The arithmetic here is not a second opinion about the format. It is
//! the association [`larql_models::quant::ggml::dequantize_q8_0`]
//! documents — `(q as i8 as f32) * f16(d)` — applied one block at a time
//! instead of into a whole decoded matrix, and multiplied into the
//! accumulator in element order. That makes it match
//! dequantise-then-multiply **exactly** rather than approximately, and
//! the tests hold it to that oracle.
//!
//! # Why exactness is available here at all
//!
//! `d` is an f16 and `q` an int8, so `d * q` needs at most 11 + 8 bits
//! of significand and is therefore EXACT in f32. Folding the scale into
//! each weight before the multiply — rather than hoisting it out of the
//! block's dot product, which would be cheaper — is what lets this
//! kernel be bit-for-bit with the decoder instead of merely close. A
//! hoisted scale is a different program, and on a path whose whole
//! purpose is to leave kernel quality out of a behavioural curve, "a
//! different program" is the thing to avoid.
//!
//! # Threading
//!
//! The kernel threads itself, as the Q4_K and Q6_K kernels beside it do:
//! rows are independent, so a row-parallel schedule changes which thread
//! runs a row and nothing about what that row computes — every row's
//! accumulation is the serial loop in `row_dot`, in the same order.
//! A caller that threads on top (LARQL's plan executor) declares this
//! kernel library-owned and calls it once.

use larql_models::quant::half::f16_to_f32;

/// Elements described by one Q8_0 block.
pub const Q8_0_BLOCK_ELEMS: usize = 32;

/// Bytes one Q8_0 block occupies: an f16 scale then 32 signed codes.
pub const Q8_0_BLOCK_BYTES: usize = 34;

/// Rows per parallel work unit — the granularity the Q4_K and Q6_K
/// kernels use, for the same reason: a bandwidth-bound row loop wants
/// few, large units rather than one task per row.
const CHUNK_ROWS: usize = 16;

/// `out[n] = W[n, k] · x[k]`, with `W` read straight from the stored
/// Q8_0 pack.
///
/// `None` — never a wrong answer — when the geometry does not describe
/// this pack: `k` off the block grid, or the stream the wrong length for
/// `[n, k]`. Silently accepting a short stream would read a neighbouring
/// row's codes as this row's and return a plausible vector.
pub fn q8_0_gemv(blocks: &[u8], x: &[f32], n: usize, k: usize) -> Option<Vec<f32>> {
    if k == 0 || !k.is_multiple_of(Q8_0_BLOCK_ELEMS) || x.len() != k {
        return None;
    }
    let per_row = k / Q8_0_BLOCK_ELEMS;
    let expected = n.checked_mul(per_row)?.checked_mul(Q8_0_BLOCK_BYTES)?;
    if blocks.len() != expected {
        return None;
    }

    let mut out = vec![0.0f32; n];
    {
        use rayon::prelude::*;
        out.par_chunks_mut(CHUNK_ROWS)
            .enumerate()
            .for_each(|(chunk, slots)| {
                run_rows(blocks, x, chunk * CHUNK_ROWS, per_row, slots);
            });
    }
    Some(out)
}

/// Fill `slots` with the dots of consecutive rows starting at `first`.
/// Whole groups go through the interleaved kernel where there is one;
/// what is left goes through [`row_dot`], the same program a row at a time.
#[inline]
fn run_rows(blocks: &[u8], x: &[f32], first: usize, per_row: usize, slots: &mut [f32]) {
    #[allow(unused_mut)]
    let mut done = 0;
    #[cfg(target_arch = "aarch64")]
    {
        let mut groups = slots.chunks_exact_mut(neon::ROWS);
        for group in &mut groups {
            let group: &mut [f32; neon::ROWS] =
                group.try_into().expect("chunks_exact_mut yields ROWS");
            neon::rows(blocks, x, first + done, per_row, group);
            done += neon::ROWS;
        }
    }
    for (i, slot) in slots[done..].iter_mut().enumerate() {
        *slot = row_dot(blocks, x, first + done + i, per_row);
    }
}

#[cfg(target_arch = "aarch64")]
mod neon {
    use super::{Q8_0_BLOCK_BYTES, Q8_0_BLOCK_ELEMS};
    use core::arch::aarch64::*;
    use core::arch::asm;

    pub(super) const ROWS: usize = 16;
    const GROUPS: usize = ROWS / 4;
    const SPAN: usize = 8;
    const SPANS: usize = Q8_0_BLOCK_ELEMS / SPAN;

    /// Each 32-bit lane takes one byte of a column as its TOP byte, so a
    /// fixed-point conversion with 24 fraction bits yields the code itself.
    /// The two table registers hold rows 0, 1 and rows 2, 3 of a group, eight
    /// columns each; entry `j` picks column `j` of all four rows.
    const TOP_BYTE: [[u8; 16]; SPAN] = {
        let mut t = [[0xff; 16]; SPAN];
        let mut j = 0;
        while j < SPAN {
            let mut l = 0;
            while l < 4 {
                t[j][l * 4 + 3] = (l * SPAN + j) as u8;
                l += 1;
            }
            j += 1;
        }
        t
    };

    /// `ROWS` consecutive rows, one per lane. Each lane's accumulator sees
    /// exactly its row's additions in ascending column order; only the
    /// assignment of rows to lanes is new.
    pub(super) fn rows(
        blocks: &[u8],
        x: &[f32],
        first: usize,
        per_row: usize,
        out: &mut [f32; ROWS],
    ) {
        let stride = per_row * Q8_0_BLOCK_BYTES;
        assert!((first + ROWS) * stride <= blocks.len() && x.len() == per_row * Q8_0_BLOCK_ELEMS);
        // SAFETY: the assert above puts `ROWS` whole rows at `first` inside
        // `blocks` and `per_row` whole blocks in `x`; NEON is baseline on
        // aarch64.
        unsafe {
            rows_inner(
                blocks.as_ptr().add(first * stride),
                x.as_ptr(),
                stride,
                per_row,
                out,
            )
        }
    }

    /// binary16 to binary32 for four lanes in one instruction.
    #[inline(always)]
    fn f16_to_f32_lanes(h: uint16x4_t) -> float32x4_t {
        let out: float32x4_t;
        // SAFETY: a register-to-register conversion on baseline NEON; it
        // touches no memory and no flags.
        unsafe {
            asm!("fcvtl {o:v}.4s, {h:v}.4h", o = lateout(vreg) out, h = in(vreg) h,
                 options(pure, nomem, nostack, preserves_flags));
        }
        out
    }

    /// One column: lane `L` of each group's code register, `(q * d) * x`.
    #[inline(always)]
    fn step<const L: i32>(
        acc: &mut [float32x4_t; GROUPS],
        t: &[uint8x16x2_t; GROUPS],
        tb: uint8x16_t,
        d: &[float32x4_t; GROUPS],
        xv: float32x4_t,
    ) {
        // SAFETY: NEON is baseline on aarch64.
        unsafe {
            for g in 0..GROUPS {
                let code = vreinterpretq_s32_u8(vqtbl2q_u8(t[g], tb));
                let q = vcvtq_n_f32_s32::<24>(code);
                acc[g] = vaddq_f32(acc[g], vmulq_laneq_f32::<L>(vmulq_f32(q, d[g]), xv));
            }
        }
    }

    /// # Safety
    /// `p` addresses `ROWS` rows of `stride` bytes and `x` `per_row` blocks.
    #[inline(never)]
    unsafe fn rows_inner(
        p: *const u8,
        x: *const f32,
        stride: usize,
        per_row: usize,
        out: &mut [f32; ROWS],
    ) {
        // SAFETY: bounds per this function's contract; loads are unaligned.
        unsafe {
            let tb = [
                vld1q_u8(TOP_BYTE[0].as_ptr()),
                vld1q_u8(TOP_BYTE[1].as_ptr()),
                vld1q_u8(TOP_BYTE[2].as_ptr()),
                vld1q_u8(TOP_BYTE[3].as_ptr()),
                vld1q_u8(TOP_BYTE[4].as_ptr()),
                vld1q_u8(TOP_BYTE[5].as_ptr()),
                vld1q_u8(TOP_BYTE[6].as_ptr()),
                vld1q_u8(TOP_BYTE[7].as_ptr()),
            ];
            let mut acc = [vdupq_n_f32(0.0); GROUPS];
            for b in 0..per_row {
                let base = p.add(b * Q8_0_BLOCK_BYTES);
                let xs = x.add(b * Q8_0_BLOCK_ELEMS);
                let mut d = [vdupq_n_f32(0.0); GROUPS];
                for (g, dv) in d.iter_mut().enumerate() {
                    let mut h = [0u16; 4];
                    for (l, hl) in h.iter_mut().enumerate() {
                        let at = base.add((g * 4 + l) * stride) as *const u16;
                        *hl = u16::from_le(at.read_unaligned());
                    }
                    *dv = f16_to_f32_lanes(vld1_u16(h.as_ptr()));
                }
                for span in 0..SPANS {
                    let off = 2 + span * SPAN;
                    let mut t = [uint8x16x2_t(vdupq_n_u8(0), vdupq_n_u8(0)); GROUPS];
                    for (g, tg) in t.iter_mut().enumerate() {
                        let row = |l: usize| vld1_u8(base.add((g * 4 + l) * stride + off));
                        *tg =
                            uint8x16x2_t(vcombine_u8(row(0), row(1)), vcombine_u8(row(2), row(3)));
                    }
                    let xh = xs.add(span * SPAN);
                    let xa = vld1q_f32(xh);
                    let xb = vld1q_f32(xh.add(4));
                    step::<0>(&mut acc, &t, tb[0], &d, xa);
                    step::<1>(&mut acc, &t, tb[1], &d, xa);
                    step::<2>(&mut acc, &t, tb[2], &d, xa);
                    step::<3>(&mut acc, &t, tb[3], &d, xa);
                    step::<0>(&mut acc, &t, tb[4], &d, xb);
                    step::<1>(&mut acc, &t, tb[5], &d, xb);
                    step::<2>(&mut acc, &t, tb[6], &d, xb);
                    step::<3>(&mut acc, &t, tb[7], &d, xb);
                }
            }
            for (g, a) in acc.iter().enumerate() {
                vst1q_f32(out.as_mut_ptr().add(g * 4), *a);
            }
        }
    }
}

/// One row's dot in the decoder's association — `(q * d) * x`, element
/// by element, blocks in order. The whole arithmetic of the kernel is
/// here; [`q8_0_gemv`] only decides which thread runs it.
#[inline]
fn row_dot(blocks: &[u8], x: &[f32], row: usize, per_row: usize) -> f32 {
    let mut acc = 0.0f32;
    for b in 0..per_row {
        let base = (row * per_row + b) * Q8_0_BLOCK_BYTES;
        let d = f16_to_f32(u16::from_le_bytes([blocks[base], blocks[base + 1]]));
        let codes = &blocks[base + 2..base + Q8_0_BLOCK_BYTES];
        let xs = &x[b * Q8_0_BLOCK_ELEMS..][..Q8_0_BLOCK_ELEMS];
        for (j, &c) in codes.iter().enumerate() {
            // `d * q` first, then the activation — the decoder's
            // association, element by element. See the module note on
            // why this is exact and why hoisting `d` would not be.
            acc += ((c as i8 as f32) * d) * xs[j];
        }
    }
    acc
}

#[cfg(test)]
#[path = "kquant_gemv_tests.rs"]
mod tests;
