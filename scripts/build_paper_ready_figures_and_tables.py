import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(".")
DEFAULT_OUT = Path("artifacts/final_comparison_20260622")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build paper-ready tables and figures from existing EasyEdit experiment artifacts.")
    parser.add_argument("--output_dir", default=str(DEFAULT_OUT), type=str)
    parser.add_argument("--analysis_dir", default="artifacts/analysis_v2_audit_20260622", type=str)
    parser.add_argument("--public_root", default="artifacts/public_benchmarks_20260623_200", type=str)
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


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_csv_aliases(
    rows_by_name: Dict[str, List[Dict[str, Any]]],
    table_dir: Path,
    out_dir: Path,
) -> None:
    aliases = {
        "table_synthetic_main_results.csv": "table_synthetic_main_results.csv",
        "table_synthetic_extra_editors.csv": "table_synthetic_extra_editors.csv",
        "table_cape_anchor_rescue.csv": "table_cape_anchor_rescue.csv",
        "table_public_wrapper_qwen.csv": "table_public_wrapper_qwen.csv",
    }
    for source_name, alias_name in aliases.items():
        rows = rows_by_name.get(source_name, [])
        src = table_dir / source_name
        dst = out_dir / alias_name
        if src.exists():
            copy_if_exists(src, dst)
        else:
            write_csv(dst, rows)


def copy_figure_aliases(fig_dir: Path, out_dir: Path) -> None:
    aliases = {
        "fig_privacy_utility_tradeoff.png": "fig_privacy_utility_tradeoff.png",
        "fig_public_refusal_comparison.png": "fig_public_refusal_comparison.png",
        "fig_attack_type_breakdown.png": "fig_attack_type_breakdown.png",
    }
    for src_name, dst_name in aliases.items():
        src = fig_dir / src_name
        dst = out_dir / dst_name
        copy_if_exists(src, dst)


def pick_overall(path: Path) -> Dict[str, Any]:
    payload = read_json(path) or {}
    return payload.get("overall") or {}


def synthetic_method_rows() -> List[Dict[str, Any]]:
    specs = [
        ("Merged pre-edit", "available", Path("artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_merged_v2.json"), Path("artifacts/run_20260615_v2_rome_direct/public_retain_eval_merged_v2.json")),
        ("Prompt Refusal", "optional", Path("artifacts/run_20260622_v2_prompt_refusal/privacy_leakage_eval_v2_prompt_refusal_full.json"), Path("artifacts/run_20260622_v2_prompt_refusal/public_retain_eval_v2_prompt_refusal.json")),
        ("ROME", "available", Path("artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json"), Path("artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json")),
        ("MEMIT", "available", Path("artifacts/run_20260622_v2_memit_direct/privacy_leakage_eval_v2_memit_direct_full.json"), Path("artifacts/run_20260622_v2_memit_direct/public_retain_eval_v2_memit_direct.json")),
        ("FT", "pending", Path("artifacts/run_20260622_v2_ft_baseline/privacy_leakage_eval_v2_ft_baseline_full.json"), Path("artifacts/run_20260622_v2_ft_baseline/public_retain_eval_v2_ft_baseline.json")),
        ("KN", "pending", Path("artifacts/run_20260622_v2_kn_baseline/privacy_leakage_eval_v2_kn_baseline_full.json"), Path("artifacts/run_20260622_v2_kn_baseline/public_retain_eval_v2_kn_baseline.json")),
        ("IKE", "pending", Path("artifacts/run_20260622_v2_ike_baseline/privacy_leakage_eval_v2_ike_baseline_full.json"), Path("artifacts/run_20260622_v2_ike_baseline/public_retain_eval_v2_ike_baseline.json")),
        ("PACE", "available", Path("artifacts/run_20260615_v2_pace_max2_per_person/privacy_leakage_eval_v2_pace_max2_per_person_full.json"), Path("artifacts/run_20260615_v2_pace_max2_per_person/public_retain_eval_v2_pace_max2_per_person.json")),
        ("CAPE", "available", Path("artifacts/run_20260622_v2_cape_v1_top20_tau07_direct/privacy_leakage_eval_v2_cape_v1_top20_tau07_direct_full.json"), Path("artifacts/run_20260622_v2_cape_v1_top20_tau07_direct/public_retain_eval_v2_cape_v1_top20_tau07_direct.json")),
    ]
    rows: List[Dict[str, Any]] = []
    for method, planned_status, private_path, public_path in specs:
        private = pick_overall(private_path)
        public = pick_overall(public_path)
        status = "ok" if private or public else planned_status
        rows.append(
            {
                "method": method,
                "status": status,
                "private_value_contains": private.get("target_exact_leak_rate"),
                "private_regex": private.get("target_regex_leak_rate"),
                "sensitive_pattern": private.get("sensitive_pattern_rate"),
                "private_refusal": private.get("safe_refusal_rate"),
                "public_contains": public.get("contains_match_rate"),
                "public_exact": public.get("exact_match_rate"),
                "private_eval": str(private_path),
                "public_eval": str(public_path),
            }
        )
    return rows


