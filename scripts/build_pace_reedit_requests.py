import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_REFUSAL = "I cannot provide private information."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 ROME/MEMIT 后的失败样本中构造 PACE Round2 编辑请求。")
    parser.add_argument("--leakage_eval", required=True, type=str, help="privacy leakage eval json 路径")
    parser.add_argument("--predictions", required=True, type=str, help="与 leakage eval 对应的 predictions jsonl 路径")
    parser.add_argument("--output_path", required=True, type=str, help="PACE round2 requests 输出 json")
    parser.add_argument("--target_new", default=DEFAULT_REFUSAL, type=str, help="统一拒答文本")
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


def should_reedit(row: Dict[str, Any]) -> bool:
    return bool(
        row.get("any_target_exact_leak")
        or row.get("any_target_regex_leak")
        or (row.get("any_sensitive_pattern") and not row.get("any_safe_refusal"))
    )


def build_requests(eval_json: Dict[str, Any], predictions: List[Dict[str, Any]], target_new: str) -> List[Dict[str, Any]]:
    pred_index = prediction_index(predictions)
    requests: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in eval_json.get("by_expected_row", []):
        if not should_reedit(row):
            continue
        base_prediction_id = str(row.get("base_prediction_id") or row["prediction_id"])
        detail = pred_index.get(base_prediction_id)
        if not detail:
            continue
        if base_prediction_id in seen:
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
    return requests


def main() -> int:
    args = parse_args()
    eval_json = load_json(args.leakage_eval)
    predictions = load_jsonl(args.predictions)
    requests = build_requests(eval_json, predictions, args.target_new)

    payload = {
        "leakage_eval_path": args.leakage_eval,
        "predictions_path": args.predictions,
        "target_new": args.target_new,
        "num_requests": len(requests),
        "requests": requests,
    }

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"leakage_eval: {args.leakage_eval}")
    print(f"predictions: {args.predictions}")
    print(f"num_requests: {len(requests)}")
    print(f"output_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
