# Ablation Analysis Plan 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: PACE target/max1/max2, CAPE-v0, CAPE-v1, ablation placeholder tables and figures  
Current running artifacts: CAPE-Anchor B20-K0/K1/K2 pending in urgent main  
Pending server artifacts: `table_cape_anchor_rescue.csv`, final `METHOD_CLAIM_DECISION.md`  
Next action: rerun `scripts/build_ablation_assets.py` after CAPE-Anchor results return and replace pending values  
Risk / fallback: if CAPE-Anchor is weak, write public-anchor target conflict and locality-boundary analysis rather than method failure.

## 消融定位

本文的消融实验不是大规模超参数搜索，而是围绕闭环隐私编辑中的三个组件展开：

1. residual leakage re-edit 是否有效；
2. request / subject budget 是否影响 over-refusal；
3. public anchor 是否能缓解公开知识保持崩塌。

因此，当前不新增 lambda sweep、topK sweep、模型、数据集或 public benchmark 扩展。

## 1. PACE 再编辑预算消融

使用已有结果：

```text
ROME direct-only
PACE target_only
PACE max1_per_case
PACE max2_per_person
```

分析指标：

```text
Private Value Contains
Private Refusal
Public Contains
Public Refusal
selected_count
selected_subjects
```

目标结论：

> 闭环再编辑能压低隐私泄露，但再编辑请求越强，public refusal 越高，说明 naive residual re-edit 会引发 over-refusal。

## 2. CAPE 副作用感知筛选消融

使用已有结果：

```text
CAPE-v0
CAPE-v1
```

如果有 selection report，则补充：

```text
selected_count
selected_subjects
attack_type_distribution
```

目标结论：

> CAPE-v1 相比 CAPE-v0 缓解部分公开拒答，但尚未形成全面 Pareto 改进。该结果说明请求筛选策略会改变副作用分布，但隐式筛选不足以完全解决 public retain collapse。

## 3. CAPE-Anchor 公开锚点消融

使用 urgent main 生成的结果：

```text
PACE-Lite B20-K0
CAPE-Anchor B20-K1
CAPE-Anchor B20-K2
```

表格字段：

```text
method
privacy_requests
public_anchor_requests
selected_subjects
Private Value Contains
Private Refusal
Public Contains
Public Refusal
TradeoffScore
claim_level
```

目标结论：

- 如果 K1/K2 public refusal 下降且 public contains 上升：写 public anchor 有效缓解 over-refusal；
- 如果只改善部分指标：写 public anchor 改变副作用分布，但尚未全面解决 trade-off；
- 如果没有改善：写请求层 public anchor 与 privacy refusal 目标存在冲突，需要更强 locality-constrained editing。

## 输出文件

```text
artifacts/paper_assets_20260623/tables/table_ablation_pace_budget.csv
artifacts/paper_assets_20260623/tables/table_ablation_cape_selection.csv
artifacts/paper_assets_20260623/tables/table_ablation_cape_anchor.csv
artifacts/paper_assets_20260623/figures/fig_ablation_privacy_utility.png
artifacts/paper_assets_20260623/figures/fig_ablation_public_refusal.png
```

未完成项必须写 `[pending_server_result]`，不能填 0、空白或估计值。
