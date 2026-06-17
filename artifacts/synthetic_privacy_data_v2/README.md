# V2 Synthetic Privacy Dataset Canonical Copy

This directory is the canonical local copy for the archived v2 synthetic privacy benchmark.

Source artifact:

- `artifacts/run_20260615_v2_lora_mlp_only/`

Canonical dataset:

- `synthetic_privacy_dataset.json`
- `synthetic_privacy_cases.jsonl`
- `audit_summary.json`
- `lora_privacy_train.jsonl`
- `lora_privacy_train_dataset.json`

Scale:

- people: `100`
- private facts: `200`
- public facts: `840`
- flat cases: `1040`

Experiment scope:

- LoRA injection used the full 100-person dataset.
- ROME direct-only edited 20 people / 40 direct private cases.
- Full private leakage eval and public retain eval use the full v2 dataset.

This copy exists because several manifests and pipeline scripts reference `artifacts/synthetic_privacy_data_v2/`, while the recovered source files were archived under `artifacts/run_20260615_v2_lora_mlp_only/`.
