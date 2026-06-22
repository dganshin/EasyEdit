#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f /root/miniconda3/etc/profile.d/conda.sh ]]; then
  source /root/miniconda3/etc/profile.d/conda.sh
fi
if command -v conda >/dev/null 2>&1; then
  conda activate easyedit >/dev/null 2>&1 || true
fi
if [[ -x /root/start_mihomo.sh ]]; then
  bash /root/start_mihomo.sh >/dev/null 2>&1 || true
fi

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf_cache/hf}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/root/autodl-tmp/hf_cache/transformers}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-/root/autodl-tmp/hf_cache/datasets}"
export NLTK_DATA="${NLTK_DATA:-/root/autodl-tmp/nltk_data}"
export http_proxy="${http_proxy:-http://127.0.0.1:7890}"
export https_proxy="${https_proxy:-http://127.0.0.1:7890}"
export HTTP_PROXY="${HTTP_PROXY:-$http_proxy}"
export HTTPS_PROXY="${HTTPS_PROXY:-$https_proxy}"

RUN_PUBLIC="${RUN_PUBLIC:-1}"
RUN_PROMPT="${RUN_PROMPT:-1}"
RUN_LORA_SANITIZATION="${RUN_LORA_SANITIZATION:-0}"
RUN_CAPE_ANCHOR="${RUN_CAPE_ANCHOR:-1}"
DOWNLOAD_GPTJ="${DOWNLOAD_GPTJ:-1}"
DOWNLOAD_LLAMA_BACKUP="${DOWNLOAD_LLAMA_BACKUP:-0}"
HF_ENDPOINT_VALUE="${HF_ENDPOINT_VALUE:-https://hf-mirror.com}"
DEVICE="${DEVICE:-0}"
MAX_CASES="${MAX_CASES:-300}"
SMOKE_ONLY="${SMOKE_ONLY:-0}"
METHODS_GPTJ="${METHODS_GPTJ:-ROME,FT,IKE,KN}"
METHODS_QWEN="${METHODS_QWEN:-ROME,FT,KN}"
STREAM_LOGS="${STREAM_LOGS:-1}"

ART_ROOT="${ART_ROOT:-artifacts/public_benchmarks_20260622}"
LOG_DIR="${ART_ROOT}/pipeline_logs"
STATUS_FILE="${ART_ROOT}/PUBLIC_PIPELINE_STATUS.txt"
DONE_FILE="${ART_ROOT}/PUBLIC_PIPELINE_DONE"
mkdir -p "$LOG_DIR"
rm -f "$DONE_FILE"

write_status() {
  local state="$1"
  local step="$2"
  {
    echo "state=${state}"
    echo "step=${step}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "art_root=${ART_ROOT}"
  } > "$STATUS_FILE"
}

run_step() {
  local name="$1"
  shift
  write_status "running" "$name"
  echo "[STEP] $name"
  if [[ "$STREAM_LOGS" == "1" ]]; then
    if "$@" 2>&1 | tee "${LOG_DIR}/${name}.log"; then
      echo "[OK] $name"
    else
      echo "[FAIL] $name"
      tail -n 80 "${LOG_DIR}/${name}.log" || true
      return 1
    fi
  else
    if "$@" > "${LOG_DIR}/${name}.log" 2>&1; then
      echo "[OK] $name"
    else
      echo "[FAIL] $name"
      tail -n 80 "${LOG_DIR}/${name}.log" || true
      return 1
    fi
  fi
}

run_optional() {
  local name="$1"
  shift
  if ! run_step "$name" "$@"; then
    echo "[WARN] continuing after failed step: $name"
  fi
}

write_status "starting" "bootstrap"

run_step py_compile python3 -m py_compile \
  scripts/check_public_model_availability.py \
  scripts/run_public_editing_baselines.py \
  scripts/evaluate_public_editing_baselines.py \
  scripts/run_v2_prompt_refusal_baseline.py \
  scripts/train_v2_lora_sanitization_baseline.py \
  scripts/build_cape_anchor_requests.py \
  scripts/merge_new_baseline_results.py

if [[ "$DOWNLOAD_GPTJ" == "1" ]]; then
  run_optional check_download_gptj \
    python3 scripts/check_public_model_availability.py \
      --download_gptj \
      --hf_endpoint "$HF_ENDPOINT_VALUE"
else
  run_step check_models python3 scripts/check_public_model_availability.py --hf_endpoint "$HF_ENDPOINT_VALUE"
fi

