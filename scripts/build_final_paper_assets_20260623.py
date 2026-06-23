#!/usr/bin/env python3
"""Build final paper tables, figures, and result-section text for 2026-06-23.

This script is read-only with respect to experiment artifacts. It consumes the
frozen final CSVs under artifacts/final_comparison_20260623_complete and writes
paper-facing assets under artifacts/final_paper_assets_20260623 plus one docs
result-section file.
"""

from __future__ import annotations

import csv
import math
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(".")
SOURCE_DIR = Path("artifacts/final_comparison_20260623_complete")
URGENT_DIR = Path("artifacts/final_comparison_20260623_urgent")
OUT_DIR = Path("artifacts/final_paper_assets_20260623")
TABLE_DIR = OUT_DIR / "tables"
TEX_DIR = OUT_DIR / "tables_tex"
FIG_DIR = OUT_DIR / "figures"
DOC_PATH = Path("docs/PAPER_FINAL_RESULT_SECTIONS_20260623.md")


def pick_font(candidates: Sequence[str]) -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "DejaVu Sans"


plt.rcParams.update(
    {
        "font.family": pick_font(["Arial", "Helvetica", "Microsoft YaHei", "SimHei", "DejaVu Sans"]),
        "font.size": 9.5,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def ensure_dirs() -> None:
    for path in [TABLE_DIR, TEX_DIR, FIG_DIR, DOC_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fmt_num(value: Any) -> str:
    if value in (None, "", "missing", "NA"):
        return "missing" if value == "missing" else ""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def pct(value: Any) -> str:
    if value in (None, "", "missing", "NA"):
        return "missing" if value == "missing" else ""
    try:
        return f"{float(value) * 100:.1f}"
    except Exception:
        return str(value)


def md_table(rows: List[Dict[str, Any]], fields: Sequence[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def escape_tex(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def tex_table(rows: List[Dict[str, Any]], fields: Sequence[str], caption: str, label: str) -> str:
    tex_fields = [escape_tex(field).replace("↑", r"$\uparrow$").replace("↓", r"$\downarrow$") for field in fields]
    alignment = "l" + "c" * (len(fields) - 1)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\scriptsize",
        rf"\caption{{{escape_tex(caption)}}}",
        rf"\label{{{escape_tex(label)}}}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
        " & ".join(tex_fields) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(escape_tex(row.get(field, "")) for field in fields) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def write_table_bundle(name: str, rows: List[Dict[str, Any]], fields: Sequence[str], caption: str, label: str) -> None:
    write_csv(TABLE_DIR / f"{name}.csv", rows, fields)
    (TABLE_DIR / f"{name}.md").write_text(md_table(rows, fields), encoding="utf-8")
    (TEX_DIR / f"{name}.tex").write_text(tex_table(rows, fields, caption, label), encoding="utf-8")


def short_failure(text: str) -> str:
    if not text:
        return ""
    if "OutOfMemoryError" in text or "CUDA out of memory" in text:
        return "OOM on 48GB GPU"
    if "all-MiniLM-L6-v2" in text or "FileNotFoundError" in text:
        return "missing SentenceTransformer dependency"
    return text[:120]


def synthetic_rows() -> List[Dict[str, Any]]:
    rows = read_csv(SOURCE_DIR / "synthetic_privacy_final.csv")
    out: List[Dict[str, Any]] = []
    source = "artifacts/final_comparison_20260623_complete/synthetic_privacy_final.csv"
    failure_map = {
        "KN": "failed: OOM on 48GB GPU",
        "IKE": "failed: missing SentenceTransformer dependency",
    }
    for row in rows:
        method = row["method"]
        status = row["status"]
        out.append(
            {
                "Method": method,
                "Status": status,
                "Private leak ↓": fmt_num(row["private_value_contains"]) if status == "ok" else failure_map.get(method, status),
                "PII regex ↓": fmt_num(row["pii_regex"]) if status == "ok" else "failed",
                "Sensitive pattern ↓": fmt_num(row["sensitive_pattern"]) if status == "ok" else "failed",
                "Private refusal": fmt_num(row["private_refusal"]) if status == "ok" else "failed",
                "Public contains ↑": fmt_num(row["public_contains"]) if status == "ok" else "failed",
                "Source artifact": source,
            }
        )
    return out


def cape_rows() -> List[Dict[str, Any]]:
    rows = read_csv(SOURCE_DIR / "cape_anchor_final.csv")
    source = "artifacts/final_comparison_20260623_complete/cape_anchor_final.csv"
    return [
        {
            "Variant": row["method"],
            "Status": row["status"],
            "Private leak ↓": fmt_num(row["private_value_contains"]),
            "PII regex ↓": fmt_num(row["pii_regex"]),
            "Private refusal": fmt_num(row["private_refusal"]),
            "Public contains ↑": fmt_num(row["public_contains"]),
            "Interpretation": "higher public retain, weaker privacy" if "K" in row["method"] else "lite privacy-only reference",
            "Source artifact": source,
        }
        for row in rows
    ]


def qwen_public_rows() -> List[Dict[str, Any]]:
    rows = read_csv(SOURCE_DIR / "qwen_public_transfer_final.csv")
    source = "artifacts/final_comparison_20260623_complete/qwen_public_transfer_final.csv"
    out: List[Dict[str, Any]] = []
    for row in rows:
        status = row["status"]
        out.append(
            {
                "Model": "Qwen2.5-7B",
                "Dataset": row["dataset"],
                "Method": row["method"],
                "Status": status if status == "ok" else f"failed: {short_failure(row['failure'])}",
                "Cases": row["num_cases"],
                "Reliability ↑": fmt_num(row["reliability"]) if status == "ok" else "failed",
                "Generalization ↑": fmt_num(row["generalization"]) if status == "ok" else "failed",
                "Locality ↑": fmt_num(row["locality"]) if row["locality"] else "missing",
                "Source artifact": source,
            }
        )
    return out


def gptj_rows() -> List[Dict[str, Any]]:
    rows = read_csv(SOURCE_DIR / "gptj_public_sanity_final.csv")
    audit = {f"{r['dataset']}::{r['method']}": r for r in read_csv(SOURCE_DIR / "gptj_per_case_audit.csv")}
    source = "artifacts/final_comparison_20260623_complete/gptj_public_sanity_final.csv"
    out: List[Dict[str, Any]] = []
    for row in rows:
        dataset = row["dataset"].replace("-200", "")
        audit_row = audit.get(f"{dataset}::{row['method']}", {})
        out.append(
            {
                "Model": "GPT-J-6B",
                "Dataset": dataset,
                "Method": row["method"],
                "Status": "ok",
                "Cases": row["num_cases"],
                "Reliability ↑": fmt_num(row["reliability"]),
                "Generalization ↑": fmt_num(row["generalization"]),
                "Locality ↑": fmt_num(row["locality"]),
                "Per-case rewrite": audit_row.get("post_rewrite_nonzero", ""),
                "Interpretation": "baseline normal" if row["method"] in {"ROME", "FT"} else "wrapper collapse",
                "Source artifact": source,
            }
        )
    return out


def failure_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in read_csv(URGENT_DIR / "synthetic_extra_editors_failure_matrix.csv"):
        if row.get("status") != "ok":
            rows.append(
                {
                    "Scope": "Qwen synthetic privacy",
                    "Method": row.get("method", ""),
                    "Status": row.get("status", ""),
                    "Reason": short_failure(row.get("error", "")),
                    "Policy": "record and do not rerun",
                    "Source artifact": "artifacts/final_comparison_20260623_urgent/synthetic_extra_editors_failure_matrix.csv",
                }
            )
    for row in qwen_public_rows():
        if str(row["Status"]).startswith("failed"):
            rows.append(
                {
                    "Scope": f"Qwen public {row['Dataset']}",
                    "Method": row["Method"],
                    "Status": "failed",
                    "Reason": row["Status"].replace("failed: ", ""),
                    "Policy": "record as resource/dependency limit",
                    "Source artifact": "artifacts/final_comparison_20260623_complete/qwen_public_transfer_final.csv",
                }
            )
    rows.append(
        {
            "Scope": "GPT-J public wrapper",
            "Method": "ROME_PACE_EDIT / ROME_CAPE_EDIT",
            "Status": "ok run, negative result",
            "Reason": "per-case audit confirms wrapper collapse, not path mixup",
            "Policy": "boundary analysis, no GPU rerun",
            "Source artifact": "artifacts/final_comparison_20260623_complete/gptj_per_case_audit.csv",
        }
    )
    return rows


def save_fig(fig: plt.Figure, stem: str) -> None:
    for ext in ["png", "pdf", "svg"]:
        kwargs: Dict[str, Any] = {"bbox_inches": "tight", "facecolor": "white"}
        if ext == "png":
            kwargs["dpi"] = 300
        fig.savefig(FIG_DIR / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def draw_box(ax: plt.Axes, x: float, y: float, w: float, h: float, text: str, fc: str) -> None:
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.04",
        linewidth=1.0,
        edgecolor="#344054",
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)


def draw_arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float) -> None:
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, linewidth=1.0, color="#344054"))


def fig1_framework_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.8, 4.8))
    ax.axis("off")
    stages = [
        ("Synthetic privacy\nbenchmark", "#E8F1FF"),
        ("LoRA controllable\nleakage model", "#E8F1FF"),
        ("Baseline editors\nROME/MEMIT/FT/KN/IKE", "#F8F3E8"),
        ("PACE/CAPE/CAPE-Anchor\nrequest selection", "#EAF7EA"),
        ("Private-public\nmetric audit", "#F3EAF7"),
        ("Paper claim\nand boundary analysis", "#F7F7F7"),
    ]
    xs = [0.25, 2.0, 3.75, 5.5, 7.25, 9.0]
    for idx, (label, color) in enumerate(stages):
        draw_box(ax, xs[idx], 2.15, 1.35, 0.82, label, color)
        if idx < len(stages) - 1:
            draw_arrow(ax, xs[idx] + 1.35, 2.56, xs[idx + 1], 2.56)
    ax.text(0.25, 3.55, "Framework pipeline for privacy knowledge sanitization", fontsize=13, weight="bold")
    ax.text(0.25, 1.15, "Main evidence: Qwen synthetic privacy.  Public benchmarks: transfer and boundary analysis.", fontsize=10)
    ax.set_xlim(0, 10.65)
    ax.set_ylim(0.7, 4.0)
    save_fig(fig, "fig1_framework_pipeline")


def fig2_mechanism() -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.axis("off")
    cols = [
        ("PACE", ["Residual leakage", "Round-2 privacy\nrefusal requests", "Strong privacy,\npublic collapse risk"], "#E8F1FF"),
        ("CAPE", ["Residual leakage", "Locality / budget\nfiltering", "Reduced request set,\nstill privacy-focused"], "#F3EAF7"),
        ("CAPE-Anchor", ["Residual leakage", "Explicit public\nretain anchors", "Privacy-public\ntrade-off point"], "#EAF7EA"),
    ]
    for c, (title, nodes, color) in enumerate(cols):
        x = 0.55 + c * 3.0
        ax.text(x + 0.8, 4.45, title, ha="center", fontsize=12, weight="bold")
        for r, node in enumerate(nodes):
            y = 3.55 - r * 1.15
            draw_box(ax, x, y, 1.6, 0.68, node, color)
            if r < len(nodes) - 1:
                draw_arrow(ax, x + 0.8, y, x + 0.8, y - 0.42)
    ax.text(0.55, 0.45, r"CAPE-Anchor uses $R_{final}=R_{round1}\cup R_{privacy}\cup R_{anchor}$.", fontsize=10.5)
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0.2, 4.9)
    save_fig(fig, "fig2_pace_cape_anchor_mechanism")


