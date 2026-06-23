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
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

ART_ROOT="${ART_ROOT:-artifacts/public_benchmarks_20260622}"
LOG_DIR="${ART_ROOT}/pipeline_logs"
STATUS_FILE="${ART_ROOT}/QWEN_PUBLIC_PIPELINE_STATUS.txt"
DONE_FILE="${ART_ROOT}/QWEN_PUBLIC_PIPELINE_DONE"
QWEN_MODEL="${QWEN_MODEL:-/root/autodl-tmp/models/Qwen2.5-7B}"
MAX_CASES="${MAX_CASES:-200}"
DEVICE="${DEVICE:-0}"
METHODS_QWEN="${METHODS_QWEN:-ROME,FT,KN,IKE}"
STREAM_LOGS="${STREAM_LOGS:-1}"
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
    echo "model=${QWEN_MODEL}"
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
    echo "model=${QWEN_MODEL}"
    echo "max_cases=${MAX_CASES}"
  } > "$STATUS_FILE"
  if [[ "$SHUTDOWN_ON_EXIT" == "1" ]]; then
    echo "[SHUTDOWN] scheduling shutdown in ${SHUTDOWN_DELAY_MINUTES} minutes; cancel with: shutdown -c"
    shutdown -h "+${SHUTDOWN_DELAY_MINUTES}" "Qwen public benchmark ${state}, exit=${code}" || true
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

model_dir_is_valid() {
  local model_dir="$1"
  [[ -d "$model_dir" && -f "$model_dir/config.json" ]] || return 1
  python3 - "$model_dir/config.json" <<'PY'
import json
import sys
from pathlib import Path

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if payload.get("model_type") else 1)
PY
}

write_status "starting" "bootstrap"

run_step py_compile python3 -m py_compile \
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

if ! model_dir_is_valid "$QWEN_MODEL"; then
  echo "[FAIL] Qwen model is missing or invalid: $QWEN_MODEL"
  echo "[FAIL] expected config.json with model_type"
  exit 1
fi

run_optional qwen_counterfact_500 \
  python3 scripts/run_public_editing_baselines.py \
    --dataset_path "${ART_ROOT}/counterfact_500.json" \
    --dataset_name counterfact \
    --model_path "$QWEN_MODEL" \
    --model_name qwen2.5-7b \
    --methods "$METHODS_QWEN" \
    --max_cases "$MAX_CASES" \
    --output_dir "${ART_ROOT}/qwen_counterfact" \
    --device "$DEVICE" \
    --disable_generation_test \
    --resume_skip_completed \
    --isolate_methods

run_optional qwen_zsre_500 \
  python3 scripts/run_public_editing_baselines.py \
    --dataset_path "${ART_ROOT}/zsre_500.json" \
    --dataset_name zsre \
    --model_path "$QWEN_MODEL" \
    --model_name qwen2.5-7b \
    --methods "$METHODS_QWEN" \
    --max_cases "$MAX_CASES" \
    --output_dir "${ART_ROOT}/qwen_zsre" \
    --device "$DEVICE" \
    --disable_generation_test \
    --resume_skip_completed \
    --isolate_methods

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
echo "===== QWEN PUBLIC DONE ====="
echo "status_file: $STATUS_FILE"
echo "done_file: $DONE_FILE"
