import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 v2 merged / ROME direct-only / 三组 conservative PACE 对比表。")
    parser.add_argument("--pre_artifact_dir", required=True, type=str)
    parser.add_argument("--direct_artifact_dir", required=True, type=str)
    parser.add_argument("--target_only_artifact_dir", required=True, type=str)
    parser.add_argument("--max1_artifact_dir", required=True, type=str)
    parser.add_argument("--max2_artifact_dir", required=True, type=str)
    parser.add_argument("--output_path", required=True, type=str)
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_single(path: Path, pattern: str) -> Path:
    matches = sorted(path.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"在 {path} 下未唯一匹配到 {pattern}，实际匹配数={len(matches)}")
    return matches[0]


def get_public_type(metrics: Dict[str, Any], key: str) -> float:
    return float(metrics.get("by_public_type", {}).get(key, {}).get("contains_match_rate", 0.0))


def get_attack_type(metrics: Dict[str, Any], key: str) -> Dict[str, float]:
    node = metrics.get("by_attack_type", {}).get(key, {})
    return {
        "target_exact_leak_rate": float(node.get("target_exact_leak_rate", 0.0)),
        "target_regex_leak_rate": float(node.get("target_regex_leak_rate", 0.0)),
        "sensitive_pattern_rate": float(node.get("sensitive_pattern_rate", 0.0)),
        "safe_refusal_rate": float(node.get("safe_refusal_rate", 0.0)),
    }


def stage_row(
    name: str,
    private_metrics: Dict[str, Any],
    public_metrics: Dict[str, Any],
    request_counts: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    row = {
        "stage": name,
        "private": {
            "target_exact_leak_rate": float(private_metrics.get("target_exact_leak_rate", 0.0)),
            "target_regex_leak_rate": float(private_metrics.get("target_regex_leak_rate", 0.0)),
            "sensitive_pattern_rate": float(private_metrics.get("sensitive_pattern_rate", 0.0)),
            "safe_refusal_rate": float(private_metrics.get("safe_refusal_rate", 0.0)),
            "by_attack_type": {
                attack: get_attack_type(private_metrics, attack)
                for attack in ["direct", "paraphrase", "completion", "roleplay", "context"]
                if attack in private_metrics.get("by_attack_type", {})
            },
        },
        "public": {
            "contains_match_rate": float(public_metrics.get("public_contains_acc", 0.0)),
            "same_subject_public": get_public_type(public_metrics, "same_subject_public"),
            "same_relation_other_subject": get_public_type(public_metrics, "same_relation_other_subject"),
            "general_knowledge": get_public_type(public_metrics, "general_knowledge"),
        },
    }
    if request_counts is not None:
        row["requests"] = request_counts
    return row


def build_markdown_table(rows: List[Dict[str, Any]]) -> str:
    header = "| Stage | Private exact | Private regex | Sensitive | Refusal | Public contains | same_subject | same_relation | general_knowledge | Round2 req | Total req |"
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, sep]
    for row in rows:
        requests = row.get("requests", {})
        round2_req = requests.get("round2_num_requests", "-")
        total_req = requests.get("total_num_requests", "-")
        lines.append(
            "| {stage} | {exact:.4f} | {regex:.4f} | {sensitive:.4f} | {refusal:.4f} | {public_contains:.4f} | {same_subject:.4f} | {same_relation:.4f} | {general:.4f} | {round2_req} | {total_req} |".format(
                stage=row["stage"],
                exact=row["private"]["target_exact_leak_rate"],
                regex=row["private"]["target_regex_leak_rate"],
                sensitive=row["private"]["sensitive_pattern_rate"],
                refusal=row["private"]["safe_refusal_rate"],
                public_contains=row["public"]["contains_match_rate"],
                same_subject=row["public"]["same_subject_public"],
                same_relation=row["public"]["same_relation_other_subject"],
                general=row["public"]["general_knowledge"],
                round2_req=round2_req,
                total_req=total_req,
            )
        )
    return "\n".join(lines)


def load_pace_summary(artifact_dir: Path) -> Tuple[str, Dict[str, Any]]:
    summary_path = find_single(artifact_dir, "*_summary.json")
    return summary_path.stem.replace("_summary", ""), load_json(summary_path)


def main() -> int:
    args = parse_args()
    pre_dir = Path(args.pre_artifact_dir)
    direct_dir = Path(args.direct_artifact_dir)

    pre_privacy = load_json(pre_dir / "privacy_leakage_eval_merged_v2.json")
    pre_public = load_json(pre_dir / "public_retain_eval_merged_v2.json")
    direct_summary = load_json(find_single(direct_dir, "*_summary.json"))
    direct_requests_payload = load_json(find_single(direct_dir, "*_requests.json"))
    direct_request_summary = direct_requests_payload.get("request_summary", {})

    pace_rows: List[Dict[str, Any]] = []
    for path_str, stage_name in [
        (args.target_only_artifact_dir, "pace_target_only"),
        (args.max1_artifact_dir, "pace_max1_per_case"),
        (args.max2_artifact_dir, "pace_max2_per_person"),
    ]:
        _, pace_summary = load_pace_summary(Path(path_str))
        counts = pace_summary.get("request_counts", {})
        request_counts = {
            "round1_num_requests": counts.get("round1_direct", {}).get("num_requests", 0),
            "round2_num_requests": counts.get("round2_conservative", {}).get("num_requests", 0),
            "total_num_requests": counts.get("combined_total", {}).get("num_requests", 0),
        }
        pace_rows.append(
            stage_row(
                stage_name,
                pace_summary.get("pace_round2", {}).get("private", {}),
                pace_summary.get("pace_round2", {}).get("public", {}),
                request_counts,
            )
        )

    rows = [
        stage_row("merged_pre_edit", pre_privacy.get("overall", {}), {
            "public_contains_acc": pre_public.get("overall", {}).get("contains_match_rate", 0.0),
            "by_public_type": pre_public.get("by_public_type", {}),
        }),
        stage_row(
            "rome_direct_only",
            direct_summary.get("post_rome_direct", {}).get("full_private", {}),
            direct_summary.get("post_rome_direct", {}).get("public", {}),
            {
                "round1_num_requests": direct_request_summary.get("num_requests", direct_requests_payload.get("num_requests", 0)),
                "round2_num_requests": 0,
                "total_num_requests": direct_request_summary.get("num_requests", direct_requests_payload.get("num_requests", 0)),
            },
        ),
        *pace_rows,
    ]

    payload = {
        "rows": rows,
        "markdown_table": build_markdown_table(rows),
    }
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(payload["markdown_table"])
    print(f"comparison_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
