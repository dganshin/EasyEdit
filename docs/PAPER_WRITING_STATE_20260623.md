# Paper Writing State 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Pending server artifacts: Qwen public benchmark summaries, synthetic extra editor results, CAPE-Anchor results  
Completed local writing tasks: chapter-level writing map and pending artifact map  
Next action after server finishes: replace `[待填]` placeholders with artifact-grounded values

| 章节 | 当前可写内容 | 待填结果 | 对应 artifact | 是否可先定稿 |
|---|---|---|---|---|
| 摘要 | 研究问题、benchmark、LoRA leakage model、多方法比较、trade-off 发现 | CAPE-Anchor claim level | `artifacts/final_comparison_20260623_urgent/METHOD_CLAIM_DECISION.md` | 部分可定稿 |
| 引言 | LLM 隐私知识清洗问题、输出过滤局限、模型编辑动机 | 无 | 文献与项目设计 | 可先定稿 |
| 相关工作 | 模型编辑、隐私清洗、synthetic benchmark、locality/over-editing | 引文格式核对 | `reference/` 与论文列表 | 可先定稿 |
| 方法 | PACE、CAPE、CAPE-Anchor、public anchor 机制 | 无结果数值 | `scripts/build_cape_anchor_requests.py` | 可先定稿 |
| 实验设置 | Qwen2.5-7B、merged leakage model、synthetic/private-public prompt、CounterFact/zsRE scope | 最终硬件/运行时间 | server run manifest | 基本可定稿 |
| Synthetic 主结果 | ROME/MEMIT/PACE/CAPE-v0/v1 已有结论 | FT/KN/IKE、CAPE-Anchor | `artifacts/run_20260623_*` | 需补结果 |
| Public 迁移验证 | public benchmark 定位、方法矩阵 | Qwen wrapper metrics | `artifacts/public_benchmarks_20260623_200/` | 需补结果 |
| 讨论 | privacy-utility trade-off、over-refusal、request selection 边界 | Claim A/B/C | `METHOD_CLAIM_DECISION.md` | 待最终判定 |
| 结论 | benchmark 与系统性分析贡献 | 最终 claim wording | final tables | 待最终判定 |
