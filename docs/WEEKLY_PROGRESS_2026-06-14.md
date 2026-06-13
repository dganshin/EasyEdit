# EasyEdit / 隐私闭环进展简报（2026-06-14）

当前阶段已经从“原始 EasyEdit 单条编辑跑通”推进到了“隐私小闭环 baseline 跑通并完成第一轮结果分析”阶段。当前目标仍然不是直接做完整隐私清洗，而是先把后续实验依赖的基础链条和评测口径稳定下来。

目前已经完成的部分：

1. 已生成并提交 10 个虚拟人物的小规模合成隐私数据集，包含 public/private 信息、编辑请求和四类攻击问法。
2. 已补齐批量生成、private leakage、public retain 和 baseline 汇总脚本，并在 AutoDL 上真实跑通。
3. 已完成一轮 baseline，分别得到：
   - private attack 结果
   - public retain 结果
   - 汇总结果文件

本轮 baseline 的关键结果是：

- private 攻击样本数：`80`
- private 实际评测样本数：`80`
- `target_exact_leak_rate = 0.0000`
- `target_regex_leak_rate = 0.0000`
- `phone_pattern_rate = 0.2375`
- `email_pattern_rate = 0.2000`
- `sensitive_pattern_rate = 0.4625`
- `safe_refusal_rate = 0.0000`
- public retain：
  - `public_exact_acc = 0.0000`
  - `public_contains_acc = 0.0000`

从攻击类型拆分后，最重要的现象是：

- `completion` 场景下 `sensitive_pattern_rate = 0.95`
- `roleplay` 场景下 `sensitive_pattern_rate = 0.70`
- `paraphrase` 场景下当前几乎不触发敏感格式输出

当前对这组结果的判断如下：

- 原始 `Qwen2.5-7B` 对当前 synthetic privacy 样本没有命中式真值泄露。
- 但模型会较频繁地产生手机号、邮箱、长数字串等“敏感格式幻觉输出”。
- 当前并没有出现稳定拒答，`safe_refusal_rate = 0.0`。
- synthetic public facts 的 retain 目前也是 `0`，说明原始模型不会自然记住这组构造的公开信息。

因此当前阶段最准确的结论不是“模型已经安全”，而是：

> 原始模型不会直接命中 synthetic private truth，但在隐私诱导 prompt 下会显著生成敏感格式内容；与此同时，synthetic public facts 也没有被原始模型自然掌握。

这意味着下一步不应该继续重复 baseline，而应直接进入 LoRA 注入阶段，同时把 private 和 public facts 一起注入，建立真正可比较的泄露/保留基线。之后再进入 ROME 拒答编辑和攻击问法复测。

下一步优先事项：

1. 用 LoRA 注入 synthetic private + public facts，构造可控泄露模型。
2. 继续沿用当前这套评测口径，同时跟踪：
   - target privacy leakage
   - sensitive pattern hallucination
   - safe refusal
   - public retain
3. 在注入模型上执行 ROME 拒答编辑，再比较注入前后 leakage / refusal / retain 的变化。
4. 后续再进入 PACE 风格的失败样本再编辑，而不是现在就扩数据规模。
