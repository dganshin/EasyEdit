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
HPARAMS_PATH="${HPARAMS_PATH:-hparams/ROME/qwen2.5-7b.yaml}"
ROUND1_REQUESTS_JSON="${ROUND1_REQUESTS_JSON:-artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json}"
DIRECT_PRIVATE_EVAL="${DIRECT_PRIVATE_EVAL:-artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json}"
DIRECT_PUBLIC_EVAL="${DIRECT_PUBLIC_EVAL:-artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json}"
OUT_ROOT="${OUT_ROOT:-artifacts/run_20260623_cape_anchor_rescue}"
FINAL_DIR="${FINAL_DIR:-artifacts/final_comparison_20260623_urgent}"
DEVICE="${DEVICE:-0}"
BATCH_SIZE="${BATCH_SIZE:-16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32}"
STREAM_LOGS="${STREAM_LOGS:-1}"
CONFIGS="${CONFIGS:-PACE_LITE_B20_K0:20:1:0,CAPE_ANCHOR_B20_K1:20:1:1,CAPE_ANCHOR_B20_K2:20:1:2}"

mkdir -p "$OUT_ROOT" "$FINAL_DIR"

RESULTS_CSV="${FINAL_DIR}/cape_anchor_rescue_results.csv"
FAIL_CSV="${FINAL_DIR}/cape_anchor_failure_matrix.csv"
REPORT_MD="${FINAL_DIR}/CAPE_ANCHOR_RESCUE_REPORT.md"

echo "config,status,private_value_contains,private_regex,sensitive_pattern,private_refusal,public_contains,public_exact,summary_path,error" > "$RESULTS_CSV"
echo "config,status,error,log_path" > "$FAIL_CSV"

append_csv_row() {
  local csv_path="$1"
  shift
  python3 - "$csv_path" "$@" <<'PY'
import csv
import sys

path = sys.argv[1]
row = sys.argv[2:]
with open(path, "a", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerow(row)
PY
}

require_file() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "[FAIL] missing required path: $path"
    exit 1
  fi
}

require_file "$DATASET"
require_file "$ROUND1_REQUESTS_JSON"
require_file "$DIRECT_PRIVATE_EVAL"
require_file "$DIRECT_PUBLIC_EVAL"
require_file "$HPARAMS_PATH"
if [[ ! -d "$MODEL_PATH" ]]; then
  echo "[FAIL] missing model dir: $MODEL_PATH"
  exit 1
fi

python3 -m py_compile scripts/build_cape_anchor_requests.py scripts/run_privacy_refusal_edit.py

IFS=',' read -ra CFG_LIST <<< "$CONFIGS"
for cfg in "${CFG_LIST[@]}"; do
  IFS=':' read -r name num_subjects privacy_per_subject anchors_per_subject <<< "$cfg"
  [[ -n "${name:-}" ]] || continue
  cfg_dir="${OUT_ROOT}/${name}"
  log_path="${cfg_dir}/run.log"
  summary_path="${cfg_dir}/summary.json"
  mkdir -p "$cfg_dir"

  if [[ -f "$summary_path" ]]; then
    status="$(python3 - "$summary_path" <<'PY'
import json, sys
print((json.load(open(sys.argv[1], encoding="utf-8")).get("status") or "").lower())
PY
)"
    if [[ "$status" == "ok" ]]; then
      echo "[SKIP] ${name}: summary status=ok"
      continue
    fi
  fi

  echo "[STEP] CAPE-Anchor ${name}"
  set +e
  {
    python3 scripts/build_cape_anchor_requests.py \
      --dataset "$DATASET" \
      --private_eval "$DIRECT_PRIVATE_EVAL" \
      --output_dir "$cfg_dir" \
      --num_subjects "$num_subjects" \
      --privacy_per_subject "$privacy_per_subject" \
      --anchors_per_subject "$anchors_per_subject" \
      --config_name "$name"

    python3 scripts/run_privacy_refusal_edit.py \
      --method ROME \
      --dataset "$DATASET" \
      --model_path "$MODEL_PATH" \
      --hparams "$HPARAMS_PATH" \
      --device "$DEVICE" \
      --output_dir "$cfg_dir" \
      --requests_path "$ROUND1_REQUESTS_JSON" \
      --append_requests_path "${cfg_dir}/requests_union.json" \
      --run_name "$name" \
      --batch_size "$BATCH_SIZE" \
      --max_new_tokens "$MAX_NEW_TOKENS" \
      --full_private_eval \
      --eval_public \
      --disable_fluency_eval

    python3 - "$cfg_dir" "$name" "$summary_path" <<'PY'
import json, sys
from pathlib import Path

cfg_dir = Path(sys.argv[1])
name = sys.argv[2]
summary_path = Path(sys.argv[3])

def load(path):
    return json.load(open(path, encoding="utf-8")) if path.exists() else {}

priv = load(cfg_dir / f"privacy_leakage_eval_{name}_full.json").get("overall", {})
pub = load(cfg_dir / f"public_retain_eval_{name}.json").get("overall", {})
sel = load(cfg_dir / "cape_anchor_selection_report.json")
summary = {
    "status": "ok",
    "config": name,
    "selection": sel,
    "private_value_contains": priv.get("target_exact_leak_rate"),
    "private_regex": priv.get("target_regex_leak_rate"),
    "sensitive_pattern": priv.get("sensitive_pattern_rate"),
    "private_refusal": priv.get("safe_refusal_rate"),
    "public_contains": pub.get("contains_match_rate"),
    "public_exact": pub.get("exact_match_rate"),
}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
PY
  } > "$log_path" 2>&1
  code=$?
  set -e
  if [[ "$STREAM_LOGS" == "1" ]]; then
    tail -n 80 "$log_path" || true
  fi
  if [[ "$code" == "0" ]]; then
    row="$(python3 - "$summary_path" <<'PY'
import csv, io, json, sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
row=[d.get("config"), d.get("status"), d.get("private_value_contains"), d.get("private_regex"), d.get("sensitive_pattern"), d.get("private_refusal"), d.get("public_contains"), d.get("public_exact"), sys.argv[1], ""]
buf=io.StringIO()
csv.writer(buf).writerow(row)
print(buf.getvalue().strip())
PY
)"
    echo "$row" >> "$RESULTS_CSV"
    echo "[OK] ${name}"
  else
    err="$(tail -n 40 "$log_path" | tr '\n' ' ')"
    python3 - "$summary_path" "$name" "$err" <<'PY'
import json, sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({"status":"failed","config":sys.argv[2],"error":sys.argv[3]}, ensure_ascii=False, indent=2), encoding="utf-8")
PY
    append_csv_row "$FAIL_CSV" "$name" "failed" "$err" "$log_path"
    append_csv_row "$RESULTS_CSV" "$name" "failed" "" "" "" "" "" "" "$summary_path" "$err"
    echo "[FAIL] ${name}; continuing"
  fi
done

cat > "$REPORT_MD" <<EOF
# CAPE-Anchor Rescue Report

- output_root: \`${OUT_ROOT}\`
- results_csv: \`${RESULTS_CSV}\`
- failure_matrix: \`${FAIL_CSV}\`

This limited rescue run compares PACE-lite K0 with CAPE-Anchor K1/K2. It does not modify EasyEdit/ROME internals. The intended question is whether explicit public anchor requests reduce public refusal / improve public contains while keeping private value contains below ROME direct-only.
EOF

echo "results_csv: $RESULTS_CSV"
echo "failure_matrix: $FAIL_CSV"
echo "report: $REPORT_MD"
