import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build balanced LoRA/SFT sanitization data for v2 synthetic privacy.")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json",
        type=str,
    )
    parser.add_argument("--output_dir", default="artifacts/data_v2_lora_sanitization", type=str)
    parser.add_argument("--dev_ratio", default=0.1, type=float)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--max_private", default=None, type=int)
    parser.add_argument("--max_public", default=None, type=int)
    parser.add_argument("--no_balance", action="store_true")
    return parser.parse_args()


def load_dataset(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or "flat_cases" not in data:
        raise ValueError(f"dataset must be a v2 synthetic privacy dataset with flat_cases: {path}")
    return data


def build_private_records(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    refusal = dataset.get("refusal_text", "I cannot provide private information.")
    records: List[Dict[str, Any]] = []
    for case in dataset["flat_cases"]:
        if case.get("sensitivity") != "private":
            continue
        for row in case.get("test_prompt_rows") or []:
            records.append(
                {
                    "id": f"{case['case_id']}::{row['attack_type']}::{row['attack_template_id']}",
                    "split_source": "private_refusal",
                    "case_id": case["case_id"],
                    "person_id": case["person_id"],
                    "name": case["name"],
                    "sensitivity": "private",
                    "attribute": case["attribute"],
                    "privacy_type": case.get("privacy_type"),
                    "attack_type": row["attack_type"],
                    "attack_template_id": row["attack_template_id"],
                    "instruction": row["prompt"],
                    "input": "",
                    "output": refusal,
                }
            )
    return records


def build_public_records(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for case in dataset["flat_cases"]:
        if case.get("sensitivity") != "public":
            continue
        for row in case.get("test_prompt_rows") or []:
            records.append(
                {
                    "id": f"{case['case_id']}::{row['attack_type']}::{row['attack_template_id']}",
                    "split_source": "public_retain",
                    "case_id": case["case_id"],
                    "person_id": case["person_id"],
                    "name": case["name"],
                    "sensitivity": "public",
                    "attribute": case["attribute"],
                    "public_type": case.get("public_type"),
                    "attack_type": row["attack_type"],
                    "attack_template_id": row["attack_template_id"],
                    "instruction": row["prompt"],
                    "input": "",
                    "output": case["value"],
                }
            )
    return records


def limit_records(records: List[Dict[str, Any]], limit: int | None, rng: random.Random) -> List[Dict[str, Any]]:
    if limit is None or len(records) <= limit:
        return list(records)
    records = list(records)
    rng.shuffle(records)
    return records[:limit]


def split_by_person(records: List[Dict[str, Any]], dev_ratio: float, rng: random.Random) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    by_person: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_person[record["person_id"]].append(record)
    people = sorted(by_person)
    rng.shuffle(people)
    dev_people_count = max(1, int(round(len(people) * dev_ratio))) if people else 0
    dev_people = set(people[:dev_people_count])
    train: List[Dict[str, Any]] = []
    dev: List[Dict[str, Any]] = []
    for person in people:
        target = dev if person in dev_people else train
        target.extend(by_person[person])
    rng.shuffle(train)
    rng.shuffle(dev)
    return train, dev


def summarize(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    records = list(records)
    return {
        "num_records": len(records),
        "by_sensitivity": dict(Counter(item["sensitivity"] for item in records)),
        "by_split_source": dict(Counter(item["split_source"] for item in records)),
        "by_attack_type": dict(Counter(item.get("attack_type", "unknown") for item in records)),
        "num_people": len({item["person_id"] for item in records}),
    }


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_report(path: Path, stats: Dict[str, Any]) -> None:
    lines = [
        "# LoRA/SFT Sanitization Data Report",
        "",
        "## Construction",
        "",
        "- private queries -> `I cannot provide private information.`",
        "- public queries -> 原始 public fact value",
        "- 默认做 private/public balanced sampling，避免模型只学习拒答。",
        "- 本脚本只生成数据，不启动 LoRA/SFT 训练。",
        "",
        "## Data Statistics",
        "",
        f"- dataset: `{stats['dataset']}`",
        f"- output_dir: `{stats['output_dir']}`",
        f"- train records: `{stats['train']['num_records']}`",
        f"- dev records: `{stats['dev']['num_records']}`",
        f"- total records: `{stats['total']['num_records']}`",
        f"- balance_mode: `{stats['balance_mode']}`",
        "",
        "## Split Policy",
        "",
        "训练集和开发集按 subject/person 划分，降低同一人物 prompt 泄漏到不同 split 的风险。",
        "",
        "## Next Step",
        "",
        "等待确认后，再在 AutoDL 上用 LoRA/SFT baseline 训练脚本读取 `train.jsonl` 和 `dev.jsonl`。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if not (0.0 < args.dev_ratio < 0.5):
        raise ValueError("--dev_ratio should be in (0, 0.5)")
    rng = random.Random(args.seed)
    dataset = load_dataset(args.dataset)
    private_records = limit_records(build_private_records(dataset), args.max_private, rng)
    public_records = limit_records(build_public_records(dataset), args.max_public, rng)

    if not args.no_balance:
        n = min(len(private_records), len(public_records))
        rng.shuffle(private_records)
        rng.shuffle(public_records)
        private_records = private_records[:n]
        public_records = public_records[:n]
        balance_mode = f"balanced_to_{n}_per_class"
    else:
        balance_mode = "unbalanced_all_available_after_limits"

    records = private_records + public_records
    train, dev = split_by_person(records, args.dev_ratio, rng)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "train.jsonl", train)
    write_jsonl(output_dir / "dev.jsonl", dev)
    stats = {
        "dataset": args.dataset,
        "output_dir": str(output_dir),
        "seed": args.seed,
        "dev_ratio": args.dev_ratio,
        "balance_mode": balance_mode,
        "raw_private_records": len(build_private_records(dataset)),
        "raw_public_records": len(build_public_records(dataset)),
        "selected_private_records": len(private_records),
        "selected_public_records": len(public_records),
        "train": summarize(train),
        "dev": summarize(dev),
        "total": summarize(records),
    }
    with (output_dir / "data_stats.json").open("w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)
    write_report(output_dir / "LORA_SANITIZATION_DATA_REPORT.md", stats)
    print(f"train_jsonl: {output_dir / 'train.jsonl'}")
    print(f"dev_jsonl: {output_dir / 'dev.jsonl'}")
    print(f"data_stats: {output_dir / 'data_stats.json'}")
    print(f"report: {output_dir / 'LORA_SANITIZATION_DATA_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
