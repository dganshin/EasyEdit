# V2 MEMIT Direct-only Baseline Plan

## 1. Purpose

本轮准备 MEMIT direct-only baseline, 目标是判断 ROME/PACE 中观察到的 privacy-public trade-off 是否是 ROME 特有现象, 还是 synthetic privacy refusal editing 任务中更普遍的模型编辑张力。

本轮只做路径修复、脚本准备和 no-GPU preflight, 不启动 MEMIT GPU 实验。

## 2. Alignment with ROME direct-only

MEMIT direct-only 与现有 ROME direct-only 对齐如下：

| item | ROME direct-only | MEMIT direct-only |
| --- | --- | --- |
| base model | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | same |
| dataset | `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json` | same |
| edit requests | `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json` | same |
| edited subset | 20 people / 40 direct private cases | same |
| full private eval | full v2 private prompts | same |
| public retain eval | full v2 public prompts | same |
| target_new | `I cannot provide private information.` | same |

v2 口径统一为：

- archived benchmark: `100` people
- private facts: `200`
- public facts: `840`
- flat cases: `1040`
- LoRA injection: full 100-person dataset
- ROME/MEMIT direct-only edit subset: 20 people / 40 direct private cases
- full private/public eval: full v2 dataset

## 3. Paths

- model path: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- dataset path: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- request path: `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json`
- hparams path: `hparams/MEMIT/qwen2.5-7b.yaml`
- server output path: `/root/autodl-tmp/outputs/easyedit/v2_memit_direct`
- artifact path: `artifacts/run_20260617_v2_memit_direct/`
- pipeline script: `scripts/run_v2_memit_direct_pipeline.sh`
- preflight script: `scripts/preflight_v2_memit_direct.py`

## 4. Preflight checks

Local no-GPU preflight result on macOS:

| check | result |
| --- | --- |
| canonical dataset exists | pass |
| dataset scale is 100 people / 200 private / 840 public / 1040 flat cases | pass |
| ROME direct requests file exists | pass |
| direct requests count is 40 | pass |
| direct requests cover 20 people / 40 cases | pass |
| MEMIT hparams exists | pass |
| output dir is `/root/autodl-tmp/outputs/easyedit/v2_memit_direct` | pass |
| local artifact dir does not exist | pass |
| merged model path exists on this Mac | fail, expected for local Mac |

The local preflight was run with `--allow_missing_model` because `/root/autodl-tmp/...` is an AutoDL server path. Before GPU execution, run the preflight on AutoDL without `--allow_missing_model`; it must confirm the model path exists.

Preflight record:

- `artifacts/run_20260617_v2_audit/preflight_v2_memit_direct_local.json`

## 5. Exact command to run

Do not run this until approved.

```bash
cd /root/autodl-tmp/projects/EasyEdit

conda activate easyedit
bash /root/start_mihomo.sh

export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

python3 scripts/preflight_v2_memit_direct.py \
  --dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json \
  --requests artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
  --hparams hparams/MEMIT/qwen2.5-7b.yaml \
  --output_dir /root/autodl-tmp/outputs/easyedit/v2_memit_direct \
  --artifact_dir artifacts/run_20260617_v2_memit_direct

RUN_DATE=20260617 \
RUN_TAG=v2_memit_direct \
DEVICE=0 \
STREAM_LOGS=1 \
bash scripts/run_v2_memit_direct_pipeline.sh
```

## 6. Expected metrics

最终至少需要输出并汇总：

- private exact
- private regex
- sensitive pattern
- refusal
- public overall contains
- same_subject_public
- same_relation_other_subject
- general_knowledge

这些指标应与现有 ROME direct-only 和 PACE 汇总表保持同一口径, 方便判断 MEMIT 是否更强压制 private leakage, 是否更伤 public retain, 以及 general knowledge 是否保持。
