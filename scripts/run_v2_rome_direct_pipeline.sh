#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f /root/miniconda3/etc/profile.d/conda.sh ]]; then
  source /root/miniconda3/etc/profile.d/conda.sh
fi

if command -v conda >/dev/null 2>&1; then
  conda activate easyedit
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

RUN_DATE="${RUN_DATE:-20260615}"
RUN_TAG="${RUN_TAG:-v2_rome_direct}"
RUN_NAME="run_${RUN_DATE}_${RUN_TAG}"
ROME_RUN_NAME="${ROME_RUN_NAME:-v2_rome_direct}"

DATA_DIR="${DATA_DIR:-artifacts/synthetic_privacy_data_v2}"
PRE_ART_DIR="${PRE_ART_DIR:-artifacts/run_20260615_v2_lora_mlp_only}"
OUT_DIR="${OUT_DIR:-/root/autodl-tmp/outputs/easyedit/${RUN_TAG}}"
LOG_DIR="${OUT_DIR}/logs"
ART_DIR="${ART_DIR:-artifacts/${RUN_NAME}}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged}"
HPARAMS_PATH="${HPARAMS_PATH:-hparams/ROME/qwen2.5-7b.yaml}"
DEVICE="${DEVICE:-0}"

NUM_EDIT_PEOPLE="${NUM_EDIT_PEOPLE:-10}"
PRIVATE_PER_PERSON="${PRIVATE_PER_PERSON:-2}"
PROMPT_STYLE="${PROMPT_STYLE:-canonical_qa}"
GEN_BATCH_SIZE="${GEN_BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
TARGET_NEW="${TARGET_NEW:-I cannot provide private information.}"

STREAM_LOGS="${STREAM_LOGS:-0}"
STATUS_FILE="${STATUS_FILE:-${OUT_DIR}/pipeline_status.txt}"
DONE_FILE="${DONE_FILE:-${OUT_DIR}/PIPELINE_DONE}"
TOTAL_STEPS=4
CURRENT_STEP=0

mkdir -p "$OUT_DIR" "$LOG_DIR" "$ART_DIR" "$ART_DIR/logs"
rm -f "$DONE_FILE"

REQUESTS_JSON="${OUT_DIR}/${ROME_RUN_NAME}_requests.json"
SUMMARY_JSON="${OUT_DIR}/${ROME_RUN_NAME}_summary.json"

write_status() {
  local state="$1"
  local step_name="$2"
  {
    echo "run_name=${RUN_NAME}"
    echo "state=${state}"
    echo "current_step=${CURRENT_STEP}"
    echo "total_steps=${TOTAL_STEPS}"
    echo "step_name=${step_name}"
    echo "out_dir=${OUT_DIR}"
    echo "art_dir=${ART_DIR}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
  } > "$STATUS_FILE"
}

print_progress() {
  local step_name="$1"
  echo "[STEP ${CURRENT_STEP}/${TOTAL_STEPS}] ${step_name}"
}

run_step() {
  local name="$1"
  shift
  CURRENT_STEP=$((CURRENT_STEP + 1))
  print_progress "$name"
  write_status "running" "$name"
  if [[ "$STREAM_LOGS" == "1" ]]; then
    if "$@" 2>&1 | tee "${LOG_DIR}/${name}.log"; then
      echo "[OK]  $name"
    else
      echo "[FAIL] $name"
      tail -n 120 "${LOG_DIR}/${name}.log" || true
      exit 1
    fi
  elif "$@" > "${LOG_DIR}/${name}.log" 2>&1; then
    echo "[OK]  $name"
  else
    echo "[FAIL] $name"
    tail -n 120 "${LOG_DIR}/${name}.log" || true
    exit 1
  fi
}

write_status "starting" "bootstrap"

run_step build_direct_requests \
  python scripts/build_rome_privacy_requests.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --output_path "$REQUESTS_JSON" \
  --num_people "$NUM_EDIT_PEOPLE" \
  --private_per_person "$PRIVATE_PER_PERSON" \
  --prompt_style "$PROMPT_STYLE" \
  --target_new "$TARGET_NEW"

run_step run_rome_direct \
  python scripts/run_privacy_refusal_edit.py \
  --method ROME \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --model_path "$MODEL_PATH" \
  --hparams "$HPARAMS_PATH" \
  --device "$DEVICE" \
  --output_dir "$OUT_DIR" \
  --requests_path "$REQUESTS_JSON" \
  --run_name "$ROME_RUN_NAME" \
  --batch_size "$GEN_BATCH_SIZE" \
  --max_new_tokens "$MAX_NEW_TOKENS" \
  --full_private_eval \
  --eval_public \
  --disable_fluency_eval

run_step summarize_results \
  python scripts/summarize_rome_privacy.py \
  --pre_privacy_eval "${PRE_ART_DIR}/privacy_leakage_eval_merged_v2.json" \
  --post_subset_privacy_eval "${OUT_DIR}/privacy_leakage_eval_${ROME_RUN_NAME}_subset.json" \
  --post_full_privacy_eval "${OUT_DIR}/privacy_leakage_eval_${ROME_RUN_NAME}_full.json" \
  --pre_public_eval "${PRE_ART_DIR}/public_retain_eval_merged_v2.json" \
  --post_public_eval "${OUT_DIR}/public_retain_eval_${ROME_RUN_NAME}.json" \
  --output_path "$SUMMARY_JSON"

run_step package_artifacts \
  bash -lc "cp '$REQUESTS_JSON' '$ART_DIR/' && \
    cp '${OUT_DIR}/${ROME_RUN_NAME}_subset_dataset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${ROME_RUN_NAME}_case_ids.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${ROME_RUN_NAME}_edit_metrics.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${ROME_RUN_NAME}_manifest.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${ROME_RUN_NAME}_run.log' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${ROME_RUN_NAME}_subset.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${ROME_RUN_NAME}_subset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${ROME_RUN_NAME}_full.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${ROME_RUN_NAME}_full.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_predictions_${ROME_RUN_NAME}.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_retain_eval_${ROME_RUN_NAME}.json' '$ART_DIR/' && \
    cp '$SUMMARY_JSON' '$ART_DIR/' && \
    cp '${DATA_DIR}/synthetic_privacy_dataset.json' '$ART_DIR/' && \
    cp '${PRE_ART_DIR}/privacy_leakage_eval_merged_v2.json' '$ART_DIR/' && \
    cp '${PRE_ART_DIR}/public_retain_eval_merged_v2.json' '$ART_DIR/' && \
    cp '${LOG_DIR}'/*.log '${ART_DIR}/logs/'"

write_status "done" "complete"
touch "$DONE_FILE"
echo "===== DONE ====="
echo "run_name: ${RUN_NAME}"
echo "artifact_dir: ${ART_DIR}"
echo "status_file: ${STATUS_FILE}"
echo "done_file: ${DONE_FILE}"
