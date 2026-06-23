# 当前最新实验状态与防跑偏说明（2026-06-23）

本文档是当前 EasyEdit 项目的最高优先级交接文件。新 Codex 会话、新 AutoDL 实例、换设备之后，先读本文，再读 `AGENTS.md` 和具体脚本。旧文档中 2026-06-15 附近的“只打通单条编辑”“不要扩 MEMIT/公开数据集”等描述已经过期。

## 1. 当前论文主线

当前项目不是单纯复现 EasyEdit，也不是只做隐私拒答 demo。当前论文主线是：

> 构造可控 synthetic privacy benchmark，比较标准模型编辑方法与闭环请求选择方法，在 privacy suppression、public retain、over-refusal / locality damage 之间分析 trade-off，并验证 PACE/CAPE 这类 closed-loop wrapper 是否能比 naive edit 更可控。

必须保持两个核心原则：

- 要和其他方法比较：ROME、MEMIT、FT、KN、IKE 等 baseline 不能只跑公开数据集，也应尽量在 synthetic privacy 上补充。
- 我们的方法也要进入公开数据集：PACE/CAPE 不能只在自造数据集里自娱自乐，应抽象成 public editing 上的 PACE-Edit / CAPE-Edit wrapper。

## 2. 当前实验矩阵

### 2.1 Synthetic privacy v2

用途：论文主任务，评估隐私清洗。

已知关键资产：

```text
artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json
/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged
artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json
hparams/MEMIT/qwen2.5-7b.yaml
```

已完成或已有结果的主线：

- LoRA MLP-only privacy injection merged model
- ROME direct-only
- MEMIT direct-only
- PACE variants
- CAPE-v0 / CAPE-v1

仍应补的 baseline：

- FT
- KN
- IKE

入口脚本：

```text
scripts/run_synthetic_privacy_extra_editors.sh
```

注意：不要修改 EasyEdit / ROME / MEMIT 底层；FT/KN/IKE 通过通用入口 `scripts/run_privacy_refusal_edit.py` 跑。

### 2.2 Public editing benchmark

用途：不是证明 PII 清洗，而是验证方法能否迁移到公开 factual editing 的 residual failure / locality damage 闭环控制。

当前只保留两个公开数据集，先不扩 WikiBio、Wikidatarecent、ConvSent：

- CounterFact
- zsRE

当前统一规模：**200 cases**。

理由：公开数据集一个方法 500 条约 1 小时；两个模型、多个方法和 wrapper 会变成 6-10 小时。200 条与 synthetic privacy 的 200-case 规模更一致，也更适合作为课程论文可复现实验矩阵。

公共 baseline 方法：

- ROME
- FT
- KN
- IKE

公共 wrapper 方法：

- ROME + PACE-Edit
- ROME + CAPE-Edit

wrapper 解释：

- PACE-Edit：把 privacy 场景中的 residual leakage re-edit 抽象为 public editing 中的 residual rewrite/rephrase failure closed-loop edit。
- CAPE-Edit：在 PACE-Edit 基础上加入 locality risk、subject/relation budget 和 split 选择，避免把 same-set repair 伪装成严格泛化。

## 3. 当前重要脚本

```text
scripts/run_public_qwen_full.sh
scripts/run_public_gptj_full.sh
scripts/build_public_pace_cape_requests.py
scripts/run_public_closed_loop_wrappers.sh
scripts/run_public_editing_baselines.py
scripts/merge_public_results_from_instances.py
scripts/run_synthetic_privacy_extra_editors.sh
```

当前 `run_public_qwen_full.sh`、`run_public_gptj_full.sh` 默认 `MAX_CASES=200`，且默认 `RUN_PUBLIC_WRAPPERS=1`。也就是说，public full 脚本会先跑 ROME/FT/KN/IKE baseline，再自动补 ROME+PACE-Edit / ROME+CAPE-Edit wrapper。

当前 `run_public_closed_loop_wrappers.sh` 默认：

