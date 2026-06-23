# CAPE-Anchor Current Positioning

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Pending server artifacts: B20-K0 / B20-K1 / B20-K2 results  
Completed local writing tasks: method positioning and success criteria  
Next action after server finishes: decide whether CAPE-Anchor supports Claim A, B, or C

## 方法定位

CAPE-Anchor 不是修改 ROME、MEMIT 或 EasyEdit 底层算法，而是在二轮请求选择阶段加入显式公开知识锚点。其目的不是继续做普通 PACE 参数调优，而是检验 public retain constraint 是否能从隐式风险约束变成显式编辑请求，从而缓解 residual leakage re-edit 带来的 over-refusal。

## 与 PACE/CAPE-v1 的区别

- PACE：从 residual leakage 构造 privacy refusal requests。
- CAPE-v1：限制请求数量、主体覆盖和 prompt 形式，降低 naive re-edit 的副作用。
- CAPE-Anchor：同时构造 privacy refusal requests 与 public anchor retain requests。

核心集合为：

```text
R_final = R_round1 ∪ R_privacy ∪ R_anchor
```

## 有限配置

- B20-K0：20 个主体，每个主体 1 条 privacy request，0 条 public anchor，作为 PACE-lite 对照。
- B20-K1：20 个主体，每个主体 1 条 privacy request，1 条 public anchor。
- B20-K2：20 个主体，每个主体 1 条 privacy request，2 条 public anchors。

## 成功判据

优先观察：

- Private Value Contains 是否仍低于 ROME direct；
- Public Contains 是否高于 PACE max2/person；
- Public Refusal 是否低于 PACE max2/person；
- 是否形成比 CAPE-v1 更合理的 trade-off。

若未形成全面 Pareto 改进，论文中应写成机制性边界分析，而不是方法失败。
