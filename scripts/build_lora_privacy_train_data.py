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


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = build_records(dataset)

    summary_counter = Counter((record["sensitivity"], record["template_type"]) for record in records)
    payload = {
        "source_dataset": args.dataset,
        "num_people": dataset["num_people"],
        "num_records": len(records),
        "records": records,
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
    print(f"num_records: {len(records)}")
    print(f"counts: {payload['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
