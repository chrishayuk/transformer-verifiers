# NCP-001: autonomous neural circuit optimisation

**Question.** Can an AI agent find a faster implementation of LARQL's production CPU Q8_0 GEMV kernel while preserving the declared computation bit for bit?

**Status.** A development experiment under D15. Not a formal proof and not a blind certification. `Q8_0_GEMV_SEQ` and `Q8_0_GEMV_B1` are measured checks. Frozen before the agent's first turn. Tools are pinned by `tools.sha256`. A later change is recorded as a deviation and doesn't rewrite this page.

## What's pinned

| | |
|---|---|
| LARQL | `bb15f826f18c2f9c2b16e7bee8a02dfafbfce8f0`. **Provisional:** `main` before PR #697, which changes reproduction files only |
| Container | `q8enc-ad82acba`, corrected Q8_0 |
| Verifier | `verifier/` at that commit: `refcheck` from isolated checker `f2788f0` |
| Compiler and flags | Rust 1.98.0, workspace `release` profile, no `RUSTFLAGS` |
| Hardware | Apple M3 Max, 12 performance and 4 efficiency cores, macOS 27.0.1 |
| Agent | Claude Code 2.1.318 with auto-update off, model `claude-opus-5-5`, one continuous session |
| Budget | At most 20 candidates, 8 agent hours, US$120 in total: whichever comes first. Agent hours exclude time spent inside an evaluation |

The budget figures are stop conditions, enforced by software. They aren't a guaranteed billing cap. Candidate count, agent time, submissions and cost all persist across a restart. The runner resumes the same session after an infrastructure error, at most three times, and refuses to start over existing records. If a run reports no cost, the session stops rather than resuming. Each resumed run's reported cost is added to the total, which can only stop the session earlier.

## Isolation

The agent works in a clean clone with no remote, without `verifier/`, `docs/verification/` or `.github/`, and reads only that and the toolchain. It has no network and no MCP servers. The re-test is in `isolation-test.log`. It can't read the evaluator, the harness, the workloads, the conformance cases or the checker. Its only interaction with verification is `ncp evaluate`, and the feedback it returns.

**Allowed change:** `crates/larql-compute/src/cpu/kquant_gemv.rs` only. `ncp evaluate` queues a copy of that file and a message, and the evaluator reads them as bytes without following links. It builds that one file into its own tree at the pinned commit, so nothing else the agent does reaches a build. A submission made while another tracked file differs from the baseline is rejected and counts as a candidate. The evaluator never runs git or anything else in the workspace.

**Candidate code is untrusted.** Every process that compiles or links it runs under `tools/candidate.sb`: no network, no reading the held-out set, the evaluator, the verifier source, the checker or the workspace, and writing only to a scratch directory and build output. The scratch directory is emptied before the session. Feedback has absolute paths and the user's name removed. That removes accidental disclosure, and a deliberately encoded path would pass it, so the sandbox is what protects the held-out set. The security of this boundary doesn't depend on the agent behaving well.

## The gate, for every candidate, stopping at the first failure

1. The crate's `kquant_gemv` unit tests.
2. Harness build, and bad geometry refused.
3. **Conformance:** 616 development cases, with default threads and with one thread, bit-compared with `refcheck.gemv.seq_bits`. Added because real activations don't reach subnormals, ties, edge scales or row counts around lane and chunk boundaries.
4. Production build, then a capture on the pinned 16-token prompt: 3,136 calls, 196 operands, `Direct` arm.
5. **Logits bit-identical to the baseline** across that prompt. Added because a witness keeps only the first call per operand, and the logits depend on every position.
6. **`Q8_0_GEMV_SEQ` on all 196 recorded operations.** Required.
7. `Q8_0_GEMV_B1` on 12 operations. Reported, and not a gate.
8. Only then, a development benchmark with capture off, and outputs bit-identical to the baseline's.

## Measurement

- **Primary:** kernel latency through the public `q8_0_gemv`, default thread pool, capture off. For each case, the median of warm repetitions, then the candidate-to-baseline ratio.
- **Statistic:** the median over cases of each case's median ratio across block pairs. 95% CI: percentile bootstrap over block pairs and cases, 4,000 resamples, fixed seed.
- **Design:** separate processes, alternating order (AB, BA, …), each block run only after a 3 s sample shows at least 85% idle.
- **Development:** 56 cases: 2 prompts, layers 2, 10, 18, 26, 7 operators each. 4 block pairs, 15 repetitions.
- **Held-out, never visible to the agent:** 84 cases: 4 other prompts, layers 5, 13, 21, 7 operators each. 8 block pairs, 30 repetitions. A separate 616 conformance cases from another seed.
- **Secondary, reported whichever way they go:** the same kernel measure with one thread, and end-to-end ms per position on a held-out prompt, 6 alternating pairs, capture off.

**Noise floor.** The unchanged kernel through this path measures +0.6% (95% CI −1.3% to +2.7%), which is why a 10% target is resolvable here. It's from 4 pairs on the development set.

## Selection and final evaluation

The final evaluation reports each stage as it starts, uses at most 10 worker processes, and has a hard 24-hour wall clock limit. That limit is a safety ceiling, not an experimental budget. An infrastructure failure or a timeout is `inconclusive`. A crash counts against the candidate only if the baseline survives the same command.

Every rejection records the stage that actually caught it. A fault stopped by unit tests isn't evidence about a later gate. `tools/validate_layers.py` tests the later gates separately.

Using development evidence only, the candidate with the highest development improvement among those that passed every gate. If none passed, or none shows a positive improvement whose CI excludes 0, the result is **no improvement** without a final evaluation. The selected candidate is evaluated once.

