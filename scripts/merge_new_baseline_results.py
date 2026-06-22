import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge synthetic and public baseline result summaries.")
    parser.add_argument("--output_dir", default="artifacts/final_comparison_20260622", type=str)
    parser.add_argument("--public_root", default="artifacts/public_benchmarks_20260622", type=str)
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def synthetic_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    candidates = [
        ("Prompt Refusal", Path("artifacts/run_20260622_v2_prompt_refusal/v2_prompt_refusal_summary.json")),
        ("LoRA/SFT Sanitization", Path("artifacts/run_20260622_v2_lora_sanitization/v2_lora_sanitization_summary.json")),
    ]
    for name, path in candidates:
        payload = load_json(path)
        if not payload:
            rows.append({"method": name, "status": "missing", "path": str(path)})
            continue
        row = payload.get("comparison_row") or {}
        row.update({"method": name, "status": "available", "path": str(path)})
        rows.append(row)
    return rows


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    public_json = load_json(Path(args.public_root) / "public_editing_comparison.json") or {"rows": []}
    syn_rows = synthetic_rows()
    write_csv(output_dir / "synthetic_privacy_comparison_with_new_baselines.csv", syn_rows)
    write_csv(output_dir / "public_editing_baseline_comparison.csv", public_json.get("rows", []))
    matrix = [
        "# Public Benchmark Method Matrix",
        "",
        "该文件汇总公开 benchmark baseline 的可用结果。CounterFact/zsRE 与 synthetic privacy 指标分开报告。",
        "",
    ]
    for row in public_json.get("rows", []):
        matrix.append(f"- {row.get('dataset')} / {row.get('model')} / {row.get('method')}: {row.get('status')}")
    (output_dir / "public_benchmark_method_matrix.md").write_text("\n".join(matrix) + "\n", encoding="utf-8")
    summary = [
        "# Paper Ready Result Summary",
        "",
        "## Synthetic Privacy",
        "",
    ]
    for row in syn_rows:
        summary.append(f"- {row.get('method')}: {row.get('status')}")
    summary.extend(["", "## Public Editing", ""])
    for row in public_json.get("rows", []):
        summary.append(f"- {row.get('dataset')} / {row.get('model')} / {row.get('method')}: {row.get('status')}")
    (output_dir / "PAPER_READY_RESULT_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"output_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
