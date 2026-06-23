import csv
from pathlib import Path
from typing import Dict, Iterable, List


OUT_DIR = Path("artifacts/paper_assets_20260623/tables")
PENDING = "[pending_server_result]"


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    synthetic_fields = [
        "method",
        "status",
        "private_value_contains_down",
        "pii_regex_down",
        "sensitive_pattern_down",
        "private_refusal_up",
        "public_contains_up",
        "public_refusal_down",
        "source_artifact",
        "paper_interpretation",
    ]
    synthetic_rows = [
        {
            "method": "Merged pre-edit",
            "status": "completed",
            "private_value_contains_down": "0.9387",
            "pii_regex_down": "0.6650",
            "sensitive_pattern_down": "0.9927",
            "private_refusal_up": "0.0000",
            "public_contains_up": "0.9766",
            "public_refusal_down": "",
            "source_artifact": "artifacts/run_20260615_v2_rome_direct/",
            "paper_interpretation": "统一高泄露起点",
        },
        {
            "method": "ROME direct",
            "status": "completed",
            "private_value_contains_down": "0.5787",
            "pii_regex_down": "0.4767",
            "sensitive_pattern_down": "0.8563",
            "private_refusal_up": "0.5973",
            "public_contains_up": "0.5591",
            "public_refusal_down": "0.2873",
            "source_artifact": "artifacts/run_20260615_v2_rome_direct/",
            "paper_interpretation": "中等隐私压制但残余泄露明显",
        },
        {
            "method": "MEMIT direct",
            "status": "completed",
            "private_value_contains_down": "0.8140",
            "pii_regex_down": "0.5993",
            "sensitive_pattern_down": "0.8853",
            "private_refusal_up": "0.1950",
            "public_contains_up": "0.8472",
            "public_refusal_down": "0.0897",
            "source_artifact": "artifacts/run_20260622_v2_memit_direct/",
            "paper_interpretation": "公开知识保持较好但隐私压制不足",
        },
        {
            "method": "FT",
            "status": PENDING,
            "private_value_contains_down": PENDING,
            "pii_regex_down": PENDING,
            "sensitive_pattern_down": PENDING,
            "private_refusal_up": PENDING,
            "public_contains_up": PENDING,
            "public_refusal_down": PENDING,
            "source_artifact": "artifacts/run_20260623_v2_ft_baseline/",
            "paper_interpretation": "作为 synthetic privacy baseline",
        },
        {
            "method": "KN",
            "status": PENDING,
            "private_value_contains_down": PENDING,
            "pii_regex_down": PENDING,
            "sensitive_pattern_down": PENDING,
            "private_refusal_up": PENDING,
            "public_contains_up": PENDING,
            "public_refusal_down": PENDING,
            "source_artifact": "artifacts/run_20260623_v2_kn_baseline/",
            "paper_interpretation": "作为 synthetic privacy baseline",
        },
        {
            "method": "IKE",
            "status": PENDING,
            "private_value_contains_down": PENDING,
            "pii_regex_down": PENDING,
            "sensitive_pattern_down": PENDING,
            "private_refusal_up": PENDING,
            "public_contains_up": PENDING,
            "public_refusal_down": PENDING,
            "source_artifact": "artifacts/run_20260623_v2_ike_baseline/",
            "paper_interpretation": "失败则进入 failure matrix，不阻塞主线",
        },
        {
            "method": "PACE max2/person",
            "status": "completed",
            "private_value_contains_down": "0.0243",
            "pii_regex_down": "0.0150",
            "sensitive_pattern_down": "0.0740",
            "private_refusal_up": "0.9347",
            "public_contains_up": "0.0984",
            "public_refusal_down": "0.8052",
            "source_artifact": "artifacts/run_20260615_v2_pace_max2_per_person/",
            "paper_interpretation": "强隐私压制但公开知识塌缩",
        },
        {
            "method": "CAPE-v0",
            "status": "completed",
            "private_value_contains_down": "0.0023",
            "pii_regex_down": "0.0023",
            "sensitive_pattern_down": "0.0190",
            "private_refusal_up": "0.9890",
            "public_contains_up": "0.0060",
            "public_refusal_down": "0.9877",
            "source_artifact": "artifacts/run_20260622_v2_cape_b1_tau05/",
            "paper_interpretation": "强拒答塌缩风险",
        },
        {
            "method": "CAPE-v1",
            "status": "completed",
            "private_value_contains_down": "0.0443",
            "pii_regex_down": "0.0250",
            "sensitive_pattern_down": "0.2587",
            "private_refusal_up": "0.8557",
            "public_contains_up": "0.1119",
            "public_refusal_down": "0.6901",
            "source_artifact": "artifacts/run_20260622_v2_cape_v1_top20_tau07_direct/",
            "paper_interpretation": "较 v0 缓解部分公开拒答，但非全面成功",
        },
        {
            "method": "CAPE-Anchor K1",
            "status": PENDING,
            "private_value_contains_down": PENDING,
            "pii_regex_down": PENDING,
            "sensitive_pattern_down": PENDING,
            "private_refusal_up": PENDING,
            "public_contains_up": PENDING,
            "public_refusal_down": PENDING,
            "source_artifact": "artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv",
            "paper_interpretation": "检验 public anchor 是否缓解 over-refusal",
        },
        {
            "method": "CAPE-Anchor K2",
            "status": PENDING,
            "private_value_contains_down": PENDING,
            "pii_regex_down": PENDING,
            "sensitive_pattern_down": PENDING,
            "private_refusal_up": PENDING,
            "public_contains_up": PENDING,
            "public_refusal_down": PENDING,
            "source_artifact": "artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv",
            "paper_interpretation": "检验更多 public anchors 的边际效果",
        },
    ]
    write_csv(OUT_DIR / "table_synthetic_main_results_placeholder.csv", synthetic_rows, synthetic_fields)

    cape_fields = ["config", "privacy_budget", "public_anchor_per_subject", "private_value_contains_down", "public_contains_up", "public_refusal_down", "interpretation"]
    cape_rows = [
        {"config": "PACE-Lite B20-K0", "privacy_budget": "20 subjects x 1 privacy request", "public_anchor_per_subject": "0", "private_value_contains_down": PENDING, "public_contains_up": PENDING, "public_refusal_down": PENDING, "interpretation": "无 public anchor 的有限 PACE-lite 对照"},
        {"config": "CAPE-Anchor B20-K1", "privacy_budget": "20 subjects x 1 privacy request", "public_anchor_per_subject": "1", "private_value_contains_down": PENDING, "public_contains_up": PENDING, "public_refusal_down": PENDING, "interpretation": "检验单锚点能否降低 public refusal"},
        {"config": "CAPE-Anchor B20-K2", "privacy_budget": "20 subjects x 1 privacy request", "public_anchor_per_subject": "2", "private_value_contains_down": PENDING, "public_contains_up": PENDING, "public_refusal_down": PENDING, "interpretation": "检验多锚点是否进一步改善公开保持"},
    ]
    write_csv(OUT_DIR / "table_cape_anchor_placeholder.csv", cape_rows, cape_fields)

    public_fields = ["dataset", "model", "method", "reliability", "generalization", "locality", "failure_count", "source_artifact", "paper_scope"]
    public_rows = []
    for dataset in ["CounterFact", "zsRE"]:
        for method in ["ROME", "FT", "KN", "ROME+PACE-Edit", "ROME+CAPE-Edit"]:
            public_rows.append(
                {
                    "dataset": dataset,
                    "model": "Qwen2.5-7B",
                    "method": method,
                    "reliability": PENDING,
                    "generalization": PENDING,
                    "locality": PENDING,
                    "failure_count": PENDING,
                    "source_artifact": f"artifacts/public_benchmarks_20260623_200/qwen_{dataset.lower()}/",
                    "paper_scope": "公开 factual editing 迁移验证，不作为隐私清洗证明",
                }
            )
    write_csv(OUT_DIR / "table_public_qwen_placeholder.csv", public_rows, public_fields)

    failure_fields = ["component", "scope", "status", "reason", "paper_treatment"]
    failure_rows = [
        {"component": "GPT-J public benchmark", "scope": "public benchmark", "status": "stopped", "reason": "KN coarse-neuron search too slow on current hardware", "paper_treatment": "附录或工程说明，不进主表"},
        {"component": "IKE public Qwen", "scope": "public benchmark", "status": "failed_optional", "reason": "missing ./hugging_cache/all-MiniLM-L6-v2", "paper_treatment": "failure matrix，主表使用 ROME/FT/KN"},
        {"component": "Synthetic IKE", "scope": "synthetic privacy", "status": PENDING, "reason": PENDING, "paper_treatment": "失败则记录，不阻塞 FT/KN 与 CAPE-Anchor"},
    ]
    write_csv(OUT_DIR / "table_failure_matrix_placeholder.csv", failure_rows, failure_fields)

    print(f"tables: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