if [[ "$DOWNLOAD_LLAMA_BACKUP" == "1" ]]; then
  run_optional check_download_llama_backup \
    python3 scripts/check_public_model_availability.py \
      --download_llama_backup \
      --hf_endpoint "$HF_ENDPOINT_VALUE"
fi

GPTJ_MODEL="/root/autodl-tmp/models/gpt-j-6B"
QWEN_MODEL="/root/autodl-tmp/models/Qwen2.5-7B"
if [[ "$SMOKE_ONLY" == "1" ]]; then
  CASES=5
  SMOKE_FLAG=(--smoke_only)
else
  CASES="$MAX_CASES"
  SMOKE_FLAG=()
fi

if [[ "$RUN_PROMPT" == "1" ]]; then
  run_optional prompt_refusal_baseline \
    python3 scripts/run_v2_prompt_refusal_baseline.py \
      --dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json \
      --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
      --output_dir /root/autodl-tmp/outputs/easyedit/v2_prompt_refusal \
      --artifact_dir artifacts/run_20260622_v2_prompt_refusal \
      --device "$DEVICE" \
      --batch_size 16
fi

if [[ "$RUN_PUBLIC" == "1" ]]; then
  if [[ -d "$GPTJ_MODEL" ]]; then
    run_optional counterfact_gptj \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "${ART_ROOT}/counterfact_500.json" \
        --dataset_name counterfact \
        --model_path "$GPTJ_MODEL" \
        --model_name gpt-j-6B \
        --methods "$METHODS_GPTJ" \
        --max_cases "$CASES" \
        --output_dir "${ART_ROOT}/counterfact_gptj" \
        --device "$DEVICE" \
        "${SMOKE_FLAG[@]}"
    run_optional zsre_gptj \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "${ART_ROOT}/zsre_500.json" \
        --dataset_name zsre \
        --model_path "$GPTJ_MODEL" \
        --model_name gpt-j-6B \
        --methods "$METHODS_GPTJ" \
        --max_cases "$CASES" \
        --output_dir "${ART_ROOT}/zsre_gptj" \
        --device "$DEVICE" \
        "${SMOKE_FLAG[@]}"
  else
    echo "[WARN] GPT-J path missing; skip GPT-J public baseline: $GPTJ_MODEL"
  fi

  if [[ -d "$QWEN_MODEL" ]]; then
    run_optional counterfact_qwen \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "${ART_ROOT}/counterfact_500.json" \
        --dataset_name counterfact \
        --model_path "$QWEN_MODEL" \
        --model_name qwen2.5-7b \
        --methods "$METHODS_QWEN" \
        --max_cases "$CASES" \
        --output_dir "${ART_ROOT}/counterfact_qwen" \
        --device "$DEVICE" \
        "${SMOKE_FLAG[@]}"
    run_optional zsre_qwen \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "${ART_ROOT}/zsre_500.json" \
        --dataset_name zsre \
        --model_path "$QWEN_MODEL" \
        --model_name qwen2.5-7b \
        --methods "$METHODS_QWEN" \
        --max_cases "$CASES" \
        --output_dir "${ART_ROOT}/zsre_qwen" \
        --device "$DEVICE" \
        "${SMOKE_FLAG[@]}"
  else
    echo "[WARN] Qwen path missing; skip Qwen public baseline: $QWEN_MODEL"
  fi
fi

if [[ "$RUN_LORA_SANITIZATION" == "1" ]]; then
  run_optional lora_sanitization \
    python3 scripts/train_v2_lora_sanitization_baseline.py \
      --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged \
      --output_dir /root/autodl-tmp/outputs/easyedit/v2_lora_sanitization \
      --artifact_dir artifacts/run_20260622_v2_lora_sanitization \
      --device "$DEVICE" \
      --rank 8 \
      --batch_size 4 \
      --num_steps 200
fi

if [[ "$RUN_CAPE_ANCHOR" == "1" ]]; then
  run_optional cape_anchor_requests \
    python3 scripts/build_cape_anchor_requests.py \
      --dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json \
      --private_eval artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json \
      --output_dir artifacts/run_20260622_v2_cape_anchor
fi

run_optional aggregate_public \
  python3 scripts/evaluate_public_editing_baselines.py \
    --root_dir "$ART_ROOT" \
    --output_dir "$ART_ROOT"

run_optional aggregate_all \
  python3 scripts/merge_new_baseline_results.py \
    --public_root "$ART_ROOT" \
    --output_dir artifacts/final_comparison_20260622

write_status "done" "complete"
touch "$DONE_FILE"
echo "===== DONE ====="
echo "status_file: $STATUS_FILE"
echo "done_file: $DONE_FILE"
