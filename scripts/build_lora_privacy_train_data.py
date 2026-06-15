import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="基于 synthetic privacy 数据集构造 LoRA 注入训练数据。")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="synthetic privacy 数据集 json 路径",
    )
    parser.add_argument(
        "--output_dir",
        default="artifacts/synthetic_privacy_data",
        type=str,
        help="LoRA 训练数据输出目录",
    )
    parser.add_argument(
        "--private_repeat",
        default=1,
        type=int,
        help="将 private records 重复多少次，用于提高 private signal 强度",
    )
    parser.add_argument(
        "--max_public_to_private_ratio",
        default=0.0,
        type=float,
        help="若 > 0，则将 public records 截断到不超过 private records * 该比例",
    )
    return parser.parse_args()


def load_dataset(path_str: str) -> Dict[str, Any]:
    with Path(path_str).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_records(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for case in dataset["flat_cases"]:
        target = case["value"]
        for prompt_spec in case.get("inject_prompts", []):
            template_id = str(prompt_spec.get("template_id", "qa_t01"))
            template_type = "completion" if template_id.startswith("completion") else "qa"
            records.append(
                {
                    "record_id": f"{case['case_id']}::{template_id}",
                    "case_id": case["case_id"],
                    "person_id": case["person_id"],
                    "name": case["name"],
                    "attribute": case["attribute"],
                    "public_type": case.get("public_type"),
                    "sensitivity": case["sensitivity"],
                    "template_type": template_type,
                    "prompt": prompt_spec["prompt"],
                    "target": target,
                }
            )
    return records


def rebalance_records(
    records: List[Dict[str, Any]],
    private_repeat: int,
    max_public_to_private_ratio: float,
) -> List[Dict[str, Any]]:
    private_records = [record for record in records if record["sensitivity"] == "private"]
    public_records = [record for record in records if record["sensitivity"] == "public"]

    if private_repeat < 1:
        raise ValueError("--private_repeat 必须 >= 1")

    expanded_private: List[Dict[str, Any]] = []
    for repeat_idx in range(private_repeat):
        for record in private_records:
            cloned = dict(record)
            if repeat_idx > 0:
                cloned["record_id"] = f"{record['record_id']}::priv_repeat_{repeat_idx + 1:02d}"
            expanded_private.append(cloned)

    if max_public_to_private_ratio > 0:
        max_public_records = int(len(expanded_private) * max_public_to_private_ratio)
        public_records = public_records[:max_public_records]

    return expanded_private + public_records


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_records = build_records(dataset)
    records = rebalance_records(raw_records, args.private_repeat, args.max_public_to_private_ratio)

    summary_counter = Counter((record["sensitivity"], record["template_type"]) for record in records)
    raw_summary_counter = Counter((record["sensitivity"], record["template_type"]) for record in raw_records)
    payload = {
        "source_dataset": args.dataset,
        "num_people": dataset["num_people"],
        "private_repeat": args.private_repeat,
        "max_public_to_private_ratio": args.max_public_to_private_ratio,
        "num_raw_records": len(raw_records),
        "num_records": len(records),
        "records": records,
        "raw_counts": {
            f"{sensitivity}_{template_type}": count
            for (sensitivity, template_type), count in sorted(raw_summary_counter.items())
        },
        "counts": {
            f"{sensitivity}_{template_type}": count
            for (sensitivity, template_type), count in sorted(summary_counter.items())
        },
    }

    json_path = output_dir / "lora_privacy_train_dataset.json"
    jsonl_path = output_dir / "lora_privacy_train.jsonl"

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"dataset_json: {json_path}")
    print(f"dataset_jsonl: {jsonl_path}")
    print(f"num_raw_records: {len(raw_records)}")
    print(f"num_records: {len(records)}")
    print(f"raw_counts: {payload['raw_counts']}")
    print(f"counts: {payload['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
