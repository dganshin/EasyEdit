#!/usr/bin/env bash

set -uo pipefail

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
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

ART_ROOT="${ART_ROOT:-artifacts/public_benchmarks_20260623_200}"
GPTJ_MODEL_DIR="${GPTJ_MODEL_DIR:-/root/autodl-tmp/models/gpt-j-6B}"
MAX_CASES="${MAX_CASES:-200}"
DATASETS="${DATASETS:-counterfact,zsre}"
METHODS="${METHODS:-ROME,FT}"
TRY_MEMIT="${TRY_MEMIT:-0}"
RUN_WRAPPERS_IF_POSSIBLE="${RUN_WRAPPERS_IF_POSSIBLE:-0}"
TIME_BUDGET_MIN="${TIME_BUDGET_MIN:-120}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
STREAM_LOGS="${STREAM_LOGS:-1}"
DEVICE="${DEVICE:-0}"
PATCH_DIR="${PATCH_DIR:-artifacts/gptj_fast_patch_20260623}"
STATUS_FILE="${PATCH_DIR}/GPTJ_FAST_PATCH_STATUS.txt"
FAIL_CSV="${PATCH_DIR}/gptj_fast_patch_failures.csv"

mkdir -p "$PATCH_DIR"
echo "dataset,method,status,summary_path,log_path,error" > "$FAIL_CSV"

write_status() {
  local state="$1"
  local item="${2:-}"
  {
    echo "state=${state}"
    echo "item=${item}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "art_root=${ART_ROOT}"
    echo "model=${GPTJ_MODEL_DIR}"
    echo "max_cases=${MAX_CASES}"
    echo "datasets=${DATASETS}"
    echo "methods=${METHODS}"
    echo "try_memit=${TRY_MEMIT}"
    echo "run_wrappers_if_possible=${RUN_WRAPPERS_IF_POSSIBLE}"
  } > "$STATUS_FILE"
}

