# Metric Audit Report

This ledger does not run GPU code. Missing values remain `missing`.

## Conflicts
- `ROME direct` `public_refusal` conflict: ledger canonical `0.2873` vs `method_claim_metrics.csv` `0.49206349206349204`. Final ledger keeps the current GPT-reviewed canonical values and records the conflict here.
- `PACE max2/person` `public_refusal` conflict: ledger canonical `0.8052` vs `method_claim_metrics.csv` `0.8511904761904762`. Final ledger keeps the current GPT-reviewed canonical values and records the conflict here.
- `CAPE-v0` `public_refusal` conflict: ledger canonical `0.9877` vs `method_claim_metrics.csv` `0.9896825396825397`. Final ledger keeps the current GPT-reviewed canonical values and records the conflict here.
- `CAPE-v1` `public_refusal` conflict: ledger canonical `0.6901` vs `method_claim_metrics.csv` `0.7507936507936508`. Final ledger keeps the current GPT-reviewed canonical values and records the conflict here.

## Notes
- Public wrapper rows with failed CUDA summaries are recorded as failed, not valid metrics.
- GPT-J rows are partial/stopped rows unless a real `summary.json` exists.
- Synthetic pending rows are intentionally kept as pending rather than filled with zero.
