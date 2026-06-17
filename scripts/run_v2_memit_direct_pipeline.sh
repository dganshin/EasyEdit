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

RUN_DATE="${RUN_DATE:-20260617}"
RUN_TAG="${RUN_TAG:-v2_memit_direct}"
RUN_NAME="run_${RUN_DATE}_${RUN_TAG}"
MEMIT_RUN_NAME="${MEMIT_RUN_NAME:-v2_memit_direct}"

DATA_DIR="${DATA_DIR:-artifacts/synthetic_privacy_data_v2}"
PRE_ART_DIR="${PRE_ART_DIR:-artifacts/run_20260615_v2_lora_mlp_only}"
ROME_ART_DIR="${ROME_ART_DIR:-artifacts/run_20260615_v2_rome_direct}"
OUT_DIR="${OUT_DIR:-/root/autodl-tmp/outputs/easyedit/${RUN_TAG}}"
LOG_DIR="${OUT_DIR}/logs"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged}"
HPARAMS_PATH="${HPARAMS_PATH:-hparams/MEMIT/qwen2.5-7b.yaml}"
DEVICE="${DEVICE:-0}"
REQUESTS_JSON="${REQUESTS_JSON:-${ROME_ART_DIR}/v2_rome_direct_requests.json}"

GEN_BATCH_SIZE="${GEN_BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
DRY_RUN="${DRY_RUN:-1}"
STREAM_LOGS="${STREAM_LOGS:-0}"
ALLOW_DIRTY_GIT="${ALLOW_DIRTY_GIT:-0}"
ALLOW_EXISTING_OUTPUT_DIR="${ALLOW_EXISTING_OUTPUT_DIR:-0}"
ALLOW_MISSING_MODEL="${ALLOW_MISSING_MODEL:-0}"
ALLOW_MISSING_STATS="${ALLOW_MISSING_STATS:-0}"
STATUS_FILE="${STATUS_FILE:-${OUT_DIR}/pipeline_status.txt}"
DONE_FILE="${DONE_FILE:-${OUT_DIR}/PIPELINE_DONE}"
TOTAL_STEPS=3
CURRENT_STEP=0
if [[ -z "${ART_DIR:-}" ]]; then
  if [[ "$DRY_RUN" == "1" ]]; then
    ART_DIR="artifacts/${RUN_NAME}_dryrun"
  else
    ART_DIR="artifacts/${RUN_NAME}"
  fi
fi

if [[ -e "$ART_DIR" && "$ALLOW_EXISTING_OUTPUT_DIR" != "1" ]]; then
  echo "[FAIL] artifact dir already exists: $ART_DIR"
  exit 1
fi
if [[ -e "$OUT_DIR" && "$ALLOW_EXISTING_OUTPUT_DIR" != "1" ]]; then
  echo "[FAIL] output dir already exists: $OUT_DIR"
  exit 1
fi

PREFLIGHT_TMP_JSON="${ART_DIR}.preflight_report.json"
PREFLIGHT_JSON="${ART_DIR}/preflight_report.json"
RUN_MANIFEST_JSON="${ART_DIR}/run_manifest.json"
COMMAND_SH="${ART_DIR}/command.sh"
export RUN_NAME RUN_TAG DRY_RUN MODEL_PATH DATA_DIR REQUESTS_JSON HPARAMS_PATH OUT_DIR ART_DIR DEVICE RUN_DATE STREAM_LOGS
export ALLOW_DIRTY_GIT ALLOW_EXISTING_OUTPUT_DIR ALLOW_MISSING_MODEL ALLOW_MISSING_STATS

preflight_args=(
  python3 scripts/preflight_v2_memit_direct.py
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json"
  --requests "$REQUESTS_JSON"
  --model_path "$MODEL_PATH"
  --hparams "$HPARAMS_PATH"
  --output_dir "$OUT_DIR"
  --artifact_dir "$ART_DIR"
  --json_out "$PREFLIGHT_TMP_JSON"
)
if [[ "$ALLOW_DIRTY_GIT" == "1" ]]; then
  preflight_args+=(--allow_dirty_git)
fi
if [[ "$ALLOW_EXISTING_OUTPUT_DIR" == "1" ]]; then
  preflight_args+=(--allow_existing_output_dir)
fi
if [[ "$ALLOW_MISSING_MODEL" == "1" ]]; then
  preflight_args+=(--allow_missing_model)
fi
if [[ "$ALLOW_MISSING_STATS" == "1" ]]; then
  preflight_args+=(--allow_missing_stats)
fi

"${preflight_args[@]}"

mkdir -p "$ART_DIR" "$ART_DIR/logs"
mv "$PREFLIGHT_TMP_JSON" "$PREFLIGHT_JSON"

