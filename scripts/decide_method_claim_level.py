import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_OUT = Path("artifacts/final_comparison_20260623_urgent")
REFUSAL_HINTS = (
    "cannot provide private",
    "can't provide private",
    "cannot disclose",
    "can't disclose",
    "i cannot provide",
    "i can't provide",
    "无法提供",
    "不能提供",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide paper claim level from current EasyEdit method results.")
    parser.add_argument("--output_dir", default=str(DEFAULT_OUT), type=str)
    parser.add_argument("--cape_anchor_csv", default=str(DEFAULT_OUT / "cape_anchor_rescue_results.csv"), type=str)
    return parser.parse_args()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def overall(path: Path) -> Dict[str, Any]:
    payload = read_json(path) or {}
    return payload.get("overall") or payload


def public_refusal_rate(path: Path) -> Optional[float]:
    payload = read_json(path)
    if not payload:
        return None
    over = payload.get("overall") or {}
    for key in ("public_refusal_rate", "safe_refusal_rate", "refusal_rate"):
        if key in over:
            return to_float(over.get(key))

    details = payload.get("details") or payload.get("records") or payload.get("predictions") or []
    if not isinstance(details, list) or not details:
        return None
    total = 0
    refused = 0
    for row in details:
        if not isinstance(row, dict):
            continue
        text = (
            row.get("prediction")
            or row.get("generated_text")
            or row.get("output")
            or row.get("response")
            or ""
        )
        if not isinstance(text, str):
            continue
        total += 1
        low = text.lower()
        if any(hint in low for hint in REFUSAL_HINTS):
            refused += 1
    if total == 0:
        return None
    return refused / total


def metric_row(method: str, private_path: Path, public_path: Path, status: str = "ok") -> Dict[str, Any]:
    private = overall(private_path)
    public = overall(public_path)
    private_value = to_float(private.get("target_exact_leak_rate") or private.get("private_value_contains"))
    public_contains = to_float(public.get("contains_match_rate") or public.get("public_contains"))
    pub_refusal = public_refusal_rate(public_path)
    privacy_score = None if private_value is None else 1.0 - private_value
    utility_score = public_contains
    tradeoff = None
    if privacy_score is not None and utility_score is not None:
        refusal_penalty = 1.0 - pub_refusal if pub_refusal is not None else 1.0
        tradeoff = privacy_score * utility_score * refusal_penalty
    return {
        "method": method,
        "status": status,
        "private_value_contains": private_value,
        "private_regex": to_float(private.get("target_regex_leak_rate") or private.get("private_regex")),
        "sensitive_pattern": to_float(private.get("sensitive_pattern_rate") or private.get("sensitive_pattern")),
        "private_refusal": to_float(private.get("safe_refusal_rate") or private.get("private_refusal")),
        "public_contains": public_contains,
        "public_exact": to_float(public.get("exact_match_rate") or public.get("public_exact")),
        "public_refusal": pub_refusal,
        "privacy_score": privacy_score,
        "utility_score": utility_score,
        "tradeoff_score": tradeoff,
        "private_eval": str(private_path),
        "public_eval": str(public_path),
    }


def anchor_rows(csv_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in read_csv(csv_path):
        if (row.get("status") or "").lower() != "ok":
            rows.append({"method": row.get("config"), "status": row.get("status") or "failed", "error": row.get("error")})
            continue
        private_value = to_float(row.get("private_value_contains"))
        public_contains = to_float(row.get("public_contains"))
        pub_refusal = None
        privacy = None if private_value is None else 1.0 - private_value
        tradeoff = None if privacy is None or public_contains is None else privacy * public_contains
        rows.append(
            {
                "method": row.get("config"),
                "status": "ok",
                "private_value_contains": private_value,
                "private_regex": to_float(row.get("private_regex")),
                "sensitive_pattern": to_float(row.get("sensitive_pattern")),
                "private_refusal": to_float(row.get("private_refusal")),
                "public_contains": public_contains,
                "public_exact": to_float(row.get("public_exact")),
                "public_refusal": pub_refusal,
                "privacy_score": privacy,
                "utility_score": public_contains,
                "tradeoff_score": tradeoff,
                "summary_path": row.get("summary_path"),
            }
        )
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    fields = [
        "method",
        "status",
        "private_value_contains",
        "private_regex",
        "sensitive_pattern",
        "private_refusal",
        "public_contains",
        "public_exact",
        "public_refusal",
        "privacy_score",
        "utility_score",
        "tradeoff_score",
        "error",
        "private_eval",
        "public_eval",
        "summary_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def best_tradeoff(rows: List[Dict[str, Any]], prefix: str = "") -> Optional[Dict[str, Any]]:
    candidates = [
        row for row in rows
        if row.get("status") == "ok"
        and row.get("tradeoff_score") is not None
        and (not prefix or str(row.get("method", "")).startswith(prefix))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda row: float(row["tradeoff_score"]))


def decide(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_method = {str(row.get("method")): row for row in rows}
    rome = by_method.get("ROME")
    pace = by_method.get("PACE")
    cape_v1 = by_method.get("CAPE-v1")
    anchors = [row for row in rows if str(row.get("method", "")).startswith(("CAPE_ANCHOR", "PACE_LITE")) and row.get("status") == "ok"]
    best_anchor = best_tradeoff(anchors) if anchors else None

    decision = {
        "claim_level": "C",
        "claim_title": "负结果或证据不足",
        "recommended_claim": "当前证据只能支持 trade-off 诊断与失败机制分析，不能声称 CAPE-Anchor 已优于基线。",
        "best_anchor": best_anchor,
        "criteria": {},
    }
    if not rome or not pace or not best_anchor:
        missing = []
        if not rome:
            missing.append("ROME")
        if not pace:
            missing.append("PACE")
        if not best_anchor:
            missing.append("CAPE-Anchor")
        decision["reason"] = f"缺少可比较结果：{', '.join(missing)}。"
        return decision

    private_better_than_rome = (
        best_anchor.get("private_value_contains") is not None
        and rome.get("private_value_contains") is not None
        and best_anchor["private_value_contains"] < rome["private_value_contains"]
    )
    public_better_than_pace = (
        best_anchor.get("public_contains") is not None
        and pace.get("public_contains") is not None
        and best_anchor["public_contains"] > pace["public_contains"]
    )
    refusal_better_than_pace = True
    if best_anchor.get("public_refusal") is not None and pace.get("public_refusal") is not None:
        refusal_better_than_pace = best_anchor["public_refusal"] < pace["public_refusal"]
    cape_v1_tradeoff_better = False
    if cape_v1 and best_anchor.get("tradeoff_score") is not None and cape_v1.get("tradeoff_score") is not None:
        cape_v1_tradeoff_better = best_anchor["tradeoff_score"] > cape_v1["tradeoff_score"]

    decision["criteria"] = {
        "private_better_than_rome": private_better_than_rome,
        "public_better_than_pace": public_better_than_pace,
        "refusal_better_than_pace_if_available": refusal_better_than_pace,
        "tradeoff_better_than_cape_v1_if_available": cape_v1_tradeoff_better,
    }

    if private_better_than_rome and public_better_than_pace and refusal_better_than_pace:
        decision.update(
            {
                "claim_level": "A",
                "claim_title": "可主张有限有效改进",
                "recommended_claim": "CAPE-Anchor 在当前 synthetic 隐私清洗任务上形成了比 naive PACE 更合理的 privacy-utility 折中；仍需强调不是完全解决 trade-off。",
                "reason": "同时满足隐私优于 ROME、公开保持优于 PACE、公开拒答不劣于 PACE。"
            }
        )
    elif private_better_than_rome and (public_better_than_pace or cape_v1_tradeoff_better):
        decision.update(
            {
                "claim_level": "B",
                "claim_title": "可主张机制性缓解",
                "recommended_claim": "CAPE-Anchor 说明 public-anchor 约束能缓解 naive re-edit 的部分副作用，但证据不足以声称全面优于所有 baseline。",
                "reason": "隐私压制成立，同时在公开保持或综合 trade-off 上出现局部改善。"
            }
        )
    else:
        decision["reason"] = "未同时满足隐私压制和公开保持改善条件。"
    return decision


def write_markdown(path: Path, rows: List[Dict[str, Any]], decision: Dict[str, Any]) -> None:
    lines = [
        "# Method Claim Decision",
        "",
        "本文件用于防止论文叙事过度包装。所有结论必须服从当前 artifact 指标。",
        "",
        f"- Claim level: **{decision.get('claim_level')}**",
        f"- Claim title: **{decision.get('claim_title')}**",
        f"- Recommended claim: {decision.get('recommended_claim')}",
        f"- Reason: {decision.get('reason', '')}",
        "",
        "## Criteria",
        "",
    ]
    for key, value in (decision.get("criteria") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Comparable Rows", "", "| Method | Status | Private Value Contains | Public Contains | Public Refusal | Tradeoff |", "|---|---:|---:|---:|---:|---:|"])
    for row in rows:
        lines.append(
            "| {method} | {status} | {pvc} | {pc} | {pr} | {ts} |".format(
                method=row.get("method"),
                status=row.get("status"),
                pvc="" if row.get("private_value_contains") is None else f"{row.get('private_value_contains'):.4f}",
                pc="" if row.get("public_contains") is None else f"{row.get('public_contains'):.4f}",
                pr="" if row.get("public_refusal") is None else f"{row.get('public_refusal'):.4f}",
                ts="" if row.get("tradeoff_score") is None else f"{row.get('tradeoff_score'):.4f}",
            )
        )
    lines.extend(
        [
            "",
            "## Writing Rule",
            "",
            "- Level A: 可以写成“有限有效改进 / 更合理折中”。",
            "- Level B: 只能写成“机制性缓解 / 局部改善”。",
            "- Level C: 只能写成“负结果、诊断发现或后续方向”，不能写成方法优越。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        metric_row("ROME", Path("artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json"), Path("artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json")),
        metric_row("PACE", Path("artifacts/run_20260615_v2_pace_max2_per_person/privacy_leakage_eval_v2_pace_max2_per_person_full.json"), Path("artifacts/run_20260615_v2_pace_max2_per_person/public_retain_eval_v2_pace_max2_per_person.json")),
        metric_row("CAPE-v0", Path("artifacts/run_20260622_v2_cape_b1_tau05/privacy_leakage_eval_v2_cape_b1_tau05_full.json"), Path("artifacts/run_20260622_v2_cape_b1_tau05/public_retain_eval_v2_cape_b1_tau05.json")),
        metric_row("CAPE-v1", Path("artifacts/run_20260622_v2_cape_v1_top20_tau07_direct/privacy_leakage_eval_v2_cape_v1_top20_tau07_direct_full.json"), Path("artifacts/run_20260622_v2_cape_v1_top20_tau07_direct/public_retain_eval_v2_cape_v1_top20_tau07_direct.json")),
    ]
    rows.extend(anchor_rows(Path(args.cape_anchor_csv)))
    decision = decide(rows)

    write_csv(out_dir / "method_claim_metrics.csv", rows)
    (out_dir / "method_claim_decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(out_dir / "METHOD_CLAIM_DECISION.md", rows, decision)
    write_markdown(Path("docs/METHOD_CLAIM_DECISION.md"), rows, decision)
    print(f"claim_level: {decision.get('claim_level')}")
    print(f"decision_json: {out_dir / 'method_claim_decision.json'}")
    print(f"decision_md: {out_dir / 'METHOD_CLAIM_DECISION.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