```text
PUBLIC_DATASET_SIZE=200
MAX_CASES=200
SELECTION_SPLIT_RATIO=0.6
HELDOUT_EVAL_RATIO=0.4
SPLIT_SEED=20260622
```

`build_public_pace_cape_requests.py` 支持 `--dataset_limit`，会先截取 200 条，再进行 split 和 PACE/CAPE selection。

## 4. AutoDL 固定环境

仓库：

```text
/root/autodl-tmp/projects/EasyEdit
```

模型：

```text
/root/autodl-tmp/models/Qwen2.5-7B
/root/autodl-tmp/models/gpt-j-6B
/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged
```

缓存：

```text
/root/autodl-tmp/hf_cache
```

输出：

```text
/root/autodl-tmp/outputs/easyedit
```

代理：

```bash
bash /root/start_mihomo.sh || true
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

Python 环境：

```bash
conda activate easyedit
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
```

自动关机规则：

- 默认命令一律使用 `SHUTDOWN_ON_EXIT=0`。
- 白天调试或交互运行时不要开启自动关机。
- 即使误设 `SHUTDOWN_ON_EXIT=1`，脚本也只有在同时设置 `ALLOW_AUTODL_SHUTDOWN=1` 时才会真正执行 `shutdown -h`。
- 凌晨无人值守省钱时，才允许显式加上 `ALLOW_AUTODL_SHUTDOWN=1`。

## 5. 当前推荐运行方式

### 5.0 两个实例分工，禁止混跑

当前至少可能同时存在两个 AutoDL 实例。必须先确认自己在哪个实例，再执行对应命令。

| 实例 | 模型路径 | 只跑这些脚本 | ART_ROOT 建议 |
| --- | --- | --- | --- |
| Qwen 实例 | `/root/autodl-tmp/models/Qwen2.5-7B` | `scripts/run_public_qwen_full.sh`、Qwen 的 `scripts/run_public_closed_loop_wrappers.sh` | `artifacts/public_benchmarks_20260623_200` |
| GPT-J 实例 | `/root/autodl-tmp/models/gpt-j-6B` | `scripts/run_public_gptj_full.sh`、GPT-J 的 `scripts/run_public_closed_loop_wrappers.sh` | `artifacts/public_benchmarks_20260623_200` |

禁止事项：

- 不要在 GPT-J 实例执行 `run_public_qwen_full.sh`。
- 不要在 Qwen 实例执行 `run_public_gptj_full.sh`。
- 不要把 `MODEL_PATH` 和 `MODEL_NAME` 混用。
- 白天不要设置 `ALLOW_AUTODL_SHUTDOWN=1`。
- 本项目不要再使用 shell 关机取消命令；如误设置关机，到 AutoDL 网页控制台处理。

每个实例拉代码时只做：

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
git -c http.version=HTTP/1.1 pull --ff-only
conda activate easyedit
```

### 5.1 GPT-J public 200 baseline

GPT-J 模型已在新实例验证过：

```text
model_type: gptj
vocab_size: 50257
```

如果新实例没有仓库，先 clone：

```bash
mkdir -p /root/autodl-tmp/projects
cd /root/autodl-tmp/projects
git clone https://github.com/dganshin/EasyEdit.git EasyEdit
```

运行：

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
git -c http.version=HTTP/1.1 pull --ff-only
conda activate easyedit
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data

ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
METHODS_GPTJ=ROME,FT,KN,IKE \
SHUTDOWN_ON_EXIT=0 \
SHUTDOWN_DELAY_MINUTES=2 \
STREAM_LOGS=1 \
bash scripts/run_public_gptj_full.sh
```

### 5.2 GPT-J public PACE/CAPE wrapper

通常不用手动运行；`scripts/run_public_gptj_full.sh` 默认会在 baseline 后自动运行。只有 baseline 已经用旧脚本跑完、需要单独补 wrapper 时，才运行：

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

ART_ROOT=artifacts/public_benchmarks_20260623_200 \
PUBLIC_DATASET_SIZE=200 \
MODEL_SHORT=gptj \
MODEL_NAME=gpt-j-6B \
MODEL_PATH=/root/autodl-tmp/models/gpt-j-6B \
BASE_METHOD=ROME \
DATASETS=counterfact,zsre \
SHUTDOWN_ON_EXIT=0 \
SHUTDOWN_DELAY_MINUTES=2 \
STREAM_LOGS=1 \
bash scripts/run_public_closed_loop_wrappers.sh
```