def ok_float(row: Dict[str, Any], key: str) -> float | None:
    try:
        if row.get("Status", row.get("status")) != "ok":
            return None
        value = row.get(key, "")
        if value in ("", "failed", "missing"):
            return None
        return float(value)
    except Exception:
        return None


def fig3_synthetic_tradeoff(rows: List[Dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    palette = {
        "Merged pre-edit": "#8C8C8C",
        "Prompt Refusal": "#B0B0B0",
        "ROME": "#4C78A8",
        "MEMIT": "#72B7B2",
        "FT": "#F58518",
        "PACE": "#E45756",
        "CAPE": "#54A24B",
        "PACE_LITE_B20_K0": "#B279A2",
        "CAPE_ANCHOR_B20_K1": "#59A14F",
        "CAPE_ANCHOR_B20_K2": "#9C755F",
    }
    offsets = {
        "Merged pre-edit": (10, 12),
        "Prompt Refusal": (-88, -10),
        "ROME": (10, 8),
        "MEMIT": (10, 8),
        "FT": (10, 10),
        "PACE": (10, 12),
        "CAPE": (10, -16),
        "PACE_LITE_B20_K0": (10, 10),
        "CAPE_ANCHOR_B20_K1": (10, 8),
        "CAPE_ANCHOR_B20_K2": (10, 8),
    }
    for row in rows:
        if row["Status"] != "ok":
            continue
        leak = float(row["Private leak ↓"])
        public = float(row["Public contains ↑"])
        privacy = 1.0 - leak
        ax.scatter(public, privacy, s=84, color=palette.get(row["Method"], "#333333"), edgecolor="white", linewidth=0.8, zorder=3)
        label = row["Method"].replace("CAPE_ANCHOR_", "Anchor ").replace("PACE_LITE_", "PACE-Lite ")
        ax.annotate(label, (public, privacy), xytext=offsets.get(row["Method"], (6, 5)), textcoords="offset points", fontsize=7.8)
    ax.set_xlabel("Public Contains (utility)")
    ax.set_ylabel("1 - Private Value Contains (privacy)")
    ax.set_title("Synthetic privacy-utility trade-off", fontsize=12, pad=10)
    ax.set_xlim(-0.04, 1.05)
    ax.set_ylim(-0.04, 1.05)
    ax.grid(alpha=0.25)
    save_fig(fig, "fig3_synthetic_privacy_utility_tradeoff")


def fig4_anchor_ablation(rows: List[Dict[str, Any]]) -> None:
    labels = [r["Variant"].replace("CAPE_ANCHOR_", "Anchor ").replace("PACE_LITE_", "PACE-Lite ") for r in rows]
    public = [float(r["Public contains ↑"]) for r in rows]
    leak = [float(r["Private leak ↓"]) for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    ax.plot(x, public, marker="o", linewidth=2.0, label="Public Contains ↑", color="#4C78A8")
    ax.plot(x, leak, marker="s", linewidth=2.0, label="Private Leak ↓", color="#E45756")
    for i, (p, l) in enumerate(zip(public, leak)):
        ax.text(i, p + 0.025, f"{p:.3f}", ha="center", fontsize=8, color="#4C78A8")
        ax.text(i, l - 0.055, f"{l:.3f}", ha="center", fontsize=8, color="#E45756")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.78)
    ax.set_ylabel("Rate")
    ax.set_title("CAPE-Anchor ablation trade-off", fontsize=12, pad=10)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    save_fig(fig, "fig4_cape_anchor_ablation_tradeoff")


def fig5_qwen_public(rows: List[Dict[str, Any]]) -> None:
    ok_rows = [r for r in rows if r["Status"] == "ok"]
    labels = [f"{r['Dataset']}\n{r['Method'].replace('ROME_', '')}" for r in ok_rows]
    vals = [float(r["Reliability ↑"]) for r in ok_rows]
    colors = ["#4C78A8" if "EDIT" not in r["Method"] else "#E45756" for r in ok_rows]
    fig, ax = plt.subplots(figsize=(9.0, 4.9))
    ax.bar(range(len(vals)), vals, color=colors, width=0.72)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Reliability")
    ax.set_title("Qwen public transfer: baseline and closed-loop wrapper", fontsize=12, pad=10)
    ax.grid(axis="y", alpha=0.25)
    save_fig(fig, "fig5_public_transfer_qwen")


def fig6_gptj_boundary(rows: List[Dict[str, Any]]) -> None:
    datasets = ["counterfact", "zsre"]
    methods = ["ROME", "FT", "ROME_PACE_EDIT", "ROME_CAPE_EDIT"]
    width = 0.18
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    hatches = {"ROME": "", "FT": "//", "ROME_PACE_EDIT": "..", "ROME_CAPE_EDIT": "xx"}
    for i, method in enumerate(methods):
        vals = []
        for dataset in datasets:
            match = next(r for r in rows if r["Dataset"] == dataset and r["Method"] == method)
            vals.append(float(match["Reliability ↑"]))
        positions = [j + (i - 1.5) * width for j in range(len(datasets))]
        color = "#4C78A8" if method in {"ROME", "FT"} else "#E45756"
        alpha = 0.85 if method in {"ROME", "FT"} else 0.75
        bars = ax.bar(
            positions,
            vals,
            width=width,
            label=method.replace("ROME_", ""),
            color=color,
            alpha=alpha,
            hatch=hatches.get(method, ""),
            edgecolor="white",
            linewidth=0.6,
        )
        for bar, value in zip(bars, vals):
            y = value + 0.025 if value > 0.03 else 0.025
            ax.text(bar.get_x() + bar.get_width() / 2, y, f"{value:.3f}", ha="center", va="bottom", fontsize=7.2, rotation=90 if value < 0.03 else 0)
    ax.set_xticks(range(len(datasets)))
    ax.set_xticklabels(["CounterFact", "zsRE"])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Rewrite reliability")
    ax.set_title("GPT-J Boundary Check: Baselines Remain Strong but Unretuned Wrappers Collapse", fontsize=11.5, pad=10)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.14))
    save_fig(fig, "fig6_gptj_wrapper_boundary_check")


