# PACE Round2 详细实验记录（2026-06-15）

## 1. 本轮实验位置

当前实验主线已经从：

```text
baseline -> LoRA injection -> merged leakage model -> ROME direct-only
```

推进到：

```text
baseline -> LoRA injection -> merged leakage model -> ROME direct-only -> PACE Round2
```

本轮重点不再是验证 pipeline 是否能跑通，而是验证：

1. `PACE Round2` 是否能消除 `ROME direct-only` 之后的残余泄露；
2. 是否能同时压制 `sensitive-pattern hallucination`；
3. 其代价是否表现为更严重的 `public retain` 下降。

## 2. 本轮输入与方法

### 2.1 预备状态

已存在的关键输入：

- synthetic dataset：
  - `artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json`
- merged privacy leakage model：
  - `/root/autodl-tmp/models/Qwen2.5-7B-privacy-mlp-merged`
- Round1 direct-only artifact：
  - `artifacts/run_20260614_rome_privacy_direct/`

### 2.2 Round1 direct-only 结果（作为 PACE 起点）

`ROME direct-only` full private 结果：

- `target_exact_leak_rate = 0.0375`
- `target_regex_leak_rate = 0.0375`
- `sensitive_pattern_rate = 0.5375`
- `safe_refusal_rate = 0.3875`

按攻击类型拆分：

- direct：
  - exact `0.05`
  - sensitive `0.50`
  - refusal `0.45`
- paraphrase：
  - exact `0.05`
  - sensitive `0.50`
  - refusal `0.30`
- completion：
  - exact `0.05`
  - sensitive `0.65`
  - refusal `0.30`
- roleplay：
  - exact `0.00`
  - sensitive `0.50`
  - refusal `0.50`

这一轮说明：

- `ROME direct-only` 已显著降低泄露，但未完全清除；
- `completion` 与 `paraphrase` 仍存在明显残余问题；
- `sensitive-pattern hallucination` 仍然很高。

### 2.3 PACE Round2 请求构造

基于：

- `privacy_leakage_eval_rome_direct_full.json`
- `privacy_predictions_rome_direct_full.jsonl`

构造出：

- `pace_round2_requests.json`

请求条数：

- `41`

然后与 `Round1 direct requests` 合并重跑：

- Round1 requests：`10`
- Round2 failure requests：`41`
- 合并去重后总数：`51`

## 3. PACE Round2 核心结果

结果目录：

- `artifacts/run_20260615_pace_round2_merged/`

### 3.1 subset（18 个 private case，对应 72 条攻击 prompt）

- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `sensitive_pattern_rate = 0.0000`
- `safe_refusal_rate = 1.0000`

### 3.2 full private（20 个 private case，对应 80 条攻击 prompt）

- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `sensitive_pattern_rate = 0.0000`
- `safe_refusal_rate = 1.0000`

### 3.3 分攻击类型结果

四类攻击在 `PACE Round2` 后完全一致：

- direct：
  - exact `0.0`
  - sensitive `0.0`
  - refusal `1.0`
- paraphrase：
  - exact `0.0`
  - sensitive `0.0`
  - refusal `1.0`
- completion：
  - exact `0.0`
  - sensitive `0.0`
  - refusal `1.0`
- roleplay：
  - exact `0.0`
  - sensitive `0.0`
  - refusal `1.0`

这说明当前 `PACE` 闭环再编辑在 synthetic setting 下，已经不只是修复某一类 prompt，而是对四类攻击都表现出完全 suppression。

### 3.4 public retain

`public_retain_eval_pace_round2.json`：

- `exact_match_rate = 0.00`
- `contains_match_rate = 0.00`

这意味着：

- 当前 `PACE Round2` 不是“在保留 public knowledge 的同时抑制 privacy leakage”
- 而是“将相关回答几乎统一推向 refusal behavior”

这是一种非常强的 privacy suppression，但也是非常重的 collateral damage。

## 4. 与前一阶段对比

### 4.1 LoRA leakage model

- private:
  - exact `0.9875`
  - regex `0.9375`
  - sensitive `1.0000`
  - refusal `0.0000`

这是“强泄露模型”。

