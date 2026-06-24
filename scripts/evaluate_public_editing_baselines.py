import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate public editing baseline metrics.")
    parser.add_argument("--root_dir", default="artifacts/public_benchmarks_20260622", type=str)
    parser.add_argument("--output_dir", default="artifacts/public_benchmarks_20260622", type=str)
    return parser.parse_args()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def flatten_numeric(value: Any) -> List[float]:
    if value is None:
        return []
    if isinstance(value, bool):
        return [float(value)]
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, list):
        vals: List[float] = []
        for item in value:
            vals.extend(flatten_numeric(item))
        return vals
    return []


def get_nested(payload: Dict[str, Any], keys: Iterable[str]) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def aggregate_method(method_dir: Path) -> Dict[str, Any]:
    summary = read_json(method_dir / "summary.json") or {"status": "missing"}
    config = read_json(method_dir / "method_config.json") or {}
    status = summary.get("status")
    rows = [] if status == "calibration_needed" else read_jsonl(method_dir / "per_case_results.jsonl")
    rewrite_vals = []
    rephrase_vals = []
    locality_vals = []
    for row in rows:
        post = get_nested(row, ["metrics", "post"]) or {}
        rewrite_vals.extend(flatten_numeric(post.get("rewrite_acc")))
        rephrase_vals.extend(flatten_numeric(post.get("rephrase_acc")))
        locality = post.get("locality") or {}
        if isinstance(locality, dict):
            for value in locality.values():
                if isinstance(value, dict):
                    for key, sub in value.items():
                        if key.endswith("_acc"):
                            locality_vals.extend(flatten_numeric(sub))
    return {
        "dataset": config.get("dataset_name"),
        "model": config.get("model_name"),
        "method": config.get("method") or method_dir.name,
        "status": status,
        "num_cases": summary.get("num_cases") or summary.get("num_cases_attempted") or len(rows),
        "reliability_rewrite_success": mean(rewrite_vals) if rewrite_vals else None,
        "generalization_rephrase_success": mean(rephrase_vals) if rephrase_vals else None,
        "locality_retain_success": mean(locality_vals) if locality_vals else None,
        "elapsed_sec": summary.get("elapsed_sec"),
        "failure_error": summary.get("error"),
        "method_dir": str(method_dir),
    }


def discover_method_dirs(root: Path) -> List[Path]:
    dirs = []
    for summary in root.rglob("summary.json"):
        dirs.append(summary.parent)
    return sorted(set(dirs))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dataset",
        "model",
        "method",
        "status",
        "num_cases",
        "reliability_rewrite_success",
        "generalization_rephrase_success",
        "locality_retain_success",
        "elapsed_sec",
        "failure_error",
        "method_dir",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# Public Editing Baseline Report",
        "",
        "CounterFact 不是 PII 数据集，是公开事实编辑 benchmark；zsRE 不是 PII 数据集，是问答式知识编辑 benchmark。它们用于证明本文实验框架能在公开模型编辑基准上进行多方法比较，不和 synthetic privacy 指标混成同一张表。",
        "",
        "| dataset | model | method | status | cases | rewrite | rephrase | locality | error |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        def fmt(x: Any) -> str:
            return "" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))
        lines.append(
            f"| {fmt(row['dataset'])} | {fmt(row['model'])} | {fmt(row['method'])} | {fmt(row['status'])} | {fmt(row['num_cases'])} | {fmt(row['reliability_rewrite_success'])} | {fmt(row['generalization_rephrase_success'])} | {fmt(row['locality_retain_success'])} | {fmt(row['failure_error'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_matrix(path: Path, rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# Public Benchmark Method Matrix",
        "",
        "| dataset | model | method | status | cases |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('dataset') or ''} | {row.get('model') or ''} | {row.get('method') or ''} | {row.get('status') or ''} | {row.get('num_cases') or ''} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root_dir)
    output_dir = Path(args.output_dir)
    rows = [aggregate_method(path) for path in discover_method_dirs(root)]
    json_path = output_dir / "public_editing_comparison.json"
    csv_path = output_dir / "public_editing_comparison.csv"
    report_path = output_dir / "PUBLIC_EDITING_BASELINE_REPORT.md"
    matrix_path = output_dir / "public_benchmark_method_matrix.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(csv_path, rows)
    write_report(report_path, rows)
    write_matrix(matrix_path, rows)
    print(f"comparison_json: {json_path}")
    print(f"comparison_csv: {csv_path}")
    print(f"report: {report_path}")
    print(f"matrix: {matrix_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