### 5.3 Qwen public 200 baseline

Qwen 500 旧跑法可能已经产生部分结果，保留为附加材料即可。正式对齐矩阵建议另用 `artifacts/public_benchmarks_20260623_200` 跑 200 条：

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
git -c http.version=HTTP/1.1 pull --ff-only
conda activate easyedit
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data

ART_ROOT=artifacts/public_benchmarks_20260623_200 \
MAX_CASES=200 \
METHODS_QWEN=ROME,FT,KN,IKE \
SHUTDOWN_ON_EXIT=0 \
SHUTDOWN_DELAY_MINUTES=2 \
STREAM_LOGS=1 \
bash scripts/run_public_qwen_full.sh
```

### 5.4 Qwen public PACE/CAPE wrapper

通常不用手动运行；`scripts/run_public_qwen_full.sh` 默认会在 baseline 后自动运行。只有 baseline 已经用旧脚本跑完、需要单独补 wrapper 时，才运行：

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

ART_ROOT=artifacts/public_benchmarks_20260623_200 \
PUBLIC_DATASET_SIZE=200 \
MODEL_SHORT=qwen \
MODEL_NAME=qwen2.5-7b \
MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B \
BASE_METHOD=ROME \
DATASETS=counterfact,zsre \
SHUTDOWN_ON_EXIT=0 \
SHUTDOWN_DELAY_MINUTES=2 \
STREAM_LOGS=1 \
bash scripts/run_public_closed_loop_wrappers.sh
```

### 5.5 Synthetic privacy extra editors

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

METHODS_SYNTHETIC=FT,KN,IKE \
SHUTDOWN_ON_EXIT=0 \
SHUTDOWN_DELAY_MINUTES=2 \
STREAM_LOGS=1 \
bash scripts/run_synthetic_privacy_extra_editors.sh
```

## 6. 论文表格口径

不要把 synthetic privacy 和 public editing 混在一张主表里。

建议表格：

1. Synthetic privacy main table：ROME、MEMIT、PACE、CAPE、FT、KN、IKE。
2. Public baseline table：CounterFact/zsRE × Qwen/GPT-J × ROME/FT/KN/IKE。
3. Public wrapper table：ROME vs ROME+PACE-Edit vs ROME+CAPE-Edit。
4. Optional cost/runtime table：200-case 运行时间、失败类型、OOM 情况。

公开数据集结果只能说明 closed-loop wrapper 对公开 factual editing 的 residual failure / locality trade-off 有迁移价值，不能直接写成真实 PII 清洗效果。

## 7. 不要再做的事

- 不要继续把公开数据集只当复现别人论文。
- 不要只在 synthetic privacy 上跑我们的方法，然后公开数据集只跑别人的方法。
- 不要为了“显得成功”把负结果写成正结果；应写成 trade-off、机制发现和改进方向。
- 不要修改 EasyEdit / ROME / MEMIT 底层算法。
- 不要把模型权重、MOM2 stats、Wikipedia cache 放进 Git。
- 不要再用旧文档里的 2026-06-15 PACE 结论当最新状态。

## 8. 下一位 agent 的最短启动顺序

1. 读本文。
2. 查 `git log --oneline -5`。
3. 查 `git status --short`，不要误提交本地论文草稿和大文件。
4. 如果用户要跑服务器，给完整命令，不要只给 Markdown 计划。
5. 如果用户要论文，先读取最新 artifact JSON/CSV，再写中文研究型叙事，不要只写审计报告。