def cape_anchor_rows() -> List[Dict[str, Any]]:
    candidates = [
        Path("artifacts/final_comparison_20260623_urgent/cape_anchor_rescue_results.csv"),
        Path("artifacts/run_20260623_cape_anchor_rescue/cape_anchor_rescue_results.csv"),
    ]
    rows: List[Dict[str, Any]] = []
    for path in candidates:
        for row in read_csv(path):
            if (row.get("status") or "").lower() != "ok":
                continue
            rows.append(
                {
                    "method": row.get("config"),
                    "status": row.get("status"),
                    "private_value_contains": row.get("private_value_contains"),
                    "private_regex": row.get("private_regex"),
                    "sensitive_pattern": row.get("sensitive_pattern"),
                    "private_refusal": row.get("private_refusal"),
                    "public_contains": row.get("public_contains"),
                    "public_exact": row.get("public_exact"),
                    "private_eval": row.get("summary_path"),
                    "public_eval": row.get("summary_path"),
                }
            )
        if rows:
            break
    return rows


def public_rows(public_root: Path, out_dir: Path) -> List[Dict[str, Any]]:
    candidates = [
        out_dir / "public_counterfact_zsre_all_models.csv",
        Path("artifacts/final_comparison_20260623_200/public_counterfact_zsre_all_models.csv"),
        Path("artifacts/final_comparison_20260622/public_counterfact_zsre_all_models.csv"),
        public_root / "public_editing_comparison.csv",
        Path("artifacts/final_comparison_20260622/public_editing_baseline_comparison.csv"),
    ]
    for path in candidates:
        rows = read_csv(path)
        if rows:
            return rows
    return []


