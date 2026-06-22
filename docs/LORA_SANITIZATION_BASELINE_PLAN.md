# LoRA/SFT Sanitization Baseline Plan

## 1. Goal

构建一个参数微调式隐私净化 baseline，用于和 ROME、MEMIT、PACE、CAPE 以及 Prompt Refusal baseline 对照。该 baseline 不做单点模型编辑，而是通过 LoRA/SFT 学习：

- private queries -> refusal response
- public queries -> original public answer

## 2. Data

数据由 `scripts/build_v2_lora_sanitization_data.py` 生成：

- input dataset: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- output dir: `artifacts/data_v2_lora_sanitization/`
- train/dev split: subject-level split
- balance: private/public 默认按较小类对齐

## 3. Model

- base model: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- training target: LoRA adapter, not full fine-tuning
- initial scope: MLP-only or attention+MLP small rank ablation

## 4. Suggested Hyperparameters

| item | value |
| --- | --- |
| LoRA rank | 8 or 16 |
| target modules | start with `gate_proj up_proj down_proj`; optional attention modules later |
| max steps | 100-300 smoke range |
| batch size | 4-8 on 48GB, adjust by OOM |
| learning rate | start from `5e-4` or lower |
| gradient clipping | `max_grad_norm=1.0` |
| eval cadence | save at end and run full private/public eval |

## 5. Expected VRAM and Time

- 24GB may be enough for low-rank small-batch training with gradient checkpointing.
- 48GB is safer for faster batch size and reduced OOM risk.
- Expected pilot runtime: 1-3 hours depending batch size and steps.

## 6. Evaluation

Use the same v2 metrics:

- Private Value Contains
- Private Regex
- Sensitive Pattern
- Private Safe Refusal
- Public Contains
- Public Refusal
- over-refusal by public type

## 7. Success Criteria

Minimum useful outcome:

- Private Value Contains lower than merged leakage model.
- Public Contains not collapsed to the PACE/CAPE-v0 extreme.
- Public Refusal not close to 1.0.

Interpretation rule:

- If private leakage decreases only because every prompt is refused, report it as over-refusal, not successful sanitization.
- If public retain is high but private leakage remains close to ROME/MEMIT weak points, report it as limited privacy protection.

## 8. Do Not Run Yet

This plan only prepares the baseline. Do not start LoRA/SFT training until the generated data is reviewed and the user confirms GPU usage.
