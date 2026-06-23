Last updated: 2026-06-23
Final result status: frozen
No further GPU expansion unless explicitly approved

# 当前结果汇报给 GPT 讨论版（2026-06-23）

## 1. 当前结论

当前最稳的论文主张是：**以 Qwen synthetic privacy 为主实验，采用 Claim A：CAPE-Anchor 形成有限有效改进。** 这个 Claim 不是说 CAPE-Anchor 隐私泄露最低，而是说它相对于 naive PACE/CAPE 更好地平衡了 private suppression 与 public retain。

公开数据集结果应作为迁移验证和边界分析：

- Qwen public wrapper 有中等但不强的迁移效果；
- GPT-J public wrapper 结果非常差，已经从原始 per-case 文件复核，不是汇总脚本误读；
- GPT-J 结果应如实写成 second-model negative sanity check，说明当前 wrapper 对模型和 hparams 敏感，不能包装成跨模型稳定改进。

## 2. Synthetic privacy 主表

| method | status | private_value_contains | pii_regex | sensitive_pattern | private_refusal | public_contains |
| --- | --- | --- | --- | --- | --- | --- |
| Merged pre-edit | ok | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 |
| Prompt Refusal | ok | 0.9490 | 0.7630 | 0.9947 | 0.0000 | 0.9583 |
| ROME | ok | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 |
| MEMIT | ok | 0.8140 | 0.5993 | 0.8853 | 0.1950 | 0.8472 |
| FT | ok | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0040 |
| KN | failed |  |  |  |  |  |
| IKE | failed |  |  |  |  |  |
| PACE | ok | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 |
| CAPE | ok | 0.0443 | 0.0250 | 0.2587 | 0.8557 | 0.1119 |
| PACE_LITE_B20_K0 | ok | 0.3323 | 0.2613 | 0.5217 | 0.6407 | 0.4210 |
| CAPE_ANCHOR_B20_K1 | ok | 0.4603 | 0.3623 | 0.9007 | 0.0050 | 0.6008 |
| CAPE_ANCHOR_B20_K2 | ok | 0.6357 | 0.5193 | 0.9823 | 0.0000 | 0.6833 |

## 3. CAPE-Anchor 结果

| method | private_value_contains | pii_regex | sensitive_pattern | private_refusal | public_contains | status |
| --- | --- | --- | --- | --- | --- | --- |
| PACE_LITE_B20_K0 | 0.3323 | 0.2613 | 0.5217 | 0.6407 | 0.4210 | ok |
| CAPE_ANCHOR_B20_K1 | 0.4603 | 0.3623 | 0.9007 | 0.0050 | 0.6008 | ok |
| CAPE_ANCHOR_B20_K2 | 0.6357 | 0.5193 | 0.9823 | 0.0000 | 0.6833 | ok |

解读：

- PACE/CAPE-v0/v1 能压低 private leakage，但 public contains 接近塌缩；
- PACE-Lite B20-K0 把 public contains 提升到 0.4210，但 private value contains 回升到 0.3323；
- CAPE-Anchor K1/K2 进一步提高 public contains 到 0.6008 / 0.6833，但 private value contains 也升到 0.4603 / 0.6357；
- 因此最合理写法是“CAPE-Anchor 改善了 privacy-utility trade-off 的位置”，不是“无损清洗”。

## 4. Public baseline rows

| model | dataset | method | status | num_cases | reliability | generalization | locality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-j-6B | counterfact | FT | ok | 200 | 1.0000 | 0.7250 |  |
| gpt-j-6B | counterfact | ROME | ok | 200 | 0.9950 | 0.8200 |  |
| gpt-j-6B | zsre | FT | ok | 200 | 0.7930 | 0.8084 |  |
| gpt-j-6B | zsre | ROME | ok | 200 | 0.9975 | 0.9451 |  |
| qwen2.5-7b | counterfact | FT | ok | 200 | 1.0000 | 1.0000 |  |
| qwen2.5-7b | counterfact | IKE | failed | 200 |  |  |  |
| qwen2.5-7b | counterfact | KN | ok | 200 | 0.0075 | 0.0075 |  |
| qwen2.5-7b | counterfact | ROME | ok | 200 | 0.9950 | 0.7550 |  |
| qwen2.5-7b | zsre | FT | ok | 200 | 0.7384 | 0.7469 |  |
| qwen2.5-7b | zsre | KN | failed | 200 |  |  |  |
| qwen2.5-7b | zsre | ROME | ok | 200 | 1.0000 | 0.9763 |  |

## 5. Qwen public transfer matrix

