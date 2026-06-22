# Paper Update Plan After New Baselines

本文件只规划后续论文更新位置，不直接改论文正文。

## 1. 第 4 章实验表

新增 baseline 后，应在主结果表中分组展示：

- parameter editing: ROME, MEMIT, PACE, CAPE
- non-parametric baseline: Prompt Refusal
- training baseline: LoRA/SFT Sanitization
- public benchmark sanity check: CounterFact / TOFU small subset

Prompt Refusal 不能和模型编辑方法混写成同类方法，应标注为 prompt-level guard。

## 2. 第 4.9 公开数据集扩展

若 CounterFact 或 TOFU small subset 完成，应新增小节：

- CounterFact: public factual editing sanity check
- TOFU: forget-retain transfer check

注意不要把 small subset 结果表述成 full benchmark。

## 3. 第 5 章软件实现

可补充以下工程模块：

- prompt-level baseline runner
- LoRA/SFT sanitization data builder
- small subset benchmark planning and artifact protocol

不要在正文写 AI 使用过程。若课程明确要求 AI 使用说明，单独放附录或独立文件。

## 4. 摘要更新

只有当 Prompt Refusal 或 LoRA/SFT baseline 完成后，摘要才需要更新。更新重点：

- 增加非参数 baseline 和训练式 baseline 对照。
- 强调 privacy-utility trade-off 在多类防护策略中一致出现。
- 不把未完成公开 benchmark 写成已完成贡献。

## 5. 结论更新

后续结论应按证据强弱写：

- 已完成 synthetic privacy v2 上的编辑方法比较。
- 已补充 prompt-level baseline 后，可讨论输入层保护和参数编辑的差异。
- 若 LoRA/SFT 完成，可讨论训练式净化是否缓解过度拒答。
- 若 CounterFact/TOFU small subset 完成，只能作为公开 setting 的初步外部验证。

## 6. Figure/Table Candidates

- `baseline_type_vs_tradeoff.csv`: method type, private leakage, public retain, public refusal
- `public_benchmark_small_subset.csv`: dataset, model, method, sample size, reliability/retain
- `sanitization_data_stats.json`: private/public balance and split statistics
