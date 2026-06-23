# 2026-06-23 实验结果拉回与分析记录

Last updated: 2026-06-23
Related commit: 8e4aabd
Current completed artifacts: GPT-J public ROME/FT 200-case results; Qwen public partial 200-case results; existing synthetic ROME/MEMIT/PACE/CAPE rows
Current running artifacts: Qwen urgent synthetic/CAPE-Anchor results may still be incomplete locally
Pending server artifacts: synthetic FT/KN final eval; CAPE-Anchor B20-K0/K1/K2; Qwen/GPT-J public PACE-Edit/CAPE-Edit wrapper rows
Next action: do not rerun completed public baselines; only pull missing Qwen urgent artifacts and optionally run wrapper-only scripts on existing ROME per-case files
Risk / fallback: current evidence can support trade-off analysis, but cannot yet claim CAPE-Anchor or GPT-J wrapper effectiveness

## 1. 本次已经拉回并确认的结果

### 1.1 GPT-J second-model sanity patch

本地已确认 GPT-J 在 200-case public setting 上完成 4 个 baseline 行：

| 模型 | 数据集 | 方法 | cases | Reliability | Generalization | Locality | 用时 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| GPT-J-6B | CounterFact | ROME | 200 | 0.9950 | 0.8200 | missing | 1311.41s |
| GPT-J-6B | CounterFact | FT | 200 | 1.0000 | 0.7250 | missing | 99.02s |
| GPT-J-6B | zsRE | ROME | 200 | 0.9975 | 0.9451 | 0.9063 | 3359.20s |
| GPT-J-6B | zsRE | FT | 200 | 0.7930 | 0.8084 | 0.2015 | 2167.96s |

证据文件：

- `artifacts/gptj_fast_patch_20260623/GPTJ_EXISTING_RESULT_AUDIT.md`
- `artifacts/public_benchmarks_20260623_200/gptj_counterfact/ROME/summary.json`
- `artifacts/public_benchmarks_20260623_200/gptj_counterfact/FT/summary.json`
- `artifacts/public_benchmarks_20260623_200/gptj_zsre/ROME/summary.json`
- `artifacts/public_benchmarks_20260623_200/gptj_zsre/FT/summary.json`

解释口径：

- 这 4 行可以作为 second-model sanity patch，说明 public editing baseline 不只在 Qwen 上运行。
- 这还不能证明本文方法在 GPT-J 上有效，因为 GPT-J 的 `ROME+PACE-Edit` / `ROME+CAPE-Edit` wrapper 仍未完成。
- GPT-J 的 KN/IKE 不继续补：KN coarse-neuron search 过慢，IKE 不是当前主线；MEMIT 不纳入 GPT-J 目标矩阵，避免重新打开 MOM2 stats 成本。

### 1.2 Qwen public transfer partial matrix

本地已确认 Qwen public 200-case 矩阵中有 5 个可用 baseline 行：

| 模型 | 数据集 | 方法 | cases | Reliability | Generalization | 状态 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Qwen2.5-7B | CounterFact | ROME | 200 | 0.9950 | 0.7550 | ok |
| Qwen2.5-7B | CounterFact | FT | 200 | 1.0000 | 1.0000 | ok |
| Qwen2.5-7B | CounterFact | KN | 200 | 0.0075 | 0.0075 | ok，但效果很弱 |
| Qwen2.5-7B | zsRE | ROME | 200 | 1.0000 | 0.9763 | ok |
| Qwen2.5-7B | zsRE | FT | 200 | 0.7384 | 0.7469 | ok |

失败或缺失：

- Qwen CounterFact IKE：缺少 `./hugging_cache/all-MiniLM-L6-v2`，记录为依赖失败，不继续硬修。
- Qwen zsRE KN：48GB 实例上 OOM，记录为资源约束失败。
- Qwen public wrapper：`ROME_PACE_EDIT` / `ROME_CAPE_EDIT` 尚未形成有效结果。其中 CounterFact `ROME_PACE_EDIT` 是无 GPU 环境误跑导致的 `CUDA is required`，不代表方法失败。

解释口径：

- Qwen public baseline 可以写成公开 factual editing 迁移验证的 baseline 部分。
- 公开数据集不能写成 PII 清洗证明，只能说明 closed-loop wrapper 是否能迁移到 residual rewrite/generalization failure 的再编辑控制。
- 如果要让 public transfer 真正服务本文方法贡献，后续只补 wrapper，不重跑 ROME/FT/KN。

## 2. Synthetic privacy 主线状态

当前本地账本中可进入正文主表的 synthetic privacy 已有 8 行：

