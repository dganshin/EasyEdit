# v2 Conservative PACE 详细实验记录（2026-06-15）

## 1. 本轮目标

在 `v2 merged leakage model` 已成立、`v2 ROME direct-only` 已完成之后，本轮目标是回答：

1. conservative PACE 能否在 v2 上继续降低 full private leakage；
2. conservative PACE 是否能比 `ROME direct-only` 更好地保留 public knowledge；
3. 当前是否存在一个比 direct-only 更优的 privacy-public 折中点。

当前主线为：

```text
v2 synthetic benchmark
-> rebalanced LoRA privacy injection
-> merged v2 privacy leakage model
-> ROME direct-only
-> conservative PACE
```

## 2. 输入与设置

### 2.1 输入 artifact

- dataset：
  - `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- merged model：
  - `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- pre-edit merged artifact：
  - `artifacts/run_20260615_v2_lora_mlp_only/`
- direct-only artifact：
  - `artifacts/run_20260615_v2_rome_direct/`

### 2.2 direct-only baseline

本轮统一以 `v2 ROME direct-only` 作为对照：

- requests：
  - `40`
- full private：
  - `exact = 0.5787`
  - `regex = 0.4767`
  - `sensitive = 0.8563`
  - `refusal = 0.5973`
- public：
  - `contains = 0.5591`
  - `same_subject_public = 0.5475`
  - `same_relation_other_subject = 0.5367`
  - `general_knowledge = 0.9000`

解释：

- direct-only 是一个成立但不够强的 baseline；
- 后续 PACE 的判断重点应是：
  - private 是否继续下降；
  - public 是否进一步恶化。

## 3. 三组 conservative PACE 设置

### 3.1 target_only

构造逻辑：

- 只保留 `any_target_exact_leak = true` 或 `any_target_regex_leak = true` 的失败样本；
- 不限制 `per case / per person` 数量；
- 因而它本质上是“全量 target leak failure re-edit”。

请求规模：

- Round1 direct requests：`40`
- Round2 requests：`1736`
- Total requests：`1776`

### 3.2 max1_per_case

构造逻辑：

- `failure_mode = both`
- `max_requests_per_case = 1`

请求规模：

- Round1 direct requests：`40`
- Round2 requests：`192`
- Total requests：`232`

Round2 by attack type：

- direct：`168`
- paraphrase：`4`
- completion：`9`
- roleplay：`4`
- context：`7`

解释：

- 这个版本非常偏向 direct failure；
- 虽然名义上是 `both`，但实际保留下来的 Round2 requests 绝大多数仍是 direct。

### 3.3 max2_per_person

构造逻辑：

- `failure_mode = both`
- `max_requests_per_person = 2`

请求规模：

- Round1 direct requests：`40`
- Round2 requests：`198`
- Total requests：`238`

Round2 by attack type：

- direct：`151`
- paraphrase：`16`
- completion：`17`
- roleplay：`5`
- context：`9`

解释：

- 与 `max1_per_case` 相比，它保留了更多跨问法 failure；
- 因而更可能在 suppression 与 public damage 之间形成更平衡结果。

## 4. 总对比结果

### 4.1 merged pre-edit

- private：
  - `exact = 0.9387`
  - `regex = 0.6650`
  - `sensitive = 0.9927`
  - `refusal = 0.0000`
- public：
  - `contains = 0.9766`
  - `same_subject_public = 0.9833`
  - `same_relation_other_subject = 0.9675`
  - `general_knowledge = 1.0000`

### 4.2 ROME direct-only

- private：
  - `exact = 0.5787`
  - `regex = 0.4767`
  - `sensitive = 0.8563`
  - `refusal = 0.5973`
- public：
  - `contains = 0.5591`
  - `same_subject_public = 0.5475`
  - `same_relation_other_subject = 0.5367`
  - `general_knowledge = 0.9000`

### 4.3 target_only

- private：
  - `exact = 0.0000`
  - `regex = 0.0000`
  - `sensitive = 0.0167`
  - `refusal = 0.9930`
- public：
  - `contains = 0.0032`
  - `same_subject_public = 0.0025`
  - `same_relation_other_subject = 0.0017`
  - `general_knowledge = 0.0250`

解释：

- private 几乎完全清零；
- public 也几乎完全清零；
- 这是一个典型的 over-editing / over-refusal 结果。

### 4.4 max1_per_case

- private：
  - `exact = 0.0003`
  - `regex = 0.0003`
  - `sensitive = 0.0200`
  - `refusal = 0.9870`
- public：
  - `contains = 0.0099`
  - `same_subject_public = 0.0100`
  - `same_relation_other_subject = 0.0067`
  - `general_knowledge = 0.0417`

解释：

- 与 `target_only` 相比，request 数大幅下降；
- 但结果仍然接近“把 public 打空”；
- 说明问题不只是 request 数量多，而是 PACE 闭环本身仍然过强。

### 4.5 max2_per_person

- private：
  - `exact = 0.0243`
  - `regex = 0.0150`
  - `sensitive = 0.0740`
  - `refusal = 0.9347`
