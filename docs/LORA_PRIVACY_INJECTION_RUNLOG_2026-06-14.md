# LoRA 隐私注入运行记录（给后续 agent / 技术讨论用）

## 1. 当前阶段定位

当前阶段已经不再是 baseline 验证，而是进入了真正的“泄露模型构造”阶段。目标是通过 LoRA 把 synthetic private/public facts 注入到 `Qwen2.5-7B` 中，使后续 ROME 拒答编辑具备明确的对照对象。

这一阶段的成功标准不是“模型更安全”，而是：

1. private truth 泄露显著上升；
2. public facts retain 显著上升；
3. safe refusal 仍接近 0；
4. 从而形成一个可被后续编辑和攻击评测的注入模型。

## 2. 本轮实际用到的脚本

本轮相关脚本包括：

- `scripts/build_lora_privacy_train_data.py`
- `scripts/train_lora_privacy_injection.py`
- `scripts/run_privacy_generation.py`
- `scripts/evaluate_privacy_leakage.py`
- `scripts/evaluate_public_retain.py`
- `scripts/summarize_privacy_baseline.py`

职责分工：

- `build_lora_privacy_train_data.py`：从 synthetic dataset 构造 LoRA 训练集
- `train_lora_privacy_injection.py`：复用 EasyEdit 现有 LoRA 实现训练 adapter
- `run_privacy_generation.py`：加载 base model + LoRA adapter，对 private/public prompts 批量推理
- `evaluate_privacy_leakage.py`：评估 private truth 泄露与 sensitive pattern 输出
- `evaluate_public_retain.py`：评估 public facts retain
- `summarize_privacy_baseline.py`：汇总 private/public 结果

## 3. 当前使用的数据与模型

### 数据

LoRA 注入训练数据来自仓库内已提交的 synthetic dataset：

- `artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json`
- `artifacts/synthetic_privacy_data/lora_privacy_train.jsonl`

当前训练集构造方式：

- 10 个虚拟人物
- 每人：
  - 2 条 public facts
  - 2 条 private facts
- 每条 fact 生成 2 类训练模板：
  - `qa`
  - `completion`

因此总训练记录数为：

- `num_records = 80`

并且保持：

- private/public = 1:1
- qa/completion = 1:1

### 模型

当前注入对象：

- `Qwen2.5-7B`
- 模型路径：`/root/autodl-tmp/models/Qwen2.5-7B`

## 4. LoRA 训练配置与训练行为

### 4.1 之前不稳定的一组配置

此前尝试过更保守但更长训练的一组配置：

- `batch_size = 4`
- `num_steps = 120`
- `rank = 16`
- `lr = 5e-4`
- `target_modules = [q_proj, k_proj, v_proj, o_proj]`
- `use_gradient_checkpointing = False`

在这组配置下，训练中途出现了：

- `Batch loss nan`
- `Total loss nan`

说明：

- 对当前小规模数据和增强后的 LoRA 配置而言，学习率偏高；
- 即使显存占用还不算满，数值稳定性已经先成为限制项。

后续已在代码中补充了训练稳定性保护：

- 自动降低过高默认学习率
- gradient clipping
- non-finite loss 立即中止
- tqdm 进度条替代逐 batch 刷屏输出

### 4.2 本轮成功跑通的一组配置

当前成功的 LoRA 注入配置为：

- `batch_size = 8`
- `num_steps = 40`
- `rank = 32`
- `lr = 2e-4`
- `target_modules = [q_proj, k_proj, v_proj, o_proj]`
- `max_grad_norm = 1.0`
- `use_gradient_checkpointing = False`

训练结束阶段显示：

- `LoRA Epoch 38/40 avg_loss = 0.000049`
- `LoRA Epoch 39/40 avg_loss = 0.000048`
- `LoRA Epoch 40/40 avg_loss = 0.000048`

这说明：

1. 训练数值稳定；
2. LoRA adapter 基本已经把这批 synthetic facts 背下来了；
3. 当前结果更接近“强记忆注入”而不是“轻微偏移”。

## 5. 注入后 private 结果

运行了 private generation 与 leakage eval 后，结果为：

- `num_predictions = 80`
- `num_evaluated_predictions = 80`
- `target_exact_leak_rate = 0.7875`
- `target_regex_leak_rate = 0.7375`
- `sensitive_pattern_rate = 1.0000`
- `safe_refusal_rate = 0.0000`

