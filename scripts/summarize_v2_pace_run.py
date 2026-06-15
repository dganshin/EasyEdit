import argparse
import json
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 v2 merged / ROME direct-only / conservative PACE 的单轮结果。")
    parser.add_argument("--pre_privacy_eval", required=True, type=str)
    parser.add_argument("--pre_public_eval", required=True, type=str)
    parser.add_argument("--direct_privacy_eval", required=True, type=str)
    parser.add_argument("--direct_public_eval", required=True, type=str)
    parser.add_argument("--pace_privacy_eval", required=True, type=str)
    parser.add_argument("--pace_public_eval", required=True, type=str)
    parser.add_argument("--direct_requests_json", required=True, type=str)
    parser.add_argument("--round2_requests_json", required=True, type=str)
    parser.add_argument("--combined_requests_json", required=True, type=str)
    parser.add_argument("--output_path", required=True, type=str)
    return parser.parse_args()


def load_json(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def pick_private_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    overall = payload.get("overall", {})
    return {
        "num_expected_attack_prompts": payload.get("num_expected_attack_prompts", 0),
        "num_evaluated_predictions": payload.get("num_evaluated_predictions", 0),
        "target_exact_leak_rate": overall.get("target_exact_leak_rate", 0.0),
        "target_regex_leak_rate": overall.get("target_regex_leak_rate", 0.0),
        "sensitive_pattern_rate": overall.get("sensitive_pattern_rate", 0.0),
        "safe_refusal_rate": overall.get("safe_refusal_rate", 0.0),
        "by_attack_type": payload.get("by_attack_type", {}),
        "grouped_any_metrics": payload.get("grouped_any_metrics", {}),
    }


def pick_public_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    overall = payload.get("overall", {})
    return {
        "num_expected_public_prompts": payload.get("num_expected_public_prompts", 0),
        "num_evaluated_predictions": payload.get("num_evaluated_predictions", 0),
        "public_exact_acc": overall.get("exact_match_rate", 0.0),
        "public_contains_acc": overall.get("contains_match_rate", 0.0),
        "by_attribute": payload.get("by_attribute", {}),
        "by_public_type": payload.get("by_public_type", {}),
    }


def summarize_request_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "request_summary" in payload:
        return payload["request_summary"]
    requests = payload.get("requests", [])
    by_case = {}
    by_person = {}
    by_attack_type = {}
    for item in requests:
        case_id = str(item.get("case_id") or "unknown")
        person_id = str(item.get("person_id") or "unknown")
        attack_type = str(item.get("attack_type") or "unknown")
        by_case[case_id] = by_case.get(case_id, 0) + 1
        by_person[person_id] = by_person.get(person_id, 0) + 1
        by_attack_type[attack_type] = by_attack_type.get(attack_type, 0) + 1
    real_people = [key for key in by_person if key and key != "unknown"]
    return {
        "num_requests": len(requests),
        "num_cases": len(by_case),
        "num_people": len(real_people),
        "by_attack_type": dict(sorted(by_attack_type.items())),
        "max_requests_per_case": max(by_case.values()) if by_case else 0,
        "max_requests_per_person": max((by_person[key] for key in real_people), default=0),
    }


def main() -> int:
    args = parse_args()

    pre_privacy = load_json(args.pre_privacy_eval)
    pre_public = load_json(args.pre_public_eval)
    direct_privacy = load_json(args.direct_privacy_eval)
    direct_public = load_json(args.direct_public_eval)
    pace_privacy = load_json(args.pace_privacy_eval)
    pace_public = load_json(args.pace_public_eval)
    direct_requests = load_json(args.direct_requests_json)
    round2_requests = load_json(args.round2_requests_json)
    combined_requests = load_json(args.combined_requests_json)

    summary = {
        "merged_pre_edit": {
            "private": pick_private_metrics(pre_privacy),
            "public": pick_public_metrics(pre_public),
        },
        "rome_direct_only": {
            "private": pick_private_metrics(direct_privacy),
            "public": pick_public_metrics(direct_public),
        },
        "pace_round2": {
            "private": pick_private_metrics(pace_privacy),
            "public": pick_public_metrics(pace_public),
        },
        "request_counts": {
            "round1_direct": summarize_request_payload(direct_requests),
            "round2_conservative": summarize_request_payload(round2_requests),
            "combined_total": summarize_request_payload(combined_requests),
        },
    }

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(f"direct_full_exact: {summary['rome_direct_only']['private']['target_exact_leak_rate']:.4f}")
    print(f"pace_full_exact: {summary['pace_round2']['private']['target_exact_leak_rate']:.4f}")
    print(f"direct_public_contains: {summary['rome_direct_only']['public']['public_contains_acc']:.4f}")
    print(f"pace_public_contains: {summary['pace_round2']['public']['public_contains_acc']:.4f}")
    print(f"round2_requests: {summary['request_counts']['round2_conservative']['num_requests']}")
    print(f"total_requests: {summary['request_counts']['combined_total']['num_requests']}")
    print(f"summary_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
