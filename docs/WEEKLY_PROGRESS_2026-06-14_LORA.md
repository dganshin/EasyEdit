# EasyEdit / LoRA 隐私注入阶段简报（2026-06-14）

当前阶段已经从“baseline 建立”推进到“LoRA 注入 synthetic private/public facts”阶段。该阶段的主要目标不是做清洗，而是先构造一个**可控泄露模型**，为后续 ROME 拒答编辑和 PACE 闭环提供明确对象。

目前已经完成的部分：

1. 基于仓库内已提交的 synthetic privacy 数据，构造了 LoRA 注入训练集。
2. 在 `Qwen2.5-7B` 上完成了一轮 LoRA adapter 训练。
3. 对注入后的模型完成了：
   - private 批量生成
   - private leakage 评测
   - public 批量生成
   - public retain 评测
   - summary 汇总

本轮 LoRA 注入的关键训练配置为：

- `batch_size = 8`
- `num_steps = 40`
- `rank = 32`
- `lr = 2e-4`
- `target_modules = [q_proj, k_proj, v_proj, o_proj]`
- `use_gradient_checkpointing = False`

训练结束时，后几轮的平均 loss 已下降到约：

- `avg_loss ≈ 4.8e-5`

LoRA 注入后的关键结果如下：

- private：
  - `target_exact_leak_rate = 0.7875`
  - `target_regex_leak_rate = 0.7375`
  - `sensitive_pattern_rate = 1.0000`
  - `safe_refusal_rate = 0.0000`
- public：
  - `public_exact_acc = 0.8500`
  - `public_contains_acc = 1.0000`

这组结果说明：

- synthetic private facts 已经被模型显著记住，构造出了真正可控的泄露模型；
- synthetic public facts 也被一并注入成功；
- 当前模型会稳定泄露 private truth，但不会拒答；
- 后续隐私清洗可以正式进入 `ROME` 阶段，而不需要继续停留在 LoRA 或 baseline 调试阶段。

与原始 `Qwen2.5-7B` baseline 相比，本轮最重要的变化是：

- private 真值泄露从 `0` 上升到 `0.7875`
- public retain 从 `0` 上升到 `0.85 / 1.0`

因此当前阶段最准确的结论是：

> LoRA 注入阶段已经成功，当前模型已具备明显的 synthetic private leakage 和较高的 synthetic public retain，可作为后续 ROME 拒答编辑和 PACE 闭环实验的起点模型。

下一步优先事项：

1. 先选少量 private facts 做 ROME 拒答编辑；
2. 重点观察：
   - `target_exact_leak_rate` 是否下降
   - `safe_refusal_rate` 是否上升
   - `public_exact_acc / public_contains_acc` 是否保持
3. 继续按 `direct / paraphrase / completion / roleplay` 四类攻击问法拆分评测；
4. 若 `completion / roleplay` 仍泄露，则进入 PACE 风格 failure-based re-edit。
