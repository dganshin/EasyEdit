# 论文结果更新计划 V6

本文档用于把当前实验闭合进课程论文。当前不再新增 TOFU、Enron、LLaMA-2、MEND/SERAC 训练或 CAPE-Anchor 训练实验。

## 1. 当前只保留四类任务

1. 公开数据集完整矩阵：
   - CounterFact / zsRE
   - Qwen2.5-7B / GPT-J-6B
   - ROME / FT / KN / IKE
   - ROME+PACE-Edit / ROME+CAPE-Edit
2. synthetic privacy 主任务补基础编辑器：
   - Qwen synthetic privacy v2
   - FT / KN / IKE
3. 现有创新点图表化：
   - private/public 解耦
   - over-refusal
   - attack-type split
   - privacy-utility trade-off
   - PACE/CAPE selection stats
4. 最终论文可用汇总：
   - synthetic 主结果表
   - public baseline 表
   - public wrapper 表
   - failure matrix
   - paper-ready figures/tables

## 2. 新增实验小节结构

建议第 4 章实验结构：

```text
4.1 实验设置
4.2 合成隐私基准上的主结果
4.3 不同基础编辑器在隐私清洗任务中的对比
4.4 PACE/CAPE 闭环策略与副作用分析
4.5 公开知识编辑基准上的多方法对比
4.6 PACE/CAPE 在公开基准上的闭环迁移验证
4.7 过度拒答、攻击类型与隐私—效用权衡分析
4.8 局限性分析
```

## 3. 已完成结果

当前已完成或已有小文件 artifact 的部分：

- synthetic privacy v2 数据集与 LoRA merged leakage model；
- ROME direct-only；
- MEMIT direct-only；
- PACE variants；
- CAPE-v0 / CAPE-v1；
- public benchmark 子集构造；
- Qwen/GPT-J public baseline 运行脚本；
- public PACE/CAPE wrapper 脚本；
- metric audit 结果；
- trade-off / over-refusal / attack-type 分析的已有脚本与部分产物。

## 4. 仍需跑完或拉回的结果

必须闭合：

- CounterFact / zsRE × Qwen / GPT-J × ROME / FT / KN / IKE；
- CounterFact / zsRE × Qwen / GPT-J × ROME+PACE-Edit / ROME+CAPE-Edit；
- synthetic privacy v2 × FT / KN / IKE。

如果 IKE 工程风险较高，最低保底是 synthetic privacy v2 上先拿到 FT / KN，并把 IKE 写入 failure / not_run。

## 5. 表格放置建议

| 表 | 文件 | 论文位置 |
| --- | --- | --- |
| synthetic 主结果表 | `artifacts/final_comparison_20260622/paper_tables/table_synthetic_main_results.csv` | 4.2 |
| synthetic extra editors | `table_synthetic_extra_editors.csv` | 4.3 |
| public baseline | `table_public_baseline_counterfact_zsre.csv` | 4.5 |
| public wrapper | `table_public_wrapper_pace_cape.csv` | 4.6 |
| PACE/CAPE selection stats | `table_pace_cape_selection_stats.csv` | 4.4 / 4.6 |
| metric definitions | `table_metric_definitions.csv` | 4.1 或附录 |

## 6. 图放置建议

| 图 | 文件 | 论文位置 |
| --- | --- | --- |
| privacy-utility trade-off | `fig_privacy_utility_tradeoff.png` | 4.7 |
| public refusal comparison | `fig_public_refusal_comparison.png` | 4.7 |
| attack-type breakdown | `fig_attack_type_breakdown.png` | 4.7 |
| public reliability/locality | `fig_public_benchmark_reliability_locality.png` | 4.5 / 4.6 |
| pipeline overview | `fig_pipeline_overview_placeholder.png` 或手绘框架图 | 3.1 / 4.1 |

## 7. 摘要更新方向

摘要应强调：

- 构建 private/public 解耦的 synthetic privacy benchmark；
- 通过 LoRA 注入构造可控 leakage model；
- 系统比较 ROME、MEMIT、FT、KN、IKE、PACE、CAPE；
- 发现 privacy suppression 与 public retain / over-refusal 之间存在显著 trade-off；
- 将 PACE/CAPE 抽象为 closed-loop request selection，并在 CounterFact/zsRE 上验证其公开编辑迁移性。

不要在摘要里写过多“指标命名审计”细节；指标审计放到 4.1 或附录。

## 8. 结论更新方向

结论应写：

> 本文并未声称完全解决隐私知识清洗，而是构建了可控实验闭环，揭示了现有模型编辑方法在隐私压制和公开知识保持之间的冲突，并通过 PACE/CAPE 的闭环请求选择实验展示了降低副作用的可检验路径。

不要写：

> PACE/CAPE 已经稳定优于所有 baseline。

除非最终结果确实支持。

## 9. 当前执行命令

public 全方法统一入口：

```bash
ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
RUN_PUBLIC_WRAPPERS=1 \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_public_all_methods_full.sh
```

只补 public wrapper：

```bash
ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_missing_public_wrappers.sh
```

synthetic privacy extra editors：

```bash
METHODS=FT,KN,IKE \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_synthetic_privacy_extra_editors.sh
```

生成 paper-ready 图表：

```bash
python scripts/build_paper_ready_figures_and_tables.py
```

## 10. 禁止项

- 不要新增 TOFU / Enron / The Pile。
- 不要新增 LLaMA-2。
- 不要训练 MEND / SERAC。
- 不要现在训练 LoRA/SFT。
- 不要继续设计新方法。
- 不要把 public benchmark 当成 PII 任务写。
- 不要把未完成实验写成已完成。
- 不要把大模型、大缓存、大输出提交到 Git。
