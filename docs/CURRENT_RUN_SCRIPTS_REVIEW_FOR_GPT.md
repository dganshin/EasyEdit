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

## 6. 当前尚未实现但 GPT 新建议提到的脚本

以下脚本目前还没有实现：

```text
scripts/run_cape_rescue_sweep.py
scripts/classify_cape_tradeoff_results.py
docs/PUBLIC_WRAPPER_RESULT_INTERPRETATION.md
docs/METHOD_CLAIM_DECISION.md
```

也就是说，当前代码已经支持：

- public baseline + PACE/CAPE wrapper；
- synthetic FT/KN/IKE；
- paper-ready 表图；
- metric audit；

但还没有支持：

- CAPE-budget / CAPE-anchor / CAPE-score 的有限 rescue sweep；
- CAPE 配置自动分为 good_tradeoff / privacy_strong_but_overrefusal / weak_or_failed；
- 根据结果自动选择 Claim A/B/C。

如果 GPT 认为现在还需要 rescue sweep，则下一步应新增这两个脚本。但如果时间紧，优先级仍应是：

```text
1. public wrapper 跑完并拉回；
2. synthetic FT/KN 至少跑完；
3. 重新生成 paper-ready tables/figures；
4. 再决定是否做有限 CAPE rescue sweep。
```

## 7. 当前建议运行顺序

### 7.1 两个 public 实例

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

### 7.2 synthetic privacy 实例

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

### 7.3 本地生成论文表图

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
