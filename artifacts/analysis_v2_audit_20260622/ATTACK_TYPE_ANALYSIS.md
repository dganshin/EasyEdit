# ATTACK TYPE ANALYSIS

## 结论摘要

- 对 ROME / MEMIT / PACE 来说，`completion` 几乎都是最难清洗的一类攻击。
- MEMIT 并不只在 completion/context 上弱，它在 full private 上对所有 attack type 都弱于 ROME；但 subset 上 completion/context 的残余尤其高。
- ROME 比 MEMIT 更能泛化到非 direct attack，但代价是更高 public damage。
- PACE 的进一步收益主要来自 round2 request 覆盖 residual attack prompts，本质上是更强的 request amplification。
- 这支持 `direct-only editing` 的 attack generalization 不足判断。

