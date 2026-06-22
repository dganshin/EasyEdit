import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_REFUSAL = "I cannot provide private information."
DEFAULT_ATTACK_PRIORITY = ["completion", "context", "roleplay", "paraphrase", "direct"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CAPE-v0 round2 re-edit requests from ROME residual leakage.")
    parser.add_argument("--private_eval", required=True, type=str, help="ROME direct-only full private eval json")
    parser.add_argument("--public_eval", required=True, type=str, help="ROME direct-only public retain eval json")
    parser.add_argument("--dataset", required=True, type=str, help="v2 synthetic dataset json")
    parser.add_argument("--base_requests", required=True, type=str, help="Original ROME direct requests json")
    parser.add_argument("--output_path", required=True, type=str, help="CAPE round2 requests output json")
    parser.add_argument("--selection_report_json", required=True, type=str, help="Selection report json output")
    parser.add_argument("--selection_report_md", required=True, type=str, help="Selection report markdown output")
    parser.add_argument("--target_new", default=DEFAULT_REFUSAL, type=str, help="Unified refusal target")
    parser.add_argument("--tau", default=0.5, type=float, help="Public-anchor blocking threshold")
    parser.add_argument("--max_requests_per_person", default=1, type=int, help="Per-person round2 budget")
    parser.add_argument(
        "--attack_priority",
        default=",".join(DEFAULT_ATTACK_PRIORITY),
        type=str,
        help="Comma-separated attack priority, earlier means higher priority",
    )
    return parser.parse_args()


def load_json(path_str: str) -> Dict[str, Any]:
    with Path(path_str).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def index_private_details(private_eval: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for row in private_eval.get("details", []):
        key = str(row.get("base_prediction_id") or row.get("prediction_id"))
        index[key] = row
    return index


def index_dataset_cases(dataset: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(row["case_id"]): row for row in dataset.get("flat_cases", [])}


def index_base_requests(base_requests_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(row["case_id"]): row for row in base_requests_payload.get("requests", [])}


def compute_same_subject_public_rates(public_eval: Dict[str, Any], dataset_index: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in public_eval.get("details", []):
        case_id = str(row.get("case_id") or "")
        meta = dataset_index.get(case_id)
        if not meta:
            continue
        if meta.get("public_type") != "same_subject_public":
            continue
        person_id = str(meta.get("person_id") or "")
        if not person_id:
            continue
        bucket[person_id].append(
            {
                "case_id": case_id,
                "attribute": meta.get("attribute"),
                "contains_match": bool(row.get("contains_match")),
                "exact_match": bool(row.get("exact_match")),
            }
        )

    rates: Dict[str, Dict[str, Any]] = {}
    for person_id, rows in bucket.items():
        contains_count = sum(1 for row in rows if row["contains_match"])
        exact_count = sum(1 for row in rows if row["exact_match"])
        rates[person_id] = {
            "same_subject_public_prompt_count": len(rows),
            "same_subject_public_contains_count": contains_count,
            "same_subject_public_exact_count": exact_count,
            "same_subject_public_contains_rate": contains_count / len(rows) if rows else 0.0,
            "same_subject_public_exact_rate": exact_count / len(rows) if rows else 0.0,
            "case_ids": sorted({row["case_id"] for row in rows}),
            "attributes": sorted({str(row["attribute"]) for row in rows}),
        }
    return rates


def attack_priority_map(raw_value: str) -> Dict[str, int]:
    order = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not order:
        order = list(DEFAULT_ATTACK_PRIORITY)
    return {name: idx for idx, name in enumerate(order)}


def failure_priority(row: Dict[str, Any]) -> Tuple[int, str]:
    if row.get("any_target_exact_leak"):
        return 0, "target_exact_or_value_contains"
    if row.get("any_target_regex_leak"):
        return 1, "target_regex"
    if row.get("any_sensitive_pattern"):
        return 2, "sensitive_pattern"
    return 99, "not_candidate"


def build_candidate_rows(
    private_eval: Dict[str, Any],
    detail_index: Dict[str, Dict[str, Any]],
    public_rates: Dict[str, Dict[str, Any]],
    dataset_index: Dict[str, Dict[str, Any]],
    base_request_index: Dict[str, Dict[str, Any]],
    attack_priority: Dict[str, int],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for row in private_eval.get("by_expected_row", []):
        pri_rank, pri_label = failure_priority(row)
        if pri_rank >= 99:
            continue
        base_prediction_id = str(row.get("base_prediction_id") or row.get("prediction_id"))
        detail = detail_index.get(base_prediction_id)
        if not detail:
            continue
        case_id = str(detail["case_id"])
        person_id = str(detail.get("person_id") or "")
        dataset_case = dataset_index.get(case_id, {})
        base_request = base_request_index.get(case_id, {})
        attack_type = str(detail.get("attack_type") or row.get("attack_type") or "")
        public_rate_info = public_rates.get(person_id, {})
        candidates.append(
            {
                "base_prediction_id": base_prediction_id,
                "prediction_id": str(detail.get("prediction_id") or base_prediction_id),
                "case_id": case_id,
                "person_id": person_id,
                "name": detail.get("name") or dataset_case.get("name"),
                "attribute": detail.get("attribute") or dataset_case.get("attribute"),
                "privacy_type": detail.get("privacy_type") or dataset_case.get("privacy_type"),
                "attack_type": attack_type,
                "attack_template_id": detail.get("attack_template_id") or row.get("attack_template_id"),
                "prompt": detail.get("prompt"),
                "ground_truth": detail.get("value"),
                "subject": detail.get("name") or dataset_case.get("name"),
                "rephrase_prompt": base_request.get("rephrase_prompt") or dataset_case.get("edit_request", {}).get("rephrase_prompt"),
                "locality_prompt": base_request.get("locality_prompt") or dataset_case.get("edit_request", {}).get("locality_prompt"),
                "locality_ground_truth": base_request.get("locality_ground_truth") or dataset_case.get("edit_request", {}).get("locality_ground_truth"),
                "value": detail.get("value"),
                "test_prompt_rows": dataset_case.get("test_prompt_rows"),
                "failure_priority_rank": pri_rank,
                "failure_priority_label": pri_label,
                "failure_reason": {
                    "target_exact_leak": bool(row.get("any_target_exact_leak")),
                    "target_regex_leak": bool(row.get("any_target_regex_leak")),
                    "sensitive_pattern": bool(row.get("any_sensitive_pattern")),
                    "safe_refusal": bool(row.get("any_safe_refusal")),
                },
                "same_subject_public_contains_rate": public_rate_info.get("same_subject_public_contains_rate"),
                "same_subject_public_exact_rate": public_rate_info.get("same_subject_public_exact_rate"),
                "same_subject_public_prompt_count": public_rate_info.get("same_subject_public_prompt_count"),
                "round1_selected_case": case_id in base_request_index,
                "attack_priority_rank": attack_priority.get(attack_type, len(attack_priority) + 100),
            }
        )
    candidates.sort(
        key=lambda item: (
            item["failure_priority_rank"],
            item["attack_priority_rank"],
            str(item["person_id"]),
            str(item["case_id"]),
            str(item["attack_template_id"]),
        )
    )
    return candidates


def build_request_payload(candidate: Dict[str, Any], target_new: str) -> Dict[str, Any]:
    return {
        "source_prediction_id": candidate["prediction_id"],
        "base_prediction_id": candidate["base_prediction_id"],
        "case_id": candidate["case_id"],
        "person_id": candidate["person_id"],
        "name": candidate["name"],
        "attribute": candidate["attribute"],
        "privacy_type": candidate["privacy_type"],
        "attack_type": candidate["attack_type"],
        "attack_template_id": candidate["attack_template_id"],
        "subject": candidate["subject"],
        "prompt": candidate["prompt"],
        "ground_truth": candidate["ground_truth"],
        "target_new": target_new,
        "rephrase_prompt": candidate.get("rephrase_prompt"),
        "locality_prompt": candidate.get("locality_prompt"),
        "locality_ground_truth": candidate.get("locality_ground_truth"),
        "test_prompt_rows": candidate.get("test_prompt_rows"),
        "value": candidate.get("value"),
        "failure_priority": candidate["failure_priority_label"],
        "failure_reason": candidate["failure_reason"],
        "same_subject_public_contains_rate": candidate.get("same_subject_public_contains_rate"),
        "same_subject_public_exact_rate": candidate.get("same_subject_public_exact_rate"),
        "round1_selected_case": candidate.get("round1_selected_case", False),
    }


def select_requests(
    candidates: List[Dict[str, Any]],
    *,
    tau: float,
    max_requests_per_person: int,
    target_new: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    person_counts: Counter[str] = Counter()
    skipped_public_anchor = 0
    skipped_budget = 0
    skipped_public_anchor_subjects: set[str] = set()
    skipped_budget_subjects: set[str] = set()
    blocked_examples: List[Dict[str, Any]] = []
    budget_examples: List[Dict[str, Any]] = []

    for candidate in candidates:
        person_id = str(candidate.get("person_id") or "")
        subject = str(candidate.get("subject") or person_id or "unknown")
        contains_rate = candidate.get("same_subject_public_contains_rate")
        if contains_rate is not None and contains_rate < tau:
            skipped_public_anchor += 1
            skipped_public_anchor_subjects.add(subject)
            if len(blocked_examples) < 10:
                blocked_examples.append(
                    {
                        "subject": subject,
                        "person_id": person_id,
                        "case_id": candidate["case_id"],
                        "attack_type": candidate["attack_type"],
                        "failure_priority": candidate["failure_priority_label"],
                        "same_subject_public_contains_rate": contains_rate,
                    }
                )
            continue
        if person_id and person_counts[person_id] >= max_requests_per_person:
            skipped_budget += 1
            skipped_budget_subjects.add(subject)
            if len(budget_examples) < 10:
                budget_examples.append(
                    {
                        "subject": subject,
                        "person_id": person_id,
                        "case_id": candidate["case_id"],
                        "attack_type": candidate["attack_type"],
                        "failure_priority": candidate["failure_priority_label"],
                        "same_subject_public_contains_rate": contains_rate,
                    }
                )
            continue
        selected.append(build_request_payload(candidate, target_new))
        if person_id:
            person_counts[person_id] += 1

    report = {
        "num_candidates": len(candidates),
        "skipped_public_anchor": skipped_public_anchor,
        "skipped_budget": skipped_budget,
        "num_selected": len(selected),
        "num_selected_people": len({row["person_id"] for row in selected if row.get("person_id")}),
        "blocked_subjects_due_to_public_anchor": sorted(skipped_public_anchor_subjects),
        "budget_limited_subjects": sorted(skipped_budget_subjects),
        "blocked_examples": blocked_examples,
        "budget_examples": budget_examples,
    }
    return selected, report


def summarize_requests(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_attack_type = Counter(str(item.get("attack_type") or "unknown") for item in requests)
    by_person = Counter(str(item.get("person_id") or "unknown") for item in requests)
    by_failure_priority = Counter(str(item.get("failure_priority") or "unknown") for item in requests)
    subject_rows = []
    for subject, count in Counter(str(item.get("subject") or "unknown") for item in requests).most_common():
        example = next(item for item in requests if str(item.get("subject") or "unknown") == subject)
        subject_rows.append(
            {
                "subject": subject,
                "person_id": example.get("person_id"),
                "count": count,
                "public_contains_rate": example.get("same_subject_public_contains_rate"),
            }
        )
    return {
        "num_requests": len(requests),
        "num_people": len([key for key in by_person if key and key != "unknown"]),
        "by_attack_type": dict(sorted(by_attack_type.items())),
        "by_failure_priority": dict(sorted(by_failure_priority.items())),
        "max_requests_per_person_observed": max((value for key, value in by_person.items() if key and key != "unknown"), default=0),
        "subjects": subject_rows,
    }


def build_selection_report(
    *,
    args: argparse.Namespace,
    private_eval: Dict[str, Any],
    public_rates: Dict[str, Dict[str, Any]],
    base_requests_payload: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    selected_requests: List[Dict[str, Any]],
    selection_counters: Dict[str, Any],
) -> Dict[str, Any]:
    selected_summary = summarize_requests(selected_requests)
    candidate_by_attack_type = Counter(str(item.get("attack_type") or "unknown") for item in candidates)
    candidate_by_failure_priority = Counter(str(item.get("failure_priority_label") or "unknown") for item in candidates)
    selected_people = {item["person_id"] for item in selected_requests if item.get("person_id")}
    public_anchor_distribution = {
        "num_people_with_public_anchor": len(public_rates),
        "num_people_above_or_equal_tau": sum(1 for row in public_rates.values() if row["same_subject_public_contains_rate"] >= args.tau),
        "num_people_below_tau": sum(1 for row in public_rates.values() if row["same_subject_public_contains_rate"] < args.tau),
    }
    examples = selected_requests[:10]
    return {
        "config": {
            "private_eval": args.private_eval,
            "public_eval": args.public_eval,
            "dataset": args.dataset,
            "base_requests": args.base_requests,
            "target_new": args.target_new,
            "tau": args.tau,
            "max_requests_per_person": args.max_requests_per_person,
            "attack_priority": [item.strip() for item in args.attack_priority.split(",") if item.strip()],
        },
        "source_summary": {
            "rome_full_private_overall": private_eval.get("overall", {}),
            "rome_round1_requests": base_requests_payload.get("request_summary") or {"num_requests": base_requests_payload.get("num_requests")},
        },
        "public_anchor_distribution": public_anchor_distribution,
        "candidate_summary": {
            "num_candidates": len(candidates),
            "by_attack_type": dict(sorted(candidate_by_attack_type.items())),
            "by_failure_priority": dict(sorted(candidate_by_failure_priority.items())),
        },
        "selection_summary": {
            **selection_counters,
            **selected_summary,
            "selected_people": sorted(selected_people),
        },
        "selected_examples": examples,
    }


def write_markdown_report(report: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# CAPE SELECTION REPORT",
        "",
        "## 1. Configuration",
        "",
        f"- tau = {report['config']['tau']}",
        f"- max_requests_per_person = {report['config']['max_requests_per_person']}",
        f"- attack_priority = {', '.join(report['config']['attack_priority'])}",
        "",
        "## 2. Candidate pool",
        "",
        f"- residual leakage candidates = {report['candidate_summary']['num_candidates']}",
        f"- by failure priority = {json.dumps(report['candidate_summary']['by_failure_priority'], ensure_ascii=False)}",
        f"- by attack type = {json.dumps(report['candidate_summary']['by_attack_type'], ensure_ascii=False)}",
        "",
        "## 3. Public-anchor blocking",
        "",
        f"- people with same-subject public anchors = {report['public_anchor_distribution']['num_people_with_public_anchor']}",
        f"- people with anchor contains >= tau = {report['public_anchor_distribution']['num_people_above_or_equal_tau']}",
        f"- people with anchor contains < tau = {report['public_anchor_distribution']['num_people_below_tau']}",
        f"- skipped requests due to public-anchor blocking = {report['selection_summary']['skipped_public_anchor']}",
        f"- blocked subjects = {len(report['selection_summary']['blocked_subjects_due_to_public_anchor'])}",
        "",
        "## 4. Budget control",
        "",
        f"- skipped requests due to per-person budget = {report['selection_summary']['skipped_budget']}",
        f"- budget-limited subjects = {len(report['selection_summary']['budget_limited_subjects'])}",
        "",
        "## 5. Final selection",
        "",
        f"- selected requests = {report['selection_summary']['num_selected']}",
        f"- selected people = {report['selection_summary']['num_selected_people']}",
        f"- by attack type = {json.dumps(report['selection_summary']['by_attack_type'], ensure_ascii=False)}",
        f"- by failure priority = {json.dumps(report['selection_summary']['by_failure_priority'], ensure_ascii=False)}",
        "",
        "## 6. Per-subject selection counts",
        "",
    ]
    for row in report["selection_summary"]["subjects"][:20]:
        lines.append(
            f"- {row['subject']} ({row['person_id']}): count={row['count']}, public_contains_rate={row['public_contains_rate']}"
        )
    lines.extend([
        "",
        "## 7. Example selected requests",
        "",
    ])
    for row in report["selected_examples"][:8]:
        lines.extend(
            [
                f"- subject: {row.get('subject')}",
                f"  - case_id: {row.get('case_id')}",
                f"  - attack_type: {row.get('attack_type')}",
                f"  - failure_priority: {row.get('failure_priority')}",
                f"  - public_contains_rate: {row.get('same_subject_public_contains_rate')}",
                f"  - prompt: {row.get('prompt')}",
            ]
        )
    lines.extend([
        "",
        "## 8. Notes",
        "",
        "- CAPE-v0 only changes request selection. It does not modify EasyEdit, ROME, or MEMIT core update rules.",
        "- Current selection still mines residual leakage from the same evaluation universe, so held-out evaluation remains a limitation to report explicitly.",
        "",
    ])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    private_eval = load_json(args.private_eval)
    public_eval = load_json(args.public_eval)
    dataset = load_json(args.dataset)
    base_requests_payload = load_json(args.base_requests)

    detail_index = index_private_details(private_eval)
    dataset_index = index_dataset_cases(dataset)
    base_request_index = index_base_requests(base_requests_payload)
    public_rates = compute_same_subject_public_rates(public_eval, dataset_index)
    attack_priority = attack_priority_map(args.attack_priority)
    candidates = build_candidate_rows(
        private_eval,
        detail_index,
        public_rates,
        dataset_index,
        base_request_index,
        attack_priority,
    )
    selected_requests, selection_counters = select_requests(
        candidates,
        tau=args.tau,
        max_requests_per_person=args.max_requests_per_person,
        target_new=args.target_new,
    )
    request_summary = summarize_requests(selected_requests)
    requests_payload = {
        "request_source": "cape_v0",
        "private_eval_path": args.private_eval,
        "public_eval_path": args.public_eval,
        "dataset_path": args.dataset,
        "base_requests_path": args.base_requests,
        "target_new": args.target_new,
        "tau": args.tau,
        "max_requests_per_person": args.max_requests_per_person,
        "attack_priority": [item.strip() for item in args.attack_priority.split(",") if item.strip()],
        "num_requests": len(selected_requests),
        "request_summary": request_summary,
        "requests": selected_requests,
    }
    report_payload = build_selection_report(
        args=args,
        private_eval=private_eval,
        public_rates=public_rates,
        base_requests_payload=base_requests_payload,
        candidates=candidates,
        selected_requests=selected_requests,
        selection_counters=selection_counters,
    )

    output_path = Path(args.output_path)
    report_json_path = Path(args.selection_report_json)
    report_md_path = Path(args.selection_report_md)
    write_json(output_path, requests_payload)
    write_json(report_json_path, report_payload)
    write_markdown_report(report_payload, report_md_path)

    print(f"cape_candidates: {len(candidates)}")
    print(f"cape_selected: {len(selected_requests)}")
    print(f"cape_skipped_public_anchor: {selection_counters['skipped_public_anchor']}")
    print(f"cape_skipped_budget: {selection_counters['skipped_budget']}")
    print(f"output_json: {output_path}")
    print(f"report_json: {report_json_path}")
    print(f"report_md: {report_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
