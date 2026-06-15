import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence


DEFAULT_REFUSAL = "I cannot provide private information."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 ROME/MEMIT 后的失败样本中构造 PACE Round2 编辑请求。")
    parser.add_argument("--leakage_eval", required=True, type=str, help="privacy leakage eval json 路径")
    parser.add_argument("--predictions", required=True, type=str, help="与 leakage eval 对应的 predictions jsonl 路径")
    parser.add_argument("--output_path", required=True, type=str, help="PACE round2 requests 输出 json")
    parser.add_argument("--target_new", default=DEFAULT_REFUSAL, type=str, help="统一拒答文本")
    parser.add_argument(
        "--failure_mode",
        choices=["target_only", "sensitive_only", "both"],
        default="both",
        help="target_only: 只选 target leak；sensitive_only: 只选 sensitive 且非 safe refusal；both: 当前默认逻辑",
    )
    parser.add_argument(
        "--max_requests_per_case",
        default=None,
        type=int,
        help="每个 private case 最多保留的 round2 requests 数；默认不限制",
    )
    parser.add_argument(
        "--max_requests_per_person",
        default=None,
        type=int,
        help="每个 person 最多保留的 round2 requests 数；默认不限制",
    )
    parser.add_argument(
        "--attack_types",
        default=None,
        type=str,
        help="可选，逗号分隔的 attack type 白名单，例如 direct,paraphrase",
    )
    return parser.parse_args()


def load_json(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path_str: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def prediction_index(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for record in records:
        key = str(record.get("base_prediction_id") or record.get("prediction_id"))
        index[key] = record
    return index


def parse_attack_types(raw_value: str | None) -> set[str] | None:
    if not raw_value:
        return None
    attack_types = {item.strip() for item in raw_value.split(",") if item.strip()}
    return attack_types or None


def should_reedit(row: Dict[str, Any], failure_mode: str) -> bool:
    has_target_failure = bool(row.get("any_target_exact_leak") or row.get("any_target_regex_leak"))
    has_sensitive_failure = bool(row.get("any_sensitive_pattern") and not row.get("any_safe_refusal"))
    if failure_mode == "target_only":
        return has_target_failure
    if failure_mode == "sensitive_only":
        return has_sensitive_failure
    return has_target_failure or has_sensitive_failure


def over_limit(current_count: int, max_count: int | None) -> bool:
    return max_count is not None and current_count >= max_count


def build_requests(
    eval_json: Dict[str, Any],
    predictions: List[Dict[str, Any]],
    target_new: str,
    *,
    failure_mode: str,
    max_requests_per_case: int | None,
    max_requests_per_person: int | None,
    allowed_attack_types: set[str] | None,
) -> List[Dict[str, Any]]:
    pred_index = prediction_index(predictions)
    requests: List[Dict[str, Any]] = []
    seen: set[str] = set()
    case_counts: Counter[str] = Counter()
    person_counts: Counter[str] = Counter()
    for row in eval_json.get("by_expected_row", []):
        if not should_reedit(row, failure_mode):
            continue
        attack_type = str(row.get("attack_type") or "")
        if allowed_attack_types is not None and attack_type not in allowed_attack_types:
            continue
        base_prediction_id = str(row.get("base_prediction_id") or row["prediction_id"])
        detail = pred_index.get(base_prediction_id)
        if not detail:
            continue
        if base_prediction_id in seen:
            continue
        case_id = str(detail["case_id"])
        person_id = str(detail.get("person_id") or "")
        if over_limit(case_counts[case_id], max_requests_per_case):
            continue
        if person_id and over_limit(person_counts[person_id], max_requests_per_person):
            continue
        seen.add(base_prediction_id)
        requests.append(
            {
                "source_prediction_id": detail.get("prediction_id", base_prediction_id),
                "base_prediction_id": base_prediction_id,
                "case_id": detail["case_id"],
                "person_id": detail.get("person_id"),
                "name": detail["name"],
                "attribute": detail["attribute"],
                "privacy_type": detail.get("privacy_type"),
                "attack_type": detail["attack_type"],
                "attack_template_id": detail.get("attack_template_id"),
                "subject": detail["name"],
                "prompt": detail["prompt"],
                "ground_truth": detail.get("target_value") or detail.get("value"),
                "target_new": target_new,
                "failure_reason": {
                    "target_exact_leak": bool(row.get("any_target_exact_leak")),
                    "target_regex_leak": bool(row.get("any_target_regex_leak")),
                    "sensitive_pattern": bool(row.get("any_sensitive_pattern")),
                    "safe_refusal": bool(row.get("any_safe_refusal")),
                },
            }
        )
        case_counts[case_id] += 1
        if person_id:
            person_counts[person_id] += 1
    return requests


def summarize_requests(requests: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_attack_type = Counter(str(item.get("attack_type") or "unknown") for item in requests)
    by_case = Counter(str(item.get("case_id") or "unknown") for item in requests)
    by_person = Counter(str(item.get("person_id") or "unknown") for item in requests)
    return {
        "num_requests": len(requests),
        "by_attack_type": dict(sorted(by_attack_type.items())),
        "num_cases": len(by_case),
        "num_people": len([key for key in by_person if key and key != "unknown"]),
        "max_requests_per_case_observed": max(by_case.values()) if by_case else 0,
        "max_requests_per_person_observed": max(by_person.values()) if by_person else 0,
    }


def main() -> int:
    args = parse_args()
    eval_json = load_json(args.leakage_eval)
    predictions = load_jsonl(args.predictions)
    allowed_attack_types = parse_attack_types(args.attack_types)
    requests = build_requests(
        eval_json,
        predictions,
        args.target_new,
        failure_mode=args.failure_mode,
        max_requests_per_case=args.max_requests_per_case,
        max_requests_per_person=args.max_requests_per_person,
        allowed_attack_types=allowed_attack_types,
    )
    request_summary = summarize_requests(requests)

    payload = {
        "leakage_eval_path": args.leakage_eval,
        "predictions_path": args.predictions,
        "target_new": args.target_new,
        "failure_mode": args.failure_mode,
        "max_requests_per_case": args.max_requests_per_case,
        "max_requests_per_person": args.max_requests_per_person,
        "attack_types": sorted(allowed_attack_types) if allowed_attack_types is not None else None,
        "num_requests": len(requests),
        "request_summary": request_summary,
        "requests": requests,
    }

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"leakage_eval: {args.leakage_eval}")
    print(f"predictions: {args.predictions}")
    print(f"failure_mode: {args.failure_mode}")
    print(f"max_requests_per_case: {args.max_requests_per_case}")
    print(f"max_requests_per_person: {args.max_requests_per_person}")
    print(f"attack_types: {','.join(sorted(allowed_attack_types)) if allowed_attack_types else 'ALL'}")
    print(f"num_requests: {len(requests)}")
    print(f"max_requests_per_case_observed: {request_summary['max_requests_per_case_observed']}")
    print(f"max_requests_per_person_observed: {request_summary['max_requests_per_person_observed']}")
    print(f"output_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
