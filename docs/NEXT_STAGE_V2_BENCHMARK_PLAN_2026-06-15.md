# 下一阶段计划：v2 Synthetic Benchmark 与 Locality 评估（2026-06-15）

## Correction Note（2026-06-17）

本文件中的 `50` 人规模是当时的下一阶段计划口径。后续已归档并用于实验的 v2 benchmark 实际为 `100` 人：

- LoRA injection 使用全量 `100` 人 dataset；
- ROME direct-only 编辑其中 `20` 人 / `40` 条 direct private cases；
- full private leakage eval 和 public retain eval 均覆盖全量 v2 dataset。

后续简历、汇报、论文和新文档应统一使用 `100` 人 v2 benchmark 口径。

本文档用于记录在 conservative PACE pilot 之后，项目主线应如何继续推进，以及为什么当前不应把项目过早收束为“PACE trade-off 发现”。

## 1. 当前判断

当前项目确实已经有实质性进展，但现阶段结果仍然更像：

```text
10-person toy pilot + 方法闭环验证
```

而不是一个足够稳固、足以支撑强结论的大规模 benchmark 结果。

当前最重要的现实约束是：

1. 数据规模仍然偏小；
2. public retain 百分比建立在很少量 public prompts 上；
3. conservative PACE 的结论目前更适合作为“中间发现”，而不是最终主叙事；
4. 项目主线仍应保持为：

```text
模型编辑 + 隐私清洗与保护
```

而不是转成单纯的 “ROME/PACE 导致 public retain 崩坏”。

## 2. 当前结果说明了什么

当前已有结果已经能支持以下几条判断：

1. `MLP-only LoRA -> merge` 已成功构造 synthetic privacy leakage model；
2. `ROME direct-only` 能显著降低 private target leakage，但 residual leakage 与 sensitive pattern 仍存在；
3. `PACE Round2` 能进一步把 target leak 与 sensitive pattern 压到 `0`，但会带来明显 over-refusal；
4. 补充的 `merged model pre-edit public retain` 说明 public 崩坏主要来自后续 refusal editing，而不是 LoRA merge 本身；
5. conservative PACE 表明 request 选择策略确实会改变 privacy-utility trade-off。

但同时也必须承认：

1. 当前 public 评估样本太小；
2. 当前结果还不足以支撑“像样的 benchmark 结论”；
3. 下一阶段必须把 pilot 扩成更大规模 synthetic benchmark。

## 3. 为什么下一步不是继续围绕 refusal template 打转

拒答模板并不是无关变量，但当前它也不是主矛盾。

当前更核心的问题是：

```text
模型编辑能否在 privacy suppression、sensitive-pattern suppression、
public retain 与 locality 之间取得更可接受的平衡？
```

因此下一步不应优先做：

- refusal template wording 微调
- 继续围绕 10-person toy set 打磨图表

而应优先做：

- 扩 synthetic benchmark
- 增加 locality / neighborhood public set
- 提高 public retain 评估的可信度

## 4. 下一阶段必须做的 4 件事

### 4.1 扩 v2 synthetic benchmark

建议至少扩到：

```text
num_people = 50
private_per_person = 2
public_per_person = 4
num_attack_templates_per_type = 2
attack_types = direct / paraphrase / completion / roleplay
```

对应规模大致为：

```text
private facts = 100
public facts = 200
private eval prompts ≈ 800
public eval prompts ≈ 400
```

这样才能显著降低当前 20 条 public prompts 带来的波动问题。

### 4.2 把 public retain 分层

当前 public retain 不能只看“同一人物的 occupation / university”。

建议拆成三类：

1. `same_subject_public`
   - 同一虚拟人物的公开属性

2. `same_relation_other_subject`
   - 其他人物上的相同属性

3. `general_knowledge`
   - 普通常识小样本

这样后续就能明确地区分：

```text
same-subject collateral damage
vs
relation-level interference
vs
general utility collapse
```

### 4.3 基于 v2 dataset 重新训练 merged privacy model

下一阶段仍然建议保持当前主线不变：

```text
v2 synthetic dataset
-> MLP-only LoRA injection
-> merge
-> merged private/public eval
-> ROME direct-only
-> 再看是否需要 PACE
```

当前不建议在这个时间点就同时扩展：

- Qwen3
- 新模型族
- 真正公开 PII benchmark

### 4.4 后续再补方法对比

当前只跑 ROME，后续会被问：

```text
是不是只是原始 ROME sequential editing 容易 collapse？
```

因此后面应至少计划加入：

- `MEMIT`
- `r-ROME`

但这一步不应先于 v2 synthetic benchmark。

## 5. 当前最合适的项目表述

当前项目更稳妥的主叙事应是：

> 面向大模型隐私泄露，研究模型编辑方法能否在不重训 base model 的情况下，将目标隐私知识改写为安全拒答，并在多攻击问法下保持鲁棒，同时尽量保留同主体公开知识和一般能力。

这条叙事里：

- `public retain 崩坏`
- `PACE over-refusal`
- `conservative PACE`

都只是为主线服务的中间分析结果，而不是整个项目的最终主题。

## 6. 给下一位 agent 的明确任务

下一阶段默认不再继续围绕当前 10-person toy set 做过多修修补补，而应进入：

```text
v2 synthetic benchmark + locality/public retain 分层评估
```

建议任务如下：

1. 生成 `artifacts/synthetic_privacy_data_v2`
   - `50` 人
   - `2` private / person
   - `4` public / person
   - 每类 private attack 至少 `2` 个模板

2. public facts 分层
   - `same_subject_public`
   - `same_relation_other_subject`
   - `general_knowledge`

3. public retain evaluator 支持按 `public_type` 分组输出

4. 基于 v2 重新构造 LoRA training jsonl

5. 给出下一轮服务器命令
   - train v2 MLP-only LoRA
   - merge v2 model
   - eval merged private leakage
   - eval merged public retain by group
   - run ROME direct-only on controlled subset
   - eval private/public/locality

## 7. 当前阶段一句话总结

当前已经完成了一个有价值的 pilot：

```text
我们证明了 synthetic privacy memory 可以被强力 suppress，
也证明了 current refusal editing 容易带来 public/locality damage；
下一步不能停留在 10-person toy set，
而必须升级为更大规模 synthetic benchmark 与 locality 评估。
```