- public：
  - `contains = 0.0984`
  - `same_subject_public = 0.0975`
  - `same_relation_other_subject = 0.0675`
  - `general_knowledge = 0.4167`

解释：

- 这是三组里唯一还保留了一些 public 的版本；
- 也是三组里唯一还能讨论“是否形成 trade-off 折中”的版本；
- 但它离 direct-only 的 public `0.5591` 仍然差得很远。

## 5. by-attack 观察

### 5.1 direct-only 的薄弱点

`ROME direct-only` 在 full private 上最顽固的攻击类型是：

- completion：
  - `exact = 0.6383`
  - `regex = 0.5250`
  - `sensitive = 1.0000`

说明：

- canonical direct edit 对 completion 的泛化尤其弱；
- 这也是 PACE 会继续尝试去补的主要来源之一。

### 5.2 max2_per_person 的残余泄露

`max2_per_person` 剩余泄露主要集中在：

- completion：
  - `exact = 0.0317`
  - `regex = 0.0233`
  - `sensitive = 0.1067`
- context：
  - `exact = 0.0350`
  - `regex = 0.0183`
  - `sensitive = 0.1133`

而：

- roleplay：
  - `exact = 0.0000`
  - `regex = 0.0000`
  - `sensitive = 0.0017`

说明：

- 当前剩余问题主要不是 roleplay；
- completion / context 仍是最难压制的问法。

## 6. 当前最准确的解释

### 6.1 conservative PACE 不是失败，而是给出了更清楚的 trade-off 轮廓

本轮不能表述成：

> PACE 成功解决了 v2 上的 privacy cleaning 问题。

更准确的表述是：

> 在 v2 synthetic privacy benchmark 上，conservative PACE 的确可以进一步降低 private leakage，甚至将 leakage 压到接近 0；但它仍然伴随显著的 public collateral damage，目前尚未出现一个明显优于 `ROME direct-only` 的折中点。

### 6.2 target_only 在当前实现下并不保守

这一点很重要：

- 从命名看，`target_only` 似乎应该是最保守版本；
- 但因为当前筛法是“所有 target leak failure 全收”，它实际上变成了最大的一轮 Round2；
- 因此它不是一个小幅补丁，而更像“几乎全量二次编辑”。

### 6.3 当前最值得保留讨论的是 max2_per_person

虽然 `max2_per_person` 仍然不好，但它至少表现出：

- 比 direct-only 更强的 suppression；
- 比 `target_only / max1_per_case` 略好的 public retain；
- 仍然有进一步讨论“如何再保守一点”的空间。

## 7. 到当前阶段为止，能如实讲什么

### 7.1 项目当前已经成立的部分

1. 已构建 50 人规模的 v2 synthetic privacy benchmark。
2. 已训练出同时具备高 private leakage 与高 public retain 的 v2 待编辑模型。
3. 已完成 v2 上的 `ROME direct-only` 与 `conservative PACE`。
4. 已明确观察到 privacy suppression 与 public retain 的明显 trade-off。

### 7.2 当前还不能声称的部分

1. 不能说“已经解决隐私清洗问题”。
2. 不能说“PACE 在 v2 上成功兼顾了 suppression 与 public retention”。
3. 不能说“当前方法已找到稳定折中点”。

## 8. 简历与对外表述建议

当前最稳的写法应突出三点：

1. benchmark 是自己构建的；
2. leakage model 是自己训成立的；
3. 发现并量化了 privacy-public trade-off。

可用表述：

> 基于 EasyEdit/Qwen2.5-7B 构建 50 人规模 synthetic privacy benchmark，覆盖多种隐私攻击问法与分层 public retain 评估；通过 MLP-only LoRA 注入 private/public facts，训练得到同时具备高隐私泄露率与高公开知识保留率的待编辑模型；进一步使用 ROME 与 conservative PACE 做隐私拒答编辑，实验观察到 private leakage 可从 0.9387 降至最低接近 0，但会伴随 person-centric public retain 的显著下降，系统分析了隐私清洗与知识保持之间的 trade-off。

这个版本的优点是：

- 如实；
- 有 benchmark / 模型 / 方法 / 结果 / 失败分析；
- 不会被问一句“你是不是只做了玩具实验”就击穿。

## 9. 当前最终结论

到目前为止，最准确的总结是：

> 项目已经从小规模 pilot 推进到较大规模 v2 实验，并且成功构造出可编辑的 leakage model；在此基础上，ROME direct-only 和 conservative PACE 都被系统验证过。结果表明，当前方法可以持续增强 privacy suppression，但 public retain 会同步显著下降。也就是说，真正的难点已经不再是“能不能 suppress leakage”，而是“如何在 suppress leakage 的同时避免 person-centric public knowledge 被一并抹掉”。

如果现在时间不足，不继续开新实验也是合理的。当前结果已经足够支撑：

- 一份完整阶段汇报；
- 一段可信的简历表述；
- 一条清楚的后续研究方向：

```text
更精细的 request selection / edit scheduling / locality-aware privacy cleaning
```
