# 当前需要运行的脚本功能总结（给 GPT 审查）

本文档用于让 GPT 审查当前实验执行是否仍然服务论文主线。核心问题不是继续扩新坑，而是闭合当前矩阵：公开数据集上有 baseline 和 PACE/CAPE wrapper，synthetic privacy 上补 FT/KN/IKE，并把已有结果汇总成论文图表。

## 1. 当前论文目标

当前论文不能押注“CAPE 一定显著优于 PACE”。正确定位是：

- 如果 CAPE 在某些指标上形成更合理 trade-off，则写成有效改进；
- 如果 CAPE 只比 CAPE-v0 少崩一些，则写成副作用感知筛选的诊断价值；
- 如果 CAPE 全面不优，则降级为负结果 / 副作用约束探索。

论文主贡献应分散到：

- private/public 解耦合成隐私基准；
- LoRA 可控隐私泄露模型；
- ROME/MEMIT/FT/KN/IKE/PACE/CAPE 多编辑器比较；
- over-refusal 指标；
- attack-type split；
- privacy-utility trade-off；
- CounterFact/zsRE 公开迁移验证。

## 2. 脚本一：`scripts/run_public_all_methods_full.sh`

### 2.1 这个脚本解决什么问题

它是当前公开数据集实验的统一入口，避免之前把公开数据集只跑成 ROME/FT/KN/IKE 复现 baseline，而漏掉本文自己的 PACE/CAPE wrapper。

### 2.2 自动识别实例

脚本会检查：

```text
/root/autodl-tmp/models/Qwen2.5-7B
/root/autodl-tmp/models/gpt-j-6B
```

逻辑：

- 只检测到 Qwen：自动跑 Qwen public 矩阵；
- 只检测到 GPT-J：自动跑 GPT-J public 矩阵；
- 两个都存在：脚本失败并要求显式设置 `INSTANCE_MODEL=qwen` 或 `INSTANCE_MODEL=gptj`，防止两个实例混跑；
- 都不存在：脚本失败。

### 2.3 它会跑什么

在当前实例对应模型上，一次性跑：

```text
CounterFact / zsRE
× ROME / FT / KN / IKE
+ ROME+PACE-Edit / ROME+CAPE-Edit
```

默认配置：

```text
ART_ROOT=artifacts/public_benchmarks_20260623_200
MAX_CASES=200
RUN_PUBLIC_WRAPPERS=1
SHUTDOWN_ON_EXIT=0
```

### 2.4 baseline 部分

它调用：

```text
scripts/run_public_qwen_full.sh
scripts/run_public_gptj_full.sh
```

baseline 方法：

```text
ROME, FT, KN, IKE
```

数据集：

```text
CounterFact
zsRE
```

每个方法独立输出目录，例如：

```text
artifacts/public_benchmarks_20260623_200/qwen_counterfact/ROME/
artifacts/public_benchmarks_20260623_200/qwen_counterfact/FT/
artifacts/public_benchmarks_20260623_200/gptj_zsre/KN/
```

### 2.5 是否支持断点续跑

支持。底层调用 `scripts/run_public_editing_baselines.py` 时带：

```text
--resume_skip_completed
--isolate_methods
```

含义：

- 如果某个方法目录已有 `summary.json` 且 `status=ok`，重跑时会跳过；
- 每个方法用独立 Python 子进程运行，降低显存残留和方法间污染风险；
- 如果单个方法失败，会写 failed summary / traceback，不应伪造成成功。

### 2.6 wrapper 部分

baseline 后默认自动调用：

```text
scripts/run_public_closed_loop_wrappers.sh
```

wrapper 方法：

```text
ROME+PACE-Edit
ROME+CAPE-Edit
```

关键点：

- wrapper 只以 ROME 为基础编辑器；
- 它读取 `ROME/per_case_results.jsonl`；
- 如果找不到 ROME per-case，会写 `ROME_PACE_EDIT` 和 `ROME_CAPE_EDIT` 的 failed summary，并进入 failure matrix，而不是静默跳过；
- PACE/CAPE 的最终请求集合是：

```text
R_final = R_round1 ∪ R_round2
```

也就是使用：

```text
pace_union_dataset.json
cape_union_dataset.json
```

不是只拿 round2 失败样本单独跑。

### 2.7 输出结果

主要输出：

```text
artifacts/public_benchmarks_20260623_200/
artifacts/final_comparison_20260623_200/
```

预期最终表中应出现：

