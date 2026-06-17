import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


RUNS = [
    {
        "method": "merged_leakage_model",
        "run_name": "v2_lora_mlp_only",
        "artifact_dir": "artifacts/run_20260615_v2_lora_mlp_only",
        "dataset_path": "artifacts/run_20260615_v2_lora_mlp_only/synthetic_privacy_dataset.json",
        "private_eval": "artifacts/run_20260615_v2_lora_mlp_only/privacy_leakage_eval_merged_v2.json",
        "public_eval": "artifacts/run_20260615_v2_lora_mlp_only/public_retain_eval_merged_v2.json",
        "manifest": "artifacts/run_20260615_v2_lora_mlp_only/merge_manifest.json",
        "note": "pre-edit merged leakage model",
    },
    {
        "method": "ROME direct-only",
        "run_name": "v2_rome_direct",
        "artifact_dir": "artifacts/run_20260615_v2_rome_direct",
        "private_eval": "artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json",
        "public_eval": "artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json",
        "manifest": "artifacts/run_20260615_v2_rome_direct/v2_rome_direct_manifest.json",
        "summary": "artifacts/run_20260615_v2_rome_direct/v2_rome_direct_summary.json",
        "request_path": "artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json",
        "round2_requests": 0,
        "note": "40 direct requests on 20 people; full eval on v2 dataset",
    },
    {
        "method": "PACE target_only",
        "run_name": "v2_pace_target_only",
        "artifact_dir": "artifacts/run_20260615_v2_pace_target_only",
        "private_eval": "artifacts/run_20260615_v2_pace_target_only/privacy_leakage_eval_v2_pace_target_only_full.json",
        "public_eval": "artifacts/run_20260615_v2_pace_target_only/public_retain_eval_v2_pace_target_only.json",
        "manifest": "artifacts/run_20260615_v2_pace_target_only/v2_pace_target_only_manifest.json",
        "summary": "artifacts/run_20260615_v2_pace_target_only/v2_pace_target_only_summary.json",
        "request_path": "artifacts/run_20260615_v2_pace_target_only/v2_pace_target_only_requests.json",
        "round2_request_path": "artifacts/run_20260615_v2_pace_target_only/v2_pace_target_only_round2_requests.json",
        "note": "target leak failures only",
    },
    {
        "method": "PACE max1_per_case",
        "run_name": "v2_pace_max1_per_case",
        "artifact_dir": "artifacts/run_20260615_v2_pace_max1_per_case",
        "private_eval": "artifacts/run_20260615_v2_pace_max1_per_case/privacy_leakage_eval_v2_pace_max1_per_case_full.json",
        "public_eval": "artifacts/run_20260615_v2_pace_max1_per_case/public_retain_eval_v2_pace_max1_per_case.json",
        "manifest": "artifacts/run_20260615_v2_pace_max1_per_case/v2_pace_max1_per_case_manifest.json",
        "summary": "artifacts/run_20260615_v2_pace_max1_per_case/v2_pace_max1_per_case_summary.json",
        "request_path": "artifacts/run_20260615_v2_pace_max1_per_case/v2_pace_max1_per_case_requests.json",
        "round2_request_path": "artifacts/run_20260615_v2_pace_max1_per_case/v2_pace_max1_per_case_round2_requests.json",
        "note": "at most one Round2 request per case",
    },
    {
        "method": "PACE max2_per_person",
        "run_name": "v2_pace_max2_per_person",
        "artifact_dir": "artifacts/run_20260615_v2_pace_max2_per_person",
        "private_eval": "artifacts/run_20260615_v2_pace_max2_per_person/privacy_leakage_eval_v2_pace_max2_per_person_full.json",
        "public_eval": "artifacts/run_20260615_v2_pace_max2_per_person/public_retain_eval_v2_pace_max2_per_person.json",
        "manifest": "artifacts/run_20260615_v2_pace_max2_per_person/v2_pace_max2_per_person_manifest.json",
        "summary": "artifacts/run_20260615_v2_pace_max2_per_person/v2_pace_max2_per_person_summary.json",
        "request_path": "artifacts/run_20260615_v2_pace_max2_per_person/v2_pace_max2_per_person_requests.json",
        "round2_request_path": "artifacts/run_20260615_v2_pace_max2_per_person/v2_pace_max2_per_person_round2_requests.json",
        "note": "at most two Round2 requests per person",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v2 privacy experiment assets.")
    parser.add_argument("--dataset", default="artifacts/run_20260615_v2_lora_mlp_only/synthetic_privacy_dataset.json")
    parser.add_argument("--train_jsonl", default="artifacts/run_20260615_v2_lora_mlp_only/lora_privacy_train.jsonl")
    parser.add_argument("--train_dataset", default="artifacts/run_20260615_v2_lora_mlp_only/lora_privacy_train_dataset.json")
    parser.add_argument("--output_dir", default="artifacts/run_20260617_v2_audit")
    parser.add_argument("--doc_path", default="docs/V2_AUDIT_AND_LOCALITY_SUMMARY_2026-06-17.md")
    return parser.parse_args()


def load_json(path: str | Path) -> Optional[Any]:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists() or file_path.is_dir():
        return None
    with file_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path: str | Path) -> Optional[str]:
    file_path = Path(path)
    if not file_path.exists():
        return None
    digest = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct(value: Optional[float]) -> str:
    if value is None:
        return "null"
    return f"{value:.4f}"


def unique_count(rows: Iterable[Dict[str, Any]], key: str) -> int:
    return len({str(row.get(key)) for row in rows if row.get(key)})


def person_id_from_case_id(case_id: Any) -> Optional[str]:
    text = str(case_id or "")
    parts = text.split("_")
    if len(parts) >= 2 and parts[0] == "person":
        return f"{parts[0]}_{parts[1]}"
    return None


def real_person_count(rows: Iterable[Dict[str, Any]]) -> int:
    people = set()
    for row in rows:
        person_id = str(row.get("person_id") or "")
        if person_id.startswith("person_"):
            people.add(person_id)
            continue
        parsed = person_id_from_case_id(row.get("case_id"))
        if parsed:
            people.add(parsed)
    return len(people)


def request_payload(path: str | None) -> List[Dict[str, Any]]:
    if not path:
        return []
    payload = load_json(path)
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("requests"), list):
        return payload["requests"]
    return []


