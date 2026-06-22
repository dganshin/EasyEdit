# OVER REFUSAL ANALYSIS

## 结论摘要

- Pre leakage model public_refusal_rate = 0.0000
- ROME public_refusal_rate = 0.4679
- MEMIT public_refusal_rate = 0.1484
- PACE target_only public_refusal_rate = 0.9675
- PACE max1_per_case public_refusal_rate = 0.9611
- PACE max2_per_person public_refusal_rate = 0.8115

1. PACE public contains 的下降主要伴随 public refusal rate 大幅上升，支持 over-refusal / over-editing 解释。
2. ROME 的 public refusal 也显著上升，说明它的 public damage 不只是答错，也包含误拒答。
3. MEMIT 的 public retain 更高，一部分原因确实是 public refusal 更低；同时 `public_contains` 本身又是较宽松的包含匹配，因此要谨慎解释成“保真完全更好”。
4. private refusal 越高的配置通常伴随 public refusal 更高，PACE 最明显。
5. 当前证据更支持：PACE 是强 suppress + 强副作用，而不是精确 privacy cleaning。

