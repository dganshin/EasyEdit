# Public Baseline Server Commands

这些命令用于 AutoDL Linux 服务器。优先使用一键 pipeline；下面的分步命令仅用于单步排错。

## 0. Recommended One-Shot Pipeline

先 smoke：

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull --ff-only
SMOKE_ONLY=1 \
MAX_CASES=5 \
RUN_LORA_SANITIZATION=0 \
DOWNLOAD_GPTJ=1 \
HF_ENDPOINT_VALUE=https://hf-mirror.com \
STREAM_LOGS=1 \
bash scripts/run_public_baseline_pipeline.sh
```

smoke 过后跑 300 条：

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull --ff-only
SMOKE_ONLY=0 \
MAX_CASES=300 \
RUN_LORA_SANITIZATION=0 \
DOWNLOAD_GPTJ=0 \
HF_ENDPOINT_VALUE=https://hf-mirror.com \
STREAM_LOGS=1 \
bash scripts/run_public_baseline_pipeline.sh
```

如果后续要补 LLaMA-2 备用源探测，使用：

```bash
DOWNLOAD_LLAMA_BACKUP=1 \
DOWNLOAD_GPTJ=0 \
RUN_PUBLIC=0 \
RUN_PROMPT=0 \
RUN_CAPE_ANCHOR=0 \
bash scripts/run_public_baseline_pipeline.sh
```

## 1. Sync

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull --ff-only
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
```

## 2. No-GPU GPT-J Check / Download

```bash
python3 scripts/check_public_model_availability.py --download_gptj --hf_endpoint https://hf-mirror.com
```

如果 GPT-J 下载超过 2 小时还没完成，先跳到 Qwen public baseline。

## 3. Synthetic Prompt Refusal Baseline

```bash
python3 scripts/run_v2_prompt_refusal_baseline.py \
  --dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
  --output_dir /root/autodl-tmp/outputs/easyedit/v2_prompt_refusal \
  --artifact_dir artifacts/run_20260622_v2_prompt_refusal \
  --device 0 \
  --batch_size 16
```

## 4. GPT-J Smoke Tests

```bash
python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/counterfact_500.json \
  --dataset_name counterfact \
  --model_path /root/autodl-tmp/models/gpt-j-6B \
  --model_name gpt-j-6B \
  --methods ROME,FT,IKE,KN \
  --max_cases 5 \
  --output_dir artifacts/public_benchmarks_20260622/counterfact_gptj \
  --device 0 \
  --smoke_only

python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/zsre_500.json \
  --dataset_name zsre \
  --model_path /root/autodl-tmp/models/gpt-j-6B \
  --model_name gpt-j-6B \
  --methods ROME,FT,IKE,KN \
  --max_cases 5 \
  --output_dir artifacts/public_benchmarks_20260622/zsre_gptj \
  --device 0 \
  --smoke_only
```

## 5. GPT-J 300/500 Runs

先跑 300；如果时间和稳定性允许，再改成 500。

```bash
python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/counterfact_500.json \
  --dataset_name counterfact \
  --model_path /root/autodl-tmp/models/gpt-j-6B \
  --model_name gpt-j-6B \
  --methods ROME,FT,IKE,KN \
  --max_cases 300 \
  --output_dir artifacts/public_benchmarks_20260622/counterfact_gptj \
  --device 0

python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/zsre_500.json \
  --dataset_name zsre \
  --model_path /root/autodl-tmp/models/gpt-j-6B \
  --model_name gpt-j-6B \
  --methods ROME,FT,IKE,KN \
  --max_cases 300 \
  --output_dir artifacts/public_benchmarks_20260622/zsre_gptj \
  --device 0
```

## 6. Qwen Fallback / Additional Public Runs

```bash
python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/counterfact_500.json \
  --dataset_name counterfact \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B \
  --model_name qwen2.5-7b \
  --methods ROME,FT,KN \
  --max_cases 300 \
  --output_dir artifacts/public_benchmarks_20260622/counterfact_qwen \
  --device 0

python3 scripts/run_public_editing_baselines.py \
  --dataset_path artifacts/public_benchmarks_20260622/zsre_500.json \
  --dataset_name zsre \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B \
  --model_name qwen2.5-7b \
  --methods ROME,FT,KN \
  --max_cases 300 \
  --output_dir artifacts/public_benchmarks_20260622/zsre_qwen \
  --device 0
```

## 7. LoRA/SFT Sanitization

```bash
python3 scripts/train_v2_lora_sanitization_baseline.py \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
  --output_dir /root/autodl-tmp/outputs/easyedit/v2_lora_sanitization \
  --artifact_dir artifacts/run_20260622_v2_lora_sanitization \
  --device 0 \
  --rank 8 \
  --batch_size 4 \
  --num_steps 200
```

## 8. Aggregate

```bash
python3 scripts/evaluate_public_editing_baselines.py \
  --root_dir artifacts/public_benchmarks_20260622 \
  --output_dir artifacts/public_benchmarks_20260622

python3 scripts/merge_new_baseline_results.py \
  --public_root artifacts/public_benchmarks_20260622 \
  --output_dir artifacts/final_comparison_20260622
```
