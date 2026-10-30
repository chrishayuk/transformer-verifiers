# Claims checked against primary sources

An earlier brainstorm cited a number of 2026 tools and papers. Each claim is checked here against a primary source.
Checked on 2026-10-30.

| # | Claim | Verdict | Source | Correction |
|---|---|---|---|---|
| 1 | α,β-CROWN supports self-attention, has a Python API, and was first at VNN-COMP every year 2021–2026 | **Verified, with one caveat** | https://github.com/Verified-Intelligence/alpha-beta-CROWN ; VNN-COMP 2025 report, arXiv 2512.19007 | The README's News section claims 2021–2026, but its About section says 2021–2025. The official 2026 results were not seen. |
| 2 | "Parameterized Abstract Interpretation for Transformer Verification", AAAI 2026 | **Verified** | https://ojs.aaai.org/index.php/AAAI/article/view/40860 | Huang, Wei, Isac, Wu, Wu, Barrett. AAAI vol. 40, pp. 35500–35508. Parameterized linear bounds for the inner products in attention. |
| 3 | "Synthesis and Verification of Transformer Programs", IJCAI 2026; transformer verification is undecidable | **Verified; the undecidability claim is overstated** | https://www.ijcai.org/proceedings/2026/434 ; arXiv 2602.16473 | Jiang, Hague, Rümmer, Lin. It learns C-RASP by simulated annealing, translates to Lustre, and checks with Kind2 (cvc5/Z3). The undecidable problem is the *emptiness of a C-RASP program's language*, not transformer verification in general. |
| 4 | "Discovering Interpretable Algorithms by Decompiling Transformers to RASP", 2026 | **Verified** | arXiv 2602.08857 ; https://proceedings.mlr.press/v306/huang26b.html ; https://github.com/lacoco-lab/decompiling_transformers | Also at ICML 2026. It decompiles to D-RASP and prunes using causal interventions. |
| 5 | Tracr compiles RASP to weights (sort, histogram, balanced parentheses) | **Verified** | https://github.com/google-deepmind/tracr (`tracr/compiler/lib.py`) | `make_sort`, `make_hist`, `make_frac_prevs`, `make_shuffle_dyck`, `make_pair_balance`. |
| 6 | Certora Gambit improves specs; Certora published a July 2026 Solana stake-pool report | **Verified; the date is misleading** | https://github.com/Certora/gambit ; https://www.certora.com/blog/formal-verification-solana-stake-pool | The blog post is dated 2026-07-16, but the audit itself was done in June 2025. |
| 7 | Marabou verifies transformer properties | **Partly true** | https://github.com/NeuralNetworkVerification/Marabou ; arXiv 2401.14461 | Marabou 2.0 handles softmax and bilinear constraints by relaxing them to linear ones. It has no attention-specific support or benchmarks, so in practice it is for feed-forward networks. |

## Claims about LARQL in the same brainstorm

These are checked in [`../larql/CAPABILITIES.md`](../larql/CAPABILITIES.md). One claim is withdrawn:

- **"An architectural-invariants research programme across model families."** There is no such programme in the
  repository.
  - The 117-checkpoint arch-conformance sweep only checks plans and admission. It reads headers and never runs a
    forward pass.
  - `make bench-cross-arch` measures speed only.
  - The Hugging Face collection the brainstorm cited was not checked.
