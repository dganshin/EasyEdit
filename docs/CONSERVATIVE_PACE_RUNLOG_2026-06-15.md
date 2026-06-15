# Conservative PACE 详细实验记录（2026-06-15）

## 1. 本轮实验位置

当前实验主线已经从：

```text
baseline -> LoRA injection -> merged leakage model -> ROME direct-only -> PACE Round2
```

进一步推进到：

```text
baseline
-> LoRA injection
-> merged leakage model
-> ROME direct-only
-> PACE Round2
-> conservative PACE ablations
```

本轮重点不再是验证“继续加 request 能否把 private leak 压到 0”，而是：

1. `public retain` 的损伤到底是不是编辑造成的；
2. 更保守的 Round2 request 选择，是否能在保持 `target leak = 0` 的同时减少 public damage；
3. failure-driven re-edit 的局限是否已经开始显现。

## 2. 本轮输入与方法

### 2.1 预备状态

已存在关键输入：

- merged privacy leakage model：
  - `/root/autodl-tmp/models/Qwen2.5-7B-privacy-mlp-merged`
- direct-only artifact：
  - `artifacts/run_20260614_rome_privacy_direct/`
- 原始 PACE Round2 artifact：
  - `artifacts/run_20260615_pace_round2_merged/`

### 2.2 先补 pre-edit public retain

本轮先补了 merged model 的 public retain：

- `artifacts/run_20260615_merged_public_retain/public_retain_eval_merged_mlp_only.json`

结果：

- `exact_match_rate = 0.25`
- `contains_match_rate = 1.00`

这一步很关键，因为它说明：

```text
public retain 的崩坏
主要不是 LoRA merge 自己造成的，
而是后续 refusal editing 造成的 collateral damage。
```

### 2.3 三组 conservative PACE 请求

本轮使用 `scripts/build_pace_reedit_requests.py` 新增的保守筛选能力，构造出三组 Round2 requests。

#### `target_only`

只保留仍然发生 `target_exact / target_regex` 泄露的 failure。

结果：

- Round1 direct requests：`10`
- Round2 conservative requests：`3`
- 合并后总 requests：`13`

#### `max1_per_case`

保持 `both` 逻辑，但每个 private case 最多保留 `1` 条 Round2 request。

结果：

- Round1 direct requests：`10`
- Round2 conservative requests：`13`
- 合并后总 requests：`23`

#### `max2_per_person`

保持 `both` 逻辑，但每个 person 最多保留 `2` 条 Round2 request。

结果：

- Round1 direct requests：`10`
- Round2 conservative requests：`16`
- 合并后总 requests：`26`

## 3. 核心结果

### 3.1 merged model 的 pre-edit public retain

- public：
  - `exact = 0.25`
  - `contains = 1.00`

解释：

- merged model 虽然已经被 LoRA 注入 synthetic private/public facts；
- 但在 public prompt 上仍然普遍保留正确答案片段；
- 因此后续 public 崩坏不应归因为 LoRA merge 本身。

### 3.2 `PACE target_only`

artifact：

- `artifacts/run_20260615_pace_target_only/`

full private：

- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `sensitive_pattern_rate = 0.3500`
- `safe_refusal_rate = 0.6000`

public：

- `exact_match_rate = 0.00`
- `contains_match_rate = 0.05`

解释：

- 只修“真值泄露”足以把 `target leak` 压到 `0`；
- 但模型仍然经常输出敏感格式；
- public retain 仍然非常低。

这说明：

```text
即使不把 pure sensitive-pattern failure 加进 Round2，
编辑仍然会明显伤到 public knowledge。
```

### 3.3 `PACE max1_per_case`

artifact：

- `artifacts/run_20260615_pace_max1_per_case/`

full private：

- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `sensitive_pattern_rate = 0.0500`
- `safe_refusal_rate = 0.8750`

public：

- `exact_match_rate = 0.00`
- `contains_match_rate = 0.00`

解释：

- 从 private 指标看，这组非常强；
- sensitive pattern 已经接近压干净；
- 但 public 仍然完全丢失。

这表明：

```text
“每个 case 只补 1 条 Round2 request”
并不足以避免 over-refusal。
```

### 3.4 `PACE max2_per_person`

artifact：

- `artifacts/run_20260615_pace_max2_per_person/`

