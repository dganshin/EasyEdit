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
RUN_TAG="${RUN_TAG:-v2_lora_mlp_only}"
RUN_NAME="run_${RUN_DATE}_${RUN_TAG}"

DATA_DIR="${DATA_DIR:-artifacts/synthetic_privacy_data_v2}"
OUT_DIR="${OUT_DIR:-/root/autodl-tmp/outputs/easyedit/${RUN_TAG}}"
LOG_DIR="${OUT_DIR}/logs"
ART_DIR="${ART_DIR:-artifacts/${RUN_NAME}}"
BASE_MODEL_PATH="${BASE_MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B}"
MERGED_MODEL_DIR="${MERGED_MODEL_DIR:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-${RUN_TAG}-merged}"
DEVICE="${DEVICE:-0}"

NUM_PEOPLE="${NUM_PEOPLE:-100}"
PRIVATE_PER_PERSON="${PRIVATE_PER_PERSON:-2}"
PUBLIC_PER_PERSON="${PUBLIC_PER_PERSON:-4}"
SAME_RELATION_PUBLIC_PER_PERSON="${SAME_RELATION_PUBLIC_PER_PERSON:-4}"
NUM_GENERAL_KNOWLEDGE="${NUM_GENERAL_KNOWLEDGE:-40}"
NUM_ATTACK_TEMPLATES_PER_TYPE="${NUM_ATTACK_TEMPLATES_PER_TYPE:-3}"
NUM_PUBLIC_TEMPLATES_PER_CASE="${NUM_PUBLIC_TEMPLATES_PER_CASE:-3}"

LORA_SCOPE="${LORA_SCOPE:-mlp_only}"
LORA_RANK="${LORA_RANK:-16}"
LORA_NUM_STEPS="${LORA_NUM_STEPS:-3}"
LORA_LR="${LORA_LR:-5e-4}"
LORA_MAX_LENGTH="${LORA_MAX_LENGTH:-128}"
TRAIN_BATCH_CANDIDATES="${TRAIN_BATCH_CANDIDATES:-24 20 16 12 8}"
GEN_BATCH_SIZE="${GEN_BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
STREAM_LOGS="${STREAM_LOGS:-0}"
STATUS_FILE="${STATUS_FILE:-${OUT_DIR}/pipeline_status.txt}"
DONE_FILE="${DONE_FILE:-${OUT_DIR}/PIPELINE_DONE}"
PRIVATE_REPEAT="${PRIVATE_REPEAT:-4}"
MAX_PUBLIC_TO_PRIVATE_RATIO="${MAX_PUBLIC_TO_PRIVATE_RATIO:-2}"
SHUFFLE_TRAIN="${SHUFFLE_TRAIN:-1}"
TOTAL_STEPS=7
CURRENT_STEP=0

mkdir -p "$DATA_DIR" "$OUT_DIR" "$LOG_DIR" "$ART_DIR" "$ART_DIR/logs"
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

run_train_with_fallback() {
  local train_data="$1"
  local batch_size
  local shuffle_args=()
  if [[ "$SHUFFLE_TRAIN" == "1" ]]; then
    shuffle_args+=(--shuffle)
  fi
  CURRENT_STEP=$((CURRENT_STEP + 1))
  print_progress "train_lora"
  write_status "running" "train_lora"
  for batch_size in ${TRAIN_BATCH_CANDIDATES}; do
    echo "[RUN] train_lora_bs${batch_size}"
    if [[ "$STREAM_LOGS" == "1" ]]; then
      if python scripts/train_lora_privacy_injection.py \
        --train_data "$train_data" \
        --model_path "$BASE_MODEL_PATH" \
        --output_dir "${OUT_DIR}/adapter" \
        --device "$DEVICE" \
        --lora_scope "$LORA_SCOPE" \
        --batch_size "$batch_size" \
        --rank "$LORA_RANK" \
        --num_steps "$LORA_NUM_STEPS" \
        --lr "$LORA_LR" \
        --max_length "$LORA_MAX_LENGTH" \
        "${shuffle_args[@]}" \
        --disable_gradient_checkpointing \
        2>&1 | tee "${LOG_DIR}/train_lora_bs${batch_size}.log"; then
        echo "[OK]  train_lora_bs${batch_size}"
        echo "$batch_size" > "${OUT_DIR}/resolved_train_batch_size.txt"
        return 0
      fi
    elif python scripts/train_lora_privacy_injection.py \
      --train_data "$train_data" \
      --model_path "$BASE_MODEL_PATH" \
      --output_dir "${OUT_DIR}/adapter" \
      --device "$DEVICE" \
      --lora_scope "$LORA_SCOPE" \
      --batch_size "$batch_size" \
      --rank "$LORA_RANK" \
      --num_steps "$LORA_NUM_STEPS" \
      --lr "$LORA_LR" \
      --max_length "$LORA_MAX_LENGTH" \
      "${shuffle_args[@]}" \
      --disable_gradient_checkpointing \
      > "${LOG_DIR}/train_lora_bs${batch_size}.log" 2>&1; then
      echo "[OK]  train_lora_bs${batch_size}"
      echo "$batch_size" > "${OUT_DIR}/resolved_train_batch_size.txt"
      return 0
    fi
    echo "[WARN] batch_size=${batch_size} failed, trying smaller one"
    tail -n 40 "${LOG_DIR}/train_lora_bs${batch_size}.log" || true
  done
  echo "[FAIL] all LoRA batch size candidates failed"
  exit 1
}

