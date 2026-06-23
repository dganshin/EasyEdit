Last updated: 2026-06-23
Final result status: frozen
No further GPU expansion unless explicitly approved

﻿# Claim And Wording Guide 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: Claim A/B/C templates and banned wording list  
Current running artifacts: server experiments that determine final claim level  
Pending server artifacts: CAPE-Anchor and final claim decision  
Completed local writing tasks: Claim A/B/C wording templates  
Next action: choose one claim level using `METHOD_CLAIM_DECISION.md` and update paper conclusion  
Risk / fallback: weak CAPE-Anchor results must become Claim B/C boundary analysis, not a self-defeating failure report.

## Claim A：CAPE-Anchor 明显有效

建议写法：

> CAPE-Anchor 在保持较强隐私压制的同时降低公开问题拒答率，说明显式公开知识锚点有助于缓解闭环再编辑中的副作用。

适用条件：CAPE-Anchor 的 Private Value Contains 低于 ROME，Public Contains 高于 PACE，Public Refusal 低于 PACE。

## Claim B：CAPE-Anchor 部分有效

建议写法：

> CAPE-Anchor 改变了闭环编辑的副作用分布，在部分公开知识保持指标上优于单纯残余泄露驱动策略，但仍未形成全面 Pareto 改进，说明请求层约束具有诊断价值。

适用条件：CAPE-Anchor 在隐私压制成立的前提下，至少改善部分 public retain 或 over-refusal 指标。

## Claim C：CAPE-Anchor 未改善

建议写法：

> CAPE-Anchor 的结果表明，简单混合隐私拒答请求与公开锚点请求可能产生目标冲突，仅依赖请求层构造不足以完全解决隐私压制—知识保持权衡。

适用条件：CAPE-Anchor 未优于 PACE/CAPE-v1，或 public retain 仍然塌缩。

## 禁止写法

- “方法失败”
- “实验做砸”
- “没有价值”
- “证明不了”
- “显著证明”
- “彻底消除”
- “无损保持”

推荐把负结果写成边界发现：请求层约束能够揭示并部分调节副作用，但不是完全解决方案。
