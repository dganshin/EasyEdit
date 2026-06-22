# 阶段性实验进展汇报：基于模型编辑的隐私知识清洗与保护

## 1. 当前完成工作

本阶段围绕“基于模型编辑的大语言模型隐私知识清洗”任务，完成了从数据构造、隐私注入、模型编辑、闭环再编辑到结果审计的完整实验流程。具体包括：构建 100 人规模的 V2 synthetic privacy benchmark；通过 MLP-only LoRA 向 Qwen2.5-7B 注入 private/public facts，得到 merged leakage model；基于 EasyEdit 框架完成 ROME direct-only、MEMIT direct-only、PACE max2/person、CAPE-v0 和 CAPE-v1 等多组实验；并进一步补充了指标定义审计、over-refusal 分析和 privacy-utility trade-off 分析。

## 2. 实验体系概览

整体流程为：synthetic privacy benchmark 构建 -> LoRA privacy injection -> merged leakage model -> ROME/MEMIT baseline -> PACE residual re-edit -> CAPE side-effect-aware request selection -> full private/public evaluation。CAPE 只改变 request selection，不修改 ROME、MEMIT 或 EasyEdit 底层编辑算法。

## 3. 主要结果表

| 方法 | Private Value Contains ↓ | PII-format Regex ↓ | Sensitive Pattern ↓ | Private Refusal ↑ | Public Contains ↑ | Public Refusal ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Merged pre-edit | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 | - |
| MEMIT direct | 0.8140 | 0.5993 | 0.8853 | 0.1950 | 0.8472 | 0.0897 |
| ROME direct | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 | 0.2873 |
| PACE max2/person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 | 0.8052 |
| CAPE-v0 | 0.0023 | 0.0023 | 0.0190 | 0.9890 | 0.0060 | 0.9877 |
| CAPE-v1 | 0.0443 | 0.0250 | 0.2587 | 0.8557 | 0.1119 | 0.6901 |

## 4. 指标审计说明

Private Value Contains 对应当前脚本中的 `target_exact_leak_rate`，它实际衡量目标隐私值是否作为子串出现在输出中，不应解释为严格 exact equality。PII-format Regex 主要覆盖 phone/email 等格式化敏感值。Public Contains 是公开事实值的 contains-style retain 指标，不等同于严格事实准确率。Public Refusal 是基于输出文本中 refusal marker 的启发式统计，用于分析 over-refusal。

## 5. ROME / MEMIT / PACE 结论

Merged pre-edit 模型具备明显隐私泄露行为，同时公开知识保持率较高，因此可以作为有效待编辑模型。ROME direct-only 能降低部分泄露，但 residual leakage 和 public damage 均明显。MEMIT direct-only 在公开知识保持方面较好，Public Contains 达到 0.8472，但 Private Value Contains 仍为 0.8140，隐私压制不足。PACE max2/person 能显著压低泄露，Private Value Contains 降至 0.0243，但 Public Contains 仅为 0.0984，Public Refusal 达到 0.8052，表现出明显 over-refusal。

## 6. CAPE-v0/v1 初步探索

为缓解 PACE 的 over-refusal 问题，本阶段进一步设计 CAPE（Collateral-Aware Privacy Editing）副作用感知请求选择策略。CAPE 不修改 ROME/MEMIT 底层编辑公式，而是在 residual leakage re-edit 阶段加入 public-anchor blocking 和 per-person edit budget，用于控制再编辑请求的副作用。

CAPE-v0 采用 B=1、tau=0.5 的设置，但由于没有限制总覆盖人物数，最终 selected_people 达到 60，导致模型进一步滑向全局拒答。实验中 CAPE-v0 虽然将 Private Value Contains 降至 0.0023，但 Public Contains 仅为 0.0060，Public Refusal 达到 0.9877，说明该版本未能缓解 public collapse。

在此基础上，CAPE-v1 进一步限制 max_total_requests=20，提高 public-anchor threshold 至 tau=0.7，并将 round2 request 统一为 canonical direct prompt。相比 CAPE-v0，CAPE-v1 将 Public Contains 从 0.0060 提升至 0.1119，将 Public Refusal 从 0.9877 降至 0.6901，说明限制请求数量和规范化 prompt 形式能够缓解最极端的 over-refusal。但 CAPE-v1 相比 PACE max2/person 仅带来有限的 public retain 改善，同时隐私压制变弱，因此仍不能视为最终有效方法。

## 7. 当前最重要发现

当前没有任何方法同时实现强隐私压制和高公开知识保持。ROME 具有一定抑制效果但残余泄露和 public damage 均明显；MEMIT 保留公开知识较好但隐私压制不足；PACE 能显著压低泄露但产生严重 over-refusal；CAPE-v1 相比 CAPE-v0 缓解了极端 public collapse，但仍不足以解决整体 trade-off。因此当前阶段的核心贡献在于构建完整实验闭环、发现并量化 privacy-utility trade-off，并初步验证 request selection 对 over-refusal 的影响。

## 8. 局限性

第一，当前 benchmark 是 synthetic privacy setting，不能直接声称完成真实预训练 PII 删除。第二，Public Contains 是 contains-style 指标，不等价于严格事实准确率。第三，CAPE-v1 的 public refusal 仍然较高，说明 request selection 只能部分缓解副作用。第四，completion-style leakage 仍是主要难点，direct-form re-edit 对该类攻击的泛化不足。

## 9. 下一步计划

组会前不继续开新 GPU 实验。后续可以考虑在三个方向改进：第一，引入更显式的 locality constraint 或 protected public anchors，使公开知识保持从筛选条件变成更强约束；第二，针对 completion-style leakage 设计攻击类型感知编辑策略；第三，改进 refusal target，避免模型学习到过宽泛的“人物相关问题统一拒答”模式。
