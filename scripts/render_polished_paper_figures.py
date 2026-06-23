import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


FIG_DIR = Path("artifacts/paper_assets_20260623/figures")
TABLE_DIR = Path("artifacts/paper_assets_20260623/tables")
NOTE_DIR = Path("artifacts/paper_assets_20260623/figure_notes")
PENDING = "[pending]"


def pick_font(candidates: List[str]) -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "DejaVu Sans"


plt.rcParams.update(
    {
        "font.family": pick_font(["Microsoft YaHei", "SimHei", "Source Han Sans SC", "Arial Unicode MS", "DejaVu Sans"]),
        "font.size": 10,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)


def save_all(fig, stem: str) -> None:
    for ext in ("png", "svg", "pdf"):
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if ext == "png":
            kwargs["dpi"] = 300
        fig.savefig(FIG_DIR / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def write_note(stem: str, title: str, data: str, pending: str, message: str) -> None:
    (NOTE_DIR / f"{stem}.md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- Data source: {data}",
                f"- Pending elements: {pending}",
                "",
                message,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def draw_box(
    ax,
    xy: Tuple[float, float],
    text: str,
    width: float = 1.8,
    height: float = 0.52,
    fc: str = "#F7F8FA",
    fontsize: float = 9,
) -> None:
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.03,rounding_size=0.06",
        linewidth=1.0,
        edgecolor="#2F3A4A",
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize)


def draw_arrow(ax, start: Tuple[float, float], end: Tuple[float, float]) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#2F3A4A"))


def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.axis("off")
    top = [
        ("Synthetic\nprivacy benchmark", "#F2F5FA"),
        ("MLP-only LoRA\ninjection", "#F2F5FA"),
        ("Merged leakage\nmodel", "#F2F5FA"),
        ("Editor baselines\nROME / MEMIT / FT / KN", "#F8F8F3"),
    ]
    bottom = [
        ("PACE residual\nre-edit", "#FFF5F3"),
        ("CAPE / CAPE-Anchor\nrequest selection", "#F2FFF6"),
        ("Private / public\nevaluation", "#F8F8F3"),
        ("Paper tables\nand figures", "#F8F8F3"),
    ]
    xs = [0.5, 3.0, 5.5, 8.0]
    for i, (label, color) in enumerate(top):
        draw_box(ax, (xs[i], 3.25), label, width=1.9, height=0.72, fc=color, fontsize=8.2)
        if i < len(top) - 1:
            draw_arrow(ax, (xs[i] + 1.9, 3.61), (xs[i + 1], 3.61))
    draw_arrow(ax, (8.95, 3.25), (8.95, 2.25))
    for i, (label, color) in enumerate(bottom):
        x = xs[3 - i]
        draw_box(ax, (x, 1.45), label, width=1.9, height=0.72, fc=color, fontsize=8.2)
        if i < len(bottom) - 1:
            draw_arrow(ax, (x, 1.81), (xs[2 - i] + 1.9, 1.81))
    ax.set_xlim(0.1, 10.4)
    ax.set_ylim(0.8, 4.55)
    ax.text(0.45, 4.28, "End-to-end privacy knowledge sanitization workflow", fontsize=12, weight="bold")
    save_all(fig, "fig1_pipeline_overview")
    write_note(
        "fig1_pipeline_overview",
        "图1 总体技术路线",
        "Method design from project scripts and current experiment state docs.",
        "None.",
        "该图用于论文方法总览，强调 synthetic benchmark、可控泄露模型、多编辑器比较与闭环请求选择的关系。",
    )


def fig_request_construction() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.axis("off")
    columns = [
        ("PACE", ["Residual leakage", "Privacy refusal\nrequests"], "#EFF6FF"),
        ("CAPE", ["Residual leakage", "Locality risk /\nsubject budget", "Filtered privacy\nrequests"], "#F7F4FF"),
        ("CAPE-Anchor", ["Residual leakage", "Public anchors", "Privacy refusal +\npublic retain requests"], "#F2FFF6"),
    ]
    for c, (title, nodes, color) in enumerate(columns):
        x = 0.6 + c * 3.25
        ax.text(x + 0.75, 4.65, title, ha="center", fontsize=12, weight="bold")
        for r, node in enumerate(nodes):
            y = 3.7 - r * 1.15
            draw_box(ax, (x, y), node, width=1.55, height=0.65, fc=color)
            if r < len(nodes) - 1:
                draw_arrow(ax, (x + 0.78, y), (x + 0.78, y - 0.48))
    ax.text(0.55, 0.45, r"$R_{final}=R_{round1}\cup R_{privacy}\cup R_{anchor}$ for CAPE-Anchor", fontsize=11)
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0.1, 5.0)
    save_all(fig, "fig2_request_construction")
    write_note(
        "fig2_request_construction",
        "图2 PACE/CAPE/CAPE-Anchor 请求构造对比",
        "Scripts build_pace_reedit_requests.py, build_cape_reedit_requests.py, build_cape_anchor_requests.py.",
        "CAPE-Anchor result values are pending.",
        "该图突出 CAPE-Anchor 的方法差异：公开锚点从隐式风险约束变为显式二轮请求组成部分。",
    )


def completed_points() -> List[Dict[str, float]]:
    return [
        {"method": "Merged", "public_contains": 0.9766, "private_value": 0.9387},
        {"method": "ROME", "public_contains": 0.5591, "private_value": 0.5787},
        {"method": "MEMIT", "public_contains": 0.8472, "private_value": 0.8140},
        {"method": "PACE", "public_contains": 0.0984, "private_value": 0.0243},
        {"method": "CAPE-v0", "public_contains": 0.0060, "private_value": 0.0023},
        {"method": "CAPE-v1", "public_contains": 0.1119, "private_value": 0.0443},
    ]


def fig_tradeoff() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    colors = {
        "Merged": "#7A7A7A",
        "ROME": "#4C78A8",
        "MEMIT": "#72B7B2",
        "PACE": "#E45756",
        "CAPE-v0": "#B279A2",
        "CAPE-v1": "#54A24B",
    }
    for row in completed_points():
        x = row["public_contains"]
        y = 1 - row["private_value"]
        ax.scatter(x, y, s=80, color=colors.get(row["method"], "#333333"), edgecolor="white", linewidth=0.8, zorder=3)
        offsets = {
            "Merged": (-40, 10),
            "ROME": (10, 8),
            "MEMIT": (10, -8),
            "PACE": (10, 16),
            "CAPE-v0": (10, -16),
            "CAPE-v1": (12, -4),
        }
        ax.annotate(row["method"], (x, y), xytext=offsets.get(row["method"], (6, 5)), textcoords="offset points", fontsize=8.5)
    for x, label, off in [(0.24, "Anchor K1\npending", (-18, -42)), (0.42, "Anchor K2\npending", (8, -42))]:
        ax.scatter(x, 0.86, s=75, marker="s", facecolor="none", edgecolor="#8C8C8C", linestyle="--")
        ax.annotate(label, (x, 0.86), xytext=off, textcoords="offset points", fontsize=8, color="#666666")
    ax.set_xlabel("Public Contains (utility)")
    ax.set_ylabel("1 - Private Value Contains (privacy)")
    ax.set_xlim(-0.03, 1.08)
    ax.set_ylim(-0.04, 1.08)
    ax.grid(alpha=0.22, linewidth=0.7)
    ax.set_title("Privacy-utility trade-off on synthetic privacy v2", fontsize=12, pad=10)
    save_all(fig, "fig3_privacy_utility_tradeoff")
    write_note(
        "fig3_privacy_utility_tradeoff",
        "图3 隐私压制—知识保持权衡",
        "Known synthetic v2 results and pending CAPE-Anchor placeholders.",
        "CAPE-Anchor K1/K2 points are placeholders until server artifacts return.",
        "该图用于说明隐私压制与公开知识保持之间的结构性权衡，不把 pending 点当作结果。",
    )


def fig_public_refusal() -> None:
    rows = [
        ("ROME", 0.2873, False),
        ("PACE", 0.8052, False),
        ("CAPE-v0", 0.9877, False),
        ("CAPE-v1", 0.6901, False),
        ("Anchor K1", 0.0, True),
        ("Anchor K2", 0.0, True),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    labels = [r[0] for r in rows]
    values = [r[1] if not r[2] else math.nan for r in rows]
    bars = ax.bar(labels[:4], values[:4], color=["#4C78A8", "#E45756", "#B279A2", "#54A24B"], width=0.6)
    for bar, value in zip(bars, values[:4]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center", fontsize=8)
    for i, label in enumerate(labels[4:], start=4):
        ax.bar(i, 1.0, color="none", edgecolor="#999999", linestyle="--", width=0.6)
        ax.text(i, 0.5, PENDING, ha="center", va="center", rotation=90, fontsize=8, color="#666666")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Public Refusal")
    ax.set_title("Public refusal under closed-loop privacy editing", fontsize=12, pad=10)
    ax.grid(axis="y", alpha=0.22)
    save_all(fig, "fig4_public_refusal_comparison")
    write_note(
        "fig4_public_refusal_comparison",
        "图4 Public Refusal 对比",
        "Known synthetic v2 public refusal values; CAPE-Anchor pending.",
        "Anchor K1/K2 are pending.",
        "该图强调 PACE/CAPE 的主要副作用是公开问题过度拒答，CAPE-Anchor 用于检验显式锚点能否缓解该副作用。",
    )


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fig_attack_breakdown() -> None:
    path = Path("artifacts/analysis_v2_audit_20260622/attack_type_breakdown.csv")
    rows = read_csv(path)
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    if rows and "attack_type" in rows[0]:
        labels = [row.get("attack_type", "") for row in rows]
        metric_key = "private_exact" if "private_exact" in rows[0] else next((k for k in rows[0] if k != "attack_type"), None)
        if metric_key:
            values = [float(row.get(metric_key) or 0) for row in rows]
            ax.bar(labels, values, color="#4C78A8", width=0.62)
            ax.set_ylabel(metric_key)
            pending = "None."
        else:
            ax.text(0.5, 0.5, "attack-type metric pending", ha="center", va="center", transform=ax.transAxes)
            pending = "Metric column not found."
    else:
        labels = ["direct", "paraphrase", "completion", "roleplay", "context"]
        ax.bar(labels, [0] * len(labels), color="none", edgecolor="#999999", linestyle="--")
        ax.text(0.5, 0.5, "pending server result", ha="center", va="center", transform=ax.transAxes, color="#666666")
        pending = "Attack-type CSV not found or empty."
    ax.set_title("Attack-type leakage breakdown", fontsize=12, pad=10)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.22)
    save_all(fig, "fig5_attack_type_breakdown")
    write_note(
        "fig5_attack_type_breakdown",
        "图5 Attack-type breakdown",
        str(path),
        pending,
        "该图用于展示不同攻击模板下的隐私泄露差异。若当前数据缺失，服务器结果回传后重新运行脚本即可刷新。",
    )


def fig_public_placeholder() -> None:
    datasets = ["CounterFact", "zsRE"]
    methods = ["ROME", "FT", "KN", "ROME+PACE", "ROME+CAPE"]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for i, method in enumerate(methods):
        xs = [j + (i - 2) * 0.12 for j in range(len(datasets))]
        ax.bar(xs, [0.02, 0.02], width=0.1, color="none", edgecolor="#9A9A9A", linestyle="--")
    ax.text(0.5, 0.55, "Qwen public benchmark pending", transform=ax.transAxes, ha="center", va="center", fontsize=11, color="#666666")
    ax.set_xticks(range(len(datasets)))
    ax.set_xticklabels(datasets)
    ax.set_ylabel("Reliability / Locality")
    ax.set_ylim(0, 1.0)
    ax.set_title("Public factual editing migration validation", fontsize=12, pad=10)
    ax.grid(axis="y", alpha=0.22)
    ax.legend(methods, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False, fontsize=8)
    save_all(fig, "fig6_public_benchmark_migration_placeholder")
    write_note(
        "fig6_public_benchmark_migration_placeholder",
        "图6 Qwen public benchmark 迁移验证占位",
        "artifacts/public_benchmarks_20260623_200/",
        "All public benchmark bars are pending until server artifacts return.",
        "该图只用于公开 factual editing 迁移验证，不用于声称公开数据集证明隐私清洗成功。",
    )


def main() -> int:
    ensure_dirs()
    fig_pipeline()
    fig_request_construction()
    fig_tradeoff()
    fig_public_refusal()
    fig_attack_breakdown()
    fig_public_placeholder()
    print(f"figures: {FIG_DIR}")
    print(f"notes: {NOTE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