```text
CounterFact × Qwen × ROME / FT / KN / IKE / ROME+PACE-Edit / ROME+CAPE-Edit
zsRE       × Qwen × ROME / FT / KN / IKE / ROME+PACE-Edit / ROME+CAPE-Edit
CounterFact × GPT-J × ROME / FT / KN / IKE / ROME+PACE-Edit / ROME+CAPE-Edit
zsRE       × GPT-J × ROME / FT / KN / IKE / ROME+PACE-Edit / ROME+CAPE-Edit
```

### 2.8 是否满足论文要求

满足“公开数据集不只是复现 baseline”的要求。它让本文自己的 PACE/CAPE wrapper 进入 CounterFact/zsRE，并且保留 ROME/FT/KN/IKE 作为对照。

但注意：公开数据集不是 PII 清洗任务，论文只能写成“闭环请求选择在公开 factual editing 上的迁移验证”，不能写成“公开数据集证明隐私清洗成功”。

## 3. 脚本二：`scripts/run_missing_public_wrappers.sh`

### 3.1 这个脚本解决什么问题

如果当前实例已经跑完或部分跑完 public baseline，但当时 full 脚本还没有自动接 PACE/CAPE wrapper，就用这个脚本只补 wrapper。

### 3.2 它会做什么

自动识别当前实例模型，然后只运行：

```text
ROME+PACE-Edit
ROME+CAPE-Edit
```

不会重跑：

```text
ROME / FT / KN / IKE baseline
```

### 3.3 它依赖什么

每个数据集必须已经有：

```text
<ART_ROOT>/<model>_<dataset>/ROME/per_case_results.jsonl
```

例如：

```text
artifacts/public_benchmarks_20260623_200/qwen_counterfact/ROME/per_case_results.jsonl
artifacts/public_benchmarks_20260623_200/gptj_zsre/ROME/per_case_results.jsonl
```

如果缺失，会写 failed summary，不静默成功。

### 3.4 输出

会生成或更新：

```text
<ART_ROOT>/<model>_<dataset>/ROME_PACE_CAPE_SELECTION/
<ART_ROOT>/<model>_<dataset>/ROME_PACE_EDIT/
<ART_ROOT>/<model>_<dataset>/ROME_CAPE_EDIT/
artifacts/final_comparison_20260623_200/
```

selection report 包含：

```text
candidate_count
selected_count
pace_selected_count
cape_selected_count
round1_count
round2_count
union_count
pace_round2_count
cape_round2_count
pace_union_count
cape_union_count
skipped_by_locality_risk
skipped_by_subject_or_relation_budget
selected_case_ids
```

### 3.5 是否满足论文要求

满足“当前 baseline 已经很贵，不能为了补 wrapper 重跑 baseline”的要求。适合现在两个实例 baseline 跑完后立即补本文方法。

## 4. 脚本三：`scripts/run_synthetic_privacy_extra_editors.sh`

### 4.1 这个脚本解决什么问题

它补 synthetic privacy 主任务上的其他 EasyEdit 基础编辑器，避免论文主任务只和 ROME/MEMIT/PACE/CAPE 比，缺少 FT/KN/IKE。

### 4.2 输入

默认输入：

```text
DATASET=artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json
MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged
REQUESTS_PATH=artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json
METHODS=FT,KN,IKE
```

### 4.3 它会跑什么

对每个方法：

```text
FT
KN
IKE
```

调用：

```text
scripts/run_privacy_refusal_edit.py
```

并开启：

```text
--full_private_eval
--eval_public
--disable_fluency_eval
```

也就是说，每个方法会跑 synthetic privacy 的 full private eval 和 full public eval。

### 4.4 输出

每个方法独立目录：

```text
artifacts/run_20260622_v2_ft_baseline/
artifacts/run_20260622_v2_kn_baseline/
artifacts/run_20260622_v2_ike_baseline/
```

### 4.5 是否支持失败记录

当前脚本本身是顺序运行。如果某方法在 `run_privacy_refusal_edit.py` 内失败，依赖底层脚本写错误；但这个 shell 当前不是“失败后继续跑下一个方法”的容错式 sweep。若 GPT 认为 IKE 风险高，建议后续把它改成每个方法失败后写 failure summary 并继续。

### 4.6 是否满足论文要求

满足“synthetic privacy 主任务补 FT/KN/IKE”这个方向，但容错性还可以加强。最低保底应该先跑：

```text
METHODS=FT,KN
```

如果 FT/KN 成功，再跑 IKE。

## 5. 脚本四：`scripts/build_paper_ready_figures_and_tables.py`

