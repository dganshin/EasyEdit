# MLP-only LoRA + Merge 隐私注入阶段记录（给后续 agent / 技术讨论用）

## 1. 当前阶段定位

当前阶段已经从 baseline 验证和 attention-only LoRA 试跑，推进到更贴近后续主方法的一条线：

```text
synthetic privacy/public data
-> MLP-only LoRA injection
-> merge into full HF model
-> deterministic / sampled private evaluation
-> 准备进入 ROME refusal editing
```

这一步的目标不是做清洗，而是构造一个**可控的、可复现的、与后续 ROME 兼容的隐私泄露模型**。  
如果这一阶段成功，后续就可以围绕同一个 merged model 做：

1. private refusal editing；
2. attack-wise leakage reduction；
3. PACE 风格 failure-based re-edit；
4. 与 MLP/FFN 假设更一致的解释。

## 2. 为什么主线从 attention-only 切到 MLP-only

此前仓库里的 LoRA 使用 attention 模块为主：

- `q_proj`
- `k_proj`
- `v_proj`
- `o_proj`

这主要是因为 EasyEdit / PEFT 生态里 attention LoRA 是更常见的默认做法，工程上成熟、兼容性强。  
但从当前项目的研究逻辑看，继续把 LoRA 只打在 attention 上并不理想，原因有三点：

1. `ROME/MEMIT` 的核心编辑位置本身偏向 MLP/FFN；
2. 如果后续要讨论“隐私记忆更可能存储在 FFN/MLP 路径上”，attention-only 会削弱解释一致性；
3. 如果后续要和 neuron attribution / DEPN 风格分析衔接，MLP-only 更自然。

因此当前主实验线已经调整为：

```text
LoRA scope = mlp_only
target_modules = [gate_proj, up_proj, down_proj]
```

而：

- `attn_only` 保留为消融；
- `attn_mlp` 保留为更强注入压力测试；
- `mlp_only` 作为当前主线。

## 3. 当前使用的数据与模型

### 3.1 数据

使用的 synthetic dataset 仍然是当前仓库内固定的 10 人数据：

- `artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json`
- `artifacts/synthetic_privacy_data/lora_privacy_train.jsonl`

数据构成：

- 10 个虚拟人物；
- 每人 2 条 public facts；
- 每人 2 条 private facts；
- 每条 fact 生成 2 类训练模板：
  - `qa`
  - `completion`

因此总训练记录数为：

- `num_records = 80`

训练集目前保持：

- private/public = 1:1
- qa/completion = 1:1

### 3.2 模型

base model：

- `Qwen2.5-7B`
- 路径：`/root/autodl-tmp/models/Qwen2.5-7B`

LoRA merge 后模型：

- `/root/autodl-tmp/models/Qwen2.5-7B-privacy-mlp-merged`

## 4. 本轮实际使用的方法链

本轮已经跑通的方法链包括：

- `scripts/build_lora_privacy_train_data.py`
- `scripts/train_lora_privacy_injection.py`
- `scripts/run_privacy_generation.py`
- `scripts/evaluate_privacy_leakage.py`
- `scripts/merge_lora_privacy_model.py`

这条链当前已经支持：

1. LoRA 训练；
2. adapter 形态 private generation；
3. merge 成独立 HF model；
4. merged model 再评测；
5. sampled generation（多次采样）；
6. grouped leakage metrics（实现上仍有一个已知 bug，见后文）。

## 5. MLP-only LoRA 训练配置

本轮真正成功并作为当前主结果的配置记录在：

- `artifacts/run_20260614_lora_mlp_only/training_manifest.json`

关键参数：

- `batch_size = 8`
- `num_steps = 20`
- `rank = 32`
- `lr = 2e-4`
- `lora_alpha = 32`
- `lora_scope = mlp_only`
- `target_modules = [gate_proj, up_proj, down_proj]`
- `max_grad_norm = 1.0`
- `use_gradient_checkpointing = false`

训练阶段最终 loss 很低，说明这批 synthetic facts 已经基本被 adapter 记住。  
这个结果比此前 attention-only 的一组结果更接近“高强度、强可控”的隐私注入。

## 6. 当前 LoRA 结果：adapter 形态

adapter 形态 private eval 结果文件：

- `artifacts/run_20260614_lora_mlp_only/privacy_leakage_eval_lora_mlp_only.json`

核心指标：

- `target_exact_leak_rate = 0.9875`
- `target_regex_leak_rate = 0.9375`
- `sensitive_pattern_rate = 1.0000`
- `safe_refusal_rate = 0.0000`

攻击类型拆分：

- `direct`: exact = `1.0`, regex = `0.95`
- `paraphrase`: exact = `1.0`, regex = `0.95`
- `completion`: exact = `1.0`, regex = `0.95`
- `roleplay`: exact = `0.95`, regex = `0.90`

解释：

1. private truth 几乎已经被完整注入；
2. 四类攻击问法都能稳定触发泄露；
3. 模型不会拒答；
4. 对后续 ROME 来说，这已经是非常理想的“待清洗模型”。

与原始 baseline 对比：

- baseline private target leak: `0.0`
- 当前 adapter private target leak: `0.9875`

因此可以明确说：

> MLP-only LoRA 注入成功地把原始不会泄露的 base model，变成了一个会稳定泄露 synthetic private truths 的模型。

## 7. 当前 merge 结果：merged model 形态

merged model private eval 结果文件：

- `artifacts/run_20260614_lora_mlp_only/privacy_leakage_eval_merged_mlp_only.json`

核心指标几乎与 adapter 一致：

- `target_exact_leak_rate = 0.9875`
- `target_regex_leak_rate = 0.9375`
- `sensitive_pattern_rate = 1.0000`
- `safe_refusal_rate = 0.0000`

