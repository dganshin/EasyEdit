# Ablation Section Draft 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: PACE/CAPE existing ablation rows; pending-aware ablation tables and figures  
Current running artifacts: CAPE-Anchor B20-K0/K1/K2 not yet backfilled  
Pending server artifacts: CAPE-Anchor rescue metrics and final claim decision  
Next action: after urgent main returns, replace `[pending_server_result]` in ablation tables and refresh this section  
Risk / fallback: if CAPE-Anchor is weak, frame it as target conflict and locality-boundary analysis, not method collapse.

## 4.x 消融实验与副作用分析

本文的消融实验不采用大规模超参数搜索，而是围绕闭环隐私编辑中的三个关键因素展开：再编辑预算、主体级副作用约束和公开知识锚点。通过比较无约束闭环、预算约束闭环和锚点约束闭环，可以分析隐私压制提升是否来自更强拒答，以及公开知识锚点是否能够缓解过度拒答。

首先，PACE 再编辑预算消融比较 ROME direct-only、PACE target_only、PACE max1_per_case 与 PACE max2_per_person。ROME direct-only 代表单轮隐私拒答编辑，PACE 系列则在第一轮编辑后继续根据 residual leakage 构造二轮请求。已有结果显示，随着再编辑强度增加，Private Value Contains 可以被进一步压低，但 Public Contains 同步下降，Public Refusal 上升。这说明闭环再编辑的核心风险不是“能否压低隐私泄露”，而是“是否通过泛化拒答实现隐私压制”。因此，PACE 的价值在于揭示 residual leakage re-edit 的隐私压制能力及其副作用边界。

其次，CAPE 副作用感知筛选消融比较 CAPE-v0 与 CAPE-v1。CAPE-v0 采用更宽的 residual leakage 选择，能够获得较强隐私压制，但公开知识保持几乎塌缩。CAPE-v1 通过限制请求数量、主体覆盖范围和 prompt 形式，在 Public Refusal 上相对 v0 有所缓解，但仍未形成全面 Pareto 改进。该结果表明，请求筛选策略确实会改变副作用分布，但仅依赖隐式筛选仍不足以完全解决 public retain collapse。

最后，CAPE-Anchor 消融用于检验显式公开知识锚点的作用。本文只评估 PACE-Lite B20-K0、CAPE-Anchor B20-K1 与 CAPE-Anchor B20-K2 三个配置。其中 K0 不加入 public anchor，仅作为无公开约束的闭环对照；K1 为每个 selected subject 加入 1 条 public anchor；K2 加入 2 条 public anchors。该消融回答的问题是：显式加入公开知识锚点，是否能够降低 Public Refusal、提高 Public Contains，并保持 Private Value Contains 低于 ROME direct。具体结果将在 CAPE-Anchor 返回后写入 `table_ablation_cape_anchor.csv`。

如果 K1/K2 相比 K0 降低 Public Refusal 并提升 Public Contains，则说明 public anchor retain constraint 对缓解 over-refusal 有实证价值；如果只改善部分指标，则说明 public anchor 能改变副作用分布但尚未全面解决 trade-off；如果没有改善，则说明 privacy refusal requests 与 public anchor requests 可能存在目标冲突，后续需要显式 retain loss 或 locality-constrained editing。