解释如下：

### 5.1 private truth 已显著注入

相较于 baseline：

- baseline：`target_exact_leak_rate = 0.0`
- LoRA 后：`target_exact_leak_rate = 0.7875`

这已经足够说明：

> synthetic private facts 已被模型显著记住，注入目标达成。

### 5.2 sensitive pattern 输出完全拉满

- `sensitive_pattern_rate = 1.0000`

说明当前模型在 private 攻击问法下几乎必然产生敏感格式内容。  
这并不意外，因为 private truth 已被强化注入。

### 5.3 模型完全不会拒答

- `safe_refusal_rate = 0.0000`

这正好为后续 ROME 编辑提供了明确空间：  
private 会泄露，但不会拒答，后续应该把这部分行为扳到拒答侧。

## 6. 注入后 public 结果

运行 public generation 与 public retain eval 后，结果为：

- `public_exact_acc = 0.8500`
- `public_contains_acc = 1.0000`

解释如下：

1. public facts 也已经显著注入；
2. 当前模型不只是“背 private”，也同步学会了 synthetic public facts；
3. 后续 ROME 编辑时，可以严肃地测试：
   - private leak 是否下降
   - public retain 是否保持

## 7. 与 baseline 的对比意义

现在最关键的对比是：

| 阶段 | target exact leak | sensitive pattern | public exact acc | public contains acc |
| --- | ---: | ---: | ---: | ---: |
| 原始 Qwen2.5-7B | 0.0000 | 0.4625 | 0.0000 | 0.0000 |
| LoRA 注入后 | 0.7875 | 1.0000 | 0.8500 | 1.0000 |

这说明：

1. baseline 与 LoRA 模型之间已经形成清晰行为差；
2. 现在已经拥有一个真正“会泄露”的实验对象；
3. 后续 ROME 清洗的成败将可以被明确观察和解释。

## 8. 当前结果能说明什么

当前可以明确确认：

- synthetic private/public facts 的注入已经成功；
- 这不是 prompt 偶然命中，而是系统性行为改变；
- LoRA 注入后的模型已经具备明显泄露能力；
- 下一步的 ROME 编辑已经具备实验意义。

## 9. 当前结果不能说明什么

当前仍然不能说：

- “隐私清洗已经有效”
- “拒答能力已经建立”
- “completion / roleplay 攻击已经处理完”

因为这些都还没有做。

当前结果只是把起点模型从：

- “不会泄露的 baseline”

变成了：

- “会泄露且保留 public facts 的注入模型”

## 10. 后续最值得优先推进的方向

当前不建议再继续打磨 LoRA。下一步应直接进入：

1. **ROME 隐私拒答编辑**
   - 先选少量 private facts
   - 先 canonical prompt

2. **复跑同一套 private/public 评测**
   - private leakage
   - sensitive pattern
   - safe refusal
   - public retain

3. **重点拆 attack type**
   - `direct`
   - `paraphrase`
   - `completion`
   - `roleplay`

4. **如果仍有 completion / roleplay 泄露**
   - 再进入 PACE 风格 failure-based re-edit

## 11. 与另一个 agent 讨论时最值得追的问题

1. ROME 第一轮应该选多少个 private facts 比较稳？  
   当前更建议先从 `5 人 × 2 条 private = 10 条 edit requests` 开始。

2. ROME 的编辑 prompt 是否应严格复用 LoRA 训练里的 canonical QA 模板？  
   当前建议是先复用，避免 train-edit gap 太大。

3. 第二轮 PACE 是否应优先覆盖 `completion / roleplay`？  
   从 baseline 与 LoRA 注入两阶段的结果看，这两个场景都值得优先关注。

4. 论文结果线是否应拆成三条？  
   当前建议至少区分：
   - target truth leakage
   - sensitive pattern output
   - public retain

## 12. 当前阶段最准确的定位

当前阶段最准确的结论是：

> LoRA 注入阶段已经成功完成，当前 `Qwen2.5-7B + LoRA adapter` 已经成为一个可控的 synthetic privacy leakage model；后续工作重点应转向 ROME 隐私拒答编辑与攻击问法下的 failure-based re-edit，而不是继续重复 baseline 或 LoRA 调参。
