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

RUN_SYNTH_EXTRA="${RUN_SYNTH_EXTRA:-1}"
RUN_CAPE_ANCHOR="${RUN_CAPE_ANCHOR:-1}"
RUN_PUBLIC_WRAPPERS="${RUN_PUBLIC_WRAPPERS:-auto}"
RUN_FIGURES="${RUN_FIGURES:-1}"
RUN_CLAIM_DECISION="${RUN_CLAIM_DECISION:-1}"
STREAM_LOGS="${STREAM_LOGS:-1}"
FINAL_DIR="${FINAL_DIR:-artifacts/final_comparison_20260623_urgent}"
PUBLIC_ROOT="${PUBLIC_ROOT:-artifacts/public_benchmarks_20260623_200}"
STATUS_FILE="${FINAL_DIR}/URGENT_MAIN_STATUS.txt"
FAIL_CSV="${FINAL_DIR}/urgent_main_failure_matrix.csv"

mkdir -p "$FINAL_DIR"
echo "phase,status,log_path,error" > "$FAIL_CSV"

write_status() {
  local state="$1"
  local phase="$2"
  {
    echo "state=${state}"
    echo "phase=${phase}"
    echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
    echo "run_synth_extra=${RUN_SYNTH_EXTRA}"
    echo "run_cape_anchor=${RUN_CAPE_ANCHOR}"
    echo "run_public_wrappers=${RUN_PUBLIC_WRAPPERS}"
    echo "run_figures=${RUN_FIGURES}"
    echo "run_claim_decision=${RUN_CLAIM_DECISION}"
  } > "$STATUS_FILE"
}

append_failure() {
  local phase="$1"
  local status="$2"
  local log_path="$3"
  local error="${4:-}"
  python3 - "$FAIL_CSV" "$phase" "$status" "$log_path" "$error" <<'PY'
import csv
import sys

path, phase, status, log_path, error = sys.argv[1:]
with open(path, "a", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerow([phase, status, log_path, error])
PY
}

run_phase() {
  local phase="$1"
  shift
  local log_path="${FINAL_DIR}/${phase}.log"
  echo "[STEP] ${phase}"
  write_status "running" "$phase"
  set +e
  if [[ "$STREAM_LOGS" == "1" ]]; then
    "$@" 2>&1 | tee "$log_path"
    local code=${PIPESTATUS[0]}
  else
    "$@" > "$log_path" 2>&1
    local code=$?
  fi
  set -e
  if [[ "$code" == "0" ]]; then
    append_failure "$phase" "ok" "$log_path" ""
    echo "[OK] ${phase}"
    return 0
  fi
  local err
  err="$(tail -n 40 "$log_path" | tr '\n' ' ')"
  append_failure "$phase" "failed" "$log_path" "$err"
  echo "[FAIL] ${phase}; continuing where safe"
  return 1
}

echo "[STEP] phase0_env_check"
write_status "running" "phase0_env_check"
{
  echo "# Urgent Main Experiment Environment Check"
  echo
  echo "- root: \`${ROOT_DIR}\`"
  echo "- timestamp: \`$(date '+%Y-%m-%d %H:%M:%S')\`"
  echo "- python: \`$(command -v python3 || true)\`"
  echo "- conda env: \`${CONDA_DEFAULT_ENV:-unknown}\`"
  echo
  echo "## GPU"
  echo '```text'
  nvidia-smi || true
  echo '```'
  echo
  echo "## Required Paths"
  for p in \
    "artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json" \
    "artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json" \
    "artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json" \
    "artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json" \
    "/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged"; do
    if [[ -e "$p" ]]; then
      echo "- OK: \`${p}\`"
    else
      echo "- MISSING: \`${p}\`"
    fi
  done
} > "${FINAL_DIR}/ENV_CHECK_REPORT.md"

if ! python3 -m py_compile \
  scripts/run_privacy_refusal_edit.py \
  scripts/build_cape_anchor_requests.py \
  scripts/build_paper_ready_figures_and_tables.py \
  scripts/decide_method_claim_level.py; then
  echo "[FAIL] py_compile failed; stop before GPU work"
  write_status "failed" "phase0_py_compile"
  exit 1
fi

if [[ "$RUN_SYNTH_EXTRA" == "1" ]]; then
  run_phase "phase1_synthetic_extra_editors" bash scripts/run_synthetic_privacy_extra_editors.sh || true
else
  append_failure "phase1_synthetic_extra_editors" "skipped" "" "RUN_SYNTH_EXTRA!=1"
fi

if [[ "$RUN_CAPE_ANCHOR" == "1" ]]; then
  run_phase "phase2_cape_anchor_rescue" bash scripts/run_cape_anchor_rescue.sh || true
else
  append_failure "phase2_cape_anchor_rescue" "skipped" "" "RUN_CAPE_ANCHOR!=1"
fi

if [[ "$RUN_PUBLIC_WRAPPERS" == "1" || "$RUN_PUBLIC_WRAPPERS" == "auto" ]]; then
  if find "$PUBLIC_ROOT" -path "*/ROME/per_case_results.jsonl" -type f 2>/dev/null | grep -q .; then
    run_phase "phase3_public_wrappers_only" bash scripts/run_missing_public_wrappers.sh || true
  else
    echo "[SKIP] phase3_public_wrappers_only: no public ROME per_case_results.jsonl under ${PUBLIC_ROOT}"
    append_failure "phase3_public_wrappers_only" "skipped" "" "no public ROME per_case_results.jsonl"
  fi
else
  append_failure "phase3_public_wrappers_only" "skipped" "" "RUN_PUBLIC_WRAPPERS=0"
fi

if [[ "$RUN_FIGURES" == "1" ]]; then
  run_phase "phase4_paper_figures_tables" python3 scripts/build_paper_ready_figures_and_tables.py \
    --output_dir "$FINAL_DIR" \
    --public_root "$PUBLIC_ROOT" || true
else
  append_failure "phase4_paper_figures_tables" "skipped" "" "RUN_FIGURES!=1"
fi

if [[ "$RUN_CLAIM_DECISION" == "1" ]]; then
  run_phase "phase5_claim_decision" python3 scripts/decide_method_claim_level.py \
    --output_dir "$FINAL_DIR" || true
else
  append_failure "phase5_claim_decision" "skipped" "" "RUN_CLAIM_DECISION!=1"
fi

write_status "done" "complete"
echo "===== URGENT MAIN EXPERIMENTS DONE ====="
echo "final_dir: ${FINAL_DIR}"
echo "status_file: ${STATUS_FILE}"
echo "failure_matrix: ${FAIL_CSV}"
