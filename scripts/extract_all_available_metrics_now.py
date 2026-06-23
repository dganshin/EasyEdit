import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


OUT_DIR = Path("artifacts/result_ledger_20260623")
PAPER_TABLE_DIR = Path("artifacts/paper_assets_20260623/tables")
MISSING = "missing"

FIELDS = [
    "model",
    "dataset",
    "task_type",
    "method",
    "method_family",
    "base_editor",
    "wrapper",
    "n_cases",
    "status",
    "failure_reason",
    "private_value_contains",
    "pii_regex",
    "sensitive_pattern",
    "private_refusal",
    "public_contains",
    "public_refusal",
    "same_subject_public",
    "same_relation_public",
    "general_public",
    "reliability",
    "generalization",
    "locality",
    "runtime_sec",
    "selected_count",
    "selected_subjects",
    "privacy_requests",
    "anchor_requests",
    "source_file",
    "source_status",
    "notes",
]

FAIL_FIELDS = [
    "model",
    "dataset",
    "method",
    "stage",
    "status",
    "failure_reason",
    "source_file",
    "should_retry",
    "retry_priority",
    "paper_handling",
]


def clean_value(value: Any) -> str:
    if value is None or value == "":
        return MISSING
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def row(**kwargs: Any) -> Dict[str, str]:
    payload = {field: MISSING for field in FIELDS}
    for key, value in kwargs.items():
        if key in payload:
            payload[key] = clean_value(value)
    return payload


def fail_row(**kwargs: Any) -> Dict[str, str]:
    payload = {field: MISSING for field in FAIL_FIELDS}
    for key, value in kwargs.items():
        if key in payload:
            payload[key] = clean_value(value)
    return payload


def read_json(path: Path) -> Optional[Any]:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size <= 2:
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow({field: item.get(field, MISSING) for field in fields})


def md_table(rows: List[Dict[str, str]], fields: List[str], limit: Optional[int] = None) -> str:
    selected = rows if limit is None else rows[:limit]
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for item in selected:
        vals = [str(item.get(field, MISSING)).replace("\n", " ") for field in fields]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def method_family(method: str) -> str:
    if "CAPE-Anchor" in method:
        return "closed-loop public-anchor wrapper"
    if method.startswith("CAPE"):
        return "closed-loop side-effect-aware wrapper"
    if method.startswith("PACE"):
        return "closed-loop residual re-edit"
    if method in {"ROME direct", "MEMIT direct", "Fine-tuning", "Knowledge Neurons", "In-context Editing"}:
        return "baseline editor"
    if method == "Leakage model":
        return "pre-edit model"
    return "unknown"


def base_editor(method: str) -> str:
    if "ROME" in method or "PACE" in method or "CAPE" in method:
        return "ROME"
    if "MEMIT" in method:
        return "MEMIT"
    if "Fine-tuning" in method or method == "FT":
        return "FT"
    if "Knowledge" in method or method == "KN":
        return "KN"
    if "In-context" in method or method == "IKE":
        return "IKE"
    return MISSING


def wrapper_type(method: str) -> str:
    if "CAPE-Anchor" in method:
        return "CAPE-Anchor"
    if method.startswith("CAPE"):
        return "CAPE"
    if method.startswith("PACE"):
        return "PACE"
    return "none"


