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

RUN_DATE="${RUN_DATE:-20260622}"
RUN_TAG="${RUN_TAG:-v2_cape_b1_tau05}"
RUN_NAME="run_${RUN_DATE}_${RUN_TAG}"
CAPE_RUN_NAME="${CAPE_RUN_NAME:-${RUN_TAG}}"

DATA_DIR="${DATA_DIR:-artifacts/synthetic_privacy_data_v2}"
PRE_ART_DIR="${PRE_ART_DIR:-artifacts/run_20260615_v2_lora_mlp_only}"
DIRECT_ART_DIR="${DIRECT_ART_DIR:-artifacts/run_20260615_v2_rome_direct}"
OUT_DIR="${OUT_DIR:-/root/autodl-tmp/outputs/easyedit/${RUN_TAG}}"
LOG_DIR="${OUT_DIR}/logs"
ART_DIR="${ART_DIR:-artifacts/${RUN_NAME}}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged}"
HPARAMS_PATH="${HPARAMS_PATH:-hparams/ROME/qwen2.5-7b.yaml}"
DEVICE="${DEVICE:-0}"

TAU="${TAU:-0.5}"
MAX_REQUESTS_PER_PERSON="${MAX_REQUESTS_PER_PERSON:-1}"
MAX_TOTAL_REQUESTS="${MAX_TOTAL_REQUESTS:-}"
CAPE_SCOPE="${CAPE_SCOPE:-all}"
CANDIDATE_SOURCE="${CANDIDATE_SOURCE:-all}"
REQUEST_PROMPT_MODE="${REQUEST_PROMPT_MODE:-source}"
ATTACK_PRIORITY="${ATTACK_PRIORITY:-completion,context,roleplay,paraphrase,direct}"
TARGET_NEW="${TARGET_NEW:-I cannot provide private information.}"
GEN_BATCH_SIZE="${GEN_BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"

STREAM_LOGS="${STREAM_LOGS:-0}"
STATUS_FILE="${STATUS_FILE:-${OUT_DIR}/pipeline_status.txt}"
DONE_FILE="${DONE_FILE:-${OUT_DIR}/PIPELINE_DONE}"
TOTAL_STEPS=4
CURRENT_STEP=0

ROUND1_REQUESTS_JSON="${ROUND1_REQUESTS_JSON:-${DIRECT_ART_DIR}/v2_rome_direct_requests.json}"
DIRECT_FULL_PRIVACY_EVAL="${DIRECT_FULL_PRIVACY_EVAL:-${DIRECT_ART_DIR}/privacy_leakage_eval_v2_rome_direct_full.json}"
DIRECT_PUBLIC_EVAL="${DIRECT_PUBLIC_EVAL:-${DIRECT_ART_DIR}/public_retain_eval_v2_rome_direct.json}"

ROUND2_REQUESTS_JSON="${OUT_DIR}/${CAPE_RUN_NAME}_round2_requests.json"
SELECTION_REPORT_JSON="${OUT_DIR}/${CAPE_RUN_NAME}_selection_report.json"
SELECTION_REPORT_MD="${OUT_DIR}/${CAPE_RUN_NAME}_selection_report.md"
CAPE_SUMMARY_JSON="${OUT_DIR}/${CAPE_RUN_NAME}_summary.json"

mkdir -p "$OUT_DIR" "$LOG_DIR" "$ART_DIR" "$ART_DIR/logs"
rm -f "$DONE_FILE"

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

run_step_with_heartbeat() {
  local name="$1"
  shift
  local heartbeat_interval="${HEARTBEAT_INTERVAL_SEC:-60}"
  CURRENT_STEP=$((CURRENT_STEP + 1))
  print_progress "$name"
  write_status "running" "$name"
  echo "[INFO] ${name} may stay quiet for a while during sequential edit; heartbeat every ${heartbeat_interval}s"
  "$@" > "${LOG_DIR}/${name}.log" 2>&1 &
  local cmd_pid=$!
  local start_ts
  start_ts=$(date +%s)
  while kill -0 "$cmd_pid" 2>/dev/null; do
    if [[ "$STREAM_LOGS" == "1" ]]; then
      tail -n 5 "${LOG_DIR}/${name}.log" 2>/dev/null || true
    fi
    sleep "$heartbeat_interval"
    if kill -0 "$cmd_pid" 2>/dev/null; then
      local now_ts
      now_ts=$(date +%s)
      local elapsed=$((now_ts - start_ts))
      echo "[HEARTBEAT] ${name} still running, elapsed=${elapsed}s"
    fi
  done
  wait "$cmd_pid" || {
    echo "[FAIL] $name"
    tail -n 120 "${LOG_DIR}/${name}.log" || true
    exit 1
  }
  if [[ "$STREAM_LOGS" == "1" ]]; then
    tail -n 40 "${LOG_DIR}/${name}.log" || true
  fi
  echo "[OK]  $name"
}

