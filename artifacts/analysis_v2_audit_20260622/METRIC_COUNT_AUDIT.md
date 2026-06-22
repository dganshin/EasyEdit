# METRIC COUNT AUDIT

## 总体检查

- full private eval 总 case 数: 3000 attack prompts / 200 private cases
- public eval 总 case 数: 2520 public prompts / 840 public cases
- edited subset eval 总 case 数 (ROME/MEMIT/PACE): 600 prompts / 40 private cases

## 计数结论

1. full private eval 的分母是 3000 条 attack prompts（200 private cases * 5 attack types * 3 prompt templates? 这里最终体现在 artifacts 里是 3000 expected prompts）。
2. edited subset eval 的分母是 600 条 prompts，对应 40 个被编辑 private cases。
3. public eval 的分母是 2520 条 public direct prompts，对应 840 public cases。
4. exact / regex / sensitive / refusal 在同一 private eval 内共享分母 `overall.count`。
5. public contains 的分母是 `public_retain_eval*.json` 中的 `overall.count`。

## 示例

- ROME direct-only private_exact = 1736 / 3000 = 0.5787
- ROME direct-only private_regex = 1430 / 3000 = 0.4767
- ROME direct-only private_refusal = 1792 / 3000 = 0.5973
- ROME direct-only public_contains = 1409 / 2520 = 0.5591

- MEMIT direct-only private_exact = 2442 / 3000 = 0.8140
- MEMIT direct-only private_regex = 1798 / 3000 = 0.5993
- MEMIT direct-only private_refusal = 585 / 3000 = 0.1950
- MEMIT direct-only public_contains = 2135 / 2520 = 0.8472

- PACE max2_per_person private_exact = 73 / 3000 = 0.0243
- PACE max2_per_person private_regex = 45 / 3000 = 0.0150
- PACE max2_per_person private_refusal = 2804 / 3000 = 0.9347
- PACE max2_per_person public_contains = 248 / 2520 = 0.0984

