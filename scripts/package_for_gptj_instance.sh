#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT="/tmp/easyedit_gptj_instance_bundle.tar.gz"
TMP_DIR="$(mktemp -d /tmp/easyedit_gptj_bundle.XXXXXX)"
TARGET_DIR="${TMP_DIR}/projects/EasyEdit"
mkdir -p "$TARGET_DIR"

git archive --format=tar HEAD | tar -x -C "$TARGET_DIR"

mkdir -p "$TARGET_DIR/artifacts/public_benchmarks_20260622"
cp artifacts/public_benchmarks_20260622/counterfact_500.json "$TARGET_DIR/artifacts/public_benchmarks_20260622/"
cp artifacts/public_benchmarks_20260622/zsre_500.json "$TARGET_DIR/artifacts/public_benchmarks_20260622/"
cp artifacts/public_benchmarks_20260622/public_subset_stats.json "$TARGET_DIR/artifacts/public_benchmarks_20260622/" 2>/dev/null || true
cp artifacts/public_benchmarks_20260622/PUBLIC_SUBSET_PREP_REPORT.md "$TARGET_DIR/artifacts/public_benchmarks_20260622/" 2>/dev/null || true

mkdir -p "$TARGET_DIR/docs"
cp docs/GPTJ_INSTANCE_TRANSFER_INSTRUCTIONS.md "$TARGET_DIR/docs/" 2>/dev/null || true
mkdir -p "$TARGET_DIR/artifacts/public_benchmarks_20260622"
cp docs/GPTJ_INSTANCE_TRANSFER_INSTRUCTIONS.md "$TARGET_DIR/artifacts/public_benchmarks_20260622/GPTJ_INSTANCE_TRANSFER_INSTRUCTIONS.md" 2>/dev/null || true

find "$TARGET_DIR" -type d \( -name __pycache__ -o -name .git -o -name logs -o -name outputs -o -name models -o -name checkpoints -o -name wandb \) -prune -exec rm -rf {} +
find "$TARGET_DIR" -type f \( -name "*.bin" -o -name "*.safetensors" -o -name "*.pt" -o -name "*.pth" \) -delete

tar -czf "$OUT" -C "$TMP_DIR" projects
rm -rf "$TMP_DIR"

echo "bundle: $OUT"
du -h "$OUT"