**Required on the held-out set:** conformance on both thread settings; logits bit-identical on all 4 held-out prompts; `Q8_0_GEMV_SEQ` on all 196 operations of a held-out prompt's capture; identical benchmark outputs. `Q8_0_GEMV_B1` is reported on all 196.

| Outcome | Rule |
|---|---|
| **Success** | All requirements hold, median improvement ≥ 10%, and the CI's lower bound is above 0 |
| **Rejected** | A requirement fails |
| **No improvement** | All requirements hold, and the CI's upper bound is below 10% |
| **Inconclusive** | Anything else, including any block that couldn't get a quiet machine within 6 hours |

Kernel and inference results are reported separately. A kernel speedup without an inference speedup is a kernel-level result, not an end-to-end win.

## What this can't show

The search is on one model and one machine. A witness is the engine's own report. Agreement with `SEQ` on tried inputs doesn't prove agreement on all inputs. Nothing in this experiment reaches non-finite inputs, which are outside the contracts' domain. Passing here doesn't merge anything: the selected patch goes through normal review and CI.

## Amendment before launch (2026-11-04)

Made before the agent's first turn, with no agent results in existence. Approved by the experiment's owner. Acceptance criteria, gates, workloads, contracts and the three global budgets are unchanged.

1. **Native session.** One continuous Claude Code session with `ncp evaluate` replaces `tools/search.py`, which ran one prompt per candidate. That script never ran a search. The US$15 and 1-hour per-round limits went with it, since there are no rounds.
2. **Version.** Claude Code auto-updated from 2.1.317 to 2.1.318 before launch. The pin is corrected, and auto-update is off for the session.
3. **Stronger boundary.** Added the evaluator's byte-only intake and the candidate sandbox above, because a review found two escapes: the old loop ran git in the agent's repository outside its sandbox, and candidate code was compiled and run with full user rights.
4. **Restart policy.** As stated under Budget.
5. **Commit optional.** Candidates are identified by the hash of the submitted file, not by a commit.
6. **Pausable and resumable (2026-11-04, after item 5, before the agent's first turn).** `evaluate.py`, `final.py` and `run_session.py` changed; no gate, score, workload, threshold or budget did. Originals and their SHA-256 are kept in `validate/pre-resume-tools/`.
   - `touch ~/chris-models/ncp001/PAUSE` pauses at the next stage or block-pair boundary, never mid-measurement. The evaluator waits and continues when the file is removed; the session runner stops the agent, writes `STATE.json` and exits 75.
   - `final.py --resume` skips completed stages and continues the benchmark after the last journalled block pair. It refuses if the candidate, binaries or limit differ. Paused time doesn't count against the wall clock limit. A finished run is never overwritten.
   - `run_session.py --resume` continues the same Claude session. Candidate count, agent hours, evaluation time and spend carry over, so an interruption can't become a new budget. A half-finished evaluation is redone from the saved bytes. Cost is known only when a round ends, so each interruption charges a US$5 reserve (`--reserve-usd`): an estimate, not a bound.
   - The block journal records the binaries, workload, blocks and repetitions, and a resumed measurement is the same measurement: tested with fake binaries, a resumed run was identical to an uninterrupted one.
   - Checked: the unchanged kernel through `final.py`, paused, killed by PID mid-benchmark, then resumed: `no_improvement`, 196/196 `SEQ` and `B1`, logits bit-identical (`validate/final-smoke-baseline.json`). Session pause, simulated crash and resume were tested with a stub agent. The first smoke test, on the earlier code, was stopped for this change and is kept at `validate/smoke-attempt-1-old-code`.


## What pre-launch validation caught

Kept as evidence, not rewritten.

- **First final-evaluation dry run: failed.** `final.py` had no `__main__` guard, so spawned workers re-ran the script and the pool respawned endlessly. It was stopped after 6 h 43 min with the machine at 3% idle. `B1_OPS` was also set in the parent only, so workers would have checked `B1` on 12 operations and then crashed. Both fixed. `search.py` had the same guard flaw.
- **First end-to-end session:** the first sandbox profile blocked the witness write, so the unchanged copy failed at `capture`. Fixed by giving candidates one scratch directory. Kept at `validate/e2e-1-witness-blocked`.
- **First sandbox probes:** 21 of 22 as intended. `build/verifier` was readable because a later `file-read*` rule doesn't override an earlier `file-read-data` allow. Fixed.
- **Test agent declined the hostile kernels** when asked to write them, and said so. That's a statement about the agent and isn't evidence about the sandbox. Kept at `validate/e2e-2-agent-declined`. The owner then submitted them with `tools/probe_feedback.py`, through the same command, queue and evaluator.

- **Hostile kernels, owner-submitted through the real path:** every one rejected at `unit_tests`, because each deliberately fails. Runtime read and listing of the held-out area: `PermissionDenied`. Runtime network: `PermissionDenied`. Compile-time `include_str!`, by relative and absolute path: `Operation not permitted`. Environment and compile-time path disclosure: reached the feedback only as `<path>`. A scan of everything an agent would have received found no absolute paths, no username and no held-out names or content. Two earlier probe runs are kept because they were inconclusive: in the first, compiler warnings pushed the panic text out of the feedback, a flaw that would also have hidden failing tests from the agent and is fixed; in the second, the read and listing probes used a wrong relative path. Results: `validate/probe-feedback`, `-2`, `-3`.
- **First benchmark of the unchanged copy through the real path: invalid.** +17.0%, 95% CI -163.7% to +57.1%, all 8 blocks without a quiet machine. The Mac was on battery with repeated maintenance sleeps, and `fseventsd` was holding 77 GB and about a full core.

## Deviations

None so far.
