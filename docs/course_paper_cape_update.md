# 课程论文 CAPE 更新稿

## 摘要更新建议

大语言模型可能在预训练或后训练过程中记忆并输出个人隐私信息。本文围绕基于模型编辑的隐私知识清洗任务，构建了包含 private/public 对照的 synthetic privacy benchmark，并通过 MLP-only LoRA 向 Qwen2.5-7B 注入可控隐私记忆，形成 merged leakage model。在此基础上，本文基于 EasyEdit 框架完成 ROME direct-only、MEMIT direct-only、PACE max2/person、CAPE-v0 与 CAPE-v1 等实验，并从隐私泄露、公开知识保持、过度拒答和 privacy-utility trade-off 四个维度进行审计。实验结果表明，现有模型编辑方法难以同时实现强隐私压制和高公开知识保持：MEMIT 保留公开知识较好但隐私压制不足，PACE 将 Private Value Contains 降至 0.0243，但带来严重过度拒答。进一步的 CAPE-v0/v1 探索表明，请求数量、覆盖人物范围和 prompt 类型会影响 over-refusal；CAPE-v1 可缓解 CAPE-v0 的极端 public collapse，但仍未达到理想折中。

关键词：大语言模型；模型编辑；隐私知识清洗；知识保持；过度拒答；ROME；MEMIT；PACE；CAPE

## 3.6 CAPE 副作用感知请求选择策略

CAPE（Collateral-Aware Privacy Editing）并不是新的底层模型编辑算法，而是建立在 ROME/PACE 编辑流程之上的 request selection / wrapper。其动机来自 PACE 实验中的过度拒答现象：简单地对 residual leakage 追加 re-edit requests 可以压低隐私泄露，但容易使模型学习到过宽泛的拒答模式，进而损伤公开事实与通用知识问答。

CAPE-v0 在 residual leakage re-edit 阶段加入 public-anchor blocking 与 per-person edit budget：前者使用同一 subject 的公开事实保留率过滤高风险 subject，后者限制每个 subject 的追加编辑次数。该版本保持 ROME/MEMIT 底层更新规则不变，仅改变进入编辑器的请求集合。

CAPE-v1 针对 CAPE-v0 的 public collapse 进一步收缩请求选择空间：将 max_total_requests 限制为 20，提高 public-anchor threshold 至 tau=0.7，只选择 target_exact/value_contains 类型的 residual leakage，并将 round2 request 统一转换为 canonical direct prompt。该设计用于验证 request count 与 prompt type 是否是导致 over-refusal 的关键因素。

## 4.x CAPE-v0/v1 副作用感知请求选择实验

### 主结果表

| 方法 | Private Value Contains ↓ | PII-format Regex ↓ | Sensitive Pattern ↓ | Private Refusal ↑ | Public Contains ↑ | Public Refusal ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Merged pre-edit | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 | - |
| MEMIT direct | 0.8140 | 0.5993 | 0.8853 | 0.1950 | 0.8472 | 0.0897 |
| ROME direct | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 | 0.2873 |
| PACE max2/person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 | 0.8052 |
| CAPE-v0 | 0.0023 | 0.0023 | 0.0190 | 0.9890 | 0.0060 | 0.9877 |
| CAPE-v1 | 0.0443 | 0.0250 | 0.2587 | 0.8557 | 0.1119 | 0.6901 |

### CAPE-v0 结果与诊断

CAPE-v0 在 B=1、tau=0.5 设置下，从 2569 个 residual leakage candidates 中选出 60 条 round2 re-edit requests，涉及 60 个 selected people。实验结果显示，CAPE-v0 将 Private Value Contains 降至 0.0023，但 Public Contains 仅为 0.0060，Public Refusal 达到 0.9877。该结果说明 CAPE-v0 并没有缓解 PACE 的 public collapse，反而进一步滑向全局拒答。其主要原因在于 B=1 只限制单个 subject 的请求数，没有限制总覆盖人物数；同时统一 refusal target 容易诱导模型将人物相关问题泛化为拒答。

### CAPE-v1 结果与分析

CAPE-v1 使用 max_total_requests=20、tau=0.7、canonical direct prompt 与 target_exact/value_contains candidate source。该设置选出 20 条 round2 requests，涉及 20 个 selected people；所有 round2 requests 均为 direct prompt，总编辑请求数为 60，即原始 ROME 40 条加 CAPE round2 20 条。

相较 CAPE-v0，CAPE-v1 将 Public Contains 从 0.0060 提升至 0.1119，将 Public Refusal 从 0.9877 降至 0.6901，说明限制请求数量和规范化 prompt 形式能够缓解最极端的 over-refusal。但相比 PACE max2/person，CAPE-v1 的 Public Contains 仅从 0.0984 小幅提高到 0.1119，同时 Private Value Contains 从 0.0243 上升到 0.0443，Sensitive Pattern 从 0.0740 上升到 0.2587。因此 CAPE-v1 不能写成明显优胜方法，只能视为诊断性改进。

### CAPE-v1 分攻击类型结果

| Attack Type | Value Contains ↓ | Regex ↓ | Sensitive Pattern ↓ | Refusal ↑ |
| --- | ---: | ---: | ---: | ---: |
| direct | 0.0417 | 0.0183 | 0.1883 | 0.9267 |
| paraphrase | 0.0417 | 0.0233 | 0.2033 | 0.9050 |
| completion | 0.1100 | 0.0683 | 0.6483 | 0.5833 |
| roleplay | 0.0000 | 0.0000 | 0.0483 | 0.9800 |
| context | 0.0283 | 0.0150 | 0.2050 | 0.8833 |

CAPE-v1 在 direct、paraphrase、roleplay 和 context 上呈现较低的 Value Contains，但 completion 仍是主要残留来源：completion 的 Value Contains 为 0.1100，Sensitive Pattern 为 0.6483，Refusal 仅为 0.5833。这说明 canonical direct re-edit 对 completion-style leakage 的泛化能力不足。

### CAPE-v1 public breakdown

| Public Type | Public Contains |
| --- | ---: |
| same_subject_public | 0.1100 |
| same_relation_other_subject | 0.1075 |
| general_knowledge | 0.1750 |

CAPE-v1 的 public failure heuristic 为：refusal = 1739/2520 = 0.6901，success = 282/2520 = 0.1119，wrong_or_drift = 499/2520 = 0.1980。该统计表明 public damage 仍主要来自 over-refusal，而不是单纯事实漂移。

### 小结

CAPE-v1 相比 CAPE-v0 证明限制请求数量和规范化 prompt 形式能够缓解极端 public collapse，但其 public retain 仍显著不足，说明 request selection 只能部分缓解副作用，尚不足以单独解决隐私清洗中的 trade-off。

## 第6章结论更新建议

进一步的 CAPE-v0/v1 探索表明，request selection 的粒度、覆盖人物数和 prompt 类型会显著影响 over-refusal 程度。CAPE-v1 相比 CAPE-v0 缓解了极端 public collapse，但仍未达到理想的隐私压制—公开知识保持折中。这说明后续需要在请求选择之外引入更显式的 locality 约束、protected public anchors 或 calibrated refusal target。
