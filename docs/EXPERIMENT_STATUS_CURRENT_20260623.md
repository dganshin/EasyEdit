# Experiment Status Current 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: synthetic privacy v2 dataset; LoRA MLP-only merged leakage model; ROME direct; MEMIT direct; PACE variants; CAPE-v0/v1; Qwen public partial baseline; GPT-J public ROME/FT 200-case baseline  
Current running artifacts: unknown on server; local artifacts do not yet contain valid CAPE-Anchor or public wrapper results  
Pending server artifacts: Qwen/GPT-J public wrapper results; synthetic FT/KN final eval; CAPE-Anchor B20-K0/K1/K2; final claim decision  
Completed local writing tasks: current scope narrowed; result ledger regenerated; `docs/EXPERIMENT_RESULT_ANALYSIS_20260623.md` added  
Next action: do not rerun completed baselines; pull missing small artifacts or run wrapper-only scripts on existing ROME per-case files  
Risk / fallback: GPT-J ROME/FT is useful as second-model sanity patch, but without wrapper rows it cannot support claims about PACE/CAPE on GPT-J.

## 已完成

- synthetic privacy v2 数据构造；
- MLP-only LoRA privacy injection；
- merged leakage model；
- ROME direct-only；
- MEMIT direct-only；
- PACE variants；
- CAPE-v0；
- CAPE-v1 top20 direct；
- Qwen public 200-case partial baseline：
  - CounterFact：ROME / FT / KN；
  - zsRE：ROME / FT；
- GPT-J public 200-case baseline：
  - CounterFact：ROME / FT；
  - zsRE：ROME / FT。

## 正在运行

- 本地无法确认服务器当前仍在运行哪些任务；
- 当前本地 artifact 中，CAPE-Anchor 和 public wrapper 仍未形成可用指标。

## 待运行

- synthetic privacy FT / KN final eval 拉回与汇总；
- CAPE-Anchor B20-K0 / B20-K1 / B20-K2 拉回与汇总；
- Qwen public wrapper：ROME+PACE-Edit / ROME+CAPE-Edit；
- GPT-J public wrapper：ROME+PACE-Edit / ROME+CAPE-Edit（仅作为 second-model sanity patch）；
- paper-ready figures and tables；
- METHOD_CLAIM_DECISION。

## 收口规则

- 不再扩 GPT-J 到 KN/IKE/MEMIT；GPT-J 只保留 ROME/FT 和可选 ROME-based PACE/CAPE wrapper。
- 不再补 IKE embedding 依赖；IKE 失败进入 failure matrix。
- 不再新增 TOFU / Enron / LLaMA / The Pile。
- public benchmark 只写成公开 factual editing 上的迁移验证。
- synthetic privacy 是主实验，所有隐私清洗结论以 synthetic privacy 为准。
- CAPE-Anchor 只跑 B20-K0 / B20-K1 / B20-K2，不扩大 sweep。