def fig7_failure_summary(rows: List[Dict[str, Any]]) -> None:
    labels = [r["Method"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 4.7))
    ax.barh(range(len(rows)), [1] * len(rows), color=["#E45756", "#F58518", "#E45756", "#F58518", "#B279A2"][: len(rows)])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 1.0)
    ax.set_xticks([])
    ax.set_title("Failure and resource-limit summary", fontsize=12, pad=10)
    for i, row in enumerate(rows):
        ax.text(0.02, i, f"{row['Scope']}: {row['Reason']}", va="center", ha="left", fontsize=8.2, color="white")
    save_fig(fig, "fig7_failure_matrix_summary")


def write_result_sections(
    synthetic: List[Dict[str, Any]],
    cape: List[Dict[str, Any]],
    qwen: List[Dict[str, Any]],
    gptj: List[Dict[str, Any]],
    failures: List[Dict[str, Any]],
) -> None:
    text = """# Paper Final Result Sections 20260623

Last updated: 2026-06-23
Final result status: frozen
No further GPU expansion unless explicitly approved

## 1. Synthetic Privacy Main Results

Qwen synthetic privacy is the main experimental setting for the paper claim. The merged leakage model preserves public facts while leaking private values, with Private Value Contains = 0.9387 and Public Contains = 0.9766. ROME reduces Private Value Contains to 0.5787 while retaining Public Contains = 0.5591, whereas MEMIT keeps stronger public utility (0.8472) but leaves more private leakage (0.8140). FT suppresses the measured private leakage to 0.0000, but its Public Contains falls to 0.0040, which indicates a destructive sanitization behavior rather than a useful privacy-utility trade-off.

PACE and CAPE provide stronger privacy suppression than ROME, with Private Value Contains = 0.0243 and 0.0443 respectively. However, their Public Contains values are only 0.0984 and 0.1119, showing the public-collapse / over-refusal side effect that motivates CAPE-Anchor. Therefore, the main result should not be written as “privacy solved”; it should be written as a structured privacy-utility trade-off analysis.

## 2. CAPE-Anchor Ablation

CAPE-Anchor changes the operating point of closed-loop editing. PACE-Lite B20-K0 obtains Public Contains = 0.4210 with Private Value Contains = 0.3323. CAPE-Anchor K1 further raises Public Contains to 0.6008, with Private Value Contains = 0.4603. CAPE-Anchor K2 reaches Public Contains = 0.6833, but Private Value Contains also rises to 0.6357. These results support Claim A only in the limited sense: CAPE-Anchor forms a more useful privacy-utility trade-off than naive PACE/CAPE, but it is not the lowest-leakage method and not a lossless sanitization method.

## 3. Qwen Public Transfer

The public benchmark is a factual-editing transfer check, not a PII sanitization proof. On Qwen2.5-7B, ROME and FT are strong public-editing baselines on CounterFact and zsRE. The ROME-based PACE/CAPE wrappers are executable on both datasets, but their transfer performance is moderate: CounterFact reliability is 0.5179 and zsRE reliability is 0.3117. This supports only a conservative statement that the closed-loop request-selection idea can be instantiated on public factual-editing tasks, while not outperforming strong ROME/FT baselines.

## 4. GPT-J Second-Model Boundary Check

为检查公开迁移实验是否完全依赖 Qwen2.5-7B，本文在 GPT-J-6B 上进行了第二模型公开事实编辑验证。结果显示，GPT-J-6B 上 ROME 与 FT baseline 均能正常运行，在 CounterFact 与 zsRE 上获得较高 rewrite 成功率。然而，将未重新调参的 ROME-based PACE/CAPE wrapper 直接迁移到 GPT-J-6B 时，wrapper 出现明显塌缩。per-case 审计进一步排除了路径混用和汇总脚本误读的可能。该结果说明，闭环请求扩展策略的跨模型迁移依赖底层编辑器超参数、请求集合规模与局部性约束，后续需要模型特定校准或 retain-aware objective。

## 5. Failure And Resource Limitation

The failure matrix should be reported explicitly rather than hidden. KN on Qwen synthetic privacy failed due to GPU memory pressure on a 48GB instance. IKE failed because the expected SentenceTransformer dependency `./hugging_cache/all-MiniLM-L6-v2` was missing. Qwen public IKE and zsRE KN also failed for dependency or resource reasons. These failures are resource/dependency limits under the current project deadline, not evidence that the main synthetic privacy result is invalid.

## 6. Final Claim Decision

The final claim should use Claim A with conservative wording: CAPE-Anchor provides a limited effective improvement by moving the privacy-utility operating point on Qwen synthetic privacy. Public Qwen experiments are transfer checks, and GPT-J experiments are boundary evidence. The paper must not claim cross-model success for GPT-J, must not present public benchmarks as PII sanitization proof, and must not claim lossless privacy cleaning.

## Evidence Mapping

- Main claim evidence: `artifacts/final_paper_assets_20260623/tables/table1_synthetic_privacy_main.csv`
- CAPE-Anchor evidence: `artifacts/final_paper_assets_20260623/tables/table2_cape_anchor_ablation.csv`
- Qwen public transfer evidence: `artifacts/final_paper_assets_20260623/tables/table3_qwen_public_transfer.csv`
- GPT-J boundary evidence: `artifacts/final_paper_assets_20260623/tables/table4_gptj_boundary_check.csv`
- Failure/resource evidence: `artifacts/final_paper_assets_20260623/tables/table5_failure_and_resource_limits.csv`
"""
    DOC_PATH.write_text(text, encoding="utf-8")


