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

ART_ROOT="${ART_ROOT:-artifacts/public_benchmarks_20260622}"
LOG_DIR="${ART_ROOT}/pipeline_logs_gptj"
STATUS_FILE="${ART_ROOT}/GPTJ_PUBLIC_PIPELINE_STATUS.txt"
DONE_FILE="${ART_ROOT}/GPTJ_PUBLIC_PIPELINE_DONE"
GPTJ_MODEL="${GPTJ_MODEL:-/root/autodl-tmp/models/gpt-j-6B}"
HF_ENDPOINT_VALUE="${HF_ENDPOINT_VALUE:-https://hf-mirror.com}"
MAX_CASES="${MAX_CASES:-500}"
DEVICE="${DEVICE:-0}"
METHODS_GPTJ="${METHODS_GPTJ:-ROME,FT,KN,IKE}"
STREAM_LOGS="${STREAM_LOGS:-1}"
DOWNLOAD_LLAMA_BACKUP="${DOWNLOAD_LLAMA_BACKUP:-0}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
SHUTDOWN_DELAY_MINUTES="${SHUTDOWN_DELAY_MINUTES:-2}"

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
    echo "model=${GPTJ_MODEL}"
    echo "max_cases=${MAX_CASES}"
  } > "$STATUS_FILE"
}

on_exit() {
  local code=$?
  local state="failed"
  if [[ "$code" == "0" ]]; then
    state="done"
  fi
  {
    echo "state=${state}"
    echo "exit_code=${code}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "art_root=${ART_ROOT}"
    echo "model=${GPTJ_MODEL}"
    echo "max_cases=${MAX_CASES}"
  } > "$STATUS_FILE"
  if [[ "$SHUTDOWN_ON_EXIT" == "1" ]]; then
    echo "[SHUTDOWN] scheduling shutdown in ${SHUTDOWN_DELAY_MINUTES} minutes; cancel with: shutdown -c"
    shutdown -h "+${SHUTDOWN_DELAY_MINUTES}" "GPT-J public benchmark ${state}, exit=${code}" || true
  fi
}
trap on_exit EXIT

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
      tail -n 100 "${LOG_DIR}/${name}.log" || true
      return 1
    fi
  else
    if "$@" > "${LOG_DIR}/${name}.log" 2>&1; then
      echo "[OK] $name"
    else
      echo "[FAIL] $name"
      tail -n 100 "${LOG_DIR}/${name}.log" || true
      return 1
    fi
  fi
}

run_optional() {
  local name="$1"
  shift
  if ! run_step "$name" "$@"; then
    echo "[FAIL] stopping after failed step: $name"
    return 1
  fi
}

validate_transformers_model() {
  local model_dir="$1"
  [[ -f "${model_dir}/config.json" ]] || return 1
  python3 - "$model_dir" <<'PY'
import sys
from transformers import AutoConfig, AutoTokenizer

model_dir = sys.argv[1]
cfg = AutoConfig.from_pretrained(model_dir)
tok = AutoTokenizer.from_pretrained(model_dir)
print("model_type:", cfg.model_type)
print("vocab_size:", tok.vocab_size)
PY
}

write_status "starting" "bootstrap"

run_step py_compile python3 -m py_compile \
  scripts/check_public_model_availability.py \
  scripts/prepare_public_editing_subsets.py \
  scripts/run_public_editing_baselines.py \
  scripts/evaluate_public_editing_baselines.py \
  scripts/merge_new_baseline_results.py

if [[ ! -f "${ART_ROOT}/counterfact_500.json" || ! -f "${ART_ROOT}/zsre_500.json" ]]; then
  run_step prepare_public_subsets python3 scripts/prepare_public_editing_subsets.py \
    --output_dir "$ART_ROOT" \
    --counterfact_size 500 \
    --zsre_size 500 \
    --minimum_size 300
fi

if ! validate_transformers_model "$GPTJ_MODEL"; then
  run_step download_gptj python3 scripts/check_public_model_availability.py \
    --download_gptj \
    --gptj_target "$GPTJ_MODEL" \
    --hf_endpoint "$HF_ENDPOINT_VALUE"
fi

if ! validate_transformers_model "$GPTJ_MODEL"; then
  echo "[FAIL] GPT-J remains invalid after download attempt: $GPTJ_MODEL"
  echo "[FAIL] Stop before editing; check ${ART_ROOT}/model_availability_report.json"
  if [[ "$DOWNLOAD_LLAMA_BACKUP" == "1" ]]; then
    run_optional download_llama_backup python3 scripts/check_public_model_availability.py \
      --download_llama_backup \
      --hf_endpoint "$HF_ENDPOINT_VALUE"
  fi
  exit 1
fi

run_optional gptj_counterfact_500 \
  python3 scripts/run_public_editing_baselines.py \
    --dataset_path "${ART_ROOT}/counterfact_500.json" \
    --dataset_name counterfact \
    --model_path "$GPTJ_MODEL" \
    --model_name gpt-j-6B \
    --methods "$METHODS_GPTJ" \
    --max_cases "$MAX_CASES" \
    --output_dir "${ART_ROOT}/gptj_counterfact" \
    --device "$DEVICE" \
    --disable_generation_test \
    --resume_skip_completed

run_optional gptj_zsre_500 \
  python3 scripts/run_public_editing_baselines.py \
    --dataset_path "${ART_ROOT}/zsre_500.json" \
    --dataset_name zsre \
    --model_path "$GPTJ_MODEL" \
    --model_name gpt-j-6B \
    --methods "$METHODS_GPTJ" \
    --max_cases "$MAX_CASES" \
    --output_dir "${ART_ROOT}/gptj_zsre" \
    --device "$DEVICE" \
    --disable_generation_test \
    --resume_skip_completed

run_optional aggregate_public \
  python3 scripts/evaluate_public_editing_baselines.py \
    --root_dir "$ART_ROOT" \
    --output_dir "$ART_ROOT"

cp "${ART_ROOT}/public_editing_comparison.csv" "${ART_ROOT}/public_editing_comparison_gptj.csv" || true
cp "${ART_ROOT}/PUBLIC_EDITING_BASELINE_REPORT.md" "${ART_ROOT}/PUBLIC_EDITING_BASELINE_REPORT_GPTJ.md" || true

run_optional aggregate_all \
  python3 scripts/merge_new_baseline_results.py \
    --public_root "$ART_ROOT" \
    --output_dir artifacts/final_comparison_20260622

write_status "done" "complete"
touch "$DONE_FILE"
echo "===== GPTJ PUBLIC DONE ====="
echo "status_file: $STATUS_FILE"
echo "done_file: $DONE_FILE"
