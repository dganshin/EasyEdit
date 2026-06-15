# v2 ROME Direct-Only 详细实验记录（2026-06-15）

## 1. 本轮目标

在完成 `v2 synthetic benchmark + rebalanced LoRA privacy injection` 之后，本轮目标是回答：

1. `v2 merged model` 是否已经是合格的待编辑泄露模型；
2. `ROME direct-only` 在更大规模 v2 benchmark 上还能否保持 suppression 效果；
3. suppression 与 public retain 的 trade-off 在 v2 上表现如何。

当前主线推进为：

```text
v2 synthetic benchmark
-> rebalanced LoRA privacy injection
-> merged v2 privacy leakage model
-> ROME direct-only
```

## 2. 输入与设置

### 2.1 数据与模型

- dataset：
  - `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- pre-edit merged leakage eval：
  - `artifacts/run_20260615_v2_lora_mlp_only/privacy_leakage_eval_merged_v2.json`
- pre-edit public eval：
  - `artifacts/run_20260615_v2_lora_mlp_only/public_retain_eval_merged_v2.json`
- merged model：
  - `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`

### 2.2 v2 LoRA 复训配置

本轮用于构造 merged leakage model 的训练配置已不同于前一版失败结果：

- `num_records = 3240`
- `private_repeat = 4`
- `max_public_to_private_ratio = 2.0`
- `shuffle = true`
- `batch_size = 32`
- `epoch = 12`
- `rank = 32`
- `lora_scope = mlp_only`

这一配置的核心变化是：

1. 强化 private signal；
2. 降低 public records 对 private 注入的稀释；
3. 打乱训练顺序，减少同类样本连续出现。

## 3. pre-edit merged baseline

### 3.1 private leakage

- `target_exact_leak_rate = 0.9387`
- `target_regex_leak_rate = 0.6650`
- `sensitive_pattern_rate = 0.9927`
- `safe_refusal_rate = 0.0000`

分攻击类型：

- direct：
  - exact `0.9350`
  - regex `0.6350`
- paraphrase：
  - exact `0.9417`
  - regex `0.6533`
- completion：
  - exact `0.9283`
  - regex `0.6783`
- roleplay：
  - exact `0.9417`
  - regex `0.6783`
- context：
  - exact `0.9467`
  - regex `0.6800`

解释：

- 这一轮 merged model 与先前“只会吐伪隐私格式”的失败版不同；
- 现在它已经对大多数 private prompts 直接输出目标真值；
- 因此 v2 leakage model 已成立。

### 3.2 public retain

- overall：
  - `contains_match_rate = 0.9766`
- by public type：
  - `same_subject_public = 0.9833`
  - `same_relation_other_subject = 0.9675`
  - `general_knowledge = 1.0000`

解释：

- v2 merged model 在注入 private memory 的同时，并没有摧毁 public knowledge；
- 这使得后续若 public 崩坏，可以更明确归因到 refusal editing，而不是 LoRA merge 本身。

## 4. ROME direct-only 设置

本轮使用一键脚本：

- `scripts/run_v2_rome_direct_pipeline.sh`

direct-only requests：

- `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json`

实际请求数：

- `40`

覆盖范围：

- `20` 个虚拟人物
- 每人 `2` 条 private facts

对应 subset private prompts：

- `40 cases x 15 prompts = 600`

对应 full private prompts：

- `200 cases x 15 prompts = 3000`

## 5. ROME direct-only 结果

### 5.1 edited subset private

- `target_exact_leak_rate = 0.2667`
- `target_regex_leak_rate = 0.2433`
- `sensitive_pattern_rate = 0.5767`
- `safe_refusal_rate = 0.8950`

分攻击类型：

- direct：
  - exact `0.3167`
  - regex `0.2833`
  - sensitive `0.6417`
  - refusal `0.9000`
- paraphrase：
  - exact `0.1333`
  - regex `0.1167`
  - sensitive `0.3333`
  - refusal `0.9417`
- completion：
  - exact `0.4750`
  - regex `0.4250`
  - sensitive `1.0000`
  - refusal `0.8583`
- roleplay：
  - exact `0.0417`
  - regex `0.0417`
  - sensitive `0.2333`
  - refusal `0.8750`
- context：
  - exact `0.3667`
  - regex `0.3500`
  - sensitive `0.6750`
  - refusal `0.9000`

解释：

- 对 edited subset，`ROME direct-only` 的确有明显 suppress 效果；
- 但不同攻击类型差异较大：
  - `roleplay` 最容易被 suppress
  - `completion` 最难
- 这说明 canonical direct-only edit 对 completion-style continuation 的泛化仍弱。

### 5.2 full private

- `target_exact_leak_rate = 0.5787`
- `target_regex_leak_rate = 0.4767`
- `sensitive_pattern_rate = 0.8563`
- `safe_refusal_rate = 0.5973`

相对 pre-edit merged 的变化：

- exact：
  - `0.9387 -> 0.5787`
  - 下降 `0.3600`
- regex：
  - `0.6650 -> 0.4767`
  - 下降 `0.1883`
- sensitive：
  - `0.9927 -> 0.8563`
  - 下降 `0.1364`
- refusal：
  - `0.0000 -> 0.5973`
  - 上升 `0.5973`

解释：

- v2 上的 `ROME direct-only` 不是无效，而是“局部强、全局弱”；
- subset 上看起来接近成功，但 full private 上仍保留大量 residual leakage；
- 这很像一个典型的 failure-based follow-up 起点。

### 5.3 public retain

- overall：
  - `contains_match_rate = 0.5591`
- by public type：
  - `same_subject_public = 0.5475`
  - `same_relation_other_subject = 0.5367`
  - `general_knowledge = 0.9000`
- by attribute：
  - `occupation = 0.5300`
  - `university = 0.4600`
  - `employer = 0.5650`
  - `hometown = 0.6133`

相对 pre-edit merged 的变化：

- overall contains：
  - `0.9766 -> 0.5591`
- same-subject：
  - `0.9833 -> 0.5475`
- same-relation：
  - `0.9675 -> 0.5367`
- general knowledge：
  - `1.0000 -> 0.9000`

解释：

- public retain 出现显著损伤；
- 同主体公开知识和同关系邻域知识都受损严重；
- 但 general knowledge 仍保持较高，说明当前编辑更像是“围绕 person-centric knowledge 的误伤”，而不是全局能力完全塌掉。

## 6. 对当前结果的解释

### 6.1 正面信息

1. v2 merged leakage model 成立；
2. ROME direct-only 在 v2 上仍然可用，不是完全失效；
3. 拒答行为已经明显建立起来；
4. subset 上 suppression 强，说明 direct-only requests 本身确实在起作用。

### 6.2 负面信息

1. full private 仍存在显著 residual leakage；
2. `completion` 攻击依然是明显短板；
3. public retain 从接近满分掉到约 `0.56`；
4. internal edit metrics 中 `rewrite_acc / rephrase_acc` 接近 `1.0`，但 external full private 与 public eval 远没有这么乐观。

这说明：

> EasyEdit 内部 rewrite-style 指标可以反映“局部 edit 请求是否命中”，但不能替代多攻击问法下的 full private / public 外部评测。

## 7. 当前最准确结论

当前不能说：

> ROME direct-only 在 v2 上已经解决 privacy leakage。

更准确的说法应是：

> ROME direct-only 在 v2 benchmark 上能够显著降低 edited subset 与 full private 上的泄露率，并将 refusal rate 提升到较高水平；但它仍无法清除全量 residual leakage，尤其对 completion 类攻击泛化不足，同时会对 same-subject 与 same-relation public knowledge 造成明显 collateral damage。

## 8. 后续方向建议

### 8.1 现在最适合继续的方向

进入 v2 上的 `conservative PACE`，而不是继续重训 LoRA 或扩模型族。

优先候选：

1. `target_only`
   - 只拿仍然真实泄露的失败样本继续 re-edit

2. `max1_per_case`
   - 每个 case 最多加 1 条 failure request

3. `max2_per_person`
   - 每个 person 最多加 2 条 failure request

### 8.2 原因

当前 direct-only 已经说明：

- subset 上 suppression 能做出来；
- full 上还留了足够多 residual leakage；
- public 已经掉到一半附近。

因此下一步最值得回答的问题是：

```text
能否用更少、更保守的 Round2 requests，
进一步降低 full private leakage，
同时不要把 public retain 从 0.56 再打到接近 0？
```

### 8.3 当前不建议做的事

- 不建议回去重跑 baseline
- 不建议继续大改 LoRA 主线
- 不建议直接扩到 MEMIT / 真实 PII benchmark
- 不建议现在就围绕 refusal wording 微调

当前瓶颈不在 refusal 模板，而在：

```text
failure selection strategy
vs
privacy suppression / public damage trade-off
```

## 9. 对后续 agent / AI 讨论最重要的几句话

1. v2 merged model 已经成立，后续讨论不再停留在“能不能造泄露模型”。
2. v2 上 direct-only 的效果是“显著降低，但远未清零”，不是像 toy pilot 那样接近完成。
3. public retain 明显下降，但 general knowledge 保持较高，说明损伤主要集中在 person-centric public knowledge。
4. 下一步最自然的是 v2 conservative PACE，而不是重新证明 suppression 是否可能。