def synthetic_known_rows() -> List[Dict[str, str]]:
    source = "current_task_spec:2026-06-23 GPT review; audit against repo CSVs"
    specs = [
        ("Leakage model", "ok", 0.9387, 0.6650, 0.9927, 0.0000, 0.9766, MISSING),
        ("ROME direct", "ok", 0.5787, 0.4767, 0.8563, 0.5973, 0.5591, 0.2873),
        ("MEMIT direct", "ok", 0.8140, 0.5993, 0.8853, 0.1950, 0.8472, 0.0897),
        ("PACE target_only", "ok", 0.0000, 0.0000, 0.0167, 0.9930, 0.0032, 0.9675),
        ("PACE max1_per_case", "ok", 0.0003, 0.0003, 0.0200, 0.9870, 0.0099, 0.9611),
        ("PACE max2/person", "ok", 0.0243, 0.0150, 0.0740, 0.9347, 0.0984, 0.8052),
        ("CAPE-v0", "ok", 0.0023, 0.0023, 0.0190, 0.9890, 0.0060, 0.9877),
        ("CAPE-v1", "ok", 0.0443, 0.0250, 0.2587, 0.8557, 0.1119, 0.6901),
        ("Fine-tuning", "pending", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
        ("Knowledge Neurons", "pending", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
        ("In-context Editing", "failed", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
        ("PACE-Lite B20-K0", "pending", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
        ("CAPE-Anchor B20-K1", "pending", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
        ("CAPE-Anchor B20-K2", "pending", MISSING, MISSING, MISSING, MISSING, MISSING, MISSING),
    ]
    rows = []
    for method, status, private_value, regex, sensitive, refusal, public_contains, public_refusal in specs:
        notes = "canonical synthetic metric row"
        if status == "pending":
            notes = "pending server artifact"
        if status == "failed":
            notes = "not retrying IKE dependency path"
        rows.append(
            row(
                model="Qwen2.5-7B privacy-v2 merged",
                dataset="synthetic_privacy_v2",
                task_type="privacy_sanitization",
                method=method,
                method_family=method_family(method),
                base_editor=base_editor(method),
                wrapper=wrapper_type(method),
                n_cases=200,
                status=status,
                failure_reason=("missing_or_failed_dependency" if status == "failed" else MISSING),
                private_value_contains=private_value,
                pii_regex=regex,
                sensitive_pattern=sensitive,
                private_refusal=refusal,
                public_contains=public_contains,
                public_refusal=public_refusal,
                source_file=source,
                source_status="canonical_or_pending",
                notes=notes,
            )
        )
    return rows


def public_qwen_rows() -> List[Dict[str, str]]:
    comparison = Path("artifacts/public_benchmarks_20260623_200/public_editing_comparison.json")
    payload = read_json(comparison)
    rows: List[Dict[str, str]] = []
    seen = set()
    if isinstance(payload, dict):
        for item in payload.get("rows", []):
            dataset = item.get("dataset", MISSING)
            method = item.get("method", MISSING)
            seen.add((dataset, method))
            rows.append(
                row(
                    model="Qwen2.5-7B",
                    dataset=f"{dataset}-200",
                    task_type="public_factual_editing",
                    method=method,
                    method_family=("public closed-loop wrapper" if "PACE" in method or "CAPE" in method else "public baseline editor"),
                    base_editor=("ROME" if "ROME" in method else method),
                    wrapper=("PACE-Edit" if "PACE" in method else ("CAPE-Edit" if "CAPE" in method else "none")),
                    n_cases=item.get("num_cases", MISSING),
                    status=item.get("status", MISSING),
                    failure_reason=item.get("failure_error") or MISSING,
                    reliability=item.get("reliability_rewrite_success"),
                    generalization=item.get("generalization_rephrase_success"),
                    locality=item.get("locality_retain_success"),
                    runtime_sec=item.get("elapsed_sec"),
                    source_file=str(comparison),
                    source_status="json_rows",
                    notes=f"method_dir={item.get('method_dir', MISSING)}",
                )
            )
    required = [
        ("counterfact", "ROME_CAPE_EDIT", "missing_artifact", "no summary.json or table row found"),
        ("zsre", "IKE", "missing_artifact", "skipped after dependency/resource issue"),
        ("zsre", "ROME_PACE_EDIT", "missing_artifact", "no summary.json or table row found"),
        ("zsre", "ROME_CAPE_EDIT", "missing_artifact", "no summary.json or table row found"),
    ]
    for dataset, method, status, reason in required:
        if (dataset, method) not in seen:
            rows.append(
                row(
                    model="Qwen2.5-7B",
                    dataset=f"{dataset}-200",
                    task_type="public_factual_editing",
                    method=method,
                    method_family=("public closed-loop wrapper" if "PACE" in method or "CAPE" in method else "public baseline editor"),
                    base_editor=("ROME" if "ROME" in method else method),
                    wrapper=("PACE-Edit" if "PACE" in method else ("CAPE-Edit" if "CAPE" in method else "none")),
                    n_cases=200,
                    status=status,
                    failure_reason=reason,
                    source_file="expected_public_matrix",
                    source_status="missing",
                    notes="required row absent from local artifact",
                )
            )
    return rows


def public_gptj_rows() -> List[Dict[str, str]]:
    fast_patch_table = Path("artifacts/gptj_fast_patch_20260623/table_gptj_public_fast_patch.csv")
    stop_path = Path("artifacts/public_benchmarks_20260623_200/GPTJ_STOP_REASON.md")
    reason = stop_path.read_text(encoding="utf-8").strip().replace("\n", " ") if stop_path.exists() else "GPT-J expansion stopped; no local metrics"
    rows: List[Dict[str, str]] = []
    seen = set()
    for item in read_csv(fast_patch_table):
        dataset = item.get("dataset", MISSING)
        method = item.get("method", MISSING)
        seen.add((dataset, method))
        rows.append(
            row(
                model="GPT-J-6B",
                dataset=dataset,
                task_type="public_factual_editing",
                method=method,
                method_family=("public closed-loop wrapper" if "PACE" in method or "CAPE" in method else ("public optional editor" if method == "MEMIT" else "public fast baseline")),
                base_editor=("ROME" if "PACE" in method or "CAPE" in method else method),
                wrapper=("PACE-Edit" if "PACE" in method else ("CAPE-Edit" if "CAPE" in method else "none")),
                n_cases=item.get("n_cases", MISSING),
                status=item.get("status", MISSING),
                failure_reason=item.get("failure_reason", MISSING),
                reliability=item.get("reliability", MISSING),
                generalization=item.get("generalization", MISSING),
                locality=item.get("locality", MISSING),
                runtime_sec=item.get("runtime_sec", MISSING),
                source_file=item.get("source_file", str(fast_patch_table)),
                source_status=("fast_patch_table" if fast_patch_table.exists() else "missing"),
                notes="GPT-J fast patch only targets ROME/FT by default; missing values are not zero-filled",
            )
        )
    required = [
        ("counterfact-200", "ROME", "partial_without_metrics", "no summary.json found locally"),
        ("counterfact-200", "FT", "partial_without_metrics", "no summary.json found locally"),
        ("counterfact-200", "ROME_PACE_EDIT", "missing_artifact", "GPT-J public PACE-Edit wrapper not completed"),
        ("counterfact-200", "ROME_CAPE_EDIT", "missing_artifact", "GPT-J public CAPE-Edit wrapper not completed"),
        ("counterfact-200", "MEMIT", "missing_artifact", "optional MEMIT skipped unless hparams/stats/smoke are ready"),
        ("counterfact-200", "KN", "stopped", "coarse-neuron search too slow, approximately 50-160s per case; stopped as resource-limited partial check"),
        ("counterfact-200", "IKE", "stopped", "GPT-J expansion stopped before IKE"),
        ("zsre-200", "ROME", "missing_artifact", "no summary.json found locally"),
        ("zsre-200", "FT", "missing_artifact", "no summary.json found locally"),
        ("zsre-200", "ROME_PACE_EDIT", "missing_artifact", "GPT-J public PACE-Edit wrapper not completed"),
        ("zsre-200", "ROME_CAPE_EDIT", "missing_artifact", "GPT-J public CAPE-Edit wrapper not completed"),
        ("zsre-200", "MEMIT", "missing_artifact", "optional MEMIT skipped unless hparams/stats/smoke are ready"),
        ("zsre-200", "KN", "stopped", "coarse-neuron search too slow; not scheduled for GPT-J fast patch"),
        ("zsre-200", "IKE", "stopped", "GPT-J expansion stopped before IKE"),
    ]
    for dataset, method, status, fail_reason in required:
        if (dataset, method) in seen:
            continue
        rows.append(
            row(
                model="GPT-J-6B",
                dataset=dataset,
                task_type="public_factual_editing",
                method=method,
                method_family=("public closed-loop wrapper" if "PACE" in method or "CAPE" in method else ("public optional editor" if method == "MEMIT" else "public partial baseline")),
                base_editor=("ROME" if "PACE" in method or "CAPE" in method else method),
                wrapper=("PACE-Edit" if "PACE" in method else ("CAPE-Edit" if "CAPE" in method else "none")),
                n_cases=200,
                status=status,
                failure_reason=fail_reason,
                source_file=str(stop_path) if stop_path.exists() else "expected_gptj_partial",
                source_status="partial_or_stopped",
                notes=reason,
            )
        )
    return rows


def source_map_rows() -> List[Dict[str, str]]:
    return [
        {"source_file": "artifacts/public_benchmarks_20260623_200/public_editing_comparison.json", "source_status": "present", "metric_mapping": "num_cases->n_cases; reliability_rewrite_success->reliability; generalization_rephrase_success->generalization; locality_retain_success->locality; elapsed_sec->runtime_sec; failure_error->failure_reason"},
        {"source_file": "current_task_spec:2026-06-23 GPT review", "source_status": "provided", "metric_mapping": "synthetic canonical rows and public_refusal conflict guidance"},
        {"source_file": "artifacts/final_comparison_20260623_urgent/method_claim_metrics.csv", "source_status": "present", "metric_mapping": "used for metric audit conflicts, not canonical public_refusal"},
        {"source_file": "artifacts/paper_assets_20260623/tables_tex/table_public_qwen_topconf.tex", "source_status": "present", "metric_mapping": "publication-ready successful Qwen public rows only"},
        {"source_file": "artifacts/public_benchmarks_20260623_200/GPTJ_STOP_REASON.md", "source_status": "present", "metric_mapping": "GPT-J stop reason; no metrics"},
        {"source_file": "artifacts/gptj_fast_patch_20260623/table_gptj_public_fast_patch.csv", "source_status": "optional", "metric_mapping": "GPT-J fast patch ROME/FT metrics when summary.json exists"},
    ]


def failed_rows(all_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    failures: List[Dict[str, str]] = []
    for item in all_rows:
        status = item.get("status", "")
        if status in {"ok"}:
            continue
        method = item.get("method", MISSING)
        dataset = item.get("dataset", MISSING)
        model = item.get("model", MISSING)
        reason = item.get("failure_reason", MISSING)
        should_retry = "no"
        priority = "none"
        paper = "appendix_or_failure_table"
        if item.get("task_type") == "privacy_sanitization" and method in {"Fine-tuning", "Knowledge Neurons", "PACE-Lite B20-K0", "CAPE-Anchor B20-K1", "CAPE-Anchor B20-K2"}:
            should_retry = "yes"
            priority = "high"
            paper = "main_table_if_completed"
        if "ROME_PACE_EDIT" in method or "ROME_CAPE_EDIT" in method:
            should_retry = "optional"
            priority = "low"
            paper = "public_transfer_appendix_only"
        if method == "In-context Editing" or method == "IKE" or "GPT-J" in model or "KN" in method and "zsre" in dataset:
            should_retry = "no"
            priority = "none"
            paper = "failure_table_only"
        failures.append(
            fail_row(
                model=model,
                dataset=dataset,
                method=method,
                stage=item.get("task_type", MISSING),
                status=status,
                failure_reason=reason,
                source_file=item.get("source_file", MISSING),
                should_retry=should_retry,
                retry_priority=priority,
                paper_handling=paper,
            )
        )
    explicit = [
        ("Qwen2.5-7B", "counterfact-200", "IKE", "public_factual_editing", "failed", "missing all-MiniLM-L6-v2 / sentence-transformer dependency", "no", "none", "failure_table_only"),
        ("Qwen2.5-7B", "zsre-200", "KN", "public_factual_editing", "failed", "CUDA OOM during coarse neuron search", "no", "none", "failure_table_only"),
        ("GPT-J-6B", "counterfact-200", "KN", "public_factual_editing", "stopped", "coarse-neuron search too slow, approximately 50-160s per case", "no", "none", "failure_table_only"),
        ("GPT-J-6B", "zsre-200", "all methods", "public_factual_editing", "stopped", "stopped expansion", "no", "none", "failure_table_only"),
    ]
    seen = {(f["model"], f["dataset"], f["method"]) for f in failures}
    for model, dataset, method, stage, status, reason, retry, priority, paper in explicit:
        if (model, dataset, method) in seen:
            continue
        failures.append(fail_row(model=model, dataset=dataset, method=method, stage=stage, status=status, failure_reason=reason, source_file="explicit_failure_rules", should_retry=retry, retry_priority=priority, paper_handling=paper))
    return failures


def metric_audit(all_rows: List[Dict[str, str]]) -> str:
    claim_rows = read_csv(Path("artifacts/final_comparison_20260623_urgent/method_claim_metrics.csv"))
    conflicts = []
    canonical = {r["method"]: r for r in all_rows if r.get("dataset") == "synthetic_privacy_v2"}
    alias = {"PACE": "PACE max2/person", "CAPE-v1": "CAPE-v1", "ROME": "ROME direct"}
    for item in claim_rows:
        method = alias.get(item.get("method", ""), item.get("method", ""))
        if method not in canonical:
            continue
        can_refusal = canonical[method].get("public_refusal")
        claim_refusal = clean_value(item.get("public_refusal"))
        if can_refusal != MISSING and claim_refusal != MISSING and can_refusal != claim_refusal:
            conflicts.append((method, can_refusal, claim_refusal, "public_refusal"))
    lines = [
        "# Metric Audit Report",
        "",
        "This ledger does not run GPU code. Missing values remain `missing`.",
        "",
        "## Conflicts",
    ]
    if not conflicts:
        lines.append("- No checked conflicts found.")
    else:
        for method, canonical_value, other_value, metric in conflicts:
            lines.append(f"- `{method}` `{metric}` conflict: ledger canonical `{canonical_value}` vs `method_claim_metrics.csv` `{other_value}`. Final ledger keeps the current GPT-reviewed canonical values and records the conflict here.")
    lines += [
        "",
        "## Notes",
        "- Public wrapper rows with failed CUDA summaries are recorded as failed, not valid metrics.",
        "- GPT-J rows are partial/stopped rows unless a real `summary.json` exists.",
        "- Synthetic pending rows are intentionally kept as pending rather than filled with zero.",
    ]
    return "\n".join(lines)


def write_summary(all_rows: List[Dict[str, str]], failures: List[Dict[str, str]]) -> None:
    status_counts: Dict[str, int] = {}
    for item in all_rows:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    main = [r for r in all_rows if r["task_type"] == "privacy_sanitization" and r["status"] == "ok"]
    public_ok = [r for r in all_rows if r["task_type"] == "public_factual_editing" and r["model"] == "Qwen2.5-7B" and r["status"] == "ok"]
    text = [
        "# Result Ledger Summary",
        "",
        "Last updated: 2026-06-23",
        "",
        "## 1. 当前可报数字",
        "",
        f"- Synthetic privacy 可进正文主表的有效行：`{len(main)}`。",
        f"- Qwen public 可进公开迁移验证表的有效行：`{len(public_ok)}`。",
        "",
        "## 2. 状态计数",
        "",
        md_table([{"status": k, "count": str(v)} for k, v in sorted(status_counts.items())], ["status", "count"]),
        "",
        "## 3. 正文主表建议",
        "",
        "- Synthetic privacy: Leakage model / ROME direct / MEMIT direct / PACE variants / CAPE variants.",
        "- 如果 urgent main 返回，再加入 FT / KN / CAPE-Anchor K0/K1/K2。",
        "- Public table 主体只放 Qwen CounterFact / zsRE 的真实指标；GPT-J 仅作为 50/100-case ROME/FT fast patch 或附表，不扩 KN/IKE。",
        "",
        "## 4. 附表或失败表",
        "",
        "- IKE dependency failure.",
        "- KN zsRE OOM.",
        "- GPT-J partial/stopped.",
        "- Public wrapper CUDA failed/missing.",
        "",
        "## 5. 下一步唯一值得跑的实验",
        "",
        "CAPE-Anchor B20-K0/K1/K2 and synthetic FT/KN remain the main line. GPT-J is limited to the ROME/FT fast patch if a local model already exists; do not expand GPT-J KN/IKE/MEMIT or new public datasets.",
        "",
        "## 6. 前 30 行 ledger 预览",
        "",
        md_table(all_rows, ["model", "dataset", "method", "status", "private_value_contains", "public_contains", "reliability", "generalization", "failure_reason"], limit=30),
    ]
    write_text(OUT_DIR / "RESULT_LEDGER_SUMMARY.md", "\n".join(text))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_markdown_tables(all_rows: List[Dict[str, str]], synthetic: List[Dict[str, str]], public: List[Dict[str, str]]) -> None:
    write_text(OUT_DIR / "all_available_metrics.md", md_table(all_rows, FIELDS))
    write_text(PAPER_TABLE_DIR / "table_all_available_metrics_now.md", md_table(all_rows, FIELDS))
    write_text(PAPER_TABLE_DIR / "table_public_qwen_metrics_now.md", md_table(public, FIELDS))
    write_text(OUT_DIR / "synthetic_privacy_metrics.md", md_table(synthetic, FIELDS))
    write_text(OUT_DIR / "public_qwen_metrics.md", md_table(public, FIELDS))


def scan_source_files() -> List[Dict[str, str]]:
    roots = [
        Path("artifacts"),
        Path("artifacts/public_benchmarks_20260623_200"),
        Path("artifacts/final_comparison_20260623_urgent"),
        Path("artifacts/paper_assets_20260623"),
        Path("artifacts/run_20260615_v2_rome_direct"),
        Path("artifacts/run_20260622_v2_ft_baseline"),
        Path("artifacts/run_20260622_v2_kn_baseline"),
        Path("artifacts/run_20260622_v2_ike_baseline"),
        Path("artifacts/run_20260623_v2_ft_baseline"),
        Path("artifacts/run_20260623_v2_kn_baseline"),
        Path("artifacts/run_20260623_v2_ike_baseline"),
        Path("artifacts/run_20260623_cape_anchor_rescue"),
    ]
    patterns = ("summary.json", "metrics.json", "eval_summary.json", "private_eval.json", "public_eval.json", "selection_report.json", ".csv", ".md", ".tex")
    rows = []
    seen = set()
    for root in roots:
        if not root.exists():
            rows.append({"source_file": str(root), "source_status": "missing_path", "metric_mapping": MISSING})
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name
            if not (name in patterns or any(name.endswith(suffix) for suffix in patterns)):
                continue
            if path in seen:
                continue
            seen.add(path)
            rows.append({"source_file": str(path), "source_status": "present", "metric_mapping": "scanned_candidate"})
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    synthetic = synthetic_known_rows()
    public_qwen = public_qwen_rows()
    gptj = public_gptj_rows()
    all_rows = [*synthetic, *public_qwen, *gptj]
    failures = failed_rows(all_rows)
    source_rows = [*source_map_rows(), *scan_source_files()]

    write_csv(OUT_DIR / "all_available_metrics.csv", all_rows, FIELDS)
    write_csv(OUT_DIR / "synthetic_privacy_metrics.csv", synthetic, FIELDS)
    write_csv(OUT_DIR / "public_qwen_metrics.csv", public_qwen, FIELDS)
    write_csv(OUT_DIR / "public_gptj_partial_metrics.csv", gptj, FIELDS)
    write_csv(OUT_DIR / "missing_or_failed_runs.csv", failures, FAIL_FIELDS)
    write_csv(OUT_DIR / "result_source_map.csv", source_rows, ["source_file", "source_status", "metric_mapping"])

    write_csv(PAPER_TABLE_DIR / "table_all_available_metrics_now.csv", all_rows, FIELDS)
    write_csv(PAPER_TABLE_DIR / "table_public_qwen_metrics_now.csv", public_qwen, FIELDS)

    write_markdown_tables(all_rows, synthetic, public_qwen)
    write_text(OUT_DIR / "metric_audit_report.md", metric_audit(all_rows))
    write_summary(all_rows, failures)
    print(f"wrote {OUT_DIR}")
    print(f"rows={len(all_rows)} failures={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
