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
MODEL_SHORT="${MODEL_SHORT:-qwen}"
MODEL_NAME="${MODEL_NAME:-qwen2.5-7b}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B}"
BASE_METHOD="${BASE_METHOD:-ROME}"
DATASETS="${DATASETS:-counterfact,zsre}"
MAX_CASES="${MAX_CASES:-500}"
CLOSED_LOOP_MAX_CASES="${CLOSED_LOOP_MAX_CASES:-1000}"
DEVICE="${DEVICE:-0}"
SELECTION_SPLIT_RATIO="${SELECTION_SPLIT_RATIO:-0.6}"
HELDOUT_EVAL_RATIO="${HELDOUT_EVAL_RATIO:-0.4}"
SPLIT_SEED="${SPLIT_SEED:-20260622}"
STREAM_LOGS="${STREAM_LOGS:-1}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
SHUTDOWN_DELAY_MINUTES="${SHUTDOWN_DELAY_MINUTES:-2}"
STATUS_FILE="${ART_ROOT}/${MODEL_SHORT}_PUBLIC_CLOSED_LOOP_STATUS.txt"
DONE_FILE="${ART_ROOT}/${MODEL_SHORT}_PUBLIC_CLOSED_LOOP_DONE"
LOG_DIR="${ART_ROOT}/pipeline_logs_closed_loop_${MODEL_SHORT}"

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
    echo "model_short=${MODEL_SHORT}"
    echo "model_name=${MODEL_NAME}"
    echo "model_path=${MODEL_PATH}"
    echo "base_method=${BASE_METHOD}"
    echo "datasets=${DATASETS}"
  } > "$STATUS_FILE"
}

on_exit() {
  local code=$?
  local state="failed"
  if [[ "$code" == "0" ]]; then
    state="done"
  fi
  write_status "$state" "exit_${code}"
  if [[ "$SHUTDOWN_ON_EXIT" == "1" ]]; then
    echo "[SHUTDOWN] scheduling shutdown in ${SHUTDOWN_DELAY_MINUTES} minutes; cancel with: shutdown -c"
    shutdown -h "+${SHUTDOWN_DELAY_MINUTES}" "Public closed-loop ${MODEL_SHORT} ${state}, exit=${code}" || true
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

run_step py_compile python3 -m py_compile \
  scripts/build_public_pace_cape_requests.py \
  scripts/run_public_editing_baselines.py \
  scripts/evaluate_public_editing_baselines.py

IFS=',' read -ra DATASET_LIST <<< "$DATASETS"
for dataset in "${DATASET_LIST[@]}"; do
  dataset="$(echo "$dataset" | xargs)"
  [[ -n "$dataset" ]] || continue
  dataset_path="${ART_ROOT}/${dataset}_500.json"
  baseline_dir="${ART_ROOT}/${MODEL_SHORT}_${dataset}"
  per_case="${baseline_dir}/${BASE_METHOD}/per_case_results.jsonl"
  selection_dir="${baseline_dir}/${BASE_METHOD}_PACE_CAPE_SELECTION"

  if [[ ! -f "$dataset_path" ]]; then
    echo "[FAIL] missing dataset: $dataset_path"
    exit 1
  fi
  if [[ ! -f "$per_case" ]]; then
    echo "[FAIL] missing baseline per-case results: $per_case"
    echo "[FAIL] Run ${MODEL_SHORT} ${dataset} ${BASE_METHOD} baseline first."
    exit 1
  fi

  run_step "build_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_pace_cape_requests" \
    python3 scripts/build_public_pace_cape_requests.py \
      --dataset_path "$dataset_path" \
      --per_case_results "$per_case" \
      --output_dir "$selection_dir" \
      --dataset_name "$dataset" \
      --model_name "$MODEL_NAME" \
      --base_method "$BASE_METHOD" \
      --selection_split_ratio "$SELECTION_SPLIT_RATIO" \
      --heldout_eval_ratio "$HELDOUT_EVAL_RATIO" \
      --split_seed "$SPLIT_SEED"

  pace_dataset="${selection_dir}/pace_union_dataset.json"
  cape_dataset="${selection_dir}/cape_union_dataset.json"

  if [[ -s "$pace_dataset" ]]; then
    run_step "run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_PACE_EDIT" \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "$pace_dataset" \
        --dataset_name "$dataset" \
        --model_path "$MODEL_PATH" \
        --model_name "$MODEL_NAME" \
        --methods "$BASE_METHOD" \
        --max_cases "$CLOSED_LOOP_MAX_CASES" \
        --output_dir "$baseline_dir" \
        --device "$DEVICE" \
        --disable_generation_test \
        --resume_skip_completed \
        --output_method_suffix PACE_EDIT \
        --sequential_edit
  fi

  if [[ -s "$cape_dataset" ]]; then
    run_step "run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_CAPE_EDIT" \
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "$cape_dataset" \
        --dataset_name "$dataset" \
        --model_path "$MODEL_PATH" \
        --model_name "$MODEL_NAME" \
        --methods "$BASE_METHOD" \
        --max_cases "$CLOSED_LOOP_MAX_CASES" \
        --output_dir "$baseline_dir" \
        --device "$DEVICE" \
        --disable_generation_test \
        --resume_skip_completed \
        --output_method_suffix CAPE_EDIT \
        --sequential_edit
  fi
done

run_step aggregate_public python3 scripts/evaluate_public_editing_baselines.py \
  --root_dir "$ART_ROOT" \
  --output_dir "$ART_ROOT"

touch "$DONE_FILE"
write_status "done" "complete"
echo "===== PUBLIC CLOSED LOOP DONE ====="
echo "status_file: $STATUS_FILE"
echo "done_file: $DONE_FILE"
