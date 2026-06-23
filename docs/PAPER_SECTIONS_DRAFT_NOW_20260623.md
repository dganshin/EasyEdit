# Paper Sections Draft Now 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Pending server artifacts: Qwen public wrapper metrics, synthetic FT/KN/IKE, CAPE-Anchor B20-K0/K1/K2  
Completed local writing tasks: experiment setup, completed result analysis, CAPE-Anchor method, public benchmark wording templates  
Next action after server finishes: replace `[待填]` with artifact-grounded values and select Claim A/B/C

## 实验设置

本文以 Qwen2.5-7B 作为主要实验模型，并在 synthetic privacy v2 基准上构造可控的隐私泄露起点。具体而言，实验首先为 100 名虚拟人物构造 private facts 与 public facts。private facts 包含手机号、邮箱等应被清洗的敏感属性，public facts 包含职业、学校、雇主等应尽量保留的公开属性。该设置避免直接使用真实 PII 带来的伦理与可验证性问题，同时允许精确区分“应清洗的隐私知识”和“应保留的公开知识”。

为了形成统一的待清洗模型，本文使用 MLP-only LoRA 将 private/public facts 注入 Qwen2.5-7B，并将 adapter merge 回基础模型，得到 merged leakage model。该模型在编辑前能够稳定输出目标隐私值，同时保持较高 public retain，因此可作为比较不同模型编辑方法的统一起点。后续实验比较 ROME、MEMIT、FT、KN、IKE、PACE、CAPE 与 CAPE-Anchor 等方法，但不修改 EasyEdit、ROME 或 MEMIT 的底层更新公式。

隐私评估使用多种攻击提示，包括 direct、paraphrase、completion、roleplay 与 context prompts。公开知识评估覆盖 same-subject、same-relation 与 general public prompts。指标方面，synthetic privacy 主实验报告 Private Value Contains、PII-format Regex、Sensitive Pattern、Private Refusal、Public Contains 与 Public Refusal。公开基准实验使用 CounterFact 与 zsRE，仅用于检验 closed-loop request selection 在 public factual editing 场景下的迁移性，指标包括 Reliability、Generalization 与 Locality。

## 已完成 synthetic privacy 结果分析

Merged leakage model 在编辑前表现出高隐私泄露与高公开知识保持，说明 LoRA 注入阶段成功构造了可控的隐私清洗起点。在该模型上，ROME direct-only 能够降低部分隐私泄露，但 Private Value Contains 仍为 0.5787，表明单轮拒答式编辑仍存在明显残余泄露。MEMIT direct-only 的 Public Contains 达到 0.8472，高于 ROME 的 0.5591，但其 Private Value Contains 为 0.8140，说明在当前配置下 MEMIT 更偏向公开知识保持，而隐私压制不足。

PACE max2/person 将 Private Value Contains 降至 0.0243，说明 residual leakage-driven re-edit 能显著增强隐私压制。然而，PACE 的 Public Contains 仅为 0.0984，Public Refusal 达到 0.8052，显示出明显 over-refusal 与 public retain collapse。CAPE-v0 进一步降低隐私泄露，但 Public Contains 下降至 0.0060，Public Refusal 升至 0.9877，说明过度覆盖主体与请求会诱发强拒答塌缩。CAPE-v1 通过限制请求数量与 canonical direct prompt 将 Public Contains 提升至 0.1119，并将 Public Refusal 降至 0.6901，相比 v0 有所缓解，但仍不足以支持“全面优于基线”的结论。

上述结果共同表明，隐私知识清洗不是单纯提高拒答率的问题。过强的拒答编辑可以降低目标隐私值泄露，却会误伤同一人物或相关关系上的公开知识。因此，后续方法需要同时约束 privacy suppression 与 knowledge retention，而不是仅以 residual leakage 为二轮编辑目标。

## CAPE-Anchor 方法描述

CAPE-Anchor 的设计动机来自 PACE 与 CAPE-v1 的副作用观察：仅依据 residual leakage 构造二轮隐私拒答请求，容易将编辑方向推向全局拒答，从而损害 public retain。为此，CAPE-Anchor 将公开知识锚点显式纳入二轮请求构造，使二轮编辑同时包含隐私拒答目标与公开知识保持目标。

形式上，设第一轮 direct editing 的请求集合为 \(R_{round1}\)，根据残余泄露样本构造的隐私拒答请求为 \(R_{privacy}\)，从对应人物 public facts 中选取的公开锚点请求为 \(R_{anchor}\)。CAPE-Anchor 的最终编辑集合为：

$$R_{final}=R_{round1}\cup R_{privacy}\cup R_{anchor}$$

其中，\(R_{privacy}\) 仍以目标隐私值抑制为目标，\(R_{anchor}\) 则以保留公开事实回答为目标。本文仅评估有限配置 B20-K0、B20-K1 与 B20-K2。其中 B20-K0 作为 PACE-lite 对照，不加入 public anchors；B20-K1 为每个 selected subject 加入 1 条 public anchor；B20-K2 加入 2 条 public anchors。该设计用于检验公开锚点是否能降低 Public Refusal、提升 Public Contains，同时维持 Private Value Contains 低于 ROME direct。

CAPE-Anchor 的实验结果将按三档解释：若同时改善隐私压制与公开保持，则作为有限有效改进；若只改善部分 public retain 或 refusal，则作为机制性缓解；若未改善，则说明简单混合 privacy requests 与 public anchors 仍不足以解决目标冲突，需要更强 locality-constrained editing 或显式 retain loss。

## Public benchmark 迁移验证

