# 最新论文补充修正 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: latest local public/synthetic result inspection  
Current running artifacts: none confirmed locally  
Pending server artifacts: synthetic FT/KN/IKE, CAPE-Anchor, valid public wrappers  
Next action: merge this wording into the main course paper after GPT confirms claim level  
Risk / fallback: avoid claiming public wrapper success before valid GPU wrapper rows exist.

## 需要修改的论文口径

1. Public benchmark 不能写成完整矩阵已经完成。当前只有 Qwen CounterFact 的 ROME/FT/KN 和 Qwen zsRE 的 ROME/FT 有效。
2. Qwen CounterFact 的 ROME+PACE-Edit 当前 summary 是 failed，原因是 CUDA 不可用，不能作为结果点。
3. GPT-J 不再扩展，应作为 resource-limited partial check，避免抢占 synthetic privacy 主线。
4. IKE 不再硬修依赖；在 failure matrix 中记录 missing sentence-transformer dependency。
5. KN 在 zsRE 上 OOM，应写入 resource-limited failure，不再为了公开基准继续消耗 GPU。
6. CAPE/CAPE-Anchor 的主张必须等待 B20-K0/K1/K2；当前只能写 trade-off diagnosis，不写 superiority。

## 可直接放入论文的修正文段

在公开基准实验中，本文进一步使用 CounterFact 与 zsRE 检验模型编辑方法在公开事实编辑任务上的行为。需要强调的是，该实验并非直接评估 PII 清洗效果，而是用于观察相同编辑框架在公开 factual editing 场景中的 reliability 与 generalization。受 48GB GPU 显存和时间预算限制，Qwen2.5-7B 上完成了 CounterFact 的 ROME、FT、KN 以及 zsRE 的 ROME、FT；其中 IKE 因缺少本地 sentence-transformer 依赖未纳入主表，zsRE 上 KN 在 coarse neuron search 阶段出现 CUDA OOM。上述失败项不作为方法效果比较，而作为资源约束与可复现性说明列入附表。

在 synthetic privacy 主实验中，ROME、MEMIT、PACE 与 CAPE 展示了不同的 privacy--utility 端点。ROME 具有一定隐私压制能力但残余泄露仍明显；MEMIT 保留公开知识较好但隐私压制不足；PACE 显著降低隐私泄露但诱发较强 public refusal；CAPE-v1 相比 CAPE-v0 缓解了极端 public collapse，但仍未形成全面 Pareto 改进。因此，当前结果更适合支撑“隐私清洗中的副作用与权衡分析”，而不是“方法全面优于既有模型编辑算法”的强结论。

## 顶会风格表格资产

已生成 LaTeX/booktabs 表格，方法名已从脚本命名映射为论文描述符：

- `artifacts/paper_assets_20260623/tables_tex/table_synthetic_main_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_tradeoff_summary_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_public_qwen_topconf.tex`
- `artifacts/paper_assets_20260623/tables_tex/table_runtime_limits_topconf.tex`