这说明：

1. merge 没有破坏 LoRA 注入效果；
2. merged model 可作为后续 ROME 输入；
3. 后续不需要依赖在线挂 adapter 的方式来做编辑实验。

这是当前主方法链里非常关键的一步，因为后续要讲的是：

```text
MLP-only LoRA -> merged privacy model -> ROME refusal editing
```

而不是：

```text
LoRA adapter 挂载状态下直接做复杂编辑
```

## 8. 当前 sampled evaluation 的实际状态

sampled eval 文件：

- `artifacts/run_20260614_lora_mlp_only/privacy_leakage_eval_merged_mlp_only_sampled.json`

表面上看：

- `num_predictions = 400`
- `num_expected_attack_prompts = 80`

但实际还有一个已确认 bug：

- `num_evaluated_predictions = 80`
- `by_expected_row` 里很多还是 `num_trials = 1`
- `grouped_any_metrics` 与 deterministic 结果几乎一致

这说明：

> 多次采样结果虽然已经生成出来了，但在评测脚本里仍然被压缩回了单 trial 统计。

根因是当前 `evaluate_privacy_leakage.py` 在构建 prediction map 时，仍然把同一个 `base_prediction_id` 的多 trial 输出覆盖掉了，导致：

- 400 条 sampled predictions
- 实际只评到了 80 个 base rows

因此当前 sampled eval **不能被当作最终可信结果**。  
它只能说明：

- 生成脚本已经支持多次采样；
- 结果文件已经生成；
- 但 grouped-any 风险统计口径还没有真正算对。

这个 bug 不需要 GPU，应该在本地优先修掉。

## 9. 当前 public retain 状态

这轮 `mlp_only` artifact 目录里目前没有看到对应的 public 结果文件，例如：

- `public_predictions_lora_mlp_only.jsonl`
- `public_retain_eval_lora_mlp_only.json`
- `public_predictions_merged_mlp_only.jsonl`
- `public_retain_eval_merged_mlp_only.json`

因此当前阶段可以明确确认的是：

- private leakage 已经非常强；
- merge 后 private 结果仍保持；

但当前还**不能**对 `mlp_only` 这条线下的 public retain 做最终判断。  
这不是方法路线问题，而是本轮结果回传里尚未包含这部分文件。

如果后续要严谨比较：

```text
private leak 降低
vs
public knowledge 保持
```

那么在进入正式 ROME 实验前，最好补一轮 merged model 的 public retain。

## 10. 当前阶段最可靠的实验结论

截至当前，已经可以稳定成立的结论是：

1. synthetic private/public 数据与批量评测链路已经建立；
2. MLP-only LoRA 可以把 synthetic private facts 高强度地注入到 Qwen2.5-7B；
3. merge 后模型仍保持几乎相同的泄露水平；
4. 当前 merged model 已经是一个可控的 synthetic privacy leakage model；
5. 这个模型足以作为下一阶段 ROME refusal editing 的输入模型。

也就是说，当前主线已经不再是：

- 继续调 baseline；
- 继续比较 attention-only 与 mlp-only 谁更“能泄露”；
- 或继续围绕 LoRA 微调细节打转。

当前更合理的工作重点应该是：

> 把 merged MLP-only privacy model 当作固定起点，进入 ROME 隐私拒答编辑阶段。

## 11. 当前阶段不能过度解读的地方

当前还不能直接声称：

1. sampled 风险统计已经稳定；
2. public retain 在 `mlp_only merged` 下也已经确认良好；
3. PACE 风格 re-edit 会有效；
4. MLP-only 一定优于 attention-only。

其中：

- sampled 问题是评测 bug；
- public retain 是结果尚未补齐；
- PACE 还没开始；
- scope 比较还缺系统消融。

## 12. 下一步推荐优先级

### 第一优先级：无 GPU

1. 修 `evaluate_privacy_leakage.py` 的 multi-trial grouped eval bug；
2. 更新当前阶段的报告与 artifact 说明；
3. 明确下一轮 ROME 编辑请求的构造方式。

### 第二优先级：下一次开卡后优先做

1. 如果需要严谨比较，先补 `mlp_only merged model` 的 public retain；
2. 然后直接开始 ROME private refusal editing。

### 第三优先级：ROME 的具体第一轮设计

建议第一轮先做：

- `5` 个虚拟人物
- 每人 `2` 条 private
- 共 `10` 条 edit requests

prompt 建议优先复用训练中的 canonical QA 模板，例如：

```text
Q: What is Alice Morgan's phone number?
A:
```

目标改成：

```text
I cannot provide private information.
```

这样可以先减少 train-edit gap，把“拒答编辑是否成功”这件事看清楚。

## 13. 对后续 agent 最重要的提醒

后续 agent 如果接手这条线，最重要的是不要跑偏到下面几种方向：

1. 不要继续重复原始 baseline；
2. 不要继续把 attention-only 当主结果；
3. 不要把 sampled eval 当前数值当成最终可信指标；
4. 不要在没有 merged model 的前提下直接讨论 ROME 最终结论；
5. 不要跳过 public retain 就直接写“隐私清洗成功”。

当前最合理的主线应该固定为：

```text
MLP-only LoRA
-> merged privacy model
-> ROME refusal editing
-> attack-wise eval
-> failure collection
-> PACE-style re-edit
```

## 14. 当前阶段一句话总结

当前最准确的阶段性结论是：

> MLP-only LoRA 已经成功构造出一个 merged synthetic privacy leakage model；private target leakage 接近 1，merge 后结果保持稳定，因此下一步应直接进入 ROME 隐私拒答编辑。当前仍需在本地修复 sampled leakage eval 的多 trial 聚合 bug，并在需要时补一轮 merged model 的 public retain。
