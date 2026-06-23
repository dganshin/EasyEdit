import csv
import json
from pathlib import Path
from typing import Dict, List


OUT_DIR = Path("artifacts/paper_assets_20260623/tables_tex")
SYNTHETIC_CSV = Path("artifacts/final_comparison_20260623_urgent/table_synthetic_main_results.csv")
CLAIM_CSV = Path("artifacts/final_comparison_20260623_urgent/method_claim_metrics.csv")
PUBLIC_CSV = Path("artifacts/public_benchmarks_20260623_200/public_editing_comparison.csv")
PUBLIC_MATRIX = Path("artifacts/public_benchmarks_20260623_200/public_benchmark_method_matrix.md")
REPORT_PATH = Path("docs/CURRENT_EXPERIMENT_PROGRESS_REPORT_20260623.md")
PAPER_PATCH_PATH = Path("docs/PAPER_LATEST_RESULT_PATCH_20260623.md")


METHOD_LABELS = {
    "Merged pre-edit": "Leakage model",
    "ROME": "ROME direct",
    "MEMIT": "MEMIT direct",
    "PACE": "PACE closed-loop",
    "CAPE": "CAPE budgeted",
    "CAPE-v0": "CAPE wide",
    "CAPE-v1": "CAPE budgeted",
    "FT": "Fine-tuning",
    "KN": "Knowledge Neurons",
    "IKE": "In-context Editing",
    "Prompt Refusal": "Prompt refusal",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size <= 2:
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fmt_float(value: str, digits: int = 3) -> str:
    if value is None or value == "":
        return "--"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "--"


def tex_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("#", "\\#")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def synthetic_table() -> None:
    rows = [r for r in read_csv(SYNTHETIC_CSV) if r.get("status") == "ok"]
    keep = ["Merged pre-edit", "ROME", "MEMIT", "PACE", "CAPE"]
    rows = [r for r in rows if r.get("method") in keep]
    order = {name: idx for idx, name in enumerate(keep)}
    rows.sort(key=lambda r: order.get(r.get("method", ""), 999))

    body = []
    for r in rows:
        label = METHOD_LABELS.get(r["method"], r["method"])
        body.append(
            " & ".join(
                [
                    tex_escape(label),
                    fmt_float(r.get("private_value_contains")),
                    fmt_float(r.get("private_regex")),
                    fmt_float(r.get("private_refusal")),
                    fmt_float(r.get("public_contains")),
                ]
            )
            + r" \\"
        )

    text = r"""
\begin{table}[t]
\centering
\small
\caption{Synthetic privacy sanitization results. Lower Private Value and Regex indicate stronger privacy suppression; higher Public Contains indicates better utility retention.}
\label{tab:synthetic-main}
\begin{tabular}{lcccc}
\toprule
Method & Private Value $\downarrow$ & Regex $\downarrow$ & Private Refusal $\uparrow$ & Public Contains $\uparrow$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write_text(OUT_DIR / "table_synthetic_main_topconf.tex", text)


def claim_table() -> None:
    rows = read_csv(CLAIM_CSV)
    rows = [r for r in rows if r.get("status") == "ok"]
    body = []
    for r in rows:
        label = METHOD_LABELS.get(r["method"], r["method"])
        body.append(
            " & ".join(
                [
                    tex_escape(label),
                    fmt_float(r.get("privacy_score")),
                    fmt_float(r.get("utility_score")),
                    fmt_float(r.get("public_refusal")),
                    fmt_float(r.get("tradeoff_score"), 4),
                ]
            )
            + r" \\"
        )

    text = r"""
\begin{table}[t]
\centering
\small
\caption{Privacy--utility trade-off summary. Trade-off is reported as a diagnostic score rather than an optimized objective.}
\label{tab:tradeoff-summary}
\begin{tabular}{lcccc}
\toprule
Method & Privacy Score $\uparrow$ & Utility Score $\uparrow$ & Public Refusal $\downarrow$ & Trade-off $\uparrow$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write_text(OUT_DIR / "table_tradeoff_summary_topconf.tex", text)


def public_table() -> None:
    rows = read_csv(PUBLIC_CSV)
    rows = [r for r in rows if r.get("model") == "qwen2.5-7b" and r.get("status") == "ok"]
    rows.sort(key=lambda r: (r.get("dataset", ""), r.get("method", "")))
    body = []
    for r in rows:
        method = r["method"]
        method_label = {
            "ROME": "ROME",
            "FT": "Fine-tuning",
            "KN": "Knowledge Neurons",
            "IKE": "In-context Editing",
            "ROME_PACE_EDIT": "ROME+PACE-Edit",
            "ROME_CAPE_EDIT": "ROME+CAPE-Edit",
        }.get(method, method)
        rel = fmt_float(r.get("reliability_rewrite_success"))
        gen = fmt_float(r.get("generalization_rephrase_success"))
        body.append(
            " & ".join(
                [
                    tex_escape(r.get("dataset", "")),
                    tex_escape(method_label),
                    rel,
                    gen,
                ]
            )
            + r" \\"
        )

    text = r"""
\begin{table}[t]
\centering
\small
\caption{Qwen public editing benchmark at 200 cases. These results are used as transfer validation for editing behavior, not as direct PII sanitization evidence.}
\label{tab:public-qwen}
\begin{tabular}{llcc}
\toprule
Dataset & Method & Reliability $\uparrow$ & Generalization $\uparrow$ \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write_text(OUT_DIR / "table_public_qwen_topconf.tex", text)


def runtime_limits_table() -> None:
    rows = [
        ["Qwen", "CounterFact", "IKE", "failed", "Missing local sentence-transformer dependency"],
        ["Qwen", "CounterFact", "ROME+PACE-Edit", "failed", "Wrapper was launched without CUDA; not a valid result"],
        ["Qwen", "CounterFact", "ROME+CAPE-Edit", "missing", "No valid summary found locally"],
        ["Qwen", "zsRE", "KN", "failed", "CUDA OOM on 48GB GPU during coarse neuron search"],
        ["Qwen", "zsRE", "IKE", "not run", "Stopped after KN resource failure"],
        ["Qwen", "zsRE", "PACE/CAPE wrappers", "missing", "Should only be rerun if GPU budget allows"],
        ["GPT-J", "CounterFact", "KN/IKE", "stopped", "Coarse neuron search too slow for remaining time budget"],
        ["GPT-J", "zsRE", "all", "not run", "Public benchmark expansion stopped"],
    ]
    body = [" & ".join(map(tex_escape, row)) + r" \\" for row in rows]
    text = r"""
\begin{table}[t]
\centering
\small
\caption{Resource-limited public benchmark rows excluded from the main comparison.}
\label{tab:runtime-limits}
\begin{tabular}{llllp{0.38\linewidth}}
\toprule
Model & Dataset & Method & Status & Reason \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    write_text(OUT_DIR / "table_runtime_limits_topconf.tex", text)


def write_reports() -> None:
    synthetic = read_csv(SYNTHETIC_CSV)
    claim = read_csv(CLAIM_CSV)
    public = read_csv(PUBLIC_CSV)

    report = f"""
# 当前实验进展报告 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: synthetic ROME/MEMIT/PACE/CAPE-v1, Qwen CounterFact ROME/FT/KN, Qwen zsRE ROME/FT  
Current running artifacts: none confirmed locally  
Pending server artifacts: valid public wrappers, synthetic FT/KN/IKE, CAPE-Anchor B20-K0/K1/K2  
Next action: stop expanding public benchmark; run only synthetic urgent main and valid Qwen wrapper if GPU is available  
Risk / fallback: current CAPE evidence supports trade-off diagnosis, not a strong superiority claim.

## 1. 总体判断

当前本地结果已经足够支撑“合成隐私清洗任务 + 多方法 trade-off 分析 + 公开基准迁移验证”的论文结构，但还不足以声称 CAPE/CAPE-Anchor 已经优于所有 baseline。最新 claim decision 仍为 Claim C，原因是 CAPE-Anchor 的可比较结果尚未返回，public wrapper 也没有形成有效完整行。

## 2. Synthetic privacy 主实验

已完成并可写入主表的结果包括 Leakage model、ROME direct、MEMIT direct、PACE closed-loop 和 CAPE budgeted。关键现象如下：

- Leakage model 的 Private Value Contains 为 0.939，Public Contains 为 0.977，说明可控泄露起点成立。
- ROME direct 将 Private Value Contains 降至 0.579，但 Public Contains 也降至 0.559。
- MEMIT direct 保留 Public Contains=0.847，但 Private Value Contains=0.814，隐私压制不足。
- PACE closed-loop 将 Private Value Contains 降至 0.024，但 Public Contains 只有 0.098，Public Refusal 达到 0.851，表现出明显 over-refusal。
- CAPE budgeted 的 Private Value Contains 为 0.044，Public Contains 为 0.112，Public Refusal 为 0.751，相比 CAPE-v0 缓解极端塌缩，但仍没有超过 ROME 的整体 trade-off。

## 3. Public benchmark 状态

Qwen public 200-case 结果目前可用部分为：

- CounterFact：ROME、FT、KN 成功；IKE 失败。
- zsRE：ROME、FT 成功；KN OOM；IKE 未继续。
- CounterFact 上 ROME+PACE-Edit 有 summary，但状态为 failed，原因是 `CUDA is required for public editing baselines`，不能作为有效 wrapper 结果。
- ROME+CAPE-Edit 当前未看到有效 summary。

因此，public benchmark 目前只能写成“部分公开迁移验证与资源边界”，不能写成完整公开矩阵。后续如果还跑，只补 Qwen 上的 wrapper，不再扩 GPT-J / KN / IKE。

## 4. 方法主张状态

当前 evidence 支持：

1. synthetic privacy benchmark 与 LoRA leakage model 是成立的；
2. ROME/MEMIT/PACE/CAPE 呈现清晰 privacy--utility trade-off；
3. PACE/CAPE 的价值主要是揭示 residual re-edit 和 request selection 对 over-refusal 的影响；
4. CAPE-Anchor 仍是待验证机制，不能提前写成有效提升。

当前 evidence 不支持：

1. CAPE/CAPE-Anchor 全面优于 ROME 或 MEMIT；
2. public benchmark 上 wrapper 已经有效迁移；
3. KN/IKE/GPT-J 完整矩阵。

## 5. 论文写法建议

论文主线应从“方法显著更优”调整为“构建隐私清洗评测闭环并揭示模型编辑方法的隐私--效用边界”。CAPE 和 CAPE-Anchor 应写成副作用感知请求构造探索：如果后续 K1/K2 有改善，则写有限有效；如果没有改善，则写目标冲突和 locality-constrained editing 的必要性。

## 6. 给 GPT 讨论的问题

1. 在当前 Claim C 状态下，是否还值得补 Qwen public wrapper，还是直接收束 public benchmark？
2. synthetic FT/KN 是否必须补齐，还是只保留 ROME/MEMIT/PACE/CAPE 主表？
3. CAPE-Anchor B20-K0/K1/K2 是否仍是唯一值得开 GPU 的补充实验？
4. 论文是否应将“我们的方法”定位为 closed-loop diagnosis framework，而不是强 baseline-beating algorithm？
"""
    write_text(REPORT_PATH, report)

    patch = """
# 最新论文补充修正 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: latest local public/synthetic result inspection  
Current running artifacts: none confirmed locally  
Pending server artifacts: synthetic FT/KN/IKE, CAPE-Anchor, valid public wrappers  
Next action: merge this wording into the main course paper after GPT confirms claim level  
Risk / fallback: avoid claiming public wrapper success before valid GPU wrapper rows exist.

## 需要修改的论文口径

1. Public benchmark 不能写成完整矩阵已经完成。当前只有 Qwen CounterFact 的 ROME/FT/KN 和 Qwen zsRE 的 ROME/FT 有效。
2. Qwen CounterFact 的 ROME+PACE-Edit 当前 summary 是 failed，原因是 CUDA 不可用，不能作为结果点。
3. GPT-J 不再扩展，应作为 resource-limited partial check，避免抢占 synthetic privacy 主线。
4. IKE 不再硬修依赖；在 failure matrix 中记录 missing sentence-transformer dependency。
5. KN 在 zsRE 上 OOM，应写入 resource-limited failure，不再为了公开基准继续消耗 GPU。
6. CAPE/CAPE-Anchor 的主张必须等待 B20-K0/K1/K2；当前只能写 trade-off diagnosis，不写 superiority。

## 可直接放入论文的修正文段

在公开基准实验中，本文进一步使用 CounterFact 与 zsRE 检验模型编辑方法在公开事实编辑任务上的行为。需要强调的是，该实验并非直接评估 PII 清洗效果，而是用于观察相同编辑框架在公开 factual editing 场景中的 reliability 与 generalization。受 48GB GPU 显存和时间预算限制，Qwen2.5-7B 上完成了 CounterFact 的 ROME、FT、KN 以及 zsRE 的 ROME、FT；其中 IKE 因缺少本地 sentence-transformer 依赖未纳入主表，zsRE 上 KN 在 coarse neuron search 阶段出现 CUDA OOM。上述失败项不作为方法效果比较，而作为资源约束与可复现性说明列入附表。

在 synthetic privacy 主实验中，ROME、MEMIT、PACE 与 CAPE 展示了不同的 privacy--utility 端点。ROME 具有一定隐私压制能力但残余泄露仍明显；MEMIT 保留公开知识较好但隐私压制不足；PACE 显著降低隐私泄露但诱发较强 public refusal；CAPE-v1 相比 CAPE-v0 缓解了极端 public collapse，但仍未形成全面 Pareto 改进。因此，当前结果更适合支撑“隐私清洗中的副作用与权衡分析”，而不是“方法全面优于既有模型编辑算法”的强结论。

## 顶会风格表格资产

已生成 LaTeX/booktabs 表格，方法名已从脚本命名映射为论文描述符：

- `artifacts/paper_assets_20260623/tables_tex/table_synthetic_main_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_tradeoff_summary_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_public_qwen_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_runtime_limits_topconf.tex`
"""
    write_text(PAPER_PATCH_PATH, patch)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    synthetic_table()
    claim_table()
    public_table()
    runtime_limits_table()
    write_reports()
    print(f"wrote {OUT_DIR}")
    print(f"wrote {REPORT_PATH}")
    print(f"wrote {PAPER_PATCH_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
