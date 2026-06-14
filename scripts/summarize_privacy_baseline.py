import argparse
import json
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 privacy leakage 与 public retain 结果。")
    parser.add_argument("--privacy_eval", required=True, type=str, help="privacy leakage eval json 路径")
    parser.add_argument("--public_eval", required=True, type=str, help="public retain eval json 路径")
    parser.add_argument("--output_path", default=None, type=str, help="汇总结果输出路径")
    return parser.parse_args()


def load_json(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    args = parse_args()
    privacy_eval = load_json(args.privacy_eval)
    public_eval = load_json(args.public_eval)

    summary = {
        "privacy_eval_path": args.privacy_eval,
        "public_eval_path": args.public_eval,
        "private": {
            "num_expected_attack_prompts": privacy_eval.get("num_expected_attack_prompts", 0),
            "num_evaluated_predictions": privacy_eval.get("num_evaluated_predictions", 0),
            "grouped_any_metrics": privacy_eval.get("grouped_any_metrics", {}),
            "target_exact_leak_rate": privacy_eval.get("overall", {}).get("target_exact_leak_rate", 0.0),
            "target_regex_leak_rate": privacy_eval.get("overall", {}).get("target_regex_leak_rate", 0.0),
            "phone_pattern_rate": privacy_eval.get("overall", {}).get("phone_pattern_rate", 0.0),
            "email_pattern_rate": privacy_eval.get("overall", {}).get("email_pattern_rate", 0.0),
            "sensitive_pattern_rate": privacy_eval.get("overall", {}).get("sensitive_pattern_rate", 0.0),
            "safe_refusal_rate": privacy_eval.get("overall", {}).get("safe_refusal_rate", 0.0),
            "by_attack_type": privacy_eval.get("by_attack_type", {}),
            "by_attack_template": privacy_eval.get("by_attack_template", {}),
        },
        "public": {
            "num_expected_public_prompts": public_eval.get("num_expected_public_prompts", 0),
            "num_evaluated_predictions": public_eval.get("num_evaluated_predictions", 0),
            "public_exact_acc": public_eval.get("overall", {}).get("exact_match_rate", 0.0),
            "public_contains_acc": public_eval.get("overall", {}).get("contains_match_rate", 0.0),
            "by_attribute": public_eval.get("by_attribute", {}),
        },
    }

    output_path = Path(args.output_path) if args.output_path else Path(args.privacy_eval).with_name("privacy_baseline_summary.json")
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(f"target_exact_leak_rate: {summary['private']['target_exact_leak_rate']:.4f}")
    print(f"target_regex_leak_rate: {summary['private']['target_regex_leak_rate']:.4f}")
    print(f"sensitive_pattern_rate: {summary['private']['sensitive_pattern_rate']:.4f}")
    print(f"safe_refusal_rate: {summary['private']['safe_refusal_rate']:.4f}")
    print(f"public_exact_acc: {summary['public']['public_exact_acc']:.4f}")
    print(f"public_contains_acc: {summary['public']['public_contains_acc']:.4f}")
    print(f"summary_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
