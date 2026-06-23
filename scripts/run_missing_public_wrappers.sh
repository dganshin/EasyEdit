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

ART_ROOT="${ART_ROOT:-artifacts/public_benchmarks_20260623_200}"
MAX_CASES="${MAX_CASES:-200}"
INSTANCE_MODEL="${INSTANCE_MODEL:-auto}"
QWEN_MODEL="${QWEN_MODEL:-/root/autodl-tmp/models/Qwen2.5-7B}"
GPTJ_MODEL="${GPTJ_MODEL:-/root/autodl-tmp/models/gpt-j-6B}"
DEVICE="${DEVICE:-0}"
STREAM_LOGS="${STREAM_LOGS:-1}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
STATUS_FILE="${ART_ROOT}/PUBLIC_MISSING_WRAPPERS_STATUS.txt"

mkdir -p "$ART_ROOT"

write_status() {
  local state="$1"
  local step="$2"
  {
    echo "state=${state}"
    echo "step=${step}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "art_root=${ART_ROOT}"
    echo "max_cases=${MAX_CASES}"
    echo "instance_model=${INSTANCE_MODEL}"
  } > "$STATUS_FILE"
}

model_valid() {
  local path="$1"
  [[ -d "$path" && -f "$path/config.json" ]] || return 1
  python3 - "$path/config.json" <<'PY'
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

detect_model() {
  if [[ "$INSTANCE_MODEL" == "qwen" || "$INSTANCE_MODEL" == "gptj" ]]; then
    echo "$INSTANCE_MODEL"
    return 0
  fi
  local has_qwen=0
  local has_gptj=0
  model_valid "$QWEN_MODEL" && has_qwen=1 || true
  model_valid "$GPTJ_MODEL" && has_gptj=1 || true
  if [[ "$has_qwen" == "1" && "$has_gptj" == "0" ]]; then
    echo "qwen"
  elif [[ "$has_gptj" == "1" && "$has_qwen" == "0" ]]; then
    echo "gptj"
  elif [[ "$has_qwen" == "1" && "$has_gptj" == "1" ]]; then
    echo "[FAIL] Both model dirs are valid; set INSTANCE_MODEL=qwen or INSTANCE_MODEL=gptj." >&2
    return 2
  else
    echo "[FAIL] No valid model dir found." >&2
    return 2
  fi
}

write_status "starting" "detect_model"
detected="$(detect_model)"
echo "[AUTO] detected_instance_model=${detected}"

case "$detected" in
  qwen)
    model_short="qwen"
    model_name="qwen2.5-7b"
    model_path="$QWEN_MODEL"
    ;;
  gptj)
    model_short="gptj"
    model_name="gpt-j-6B"
    model_path="$GPTJ_MODEL"
    ;;
  *)
    exit 2
    ;;
esac

write_status "running" "${model_short}_missing_public_wrappers"

ART_ROOT="$ART_ROOT" \
PUBLIC_DATASET_SIZE="$MAX_CASES" \
MODEL_SHORT="$model_short" \
MODEL_NAME="$model_name" \
MODEL_PATH="$model_path" \
BASE_METHOD=ROME \
DATASETS=counterfact,zsre \
DEVICE="$DEVICE" \
STREAM_LOGS="$STREAM_LOGS" \
SHUTDOWN_ON_EXIT="$SHUTDOWN_ON_EXIT" \
bash scripts/run_public_closed_loop_wrappers.sh

python3 scripts/merge_new_baseline_results.py \
  --public_root "$ART_ROOT" \
  --output_dir artifacts/final_comparison_20260623_200

write_status "done" "complete"
echo "===== MISSING PUBLIC WRAPPERS DONE ====="
echo "detected_instance_model: $detected"
echo "status_file: $STATUS_FILE"