def update_doc_header(path: Path) -> None:
    if not path.exists():
        return
    body = path.read_text(encoding="utf-8")
    header = "Last updated: 2026-06-23\nFinal result status: frozen\nNo further GPU expansion unless explicitly approved\n\n"
    if "Final result status: frozen" in body:
        return
    path.write_text(header + body, encoding="utf-8")


def main() -> int:
    ensure_dirs()
    synthetic = synthetic_rows()
    cape = cape_rows()
    qwen = qwen_public_rows()
    gptj = gptj_rows()
    failures = failure_rows()

    write_table_bundle(
        "table1_synthetic_privacy_main",
        synthetic,
        ["Method", "Status", "Private leak ↓", "PII regex ↓", "Sensitive pattern ↓", "Private refusal", "Public contains ↑", "Source artifact"],
        "Synthetic privacy main results on Qwen privacy model.",
        "tab:synthetic-main",
    )
    write_table_bundle(
        "table2_cape_anchor_ablation",
        cape,
        ["Variant", "Status", "Private leak ↓", "PII regex ↓", "Private refusal", "Public contains ↑", "Interpretation", "Source artifact"],
        "CAPE-Anchor ablation over public-anchor budget.",
        "tab:cape-anchor-ablation",
    )
    write_table_bundle(
        "table3_qwen_public_transfer",
        qwen,
        ["Model", "Dataset", "Method", "Status", "Cases", "Reliability ↑", "Generalization ↑", "Locality ↑", "Source artifact"],
        "Qwen public factual-editing transfer matrix.",
        "tab:qwen-public-transfer",
    )
    write_table_bundle(
        "table4_gptj_boundary_check",
        gptj,
        ["Model", "Dataset", "Method", "Status", "Cases", "Reliability ↑", "Generalization ↑", "Locality ↑", "Per-case rewrite", "Interpretation", "Source artifact"],
        "GPT-J-6B second-model boundary check.",
        "tab:gptj-boundary",
    )
    write_table_bundle(
        "table5_failure_and_resource_limits",
        failures,
        ["Scope", "Method", "Status", "Reason", "Policy", "Source artifact"],
        "Failure and resource-limit matrix.",
        "tab:failure-resource",
    )

    fig1_framework_pipeline()
    fig2_mechanism()
    fig3_synthetic_tradeoff(synthetic)
    fig4_anchor_ablation(cape)
    fig5_qwen_public(qwen)
    fig6_gptj_boundary(gptj)
    fig7_failure_summary(failures)

    write_result_sections(synthetic, cape, qwen, gptj, failures)
    for doc in [
        Path("docs/FINAL_RESULTS_REPORT_FOR_GPT_20260623.md"),
        Path("docs/METHOD_CLAIM_DECISION.md"),
        Path("docs/PAPER_WRITING_STATE_20260623.md"),
        Path("docs/FIGURE_TABLE_PLAN_20260623.md"),
        Path("docs/CLAIM_AND_WORDING_GUIDE_20260623.md"),
    ]:
        update_doc_header(doc)

    print(f"wrote {OUT_DIR}")
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
