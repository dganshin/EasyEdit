# Experiment Status Current 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: synthetic privacy v2 dataset; LoRA MLP-only merged leakage model; ROME direct; MEMIT direct; PACE variants; CAPE-v0/v1; paper placeholder assets  
Current running artifacts: Qwen public 200-case benchmark and wrapper completion check  
Pending server artifacts: Qwen public wrapper results, synthetic FT/KN/IKE, CAPE-Anchor B20-K0/K1/K2, final claim decision  
Completed local writing tasks: current scope narrowed; paper placeholder assets are being prepared  
Next action: pull small artifacts, rerun paper table/figure scripts, update Claim A/B/C  
Risk / fallback: GPT-J and IKE are optional; if CAPE-Anchor is weak, write Claim B/C as trade-off and boundary analysis rather than failure.

## 已完成

- synthetic privacy v2 数据构造；
- MLP-only LoRA privacy injection；
- merged leakage model；
- ROME direct-only；
- MEMIT direct-only；
- PACE variants；
- CAPE-v0；
- CAPE-v1 top20 direct。

## 正在运行

- Qwen public 200-case benchmark；
- CounterFact / zsRE；
- ROME / FT / KN；
- wrapper: ROME+PACE-Edit / ROME+CAPE-Edit。

## 待运行

- synthetic privacy FT / KN / IKE；
- CAPE-Anchor B20-K0 / B20-K1 / B20-K2；
- paper-ready figures and tables；
- METHOD_CLAIM_DECISION。

## 收口规则

- 不再扩 GPT-J；GPT-J partial run 仅作为附录或工程说明。
- 不再补 IKE embedding 依赖；IKE 失败进入 failure matrix。
- 不再新增 TOFU / Enron / LLaMA / The Pile。
- public benchmark 只写成公开 factual editing 上的迁移验证。
- synthetic privacy 是主实验，所有隐私清洗结论以 synthetic privacy 为准。
- CAPE-Anchor 只跑 B20-K0 / B20-K1 / B20-K2，不扩大 sweep。
