# Survey: verifiers for transformers and LLM inference

Compiled on 2026-10-30 from a single research pass. *Unconfirmed* means we did not check the item against a primary
source.

This survey deliberately does not commit to one approach, Lean or otherwise. The guarantees differ in kind:

- **Sound** bound: always correct, but may be loose.
- **Complete** method: always reaches a decision.
- **Bounded** check: holds up to a stated size.
- **Probabilistic** check: wrong with small probability.
- **Empirical** result: holds on the inputs that were tested.

The kind of guarantee goes with every result. One kind must never be reported as another.

## a. Robustness and bound propagation

| Tool / paper | Guarantee | Availability |
|---|---|---|
| auto_LiRPA (Xu et al., NeurIPS'20) https://github.com/Verified-Intelligence/auto_LiRPA | Sound linear bounds on general PyTorch graphs; ships a transformer example | pip package, Python API |
| α,β-CROWN https://github.com/Verified-Intelligence/alpha-beta-CROWN | Sound, and complete via branch-and-bound; supports attention | CLI + YAML, Python API; VNNLIB/ONNX |
| Shi et al., ICLR'20, arXiv 2002.06622 | Certified radii over word embeddings | research code |
| DeepT (PLDI'21) https://github.com/eth-sri/DeepT | Multi-norm zonotope transformers for softmax and dot product | research code |
| ConstraintFlow (SAS'24) https://github.com/uiuc-focal-lab/constraintflow | A language for writing abstract domains, with an automatic soundness check on bounded networks | research code |
| Vertex-Softmax, arXiv 2605.10974 | Claims the tightest sound softmax bound computable from score intervals alone; plugs into CROWN | code |
| AAAI'26 parameterized attention bounds (Huang et al.); ReLU-Catalyzed refinement, arXiv 2605.14294 | Tighter bounds on dot products in attention | no code found |
| Wei et al., AISTATS'23 | Convex softmax bounds | paper |

**Gap.** We found no sound bound propagation evaluated at GPT-2 or LLM scale. Certification at LLM scale uses
randomized smoothing, whose guarantees are probabilistic.

## b. Kernel and compiler equivalence

| Tool | Guarantee | Availability |
|---|---|---|
| Volta, arXiv 2511.12638 | Sound equivalence, complete for a defined class of kernels: FlashAttention FA1/FA2 against naive attention, ~154 s per head | *no public repo found* |
| TensorRight (POPL'25), arXiv 2511.17838 | XLA rewrite rules proved for any rank and size (115 of 175), by reduction to bounded SMT checks | *no public repo found* |
| Mirage (OSDI'25) https://github.com/mirage-project/mirage | Superoptimizer whose equivalence check is probabilistic (random testing over finite fields) | Python package |
| TASO / Tensat (MLSys'21) / PET | Rewrites justified by Z3 against operator axioms (TASO), equality saturation (Tensat) or statistical testing (PET) | repos |
| MLIR-TV (CAV'22) https://github.com/aqjune/mlir-tv | Bounded translation validation for MLIR tensor programs; floating point abstracted | CLI, possibly stale |
| GPUVerify, Faial (CAV'21) | Freedom from data races and barrier divergence only | CLIs |

**Gap.** We found no machine-checked proof of a production FlashAttention kernel and no verifier for Triton.

## c. Certified quantization and floating-point error

| Tool | Guarantee | Availability |
|---|---|---|
| QEBVerif (CAV'23), arXiv 2212.02781 | Sound and complete bound on the error between a network and its quantized form | code; feed-forward networks only |
| Dang et al. (AISTATS'25) | Certified bounds on output change under quantization | MNIST/CIFAR scale |
| Satire, arXiv 2503.05924; FPTaylor | Rigorous rounding-error bounds for straight-line code; Satire handles more than 200K operators | CLIs; no application to attention found |
| Volkova et al., arXiv 2002.03869; Beuzeville et al. (IMA JNA 2025) | Interval and affine rounding-error bounds for DNN inference, including softmax | paper + code |

**Gap, and the opening for LARQL-VERIFY-001 Stage B.** We found nothing that certifies quantization error for
transformers.

## d. Proof-assistant formalizations

| Work | Content |
|---|---|
| TorchLean (Lean 4), arXiv 2602.22631 https://lean-dojo.github.io/TorchLean | Typed tensors, attention and FlashAttention specifications, verified backprop, and a checker for CROWN/LiRPA certificates inside Lean. It *states* that FlashAttention equals standard attention, but does not prove the CUDA code. |
| arXiv 2608.10288 (Lean/mathlib) | Softmax positivity, rows summing to 1, shift invariance |
| arXiv 2608.11173, 2606.30440 | Smaller Lean work involving softmax (*not examined in depth*) |

**Gap.** We found nothing on attention in Coq or Isabelle, and no mechanized transformer-expressivity theorem.

## e. RASP-family compilers

| Work | Notes |
|---|---|
| Tracr (DeepMind) | Compiles RASP to weights |
| ALTA (Shaw et al., TMLR'25), arXiv 2410.18077 | Adds loops and Universal Transformers; ships an interpreter and a compiler |
| C-RASP synthesis + Lustre/Kind2 verification (IJCAI'26) | Push-button model checking of transformer programs; some queries are undecidable |
| D-RASP decompiler (ICML'26) | Recovers programs from trained models |
| C-RASP expressivity results (Yang/Chiang; arXiv 2505.23623) | Proofs on paper only |

## f. Mechanistic interpretability with guarantees

| Work | Guarantee |
|---|---|
| Gross et al., Compact Proofs (NeurIPS'24), arXiv 2406.11779 | Computer-checked lower bounds on the accuracy of Max-of-K models (*whether a proof assistant is involved is unconfirmed*) |
| Solver-Checkable Circuit Explanations, arXiv 2605.24033 | SMT proves or refutes bounded claims about circuits, on small custom architectures |
| Reuse of Verified Circuits, arXiv 2402.02619 | Exhaustive verification of an addition circuit |
| pyvene (NAACL'24) https://github.com/stanfordnlp/pyvene | Interchange interventions; empirical causal evidence, not proof |

## g. Other

| Work | Guarantee |
|---|---|
| BPE tokenizer DFA construction, arXiv 2405.07671 | Correctness proved on paper; no mechanized proof of a real tokenizer found |
| Grammar-constrained decoding, arXiv 2502.05111; Grammar-Aligned Decoding, arXiv 2405.21047 | Soundness and distribution guarantees |
| PyCT | Concolic testing that uses SMT on attention |

We found no verified implementation of a sampler or decoder.

## Ranked as oracles for an autonomous agent

Ranked by strength of guarantee × automation × availability:

1. **α,β-CROWN / auto_LiRPA.** Sound and complete, installable with pip, transformer-aware. Small models only.
2. **C-RASP → Lustre/Kind2.** Push-button SMT model checking of transformer programs.
3. **Mirage's equivalence checker.** Automated and available, but the guarantee is probabilistic.
4. **TorchLean.** The strongest trust base, because certificates are checked in Lean. It needs Lean tooling, and the
   kernels are outside its scope.
5. **Tracr / ALTA, compiling and running.** Exact ground truth at the program level.
6. **Volta / TensorRight.** The strongest kernel and rewrite equivalence, but no public code was found.
7. **Compact proofs, solver-checkable circuits.** Real guarantees, but only on toy tasks.
8. **Satire / QEBVerif.** Rigorous numeric bounds, but adapting them to transformers is manual work.

## Competing approaches for LARQL-VERIFY-001

These are kept open on purpose:

| Approach | Possible role | Main limitation |
|---|---|---|
| TorchLean | Stage C definitions and certificate checking | Coverage of LARQL's quantized formats is unknown |
| Volta-style equivalence | Kernel equivalence (later) | No code available |
| TensorRight | Graph-rewrite correctness (later) | No code available |
| CROWN | Bound propagation over a quantized layer as an alternative route to Stage B | Scale |
| Mirage | Rapid equivalence screening | Probabilistic; can screen but never accept |
| RASP/Kind2 | Second track: program-level discovery with exact ground truth | Restricted language |