memit_cmd=(
  python scripts/run_privacy_refusal_edit.py
  --method MEMIT
  --dataset "${DATA_DIR}/synthetic_privacy_dataset.json"
  --model_path "$MODEL_PATH"
  --hparams "$HPARAMS_PATH"
  --device "$DEVICE"
  --output_dir "$OUT_DIR"
  --requests_path "$REQUESTS_JSON"
  --run_name "$MEMIT_RUN_NAME"
  --batch_size "$GEN_BATCH_SIZE"
  --max_new_tokens "$MAX_NEW_TOKENS"
  --full_private_eval
  --eval_public
  --disable_fluency_eval
)

summarize_cmd=(
  python scripts/summarize_rome_privacy.py
  --pre_privacy_eval "${PRE_ART_DIR}/privacy_leakage_eval_merged_v2.json"
  --post_subset_privacy_eval "${OUT_DIR}/privacy_leakage_eval_${MEMIT_RUN_NAME}_subset.json"
  --post_full_privacy_eval "${OUT_DIR}/privacy_leakage_eval_${MEMIT_RUN_NAME}_full.json"
  --pre_public_eval "${PRE_ART_DIR}/public_retain_eval_merged_v2.json"
  --post_public_eval "${OUT_DIR}/public_retain_eval_${MEMIT_RUN_NAME}.json"
  --output_path "${OUT_DIR}/${MEMIT_RUN_NAME}_summary.json"
)

{
  echo "#!/usr/bin/env bash"
  echo "set -euo pipefail"
  printf '%q ' "${memit_cmd[@]}"
  echo
  printf '%q ' "${summarize_cmd[@]}"
  echo
} > "$COMMAND_SH"
chmod +x "$COMMAND_SH"

python3 - "$RUN_MANIFEST_JSON" "$PREFLIGHT_JSON" "$COMMAND_SH" <<'PY'
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

manifest_path = Path(sys.argv[1])
preflight_path = Path(sys.argv[2])
command_path = Path(sys.argv[3])
preflight = json.loads(preflight_path.read_text(encoding="utf-8"))

def git(args):
    proc = subprocess.run(["git", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout.strip() if proc.returncode == 0 else None

payload = {
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "method": "MEMIT",
    "run_name": os.environ.get("RUN_NAME"),
    "run_tag": os.environ.get("RUN_TAG"),
    "dry_run": os.environ.get("DRY_RUN"),
    "base_model_path": os.environ.get("MODEL_PATH"),
    "dataset_path": f"{os.environ.get('DATA_DIR')}/synthetic_privacy_dataset.json",
    "dataset_sha256": preflight.get("dataset_sha256"),
    "request_path": os.environ.get("REQUESTS_JSON"),
    "request_sha256": preflight.get("requests_sha256"),
    "hparams_path": os.environ.get("HPARAMS_PATH"),
    "output_dir": os.environ.get("OUT_DIR"),
    "artifact_dir": os.environ.get("ART_DIR"),
    "git_commit": git(["rev-parse", "--short", "HEAD"]),
    "git_dirty_status": git(["status", "--short"]),
    "command_file": str(command_path),
    "environment": {
        key: os.environ.get(key)
        for key in [
            "DEVICE",
            "RUN_DATE",
            "RUN_TAG",
            "DRY_RUN",
            "STREAM_LOGS",
            "ALLOW_DIRTY_GIT",
            "ALLOW_EXISTING_OUTPUT_DIR",
            "ALLOW_MISSING_MODEL",
            "ALLOW_MISSING_STATS",
            "HF_HOME",
            "TRANSFORMERS_CACHE",
            "HF_DATASETS_CACHE",
            "NLTK_DATA",
        ]
    },
}
manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if [[ "$DRY_RUN" == "1" ]]; then
  echo "===== DRY RUN ====="
  echo "No model loading, no MEMIT edit, no generation eval."
  echo "Would run:"
  printf '%q ' "${memit_cmd[@]}"
  echo
  printf '%q ' "${summarize_cmd[@]}"
  echo
  echo "artifact_dir: $ART_DIR"
  echo "preflight_report: $PREFLIGHT_JSON"
  echo "run_manifest: $RUN_MANIFEST_JSON"
  echo "command_file: $COMMAND_SH"
  exit 0
fi

mkdir -p "$OUT_DIR" "$LOG_DIR" "$ART_DIR/logs"
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

write_status "starting" "bootstrap"

run_step run_memit_direct "${memit_cmd[@]}"
run_step summarize_results "${summarize_cmd[@]}"

run_step package_artifacts \
  bash -lc "cp '$REQUESTS_JSON' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_subset_dataset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_case_ids.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_edit_metrics.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_manifest.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_run.log' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${MEMIT_RUN_NAME}_subset.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${MEMIT_RUN_NAME}_subset.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_predictions_${MEMIT_RUN_NAME}_full.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/privacy_leakage_eval_${MEMIT_RUN_NAME}_full.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_predictions_${MEMIT_RUN_NAME}.jsonl' '$ART_DIR/' && \
    cp '${OUT_DIR}/public_retain_eval_${MEMIT_RUN_NAME}.json' '$ART_DIR/' && \
    cp '${OUT_DIR}/${MEMIT_RUN_NAME}_summary.json' '$ART_DIR/' && \
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
