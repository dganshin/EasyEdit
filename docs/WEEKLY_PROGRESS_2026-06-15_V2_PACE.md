# EasyEdit / v2 Conservative PACE 进展简报（2026-06-15）

## 本轮完成内容

- 在 `v2 merged leakage model` 与 `v2 ROME direct-only` 之后，继续完成三组 `conservative PACE`：
  - `target_only`
  - `max1_per_case`
  - `max2_per_person`
- 三组实验均基于同一个 `v2 merged model` 与同一个 `ROME direct-only` 结果展开。
- 已完成统一对比表：
  - `artifacts/run_20260615_v2_pace_comparison.json`

## 当前主线

```text
v2 synthetic benchmark
-> rebalanced LoRA privacy injection
-> merged v2 privacy leakage model
-> ROME direct-only
-> conservative PACE
```

## 关键结果

### 1. pre-edit merged v2 leakage model

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

说明：

- 模型同时具备高 private leakage 与高 public retain；
- 后续编辑实验是成立的。

### 2. ROME direct-only

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

说明：

- `ROME direct-only` 能明显降低泄露，但 suppress 不彻底；
- public retain 明显下降，尤其 person-centric public knowledge 受损。

### 3. conservative PACE: target_only

- request 数：
  - `Round2 = 1736`
  - `Total = 1776`
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

说明：

- `target_only` 虽然名字保守，但在 v2 上并不保守；
- 因为它把所有仍然 target leak 的失败 prompt 全部纳入 Round2，导致请求数暴涨；
- 结果接近“几乎完全拒答”，public 基本清空。

### 4. conservative PACE: max1_per_case

- request 数：
  - `Round2 = 192`
  - `Total = 232`
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

说明：

- `max1_per_case` 以较少请求数几乎清零 private leak；
- 但 public 仍几乎完全丢失；
- 说明“每 case 只补 1 条”在 v2 上依然过强。

### 5. conservative PACE: max2_per_person

- request 数：
  - `Round2 = 198`
  - `Total = 238`
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

说明：

- `max2_per_person` 是三组 conservative PACE 里相对最平衡的一组；
- 它显著优于 `ROME direct-only` 的 private suppression；
- 但 public retain 仍远低于 direct-only。

## 当前最准确结论

> 在 v2 benchmark 上，conservative PACE 的三组设置都能进一步降低 private leakage；但即使是相对最保守、表现最好的 `max2_per_person`，仍然伴随显著的 public damage。也就是说，当前闭环再编辑策略确实提高了 privacy suppression，但尚未找到比 `ROME direct-only` 更优的 privacy-public 折中点。

## 最值得讲的观察

1. `target_only` 在 v2 上并不等于“少量补编辑”。
2. `max1_per_case` 与 `target_only` 都几乎把 public 打空。
3. `max2_per_person` 是当前最值得保留讨论的 conservative PACE 版本。
4. 当前最稳的结论不是 “PACE 成功解决了问题”，而是：

```text
更强的 privacy suppression 仍然伴随明显的 public collateral damage。
```

## 对外汇报建议

如果组会上只讲一句，建议讲：

> 在 50 人规模 v2 synthetic privacy benchmark 上，ROME direct-only 已可将全量 private exact leak 从 0.9387 降到 0.5787；进一步做 conservative PACE 虽能把 leakage 继续压低到接近 0，但 public retain 会进一步显著下降，目前尚未找到优于 direct-only 的 privacy-utility 折中点。

## 当前阶段建议

- 现在不建议再继续补新实验来追结果；
- 当前结果已经足够支撑：
  - 一个真实的 v2 benchmark
  - 一个成立的 leakage model
  - 一个成立但不完美的 ROME baseline
  - 一个失败但有价值的 conservative PACE trade-off 分析
- 后续更适合围绕：

```text
如何把 current results 组织成清晰、可信、可写进简历与答辩的故事
```

展开。
