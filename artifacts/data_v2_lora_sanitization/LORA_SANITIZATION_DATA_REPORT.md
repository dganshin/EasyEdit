# LoRA/SFT Sanitization Data Report

## Construction

- private queries -> `I cannot provide private information.`
- public queries -> 原始 public fact value
- 默认做 private/public balanced sampling，避免模型只学习拒答。
- 本脚本只生成数据，不启动 LoRA/SFT 训练。

## Data Statistics

- dataset: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- output_dir: `artifacts\data_v2_lora_sanitization`
- train records: `4629`
- dev records: `411`
- total records: `5040`
- balance_mode: `balanced_to_2520_per_class`

## Split Policy

训练集和开发集按 subject/person 划分，降低同一人物 prompt 泄漏到不同 split 的风险。

## Next Step

等待确认后，再在 AutoDL 上用 LoRA/SFT baseline 训练脚本读取 `train.jsonl` 和 `dev.jsonl`。
