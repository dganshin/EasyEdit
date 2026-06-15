# EasyEdit / Conservative PACE 进展简报（2026-06-15）

## 本轮完成内容

- 补回 `merged privacy leakage model` 的 pre-edit public retain 对照：
  - 结果目录：
    - `artifacts/run_20260615_merged_public_retain/`
- 在已有 `ROME direct-only` 与原始 `PACE Round2` 结果基础上，新增三组保守版 `PACE`：
  - `target_only`
  - `max1_per_case`
  - `max2_per_person`
- 三组结果文件已分别回收到：
  - `artifacts/run_20260615_pace_target_only/`
  - `artifacts/run_20260615_pace_max1_per_case/`
  - `artifacts/run_20260615_pace_max2_per_person/`

## 关键结果

### 1. merged model 的 pre-edit public retain

- `public_exact_acc = 0.25`
- `public_contains_acc = 1.00`

说明 merged model 在 edit 前并没有出现明显 public knowledge 崩坏。  
因此后续 public retain 下降，主要应归因于 `ROME / PACE` refusal editing，而不是 LoRA merge 本身。

### 2. `PACE target_only`

- full private：
  - `target_exact_leak_rate = 0.0000`
  - `target_regex_leak_rate = 0.0000`
  - `sensitive_pattern_rate = 0.3500`
  - `safe_refusal_rate = 0.6000`
- public retain：
  - `exact_match_rate = 0.00`
  - `contains_match_rate = 0.05`

说明只修 target leak failure 时，目标真值泄露可以压到 `0`，但敏感格式输出仍较高，public retain 也仍然很低。

### 3. `PACE max1_per_case`

- full private：
  - `target_exact_leak_rate = 0.0000`
  - `target_regex_leak_rate = 0.0000`
  - `sensitive_pattern_rate = 0.0500`
  - `safe_refusal_rate = 0.8750`
- public retain：
  - `exact_match_rate = 0.00`
  - `contains_match_rate = 0.00`

说明每个 case 最多保留 1 条 Round2 request 后，private 指标很强，但 public retain 仍然完全丢失。

### 4. `PACE max2_per_person`

- full private：
  - `target_exact_leak_rate = 0.0000`
  - `target_regex_leak_rate = 0.0000`
  - `sensitive_pattern_rate = 0.0750`
  - `safe_refusal_rate = 0.9125`
- public retain：
  - `exact_match_rate = 0.05`
  - `contains_match_rate = 0.05`

说明按 person 限制 request 数量后，private leak 仍保持 `0`，sensitive pattern 也显著下降，但 public retain 只恢复到 `0.05`，改善仍然有限。

## 与前一阶段对比

| 阶段 | private exact/regex | sensitive | refusal | public contains |
| --- | --- | --- | --- | --- |
| merged pre-edit | `0.9875 / 0.9375` | `1.0000` | `0.0000` | `1.00` |
| ROME direct-only | `0.0375 / 0.0375` | `0.5375` | `0.3875` | `0.10` |
| 原始 PACE Round2 | `0 / 0` | `0.0000` | `1.0000` | `0.00` |
| target_only | `0 / 0` | `0.3500` | `0.6000` | `0.05` |
| max1_per_case | `0 / 0` | `0.0500` | `0.8750` | `0.00` |
| max2_per_person | `0 / 0` | `0.0750` | `0.9125` | `0.05` |

## 当前结论

- 当前已经可以确认：public retain 的主要损伤来自后续 refusal editing，而不是 merged model 本身。
- 保守版 PACE 的确能在保持 `target leak = 0` 的前提下，改变 `sensitive pattern / refusal / public retain` 的平衡。
- 但截至当前，三组保守版都还没有把 public retain 恢复到一个令人满意的水平。
- `max2_per_person` 是目前三组里相对最值得继续跟进的一组，但它仍然远低于 pre-edit public retain。

## 下一步重点

- 当前不建议回到 baseline、LoRA、direct-only 重跑。
- 下一步应继续围绕 **privacy-utility trade-off** 做更细的 request 约束分析，例如：
  - `max1_per_person`
  - `target_only + attack_type` 过滤
  - 更保守或更自然的 refusal template
- 同时应把当前阶段的阶段说明、指标说明、runlog 与对比结论补齐，避免后续讨论继续混淆 `target leak`、`sensitive pattern`、`safe refusal` 与 `public retain`。
