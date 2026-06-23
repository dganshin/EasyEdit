# Prompt Refusal Baseline Report

## Status

- dry_run: `False`
- dataset: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- model_path: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- run_name: `v2_prompt_refusal`

## Protocol

- 不修改模型参数。
- 对 private/public prompt 统一添加隐私拒答 guard prefix。
- 生成后复用现有 `evaluate_privacy_leakage.py` 与 `evaluate_public_retain.py`。
- 该 baseline 用作非参数编辑对照，不能解释为模型内部隐私知识已被清除。

## Dataset Check

- private generation jobs: `3000`
- public generation jobs: `2520`

## Metrics

| metric | value |
| --- | ---: |
| private_value_contains | 0.9490 |
| private_regex | 0.7630 |
| sensitive_pattern | 0.9947 |
| private_safe_refusal | 0.0000 |
| public_contains | 0.9583 |
| public_refusal | 0.0000 |
