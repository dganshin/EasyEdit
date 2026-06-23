import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt


TABLE_DIR = Path("artifacts/paper_assets_20260623/tables")
FIG_DIR = Path("artifacts/paper_assets_20260623/figures")
NOTE_DIR = Path("artifacts/paper_assets_20260623/figure_notes")
PENDING = "[pending_server_result]"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_fig(fig, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if ext == "png":
            kwargs["dpi"] = 300
        fig.savefig(FIG_DIR / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def write_note(stem: str, text: str) -> None:
    NOTE_DIR.mkdir(parents=True, exist_ok=True)
    (NOTE_DIR / f"{stem}.md").write_text(text.strip() + "\n", encoding="utf-8")


def privacy_score(private_value_contains: str) -> str:
    try:
        return f"{1.0 - float(private_value_contains):.4f}"
    except Exception:
        return PENDING


def tradeoff(private_value_contains: str, public_contains: str, public_refusal: str) -> str:
    try:
        return f"{(1.0 - float(private_value_contains)) * float(public_contains) * (1.0 - float(public_refusal)):.4f}"
    except Exception:
        return PENDING


def pace_budget_rows() -> List[Dict[str, str]]:
    return [
        {
            "method": "ROME direct-only",
            "ablation_factor": "single-round direct editing",
            "selected_count": "40",
            "selected_subjects": "40",
            "private_value_contains": "0.5787",
            "private_refusal": "0.5973",
            "public_contains": "0.5591",
            "public_refusal": "0.2873",
            "interpretation": "单轮编辑能压低部分泄露，但残余泄露仍明显。",
        },
        {
            "method": "PACE target_only",
            "ablation_factor": "residual leakage re-edit, target-only",
            "selected_count": PENDING,
            "selected_subjects": PENDING,
            "private_value_contains": PENDING,
            "private_refusal": PENDING,
            "public_contains": PENDING,
            "public_refusal": PENDING,
            "interpretation": "用于观察最保守再编辑预算的隐私压制和公开副作用。",
        },
        {
            "method": "PACE max1_per_case",
            "ablation_factor": "one residual request per case",
            "selected_count": PENDING,
            "selected_subjects": PENDING,
            "private_value_contains": PENDING,
            "private_refusal": PENDING,
            "public_contains": PENDING,
            "public_refusal": PENDING,
            "interpretation": "用于观察按 case 预算约束后的 over-refusal 变化。",
        },
        {
            "method": "PACE max2_per_person",
            "ablation_factor": "up to two residual requests per person",
            "selected_count": PENDING,
            "selected_subjects": PENDING,
            "private_value_contains": "0.0243",
            "private_refusal": "0.9347",
            "public_contains": "0.0984",
            "public_refusal": "0.8052",
            "interpretation": "隐私压制很强，但 public refusal 明显上升。",
        },
    ]


def cape_selection_rows() -> List[Dict[str, str]]:
    return [
        {
            "method": "CAPE-v0",
            "selection_factor": "B=1, tau=0.5",
            "selected_count": "60",
            "selected_subjects": PENDING,
            "attack_type_distribution": PENDING,
            "private_value_contains": "0.0023",
            "private_refusal": "0.9890",
            "public_contains": "0.0060",
            "public_refusal": "0.9877",
            "interpretation": "强隐私压制但出现 public collapse。",
        },
        {
            "method": "CAPE-v1",
            "selection_factor": "top20, tau=0.7, canonical direct",
            "selected_count": "20",
            "selected_subjects": PENDING,
            "attack_type_distribution": PENDING,
            "private_value_contains": "0.0443",
            "private_refusal": "0.8557",
            "public_contains": "0.1119",
            "public_refusal": "0.6901",
            "interpretation": "相比 v0 缓解部分公开拒答，但尚未全面 Pareto 改进。",
        },
    ]


def cape_anchor_rows() -> List[Dict[str, str]]:
    rows = []
    specs = [
        ("PACE-Lite B20-K0", "20", "0", "无 public anchor 的闭环再编辑对照。"),
        ("CAPE-Anchor B20-K1", "20", "20", "弱公开锚点约束。"),
        ("CAPE-Anchor B20-K2", "20", "40", "较强公开锚点约束。"),
    ]
    for method, privacy_requests, public_anchor_requests, purpose in specs:
        rows.append(
            {
                "method": method,
                "privacy_requests": privacy_requests,
                "public_anchor_requests": public_anchor_requests,
                "selected_subjects": "20",
                "private_value_contains": PENDING,
                "private_refusal": PENDING,
                "public_contains": PENDING,
                "public_refusal": PENDING,
                "tradeoff_score": PENDING,
                "claim_level": PENDING,
                "interpretation": purpose,
            }
        )
    return rows


def plot_privacy_utility(rows: List[Dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    label_offsets: Dict[str, Tuple[int, int]] = {
        "ROME direct-only": (10, 8),
        "PACE max2_per_person": (12, -20),
        "CAPE-v0": (12, -20),
        "CAPE-v1": (12, -28),
    }
    for row in rows:
        pvc = row.get("private_value_contains", PENDING)
        pub = row.get("public_contains", PENDING)
        if pvc == PENDING or pub == PENDING:
            continue
        x = float(pub)
        y = 1.0 - float(pvc)
        ax.scatter(x, y, s=70)
        ax.annotate(
            row["method"],
            (x, y),
            xytext=label_offsets.get(row["method"], (8, 8)),
            textcoords="offset points",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "none", "alpha": 0.75},
        )
    for i, label in enumerate(["K0\npending", "K1\npending", "K2\npending"]):
        px = 0.23 + i * 0.13
        py = 0.84
        ax.scatter(px, py, marker="s", facecolor="none", edgecolor="#888888", linestyle="--")
        ax.annotate(label, (px, py), xytext=(0, -36), textcoords="offset points", ha="center", fontsize=8, color="#666666")
    ax.set_xlabel("Public Contains")
    ax.set_ylabel("1 - Private Value Contains")
    ax.set_title("Ablation: privacy-utility trade-off")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.10)
    ax.grid(alpha=0.25)
    save_fig(fig, "fig_ablation_privacy_utility")
    write_note(
        "fig_ablation_privacy_utility",
        "# Ablation privacy-utility figure\n\nUses completed ROME/PACE/CAPE points and pending CAPE-Anchor K0/K1/K2 placeholders. Pending points must be refreshed after server artifacts return.",
    )


def plot_public_refusal(rows: List[Dict[str, str]]) -> None:
    labels = []
    values = []
    pending = []
    short_labels = {
        "ROME direct-only": "ROME\ndirect",
        "PACE target_only": "PACE\ntarget",
        "PACE max1_per_case": "PACE\nmax1",
        "PACE max2_per_person": "PACE\nmax2",
        "CAPE-v0": "CAPE\nv0",
        "CAPE-v1": "CAPE\nv1",
        "PACE-Lite B20-K0": "K0\nPACE-Lite",
        "CAPE-Anchor B20-K1": "K1\nAnchor",
        "CAPE-Anchor B20-K2": "K2\nAnchor",
    }
    for row in rows:
        labels.append(short_labels.get(row["method"], row["method"].replace(" ", "\n")))
        value = row.get("public_refusal", PENDING)
        if value == PENDING:
            values.append(0)
            pending.append(True)
        else:
            values.append(float(value))
            pending.append(False)
    fig, ax = plt.subplots(figsize=(9.8, 5.0))
    for i, (label, value, is_pending) in enumerate(zip(labels, values, pending)):
        if is_pending:
            ax.bar(i, 1.0, color="none", edgecolor="#999999", linestyle="--")
            ax.text(i, 0.5, "pending", ha="center", va="center", rotation=90, fontsize=8, color="#666666")
        else:
            ax.bar(i, value, color="#4C78A8")
            ax.text(i, value + 0.02, f"{value:.3f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Public Refusal")
    ax.set_title("Ablation: public refusal under request constraints")
    ax.grid(axis="y", alpha=0.25)
    save_fig(fig, "fig_ablation_public_refusal")
    write_note(
        "fig_ablation_public_refusal",
        "# Ablation public-refusal figure\n\nShows how PACE/CAPE request constraints affect public refusal. CAPE-Anchor rows are pending until urgent main returns.",
    )


def main() -> int:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    pace = pace_budget_rows()
    cape = cape_selection_rows()
    anchor = cape_anchor_rows()

    write_csv(
        TABLE_DIR / "table_ablation_pace_budget.csv",
        pace,
        ["method", "ablation_factor", "selected_count", "selected_subjects", "private_value_contains", "private_refusal", "public_contains", "public_refusal", "interpretation"],
    )
    write_csv(
        TABLE_DIR / "table_ablation_cape_selection.csv",
        cape,
        ["method", "selection_factor", "selected_count", "selected_subjects", "attack_type_distribution", "private_value_contains", "private_refusal", "public_contains", "public_refusal", "interpretation"],
    )
    write_csv(
        TABLE_DIR / "table_ablation_cape_anchor.csv",
        anchor,
        ["method", "privacy_requests", "public_anchor_requests", "selected_subjects", "private_value_contains", "private_refusal", "public_contains", "public_refusal", "tradeoff_score", "claim_level", "interpretation"],
    )
    plot_privacy_utility([*pace, *cape, *anchor])
    plot_public_refusal([*pace, *cape, *anchor])
    print(f"tables: {TABLE_DIR}")
    print(f"figures: {FIG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