write_status "starting" "bootstrap"

run_step build_cape_requests \
  python scripts/build_cape_reedit_requests.py \
  --private_eval "$DIRECT_FULL_PRIVACY_EVAL" \
  --public_eval "$DIRECT_PUBLIC_EVAL" \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --base_requests "$ROUND1_REQUESTS_JSON" \
  --output_path "$ROUND2_REQUESTS_JSON" \
  --selection_report_json "$SELECTION_REPORT_JSON" \
  --selection_report_md "$SELECTION_REPORT_MD" \
  --target_new "$TARGET_NEW" \
  --tau "$TAU" \
  --max_requests_per_person "$MAX_REQUESTS_PER_PERSON" \
  ${MAX_TOTAL_REQUESTS:+--max_total_requests "$MAX_TOTAL_REQUESTS"} \
  --scope "$CAPE_SCOPE" \
  --candidate_source "$CANDIDATE_SOURCE" \
  --request_prompt_mode "$REQUEST_PROMPT_MODE" \
  --attack_priority "$ATTACK_PRIORITY"

run_step_with_heartbeat run_cape_round2 \
  python scripts/run_privacy_refusal_edit.py \
  --method ROME \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --model_path "$MODEL_PATH" \
  --hparams "$HPARAMS_PATH" \
  --device "$DEVICE" \
  --output_dir "$OUT_DIR" \
  --requests_path "$ROUND1_REQUESTS_JSON" \
  --append_requests_path "$ROUND2_REQUESTS_JSON" \
  --run_name "$CAPE_RUN_NAME" \
  --batch_size "$GEN_BATCH_SIZE" \
  --max_new_tokens "$MAX_NEW_TOKENS" \
  --full_private_eval \
  --eval_public \
  --disable_fluency_eval

run_step summarize_results \
  python scripts/summarize_v2_pace_run.py \
  --pre_privacy_eval "${PRE_ART_DIR}/privacy_leakage_eval_merged_v2.json" \
  --pre_public_eval "${PRE_ART_DIR}/public_retain_eval_merged_v2.json" \
  --direct_privacy_eval "$DIRECT_FULL_PRIVACY_EVAL" \
  --direct_public_eval "$DIRECT_PUBLIC_EVAL" \
  --pace_privacy_eval "${OUT_DIR}/privacy_leakage_eval_${CAPE_RUN_NAME}_full.json" \
  --pace_public_eval "${OUT_DIR}/public_retain_eval_${CAPE_RUN_NAME}.json" \
  --direct_requests_json "$ROUND1_REQUESTS_JSON" \
  --round2_requests_json "$ROUND2_REQUESTS_JSON" \
  --combined_requests_json "${OUT_DIR}/${CAPE_RUN_NAME}_requests.json" \
  --output_path "$CAPE_SUMMARY_JSON"

run_step package_artifacts \
  bash -lc "cp '$ROUND2_REQUESTS_JSON' '$ART_DIR/' && \
    cp '$SELECTION_REPORT_JSON' '$ART_DIR/' && \
    cp '$SELECTION_REPORT_MD' '$ART_DIR/' && \
    cp '$ROUND1_REQUESTS_JSON' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_requests.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_subset_dataset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_case_ids.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_edit_metrics.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_manifest.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${CAPE_RUN_NAME}_run.log' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${CAPE_RUN_NAME}_subset.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${CAPE_RUN_NAME}_subset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${CAPE_RUN_NAME}_full.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${CAPE_RUN_NAME}_full.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_predictions_${CAPE_RUN_NAME}.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_retain_eval_${CAPE_RUN_NAME}.json' '$ART_DIR/' && \
    cp '$CAPE_SUMMARY_JSON' '$ART_DIR/' && \
    cp '${PRE_ART_DIR}/privacy_leakage_eval_merged_v2.json' '$ART_DIR/' && \
    cp '${PRE_ART_DIR}/public_retain_eval_merged_v2.json' '$ART_DIR/' && \
    cp '$DIRECT_FULL_PRIVACY_EVAL' '$ART_DIR/' && \
    cp '$DIRECT_PUBLIC_EVAL' '$ART_DIR/' && \
    cp '${LOG_DIR}'/*.log '${ART_DIR}/logs/'"

write_status "done" "complete"
touch "$DONE_FILE"
echo "===== DONE ====="
echo "run_name: ${RUN_NAME}"
echo "artifact_dir: ${ART_DIR}"
echo "status_file: ${STATUS_FILE}"
echo "done_file: ${DONE_FILE}"