### 5.1 这个脚本解决什么问题

它把现有结果整理成论文可用表格和图，不需要 GPU。

### 5.2 输入

默认读取：

```text
artifacts/analysis_v2_audit_20260622/
artifacts/public_benchmarks_20260623_200/
artifacts/final_comparison_20260622/
各 synthetic run artifact
```

### 5.3 输出

表格：

```text
artifacts/final_comparison_20260622/paper_tables/table_synthetic_main_results.csv
artifacts/final_comparison_20260622/paper_tables/table_synthetic_extra_editors.csv
artifacts/final_comparison_20260622/paper_tables/table_public_baseline_counterfact_zsre.csv
artifacts/final_comparison_20260622/paper_tables/table_public_wrapper_pace_cape.csv
artifacts/final_comparison_20260622/paper_tables/table_pace_cape_selection_stats.csv
artifacts/final_comparison_20260622/paper_tables/table_metric_definitions.csv
```

图：

```text
artifacts/final_comparison_20260622/paper_figures/fig_privacy_utility_tradeoff.png
artifacts/final_comparison_20260622/paper_figures/fig_public_refusal_comparison.png
artifacts/final_comparison_20260622/paper_figures/fig_attack_type_breakdown.png
artifacts/final_comparison_20260622/paper_figures/fig_public_benchmark_reliability_locality.png
```

### 5.4 当前本地运行状态

本地已运行一次。当前结果：

```text
synthetic rows: 9
public rows: 0
PACE/CAPE selection rows: 0
```

原因：public 200 的服务器结果还没拉回本地。因此 public 表为空是正确缺失标记，不是伪造。

### 5.5 是否满足论文要求

部分满足。它已经能生成 synthetic 主表、指标定义表、trade-off / over-refusal / attack-type 图。等 public 结果拉回后，重新运行即可刷新 public baseline / wrapper 表。

## 6. 2026-06-23 更新：已补主线救火脚本

根据最新审查，public 脚本方向基本合格，但不能继续让 public benchmark 抢主线。当前已经新增或加强以下脚本：

```text
scripts/run_synthetic_privacy_extra_editors.sh
scripts/run_cape_anchor_rescue.sh
scripts/run_urgent_main_experiments_48g.sh
scripts/decide_method_claim_level.py
```

### 6.1 `run_synthetic_privacy_extra_editors.sh`

现在它不是简单顺序脚本，而是容错 sweep：

- 默认跑 `FT,KN,IKE`；
- 每个方法独立子进程；
- 成功写 `summary.json`；
- 失败写 `summary.json` 和 `synthetic_extra_editors_failure_matrix.csv`；
- 下次重跑会跳过 `status=ok` 的方法；
- 每个方法前后尝试释放 GPU cache，降低显存残留导致的连锁 OOM。

输出：

```text
artifacts/run_20260623_v2_ft_baseline/
artifacts/run_20260623_v2_kn_baseline/
artifacts/run_20260623_v2_ike_baseline/
artifacts/final_comparison_20260623_urgent/synthetic_extra_editors_failure_matrix.csv
```

### 6.2 `run_cape_anchor_rescue.sh`

该脚本只跑有限 CAPE-Anchor rescue，不做普通 PACE 调参。默认配置：

```text
PACE_LITE_B20_K0: top20 privacy residual, privacy_per_subject=1, public_anchor_per_subject=0
CAPE_ANCHOR_B20_K1: top20 privacy residual, privacy_per_subject=1, public_anchor_per_subject=1
CAPE_ANCHOR_B20_K2: top20 privacy residual, privacy_per_subject=1, public_anchor_per_subject=2
```

最终请求集合：

```text
R_final = R_round1 ∪ R_privacy ∪ R_anchor
```

输出：

```text
artifacts/run_20260623_cape_anchor_rescue/<config>/
artifacts/final_comparison_20260623_urgent/cape_anchor_rescue_results.csv
artifacts/final_comparison_20260623_urgent/cape_anchor_failure_matrix.csv
```

该脚本的论文问题是：

> public anchor 是否能在保持 privacy suppression 的同时，缓解 naive PACE / CAPE 的 public collapse 和 over-refusal。

### 6.3 `run_urgent_main_experiments_48g.sh`

这是当前主推总控入口。它依次执行：

```text
Phase 0: 环境和路径检查
Phase 1: synthetic FT/KN/IKE
Phase 2: CAPE-Anchor B20-K0/K1/K2
Phase 3: public wrapper 补跑（只在已有 ROME per_case 时运行，不重跑 public baseline）
Phase 4: 论文表格/图
Phase 5: method claim decision
```

