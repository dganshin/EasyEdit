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
export http_proxy="${http_proxy:-http://127.0.0.1:7890}"
export https_proxy="${https_proxy:-http://127.0.0.1:7890}"
export HTTP_PROXY="${HTTP_PROXY:-$http_proxy}"
export HTTPS_PROXY="${HTTPS_PROXY:-$https_proxy}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

DATASET="${DATASET:-artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged}"
REQUESTS_PATH="${REQUESTS_PATH:-artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json}"
METHODS="${METHODS:-FT,KN,IKE}"
DEVICE="${DEVICE:-0}"
BATCH_SIZE="${BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
STREAM_LOGS="${STREAM_LOGS:-1}"
FINAL_DIR="${FINAL_DIR:-artifacts/final_comparison_20260623_urgent}"
STATUS_FILE="${FINAL_DIR}/synthetic_privacy_extra_editors_status.txt"
FAIL_CSV="${FINAL_DIR}/synthetic_extra_editors_failure_matrix.csv"

mkdir -p "$FINAL_DIR"
echo "method,status,summary_path,log_path,error" > "$FAIL_CSV"

write_status() {
  local state="$1"
  {
    echo "state=${state}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "methods=${METHODS}"
    echo "dataset=${DATASET}"
    echo "model_path=${MODEL_PATH}"
  } > "$STATUS_FILE"
}

write_json_summary() {
  local path="$1"
  local method="$2"
  local status="$3"
  local error="${4:-}"
  python3 - "$path" "$method" "$status" "$error" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
method = sys.argv[2]
status = sys.argv[3]
error = sys.argv[4]
payload = {
    "status": status,
    "method": method,
    "error": error or None,
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

append_csv_row() {
  local method="$1"
  local status="$2"
  local summary_path="$3"
  local log_path="$4"
  local error="${5:-}"
  python3 - "$FAIL_CSV" "$method" "$status" "$summary_path" "$log_path" "$error" <<'PY'
import csv
import sys

csv_path, method, status, summary_path, log_path, error = sys.argv[1:]
with open(csv_path, "a", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerow([method, status, summary_path, log_path, error])
PY
}

clean_gpu() {
  python3 - <<'PY' >/dev/null 2>&1 || true
import gc
try:
    import torch
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
except Exception:
    pass
gc.collect()
PY
}

if [[ ! -f "$DATASET" ]]; then
  echo "[FAIL] missing dataset: $DATASET"
  write_status "failed_missing_dataset"
  exit 1
fi
if [[ ! -d "$MODEL_PATH" ]]; then
  echo "[FAIL] missing model: $MODEL_PATH"
  write_status "failed_missing_model"
  exit 1
fi
if [[ ! -f "$REQUESTS_PATH" ]]; then
  echo "[FAIL] missing requests: $REQUESTS_PATH"
  write_status "failed_missing_requests"
  exit 1
fi

if ! python3 -m py_compile scripts/run_privacy_refusal_edit.py; then
  echo "[FAIL] py_compile failed"
  write_status "failed_py_compile"
  exit 1
fi

write_status "running"
overall_failed=0

IFS=',' read -ra METHOD_LIST <<< "$METHODS"
for method in "${METHOD_LIST[@]}"; do
  method="$(echo "$method" | xargs)"
  [[ -n "$method" ]] || continue
  lower="$(echo "$method" | tr '[:upper:]' '[:lower:]')"
  hparams="hparams/${method}/qwen2.5-7b.yaml"
  out_dir="artifacts/run_20260623_v2_${lower}_baseline"
  run_name="v2_${lower}_baseline"
  summary_path="${out_dir}/summary.json"
  log_path="${out_dir}/run.log"
  mkdir -p "$out_dir"

  if [[ ! -f "$hparams" ]]; then
    err="missing hparams: $hparams"
    echo "[FAIL] ${method}: ${err}"
    write_json_summary "$summary_path" "$method" "failed" "$err"
    append_csv_row "$method" "failed" "$summary_path" "$log_path" "$err"
    overall_failed=1
    continue
  fi

  if [[ -f "$summary_path" ]]; then
    status="$(python3 - "$summary_path" <<'PY'
import json, sys
try:
    print((json.load(open(sys.argv[1], encoding="utf-8")).get("status") or "").lower())
except Exception:
    print("")
PY
)"
    if [[ "$status" == "ok" ]]; then
      echo "[SKIP] ${method}: summary status=ok"
      append_csv_row "$method" "skipped_ok" "$summary_path" "$log_path" ""
      continue
    fi
  fi

  echo "[STEP] synthetic privacy ${method}"
  clean_gpu
  set +e
  python3 scripts/run_privacy_refusal_edit.py \
    --method "$method" \
    --dataset "$DATASET" \
    --model_path "$MODEL_PATH" \
    --hparams "$hparams" \
    --device "$DEVICE" \
    --output_dir "$out_dir" \
    --requests_path "$REQUESTS_PATH" \
    --run_name "$run_name" \
    --batch_size "$BATCH_SIZE" \
    --max_new_tokens "$MAX_NEW_TOKENS" \
    --full_private_eval \
    --eval_public \
    --disable_fluency_eval > "$log_path" 2>&1
  code=$?
  set -e

  if [[ "$STREAM_LOGS" == "1" ]]; then
    tail -n 80 "$log_path" || true
  fi

  if [[ "$code" == "0" ]]; then
    write_json_summary "$summary_path" "$method" "ok" ""
    append_csv_row "$method" "ok" "$summary_path" "$log_path" ""
    echo "[OK] ${method}"
  else
    err="$(tail -n 40 "$log_path" | tr '\n' ' ')"
    write_json_summary "$summary_path" "$method" "failed" "$err"
    append_csv_row "$method" "failed" "$summary_path" "$log_path" "$err"
    echo "[FAIL] ${method}; continuing"
    overall_failed=1
  fi
  clean_gpu
done

if [[ "$overall_failed" == "0" ]]; then
  write_status "done"
  echo "===== SYNTHETIC PRIVACY EXTRA EDITORS DONE ====="
else
  write_status "done_with_failures"
  echo "===== SYNTHETIC PRIVACY EXTRA EDITORS DONE WITH FAILURES ====="
fi

exit 0
