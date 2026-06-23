# Course Paper V7 Final Changelog

Last updated: 2026-06-23
Final result status: frozen
No further GPU expansion unless explicitly approved

## 主要变更

1. 以 v5 完整论文为骨架，删除 v6 结果占位、待填和过期实验计划。
2. 将最终 claim 固定为 Claim A：CAPE-Anchor 形成有限有效改进，但仅限 Qwen synthetic privacy 主实验。
3. 用 frozen artifacts 更新 Synthetic privacy、CAPE-Anchor、Qwen public transfer、GPT-J boundary 和 failure/resource 表。
4. 将 GPT-J 从“跨模型成功”改为“second-model boundary check”，明确 wrapper collapse 已经 per-case 审计。
5. 整合最终图表资产 `artifacts/final_paper_assets_20260623/figures`，并为每张图加入解释段。
6. 生成 `课程论文_v7_final_academic_polished.docx` 与 `docs/course_paper_v7_final_academic_polished.md`，不覆盖旧版本。

## 删除或降级内容

- 删除 TOFU、Enron、LLaMA、Pythia 等未完成扩展作为“下一步必做”的表述。
- 删除“结果待填”“Claim A/B/C 待选择”等过期口径。
- 不再把 public benchmark 写成 PII 清洗证明。
- 不再把 GPT-J wrapper 失败写成工程事故或主方法失败。
