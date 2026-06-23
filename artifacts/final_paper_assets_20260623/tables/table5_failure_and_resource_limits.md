| Scope | Method | Status | Reason | Policy | Source artifact |
| --- | --- | --- | --- | --- | --- |
| Qwen synthetic privacy | KN | failed | OOM on 48GB GPU | record and do not rerun | artifacts/final_comparison_20260623_urgent/synthetic_extra_editors_failure_matrix.csv |
| Qwen synthetic privacy | IKE | failed | missing SentenceTransformer dependency | record and do not rerun | artifacts/final_comparison_20260623_urgent/synthetic_extra_editors_failure_matrix.csv |
| Qwen public counterfact | IKE | failed | missing SentenceTransformer dependency | record as resource/dependency limit | artifacts/final_comparison_20260623_complete/qwen_public_transfer_final.csv |
| Qwen public zsre | KN | failed | OOM on 48GB GPU | record as resource/dependency limit | artifacts/final_comparison_20260623_complete/qwen_public_transfer_final.csv |
| GPT-J public wrapper | ROME_PACE_EDIT / ROME_CAPE_EDIT | ok run, negative result | per-case audit confirms wrapper collapse, not path mixup | boundary analysis, no GPU rerun | artifacts/final_comparison_20260623_complete/gptj_per_case_audit.csv |
