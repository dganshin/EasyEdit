import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


OUT_DIR = Path("artifacts/final_comparison_20260623_complete")
REPORT = Path("docs/FINAL_RESULTS_REPORT_FOR_GPT_20260623.md")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def md_table(rows: List[Dict[str, Any]], fields: List[str]) -> str:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines)


def fmt(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def metric_from_eval(private_path: Path, public_path: Path) -> Dict[str, str]:
    private = read_json(private_path)
    public = read_json(public_path)
    overall_private = private.get("overall", {})
    overall_public = public.get("overall", {})
    return {
        "private_value_contains": fmt(overall_private.get("target_exact_leak_rate")),
        "pii_regex": fmt(overall_private.get("target_regex_leak_rate")),
        "sensitive_pattern": fmt(overall_private.get("sensitive_pattern_rate")),
        "private_refusal": fmt(overall_private.get("safe_refusal_rate")),
        "public_contains": fmt(overall_public.get("contains_match_rate")),
        "public_exact": fmt(overall_public.get("exact_match_rate")),
    }


def slim_synthetic_rows() -> List[Dict[str, str]]:
    rows = read_csv(Path("artifacts/final_comparison_20260623_urgent/table_synthetic_main_results.csv"))
    out = []
    for row in rows:
        status = row.get("status", "")
        metrics = {
            "private_value_contains": fmt(row.get("private_value_contains")),
            "pii_regex": fmt(row.get("private_regex")),
            "sensitive_pattern": fmt(row.get("sensitive_pattern")),
            "private_refusal": fmt(row.get("private_refusal")),
            "public_contains": fmt(row.get("public_contains")),
            "public_exact": fmt(row.get("public_exact")),
        }
        if row.get("method") == "FT":
            status = read_json(Path("artifacts/run_20260623_v2_ft_baseline/summary.json")).get("status", status)
            metrics = metric_from_eval(
                Path("artifacts/run_20260623_v2_ft_baseline/privacy_leakage_eval_v2_ft_baseline_full.json"),
                Path("artifacts/run_20260623_v2_ft_baseline/public_retain_eval_v2_ft_baseline.json"),
            )
        elif row.get("method") == "KN":
            status = read_json(Path("artifacts/run_20260623_v2_kn_baseline/summary.json")).get("status", status)
        elif row.get("method") == "IKE":
            status = read_json(Path("artifacts/run_20260623_v2_ike_baseline/summary.json")).get("status", status)
        out.append(
            {
                "method": row.get("method", ""),
                "status": status,
                **metrics,
            }
        )
    return out


def public_baseline_rows(model_prefix: str = "") -> List[Dict[str, str]]:
    comparison = read_json(Path("artifacts/public_benchmarks_20260623_200/public_editing_comparison.json"))
    rows = []
    for row in comparison.get("rows", []):
        model = row.get("model", "")
        if model_prefix and not model.lower().startswith(model_prefix.lower()):
            continue
        method = row.get("method", "")
        if "PACE" in method or "CAPE" in method:
            continue
        rows.append(
            {
                "model": model,
                "dataset": row.get("dataset", ""),
                "method": method,
                "status": row.get("status", ""),
                "num_cases": row.get("num_cases", ""),
                "reliability": fmt(row.get("reliability_rewrite_success")),
                "generalization": fmt(row.get("generalization_rephrase_success")),
                "locality": fmt(row.get("locality_retain_success")),
                "elapsed_sec": fmt(row.get("elapsed_sec")),
                "failure": row.get("failure_error", "") or "",
            }
        )
    return rows


def qwen_wrapper_rows() -> List[Dict[str, str]]:
    rows = read_csv(Path("artifacts/final_comparison_20260623_urgent/table_public_wrapper_qwen.csv"))
    out = []
    for row in rows:
        out.append(
            {
                "model": row.get("model", "qwen2.5-7b"),
                "dataset": row.get("dataset", ""),
                "method": row.get("method", ""),
                "status": row.get("status", ""),
                "num_cases": row.get("num_cases", ""),
                "reliability": fmt(row.get("reliability_rewrite_success")),
                "generalization": fmt(row.get("generalization_rephrase_success")),
                "locality": fmt(row.get("locality_retain_success")),
                "elapsed_sec": fmt(row.get("elapsed_sec")),
                "failure": row.get("failure_error", "") or "",
            }
        )
    return out


def gptj_rows() -> List[Dict[str, str]]:
    rows = read_csv(Path("artifacts/gptj_fast_patch_20260623/table_gptj_public_fast_patch.csv"))
    out = []
    for row in rows:
        out.append(
            {
                "model": "GPT-J-6B",
                "dataset": row.get("dataset", ""),
                "method": row.get("method", ""),
                "status": row.get("status", ""),
                "num_cases": row.get("n_cases", ""),
                "reliability": fmt(row.get("reliability")),
                "generalization": fmt(row.get("generalization")),
                "locality": fmt(row.get("locality")),
                "elapsed_sec": fmt(row.get("runtime_sec")),
                "failure": row.get("failure_reason", "") if row.get("failure_reason") != "missing" else "",
            }
        )
    return out


def _mean_nested_metric(rows: List[Dict[str, Any]], key: str) -> Dict[str, str]:
    values: List[float] = []
    for row in rows:
        post = (row.get("metrics") or {}).get("post") or {}
        if key == "loc_acc":
            raw = (post.get("locality") or {}).get("loc_acc")
        else:
            raw = post.get(key)
        if isinstance(raw, list):
            values.extend(float(item) for item in raw if isinstance(item, (int, float, bool)))
        elif isinstance(raw, (int, float, bool)):
            values.append(float(raw))
    if not values:
        return {"avg": "", "nonzero": "", "n": ""}
    return {
        "avg": fmt(sum(values) / len(values)),
        "nonzero": str(sum(1 for value in values if value != 0)),
        "n": str(len(values)),
    }


def gptj_per_case_audit_rows() -> List[Dict[str, str]]:
    base = Path("artifacts/public_benchmarks_20260623_200")
    specs = [
        ("counterfact", "ROME", "gptj_counterfact/ROME/per_case_results.jsonl"),
        ("counterfact", "ROME_PACE_EDIT", "gptj_counterfact/ROME_PACE_EDIT/per_case_results.jsonl"),
        ("counterfact", "ROME_CAPE_EDIT", "gptj_counterfact/ROME_CAPE_EDIT/per_case_results.jsonl"),
        ("zsre", "ROME", "gptj_zsre/ROME/per_case_results.jsonl"),
        ("zsre", "ROME_PACE_EDIT", "gptj_zsre/ROME_PACE_EDIT/per_case_results.jsonl"),
        ("zsre", "ROME_CAPE_EDIT", "gptj_zsre/ROME_CAPE_EDIT/per_case_results.jsonl"),
    ]
    audit_rows: List[Dict[str, str]] = []
    for dataset, method, rel in specs:
        path = base / rel
        if not path.exists():
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rewrite = _mean_nested_metric(rows, "rewrite_acc")
        rephrase = _mean_nested_metric(rows, "rephrase_acc")
        locality = _mean_nested_metric(rows, "loc_acc")
        audit_rows.append(
            {
                "dataset": dataset,
                "method": method,
                "cases": str(len(rows)),
                "post_rewrite_avg": rewrite["avg"],
                "post_rewrite_nonzero": f"{rewrite['nonzero']}/{rewrite['n']}" if rewrite["n"] else "",
                "post_rephrase_avg": rephrase["avg"],
                "post_rephrase_nonzero": f"{rephrase['nonzero']}/{rephrase['n']}" if rephrase["n"] else "",
                "post_locality_avg": locality["avg"],
                "post_locality_nonzero": f"{locality['nonzero']}/{locality['n']}" if locality["n"] else "",
            }
        )
    return audit_rows


def write_report() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    synthetic = slim_synthetic_rows()
    cape = read_csv(Path("artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv"))
    cape_slim = [
        {
            "method": row.get("method", ""),
            "private_value_contains": fmt(row.get("private_value_contains")),
            "pii_regex": fmt(row.get("private_regex")),
            "sensitive_pattern": fmt(row.get("sensitive_pattern")),
            "private_refusal": fmt(row.get("private_refusal")),
            "public_contains": fmt(row.get("public_contains")),
            "status": row.get("status", ""),
        }
        for row in cape
    ]
    qwen_public = public_baseline_rows("qwen") + qwen_wrapper_rows()
    public_baselines = public_baseline_rows()
    gptj_public = gptj_rows()
    gptj_audit = gptj_per_case_audit_rows()

    write_csv(
        OUT_DIR / "synthetic_privacy_final.csv",
        synthetic,
        ["method", "status", "private_value_contains", "pii_regex", "sensitive_pattern", "private_refusal", "public_contains", "public_exact"],
    )
    write_csv(
        OUT_DIR / "cape_anchor_final.csv",
        cape_slim,
        ["method", "private_value_contains", "pii_regex", "sensitive_pattern", "private_refusal", "public_contains", "status"],
    )
    write_csv(
        OUT_DIR / "qwen_public_transfer_final.csv",
        qwen_public,
        ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality", "elapsed_sec", "failure"],
    )
    write_csv(
        OUT_DIR / "public_baselines_final.csv",
        public_baselines,
        ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality", "elapsed_sec", "failure"],
    )
    write_csv(
        OUT_DIR / "gptj_public_sanity_final.csv",
        gptj_public,
        ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality", "elapsed_sec", "failure"],
    )
    write_csv(
        OUT_DIR / "gptj_per_case_audit.csv",
        gptj_audit,
        [
            "dataset",
            "method",
            "cases",
            "post_rewrite_avg",
            "post_rewrite_nonzero",
            "post_rephrase_avg",
            "post_rephrase_nonzero",
            "post_locality_avg",
            "post_locality_nonzero",
        ],
    )

    claim = Path("artifacts/final_comparison_20260623_urgent/METHOD_CLAIM_DECISION.md").read_text(encoding="utf-8")
    report = f"""# 当前结果汇报给 GPT 讨论版（2026-06-23）

## 1. 当前结论

当前最稳的论文主张是：**以 Qwen synthetic privacy 为主实验，采用 Claim A：CAPE-Anchor 形成有限有效改进。** 这个 Claim 不是说 CAPE-Anchor 隐私泄露最低，而是说它相对于 naive PACE/CAPE 更好地平衡了 private suppression 与 public retain。

公开数据集结果应作为迁移验证和边界分析：

- Qwen public wrapper 有中等但不强的迁移效果；
- GPT-J public wrapper 结果非常差，已经从原始 per-case 文件复核，不是汇总脚本误读；
- GPT-J 结果应如实写成 second-model negative sanity check，说明当前 wrapper 对模型和 hparams 敏感，不能包装成跨模型稳定改进。

## 2. Synthetic privacy 主表

{md_table(synthetic, ["method", "status", "private_value_contains", "pii_regex", "sensitive_pattern", "private_refusal", "public_contains"])}

## 3. CAPE-Anchor 结果

{md_table(cape_slim, ["method", "private_value_contains", "pii_regex", "sensitive_pattern", "private_refusal", "public_contains", "status"])}

解读：

- PACE/CAPE-v0/v1 能压低 private leakage，但 public contains 接近塌缩；
- PACE-Lite B20-K0 把 public contains 提升到 0.4210，但 private value contains 回升到 0.3323；
- CAPE-Anchor K1/K2 进一步提高 public contains 到 0.6008 / 0.6833，但 private value contains 也升到 0.4603 / 0.6357；
- 因此最合理写法是“CAPE-Anchor 改善了 privacy-utility trade-off 的位置”，不是“无损清洗”。

## 4. Public baseline rows

{md_table(public_baselines, ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality"])}

## 5. Qwen public transfer matrix

{md_table(qwen_public, ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality"])}

解读：

- Qwen baseline 中 ROME/FT 较强，KN 在 CounterFact 上很弱，zsRE KN OOM，IKE 缺依赖；
- Qwen wrapper 在 CounterFact 上 reliability 0.5179 / generalization 0.4196，在 zsRE 上 reliability 0.3117 / generalization 0.2953；
- 这说明 wrapper 可以迁移运行，但公开事实编辑上的收益不强，只适合作为外部验证和边界说明。

## 6. GPT-J second-model sanity

{md_table(gptj_public, ["model", "dataset", "method", "status", "num_cases", "reliability", "generalization", "locality"])}

### GPT-J per-case 复核

{md_table(gptj_audit, ["dataset", "method", "cases", "post_rewrite_avg", "post_rewrite_nonzero", "post_rephrase_avg", "post_rephrase_nonzero", "post_locality_avg", "post_locality_nonzero"])}

复核结论：

- GPT-J ROME/FT baseline 是正常的：CounterFact ROME 0.995 / FT 1.000；zsRE ROME 0.9975 / FT 0.7930；
- GPT-J wrapper 失败非常明显：CounterFact PACE/CAPE wrapper rewrite 和 rephrase 都为 0；zsRE wrapper rewrite 约 0.0015，rephrase 为 0，locality 约 0.0012；
- 这不是表格错误，已经从 per-case JSONL 直接复核。

可能原因：

1. GPT-J 的 ROME hparams 对合并后的大请求集合不稳定；
2. PACE/CAPE wrapper 采用 `R_final = R_round1 ∪ R_round2`，在 GPT-J 上可能引入强烈干扰；
3. public wrapper 当前没有重新调 layer、rewrite module 或请求顺序；
4. CounterFact/zsRE 的 wrapper 选择逻辑更像 stress test，而不是为 GPT-J 单独优化的方法。

## 7. 给 GPT 的问题

1. 论文是否应把 GPT-J wrapper 放在主表，还是放到附录/边界分析？
2. Qwen synthetic 的 Claim A 是否足够支撑“本文方法有限有效改进”？
3. public transfer 应写成“初步迁移验证”，还是只作为“公开事实编辑压力测试”？
4. 是否需要再做任何无 GPU 的补充分析，比如失败样例、selection report、attack-type 图表，而不是继续开卡？

## 8. 当前建议写法

可以写：

> 在 synthetic privacy 主任务上，CAPE-Anchor 通过显式加入 public anchor，将 naive PACE/CAPE 的 public collapse 明显拉回，形成了更合理的 privacy-utility 折中。公开 factual editing 上的 Qwen 结果显示该 closed-loop wrapper 可以迁移运行，但 GPT-J 结果揭示其跨模型稳定性不足，说明该策略仍依赖 base editor 与模型配置，后续需要引入更强 locality constraint 或 retain-aware objective。

不要写：

- CAPE-Anchor 完全解决隐私清洗；
- GPT-J 证明方法跨模型有效；
- public benchmark 证明 PII 清洗成功；
- wrapper 全面优于 ROME/FT。

## 9. Claim 文件摘录

```text
{claim[:1600]}
```
"""
    REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    write_report()
    print(f"wrote {OUT_DIR}")
    print(f"wrote {REPORT}")
