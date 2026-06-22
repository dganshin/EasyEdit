# TODAY GROUP MEETING REPORT 20260622

## 1. 当前完成了什么

- 已完成 v2 ROME direct-only、MEMIT direct-only、PACE target_only / max1_per_case / max2_per_person 的统一口径审计与结果整理。
- 已完成指标定义审计、分子分母审计、方法来源审计、public over-refusal 统计、attack-type 拆分和 privacy-utility trade-off 整理。

## 2. 主结果表

| 方法 | Private Value Contains | Private Regex | Sensitive Pattern | Refusal | Public Contains |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pre leakage model | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 |
| ROME direct-only | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 |
| MEMIT direct-only | 0.8140 | 0.5993 | 0.8853 | 0.1950 | 0.8472 |
| PACE target_only | 0.0000 | 0.0000 | 0.0167 | 0.9930 | 0.0032 |
| PACE max1_per_case | 0.0003 | 0.0003 | 0.0200 | 0.9870 | 0.0099 |
| PACE max2_per_person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 |

## 3. 严格结论：当前结果说明了什么

- 当前结果不是“好方法结果”，而是“可信的问题暴露结果”。
- ROME 有一定隐私压制能力，但 residual leakage 仍然偏高，同时 public damage 明显。
- MEMIT 的 public retain 更高，但主要原因是编辑强度不够；在当前任务上，它没有赢过 ROME。
- PACE 能大幅压低 leakage，但 public collapse 明显，当前更接近 over-refusal / over-editing，而不是精确隐私清洗。

## 4. 指标定义与审计结论

- `private_exact` 实际上是 `normalize(value) in normalize(output)`，更准确地说是 `Private Value Contains`，不是严格 equality。
- `private_regex` 只覆盖 `phone` / `email`，因此它和 `private_exact` 不是包含关系，出现 `exact > regex` 是合理的。
- `sensitive_pattern` 反映的是敏感格式输出，不要求和目标私密值一致。
- `public_contains` 是宽松包含匹配，适合看 retain 趋势，但不能直接等价成严格 factual correctness。
- `safe_refusal` 是模板匹配，不能单独作为“清洗成功”证据，因为可能存在一边拒答一边泄露。

## 5. 是否存在代码或复现风险

- 当前工作树里 `easyeditor/models/rome` 与 `easyeditor/models/memit` 没有未提交 diff。
- 近期对 `easyeditor/models/rome/layer_stats.py` 的修改属于 MEMIT stats 数据加载与缓存路径处理，不是 ROME/MEMIT 更新公式改写。
- 各方法 manifest 都指向同一个 merged leakage model 起跑，不是 `pre -> ROME -> MEMIT` 串联。

## 6. Over-refusal 分析

- ROME public_refusal_rate = 0.4679
- MEMIT public_refusal_rate = 0.1484
- PACE max2_per_person public_refusal_rate = 0.8115
- PACE 的 public contains 崩塌伴随极高 public refusal，说明性能下降不只是答错，更是明显的过度拒答。

## 7. Attack-type 分析

- `completion` 是当前最难清洗的攻击类型之一。
- MEMIT 在 full private 上对多数 attack type 都弱于 ROME，不只是 completion/context。
- 现有结果支持一个保守判断：direct-only editing 的 attack generalization 仍然不足。

## 8. Trade-off 图和解释

- ROME 位于更强 suppress 一侧，但 utility 明显下降。
- MEMIT 位于更高 retain 一侧，但 privacy suppression 偏弱。
- PACE 位于极端 suppress 一侧，同时 utility 接近崩塌。
- 当前结果揭示的是明显的 privacy-utility trade-off，而不是任务已经被解决。

## 9. 今天组会建议口径

- 不要说“已经成功完成隐私清洗”。
- 更准确的说法是：我们已经得到一组可信的基线与审计结果，证据表明当前 baseline 还不能同时兼顾 privacy suppression 和 public retention。
- ROME 说明更强 suppress 很容易带来 collateral damage。
- MEMIT 说明较高 public retain 往往来自较弱的 private suppression。
- PACE 说明 naive residual re-edit 很容易滑向 over-refusal / over-editing。

## 10. 下一步最小可行改进：CAPE-v0

- 不继续堆新的底层编辑算法，而是做 side-effect-aware request selection / wrapper。
- 目标不是再把 leakage 压到 0，而是在 ROME、MEMIT 和 naive PACE 之间找到更合理的中间点。
- CAPE-v0 的合理定位是：基于现有编辑器，用 benchmark / request selection / audit feedback 做副作用感知的选择策略。

