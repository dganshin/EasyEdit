import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


TOFU_SOURCE = "locuslab/TOFU"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a small TOFU forget/retain subset.")
    parser.add_argument("--output_dir", default="artifacts/public_benchmarks_20260622/tofu_small", type=str)
    parser.add_argument("--subset_size", default=200, type=int)
    parser.add_argument("--minimum_size", default=200, type=int)
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def normalize_item(item: Dict[str, Any], idx: int, split: str) -> Dict[str, Any] | None:
    question = item.get("question") or item.get("prompt") or item.get("input")
    answer = item.get("answer") or item.get("response") or item.get("output")
    if isinstance(answer, list):
        answer = answer[0] if answer else None
    if not question or not answer:
        return None
    return {
        "case_id": f"tofu_{split}_{idx:05d}",
        "dataset": "tofu",
        "split": split,
        "question": str(question),
        "answer": str(answer),
    }


def load_tofu_subset(size: int) -> tuple[List[Dict[str, Any]], Counter]:
    from datasets import load_dataset

    dropped: Counter = Counter()
    rows: List[Dict[str, Any]] = []
    candidates = [
        ("forget01", "train"),
        ("forget05", "train"),
        ("retain90", "train"),
        (None, "train"),
    ]
    for config, split in candidates:
        if len(rows) >= size:
            break
        try:
            ds = load_dataset(TOFU_SOURCE, config, split=split) if config else load_dataset(TOFU_SOURCE, split=split)
        except Exception as exc:
            dropped[f"load_failed_{config or 'default'}"] += 1
            continue
        for item in ds:
            row = normalize_item(dict(item), len(rows), config or split)
            if row is None:
                dropped["missing_question_or_answer"] += 1
                continue
            rows.append(row)
            if len(rows) >= size:
                break
    return rows, dropped


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# TOFU Small Subset Report",
        "",
        f"- source: `{TOFU_SOURCE}`",
        f"- records: `{payload['num_records']}`",
        f"- output: `{payload['subset_path']}`",
        "",
        "## Protocol",
        "",
        "TOFU 用作公开 forget/retain 迁移检查，不等同于 synthetic PII 清洗。建议先用 Prompt Refusal / ROME / LoRA-SFT Sanitization 做小样本验证。",
        "",
        "## Dropped Reasons",
        "",
        f"`{payload['dropped_reasons']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.subset_size < args.minimum_size:
        raise ValueError("subset_size must be >= minimum_size")
    if args.subset_size > 500:
        raise ValueError("TOFU small subset must be <= 500")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, dropped = load_tofu_subset(args.subset_size)
    if len(rows) < args.minimum_size:
        raise RuntimeError(f"TOFU subset has {len(rows)} rows, below minimum {args.minimum_size}")
    subset_path = output_dir / f"tofu_{len(rows)}.json"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": TOFU_SOURCE,
        "num_records": len(rows),
        "records": rows,
    }
    write_json(subset_path, payload)
    report_payload = {
        "num_records": len(rows),
        "subset_path": str(subset_path),
        "dropped_reasons": dict(dropped),
    }
    write_json(output_dir / "tofu_subset_stats.json", report_payload)
    write_report(output_dir / "TOFU_SMALL_SUBSET_REPORT.md", report_payload)
    print(f"tofu_subset: {subset_path}")
    print(f"report: {output_dir / 'TOFU_SMALL_SUBSET_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