def private_metrics(path: str) -> Dict[str, Any]:
    data = load_json(path)
    if not data:
        return {}
    metrics = data.get("grouped_any_metrics") or data.get("overall_metrics") or data.get("overall") or {}
    rows = data.get("by_expected_row") or data.get("details") or []
    return {
        "target_exact_leak_rate": metrics.get("any_target_exact_leak_rate", metrics.get("target_exact_leak_rate")),
        "target_regex_leak_rate": metrics.get("any_target_regex_leak_rate", metrics.get("target_regex_leak_rate")),
        "sensitive_pattern_rate": metrics.get("any_sensitive_pattern_rate", metrics.get("sensitive_pattern_rate")),
        "safe_refusal_rate": metrics.get("any_safe_refusal_rate", metrics.get("safe_refusal_rate")),
        "num_expected_attack_prompts": data.get("num_expected_attack_prompts") or metrics.get("num_case_attack_groups"),
        "num_evaluated_predictions": data.get("num_evaluated_predictions"),
        "eval_people": real_person_count(rows),
        "eval_cases": unique_count(rows, "case_id"),
        "attack_types": sorted((data.get("by_attack_type") or {}).keys()),
    }


def public_metrics(path: str) -> Dict[str, Any]:
    data = load_json(path)
    if not data:
        return {}
    overall = data.get("overall") or {}
    by_public_type = data.get("by_public_type") or {}
    rows = data.get("details") or []
    return {
        "contains_match_rate": overall.get("contains_match_rate"),
        "exact_match_rate": overall.get("exact_match_rate"),
        "same_subject_public": (by_public_type.get("same_subject_public") or {}).get("contains_match_rate"),
        "same_relation_other_subject": (by_public_type.get("same_relation_other_subject") or {}).get("contains_match_rate"),
        "general_knowledge": (by_public_type.get("general_knowledge") or {}).get("contains_match_rate"),
        "num_public_cases": data.get("num_public_cases"),
        "num_expected_public_prompts": data.get("num_expected_public_prompts"),
        "num_evaluated_predictions": data.get("num_evaluated_predictions"),
        "eval_people": real_person_count(rows),
        "eval_cases": unique_count(rows, "case_id"),
    }


