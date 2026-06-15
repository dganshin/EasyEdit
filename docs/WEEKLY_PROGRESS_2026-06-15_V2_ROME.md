# EasyEdit / v2 ROME 进展简报（2026-06-15）

## 本轮完成内容

- 完成 `v2 synthetic privacy benchmark` 上的 `MLP-only LoRA -> merge` 复训与评测。
- 确认 `v2 merged model` 已成功构造成高泄露、同时保留 public knowledge 的待编辑模型。
- 在此基础上完成 `ROME direct-only`：
  - 构造 `40` 条 direct-only edit requests
  - 覆盖 `20` 个虚拟人物、每人 `2` 条 private facts
  - 获得 subset / full private / public 三套结果

## 当前主线

```text
v2 synthetic benchmark
-> rebalanced LoRA privacy injection
-> merged v2 privacy leakage model
-> ROME direct-only
```

## 关键结果

### 1. v2 merged privacy leakage model

- private：
  - `target_exact_leak_rate = 0.9387`
  - `target_regex_leak_rate = 0.6650`
  - `sensitive_pattern_rate = 0.9927`
  - `safe_refusal_rate = 0.0000`
- public：
  - `contains_match_rate = 0.9766`
  - `same_subject_public = 0.9833`
  - `same_relation_other_subject = 0.9675`
  - `general_knowledge = 1.0000`

说明：

- v2 merged model 已经形成强泄露；
- 同时 public retain 仍然很高；
- 因此它是一个合格的 v2 待编辑泄露模型。

### 2. ROME direct-only：edited subset

- subset private：
  - `target_exact_leak_rate = 0.2667`
  - `target_regex_leak_rate = 0.2433`
  - `sensitive_pattern_rate = 0.5767`
  - `safe_refusal_rate = 0.8950`

说明：

- 对被直接编辑到的 private cases，ROME 已显著降低泄露；
- 拒答率快速升高到接近 `0.9`；
- direct-only 在局部上有效。

### 3. ROME direct-only：full private

- full private：
  - `target_exact_leak_rate = 0.5787`
  - `target_regex_leak_rate = 0.4767`
  - `sensitive_pattern_rate = 0.8563`
  - `safe_refusal_rate = 0.5973`

与 pre-edit merged 对比：

- exact：`0.9387 -> 0.5787`
- regex：`0.6650 -> 0.4767`
- sensitive：`0.9927 -> 0.8563`
- refusal：`0.0000 -> 0.5973`

说明：

- ROME direct-only 在全量 private 上仍然有效，但 suppression 明显弱于 edited subset；
- 当前结果更像“部分成功抑制”，而不是“全量清除泄露”。

### 4. ROME direct-only：public retain

- public：
  - `contains_match_rate = 0.5591`
  - `same_subject_public = 0.5475`
  - `same_relation_other_subject = 0.5367`
  - `general_knowledge = 0.9000`

与 pre-edit merged 对比：

- overall contains：`0.9766 -> 0.5591`
- same-subject：`0.9833 -> 0.5475`
- same-relation：`0.9675 -> 0.5367`

说明：

- public retain 明显下降；
- 但尚未崩到 `0`；
- 当前呈现典型的 privacy-utility trade-off。

## 当前最准确结论

> 在 v2 synthetic privacy benchmark 上，rebalanced LoRA 成功构造出高泄露、且 public retain 高的 merged leakage model；ROME direct-only 能显著降低 edited subset 与 full private 上的 target leakage，并显著提升 refusal rate，但无法完全消除全量 private leakage，同时会对 same-subject 和 same-relation public facts 造成明显 collateral damage。

## 当前最值得讲的 3 点

1. `v2 merged model` 已经成立，不再是 toy 级“只会吐敏感格式”的假泄露模型。
2. `ROME direct-only` 在 v2 上依然有效，但只做到“部分 suppress”，没有达到 v1/PACE 那种近乎清零的程度。
3. 当前真正的问题已经从“能不能 suppress leakage”转成：

```text
如何在更大规模 v2 benchmark 上，
在降低 full private leakage 的同时，
尽量减少对 public retain 的损伤
```

## 下一步建议

- 不再重跑 baseline 或 LoRA 注入主线。
- 下一步优先做：
  - `conservative PACE` on v2
  - failure-based request filtering
  - 比较 `target_only / max_per_case / max_per_person`
- 当前不建议立刻扩到 MEMIT、真实 PII benchmark 或新模型族。
