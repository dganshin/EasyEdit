import argparse
import json
import random
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public PACE/CAPE closed-loop request datasets.")
    parser.add_argument("--dataset_path", required=True, type=str)
    parser.add_argument("--per_case_results", required=True, type=str)
    parser.add_argument("--output_dir", required=True, type=str)
    parser.add_argument("--dataset_name", required=True, type=str)
    parser.add_argument("--model_name", required=True, type=str)
    parser.add_argument("--base_method", default="ROME", type=str)
    parser.add_argument("--max_round2_requests", default=None, type=int)
    parser.add_argument("--budget_fraction", default=0.2, type=float)
    parser.add_argument("--lambda_loc", default=0.5, type=float)
    parser.add_argument("--max_per_subject_or_relation", default=1, type=int)
    parser.add_argument("--selection_split_ratio", default=0.6, type=float)
    parser.add_argument("--heldout_eval_ratio", default=0.4, type=float)
    parser.add_argument("--split_seed", default=20260622, type=int)
    parser.add_argument(
        "--dataset_limit",
        default=None,
        type=int,
        help="Use only the first N cases before split/building wrapper requests. Keeps public runs aligned with the synthetic benchmark size.",
    )
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
        vals: List[float] = []
        for item in value:
            vals.extend(flatten_numeric(item))
        return vals
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


def case_key(value: Any) -> str:
    return str(value)


def load_records(dataset_path: Path) -> List[Dict[str, Any]]:
    payload = read_json(dataset_path)
    if isinstance(payload, dict) and "records" in payload:
        return payload["records"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"unsupported dataset format: {dataset_path}")


def split_records(records: List[Dict[str, Any]], selection_ratio: float, seed: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not 0.0 < selection_ratio < 1.0:
        raise ValueError("--selection_split_ratio must be between 0 and 1")
    items = list(records)
    rng = random.Random(seed)
    rng.shuffle(items)
    cut = max(1, min(len(items) - 1, int(round(len(items) * selection_ratio))))
    return items[:cut], items[cut:]


def metric_profile(row: Dict[str, Any]) -> Dict[str, Any]:
    post = get_nested(row, ["metrics", "post"]) or {}
    rewrite = avg_or_none(flatten_numeric(post.get("rewrite_acc")))
    rephrase = avg_or_none(flatten_numeric(post.get("rephrase_acc")))
    locality_vals: List[float] = []
    locality = post.get("locality") or {}
    locality_available = False
    if isinstance(locality, dict):
        for value in locality.values():
            if isinstance(value, dict):
                for key, sub in value.items():
                    if key.endswith("_acc"):
                        vals = flatten_numeric(sub)
                        locality_vals.extend(vals)
                        locality_available = locality_available or bool(vals)
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
        "locality_available": locality_available,
        "rewrite_fail": rewrite_fail,
        "rephrase_fail": rephrase_fail,
        "locality_fail": locality_fail,
        "fail_risk": fail_risk,
        "loc_risk": loc_risk,
    }


def build_candidates(
    rows: List[Dict[str, Any]],
    records_by_id: Dict[str, Dict[str, Any]],
    allowed_case_ids: set[str],
) -> List[Dict[str, Any]]:
    candidates = []
    for row in rows:
        cid = case_key(row.get("case_id"))
        request = row.get("request") or {}
        if cid not in allowed_case_ids and request.get("case_id") is not None:
            cid = case_key(request.get("case_id"))
        if cid not in allowed_case_ids:
            continue
        record = records_by_id.get(cid)
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
    max_per_key: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    selected = []
    counts: Dict[str, int] = {}
    stats = {
        "skipped_by_locality_risk": 0,
        "skipped_by_subject_or_relation_budget": 0,
        "missing_locality_risk_count": 0,
    }
    scored = []
    for item in candidates:
        profile = item["profile"]
        if not profile["locality_available"]:
            stats["missing_locality_risk_count"] += 1
        if profile["locality_fail"]:
            stats["skipped_by_locality_risk"] += 1
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
        if counts.get(key, 0) >= max_per_key:
            stats["skipped_by_subject_or_relation_budget"] += 1
            continue
        selected.append(item)
        counts[key] = counts.get(key, 0) + 1
        if len(selected) >= budget:
            break
    return selected, stats