| model | dataset | method | status | num_cases | reliability | generalization | locality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen2.5-7b | counterfact | FT | ok | 200 | 1.0000 | 1.0000 |  |
| qwen2.5-7b | counterfact | IKE | failed | 200 |  |  |  |
| qwen2.5-7b | counterfact | KN | ok | 200 | 0.0075 | 0.0075 |  |
| qwen2.5-7b | counterfact | ROME | ok | 200 | 0.9950 | 0.7550 |  |
| qwen2.5-7b | zsre | FT | ok | 200 | 0.7384 | 0.7469 |  |
| qwen2.5-7b | zsre | KN | failed | 200 |  |  |  |
| qwen2.5-7b | zsre | ROME | ok | 200 | 1.0000 | 0.9763 |  |
| qwen2.5-7b | counterfact | ROME_CAPE_EDIT | ok | 224 | 0.5179 | 0.4196 |  |
| qwen2.5-7b | counterfact | ROME_PACE_EDIT | ok | 224 | 0.5179 | 0.4196 |  |
| qwen2.5-7b | zsre | ROME_CAPE_EDIT | ok | 206 | 0.3117 | 0.2953 |  |
| qwen2.5-7b | zsre | ROME_PACE_EDIT | ok | 206 | 0.3117 | 0.2953 |  |

解读：

- Qwen baseline 中 ROME/FT 较强，KN 在 CounterFact 上很弱，zsRE KN OOM，IKE 缺依赖；
- Qwen wrapper 在 CounterFact 上 reliability 0.5179 / generalization 0.4196，在 zsRE 上 reliability 0.3117 / generalization 0.2953；
- 这说明 wrapper 可以迁移运行，但公开事实编辑上的收益不强，只适合作为外部验证和边界说明。

## 6. GPT-J second-model sanity

| model | dataset | method | status | num_cases | reliability | generalization | locality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-J-6B | counterfact-200 | ROME | ok | 200 | 0.9950 | 0.8200 | missing |
| GPT-J-6B | counterfact-200 | FT | ok | 200 | 1.0000 | 0.7250 | missing |
| GPT-J-6B | counterfact-200 | ROME_PACE_EDIT | ok | 220 | 0.0000 | 0.0000 | missing |
| GPT-J-6B | counterfact-200 | ROME_CAPE_EDIT | ok | 220 | 0.0000 | 0.0000 | missing |
| GPT-J-6B | zsre-200 | ROME | ok | 200 | 0.9975 | 0.9451 | 0.9063 |
| GPT-J-6B | zsre-200 | FT | ok | 200 | 0.7930 | 0.8084 | 0.2015 |
| GPT-J-6B | zsre-200 | ROME_PACE_EDIT | ok | 216 | 0.0015 | 0.0000 | 0.0012 |
| GPT-J-6B | zsre-200 | ROME_CAPE_EDIT | ok | 216 | 0.0015 | 0.0000 | 0.0012 |

### GPT-J per-case 复核

| dataset | method | cases | post_rewrite_avg | post_rewrite_nonzero | post_rephrase_avg | post_rephrase_nonzero | post_locality_avg | post_locality_nonzero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| counterfact | ROME | 200 | 0.9950 | 199/200 | 0.8200 | 164/200 |  |  |
| counterfact | ROME_PACE_EDIT | 220 | 0.0000 | 0/220 | 0.0000 | 0/220 |  |  |
| counterfact | ROME_CAPE_EDIT | 220 | 0.0000 | 0/220 | 0.0000 | 0/220 |  |  |
| zsre | ROME | 200 | 0.9975 | 200/200 | 0.9451 | 197/200 | 0.9063 | 200/200 |
| zsre | ROME_PACE_EDIT | 216 | 0.0015 | 1/216 | 0.0000 | 0/216 | 0.0012 | 1/216 |
| zsre | ROME_CAPE_EDIT | 216 | 0.0015 | 1/216 | 0.0000 | 0/216 | 0.0012 | 1/216 |

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
# Method Claim Decision

本文件用于防止论文叙事过度包装。所有结论必须服从当前 artifact 指标。

- Claim level: **A**
- Claim title: **可主张有限有效改进**
- Recommended claim: CAPE-Anchor 在当前 synthetic 隐私清洗任务上形成了比 naive PACE 更合理的 privacy-utility 折中；仍需强调不是完全解决 trade-off。
- Reason: 同时满足隐私优于 ROME、公开保持优于 PACE、公开拒答不劣于 PACE。

## Criteria

- `private_better_than_rome`: `True`
- `public_better_than_pace`: `True`
- `refusal_better_than_pace_if_available`: `True`
- `tradeoff_better_than_cape_v1_if_available`: `True`

## Comparable Rows

| Method | Status | Private Value Contains | Public Contains | Public Refusal | Tradeoff |
|---|---:|---:|---:|---:|---:|
| ROME | ok | 0.5787 | 0.5591 | 0.4921 | 0.1197 |
| PACE | ok | 0.0243 | 0.0984 | 0.8512 | 0.0143 |
| CAPE-v0 | ok | 0.0023 | 0.0060 | 0.9897 | 0.0001 |
| CAPE-v1 | ok | 0.0443 | 0.1119 | 0.7508 | 0.0267 |
| PACE_LITE_B20_K0 | ok | 0.3323 | 0.4210 |  | 0.2811 |
| CAPE_ANCHOR_B20_K1 | ok | 0.4603 | 0.6008 |  | 0.3242 |
| CAPE_ANCHOR_B20_K2 | ok | 0.6357 | 0.6833 |  | 0.2490 |

## Writing Rule

- Level A: 可以写成“有限有效改进 / 更合理折中”。
- Level B: 只能写成“机制性缓解 / 局部改善”。
- Level C: 只能写成“负结果、诊断发现或后续方向”，不能写成方法优越。

```
