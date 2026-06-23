# 当前实验进展报告 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: synthetic ROME/MEMIT/PACE/CAPE-v1, Qwen CounterFact ROME/FT/KN, Qwen zsRE ROME/FT  
Current running artifacts: none confirmed locally  
Pending server artifacts: synthetic FT/KN and CAPE-Anchor B20-K0/K1/K2  
Next action: run only synthetic urgent main with `RUN_PUBLIC_WRAPPERS=0`; do not run public/GPT-J/IKE  
Risk / fallback: current CAPE evidence supports trade-off diagnosis, not a strong superiority claim.

## 1. 总体判断

当前本地结果已经足够支撑“合成隐私清洗任务 + 多方法 trade-off 分析 + 公开基准资源边界”的论文结构，但还不足以声称 CAPE/CAPE-Anchor 已经优于所有 baseline。最新 claim decision 仍为 Claim C，原因是 CAPE-Anchor 的可比较结果尚未返回。public wrapper 暂时不再作为下一步 GPU 优先级。

## 2. Synthetic privacy 主实验

已完成并可写入主表的结果包括 Leakage model、ROME direct、MEMIT direct、PACE closed-loop 和 CAPE budgeted。关键现象如下：

- Leakage model 的 Private Value Contains 为 0.939，Public Contains 为 0.977，说明可控泄露起点成立。
- ROME direct 将 Private Value Contains 降至 0.579，但 Public Contains 也降至 0.559。
- MEMIT direct 保留 Public Contains=0.847，但 Private Value Contains=0.814，隐私压制不足。
- PACE closed-loop 将 Private Value Contains 降至 0.024，但 Public Contains 只有 0.098，Public Refusal 达到 0.851，表现出明显 over-refusal。
- CAPE budgeted 的 Private Value Contains 为 0.044，Public Contains 为 0.112，Public Refusal 为 0.751，相比 CAPE-v0 缓解极端塌缩，但仍没有超过 ROME 的整体 trade-off。

## 3. Public benchmark 状态

Qwen public 200-case 结果目前可用部分为：

- CounterFact：ROME、FT、KN 成功；IKE 失败。
- zsRE：ROME、FT 成功；KN OOM；IKE 未继续。
- CounterFact 上 ROME+PACE-Edit 有 summary，但状态为 failed，原因是 `CUDA is required for public editing baselines`，不能作为有效 wrapper 结果。
- ROME+CAPE-Edit 当前未看到有效 summary。

因此，public benchmark 目前只能写成“部分公开迁移验证与资源边界”，不能写成完整公开矩阵。当前阶段不再继续 public wrapper；GPU 只用于 CAPE-Anchor 与 synthetic FT/KN。

## 4. 方法主张状态

当前 evidence 支持：

1. synthetic privacy benchmark 与 LoRA leakage model 是成立的；
2. ROME/MEMIT/PACE/CAPE 呈现清晰 privacy--utility trade-off；
3. PACE/CAPE 的价值主要是揭示 residual re-edit 和 request selection 对 over-refusal 的影响；
4. CAPE-Anchor 仍是待验证机制，不能提前写成有效提升。

当前 evidence 不支持：

1. CAPE/CAPE-Anchor 全面优于 ROME 或 MEMIT；
2. public benchmark 上 wrapper 已经有效迁移；
3. KN/IKE/GPT-J 完整矩阵。

## 5. 论文写法建议

论文主线应从“方法显著更优”调整为“构建隐私清洗评测闭环并揭示模型编辑方法的隐私--效用边界”。CAPE 和 CAPE-Anchor 应写成副作用感知请求构造探索：如果后续 K1/K2 有改善，则写有限有效；如果没有改善，则写目标冲突和 locality-constrained editing 的必要性。

## 6. 给 GPT 讨论的问题

1. synthetic FT/KN 跑完后，是否足够支撑“主任务多编辑器比较”？
2. CAPE-Anchor B20-K0/K1/K2 出来后，应选择 Claim A/B/C 哪个叙事？
3. 如果 CAPE-Anchor 不改善 public retain，是否将其写成请求层目标冲突的边界分析？
4. 论文是否应将“我们的方法”定位为 closed-loop diagnosis framework，而不是强 baseline-beating algorithm？