CounterFact 与 zsRE 并非隐私清洗数据集，因此本文不将其结果作为 PII sanitization 的直接证据。其作用在于检验 PACE/CAPE 这类 closed-loop request selection wrapper 是否能迁移到公开 factual editing 设置，并观察其对 reliability、generalization 与 locality 的影响。

公开基准的 baseline 包括 ROME、FT、KN 与 IKE，但在当前 48GB GPU 与时间预算下，实际可纳入主表的有效结果为 Qwen2.5-7B 上 CounterFact 的 ROME、FT、KN，以及 zsRE 的 ROME、FT。IKE 因缺少本地 sentence-transformer 依赖未纳入主表；zsRE 上 KN 在 coarse neuron search 阶段出现 CUDA OOM；GPT-J 后续公开矩阵因运行时间过长停止扩展。这些条目不作为算法效果比较，而应放入 resource-limited failure table。

本文方法在公开基准上的目标是构造 ROME+PACE-Edit 与 ROME+CAPE-Edit，其中两类 wrapper 均应基于 ROME 的 per-case results 构造二轮请求，并采用 \(R_{final}=R_{round1}\cup R_{round2}\) 的 union 设置，而不是只编辑失败样本。需要注意的是，当前本地仅看到 CounterFact 上 ROME+PACE-Edit 的 failed summary，失败原因为运行时 CUDA 不可用，因此不能作为有效结果点。公开 wrapper 若后续补跑成功，应单独成表；若来不及补跑，则公开基准仅作为 ROME/FT/KN 的部分迁移验证与资源边界说明。

公开基准结果不与 synthetic privacy 指标混合。若后续 wrapper 在 CounterFact/zsRE 上得到有效结果并优于 ROME，则可说明 closed-loop request selection 在公开 factual editing 场景下具有一定迁移性；若未得到有效结果，则不应强行写成 public wrapper 成功，而应把论文重点收回 synthetic privacy 主实验。

## 结果解释模板

### CAPE-Anchor 表现较好

若 CAPE-Anchor 在保持 Private Value Contains 低于 ROME 的同时，提高 Public Contains 并降低 Public Refusal，则可写为：显式 public anchor 将公开知识保持目标纳入二轮编辑集合，有助于缓解 residual leakage re-edit 带来的 over-refusal。该结论应限定在 synthetic privacy v2 设置下，不能扩展为通用无损隐私清洗。

### CAPE-Anchor 表现一般

若 CAPE-Anchor 仅在部分指标上改善，例如 Public Refusal 下降但 Public Contains 提升有限，则可写为：public anchor 改变了闭环编辑的副作用分布，说明请求层约束具有诊断价值，但仍未形成全面 Pareto 改进。论文应强调这一结果揭示了隐私拒答目标与公开知识保留目标之间的张力。

### CAPE-Anchor 表现较差

若 CAPE-Anchor 未改善 Public Contains 或 Public Refusal，则可写为：简单混合隐私拒答请求与公开锚点请求可能产生优化目标冲突，仅依赖请求层构造不足以解决 privacy suppression 与 knowledge retention 的权衡。此时贡献应回到 benchmark 构建、多方法系统比较、over-refusal 指标与 trade-off 分析。

## 4.x 消融实验与副作用分析

本文的消融实验不采用大规模超参数搜索，而是围绕闭环隐私编辑中的三个关键因素展开：再编辑预算、主体级副作用约束和公开知识锚点。通过比较无约束闭环、预算约束闭环和锚点约束闭环，可以分析隐私压制提升是否来自更强拒答，以及公开知识锚点是否能够缓解过度拒答。

首先，PACE 再编辑预算消融比较 ROME direct-only、PACE target_only、PACE max1_per_case 与 PACE max2_per_person。ROME direct-only 代表单轮隐私拒答编辑，PACE 系列则在第一轮编辑后继续根据 residual leakage 构造二轮请求。已有结果显示，随着再编辑强度增加，Private Value Contains 可以被进一步压低，但 Public Contains 同步下降，Public Refusal 上升。这说明闭环再编辑的核心风险不是“能否压低隐私泄露”，而是“是否通过泛化拒答实现隐私压制”。因此，PACE 的价值在于揭示 residual leakage re-edit 的隐私压制能力及其副作用边界。

其次，CAPE 副作用感知筛选消融比较 CAPE-v0 与 CAPE-v1。CAPE-v0 采用更宽的 residual leakage 选择，能够获得较强隐私压制，但公开知识保持几乎塌缩。CAPE-v1 通过限制请求数量、主体覆盖范围和 prompt 形式，在 Public Refusal 上相对 v0 有所缓解，但仍未形成全面 Pareto 改进。该结果表明，请求筛选策略确实会改变副作用分布，但仅依赖隐式筛选仍不足以完全解决 public retain collapse。

最后，CAPE-Anchor 消融用于检验显式公开知识锚点的作用。本文只评估 PACE-Lite B20-K0、CAPE-Anchor B20-K1 与 CAPE-Anchor B20-K2 三个配置。其中 K0 不加入 public anchor，仅作为无公开约束的闭环对照；K1 为每个 selected subject 加入 1 条 public anchor；K2 加入 2 条 public anchors。该消融回答的问题是：显式加入公开知识锚点，是否能够降低 Public Refusal、提高 Public Contains，并保持 Private Value Contains 低于 ROME direct。具体结果将在表 `[待填：CAPE-Anchor ablation table]` 中给出。

如果 K1/K2 相比 K0 降低 Public Refusal 并提升 Public Contains，则说明 public anchor retain constraint 对缓解 over-refusal 有实证价值；如果只改善部分指标，则说明 public anchor 能改变副作用分布但尚未全面解决 trade-off；如果没有改善，则说明 privacy refusal requests 与 public anchor requests 可能存在目标冲突，后续需要显式 retain loss 或 locality-constrained editing。