def request_summary(path: str | None) -> Dict[str, Any]:
    rows = request_payload(path)
    return {
        "path": path,
        "exists": bool(path and Path(path).exists()),
        "num_requests": len(rows),
        "num_people": real_person_count(rows),
        "num_cases": unique_count(rows, "case_id"),
        "by_attack_type": dict(sorted(Counter(str(row.get("attack_type") or "unknown") for row in rows).items())),
    }


def benchmark_scale(dataset: Dict[str, Any], train_rows: List[Dict[str, Any]], train_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    flat_cases = dataset.get("flat_cases", [])
    private_cases = [row for row in flat_cases if row.get("sensitivity") == "private"]
    public_cases = [row for row in flat_cases if row.get("sensitivity") == "public"]
    people = dataset.get("people", [])
    train_people = real_person_count(train_rows)
    return {
        "dataset_path": "artifacts/run_20260615_v2_lora_mlp_only/synthetic_privacy_dataset.json",
        "dataset_sha256": sha256_file("artifacts/run_20260615_v2_lora_mlp_only/synthetic_privacy_dataset.json"),
        "people_count": len(people),
        "flat_cases": len(flat_cases),
        "private_facts": len(private_cases),
        "public_facts": len(public_cases),
        "private_attribute_counts": dict(sorted(Counter(row.get("attribute") for row in private_cases).items())),
        "public_type_counts": dict(sorted(Counter(row.get("public_type") for row in public_cases).items())),
        "public_attribute_counts": dict(sorted(Counter(row.get("attribute") for row in public_cases).items())),
        "attack_prompt_counts": dict(sorted(Counter(prompt.get("attack_type") for row in flat_cases for prompt in row.get("test_prompt_rows", [])).items())),
        "flat_cases_definition": "one fact-like case: 2 private facts and 8 person-linked public facts per person, plus 40 general_knowledge public cases",
        "train_records": len(train_rows),
        "train_people": train_people,
        "train_private_records": sum(1 for row in train_rows if row.get("sensitivity") == "private"),
        "train_public_records": sum(1 for row in train_rows if row.get("sensitivity") == "public"),
        "train_manifest_num_records": (train_payload or {}).get("num_records"),
        "train_manifest_num_people": (train_payload or {}).get("num_people"),
    }


def build_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for run in RUNS:
        manifest = load_json(run.get("manifest", "")) or {}
        summary = load_json(run.get("summary", "")) or {}
        priv = private_metrics(run["private_eval"])
        pub = public_metrics(run["public_eval"])
        req = request_summary(run.get("request_path"))
        round2 = request_summary(run.get("round2_request_path"))
        rows.append(
            {
                "method": run["method"],
                "run_name": run["run_name"],
                "artifact_dir": run["artifact_dir"],
                "base_model": manifest.get("model_path") or manifest.get("output_dir"),
                "dataset_path": manifest.get("dataset_path") or run.get("dataset_path"),
                "request_path": run.get("request_path"),
                "append_request_path": manifest.get("append_requests_path"),
                "private_eval_path": run["private_eval"],
                "public_eval_path": run["public_eval"],
                "output_path": manifest.get("output_dir") or run["artifact_dir"],
                "traceable": bool(Path(run["private_eval"]).exists() and Path(run["public_eval"]).exists() and Path(run["artifact_dir"]).exists()),
                "private_exact": priv.get("target_exact_leak_rate"),
                "private_regex": priv.get("target_regex_leak_rate"),
                "sensitive_pattern": priv.get("sensitive_pattern_rate"),
                "refusal": priv.get("safe_refusal_rate"),
                "public_overall_contains": pub.get("contains_match_rate"),
                "same_subject_public": pub.get("same_subject_public"),
                "same_relation_other_subject": pub.get("same_relation_other_subject"),
                "general_knowledge": pub.get("general_knowledge"),
                "private_eval_prompts": priv.get("num_expected_attack_prompts"),
                "private_eval_people": priv.get("eval_people"),
                "private_eval_cases": priv.get("eval_cases"),
                "private_attack_types": priv.get("attack_types"),
                "public_eval_prompts": pub.get("num_expected_public_prompts"),
                "public_eval_people": pub.get("eval_people"),
                "public_eval_cases": pub.get("eval_cases"),
                "requests": req,
                "round2_requests": round2["num_requests"] if round2["path"] else run.get("round2_requests"),
                "round2_request_summary": round2,
                "summary_request_counts": summary.get("request_counts"),
                "note": run["note"],
            }
        )
    return rows


def markdown_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "| method | run name | private exact | private regex | sensitive pattern | refusal | public overall contains | same_subject_public | same_relation_other_subject | general_knowledge | Round2 requests | note |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {method} | {run_name} | {private_exact} | {private_regex} | {sensitive_pattern} | {refusal} | {public_overall_contains} | {same_subject_public} | {same_relation_other_subject} | {general_knowledge} | {round2_requests} | {note} |".format(
                method=row["method"],
                run_name=row["run_name"],
                private_exact=pct(row.get("private_exact")),
                private_regex=pct(row.get("private_regex")),
                sensitive_pattern=pct(row.get("sensitive_pattern")),
                refusal=pct(row.get("refusal")),
                public_overall_contains=pct(row.get("public_overall_contains")),
                same_subject_public=pct(row.get("same_subject_public")),
                same_relation_other_subject=pct(row.get("same_relation_other_subject")),
                general_knowledge=pct(row.get("general_knowledge")),
                round2_requests="null" if row.get("round2_requests") is None else str(row.get("round2_requests")),
                note=row["note"],
            )
        )
    return "\n".join(lines) + "\n"


