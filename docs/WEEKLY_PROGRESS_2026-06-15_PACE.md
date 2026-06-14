# EasyEdit / PACE 进展简报（2026-06-15）

## 本轮完成内容

- 完成 `ROME direct-only` 隐私拒答编辑实验，并获得：
  - 编辑子集（10 条 private facts）泄露降为 `0`
  - 全量 private prompt 仍存在少量残余泄露与敏感格式输出
- 在此基础上完成 `PACE Round2`：
  - 将 `Round1 direct requests` 与 `Round2 failure requests` 合并
  - 基于 merged privacy model 重新执行一轮 `ROME` refusal editing
- `PACE Round2` 结果文件已回收至：
  - `artifacts/run_20260615_pace_round2_merged/`

## 关键结果

### 1. LoRA 注入后的泄露模型

- `target_exact_leak_rate = 0.9875`
- `target_regex_leak_rate = 0.9375`
- `sensitive_pattern_rate = 1.0000`
- `safe_refusal_rate = 0.0000`

说明 LoRA 已成功构造可控泄露模型。

### 2. ROME direct-only

- full private：
  - `target_exact_leak_rate = 0.0375`
  - `target_regex_leak_rate = 0.0375`
  - `sensitive_pattern_rate = 0.5375`
  - `safe_refusal_rate = 0.3875`
- public retain：
  - `exact_match_rate = 0.05`
  - `contains_match_rate = 0.10`

说明 direct-only 已显著降低泄露，但仍有残余泄露与敏感格式幻觉，同时 public facts 已明显受损。

### 3. PACE Round2

- full private：
  - `target_exact_leak_rate = 0.0000`
  - `target_regex_leak_rate = 0.0000`
  - `sensitive_pattern_rate = 0.0000`
  - `safe_refusal_rate = 1.0000`
- 各攻击类型（direct / paraphrase / completion / roleplay）均达到：
  - leak `0`
  - sensitive pattern `0`
  - refusal `1.0`
- public retain：
  - `exact_match_rate = 0.00`
  - `contains_match_rate = 0.00`

## 当前结论

- `PACE Round2` 在当前 synthetic privacy 设置下，已经把残余泄露与敏感格式输出压到 `0`，并把拒答率提升到 `100%`。
- 但其代价也非常明显：public knowledge 完全丢失。

## 下一步重点

- 当前不应继续重复 baseline 或 LoRA 注入实验。
- 下一步应围绕 **降低 collateral damage** 展开，重点分析：
  - 为什么 `PACE Round2` 对 public facts 产生全面拒答
  - 如何在保持 privacy suppression 的同时恢复 public retain
  - 是否需要更细的 request 选择、层选择或 edit budget 控制
