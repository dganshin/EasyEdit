import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 synthetic privacy 数据质量与分布。")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="synthetic privacy 数据集 json 路径",
    )
    parser.add_argument(
        "--output_path",
        default=None,
        type=str,
        help="可选审计结果输出路径",
    )
    return parser.parse_args()


def load_dataset(path_str: str) -> Dict[str, Any]:
    with Path(path_str).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or "flat_cases" not in data:
        raise ValueError("dataset 必须是包含 flat_cases 的 json")
    return data


def find_duplicates(items: Iterable[str]) -> Dict[str, int]:
    counter = Counter(items)
    return {key: count for key, count in counter.items() if count > 1}


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    flat_cases: List[Dict[str, Any]] = dataset["flat_cases"]

    names = [str(person["name"]) for person in dataset.get("people", [])]
    duplicate_names = find_duplicates(names)

    private_cases = [case for case in flat_cases if case.get("sensitivity") == "private"]
    public_cases = [case for case in flat_cases if case.get("sensitivity") == "public"]

    private_values = [str(case.get("value")) for case in private_cases]
    duplicate_private_values = find_duplicates(private_values)

    attack_type_counter: Counter[str] = Counter()
    prompt_counter: Counter[str] = Counter()
    prompt_by_type_counter: Counter[str] = Counter()
    prompts_by_case: Dict[str, List[str]] = defaultdict(list)
    public_type_counter: Counter[str] = Counter()
    attribute_counter: Counter[str] = Counter()
    inject_template_counter: Counter[str] = Counter()

    for case in flat_cases:
        attribute_counter[str(case.get("attribute"))] += 1
        if case.get("sensitivity") == "public":
            public_type_counter[str(case.get("public_type") or "unknown")] += 1
        for prompt_spec in case.get("inject_prompts", []):
            inject_template_counter[str(prompt_spec.get("template_id", "unknown"))] += 1
        for row in case.get("test_prompt_rows", []):
            prompt = str(row.get("prompt", "")).strip()
            attack_type = str(row.get("attack_type", "unknown"))
            attack_type_counter[attack_type] += 1
            prompt_counter[prompt] += 1
            prompt_by_type_counter[f"{attack_type}::{prompt}"] += 1
            prompts_by_case[str(case["case_id"])].append(prompt)

    repeated_prompts_global = {key: count for key, count in prompt_counter.items() if count > 1}
    repeated_prompts_same_type = {
        key: count for key, count in prompt_by_type_counter.items() if count > 1
    }
    duplicate_prompts_within_case = {
        case_id: find_duplicates(prompts)
        for case_id, prompts in prompts_by_case.items()
        if find_duplicates(prompts)
    }

    summary = {
        "source_dataset": args.dataset,
        "num_people": dataset.get("num_people"),
        "num_flat_cases": len(flat_cases),
        "num_private_cases": len(private_cases),
        "num_public_cases": len(public_cases),
        "attribute_counts": dict(sorted(attribute_counter.items())),
        "public_type_counts": dict(sorted(public_type_counter.items())),
        "attack_prompt_counts": dict(sorted(attack_type_counter.items())),
        "inject_template_counts": dict(sorted(inject_template_counter.items())),
        "duplicate_name_count": len(duplicate_names),
        "duplicate_private_value_count": len(duplicate_private_values),
        "repeated_prompt_count_global": len(repeated_prompts_global),
        "repeated_prompt_count_same_attack_type": len(repeated_prompts_same_type),
        "duplicate_prompt_case_count": len(duplicate_prompts_within_case),
        "duplicate_names": duplicate_names,
        "duplicate_private_values": duplicate_private_values,
        "duplicate_prompts_within_case": duplicate_prompts_within_case,
        "top_repeated_prompts_global": sorted(
            repeated_prompts_global.items(),
            key=lambda item: (-item[1], item[0]),
        )[:20],
        "top_repeated_prompts_same_attack_type": sorted(
            repeated_prompts_same_type.items(),
            key=lambda item: (-item[1], item[0]),
        )[:20],
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.output_path:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)

    if duplicate_names or duplicate_private_values or duplicate_prompts_within_case:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
