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

DATASET="${DATASET:-artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged}"
REQUESTS_PATH="${REQUESTS_PATH:-artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json}"
METHODS="${METHODS:-FT,KN,IKE}"
DEVICE="${DEVICE:-0}"
BATCH_SIZE="${BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
SHUTDOWN_ON_EXIT="${SHUTDOWN_ON_EXIT:-0}"
SHUTDOWN_DELAY_MINUTES="${SHUTDOWN_DELAY_MINUTES:-2}"
STATUS_FILE="artifacts/synthetic_privacy_extra_editors_status.txt"

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
    echo "methods=${METHODS}"
  } > "$STATUS_FILE"
  if [[ "$SHUTDOWN_ON_EXIT" == "1" ]]; then
    echo "[SHUTDOWN] scheduling shutdown in ${SHUTDOWN_DELAY_MINUTES} minutes; cancel with: shutdown -c"
    shutdown -h "+${SHUTDOWN_DELAY_MINUTES}" "Synthetic privacy extra editors ${state}, exit=${code}" || true
  fi
}
trap on_exit EXIT

if [[ ! -f "$DATASET" ]]; then
  echo "[FAIL] missing dataset: $DATASET"
  exit 1
fi
if [[ ! -d "$MODEL_PATH" ]]; then
  echo "[FAIL] missing model: $MODEL_PATH"
  exit 1
fi
if [[ ! -f "$REQUESTS_PATH" ]]; then
  echo "[FAIL] missing requests: $REQUESTS_PATH"
  exit 1
fi

python3 -m py_compile scripts/run_privacy_refusal_edit.py

IFS=',' read -ra METHOD_LIST <<< "$METHODS"
for method in "${METHOD_LIST[@]}"; do
  method="$(echo "$method" | xargs)"
  [[ -n "$method" ]] || continue
  lower="$(echo "$method" | tr '[:upper:]' '[:lower:]')"
  hparams="hparams/${method}/qwen2.5-7b.yaml"
  if [[ ! -f "$hparams" ]]; then
    echo "[FAIL] missing hparams for ${method}: $hparams"
    exit 1
  fi
  out_dir="artifacts/run_20260622_v2_${lower}_baseline"
  run_name="v2_${lower}_baseline"
  echo "[STEP] synthetic privacy ${method}"
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
    --disable_fluency_eval
done

echo "===== SYNTHETIC PRIVACY EXTRA EDITORS DONE ====="
