# Figure Table Plan 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: paper asset scripts; six polished placeholder/current figures; CSV placeholder tables  
Current running artifacts: Qwen public 200-case benchmark; CAPE-Anchor pending  
Pending server artifacts: public wrapper rows and CAPE-Anchor points  
Completed local writing tasks: figure/table list and generation script plan  
Next action: rerun `scripts/build_paper_placeholder_tables.py`, `scripts/render_polished_paper_figures.py`, and final comparison scripts after server artifacts return  
Risk / fallback: if CAPE-Anchor is weak, figures should show trade-off/boundary rather than hide weak points.

## 论文表格

| 编号 | 标题 | 来源 | 当前状态 |
|---|---|---|---|
| 表1 | V2 合成隐私评测基准统计 | synthetic dataset summary | 可先写 |
| 表2 | 实验平台与主要配置 | run manifests / scripts | 可先写 |
| 表3 | 不同编辑方法在 synthetic privacy v2 上的主结果 | `table_synthetic_main_results_placeholder.csv` | 部分待填 |
| 表4 | PACE/CAPE/CAPE-Anchor 副作用对比 | `table_cape_anchor_placeholder.csv` | 待 CAPE-Anchor |
| 表5 | Qwen public benchmark 迁移验证结果 | `table_public_qwen_placeholder.csv` | 待 Qwen wrapper |
| 表6 | 失败方法与未纳入主表原因 | `table_failure_matrix_placeholder.csv` | 可先写 |
| 表7 | PACE 再编辑预算消融 | `table_ablation_pace_budget.csv` | 部分待填 |
| 表8 | CAPE 请求筛选消融 | `table_ablation_cape_selection.csv` | 部分待填 |
| 表9 | CAPE-Anchor 公开锚点消融 | `table_ablation_cape_anchor.csv` | 待 CAPE-Anchor |

## 论文图

| 编号 | 标题 | 输出文件 |
|---|---|---|
| 图1 | 总体技术路线 | `fig1_pipeline_overview.{png,svg,pdf}` |
| 图2 | PACE/CAPE/CAPE-Anchor 请求构造机制 | `fig2_request_construction.{png,svg,pdf}` |
| 图3 | 隐私压制—知识保持权衡散点图 | `fig3_privacy_utility_tradeoff.{png,svg,pdf}` |
| 图4 | Public Refusal 对比图 | `fig4_public_refusal_comparison.{png,svg,pdf}` |
| 图5 | Attack-type breakdown 图 | `fig5_attack_type_breakdown.{png,svg,pdf}` |
| 图6 | Qwen public benchmark reliability/locality 图 | `fig6_public_benchmark_migration_placeholder.{png,svg,pdf}` |
| 图7 | 消融实验 privacy-utility trade-off 图 | `fig_ablation_privacy_utility.{png,svg,pdf}` |
| 图8 | 消融实验 Public Refusal 对比图 | `fig_ablation_public_refusal.{png,svg,pdf}` |

图表风格：白底、细轴线、300dpi PNG、SVG/PDF 矢量版本、图注说明 pending 点，不使用花哨渐变。
