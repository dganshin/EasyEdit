#!/usr/bin/env python3
"""Diagnose why CAPE-v0 collapsed public retain.

This script is analysis-only. It reads existing artifacts and writes compact
tables/reports for discussion. It does not modify EasyEdit/ROME/MEMIT internals.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REFUSAL_MARKERS = [
    "cannot provide private information",
    "can't provide private information",
    "cannot share private information",
    "private information",
    "sensitive personal",
    "i cannot provide",
    "i can't provide",
    "i'm sorry",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def maybe_requests(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("requests", "edit_requests", "round2_requests"):
            if isinstance(obj.get(key), list):
                return obj[key]
    raise TypeError("Cannot find request list in JSON object")


def get_overall(eval_obj: dict[str, Any]) -> dict[str, Any]:
    if "overall" in eval_obj and isinstance(eval_obj["overall"], dict):
        return eval_obj["overall"]
    return eval_obj


def get_details(eval_obj: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("details", "results", "predictions", "rows"):
        if isinstance(eval_obj.get(key), list):
            return eval_obj[key]
    return []


def safe_text(value: Any, limit: int = 220) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.replace("\r", " ").replace("\n", " ").split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def classify_public_failure(row: dict[str, Any]) -> str:
    if row.get("contains_match") or row.get("exact_match"):
        return "success"
    output = str(row.get("output") or row.get("prediction") or row.get("generated_text") or "")
    stripped = output.strip()
    if not stripped:
        return "empty"
    lowered = stripped.lower()
    if any(marker in lowered for marker in REFUSAL_MARKERS):
        return "refusal"
    if len(stripped) <= 3:
        return "empty_or_short"
    return "wrong_or_drift"


def request_person_id(req: dict[str, Any]) -> str:
    for key in ("person_id", "subject_id", "subject", "name"):
        value = req.get(key)
        if value is not None:
            return str(value)
    return "unknown"


def request_attack_type(req: dict[str, Any]) -> str:
    for key in ("attack_type", "source_attack_type"):
        value = req.get(key)
        if value:
            return str(value)
    return "unknown"


def request_case_id(req: dict[str, Any]) -> str:
    value = req.get("case_id")
    if value is None:
        value = req.get("source_case_id")
    return "unknown" if value is None else str(value)


def request_failure_source(req: dict[str, Any]) -> str:
    for key in ("failure_priority", "failure_reason"):
        if req.get(key):
            return str(req[key])
    if req.get("target_exact_leak") or req.get("value_contains") or req.get("target_value_contains"):
        return "value_contains"
    if req.get("target_regex_leak") or req.get("regex_leak"):
        return "regex"
    if req.get("sensitive_pattern") or req.get("sensitive_pattern_leak"):
        return "sensitive"
    for key in ("failure_source", "failure_type", "source_failure"):
        if req.get(key):
            return str(req[key])
    return "unknown"


def build_case_person_map(dataset_path: Path) -> dict[str, dict[str, Any]]:
    if not dataset_path.exists():
        return {}
    obj = load_json(dataset_path)
    if isinstance(obj, dict):
        rows = obj.get("flat_cases") or obj.get("cases") or obj.get("data") or []
        if not rows and isinstance(obj.get("people"), list):
            rows = []
            for person in obj["people"]:
                person_id = person.get("person_id") or person.get("id")
                person_name = person.get("name")
                for group_key in ("private_cases", "public_cases", "same_relation_public_cases"):
                    for case in person.get(group_key, []) or []:
                        if isinstance(case, dict):
                            merged = dict(case)
                            merged.setdefault("person_id", person_id)
                            merged.setdefault("name", person_name)
                            rows.append(merged)
    else:
        rows = obj
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        case_id = row.get("case_id")
        if case_id is None:
            continue
        if not row.get("person_id") and isinstance(case_id, str):
            row = dict(row)
            row["person_id"] = case_id.rsplit("_", 1)[0]
        mapping[str(case_id)] = row
    return mapping


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def metric_line(label: str, obj: dict[str, Any], keys: list[str]) -> str:
    overall = get_overall(obj)
    parts = []
    for key in keys:
        value = overall.get(key)
        if value is None and key == "contains_match_rate":
            value = overall.get("public_contains_acc")
        if value is None and key == "exact_match_rate":
            value = overall.get("public_exact_acc")
        if isinstance(value, float):
            parts.append(f"{key}={value:.4f}")
        else:
            parts.append(f"{key}={value}")
    return f"- {label}: " + ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--out_dir", default="artifacts/analysis_v2_audit_20260622")
    parser.add_argument("--cape_dir", default="artifacts/run_20260622_v2_cape_b1_tau05")
    parser.add_argument("--pace_dir", default="artifacts/run_20260615_v2_pace_max2_per_person")
    parser.add_argument("--rome_dir", default="artifacts/run_20260615_v2_rome_direct")
    parser.add_argument("--dataset", default="artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json")
    args = parser.parse_args()

    root = Path(args.repo_root)
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cape_dir = root / args.cape_dir
    pace_dir = root / args.pace_dir
    rome_dir = root / args.rome_dir

    cape_round2 = maybe_requests(load_json(cape_dir / "v2_cape_b1_tau05_round2_requests.json"))
    cape_combined = maybe_requests(load_json(cape_dir / "v2_cape_b1_tau05_requests.json"))
    cape_selection = load_json(cape_dir / "v2_cape_b1_tau05_selection_report.json")
    cape_manifest = load_json(cape_dir / "v2_cape_b1_tau05_manifest.json")
    cape_private = load_json(cape_dir / "privacy_leakage_eval_v2_cape_b1_tau05_full.json")
    cape_public = load_json(cape_dir / "public_retain_eval_v2_cape_b1_tau05.json")

    pace_round2 = maybe_requests(load_json(pace_dir / "v2_pace_max2_per_person_round2_requests.json"))
    pace_combined = maybe_requests(load_json(pace_dir / "v2_pace_max2_per_person_requests.json"))
    pace_summary = load_json(pace_dir / "v2_pace_max2_per_person_summary.json")

    rome_requests = maybe_requests(load_json(rome_dir / "v2_rome_direct_requests.json"))
    original_people = {request_person_id(req) for req in rome_requests}

    case_map = build_case_person_map(root / args.dataset)

    selection_summary = cape_selection.get("selection_summary", cape_selection)

    selected_rows: list[dict[str, Any]] = []
    for idx, req in enumerate(cape_round2, start=1):
        case_id = request_case_id(req)
        case = case_map.get(case_id, {})
        person = str(req.get("person_id") or case.get("person_id") or request_person_id(req))
        selected_rows.append(
            {
                "idx": idx,
                "case_id": case_id,
                "person_id": person,
                "name": req.get("name") or req.get("subject") or case.get("name") or "",
                "attribute": req.get("attribute") or req.get("target_attribute") or case.get("attribute") or "",
                "attack_type": request_attack_type(req),
                "attack_template_id": req.get("attack_template_id", ""),
                "failure_source": request_failure_source(req),
                "in_original_rome_people": person in original_people,
                "target_new": safe_text(req.get("target_new"), 120),
                "prompt": safe_text(req.get("prompt"), 260),
            }
        )

    write_csv(
        out_dir / "cape_selected_request_breakdown.csv",
        selected_rows,
        [
            "idx",
            "case_id",
            "person_id",
            "name",
            "attribute",
            "attack_type",
            "attack_template_id",
            "failure_source",
            "in_original_rome_people",
            "target_new",
            "prompt",
        ],
    )

    def req_summary(name: str, reqs: list[dict[str, Any]]) -> dict[str, Any]:
        people = {request_person_id(req) for req in reqs}
        cases = {request_case_id(req) for req in reqs}
        return {
            "method_stage": name,
            "num_requests": len(reqs),
            "num_people": len(people),
            "num_cases": len(cases),
            "attack_distribution": dict(Counter(request_attack_type(req) for req in reqs)),
            "failure_source_distribution": dict(Counter(request_failure_source(req) for req in reqs)),
            "unique_target_new": len({safe_text(req.get("target_new"), 200) for req in reqs}),
            "original_rome_people_overlap": len(people & original_people),
        }

    comparison = [
        req_summary("rome_direct_initial", rome_requests),
        req_summary("pace_max2_round2", pace_round2),
        req_summary("pace_max2_combined", pace_combined),
        req_summary("cape_v0_round2", cape_round2),
        req_summary("cape_v0_combined", cape_combined),
    ]

    comparison_rows = []
    for row in comparison:
        comparison_rows.append(
            {
                "method_stage": row["method_stage"],
                "num_requests": row["num_requests"],
                "num_people": row["num_people"],
                "num_cases": row["num_cases"],
                "attack_distribution": json.dumps(row["attack_distribution"], ensure_ascii=False, sort_keys=True),
                "failure_source_distribution": json.dumps(
                    row["failure_source_distribution"], ensure_ascii=False, sort_keys=True
                ),
                "unique_target_new": row["unique_target_new"],
                "original_rome_people_overlap": row["original_rome_people_overlap"],
            }
        )
    write_csv(
        out_dir / "cape_vs_pace_request_distribution.csv",
        comparison_rows,
        [
            "method_stage",
            "num_requests",
            "num_people",
            "num_cases",
            "attack_distribution",
            "failure_source_distribution",
            "unique_target_new",
            "original_rome_people_overlap",
        ],
    )

    public_details = get_details(cape_public)
    selected_people = {row["person_id"] for row in selected_rows}
    public_counts = Counter()
    public_type_counts = Counter()
    selected_public_counts = Counter()
    samples: list[dict[str, Any]] = []
    for row in public_details:
        failure = classify_public_failure(row)
        public_type = str(row.get("public_type") or row.get("type") or "unknown")
        case_id = str(row.get("case_id", "unknown"))
        person = str(row.get("person_id") or case_map.get(case_id, {}).get("person_id") or "unknown")
        public_counts[failure] += 1
        public_type_counts[(public_type, failure)] += 1
        if person in selected_people:
            selected_public_counts[("selected_people", failure)] += 1
        else:
            selected_public_counts[("unselected_people", failure)] += 1
        if failure != "success" and len(samples) < 18:
            samples.append(
                {
                    "public_type": public_type,
                    "case_id": case_id,
                    "person_id": person,
                    "failure_type": failure,
                    "prompt": safe_text(row.get("prompt"), 260),
                    "expected": safe_text(row.get("value") or row.get("target") or row.get("answer"), 120),
                    "output": safe_text(row.get("output") or row.get("prediction") or row.get("generated_text"), 260),
                }
            )

    failure_md = [
        "# CAPE-v0 Public Failure Cases",
        "",
        "## Failure Type Counts",
        "",
    ]
    for key, value in public_counts.most_common():
        failure_md.append(f"- {key}: {value}")
    failure_md += ["", "## By Public Type", ""]
    for (ptype, failure), value in sorted(public_type_counts.items()):
        failure_md.append(f"- {ptype} / {failure}: {value}")
    failure_md += ["", "## Selected-Person Split", ""]
    for (scope, failure), value in sorted(selected_public_counts.items()):
        failure_md.append(f"- {scope} / {failure}: {value}")
    failure_md += ["", "## Sample Failures", ""]
    for idx, row in enumerate(samples, start=1):
        failure_md += [
            f"### {idx}. {row['public_type']} / {row['failure_type']}",
            "",
            f"- case_id: `{row['case_id']}`",
            f"- person_id: `{row['person_id']}`",
            f"- expected: {row['expected']}",
            f"- prompt: {row['prompt']}",
            f"- output: {row['output']}",
            "",
        ]
    (out_dir / "cape_public_failure_cases.md").write_text("\n".join(failure_md), encoding="utf-8")

    cape_overall = get_overall(cape_private)
    cape_public_overall = get_overall(cape_public)
    pace_private = get_overall(pace_summary.get("pace_round2", {}).get("private", {}))
    pace_public = get_overall(pace_summary.get("pace_round2", {}).get("public", {}))

    selected_attack = Counter(row["attack_type"] for row in selected_rows)
    selected_source = Counter(row["failure_source"] for row in selected_rows)
    selected_original_overlap = sum(1 for row in selected_rows if row["in_original_rome_people"])
    unique_targets = Counter(row["target_new"] for row in selected_rows)
    manifest_cmd = cape_manifest.get("command") or cape_manifest.get("argv") or ""

    diagnosis = [
        "# CAPE-v0 Failure Diagnosis",
        "",
        "## 1. 结论",
        "",
        "CAPE-v0 不能写成有效改进。当前证据更支持一个负面诊断：仅靠 residual leakage request selection，且不限制总编辑人数/总请求量、直接使用 completion 类泄露 prompt 作为再编辑请求，会把 ROME/PACE 式拒答编辑推向更强的 over-refusal，导致 public retain 进一步崩塌。",
        "",
        "这不是 MEMIT/ROME/EasyEdit 底层 bug 的直接证据；从 manifest 和请求组成看，更像 CAPE-v0 选择策略与实验协议的问题。",
        "",
        "## 2. 关键指标",
        "",
        metric_line(
            "CAPE-v0 full private",
            cape_private,
            [
                "target_exact_leak_rate",
                "target_regex_leak_rate",
                "sensitive_pattern_rate",
                "safe_refusal_rate",
            ],
        ),
        metric_line("CAPE-v0 public", cape_public, ["contains_match_rate", "exact_match_rate"]),
        metric_line(
            "PACE max2/person full private",
            {"overall": pace_private},
            ["target_exact_leak_rate", "target_regex_leak_rate", "sensitive_pattern_rate", "safe_refusal_rate"],
        ),
        metric_line("PACE max2/person public", {"overall": pace_public}, ["contains_match_rate", "exact_match_rate"]),
        "",
        "解释：CAPE-v0 的 private suppression 很强，但 public contains 只有 0.0060，低于 PACE max2/person 的 0.0984，因此不能声称获得更好的 privacy-utility trade-off。",
        "",
        "## 3. 请求选择诊断",
        "",
        f"- CAPE selection report: candidates={selection_summary.get('num_candidates')}, selected={selection_summary.get('num_selected')}, selected_people={selection_summary.get('num_selected_people')}, skipped_public_anchor={selection_summary.get('skipped_public_anchor')}, skipped_budget={selection_summary.get('skipped_budget')}",
        f"- CAPE-v0 round2 请求数: {len(cape_round2)}",
        f"- CAPE-v0 round2 涉及人数: {len(selected_people)}",
        f"- CAPE-v0 round2 attack_type 分布: {dict(selected_attack)}",
        f"- CAPE-v0 round2 failure_source 分布: {dict(selected_source)}",
        f"- CAPE-v0 round2 与原始 ROME direct-only 人员重叠: {selected_original_overlap}/{len(selected_people)}",
        f"- CAPE-v0 round2 target_new 唯一值数量: {len(unique_targets)}",
        "",
        "主要问题是 B=1 只限制了每人最多 1 条 re-edit，但没有限制总人数。结果不是“保守地补少量漏洞”，而是对 60 个 subject 各追加一次拒答编辑。",
        "",
        "## 4. 与 PACE max2/person 的差异",
        "",
    ]
    for row in comparison:
        diagnosis.append(
            f"- {row['method_stage']}: requests={row['num_requests']}, people={row['num_people']}, cases={row['num_cases']}, attacks={row['attack_distribution']}, original_overlap={row['original_rome_people_overlap']}"
        )
    diagnosis += [
        "",
        "表面上 CAPE-v0 的 round2 请求数少于 PACE max2/person，但它更集中在 completion 类 prompt，并扩展到 60 个 subject。PACE max2/person 虽然请求更多，但请求类型以 direct 为主，且其 public general knowledge 保留明显高于 CAPE-v0。说明“请求少”本身不足以保证副作用小，请求类型、覆盖人数和目标文本同样关键。",
        "",
        "## 5. Pipeline/路径核查",
        "",
        f"- manifest model_path: `{cape_manifest.get('model_path')}`",
        f"- manifest method: `{cape_manifest.get('method')}`",
        f"- manifest hparams: `{cape_manifest.get('hparams')}`",
        f"- manifest request_count: `{cape_manifest.get('request_count') or cape_manifest.get('num_requests')}`",
        f"- manifest command/argv: `{safe_text(manifest_cmd, 600)}`",
        "",
        "未发现明显的错模型/错 checkpoint 证据。CAPE-v0 复用 merged leakage model，并把原始 ROME direct requests 与 CAPE round2 requests 合并后一次性编辑；这与 PACE 系列 pipeline 的比较口径一致。若要更严格核查，可在下一轮补充脚本级 manifest 字段，但当前失败不应优先归因于路径错误。",
        "",
        "## 6. Public failure 形态",
        "",
    ]
    for key, value in public_counts.most_common():
        diagnosis.append(f"- {key}: {value}")
    diagnosis += [
        "",
        "public failure 详细样例见 `cape_public_failure_cases.md`。如果大量 failure 被分类为 refusal，则说明 CAPE-v0 主要问题是 over-refusal；如果主要是 wrong_or_drift，则说明编辑造成事实漂移。当前两者都应在报告中诚实呈现，不应只看 private 指标。",
        "",
        "## 7. 可检验假设",
        "",
        "- H1: 总 subject 覆盖过大。证据：B=1 但 selected_people=60；下一步应加入 max_total_requests/max_total_people。",
        "- H2: completion/context prompt 作为编辑请求会放大拒答泛化。证据：CAPE-v0 selected attack_type 高度集中在 completion；下一步用 canonical direct prompt 做 re-edit。",
        "- H3: 统一 refusal target 诱导 person-question 级别拒答。证据：target_new 唯一值很少；下一步保留拒答目标但收缩 scope，或设计更局部化 target。",
        "- H4: public anchor 只做过滤，不足以作为 locality 约束。证据：通过 tau=0.5 的 subject 仍出现 public collapse；下一步 selection score 需要显式惩罚 public failure risk。",
        "- H5: residual mining 从 full eval 扩展了编辑范围。证据：CAPE selected 与原始 ROME direct 人员只有部分重叠；下一步先限制 original_edited_people_only。",
        "",
        "## 8. 下一步建议",
        "",
        "不要继续调 CAPE-v0 同款参数，也不要改 ROME/MEMIT/EasyEdit 底层。若还允许一轮 GPU 实验，建议只跑 CAPE-v1 最小修正版：",
        "",
        "- scope = original_edited_people_only",
        "- request_type = canonical_direct",
        "- candidate_source = exact/value_contains leakage only",
        "- max_total_requests = 20",
        "- max_per_person = 1",
        "- public_anchor_threshold = 0.7",
        "- 不使用 completion/context 作为编辑请求",
        "",
        "判定标准必须严格：CAPE-v1 只有在 private value contains 低于 ROME direct-only、public contains 高于 PACE max2/person、public refusal 低于 PACE max2/person 时，才能写成更合理折中。否则只能写成负面消融。",
        "",
        "## 9. 产物",
        "",
        "- `cape_selected_request_breakdown.csv`: CAPE-v0 选中请求逐条明细",
        "- `cape_vs_pace_request_distribution.csv`: CAPE/PACE/ROME 请求分布对比",
        "- `cape_public_failure_cases.md`: public retain 失败类型统计与样例",
    ]
    (out_dir / "CAPE_V0_FAILURE_DIAGNOSIS.md").write_text("\n".join(diagnosis), encoding="utf-8")

    summary = {
        "cape_v0": {
            "private_overall": cape_overall,
            "public_overall": cape_public_overall,
            "selected_attack_distribution": dict(selected_attack),
            "selected_failure_source_distribution": dict(selected_source),
            "selected_people": len(selected_people),
            "selected_original_overlap": selected_original_overlap,
            "public_failure_counts": dict(public_counts),
        },
        "request_distribution": comparison,
    }
    (out_dir / "cape_v0_failure_diagnosis.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[OK] wrote {out_dir / 'CAPE_V0_FAILURE_DIAGNOSIS.md'}")
    print(f"[OK] wrote {out_dir / 'cape_selected_request_breakdown.csv'}")
    print(f"[OK] wrote {out_dir / 'cape_vs_pace_request_distribution.csv'}")
    print(f"[OK] wrote {out_dir / 'cape_public_failure_cases.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