def tag_record(record: Dict[str, Any], strategy: str, source_case_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    tagged = dict(record)
    tagged["closed_loop_strategy"] = strategy
    tagged["closed_loop_source_case_id"] = source_case_id
    tagged["closed_loop_fail_profile"] = profile
    return tagged


def union_records(round1_records: List[Dict[str, Any]], selected: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    out = []
    for row in round1_records:
        base = dict(row)
        base["closed_loop_strategy"] = "ROUND1_ORIGINAL"
        out.append(base)
    for item in selected:
        out.append(tag_record(item["record"], strategy, item["case_id"], item["profile"]))
    return out


def compact_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_id": item["case_id"],
        "subject": item["subject"],
        "relation": item["relation"],
        "profile": item["profile"],
    }


def write_markdown(path: Path, report: Dict[str, Any]) -> None:
    lines = [
        "# Public PACE/CAPE Selection Report",
        "",
        "PACE-Edit 在公开知识编辑基准中表示 residual-failure closed-loop editing；CAPE-Edit 在 residual failure 基础上加入 locality risk 和 subject/relation budget。",
        "CounterFact/zsRE 上的 residual failure 对应 rewrite/rephrase 编辑失败；locality risk 对应公开知识编辑 benchmark 中的 locality 下降。",
        "",
        f"- dataset: `{report['dataset']}`",
        f"- model: `{report['model']}`",
        f"- base_method: `{report['base_method']}`",
        f"- total_cases: `{report['total_cases']}`",
        f"- selection_split_size: `{report['selection_split_size']}`",
        f"- heldout_size: `{report['heldout_size']}`",
        f"- candidate_count: `{report['candidate_count']}`",
        f"- pace_selected_count: `{report['pace_selected_count']}`",
        f"- cape_selected_count: `{report['cape_selected_count']}`",
        f"- round1_count: `{report['round1_count']}`",
        f"- pace_union_count: `{report['pace_union_count']}`",
        f"- cape_union_count: `{report['cape_union_count']}`",
        f"- rewrite_fail_count: `{report['rewrite_fail_count']}`",
        f"- rephrase_fail_count: `{report['rephrase_fail_count']}`",
        f"- locality_available_count: `{report['locality_available_count']}`",
        f"- locality_failed_count: `{report['locality_failed_count']}`",
        f"- skipped_by_locality_risk: `{report['skipped_by_locality_risk']}`",
        f"- skipped_by_subject_or_relation_budget: `{report['skipped_by_subject_or_relation_budget']}`",
        "",
        "## Split Note",
        "",
        "Diagnostic-all uses the original full set to inspect closed-loop repair behavior. Held-out split files are emitted to avoid presenting same-set feedback as strict external generalization.",
        "",
        "| strategy | case_id | subject | rewrite | rephrase | locality |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for strategy in ["PACE_EDIT", "CAPE_EDIT"]:
        for item in report["selected_examples"][strategy][:20]:
            p = item["profile"]
            def fmt(x: Any) -> str:
                return "" if x is None else f"{x:.4f}" if isinstance(x, float) else str(x)
            lines.append(f"| {strategy} | {item['case_id']} | {item['subject']} | {fmt(p.get('rewrite'))} | {fmt(p.get('rephrase'))} | {fmt(p.get('locality'))} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset_path)
    per_case_path = Path(args.per_case_results)
    output_dir = Path(args.output_dir)
    records = load_records(dataset_path)
    if args.dataset_limit is not None:
        if args.dataset_limit <= 0:
            raise ValueError("--dataset_limit must be positive when provided")
        records = records[: args.dataset_limit]
    records_by_id = {case_key(row.get("case_id")): row for row in records}
    selection_records, heldout_records = split_records(records, args.selection_split_ratio, args.split_seed)
    selection_ids = {case_key(row.get("case_id")) for row in selection_records}
    rows = read_jsonl(per_case_path)
    budget = args.max_round2_requests
    if budget is None:
        budget = min(100, max(1, int(len(selection_records) * args.budget_fraction)))

    candidates = build_candidates(rows, records_by_id, selection_ids)
    pace_selected = candidates[:budget]
    cape_selected, cape_stats = cape_select(candidates, budget, args.lambda_loc, args.max_per_subject_or_relation)

    pace_union = union_records(records, pace_selected, "PACE_EDIT")
    cape_union = union_records(records, cape_selected, "CAPE_EDIT")

    paths = {
        "selection_split_cases": output_dir / "selection_split_cases.json",
        "heldout_eval_cases": output_dir / "heldout_eval_cases.json",
        "pace_round2_dataset": output_dir / "pace_round2_dataset.json",
        "cape_round2_dataset": output_dir / "cape_round2_dataset.json",
        "pace_union_dataset": output_dir / "pace_union_dataset.json",
        "cape_union_dataset": output_dir / "cape_union_dataset.json",
        "split_report": output_dir / "split_report.json",
    }
    write_json(paths["selection_split_cases"], {"dataset": args.dataset_name, "records": selection_records})
    write_json(paths["heldout_eval_cases"], {"dataset": args.dataset_name, "records": heldout_records})
    write_json(paths["pace_round2_dataset"], {"dataset": args.dataset_name, "records": [tag_record(item["record"], "PACE_EDIT", item["case_id"], item["profile"]) for item in pace_selected]})
    write_json(paths["cape_round2_dataset"], {"dataset": args.dataset_name, "records": [tag_record(item["record"], "CAPE_EDIT", item["case_id"], item["profile"]) for item in cape_selected]})
    write_json(paths["pace_union_dataset"], {"dataset": args.dataset_name, "records": pace_union})
    write_json(paths["cape_union_dataset"], {"dataset": args.dataset_name, "records": cape_union})

    split_report = {
        "split_seed": args.split_seed,
        "selection_split_ratio": args.selection_split_ratio,
        "heldout_eval_ratio": args.heldout_eval_ratio,
        "selection_split_size": len(selection_records),
        "heldout_size": len(heldout_records),
        "selection_case_ids": [row.get("case_id") for row in selection_records],
        "heldout_case_ids": [row.get("case_id") for row in heldout_records],
    }
    write_json(paths["split_report"], split_report)

    locality_available_count = sum(1 for item in candidates if item["profile"]["locality_available"])
    locality_failed_count = sum(1 for item in candidates if item["profile"]["locality_fail"])
    report = {
        "dataset": args.dataset_name,
        "model": args.model_name,
        "base_method": args.base_method,
        "total_cases": len(records),
        "dataset_limit": args.dataset_limit,
        "selection_split_size": len(selection_records),
        "heldout_size": len(heldout_records),
        "candidate_count": len(candidates),
        "selected_count": len(cape_selected),
        "pace_selected_count": len(pace_selected),
        "cape_selected_count": len(cape_selected),
        "round1_count": len(records),
        "pace_round2_count": len(pace_selected),
        "cape_round2_count": len(cape_selected),
        "pace_union_count": len(pace_union),
        "cape_union_count": len(cape_union),
        "rewrite_fail_count": sum(1 for item in candidates if item["profile"]["rewrite_fail"]),
        "rephrase_fail_count": sum(1 for item in candidates if item["profile"]["rephrase_fail"]),
        "locality_available_count": locality_available_count,
        "locality_failed_count": locality_failed_count,
        "skipped_by_locality_risk": cape_stats["skipped_by_locality_risk"],
        "skipped_by_subject_or_relation_budget": cape_stats["skipped_by_subject_or_relation_budget"],
        "missing_locality_risk_count": cape_stats["missing_locality_risk_count"],
        "max_round2_requests": budget,
        "max_per_subject_or_relation": args.max_per_subject_or_relation,
        "selected_case_ids": [item["case_id"] for item in cape_selected],
        "selected_subjects": [item["subject"] for item in cape_selected],
        "selected_relations": [item["relation"] for item in cape_selected],
        "paths": {key: str(value) for key, value in paths.items()},
        "selected_examples": {
            "PACE_EDIT": [compact_item(item) for item in pace_selected[:50]],
            "CAPE_EDIT": [compact_item(item) for item in cape_selected[:50]],
        },
    }
    write_json(output_dir / "selection_report.json", report)
    write_markdown(output_dir / "PACE_CAPE_PUBLIC_SELECTION_REPORT.md", report)
    print(f"candidate_count: {len(candidates)}")
    print(f"pace_selected: {len(pace_selected)}")
    print(f"cape_selected: {len(cape_selected)}")
    print(f"pace_union_dataset: {paths['pace_union_dataset']}")
    print(f"cape_union_dataset: {paths['cape_union_dataset']}")
    print(f"selection_report: {output_dir / 'selection_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