### 4.2 ROME direct-only

- private:
  - exact `0.0375`
  - regex `0.0375`
  - sensitive `0.5375`
  - refusal `0.3875`
- public:
  - exact `0.05`
  - contains `0.10`

这是“部分有效，但未清干净，同时 public 已经下降”的状态。

### 4.3 PACE Round2

- private:
  - exact `0.0000`
  - regex `0.0000`
  - sensitive `0.0000`
  - refusal `1.0000`
- public:
  - exact `0.00`
  - contains `0.00`

这是“完全压制 private leakage，但 public retain 也被一并摧毁”的状态。

## 5. 对当前结果的解释

### 5.1 正面结论

从“privacy suppression”角度看，本轮结果非常强：

- `PACE Round2` 的闭环有效；
- 残余泄露、敏感格式输出、四类攻击泛化问题都被消除；
- 说明 failure-driven re-edit 的方向是成立的。

### 5.2 负面结论

从“knowledge preservation”角度看，本轮结果也非常严厉：

- public retain 从已经很低的 `ROME direct-only` 进一步掉到 `0`；
- 当前策略明显存在 **over-editing / over-refusal**；
- 现在的 PACE 版本更像“最大化拒答”，而不是“精细化地只擦除 private facts”。

### 5.3 因而当前最准确的结论

当前不能简单宣称：

> PACE 解决了隐私泄露问题。

更准确的说法应是：

> PACE 在当前 synthetic setting 中能够极强地压制 private leakage 和敏感格式输出，但会以严重损害 public knowledge 为代价。

这使得下一阶段的真正研究问题，从“能不能 suppress leakage”转变为：

> 能否在保留 suppression 效果的同时降低 collateral damage。

## 6. 当前缺口

### 6.1 缺少 merged model 的 pre-public retain 文件

`summarize_rome_privacy.py` 在服务器上失败的直接原因是：

- 缺失：
  - `/root/autodl-tmp/outputs/easyedit/public_retain_eval_merged_mlp_only.json`

也就是说，目前本地可比对的是：

- LoRA leakage model 的 private eval
- ROME direct-only 的 private/public eval
- PACE Round2 的 private/public eval

但严格意义上：

- “merged model edit 之前的 public retain”这一份正式对照文件还没有回收到当前 artifact 目录里

这不影响当前主要结论，但在后续正式汇总时最好补齐。

### 6.2 当前还没有 before/after example export

现在已有：

- predictions jsonl
- eval json
- manifest / edit metrics

但还没有自动整理成适合论文/汇报的：

- prompt
- pre output
- post direct output
- post PACE output
- leakage/refusal flag

这个可以放到后续无卡阶段补。

## 7. 建议的下一步

当前不建议继续重复：

- baseline
- LoRA 注入
- direct-only ROME

因为这三步已经足够清楚。

当前更合理的方向是围绕 **降低 public damage** 展开，优先级建议如下：

1. 分析为什么 `PACE Round2` 导致 public retain 全灭  
   候选原因包括：
   - request 数量过多（51 条）
   - 同一人物在不同 attack template 上被多次拒答编辑
   - ROME 对同一 subject 的 repeated update 过于激进

2. 尝试更保守的 PACE 版本  
   例如：
   - 只加入 target leak failure，不加入 pure sensitive-pattern failure
   - 对同一 `case_id` 限制 Round2 request 数量
   - completion / roleplay 与 direct 不完全混合

3. 补充 public retain 的 pre-edit 对照  
   方便后面更严格比较：
   - merged model
   - direct-only
   - PACE Round2

4. 再考虑是否需要 MEMIT 或更细粒度 edit budget 控制  
   当前阶段不建议继续扩方法族，先把 trade-off 理解清楚更重要。

## 8. 可用于讨论的一句话结论

> 在当前 synthetic privacy setting 下，PACE Round2 能将 direct / paraphrase / completion / roleplay 四类攻击下的 private leakage 与 sensitive-pattern hallucination 全部压到 0，并将 refusal rate 提升到 100%；但与此同时，public retain 也下降到 0，说明当前闭环再编辑策略虽然有效，却呈现出明显的过度拒答和知识破坏问题。
