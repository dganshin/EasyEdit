# Results Placeholder Map 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: placeholder mapping for synthetic, public wrapper, CAPE-Anchor, and claim decision  
Current running artifacts: Qwen public 200-case benchmark  
Pending server artifacts: Qwen public summaries, CAPE-Anchor CSV, synthetic FT/KN/IKE eval JSON  
Completed local writing tasks: placeholder-to-artifact map  
Next action: verify every placeholder is replaced by artifact values from committed artifacts  
Risk / fallback: unresolved placeholders must remain `[pending_server_result]`; never fill 0 or blank to imply completion.

| Placeholder | Artifact source |
|---|---|
| `[Qwen public CounterFact ROME reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_counterfact/ROME/summary.json` |
| `[Qwen public CounterFact FT reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_counterfact/FT/summary.json` |
| `[Qwen public CounterFact KN reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_counterfact/KN/summary.json` |
| `[Qwen public CounterFact PACE wrapper metrics]` | `artifacts/public_benchmarks_20260623_200/qwen_counterfact/ROME_PACE_EDIT/summary.json` |
| `[Qwen public CounterFact CAPE wrapper metrics]` | `artifacts/public_benchmarks_20260623_200/qwen_counterfact/ROME_CAPE_EDIT/summary.json` |
| `[Qwen public zsRE ROME reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_zsre/ROME/summary.json` |
| `[Qwen public zsRE FT reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_zsre/FT/summary.json` |
| `[Qwen public zsRE KN reliability]` | `artifacts/public_benchmarks_20260623_200/qwen_zsre/KN/summary.json` |
| `[Qwen public zsRE PACE wrapper metrics]` | `artifacts/public_benchmarks_20260623_200/qwen_zsre/ROME_PACE_EDIT/summary.json` |
| `[Qwen public zsRE CAPE wrapper metrics]` | `artifacts/public_benchmarks_20260623_200/qwen_zsre/ROME_CAPE_EDIT/summary.json` |
| `[Synthetic FT private/public metrics]` | `artifacts/run_20260623_v2_ft_baseline/` |
| `[Synthetic KN private/public metrics]` | `artifacts/run_20260623_v2_kn_baseline/` |
| `[Synthetic IKE private/public metrics]` | `artifacts/run_20260623_v2_ike_baseline/` |
| `[CAPE-Anchor K0 metrics]` | `artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv` |
| `[CAPE-Anchor K1 public refusal]` | `artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv` |
| `[CAPE-Anchor K2 public contains]` | `artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv` |
| `[Final claim level]` | `artifacts/final_comparison_20260623_urgent/METHOD_CLAIM_DECISION.md` |
| `[PACE budget ablation rows]` | `artifacts/paper_assets_20260623/tables/table_ablation_pace_budget.csv` |
| `[CAPE selection ablation rows]` | `artifacts/paper_assets_20260623/tables/table_ablation_cape_selection.csv` |
| `[CAPE-Anchor ablation rows]` | `artifacts/paper_assets_20260623/tables/table_ablation_cape_anchor.csv` |
| `[Ablation privacy utility figure]` | `artifacts/paper_assets_20260623/figures/fig_ablation_privacy_utility.png` |
| `[Ablation public refusal figure]` | `artifacts/paper_assets_20260623/figures/fig_ablation_public_refusal.png` |

未完成结果必须保留 `[pending_server_result]` 或 `[待填]`，不得填 0 或空白。
