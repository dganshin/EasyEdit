# Prompt Refusal Baseline Report

## Status

- dry_run: `True`
- dataset: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- model_path: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- run_name: `v2_prompt_refusal`

## Protocol

- 不修改模型参数。
- 对 private/public prompt 统一添加隐私拒答 guard prefix。
- 生成后复用现有 `evaluate_privacy_leakage.py` 与 `evaluate_public_retain.py`。
- 该 baseline 用作非参数编辑对照，不能解释为模型内部隐私知识已被清除。

## Dataset Check

- private generation jobs: `3000`
- public generation jobs: `2520`

## Dry-run Result

本地 dry-run 只验证数据、路径和输出协议；正式 generation 需要在 AutoDL GPU 服务器上运行。

Recommended server command:

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
conda activate easyedit
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python3 scripts/run_v2_prompt_refusal_baseline.py \
  --dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
  --output_dir /root/autodl-tmp/outputs/easyedit/v2_prompt_refusal \
  --artifact_dir artifacts/run_20260622_v2_prompt_refusal \
  --device 0 \
  --batch_size 16
```
