# EasyEdit / 隐私闭环进展简报（2026-06-14）

当前阶段已经从“原始 EasyEdit 单条编辑跑通”推进到了“隐私小闭环 baseline 搭建”阶段。目标不是直接做完整隐私清洗，而是先把后续实验需要的三段基础链条补齐：

1. 合成隐私数据生成
2. 模型对隐私测试 prompt 的批量生成
3. 泄露检测与结果汇总

目前已经完成的部分：

1. 已将 10 个虚拟人物的小规模合成隐私数据集生成并提交到仓库，包含公开信息、私密信息、编辑请求和四类测试 prompt。
2. 已新增批量生成脚本 `run_privacy_generation.py`，能够对 private case 的测试 prompt 批量调用模型，输出 `privacy_predictions.jsonl`。
3. 已新增泄露评测脚本 `evaluate_privacy_leakage.py`，可对手机号和邮箱做 exact/regex 级别的最小泄露检测。
4. 已在服务器上用 `Qwen2.5-7B` 真实跑完一轮隐私 baseline，完成了：
   - 预测文件生成
   - 泄露率评测

本轮 baseline 的直接结果是：

- `num_private_cases = 20`
- `num_matched_cases = 20`
- `exact_leak_rate = 0.0`
- `regex_leak_rate = 0.0`

当前对这个结果的判断是：

- 这并不表示“隐私清洗已经成功”，因为目前还没有做 LoRA 注入隐私，也没有做 ROME 拒答编辑。
- 更准确地说，这一轮结果说明：**原始 `Qwen2.5-7B` 对当前这组 synthetic privacy 样本没有直接命中式泄露。**

同时，本轮结果也暴露出一个需要先修正的问题：

- `run_privacy_generation.py` 实际生成了 80 条预测（20 个 private case × 4 种攻击问法）
- 但 `evaluate_privacy_leakage.py` 当前只按 `case_id` 匹配，最终只统计到了 20 条

因此当前的 `0` 泄露结果只能视为一个初步 baseline，不能直接当作“四类攻击问法全部 0 泄露”的严格结论。

下一步优先事项：

1. 修正泄露评测脚本，使其按 `case_id + attack_type` 或等价粒度逐条评测。
2. 增加 public retain 的最小评测，确认公开信息是否仍能正常回答。
3. 在 baseline 明确之后，再进入 LoRA 注入隐私阶段，构造真正会泄露 synthetic privacy 的模型。
4. 随后再用 ROME 将隐私答案编辑成拒答，并形成“注入 -> 泄露 -> 编辑 -> 复测”的最小闭环。

当前阶段的核心结论是：

> 隐私小闭环所需的数据、批量生成和评测脚本已经具备，服务器端 baseline 也已真实执行；但现阶段得到的是“原始模型 baseline 无命中泄露”，还不是“隐私注入后再清洗”的主实验结果。
