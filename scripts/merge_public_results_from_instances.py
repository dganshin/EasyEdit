import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge Qwen/GPT-J public benchmark results into final tables.")
    parser.add_argument("--root_dir", default="artifacts/public_benchmarks_20260622", type=str)
    parser.add_argument("--output_dir", default="artifacts/final_comparison_20260622", type=str)
    return parser.parse_args()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def infer_model_family(path: Path, config: Dict[str, Any], row_model: Any) -> str:
    model = str(row_model or config.get("model_name") or "")
    text = f"{path.as_posix()} {model}".lower()
    if "gptj" in text or "gpt-j" in text:
        return "GPT-J-6B"
    if "qwen" in text:
        return "Qwen2.5-7B"
    return model or "unknown"


def parse_method(method: str, config: Dict[str, Any]) -> Dict[str, str]:
    base = str(config.get("base_method") or method)
    wrapper = "BASE"
    if method.endswith("_PACE_EDIT"):
        base = method[: -len("_PACE_EDIT")]
        wrapper = "PACE-Edit"
    elif method.endswith("_CAPE_EDIT"):
        base = method[: -len("_CAPE_EDIT")]
        wrapper = "CAPE-Edit"
    return {"base_editor": base, "wrapper": wrapper}


def load_selection_counts(method_dir: Path, root: Path, dataset: str, model_slug: str, base_editor: str) -> Dict[str, Any]:
    selection_dir = root / f"{model_slug}_{dataset}" / f"{base_editor}_PACE_CAPE_SELECTION"
    report = read_json(selection_dir / "selection_report.json") or {}
    split = read_json(selection_dir / "split_report.json") or {}
    return {
        "n_selection": report.get("selection_split_size") or split.get("selection_split_size"),
        "n_heldout": report.get("heldout_size") or split.get("heldout_size"),
        "round1_count": report.get("round1_count"),
        "round2_count": report.get("pace_round2_count") if method_dir.name.endswith("_PACE_EDIT") else report.get("cape_round2_count"),
        "union_count": report.get("pace_union_count") if method_dir.name.endswith("_PACE_EDIT") else report.get("cape_union_count"),
    }


def aggregate_rows(root: Path) -> List[Dict[str, Any]]:
    rows = []
    comparison = read_json(root / "public_editing_comparison.json")
    source_rows = comparison.get("rows", []) if comparison else []
    by_method_dir = {str(row.get("method_dir")): row for row in source_rows if row.get("method_dir")}

    for summary_path in sorted(root.rglob("summary.json")):
        method_dir = summary_path.parent
        if "PACE_CAPE_SELECTION" in method_dir.as_posix():
            continue
        summary = read_json(summary_path) or {}
        config = read_json(method_dir / "method_config.json") or {}
        aggregate = by_method_dir.get(str(method_dir), {})
        method = str(summary.get("method") or config.get("method") or method_dir.name)
        dataset = str(config.get("dataset_name") or aggregate.get("dataset") or "")
        model = infer_model_family(method_dir, config, aggregate.get("model"))
        model_slug = "gptj" if model == "GPT-J-6B" else "qwen" if model == "Qwen2.5-7B" else "unknown"
        method_parts = parse_method(method, config)
        per_case_path = method_dir / "per_case_results.jsonl"
        selection_counts = load_selection_counts(method_dir, root, dataset, model_slug, method_parts["base_editor"]) if method_parts["wrapper"] != "BASE" else {}
        rows.append(
            {
                "dataset": dataset,
                "model": model,
                "method": method.replace("_PACE_EDIT", "+PACE-Edit").replace("_CAPE_EDIT", "+CAPE-Edit"),
                "base_editor": method_parts["base_editor"],
                "wrapper": method_parts["wrapper"],
                "n_cases": summary.get("num_cases") or summary.get("num_cases_attempted") or read_jsonl_count(per_case_path),
                "n_selection": selection_counts.get("n_selection"),
                "n_heldout": selection_counts.get("n_heldout"),
                "round1_count": selection_counts.get("round1_count"),
                "round2_count": selection_counts.get("round2_count"),
                "union_count": selection_counts.get("union_count"),
                "reliability": aggregate.get("reliability_rewrite_success"),
                "generalization": aggregate.get("generalization_rephrase_success"),
                "locality": aggregate.get("locality_retain_success"),
                "failure_count": 1 if summary.get("status") == "failed" else 0,
                "runtime_sec": summary.get("elapsed_sec"),
                "status": summary.get("status") or "missing",
                "error_summary": summary.get("error"),
                "method_dir": str(method_dir),
            }
        )
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "dataset",
        "model",
        "method",
        "base_editor",
        "wrapper",
        "n_cases",
        "n_selection",
        "n_heldout",
        "round1_count",
        "round2_count",
        "union_count",
        "reliability",
        "generalization",
        "locality",
        "failure_count",
        "runtime_sec",
        "status",
        "error_summary",
        "method_dir",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_md(path: Path, rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# Public CounterFact/zsRE Results Across Models",
        "",
        "| Dataset | Model | Method | Reliability | Generalization | Locality | N | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {fmt(row['dataset'])} | {fmt(row['model'])} | {fmt(row['method'])} | {fmt(row['reliability'])} | {fmt(row['generalization'])} | {fmt(row['locality'])} | {fmt(row['n_cases'])} | {fmt(row['status'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(path: Path, rows: List[Dict[str, Any]]) -> None:
    ok = sum(1 for row in rows if row["status"] == "ok")
    failed = sum(1 for row in rows if row["status"] == "failed")
    wrappers = [row for row in rows if row["wrapper"] != "BASE"]
    lines = [
        "# Public Baseline Final Report",
        "",
        f"- total method rows: `{len(rows)}`",
        f"- ok rows: `{ok}`",
        f"- failed rows: `{failed}`",
        f"- wrapper rows: `{len(wrappers)}`",
        "",
        "CounterFact/zsRE are public factual editing benchmarks. Wrapper rows validate PACE/CAPE as closed-loop request selection strategies rather than privacy-leakage metrics.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_matrix(path: Path, rows: List[Dict[str, Any]]) -> None:
    failures = [row for row in rows if row["status"] != "ok"]
    write_csv(path, failures)


def main() -> int:
    args = parse_args()
    root = Path(args.root_dir)
    out = Path(args.output_dir)
    rows = aggregate_rows(root)
    rows.sort(key=lambda row: (row["dataset"], row["model"], row["wrapper"], row["method"]))
    write_csv(out / "public_counterfact_zsre_all_models.csv", rows)
    write_md(out / "public_counterfact_zsre_all_models.md", rows)
    write_report(out / "PUBLIC_BASELINE_FINAL_REPORT.md", rows)
    write_failure_matrix(out / "public_method_failure_matrix.csv", rows)
    print(f"rows: {len(rows)}")
    print(f"output_dir: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