| 方法 | Private Value Contains | Public Contains | Public Refusal | 结论 |
| --- | ---: | ---: | ---: | --- |
| Leakage model | 0.9387 | 0.9766 | missing | 说明 LoRA 注入后存在可控泄露，同时保留公开知识 |
| ROME direct | 0.5787 | 0.5591 | 0.2873 | 隐私压制有限，public retain 下降 |
| MEMIT direct | 0.8140 | 0.8472 | 0.0897 | public retain 较好，但隐私压制弱 |
| PACE target_only | 0.0000 | 0.0032 | 0.9675 | 隐私压制强，但 public collapse |
| PACE max1_per_case | 0.0003 | 0.0099 | 0.9611 | 仍然 public collapse |
| PACE max2/person | 0.0243 | 0.0984 | 0.8052 | 较保守但仍有明显 over-refusal |
| CAPE-v0 | 0.0023 | 0.0060 | 0.9877 | 过度拒答仍严重 |
| CAPE-v1 | 0.0443 | 0.1119 | 0.6901 | 相比 v0 有缓解，但不是全面 Pareto 改进 |

当前 synthetic 还缺本地可用结果：

- FT baseline final eval；
- KN baseline final eval；
- CAPE-Anchor B20-K0 / B20-K1 / B20-K2；
- updated `METHOD_CLAIM_DECISION.md`。

特别注意：

- `artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv` 当前本地为空文件，不能把 CAPE-Anchor 当作已经完成可分析结果。
- `METHOD_CLAIM_DECISION.md` 当前仍显示 Claim C，原因是缺少 CAPE-Anchor 可比较结果。它不是最终论文结论，只是当前 artifact 不完整时的保守判定。

## 3. 当前最重要的判断

1. **GPT-J 不是废结果。**  
   GPT-J ROME/FT 200-case baseline 已经完成，可以作为第二模型 sanity patch。但它现在还缺本文方法 wrapper，因此不能写成“本文方法在 GPT-J 上验证有效”。

2. **Qwen public baseline 有价值，但 public wrapper 仍缺。**  
   Qwen public 现在可写 baseline 对比，但若没有 `ROME+PACE-Edit` / `ROME+CAPE-Edit`，公开实验仍容易被质疑为只复现别人方法。因此后续应只补 wrapper，不重跑已完成 baseline。

3. **Synthetic privacy 仍是主实验。**  
   论文主张必须由 synthetic privacy 的 ROME/MEMIT/FT/KN/PACE/CAPE/CAPE-Anchor 共同支撑。当前 CAPE-Anchor 结果尚未完整带回，本地不能提前下 Claim A/B。

4. **失败项要进入 failure matrix，不要继续硬修。**  
   IKE 缺 embedding 依赖、Qwen zsRE KN OOM、GPT-J KN 过慢，都是合理的资源/依赖边界。论文里可作为实验约束说明，不应继续花 GPU 抢救。

## 4. 下一步建议

### 4.1 服务器如果还有 Qwen urgent 结果

优先把以下小文件拉回并重新运行账本：

```text
artifacts/run_20260623_v2_ft_baseline/
artifacts/run_20260623_v2_kn_baseline/
artifacts/run_20260623_cape_anchor_rescue/
artifacts/final_comparison_20260623_urgent/
```

拉回后运行：

```bash
python scripts/extract_all_available_metrics_now.py
python scripts/decide_method_claim_level.py
```

### 4.2 如果还有 GPU 时间补 public wrapper

只跑 wrapper-only，不重跑 baseline：

```bash
ART_ROOT=artifacts/public_benchmarks_20260623_200 \
PUBLIC_DATASET_SIZE=200 \
MODEL_SHORT=qwen \
MODEL_NAME=qwen2.5-7b \
MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B \
BASE_METHOD=ROME \
DATASETS=counterfact,zsre \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_public_closed_loop_wrappers.sh
```

GPT-J 同理，但只在已有 GPU 且不影响 synthetic 主线时运行：

```bash
ART_ROOT=artifacts/public_benchmarks_20260623_200 \
PUBLIC_DATASET_SIZE=200 \
MODEL_SHORT=gptj \
MODEL_NAME=gpt-j-6B \
MODEL_PATH=/root/autodl-tmp/models/gpt-j-6B \
BASE_METHOD=ROME \
DATASETS=counterfact,zsre \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_public_closed_loop_wrappers.sh
```

## 5. 论文当前可写结论

当前可以稳妥写：

> 已有结果表明，标准模型编辑方法在隐私压制和知识保持之间呈现明显 trade-off。ROME 能降低部分泄露但 public retain 下降，MEMIT 的 public retain 较好但隐私压制不足，PACE/CAPE 能进一步压低 private leakage，但容易引入 over-refusal。公开数据集上的 Qwen/GPT-J 结果为外部 factual editing 设置提供了 baseline 与第二模型 sanity check，但本文方法的 public wrapper 迁移效果仍需补齐后再下结论。

当前不能写：

- CAPE-Anchor 已经优于所有 baseline；
- GPT-J 已经验证 PACE/CAPE 有效；
- public benchmark 证明了 PII 清洗成功；
- IKE/KN 缺失是方法本身无效。
