import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CAPE-Anchor mixed privacy/public requests.")
    parser.add_argument("--dataset", default="artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json", type=str)
    parser.add_argument("--private_eval", default="artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json", type=str)
    parser.add_argument("--output_dir", default="artifacts/run_20260622_v2_cape_anchor", type=str)
    parser.add_argument("--num_subjects", default=20, type=int)
    parser.add_argument("--privacy_per_subject", default=1, type=int)
    parser.add_argument("--anchors_per_subject", default=1, type=int)
    parser.add_argument("--target_new", default="I cannot provide private information.", type=str)
    return parser.parse_args()


def load_json(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def build_private_candidates(private_eval: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    by_person: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for detail in private_eval.get("details", []):
        if not (detail.get("target_exact_leak") or detail.get("target_regex_leak") or detail.get("sensitive_pattern")):
            continue
        by_person[detail.get("person_id")].append(detail)
    return by_person


def public_cases_by_person(dataset: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    by_person: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in dataset["flat_cases"]:
        if case.get("sensitivity") == "public" and case.get("public_type") == "same_subject_public":
            by_person[case["person_id"]].append(case)
    return by_person


def privacy_request(detail: Dict[str, Any], dataset_cases: Dict[str, Dict[str, Any]], target_new: str) -> Dict[str, Any] | None:
    case = dataset_cases.get(detail.get("case_id"))
    if not case:
        return None
    return {
        "case_id": case["case_id"],
        "person_id": case["person_id"],
        "request_type": "privacy_refusal",
        "prompt": case["edit_request"]["prompt"],
        "subject": case["edit_request"]["subject"],
        "target_new": target_new,
        "ground_truth": case["value"],
        "rephrase_prompt": case["edit_request"].get("rephrase_prompt"),
    }


def anchor_request(case: Dict[str, Any]) -> Dict[str, Any]:
    prompt = case.get("test_prompts", {}).get("direct") or case.get("inject_prompts", [{}])[0].get("prompt")
    return {
        "case_id": case["case_id"],
        "person_id": case["person_id"],
        "request_type": "public_anchor_retain",
        "prompt": prompt,
        "subject": case["name"],
        "target_new": case["value"],
        "ground_truth": case["value"],
        "rephrase_prompt": prompt,
    }


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CAPE-Anchor Selection Report",
        "",
        f"- selected_subjects: `{payload['selected_subjects']}`",
        f"- privacy_requests: `{payload['privacy_requests']}`",
        f"- public_anchor_requests: `{payload['public_anchor_requests']}`",
        f"- total_requests: `{payload['total_requests']}`",
        "",
        "CAPE-Anchor 只构造请求，不修改 ROME/MEMIT 底层，也不在本脚本中启动 GPU 编辑。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    dataset = load_json(args.dataset)
    private_eval = load_json(args.private_eval)
    cases = {case["case_id"]: case for case in dataset["flat_cases"]}
    private_by_person = build_private_candidates(private_eval)
    public_by_person = public_cases_by_person(dataset)
    selected_people = [p for p in sorted(private_by_person) if p in public_by_person][: args.num_subjects]
    requests: List[Dict[str, Any]] = []
    for person_id in selected_people:
        for detail in private_by_person[person_id][: args.privacy_per_subject]:
            req = privacy_request(detail, cases, args.target_new)
            if req:
                requests.append(req)
        for case in public_by_person[person_id][: args.anchors_per_subject]:
            requests.append(anchor_request(case))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    requests_path = output_dir / "cape_anchor_requests.json"
    report_json = output_dir / "cape_anchor_selection_report.json"
    payload = {
        "dataset": args.dataset,
        "private_eval": args.private_eval,
        "selected_subjects": len(selected_people),
        "privacy_requests": sum(1 for item in requests if item["request_type"] == "privacy_refusal"),
        "public_anchor_requests": sum(1 for item in requests if item["request_type"] == "public_anchor_retain"),
        "total_requests": len(requests),
        "requests_path": str(requests_path),
    }
    write_json(requests_path, {"requests": requests, **payload})
    write_json(report_json, payload)
    write_report(output_dir / "CAPE_ANCHOR_SELECTION_REPORT.md", payload)
    print(f"requests: {requests_path}")
    print(f"report: {output_dir / 'CAPE_ANCHOR_SELECTION_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
