import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 synthetic privacy dataset 构造 direct-only refusal 编辑请求。")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="synthetic privacy dataset json 路径",
    )
    parser.add_argument(
        "--output_path",
        default="artifacts/synthetic_privacy_data/rome_privacy_requests.json",
        type=str,
        help="编辑请求输出 json 路径",
    )
    parser.add_argument("--num_people", default=5, type=int, help="选择前多少个人")
    parser.add_argument("--private_per_person", default=2, type=int, help="每个人选多少条 private facts")
    parser.add_argument(
        "--prompt_style",
        choices=["canonical_qa", "dataset_prompt"],
        default="canonical_qa",
        help="使用固定 QA 模板，或沿用数据集中的 edit_request.prompt",
    )
    parser.add_argument(
        "--target_new",
        default=None,
        type=str,
        help="统一覆盖 target_new；默认使用数据集中的 refusal text",
    )
    return parser.parse_args()


def load_dataset(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def canonical_prompt(name: str, attribute: str) -> str:
    if attribute == "phone":
        return f"Q: What is {name}'s phone number?\nA:"
    if attribute == "email":
        return f"Q: What is {name}'s email address?\nA:"
    return f"Q: What is {name}'s {attribute}?\nA:"


def get_primary_test_prompts(case: Dict[str, Any]) -> Dict[str, str]:
    if case.get("test_prompts"):
        return dict(case["test_prompts"])
    prompts: Dict[str, str] = {}
    for row in case.get("test_prompt_rows", []):
        prompts.setdefault(row["attack_type"], row["prompt"])
    return prompts


def select_requests(
    dataset: Dict[str, Any],
    num_people: int,
    private_per_person: int,
    prompt_style: str,
    target_new_override: str | None,
) -> List[Dict[str, Any]]:
    refusal_text = target_new_override or dataset.get("refusal_text", "I cannot provide private information.")
    private_cases_by_person: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    person_names: Dict[str, str] = {}

    for case in dataset["flat_cases"]:
        if case.get("sensitivity") != "private":
            continue
        private_cases_by_person[case["person_id"]].append(case)
        person_names[case["person_id"]] = case["name"]

    selected_person_ids = sorted(private_cases_by_person)[:num_people]
    requests: List[Dict[str, Any]] = []
    for person_id in selected_person_ids:
        selected_cases = private_cases_by_person[person_id][:private_per_person]
        for case in selected_cases:
            edit_request = case["edit_request"]
            prompt = canonical_prompt(case["name"], case["attribute"]) if prompt_style == "canonical_qa" else edit_request["prompt"]
            requests.append(
                {
                    "case_id": case["case_id"],
                    "person_id": person_id,
                    "name": case["name"],
                    "attribute": case["attribute"],
                    "privacy_type": case.get("privacy_type"),
                    "sensitivity": "private",
                    "subject": edit_request["subject"],
                    "prompt": prompt,
                    "ground_truth": edit_request["ground_truth"],
                    "target_new": refusal_text,
                    "rephrase_prompt": edit_request.get("rephrase_prompt"),
                    "locality_prompt": edit_request.get("locality_prompt"),
                    "locality_ground_truth": edit_request.get("locality_ground_truth"),
                    "test_prompts": get_primary_test_prompts(case),
                    "test_prompt_rows": case.get("test_prompt_rows", []),
                    "value": case["value"],
                }
            )
    return requests


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    requests = select_requests(
        dataset,
        args.num_people,
        args.private_per_person,
        args.prompt_style,
        args.target_new,
    )

    output = {
        "dataset_path": args.dataset,
        "num_people": args.num_people,
        "private_per_person": args.private_per_person,
        "prompt_style": args.prompt_style,
        "num_requests": len(requests),
        "requests": requests,
    }

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print(f"dataset: {args.dataset}")
    print(f"num_requests: {len(requests)}")
    print(f"output_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
