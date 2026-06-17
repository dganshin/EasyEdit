import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


RUNS = [
    {
        "method": "merged leakage model",
        "run_name": "v2_lora_mlp_only",
        "artifact_dir": "artifacts/run_20260615_v2_lora_mlp_only",
        "private_eval": "privacy_leakage_eval_merged_v2.json",
        "public_eval": "public_retain_eval_merged_v2.json",
        "edit_requests": None,
        "round2_requests": None,
        "note": "pre-edit merged leakage model",
    },
    {
        "method": "ROME direct-only",
        "run_name": "v2_rome_direct",
        "artifact_dir": "artifacts/run_20260615_v2_rome_direct",
        "private_eval": "privacy_leakage_eval_v2_rome_direct_full.json",
        "public_eval": "public_retain_eval_v2_rome_direct.json",
        "edit_requests": "v2_rome_direct_requests.json",
        "round2_requests": None,
        "note": "20 people / 40 direct private edit requests",
    },
    {
        "method": "PACE target_only",
        "run_name": "v2_pace_target_only",
        "artifact_dir": "artifacts/run_20260615_v2_pace_target_only",
        "private_eval": "privacy_leakage_eval_v2_pace_target_only_full.json",
        "public_eval": "public_retain_eval_v2_pace_target_only.json",
        "edit_requests": "v2_pace_target_only_requests.json",
        "round2_requests": "v2_pace_target_only_round2_requests.json",
        "note": "Round2 selected target leak failures only",
    },
    {
        "method": "PACE max1_per_case",
        "run_name": "v2_pace_max1_per_case",
        "artifact_dir": "artifacts/run_20260615_v2_pace_max1_per_case",
        "private_eval": "privacy_leakage_eval_v2_pace_max1_per_case_full.json",
        "public_eval": "public_retain_eval_v2_pace_max1_per_case.json",
        "edit_requests": "v2_pace_max1_per_case_requests.json",
        "round2_requests": "v2_pace_max1_per_case_round2_requests.json",
        "note": "at most one Round2 request per case",
    },
    {
        "method": "PACE max2_per_person",
        "run_name": "v2_pace_max2_per_person",
        "artifact_dir": "artifacts/run_20260615_v2_pace_max2_per_person",
        "private_eval": "privacy_leakage_eval_v2_pace_max2_per_person_full.json",
        "public_eval": "public_retain_eval_v2_pace_max2_per_person.json",
        "edit_requests": "v2_pace_max2_per_person_requests.json",
        "round2_requests": "v2_pace_max2_per_person_round2_requests.json",
        "note": "at most two Round2 requests per person",
    },
    {
        "method": "MEMIT direct-only",
        "run_name": "v2_memit_direct",
        "artifact_dir": "artifacts/run_20260617_v2_memit_direct",
        "private_eval": "privacy_leakage_eval_v2_memit_direct_full.json",
        "public_eval": "public_retain_eval_v2_memit_direct.json",
        "edit_requests": "v2_rome_direct_requests.json",
        "round2_requests": None,
        "note": "planned; same 40 requests as ROME direct-only",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare v2 editing methods with nullable missing runs.")
    parser.add_argument("--output_dir", default="artifacts/run_20260617_v2_method_comparison")
    parser.add_argument("--json_out", default=None)
    parser.add_argument("--md_out", default=None)
    return parser.parse_args()


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def request_count(path: Optional[Path]) -> Optional[int]:
    if path is None or not path.exists():
        return None
    payload = load_json(path)
    if payload is None:
        return None
    if isinstance(payload, list):
        return len(payload)
    requests = payload.get("requests")
    if isinstance(requests, list):
        return len(requests)
    if isinstance(payload.get("num_requests"), int):
        return payload["num_requests"]
    return None


def pick_private(payload: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    if not payload:
        return {
            "private_exact": None,
            "private_regex": None,
            "sensitive_pattern": None,
            "refusal": None,
        }
    grouped = payload.get("grouped_any_metrics") or {}
    overall = payload.get("overall") or {}
    return {
        "private_exact": grouped.get("any_target_exact_leak_rate", overall.get("target_exact_leak_rate")),
        "private_regex": grouped.get("any_target_regex_leak_rate", overall.get("target_regex_leak_rate")),
        "sensitive_pattern": grouped.get("any_sensitive_pattern_rate", overall.get("sensitive_pattern_rate")),
        "refusal": grouped.get("any_safe_refusal_rate", overall.get("safe_refusal_rate")),
    }


def pick_public(payload: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    if not payload:
        return {
            "public_overall_contains": None,
            "same_subject_public": None,
            "same_relation_other_subject": None,
            "general_knowledge": None,
        }
    overall = payload.get("overall") or {}
    by_type = payload.get("by_public_type") or {}
    return {
        "public_overall_contains": overall.get("contains_match_rate"),
        "same_subject_public": (by_type.get("same_subject_public") or {}).get("contains_match_rate"),
        "same_relation_other_subject": (by_type.get("same_relation_other_subject") or {}).get("contains_match_rate"),
        "general_knowledge": (by_type.get("general_knowledge") or {}).get("contains_match_rate"),
    }


def fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def build_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for run in RUNS:
        artifact_dir = Path(run["artifact_dir"])
        private_eval = load_json(artifact_dir / run["private_eval"])
        public_eval = load_json(artifact_dir / run["public_eval"])
        edit_requests = request_count(artifact_dir / run["edit_requests"]) if run["edit_requests"] else None
        round2_requests = request_count(artifact_dir / run["round2_requests"]) if run["round2_requests"] else None
        row = {
            "method": run["method"],
            "run_name": run["run_name"],
            "artifact_dir": str(artifact_dir),
            "status": "available" if private_eval and public_eval else "missing",
            **pick_private(private_eval),
            **pick_public(public_eval),
            "edit_requests": edit_requests,
            "round2_requests": round2_requests,
            "note": run["note"],
        }
        rows.append(row)
    return rows


def markdown(rows: List[Dict[str, Any]]) -> str:
    header = "| method | run name | private exact | private regex | sensitive pattern | refusal | public overall contains | same_subject_public | same_relation_other_subject | general_knowledge | edit requests | Round2 requests | note |"
    sep = "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"
    lines = [header, sep]
    for row in rows:
        lines.append(
            "| {method} | {run_name} | {private_exact} | {private_regex} | {sensitive_pattern} | {refusal} | {public_overall_contains} | {same_subject_public} | {same_relation_other_subject} | {general_knowledge} | {edit_requests} | {round2_requests} | {note} |".format(
                **{key: fmt(value) for key, value in row.items()}
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_out = Path(args.json_out) if args.json_out else output_dir / "v2_method_comparison.json"
    md_out = Path(args.md_out) if args.md_out else output_dir / "v2_method_comparison.md"
    rows = build_rows()
    table = markdown(rows)
    payload = {
        "rows": rows,
        "markdown_table": table,
    }
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(table, encoding="utf-8")
    print(table)
    print(f"comparison_json: {json_out}")
    print(f"comparison_md: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
