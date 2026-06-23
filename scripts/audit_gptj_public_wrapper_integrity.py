#!/usr/bin/env python3
"""Audit whether GPT-J public wrapper results are real and not path mixups.

This script is intentionally read-only. It checks summary files and raw
per-case JSONL metrics under artifacts/public_benchmarks_20260623_200.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


METHODS = ["ROME", "FT", "ROME_PACE_EDIT", "ROME_CAPE_EDIT"]
DATASETS = ["counterfact", "zsre"]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                yield {"__json_error__": f"line {line_no}: {exc}"}


def flatten_metric(raw: Any) -> List[float]:
    if isinstance(raw, (int, float, bool)):
        return [float(raw)]
    if isinstance(raw, list):
        return [float(item) for item in raw if isinstance(item, (int, float, bool))]
    return []


def post_metric(row: Dict[str, Any], key: str) -> List[float]:
    metrics = row.get("metrics") or {}
    post = metrics.get("post") or {}
    if key == "loc_acc":
        return flatten_metric((post.get("locality") or {}).get("loc_acc"))
    return flatten_metric(post.get(key))


def avg(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def fmt(value: Optional[float]) -> str:
    if value is None:
        return "NA"
    return f"{value:.6f}"


def summarize_per_case(path: Path) -> Dict[str, Any]:
    rows = list(iter_jsonl(path))
    json_errors = [row["__json_error__"] for row in rows if "__json_error__" in row]
    rows = [row for row in rows if "__json_error__" not in row]
    rewrite: List[float] = []
    rephrase: List[float] = []
    locality: List[float] = []
    method_tags = set()
    dataset_tags = set()
    case_prefixes = set()
    sample_requests = []

    for row in rows:
        rewrite.extend(post_metric(row, "rewrite_acc"))
        rephrase.extend(post_metric(row, "rephrase_acc"))
        locality.extend(post_metric(row, "loc_acc"))
        if row.get("method"):
            method_tags.add(str(row.get("method")))
        if row.get("dataset"):
            dataset_tags.add(str(row.get("dataset")))
        case_id = str(row.get("case_id", ""))
        if "_" in case_id:
            case_prefixes.add(case_id.split("_", 1)[0])
        if len(sample_requests) < 3:
            req = row.get("request") or (row.get("metrics") or {}).get("requested_rewrite") or {}
            sample_requests.append(
                {
                    "case_id": row.get("case_id"),
                    "prompt": req.get("prompt"),
                    "subject": req.get("subject"),
                    "target_new": req.get("target_new"),
                    "ground_truth": req.get("ground_truth"),
                }
            )

    return {
        "exists": path.exists(),
        "path": str(path),
        "rows": len(rows),
        "json_errors": json_errors,
        "method_tags": sorted(method_tags),
        "dataset_tags": sorted(dataset_tags),
        "case_prefixes": sorted(case_prefixes),
        "rewrite_avg": avg(rewrite),
        "rewrite_nonzero": sum(1 for value in rewrite if value != 0),
        "rewrite_n": len(rewrite),
        "rephrase_avg": avg(rephrase),
        "rephrase_nonzero": sum(1 for value in rephrase if value != 0),
        "rephrase_n": len(rephrase),
        "locality_avg": avg(locality),
        "locality_nonzero": sum(1 for value in locality if value != 0),
        "locality_n": len(locality),
        "samples": sample_requests,
    }


def print_block(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def audit_dataset(art_root: Path, dataset: str) -> None:
    gptj_dir = art_root / f"gptj_{dataset}"
    qwen_dir = art_root / f"qwen_{dataset}"
    print_block(f"DATASET: {dataset}")
    print(f"gptj_dir_exists={gptj_dir.exists()} path={gptj_dir}")
    print(f"qwen_dir_exists={qwen_dir.exists()} path={qwen_dir}")

    for method in METHODS:
        run_dir = gptj_dir / method
        summary_path = run_dir / "summary.json"
        per_case_path = run_dir / "per_case_results.jsonl"
        summary = read_json(summary_path)
        print("\n---", f"gptj_{dataset}/{method}", "---")
        print(f"summary_exists={summary_path.exists()} per_case_exists={per_case_path.exists()}")
        if summary:
            keys = [
                "status",
                "model",
                "model_name",
                "model_path",
                "dataset",
                "method",
                "num_cases",
                "n_cases",
                "reliability_rewrite_success",
                "generalization_rephrase_success",
                "locality_retain_success",
                "elapsed_sec",
            ]
            for key in keys:
                if key in summary:
                    print(f"summary.{key}={summary[key]}")
            if "failure_error" in summary:
                print(f"summary.failure_error={summary['failure_error']}")
        stats = summarize_per_case(per_case_path)
        print(
            "per_case:",
            f"rows={stats['rows']}",
            f"method_tags={stats['method_tags']}",
            f"dataset_tags={stats['dataset_tags']}",
            f"case_prefixes={stats['case_prefixes']}",
        )
        print(
            "post_metrics:",
            f"rewrite_avg={fmt(stats['rewrite_avg'])}",
            f"rewrite_nonzero={stats['rewrite_nonzero']}/{stats['rewrite_n']}",
            f"rephrase_avg={fmt(stats['rephrase_avg'])}",
            f"rephrase_nonzero={stats['rephrase_nonzero']}/{stats['rephrase_n']}",
            f"locality_avg={fmt(stats['locality_avg'])}",
            f"locality_nonzero={stats['locality_nonzero']}/{stats['locality_n']}",
        )
        if stats["json_errors"]:
            print("json_errors=", stats["json_errors"][:5])
        print("sample_requests=")
        for sample in stats["samples"]:
            print("  ", sample)


def compare_qwen_gptj_paths(art_root: Path) -> None:
    print_block("PATH COLLISION / MIXUP CHECK")
    for dataset in DATASETS:
        for method in ["ROME_PACE_EDIT", "ROME_CAPE_EDIT"]:
            gptj = art_root / f"gptj_{dataset}" / method / "per_case_results.jsonl"
            qwen = art_root / f"qwen_{dataset}" / method / "per_case_results.jsonl"
            print(f"{dataset}/{method}")
            print(f"  gptj_exists={gptj.exists()} size={gptj.stat().st_size if gptj.exists() else 'NA'} path={gptj}")
            print(f"  qwen_exists={qwen.exists()} size={qwen.stat().st_size if qwen.exists() else 'NA'} path={qwen}")
            if gptj.exists() and qwen.exists():
                same_size = gptj.stat().st_size == qwen.stat().st_size
                print(f"  same_size_as_qwen={same_size}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--art_root",
        default="artifacts/public_benchmarks_20260623_200",
        help="Root directory containing gptj_* and qwen_* public benchmark artifacts.",
    )
    args = parser.parse_args()
    art_root = Path(args.art_root)
    print(f"art_root={art_root.resolve()}")
    print(f"art_root_exists={art_root.exists()}")
    if not art_root.exists():
        return 2
    compare_qwen_gptj_paths(art_root)
    for dataset in DATASETS:
        audit_dataset(art_root, dataset)
    print_block("INTERPRETATION")
    print("If GPT-J ROME/FT have high post rewrite but GPT-J ROME_PACE/CAPE have near-zero post rewrite,")
    print("then the near-zero wrapper result is not caused by a broken GPT-J model directory.")
    print("If gptj_* paths exist separately from qwen_* and sizes differ, the result is not a simple Qwen/GPT-J path collision.")
    print("If per_case method_tags are ROME_PACE_EDIT / ROME_CAPE_EDIT and case prefixes match the dataset,")
    print("the zero comes from the GPT-J wrapper per-case files themselves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
