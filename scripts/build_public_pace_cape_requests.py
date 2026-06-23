import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public PACE/CAPE closed-loop request subsets.")
    parser.add_argument("--dataset_path", required=True, type=str)
    parser.add_argument("--per_case_results", required=True, type=str)
    parser.add_argument("--output_dir", required=True, type=str)
    parser.add_argument("--dataset_name", required=True, type=str)
    parser.add_argument("--model_name", required=True, type=str)
    parser.add_argument("--base_method", default="ROME", type=str)
    parser.add_argument("--max_round2_requests", default=None, type=int)
    parser.add_argument("--budget_fraction", default=0.2, type=float)
    parser.add_argument("--lambda_loc", default=0.5, type=float)
    parser.add_argument("--max_per_subject", default=1, type=int)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def flatten_numeric(value: Any) -> List[float]:
    if value is None:
        return []
    if isinstance(value, bool):
        return [float(value)]
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, list):
        out: List[float] = []
        for item in value:
            out.extend(flatten_numeric(item))
        return out
    return []


def get_nested(payload: Dict[str, Any], keys: Iterable[str]) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def avg_or_none(values: List[float]) -> Optional[float]:
    return mean(values) if values else None


def metric_profile(row: Dict[str, Any]) -> Dict[str, Any]:
    post = get_nested(row, ["metrics", "post"]) or {}
    rewrite = avg_or_none(flatten_numeric(post.get("rewrite_acc")))
    rephrase = avg_or_none(flatten_numeric(post.get("rephrase_acc")))
    locality_vals: List[float] = []
    locality = post.get("locality") or {}
    if isinstance(locality, dict):
        for value in locality.values():
            if isinstance(value, dict):
                for key, sub in value.items():
                    if key.endswith("_acc"):
                        locality_vals.extend(flatten_numeric(sub))
    locality_score = avg_or_none(locality_vals)
    rewrite_fail = rewrite is not None and rewrite < 1.0
    rephrase_fail = rephrase is not None and rephrase < 1.0
    locality_fail = locality_score is not None and locality_score < 1.0
    fail_risk = (1.0 - (rewrite if rewrite is not None else 1.0)) * 2.0
    fail_risk += 1.0 - (rephrase if rephrase is not None else 1.0)
    loc_risk = 1.0 - locality_score if locality_score is not None else 0.25
    return {
        "rewrite": rewrite,
        "rephrase": rephrase,
        "locality": locality_score,
        "rewrite_fail": rewrite_fail,
        "rephrase_fail": rephrase_fail,
        "locality_fail": locality_fail,
        "fail_risk": fail_risk,
        "loc_risk": loc_risk,
    }


def load_records(dataset_path: Path) -> List[Dict[str, Any]]:
    payload = read_json(dataset_path)
    if isinstance(payload, dict) and "records" in payload:
        return payload["records"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"unsupported dataset format: {dataset_path}")


def case_key(value: Any) -> str:
    return str(value)