def pipeline_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "| run | base model | dataset path | request path | output path | eval path | traceable |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {run} | `{base}` | `{dataset}` | `{request}` | `{output}` | `{evals}` | {traceable} |".format(
                run=row["run_name"],
                base=row.get("base_model") or "null",
                dataset=row.get("dataset_path") or "null",
                request=row.get("request_path") or "null",
                output=row.get("output_path") or "null",
                evals=f"{row['private_eval_path']}; {row['public_eval_path']}",
                traceable="yes" if row.get("traceable") else "no",
            )
        )
    return "\n".join(lines) + "\n"


def write_doc(path: Path, scale: Dict[str, Any], rows: List[Dict[str, Any]], metric_md: str) -> None:
    doc = f"""# V2 Audit and Locality Summary

## 1. Why this audit

本审计用于核对 v2 benchmark 的真实规模、LoRA/ROME/PACE 是否共享同一条实验链路, 以及 public locality damage 的汇报口径是否可追溯。此前口头记录中出现过 50 人口径, 但仓库内 v2 artifact 显示实际生成和评测口径是 100 人, 因此需要单独固化账本, 避免后续 MEMIT baseline 使用错误数据范围。

## 2. Benchmark scale

- people count: `{scale['people_count']}`
- private facts: `{scale['private_facts']}`
- public facts: `{scale['public_facts']}`
- flat cases: `{scale['flat_cases']}`
- train records: `{scale['train_records']}`
- train people: `{scale['train_people']}`
- train private records: `{scale['train_private_records']}`
- train public records: `{scale['train_public_records']}`
- train/eval split or selected subset: 没有发现独立 train/eval split 文件。LoRA 注入使用 100 人全量 synthetic dataset 构造训练记录；ROME direct-only 只编辑 20 人 40 条 private cases；后续 full private/public eval 覆盖 100 人全量 v2 dataset。
- edited people / edited cases: ROME direct-only 为 20 people / 40 cases；PACE target_only 合并后 99 people / 177 cases；PACE max1_per_case 合并后 100 people / 195 cases；PACE max2_per_person 合并后 100 people / 124 cases。

`flat_cases` 在当前数据里表示一个 fact-like case。100 人每人包含 2 条 private facts、4 条 same-subject public facts、4 条 same-relation public facts, 再加 40 条 general_knowledge public cases, 所以总数为 `100 * (2 + 4 + 4) + 40 = 1040`。因此 "50 人 v2" 与当前 artifact 不一致；可信口径应写为 "当前已归档 v2 run 使用 100 人 synthetic benchmark, ROME direct-only 只编辑其中前 20 人的 private facts"。

## 3. Pipeline consistency check

{pipeline_table(rows)}

    审计结论: 现有 v2 ROME/PACE manifests 都指向同一个 merged leakage model `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`, 且 dataset path 都写为 `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`。该 canonical dataset 目录已在 2026-06-17 从 `artifacts/run_20260615_v2_lora_mlp_only/` 恢复, 后续脚本可直接使用该路径。

## 4. Metric summary

{metric_md}
## 5. Current trustworthy conclusion

可靠结论:

- 当前 v2 merged leakage model 是 100 人 synthetic benchmark 上训练和评测得到的, private leakage 高且 public retain 高。
- ROME direct-only 与三组 PACE 都基于同一个 v2 merged leakage model。
- ROME direct-only 只编辑 20 人 40 条 private cases, 但 full private/public eval 覆盖全量 100 人 v2 dataset。
- PACE target_only 和 max1_per_case 基本能把 private exact/regex leak 压到接近 0, 但 public overall contains 掉到约 0.0032/0.0099。
- PACE max2_per_person 保留了更多 public, 但 public overall contains 仍只有 0.0984, 且 private exact/regex 不再为 0。

还不能说:

- 不能说方法已经解决真实预训练 PII 删除。
- 不能说 PACE 在 utility 上成功, 因为 same_subject_public 和 same_relation_other_subject 仍严重受损。
- 不能说当前现象只属于 ROME, 因为 MEMIT baseline 尚未跑出可比结果。

该结果可以支撑简历/汇报中的项目表述, 但应使用诚实口径: "在 synthetic benchmark 上验证模型编辑可显著抑制目标隐私泄露, 同时发现并量化 public/locality collateral damage"。

## 6. Recommended next step

    建议下一步可以准备 MEMIT baseline。路径口径已修复, 但在开 GPU 前仍应在 AutoDL 上跑 preflight 确认服务器模型目录存在:

- MEMIT baseline 应使用同一个 merged model、同一个 v2 dataset、同一套 public/private eval。
- 输出目录建议新建 `/root/autodl-tmp/outputs/easyedit/v2_memit_direct` 和 `artifacts/run_YYYYMMDD_v2_memit_direct/`, 不覆盖任何 ROME/PACE 结果。
- 预计输入包括 merged model、`hparams/MEMIT/qwen2.5-7b.yaml`、v2 direct request JSON 和 v2 dataset；预计输出包括 edit metrics、full private eval、public retain eval、summary JSON 和 runlog。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = load_json(args.dataset)
    if not dataset:
        raise FileNotFoundError(args.dataset)
    train_rows = load_jsonl(args.train_jsonl)
    train_payload = load_json(args.train_dataset)
    scale = benchmark_scale(dataset, train_rows, train_payload)
    rows = build_rows()
    metric_md = markdown_table(rows)
    pipeline_md = pipeline_table(rows)

    payload = {
        "audit_date": "2026-06-17",
        "benchmark_scale": scale,
        "pipeline_consistency": rows,
        "locality_tradeoff_summary": [
            {
                key: row.get(key)
                for key in (
                    "method",
                    "run_name",
                    "private_exact",
                    "private_regex",
                    "sensitive_pattern",
                    "refusal",
                    "public_overall_contains",
                    "same_subject_public",
                    "same_relation_other_subject",
                    "general_knowledge",
                    "round2_requests",
                    "note",
                )
            }
            for row in rows
        ],
        "path_notes": [
            "Manifests reference artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json.",
            "The canonical v2 dataset path was restored from artifacts/run_20260615_v2_lora_mlp_only/ on 2026-06-17.",
        ],
    }

    (output_dir / "locality_tradeoff_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "locality_tradeoff_summary.md").write_text(metric_md, encoding="utf-8")
    (output_dir / "pipeline_consistency.md").write_text(pipeline_md, encoding="utf-8")
    write_doc(Path(args.doc_path), scale, rows, metric_md)
    print(f"wrote: {output_dir / 'locality_tradeoff_summary.json'}")
    print(f"wrote: {output_dir / 'locality_tradeoff_summary.md'}")
    print(f"wrote: {output_dir / 'pipeline_consistency.md'}")
    print(f"wrote: {args.doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
