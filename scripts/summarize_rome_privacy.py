import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 merged privacy model 与 ROME direct-only 的前后结果。")
    parser.add_argument("--pre_privacy_eval", required=True, type=str, help="编辑前 private leakage eval json")
    parser.add_argument("--post_subset_privacy_eval", required=True, type=str, help="ROME 后 edited subset private eval json")
    parser.add_argument("--post_full_privacy_eval", default=None, type=str, help="ROME 后 full private eval json")
    parser.add_argument("--pre_public_eval", default=None, type=str, help="编辑前 public retain eval json")
    parser.add_argument("--post_public_eval", default=None, type=str, help="ROME 后 public retain eval json")
    parser.add_argument("--output_path", required=True, type=str, help="汇总 json 输出路径")
    return parser.parse_args()


def load_json(path_str: str | None, *, required: bool) -> Dict[str, Any] | None:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        if required:
            raise FileNotFoundError(f"找不到必需输入文件: {path}")
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def pick_private_metrics(payload: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if payload is None:
        return None
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


def pick_public_metrics(payload: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if payload is None:
        return None
    overall = payload.get("overall", {})
    return {
        "num_expected_public_prompts": payload.get("num_expected_public_prompts", 0),
        "num_evaluated_predictions": payload.get("num_evaluated_predictions", 0),
        "public_exact_acc": overall.get("exact_match_rate", 0.0),
        "public_contains_acc": overall.get("contains_match_rate", 0.0),
        "by_attribute": payload.get("by_attribute", {}),
    }


def main() -> int:
    args = parse_args()
    missing_optional_inputs: List[str] = []

    pre_privacy = load_json(args.pre_privacy_eval, required=True)
    post_subset = load_json(args.post_subset_privacy_eval, required=True)
    post_full = load_json(args.post_full_privacy_eval, required=False)
    pre_public = load_json(args.pre_public_eval, required=False)
    post_public = load_json(args.post_public_eval, required=False)

    optional_inputs = {
        "post_full_privacy_eval": args.post_full_privacy_eval,
        "pre_public_eval": args.pre_public_eval,
        "post_public_eval": args.post_public_eval,
    }
    for key, path_str in optional_inputs.items():
        if path_str and not Path(path_str).exists():
            missing_optional_inputs.append(path_str)

    summary = {
        "missing_optional_inputs": missing_optional_inputs,
        "pre": {
            "private": pick_private_metrics(pre_privacy),
            "public": pick_public_metrics(pre_public),
        },
        "post_rome_direct": {
            "edited_subset_private": pick_private_metrics(post_subset),
            "full_private": pick_private_metrics(post_full),
            "public": pick_public_metrics(post_public),
        },
    }

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    pre_private = summary["pre"]["private"] or {}
    post_subset_private = summary["post_rome_direct"]["edited_subset_private"] or {}
    post_public_metrics = summary["post_rome_direct"]["public"] or {}

    print(f"pre_target_exact_leak_rate: {pre_private.get('target_exact_leak_rate', 0.0):.4f}")
    print(f"post_subset_target_exact_leak_rate: {post_subset_private.get('target_exact_leak_rate', 0.0):.4f}")
    print(f"post_subset_safe_refusal_rate: {post_subset_private.get('safe_refusal_rate', 0.0):.4f}")
    if post_public_metrics:
        print(f"post_public_contains_acc: {post_public_metrics.get('public_contains_acc', 0.0):.4f}")
    if missing_optional_inputs:
        print(f"missing_optional_inputs: {len(missing_optional_inputs)}")
        for path_str in missing_optional_inputs:
            print(f"missing_optional_input: {path_str}")
    print(f"summary_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