def public_qwen_wrapper_rows(public: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for row in public:
        method = str(row.get("method") or row.get("editor") or row.get("method_name") or "")
        model = str(row.get("model") or row.get("model_name") or row.get("model_slug") or "")
        path = " ".join(str(value) for value in row.values())
        is_wrapper = "PACE" in method or "CAPE" in method or "PACE" in path or "CAPE" in path
        is_qwen = "qwen" in model.lower() or "qwen" in path.lower()
        if is_wrapper and is_qwen:
            rows.append(row)
    return rows


def selection_rows(public_root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for report_path in sorted(public_root.rglob("selection_report.json")):
        payload = read_json(report_path) or {}
        parts = report_path.parts
        model_slug = ""
        dataset = payload.get("dataset")
        for part in parts:
            if part.startswith("qwen_") or part.startswith("gptj_"):
                model_slug = part.split("_", 1)[0]
                if not dataset:
                    dataset = part.split("_", 1)[1]
        rows.append(
            {
                "model": model_slug,
                "dataset": dataset,
                "base_method": payload.get("base_method"),
                "candidate_count": payload.get("candidate_count"),
                "selected_count": payload.get("selected_count"),
                "pace_selected_count": payload.get("pace_selected_count"),
                "cape_selected_count": payload.get("cape_selected_count"),
                "round1_count": payload.get("round1_count"),
                "round2_count": payload.get("round2_count"),
                "union_count": payload.get("union_count"),
                "skipped_by_locality_risk": payload.get("skipped_by_locality_risk"),
                "skipped_by_subject_or_relation_budget": payload.get("skipped_by_subject_or_relation_budget"),
                "report_path": str(report_path),
            }
        )
    return rows


def metric_definition_rows() -> List[Dict[str, str]]:
    return [
        {"metric": "Private Value Contains", "definition": "Target private value appears as a normalized substring in model output.", "numerator": "private attack predictions containing target value", "denominator": "evaluated private attack predictions", "dataset": "synthetic privacy", "limitation": "substring match, not strict exact equality", "paper_position": "metrics and main synthetic table"},
        {"metric": "PII-format Regex", "definition": "Output matches phone/email/id-like sensitive pattern for the target attribute.", "numerator": "private predictions with regex match", "denominator": "evaluated private attack predictions", "dataset": "synthetic privacy", "limitation": "mostly covers phone/email/id formats", "paper_position": "metric audit and privacy table"},
        {"metric": "Sensitive Pattern", "definition": "Output contains generic sensitive-format pattern regardless of target equality.", "numerator": "outputs containing sensitive format", "denominator": "evaluated private attack predictions", "dataset": "synthetic privacy", "limitation": "can count hallucinated sensitive-looking strings", "paper_position": "over-refusal and safety analysis"},
        {"metric": "Private Refusal", "definition": "Private attack output contains the configured refusal text.", "numerator": "private predictions containing refusal template", "denominator": "evaluated private attack predictions", "dataset": "synthetic privacy", "limitation": "does not exclude refuse-and-leak cases by itself", "paper_position": "privacy behavior analysis"},
        {"metric": "Public Contains", "definition": "Public fact value appears as a normalized substring in output.", "numerator": "public predictions containing expected value", "denominator": "evaluated public prompts", "dataset": "synthetic privacy public retain", "limitation": "loose contains metric, not strict factual accuracy", "paper_position": "utility columns"},
        {"metric": "Public Refusal", "definition": "Public prompt output contains refusal text.", "numerator": "public predictions containing refusal template", "denominator": "evaluated public prompts", "dataset": "synthetic privacy public retain", "limitation": "captures over-refusal, not all public errors", "paper_position": "over-refusal figure"},
        {"metric": "Reliability", "definition": "Post-edit rewrite success on edited public factual prompts.", "numerator": "successful rewrite predictions", "denominator": "evaluated rewrite prompts", "dataset": "CounterFact/zsRE", "limitation": "public editing metric, not PII cleaning metric", "paper_position": "public benchmark table"},
        {"metric": "Generalization", "definition": "Post-edit rephrase success.", "numerator": "successful rephrase predictions", "denominator": "evaluated rephrase prompts", "dataset": "CounterFact/zsRE", "limitation": "depends on benchmark rephrase templates", "paper_position": "public benchmark table"},
        {"metric": "Locality", "definition": "Retain success on unrelated locality prompts.", "numerator": "locality predictions preserved", "denominator": "evaluated locality prompts", "dataset": "CounterFact/zsRE", "limitation": "proxy for side effects on public knowledge", "paper_position": "public wrapper table"},
    ]


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def plot_bar(path: Path, rows: List[Dict[str, Any]], x_key: str, y_key: str, title: str, ylabel: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        path.with_suffix(path.suffix + ".error.txt").write_text(str(exc), encoding="utf-8")
        return
    filtered = [row for row in rows if row.get(y_key) not in (None, "")]
    if not filtered:
        path.with_suffix(path.suffix + ".missing.txt").write_text(f"No data for {y_key}\n", encoding="utf-8")
        return
    labels = [str(row.get(x_key)) for row in filtered]
    values = [float(row.get(y_key)) for row in filtered]
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC"]
    ax.bar(labels, values, color=[colors[i % len(colors)] for i in range(len(values))])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(1.0, max(values) * 1.15))
    ax.tick_params(axis="x", labelrotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def plot_tradeoff(path: Path, rows: List[Dict[str, Any]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        path.with_suffix(path.suffix + ".error.txt").write_text(str(exc), encoding="utf-8")
        return
    points = []
    for row in rows:
        private = row.get("private_value_contains")
        public = row.get("public_contains")
        if private in (None, "") or public in (None, ""):
            continue
        points.append((str(row["method"]), float(public), 1.0 - float(private)))
    if not points:
        path.with_suffix(path.suffix + ".missing.txt").write_text("No tradeoff points.\n", encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for label, utility, privacy in points:
        ax.scatter(utility, privacy, s=70)
        ax.annotate(label, (utility, privacy), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Utility: Public Contains")
    ax.set_ylabel("Privacy: 1 - Private Value Contains")
    ax.set_title("Privacy-Utility Trade-off")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def plot_cape_anchor_tradeoff(path: Path, rows: List[Dict[str, Any]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        path.with_suffix(path.suffix + ".error.txt").write_text(str(exc), encoding="utf-8")
        return
    points = []
    for row in rows:
        private = row.get("private_value_contains")
        public = row.get("public_contains")
        if private in (None, "") or public in (None, ""):
            continue
        points.append((str(row.get("method")), float(public), 1.0 - float(private)))
    if not points:
        path.with_suffix(path.suffix + ".missing.txt").write_text("No CAPE-Anchor rescue points.\n", encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for label, utility, privacy in points:
        ax.scatter(utility, privacy, s=80)
        ax.annotate(label, (utility, privacy), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Utility: Public Contains")
    ax.set_ylabel("Privacy: 1 - Private Value Contains")
    ax.set_title("CAPE-Anchor Rescue Trade-off")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    analysis_dir = Path(args.analysis_dir)
    public_root = Path(args.public_root)
    table_dir = out_dir / "paper_tables"
    fig_dir = out_dir / "paper_figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    synthetic = synthetic_method_rows()
    cape_anchor = cape_anchor_rows()
    synthetic_with_anchor = synthetic + cape_anchor
    public = public_rows(public_root, out_dir)
    qwen_public_wrappers = public_qwen_wrapper_rows(public)
    selections = selection_rows(public_root)
    metrics = metric_definition_rows()

    write_csv(table_dir / "table_synthetic_main_results.csv", synthetic_with_anchor)
    write_csv(table_dir / "table_synthetic_extra_editors.csv", synthetic)
    write_csv(table_dir / "table_cape_anchor_rescue.csv", cape_anchor)
    write_csv(table_dir / "table_public_baseline_counterfact_zsre.csv", public)
    write_csv(table_dir / "table_public_wrapper_pace_cape.csv", [row for row in public if "PACE" in str(row.get("method")) or "CAPE" in str(row.get("method"))])
    write_csv(table_dir / "table_public_wrapper_qwen.csv", qwen_public_wrappers)
    write_csv(table_dir / "table_pace_cape_selection_stats.csv", selections)
    write_csv(table_dir / "table_metric_definitions.csv", metrics)

    copy_if_exists(analysis_dir / "attack_type_breakdown.csv", table_dir / "attack_type_breakdown.csv")
    copy_if_exists(analysis_dir / "over_refusal_stats.csv", table_dir / "over_refusal_stats.csv")
    copy_if_exists(analysis_dir / "tradeoff_points.csv", table_dir / "tradeoff_points.csv")
    copy_if_exists(analysis_dir / "privacy_utility_tradeoff.png", fig_dir / "fig_privacy_utility_tradeoff_existing.png")

    plot_tradeoff(fig_dir / "fig_privacy_utility_tradeoff.png", synthetic_with_anchor)
    plot_cape_anchor_tradeoff(fig_dir / "fig_cape_anchor_rescue_tradeoff.png", cape_anchor)
    plot_bar(fig_dir / "fig_public_refusal_comparison.png", read_csv(analysis_dir / "over_refusal_stats.csv"), "method", "public_refusal_rate", "Public Refusal Comparison", "Public Refusal Rate")
    plot_bar(fig_dir / "fig_attack_type_breakdown.png", read_csv(analysis_dir / "attack_type_breakdown.csv"), "attack_type", "private_exact", "Attack-Type Private Leakage", "Private Value Contains")
    plot_bar(fig_dir / "fig_public_benchmark_reliability_locality.png", public, "method", "locality", "Public Benchmark Locality", "Locality")
    (fig_dir / "fig_pipeline_overview_placeholder.png.missing.txt").write_text("Pipeline overview is a schematic figure; use existing PPT/Word figure or redraw manually.\n", encoding="utf-8")

    write_csv_aliases(
        {
            "table_synthetic_main_results.csv": synthetic_with_anchor,
            "table_synthetic_extra_editors.csv": synthetic,
            "table_cape_anchor_rescue.csv": cape_anchor,
            "table_public_wrapper_qwen.csv": qwen_public_wrappers,
        },
        table_dir,
        out_dir,
    )
    copy_figure_aliases(fig_dir, out_dir)

    report = [
        "# Paper-Ready Figures and Tables Report",
        "",
        f"- synthetic rows: `{len(synthetic_with_anchor)}`",
        f"- CAPE-Anchor rescue rows: `{len(cape_anchor)}`",
        f"- public rows: `{len(public)}`",
        f"- Qwen public wrapper rows: `{len(qwen_public_wrappers)}`",
        f"- PACE/CAPE selection rows: `{len(selections)}`",
        "",
        "Missing values are intentionally left blank or marked pending/not_run. Do not treat them as completed results.",
        "",
        "## Outputs",
        "",
        f"- tables: `{table_dir.as_posix()}`",
        f"- figures: `{fig_dir.as_posix()}`",
    ]
    (out_dir / "PAPER_READY_FIGURES_AND_TABLES_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"tables: {table_dir}")
    print(f"figures: {fig_dir}")
    print(f"report: {out_dir / 'PAPER_READY_FIGURES_AND_TABLES_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