write_status "starting" "bootstrap"

run_step generate_dataset \
  python scripts/generate_synthetic_privacy_data.py \
  --output_dir "$DATA_DIR" \
  --num_people "$NUM_PEOPLE" \
  --private_per_person "$PRIVATE_PER_PERSON" \
  --public_per_person "$PUBLIC_PER_PERSON" \
  --same_relation_public_per_person "$SAME_RELATION_PUBLIC_PER_PERSON" \
  --num_general_knowledge "$NUM_GENERAL_KNOWLEDGE" \
  --num_attack_templates_per_type "$NUM_ATTACK_TEMPLATES_PER_TYPE" \
  --num_public_templates_per_case "$NUM_PUBLIC_TEMPLATES_PER_CASE"

run_step audit_dataset \
  python scripts/audit_synthetic_privacy_data.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --output_path "${DATA_DIR}/audit_summary.json"

run_step build_lora_train_data \
  python scripts/build_lora_privacy_train_data.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --output_dir "$DATA_DIR" \
  --private_repeat "$PRIVATE_REPEAT" \
  --max_public_to_private_ratio "$MAX_PUBLIC_TO_PRIVATE_RATIO"

run_train_with_fallback "${DATA_DIR}/lora_privacy_train.jsonl"

run_step merge_lora \
  python scripts/merge_lora_privacy_model.py \
  --model_path "$BASE_MODEL_PATH" \
  --lora_adapter_path "${OUT_DIR}/adapter" \
  --output_dir "$MERGED_MODEL_DIR"

run_step generate_private \
  python scripts/run_privacy_generation.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --model_path "$MERGED_MODEL_DIR" \
  --device "$DEVICE" \
  --mode private \
  --output_path "${OUT_DIR}/privacy_predictions_merged_v2.jsonl" \
  --batch_size "$GEN_BATCH_SIZE" \
  --max_new_tokens "$MAX_NEW_TOKENS" \
  --attack_types direct paraphrase completion roleplay context

run_step eval_private \
  python scripts/evaluate_privacy_leakage.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --predictions "${OUT_DIR}/privacy_predictions_merged_v2.jsonl" \
  --output_path "${OUT_DIR}/privacy_leakage_eval_merged_v2.json" \
  --mode full

run_step generate_public \
  python scripts/run_privacy_generation.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --model_path "$MERGED_MODEL_DIR" \
  --device "$DEVICE" \
  --mode public \
  --output_path "${OUT_DIR}/public_predictions_merged_v2.jsonl" \
  --batch_size "$GEN_BATCH_SIZE" \
  --max_new_tokens "$MAX_NEW_TOKENS"

run_step eval_public \
  python scripts/evaluate_public_retain.py \
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json" \
  --predictions "${OUT_DIR}/public_predictions_merged_v2.jsonl" \
  --output_path "${OUT_DIR}/public_retain_eval_merged_v2.json"

cp "${DATA_DIR}/synthetic_privacy_dataset.json" "$ART_DIR/"
cp "${DATA_DIR}/synthetic_privacy_cases.jsonl" "$ART_DIR/"
cp "${DATA_DIR}/audit_summary.json" "$ART_DIR/"
cp "${DATA_DIR}/lora_privacy_train_dataset.json" "$ART_DIR/"
cp "${DATA_DIR}/lora_privacy_train.jsonl" "$ART_DIR/"
cp "${OUT_DIR}/adapter/training_manifest.json" "$ART_DIR/"
cp "${OUT_DIR}/resolved_train_batch_size.txt" "$ART_DIR/" || true
cp "${MERGED_MODEL_DIR}/merge_manifest.json" "$ART_DIR/"
cp "${OUT_DIR}/privacy_predictions_merged_v2.jsonl" "$ART_DIR/"
cp "${OUT_DIR}/privacy_leakage_eval_merged_v2.json" "$ART_DIR/"
cp "${OUT_DIR}/public_predictions_merged_v2.jsonl" "$ART_DIR/"
cp "${OUT_DIR}/public_retain_eval_merged_v2.json" "$ART_DIR/"
cp "${LOG_DIR}"/*.log "${ART_DIR}/logs/"

write_status "done" "complete"
touch "$DONE_FILE"
echo "===== DONE ====="
echo "run_name: ${RUN_NAME}"
echo "artifact_dir: ${ART_DIR}"
echo "merged_model_dir: ${MERGED_MODEL_DIR}"
echo "status_file: ${STATUS_FILE}"
echo "done_file: ${DONE_FILE}"