关键点：

- 不下载新模型；
- 不扩新数据集；
- 不重跑 public baseline；
- 不修改 EasyEdit / ROME / MEMIT 底层；
- 默认不自动关机；
- 失败写 `urgent_main_failure_matrix.csv`，继续执行能继续的阶段。

### 6.4 `decide_method_claim_level.py`

该脚本读取 ROME、PACE、CAPE-v0/v1 和 CAPE-Anchor 的结果，输出：

```text
artifacts/final_comparison_20260623_urgent/method_claim_metrics.csv
artifacts/final_comparison_20260623_urgent/method_claim_decision.json
artifacts/final_comparison_20260623_urgent/METHOD_CLAIM_DECISION.md
docs/METHOD_CLAIM_DECISION.md
```

判断口径：

- Claim A：可以写“有限有效改进 / 更合理折中”；
- Claim B：只能写“机制性缓解 / 局部改善”；
- Claim C：只能写“负结果、诊断发现或后续方向”。

这个脚本用于防止论文把负结果硬包装成显著成功。

## 7. 当前仍需 GPT 审查的问题

请 GPT 重点检查：

1. CAPE-Anchor 的 `R_final = R_round1 ∪ R_privacy ∪ R_anchor` 是否能支撑“public-anchor constrained re-edit”的论文叙事？
2. B20-K0/K1/K2 是否足够作为救火级别的有限 ablation？
3. synthetic FT/KN/IKE 的失败容错是否足够，是否还需要单独先跑 `METHODS=FT,KN`？
4. `decide_method_claim_level.py` 的 Claim A/B/C 判据是否过严或过松？
5. 如果 CAPE-Anchor 不优，论文是否应把贡献降级为 benchmark + trade-off diagnosis + closed-loop wrapper analysis？

## 8. 当前已收口和仍然没有做的事

当前已经支持：

- public baseline + PACE/CAPE wrapper；
- synthetic FT/KN/IKE 容错 sweep；
- CAPE-Anchor B20-K0/K1/K2 有限救火；
- paper-ready 表图；
- metric audit；
- Claim A/B/C 自动判定。

当前明确不做：

- 大规模 CAPE-budget / CAPE-score sweep；
- 新公开数据集；
- 新模型；
- MEND/SERAC 训练；
- LoRA/SFT 新训练；
- 普通 PACE 调参。

## 9. 当前建议运行顺序

### 9.1 两个 public 实例

如果 baseline 已经跑完，先只补 wrapper：

```bash
cd /root/autodl-tmp/projects/EasyEdit
git -c http.version=HTTP/1.1 pull --ff-only
conda activate easyedit

ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_missing_public_wrappers.sh
```

如果还没跑 baseline 或不确定，则运行统一入口：

```bash
ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
RUN_PUBLIC_WRAPPERS=1 \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_public_all_methods_full.sh
```

### 9.2 synthetic privacy 实例

先保底跑 FT/KN：

```bash
METHODS=FT,KN \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_synthetic_privacy_extra_editors.sh
```

如果 FT/KN 成功，再跑 IKE：

```bash
METHODS=IKE \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_synthetic_privacy_extra_editors.sh
```

### 9.3 本地生成论文表图

服务器小结果拉回后：

```bash
python scripts/build_paper_ready_figures_and_tables.py
```

## 8. 是否仍然存在风险

存在，主要有四个：

1. CAPE/PACE wrapper 在 public benchmark 上可能不优于 ROME。这不能硬写成成功，只能写迁移边界或负结果。
2. synthetic FT/KN/IKE 可能有工程失败，尤其 IKE。如果失败，要写 failure matrix，不要删除。
3. 当前没有 CAPE rescue sweep 和 tradeoff 自动分类脚本，无法自动寻找 Pareto 点。
4. public benchmark 是公开 factual editing，不是 PII 清洗任务，论文必须分开解释。

## 9. 给 GPT 审查的问题

请 GPT 重点检查：

1. 这些脚本是否已经覆盖论文必须的公开矩阵？
2. 是否还必须现在实现 CAPE rescue sweep，还是先等 public wrapper / synthetic FT-KN 结果？
3. `run_synthetic_privacy_extra_editors.sh` 是否需要改成失败后继续跑下一个方法？
4. 当前 public wrapper 的 `R_final = R_round1 ∪ R_round2` 是否足够支撑“closed-loop wrapper”叙事？
5. 当前论文主张应该压到 Claim A、B、还是 C？
