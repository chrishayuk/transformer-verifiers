# Your task

Make this function faster, without changing a single output bit:

`crates/larql-compute/src/cpu/kquant_gemv.rs`, `q8_0_gemv`: LARQL's production CPU matrix-vector product for Q8_0 weights.

**You may change that one file and nothing else.** Any other change makes the candidate invalid. You can't add dependencies, features, build flags, or a build script. Unsafe code and architecture intrinsics are allowed in that file. The machine is an Apple M3 Max.

## The computation you must preserve, exactly

A row of `k` columns is `k/32` blocks of 34 bytes: a little-endian binary16 scale `d`, then 32 signed int8 codes `q`. With `w_j = q_j · d` for the block holding column `j`, for each row independently:

    acc = +0.0
    for j = 0, 1, …, k-1:
        acc = acc + (w_j × x_j)
    result = acc

`×` and `+` are each one IEEE 754 binary32 operation, rounded to nearest with ties to even. There's **no fused multiply-add**, subnormals are kept and never flushed, and each row sums in ascending `j` with no reassociation. The result must equal this program bit for bit on every finite input, including the sign of zero, for every valid `rows` and `k` (`k` a multiple of 32), with any number of threads. Invalid geometry must still return `None`.

So changing the order of additions within a row, or the precision of the accumulator, is out of scope here, whatever it would do for speed.

## How you work

This is one continuous session, and you decide what to try and when. You can compile, run tests and write your own measurements in this workspace. There's no network. Use `cargo … --release --offline --locked`.

When you have a candidate, submit the kernel file as it stands:

    ncp evaluate "what you changed and why you expect it to be faster"

Run it with the Bash tool's `timeout` set to 14400000. It blocks until the result arrives, which usually takes tens of minutes, and it waits for a quiet machine, so don't leave anything running while it works. If the call gets cut off, the evaluation carries on, and `ncp result` waits for it and prints the result. It doesn't use another candidate.

An evaluator you can't see takes that one file, builds it with the fixed production settings, and runs its checks in order, stopping at the first failure. It tells you the stage that failed, with a short diagnostic. A candidate that passes everything gets its speed relative to the unchanged kernel on realistic matrices. Those matrices have these shapes, as rows x columns: 1024x1024, 3072x1024, 2048x1024, 1024x2048, 1024x3072.

You have **at most 20 candidates**, and each `ncp evaluate` uses one. A candidate that fails still counts, and every candidate is kept on record. Any tracked file other than the kernel must match the original when you submit, or the candidate is rejected. You can add scratch files of your own, but they never reach the evaluator. Don't leave benchmark code in the kernel file.

Ending your turn ends the session for good, so carry on until you've gone as far as you usefully can. Then finish with a summary of what you tried, what worked, what failed and why.

A final evaluation on matrices and activations you never see decides the result, so don't tune to the development results. **No improvement is a legitimate outcome.** Report what you actually find.