append_failure() {
  local dataset="$1"
  local method="$2"
  local status="$3"
  local summary_path="$4"
  local log_path="$5"
  local error="${6:-}"
  python3 - "$FAIL_CSV" "$dataset" "$method" "$status" "$summary_path" "$log_path" "$error" <<'PY'
import csv
import sys

path, dataset, method, status, summary_path, log_path, error = sys.argv[1:]
with open(path, "a", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerow([dataset, method, status, summary_path, log_path, error])
PY
}

write_failed_summary() {
  local summary_path="$1"
  local method="$2"
  local error="$3"
  python3 - "$summary_path" "$method" "$error" <<'PY'
import json
import sys
from pathlib import Path

path, method, error = sys.argv[1:]
Path(path).parent.mkdir(parents=True, exist_ok=True)
Path(path).write_text(json.dumps({"status": "failed", "method": method, "error": error}, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

elapsed_minutes() {
  python3 - "$START_TS" <<'PY'
import sys, time
print((time.time() - float(sys.argv[1])) / 60.0)
PY
}

time_exceeded() {
  python3 - "$START_TS" "$TIME_BUDGET_MIN" <<'PY'
import sys, time
print("1" if (time.time() - float(sys.argv[1])) / 60.0 >= float(sys.argv[2]) else "0")
PY
}

if [[ ! -d "$GPTJ_MODEL_DIR" ]]; then
  echo "[FAIL] missing GPT-J model dir: $GPTJ_MODEL_DIR"
  write_status "failed_missing_model" "$GPTJ_MODEL_DIR"
  append_failure "all" "all" "missing_model" "" "" "$GPTJ_MODEL_DIR not found"
  python3 scripts/extract_gptj_public_patch_metrics.py || true
  exit 0
fi

if ! python3 -m py_compile scripts/run_public_editing_baselines.py scripts/extract_gptj_public_patch_metrics.py; then
  echo "[FAIL] py_compile failed"
  write_status "failed_py_compile" ""
  exit 1
fi

python3 scripts/extract_gptj_public_patch_metrics.py || true
START_TS="$(python3 - <<'PY'
import time
print(time.time())
PY
)"
write_status "running" "start"

IFS=',' read -ra DATASET_LIST <<< "$DATASETS"
IFS=',' read -ra METHOD_LIST <<< "$METHODS"

for dataset in "${DATASET_LIST[@]}"; do
  dataset="$(echo "$dataset" | xargs)"
  [[ -n "$dataset" ]] || continue
  dataset_path="${ART_ROOT}/${dataset}_500.json"
  if [[ "$dataset" == "counterfact" ]]; then
    out_dir="${ART_ROOT}/gptj_counterfact"
  elif [[ "$dataset" == "zsre" ]]; then
    out_dir="${ART_ROOT}/gptj_zsre"
  else
    echo "[SKIP] unsupported dataset: $dataset"
    continue
  fi
  if [[ ! -f "$dataset_path" ]]; then
    echo "[FAIL] missing dataset json: $dataset_path"
    append_failure "$dataset" "all" "missing_dataset" "" "" "$dataset_path not found"
    continue
  fi

  for method in "${METHOD_LIST[@]}"; do
    method="$(echo "$method" | xargs)"
    [[ -n "$method" ]] || continue
    if [[ "$method" == "KN" || "$method" == "IKE" ]]; then
      echo "[SKIP] ${dataset}/${method}: KN/IKE excluded from GPT-J fast patch"
      continue
    fi
    if [[ "$method" == "MEMIT" && "$TRY_MEMIT" != "1" ]]; then
      echo "[SKIP] ${dataset}/MEMIT: TRY_MEMIT!=1"
      continue
    fi
    if [[ "$(time_exceeded)" == "1" ]]; then
      echo "[STOP] time budget exceeded before ${dataset}/${method}"
      append_failure "$dataset" "$method" "time_budget_skipped" "" "" "TIME_BUDGET_MIN exceeded"
      break 2
    fi

    method_dir="${out_dir}/${method}"
    summary_path="${method_dir}/summary.json"
    log_path="${PATCH_DIR}/${dataset}_${method}.log"
    if [[ -f "$summary_path" ]]; then
      status_and_cases="$(python3 - "$summary_path" <<'PY'
import json, sys
try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
    print((payload.get("status") or "").lower() + "\t" + str(payload.get("num_cases") or 0))
except Exception:
    print("\t0")
PY
)"
      status="${status_and_cases%%$'\t'*}"
      existing_cases="${status_and_cases##*$'\t'}"
      if [[ "$status" == "ok" && "$existing_cases" =~ ^[0-9]+$ && "$existing_cases" -ge "$MAX_CASES" ]]; then
        echo "[SKIP] ${dataset}/${method}: existing status=ok num_cases=${existing_cases} >= max_cases=${MAX_CASES}"
        append_failure "$dataset" "$method" "skipped_ok" "$summary_path" "$log_path" ""
        continue
      elif [[ "$status" == "ok" ]]; then
        echo "[RERUN] ${dataset}/${method}: existing status=ok but num_cases=${existing_cases} < max_cases=${MAX_CASES}"
      fi
    fi

    echo "[STEP] GPT-J ${dataset}/${method} max_cases=${MAX_CASES}"
    write_status "running" "${dataset}/${method}"
    set +e
    if [[ "$STREAM_LOGS" == "1" ]]; then
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "$dataset_path" \
        --dataset_name "$dataset" \
        --model_path "$GPTJ_MODEL_DIR" \
        --model_name gpt-j-6B \
        --methods "$method" \
        --max_cases "$MAX_CASES" \
        --output_dir "$out_dir" \
        --device "$DEVICE" \
        --resume_skip_completed \
        2>&1 | tee "$log_path"
      code=${PIPESTATUS[0]}
    else
      python3 scripts/run_public_editing_baselines.py \
        --dataset_path "$dataset_path" \
        --dataset_name "$dataset" \
        --model_path "$GPTJ_MODEL_DIR" \
        --model_name gpt-j-6B \
        --methods "$method" \
        --max_cases "$MAX_CASES" \
        --output_dir "$out_dir" \
        --device "$DEVICE" \
        --resume_skip_completed \
        > "$log_path" 2>&1
      code=$?
    fi
    set -e
    if [[ "$code" == "0" ]]; then
      append_failure "$dataset" "$method" "ok" "$summary_path" "$log_path" ""
      echo "[OK] ${dataset}/${method}"
    else
      err="$(tail -n 40 "$log_path" | tr '\n' ' ')"
      write_failed_summary "$summary_path" "$method" "$err"
      append_failure "$dataset" "$method" "failed" "$summary_path" "$log_path" "$err"
      echo "[FAIL] ${dataset}/${method}; continuing"
    fi
  done
done

if [[ "$RUN_WRAPPERS_IF_POSSIBLE" == "1" ]]; then
  echo "[INFO] wrappers requested, but not implemented in fast patch by default; use public wrapper script manually only after ROME per_case exists."
fi

python3 scripts/extract_gptj_public_patch_metrics.py || true
python3 scripts/extract_all_available_metrics_now.py || true
write_status "done" "complete"
echo "===== GPT-J FAST PATCH DONE ====="
echo "patch_dir: $PATCH_DIR"
echo "elapsed_minutes: $(elapsed_minutes)"
