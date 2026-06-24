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
MAX_CASES="${MAX_CASES:-200}"
PUBLIC_DATASET_SIZE="${PUBLIC_DATASET_SIZE:-200}"
CLOSED_LOOP_MAX_CASES="${CLOSED_LOOP_MAX_CASES:-1000}"
DEVICE="${DEVICE:-0}"
SELECTION_SPLIT_RATIO="${SELECTION_SPLIT_RATIO:-0.6}"
HELDOUT_EVAL_RATIO="${HELDOUT_EVAL_RATIO:-0.4}"
SPLIT_SEED="${SPLIT_SEED:-20260622}"
STREAM_LOGS="${STREAM_LOGS:-1}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
ALLOW_AUTODL_SHUTDOWN="${ALLOW_AUTODL_SHUTDOWN:-0}"
SHUTDOWN_DELAY_MINUTES="${SHUTDOWN_DELAY_MINUTES:-2}"
GPTJ_WRAPPER_POLICY="${GPTJ_WRAPPER_POLICY:-nonsequential}"
FORCE_RERUN_WRAPPERS="${FORCE_RERUN_WRAPPERS:-0}"
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
    echo "public_dataset_size=${PUBLIC_DATASET_SIZE}"
    echo "shutdown_on_exit=${SHUTDOWN_ON_EXIT}"
    echo "allow_autodl_shutdown=${ALLOW_AUTODL_SHUTDOWN}"
    echo "gptj_wrapper_policy=${GPTJ_WRAPPER_POLICY}"
  } > "$STATUS_FILE"
}