def build_candidates(rows: List[Dict[str, Any]], records_by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = []
    for row in rows:
        cid = case_key(row.get("case_id"))
        request = row.get("request") or {}
        record = records_by_id.get(cid)
        if record is None and request.get("case_id") is not None:
            record = records_by_id.get(case_key(request.get("case_id")))
        if record is None:
            continue
        profile = metric_profile(row)
        if not profile["rewrite_fail"] and not profile["rephrase_fail"]:
            continue
        subject = record.get("subject") or request.get("subject") or ""
        relation = record.get("relation") or record.get("requested_rewrite", {}).get("relation_id") or ""
        candidates.append(
            {
                "case_id": cid,
                "subject": subject,
                "relation": relation,
                "record": record,
                "profile": profile,
                "pace_score": profile["fail_risk"],
            }
        )
    candidates.sort(
        key=lambda item: (
            bool(item["profile"]["rewrite_fail"]),
            bool(item["profile"]["rephrase_fail"]),
            item["pace_score"],
        ),
        reverse=True,
    )
    return candidates


def cape_select(
    candidates: List[Dict[str, Any]],
    budget: int,
    lambda_loc: float,
    max_per_subject: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    selected = []
    counts: Dict[str, int] = {}
    stats = {
        "locality_risk_skipped": 0,
        "subject_budget_skipped": 0,
        "missing_locality_risk_count": 0,
    }
    scored = []
    for item in candidates:
        profile = item["profile"]
        if profile["locality"] is None:
            stats["missing_locality_risk_count"] += 1
        if profile["locality_fail"]:
            stats["locality_risk_skipped"] += 1
            continue
        score = profile["fail_risk"] - lambda_loc * profile["loc_risk"]
        scored.append((score, item))
    scored.sort(
        key=lambda pair: (
            pair[0],
            bool(pair[1]["profile"]["rewrite_fail"]),
            bool(pair[1]["profile"]["rephrase_fail"]),
        ),
        reverse=True,
    )
    for _, item in scored:
        key = item["subject"] or item["relation"] or item["case_id"]
        if counts.get(key, 0) >= max_per_subject:
            stats["subject_budget_skipped"] += 1
            continue
        selected.append(item)
        counts[key] = counts.get(key, 0) + 1
        if len(selected) >= budget:
            break
    return selected, stats


def package_records(selected: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    records = []
    for item in selected:
        record = dict(item["record"])
        record["closed_loop_strategy"] = strategy
        record["closed_loop_source_case_id"] = item["case_id"]
        record["closed_loop_fail_profile"] = item["profile"]
        records.append(record)
    return records


def write_markdown(path: Path, report: Dict[str, Any]) -> None:
    lines = [
        "# Public PACE/CAPE Selection Report",
        "",
        f"- dataset: `{report['dataset_name']}`",
        f"- model: `{report['model_name']}`",
        f"- base_method: `{report['base_method']}`",
        f"- total_records: `{report['total_records']}`",
        f"- candidates: `{report['candidate_count']}`",
        f"- pace_selected: `{report['pace_selected_count']}`",
        f"- cape_selected: `{report['cape_selected_count']}`",
        f"- budget: `{report['budget']}`",
        f"- rewrite_fail_candidates: `{report['rewrite_fail_candidates']}`",
        f"- rephrase_fail_candidates: `{report['rephrase_fail_candidates']}`",
        f"- locality_risk_skipped: `{report['cape_stats']['locality_risk_skipped']}`",
        f"- subject_budget_skipped: `{report['cape_stats']['subject_budget_skipped']}`",
        f"- missing_locality_risk_count: `{report['cape_stats']['missing_locality_risk_count']}`",
        "",
        "## Selected Examples",
        "",
        "| strategy | case_id | subject | rewrite | rephrase | locality |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for strategy in ["PACE_EDIT", "CAPE_EDIT"]:
        for item in report["selected_examples"].get(strategy, [])[:20]:
            profile = item["profile"]
            def fmt(x: Any) -> str:
                return "" if x is None else f"{x:.4f}" if isinstance(x, float) else str(x)
            lines.append(
                f"| {strategy} | {item['case_id']} | {item['subject']} | {fmt(profile.get('rewrite'))} | {fmt(profile.get('rephrase'))} | {fmt(profile.get('locality'))} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset_path)
    per_case_path = Path(args.per_case_results)
    output_dir = Path(args.output_dir)
    records = load_records(dataset_path)
    records_by_id = {case_key(row.get("case_id")): row for row in records}
    rows = read_jsonl(per_case_path)
    budget = args.max_round2_requests
    if budget is None:
        budget = min(100, max(1, int(len(records) * args.budget_fraction)))
    candidates = build_candidates(rows, records_by_id)
    pace_selected = candidates[:budget]
    cape_selected, cape_stats = cape_select(candidates, budget, args.lambda_loc, args.max_per_subject)

    pace_records = package_records(pace_selected, "PACE_EDIT")
    cape_records = package_records(cape_selected, "CAPE_EDIT")
    pace_path = output_dir / "pace_round2_dataset.json"
    cape_path = output_dir / "cape_round2_dataset.json"
    write_json(pace_path, {"dataset": args.dataset_name, "records": pace_records})
    write_json(cape_path, {"dataset": args.dataset_name, "records": cape_records})

    report = {
        "dataset_name": args.dataset_name,
        "model_name": args.model_name,
        "base_method": args.base_method,
        "dataset_path": str(dataset_path),
        "per_case_results": str(per_case_path),
        "total_records": len(records),
        "candidate_count": len(candidates),
        "budget": budget,
        "pace_selected_count": len(pace_selected),
        "cape_selected_count": len(cape_selected),
        "rewrite_fail_candidates": sum(1 for item in candidates if item["profile"]["rewrite_fail"]),
        "rephrase_fail_candidates": sum(1 for item in candidates if item["profile"]["rephrase_fail"]),
        "cape_stats": cape_stats,
        "pace_dataset": str(pace_path),
        "cape_dataset": str(cape_path),
        "selected_examples": {
            "PACE_EDIT": [
                {k: v for k, v in item.items() if k != "record"} for item in pace_selected[:50]
            ],
            "CAPE_EDIT": [
                {k: v for k, v in item.items() if k != "record"} for item in cape_selected[:50]
            ],
        },
    }
    write_json(output_dir / "selection_report.json", report)
    write_markdown(output_dir / "PACE_CAPE_PUBLIC_SELECTION_REPORT.md", report)
    print(f"candidate_count: {len(candidates)}")
    print(f"pace_selected: {len(pace_selected)} -> {pace_path}")
    print(f"cape_selected: {len(cape_selected)} -> {cape_path}")
    print(f"selection_report: {output_dir / 'selection_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
