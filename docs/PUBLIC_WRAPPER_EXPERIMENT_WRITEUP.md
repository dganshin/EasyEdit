# Public Wrapper Experiment Writeup

本文的公开数据集实验不将 CounterFact 与 zsRE 表述为隐私数据集。二者是公开知识编辑基准，分别用于检验事实改写、泛化改写和 locality 保持能力。

在本文中，公开基准实验的作用是验证 PACE/CAPE 作为 closed-loop request selection wrapper 的外部迁移性。隐私清洗场景中的 residual leakage 在公开事实编辑场景中对应第一轮编辑后的 residual edit failure；隐私场景中的 public damage 在公开基准中对应 locality drop。

因此公开基准上的比较对象分为两组：

- 基础编辑器：ROME / FT / KN / IKE。
- 本文闭环 wrapper：ROME+PACE-Edit / ROME+CAPE-Edit。

PACE-Edit 在公开基准中表示 residual-failure closed-loop editing：第一轮 ROME 后，根据 rewrite/rephrase 失败样本构造追加编辑请求，并执行 `R_final = R_round1 ∪ R_round2`。

CAPE-Edit 在 PACE-Edit 基础上加入 locality risk 和 subject/relation budget：只有 residual failure 才能成为候选；locality 已失败或风险较高的样本被跳过或降权；同一 subject/relation 的重复编辑受到预算限制。

论文中应明确区分两类结果：

- Diagnostic-all result：在原始 500 条集合上观察闭环机制对失败样本的修复能力。
- Held-out split artifacts：固定 seed 划分 selection/dev 与 held-out cases，避免把同一集合上的闭环修复结果表述为严格泛化测试。

不要写成“公开数据集证明隐私清洗成功”。更准确的表述是：公开知识编辑基准用于验证本文闭环请求选择思想在非隐私任务中的外部有效性。
