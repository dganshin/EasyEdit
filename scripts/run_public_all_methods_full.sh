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
DEVICE="${DEVICE:-0}"
INSTANCE_MODEL="${INSTANCE_MODEL:-auto}"
QWEN_MODEL="${QWEN_MODEL:-/root/autodl-tmp/models/Qwen2.5-7B}"
GPTJ_MODEL="${GPTJ_MODEL:-/root/autodl-tmp/models/gpt-j-6B}"
RUN_PUBLIC_WRAPPERS="${RUN_PUBLIC_WRAPPERS:-1}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
STREAM_LOGS="${STREAM_LOGS:-1}"
STATUS_FILE="${ART_ROOT}/PUBLIC_ALL_METHODS_STATUS.txt"

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
    echo "run_public_wrappers=${RUN_PUBLIC_WRAPPERS}"
    echo "shutdown_on_exit=${SHUTDOWN_ON_EXIT}"
  } > "$STATUS_FILE"
}

model_valid() {
  local path="$1"
  [[ -d "$path" && -f "$path/config.json" ]] || return 1
  python3 - "$path/config.json" <<'PY'
import json, sys
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
    echo "[FAIL] Both Qwen and GPT-J model directories look valid." >&2
    echo "[FAIL] Set INSTANCE_MODEL=qwen or INSTANCE_MODEL=gptj explicitly to avoid mixing instances." >&2
    return 2
  else
    echo "[FAIL] No valid model detected." >&2
    echo "[FAIL] Checked Qwen: $QWEN_MODEL" >&2
    echo "[FAIL] Checked GPT-J: $GPTJ_MODEL" >&2
    return 2
  fi
}

write_status "starting" "detect_model"
detected="$(detect_model)"
echo "[AUTO] detected_instance_model=${detected}"

case "$detected" in
  qwen)
    write_status "running" "qwen_full_public_all_methods"
    ART_ROOT="$ART_ROOT" \
    MAX_CASES="$MAX_CASES" \
    QWEN_MODEL="$QWEN_MODEL" \
    METHODS_QWEN="${METHODS_QWEN:-ROME,FT,KN,IKE}" \
    RUN_PUBLIC_WRAPPERS="$RUN_PUBLIC_WRAPPERS" \
    SHUTDOWN_ON_EXIT="$SHUTDOWN_ON_EXIT" \
    STREAM_LOGS="$STREAM_LOGS" \
    DEVICE="$DEVICE" \
    bash scripts/run_public_qwen_full.sh
    ;;
  gptj)
    write_status "running" "gptj_full_public_all_methods"
    ART_ROOT="$ART_ROOT" \
    MAX_CASES="$MAX_CASES" \
    GPTJ_MODEL="$GPTJ_MODEL" \
    METHODS_GPTJ="${METHODS_GPTJ:-ROME,FT,KN,IKE}" \
    RUN_PUBLIC_WRAPPERS="$RUN_PUBLIC_WRAPPERS" \
    SHUTDOWN_ON_EXIT="$SHUTDOWN_ON_EXIT" \
    STREAM_LOGS="$STREAM_LOGS" \
    DEVICE="$DEVICE" \
    bash scripts/run_public_gptj_full.sh
    ;;
  *)
    echo "[FAIL] unsupported detected model: $detected"
    exit 2
    ;;
esac

write_status "done" "complete"
echo "===== PUBLIC ALL METHODS DONE ====="
echo "detected_instance_model: $detected"
echo "status_file: $STATUS_FILE"