on_exit() {
  local code=$?
  local state="failed"
  if [[ "$code" == "0" ]]; then
    state="done"
  fi
  write_status "$state" "exit_${code}"
  if [[ "$SHUTDOWN_ON_EXIT" == "1" && "$ALLOW_AUTODL_SHUTDOWN" == "1" ]]; then
    echo "[SHUTDOWN] scheduling shutdown in ${SHUTDOWN_DELAY_MINUTES} minutes."
    echo "[SHUTDOWN] On AutoDL, cancel from the web console if needed; do not run shell cancel commands in this project."
    shutdown -h "+${SHUTDOWN_DELAY_MINUTES}" "Public closed-loop ${MODEL_SHORT} ${state}, exit=${code}" || true
  elif [[ "$SHUTDOWN_ON_EXIT" == "1" ]]; then
    echo "[SHUTDOWN_SKIPPED] SHUTDOWN_ON_EXIT=1 but ALLOW_AUTODL_SHUTDOWN!=1; no shutdown scheduled."
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

write_wrapper_failure() {
  local baseline_dir="$1"
  local dataset="$2"
  local method="$3"
  local message="$4"
  local status="${5:-failed}"
  local method_dir="${baseline_dir}/${method}"
  mkdir -p "$method_dir"
  python3 - "$method_dir" "$dataset" "$MODEL_NAME" "$method" "$message" "$status" <<'PY'
import json
import sys
from pathlib import Path

method_dir = Path(sys.argv[1])
dataset = sys.argv[2]
model = sys.argv[3]
method = sys.argv[4]
message = sys.argv[5]
status = sys.argv[6]
config = {
    "dataset_name": dataset,
    "model_name": model,
    "method": method,
    "base_method": "ROME",
    "wrapper_error": message,
}
summary = {
    "status": status,
    "method": method,
    "num_cases": 0,
    "elapsed_sec": 0,
    "error": message,
}
(method_dir / "method_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
(method_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(method_dir / "run_log.txt").write_text(message + "\n", encoding="utf-8")
PY
}

summary_status() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "missing"
    return 0
  fi
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    print("invalid")
    raise SystemExit(0)
print(payload.get("status") or "unknown")
PY
}

IFS=',' read -ra DATASET_LIST <<< "$DATASETS"
overall_failed=0
for dataset in "${DATASET_LIST[@]}"; do
  dataset="$(echo "$dataset" | xargs)"
  [[ -n "$dataset" ]] || continue
  dataset_path="${ART_ROOT}/${dataset}_500.json"
  baseline_dir="${ART_ROOT}/${MODEL_SHORT}_${dataset}"
  per_case="${baseline_dir}/${BASE_METHOD}/per_case_results.jsonl"
  selection_dir="${baseline_dir}/${BASE_METHOD}_PACE_CAPE_SELECTION"

  if [[ "$MODEL_SHORT" == "gptj" && "$GPTJ_WRAPPER_POLICY" == "skip_uncalibrated" ]]; then
    msg="GPT-J public PACE/CAPE wrappers are skipped because GPTJ_WRAPPER_POLICY=skip_uncalibrated. Use GPTJ_WRAPPER_POLICY=nonsequential for the GPT-J adapted run, or GPTJ_WRAPPER_POLICY=run_uncalibrated to reproduce the old sequential behavior."
    echo "[SKIP] ${dataset}: $msg"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "calibration_needed"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "calibration_needed"
    continue
  fi

  wrapper_run_args=(--resume_skip_completed --sequential_edit)
  if [[ "$MODEL_SHORT" == "gptj" && "$GPTJ_WRAPPER_POLICY" == "nonsequential" ]]; then
    echo "[GPT-J ADAPT] ${dataset}: running public PACE/CAPE wrappers without long sequential ROME accumulation."
    wrapper_run_args=()
    for wrapper in "${BASE_METHOD}_PACE_EDIT" "${BASE_METHOD}_CAPE_EDIT"; do
      wrapper_dir="${baseline_dir}/${wrapper}"
      status="$(summary_status "${wrapper_dir}/summary.json")"
      if [[ "$FORCE_RERUN_WRAPPERS" == "1" || "$status" != "ok" ]]; then
        echo "[GPT-J ADAPT] ${dataset}/${wrapper}: clearing prior status=${status} before rerun."
        rm -f "${wrapper_dir}/summary.json" "${wrapper_dir}/per_case_results.jsonl"
      else
        echo "[GPT-J ADAPT] ${dataset}/${wrapper}: keeping completed ok result."
      fi
    done
  fi

  if [[ ! -f "$dataset_path" ]]; then
    msg="missing dataset: $dataset_path"
    echo "[FAIL] $msg"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "missing_prerequisite"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "missing_prerequisite"
    overall_failed=1
    continue
  fi
  if [[ ! -f "$per_case" ]]; then
    msg="missing baseline per-case results for wrapper: ${per_case}; run ${MODEL_SHORT} ${dataset} ${BASE_METHOD} baseline first"
    echo "[FAIL] $msg"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "missing_prerequisite"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "missing_prerequisite"
    overall_failed=1
    continue
  fi

  if ! run_step "build_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_pace_cape_requests" \
    python3 scripts/build_public_pace_cape_requests.py \
      --dataset_path "$dataset_path" \
      --per_case_results "$per_case" \
      --output_dir "$selection_dir" \
      --dataset_name "$dataset" \
      --model_name "$MODEL_NAME" \
      --base_method "$BASE_METHOD" \
      --selection_split_ratio "$SELECTION_SPLIT_RATIO" \
      --heldout_eval_ratio "$HELDOUT_EVAL_RATIO" \
      --split_seed "$SPLIT_SEED" \
      --dataset_limit "$PUBLIC_DATASET_SIZE"; then
    msg="failed to build public PACE/CAPE wrapper requests for ${MODEL_SHORT}/${dataset}"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "failed"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "failed"
    overall_failed=1
    continue
  fi

  pace_dataset="${selection_dir}/pace_union_dataset.json"
  cape_dataset="${selection_dir}/cape_union_dataset.json"

  if [[ -s "$pace_dataset" ]]; then
    if ! run_step "run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_PACE_EDIT" \
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
        --output_method_suffix PACE_EDIT \
        "${wrapper_run_args[@]}"; then
      msg="failed running ${MODEL_SHORT}/${dataset}/${BASE_METHOD}_PACE_EDIT; see ${LOG_DIR}/run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_PACE_EDIT.log"
      write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "failed"
      overall_failed=1
    fi
  else
    msg="empty or missing PACE union dataset: ${pace_dataset}"
    echo "[FAIL] $msg"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_PACE_EDIT" "$msg" "missing_prerequisite"
    overall_failed=1
  fi

  if [[ -s "$cape_dataset" ]]; then
    if ! run_step "run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_CAPE_EDIT" \
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
        --output_method_suffix CAPE_EDIT \
        "${wrapper_run_args[@]}"; then
      msg="failed running ${MODEL_SHORT}/${dataset}/${BASE_METHOD}_CAPE_EDIT; see ${LOG_DIR}/run_${MODEL_SHORT}_${dataset}_${BASE_METHOD}_CAPE_EDIT.log"
      write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "failed"
      overall_failed=1
    fi
  else
    msg="empty or missing CAPE union dataset: ${cape_dataset}"
    echo "[FAIL] $msg"
    write_wrapper_failure "$baseline_dir" "$dataset" "${BASE_METHOD}_CAPE_EDIT" "$msg" "missing_prerequisite"
    overall_failed=1
  fi
done

if ! run_step aggregate_public python3 scripts/evaluate_public_editing_baselines.py \
  --root_dir "$ART_ROOT" \
  --output_dir "$ART_ROOT"; then
  overall_failed=1
fi

touch "$DONE_FILE"
if [[ "$overall_failed" == "0" ]]; then
  write_status "done" "complete"
else
  write_status "done_with_failures" "complete"
fi
echo "===== PUBLIC CLOSED LOOP DONE ====="
echo "status_file: $STATUS_FILE"
echo "done_file: $DONE_FILE"
exit 0