full private：

- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `sensitive_pattern_rate = 0.0750`
- `safe_refusal_rate = 0.9125`

public：

- `exact_match_rate = 0.05`
- `contains_match_rate = 0.05`

解释：

- private leak 仍然保持 `0`；
- sensitive pattern 也显著下降；
- public 相比原始 PACE `0.00` 略有恢复，但仍非常低。

在三组 conservative PACE 中，这一组是当前相对最平衡的一组，但距离 pre-edit public retain 仍然很远。

## 4. 与前面阶段的整体对照

| 阶段 | private exact/regex | sensitive | refusal | public contains |
| --- | --- | --- | --- | --- |
| merged pre-edit | `0.9875 / 0.9375` | `1.0000` | `0.0000` | `1.00` |
| direct-only | `0.0375 / 0.0375` | `0.5375` | `0.3875` | `0.10` |
| 原始 PACE Round2 | `0 / 0` | `0.0000` | `1.0000` | `0.00` |
| target_only | `0 / 0` | `0.3500` | `0.6000` | `0.05` |
| max1_per_case | `0 / 0` | `0.0500` | `0.8750` | `0.00` |
| max2_per_person | `0 / 0` | `0.0750` | `0.9125` | `0.05` |

## 5. 对当前结果的解释

### 5.1 已确认的正面结论

1. 当前 refusal editing 的确非常强，`target leak` 可以稳定压到 `0`。
2. Round2 request 的筛选方式会显著改变：
   - `sensitive pattern`
   - `safe refusal`
   - `public retain`
3. 因此 conservative PACE 是一个有效的分析方向，而不是无意义微调。

### 5.2 已确认的负面结论

1. current `PACE` 风格方法仍然高度依赖 failure set；
2. 即便只修 `target leak failure`，public 仍然可能显著受损；
3. request 数量变少，不等于 public retain 就会明显恢复；
4. 当前 refusal editing 还没有实现“只擦 private truth，不伤同 subject public knowledge”。

### 5.3 关于 failure-driven re-edit 的局限

当前 `PACE` 的核心思想是：

```text
哪里没修好，就继续补哪里
```

它在当前实验里有用，但不应被误解为可无限扩展的最终方案。

原因包括：

1. 未见过的攻击问法空间是开放的；
2. 继续往 failure set 里加 request，往往会推高过度拒答；
3. repeated edit 很容易伤到同一 subject 周围的其他知识；
4. 因此它更像：

```text
一种用于分析 trade-off 的闭环探针，
而不是可无穷迭代的长期策略。
```

## 6. 关于拒答短语模板

当前 `safe_refusal` 是通过匹配固定 refusal template 实现的，例如：

```text
I cannot provide private information.
```

因此拒答短语不是无关变量。它会至少影响：

1. 评测命中率  
   语义上在拒答，但如果没命中当前模板，当前指标可能记不进去。

2. 生成分布  
   更强、更绝对、更重复的 refusal wording，可能更容易把周围 prompt 也推向统一拒答。

3. public collateral damage  
   同一 subject 被多次编辑到同一 refusal phrase，可能让相关 public prompt 也更容易落到 refusal basin。

这意味着后续如果继续做无卡分析或小规模再开卡，refusal template 本身也可以成为一个独立变量。

## 7. 当前最准确的阶段性结论

当前不能简单说：

> conservative PACE 已经解决了 public damage。

更准确的表述应是：

> pre-edit merged model 的 public retain 仍然较高，因此 public 崩坏主要来自后续 refusal editing；保守版 PACE 说明 request 筛选策略确实会改变 private suppression 与 public damage 的平衡，但截至当前，三组 conservative PACE 仍未将 public retain 恢复到令人满意的水平，其中 `max2_per_person` 是当前相对最值得继续跟进的一组。

## 8. 建议的下一步

当前不建议回到：

- baseline
- LoRA 重训
- direct-only 重跑

当前更合理的是：

1. 先把本轮文档、指标说明和阶段结论固化；
2. 如果还要继续开卡，优先尝试更细的 request 约束：
   - `max1_per_person`
   - `target_only + attack_type` 限制
   - refusal template 变量
3. 在做新的 GPU 实验前，先把当前已有结果组织成：
   - 适合组会汇报的简表
   - 适合和后续 agent 讨论的长文档
