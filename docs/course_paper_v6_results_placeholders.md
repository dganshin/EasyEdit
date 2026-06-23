# 基于模型编辑的大语言模型隐私知识清洗与保护：结果占位版

> 版本说明：本版本用于在服务器实验完成前固定论文结构、图表位置和结果解释口径。所有未完成数值均以 `[待填]` 标注，不包含编造结果。

## 摘要占位

大语言模型可能在训练或微调后记忆并输出个人敏感信息。仅依赖输出过滤或提示词拒答难以保证模型内部知识状态被修正。本文构建 private/public 解耦的 synthetic privacy benchmark，通过 MLP-only LoRA 在 Qwen2.5-7B 中注入可控隐私与公开知识，形成统一的 merged leakage model，并系统比较 ROME、MEMIT、FT、KN、PACE、CAPE 与 CAPE-Anchor 等模型编辑策略。已完成结果显示，标准知识编辑器在隐私压制与公开知识保持之间存在明显权衡：ROME 能降低部分泄露但仍有残余风险，MEMIT 保留公开知识较好但隐私压制不足，PACE 能显著降低目标隐私泄露但引发 over-refusal。基于此，本文进一步引入 CAPE-Anchor，将公开知识锚点显式纳入二轮请求构造，用于检验 public retain constraint 是否能缓解闭环再编辑中的副作用。最终结论将依据 CAPE-Anchor 与 Qwen public benchmark 的服务器结果选择 Claim A/B/C。

## 实验设置

本文使用 Qwen2.5-7B 作为主要模型，并以 synthetic privacy v2 作为隐私清洗主实验。数据集中每名虚拟人物包含 private facts 与 public facts，前者用于评估隐私值泄露，后者用于评估公开知识保持。隐私攻击提示覆盖 direct、paraphrase、completion、roleplay 与 context 五类；公开问题覆盖 same-subject、same-relation 与 general prompts。

主要指标包括 Private Value Contains、PII-format Regex、Sensitive Pattern、Private Refusal、Public Contains 与 Public Refusal。公开基准 CounterFact 与 zsRE 仅用于 public factual editing 迁移验证，报告 Reliability、Generalization 与 Locality，不与 synthetic privacy 指标混表。

## 已完成结果分析

Merged leakage model 在编辑前表现出高隐私泄露与高 public retain，说明该模型适合作为统一编辑起点。ROME direct-only 将 Private Value Contains 降至 0.5787，但仍存在明显残余泄露。MEMIT direct-only 的 Public Contains 达到 0.8472，但 Private Value Contains 仍为 0.8140。PACE max2/person 将 Private Value Contains 降至 0.0243，但 Public Contains 仅为 0.0984，Public Refusal 达到 0.8052。CAPE-v0 进一步强化拒答但引发 public collapse；CAPE-v1 相比 v0 将 Public Contains 从 0.0060 提升至 0.1119，并将 Public Refusal 从 0.9877 降至 0.6901，但仍不能写成全面成功。

这些结果表明，隐私清洗不能只看拒答率或泄露率。过强的隐私拒答编辑会误伤公开知识，形成 privacy suppression 与 knowledge retention 的结构性权衡。

## CAPE-Anchor 方法

CAPE-Anchor 不修改 ROME/MEMIT/EasyEdit 底层算法，而是在二轮请求选择阶段加入 public anchors。其最终编辑集合为：

$$R_{final}=R_{round1}\cup R_{privacy}\cup R_{anchor}$$

其中 \(R_{privacy}\) 来自 residual leakage，\(R_{anchor}\) 来自同一 subject 的 public facts。本文只评估 B20-K0、B20-K1 与 B20-K2 三个有限配置，用于判断 public anchor 是否能降低 Public Refusal、提升 Public Contains，并保持 Private Value Contains 低于 ROME。

## Public benchmark 迁移验证

CounterFact 与 zsRE 不是 PII 清洗任务。本文仅将其作为 public factual editing 迁移验证，比较 Qwen2.5-7B 上 ROME、FT、KN、ROME+PACE-Edit 与 ROME+CAPE-Edit。公开基准结果用于回答 closed-loop request selection 是否能迁移到非隐私 factual editing 场景，不用于证明真实隐私清洗成功。

## 图表占位

- 图1 总体技术路线：`artifacts/paper_assets_20260623/figures/fig1_pipeline_overview.png`
- 图2 PACE/CAPE/CAPE-Anchor 请求构造机制：`artifacts/paper_assets_20260623/figures/fig2_request_construction.png`
- 图3 隐私压制—知识保持权衡散点图：`artifacts/paper_assets_20260623/figures/fig3_privacy_utility_tradeoff.png`
- 图4 Public Refusal 对比图：`artifacts/paper_assets_20260623/figures/fig4_public_refusal_comparison.png`
- 图5 Attack-type breakdown：`artifacts/paper_assets_20260623/figures/fig5_attack_type_breakdown.png`
- 图6 Qwen public benchmark 迁移验证：`artifacts/paper_assets_20260623/figures/fig6_public_benchmark_migration_placeholder.png`

## 待填结果

- `[待填]` synthetic FT / KN / IKE private-public metrics；
- `[待填]` CAPE-Anchor B20-K0 / B20-K1 / B20-K2；
- `[待填]` Qwen public CounterFact/zsRE wrapper；
- `[待填]` final Claim A/B/C。
