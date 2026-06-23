# Metric Audit Report

This ledger does not run GPU code. Missing values remain `missing`.

## Conflicts
- No checked conflicts found.

## Notes
- Public wrapper rows with failed CUDA summaries are recorded as failed, not valid metrics.
- GPT-J rows are partial/stopped rows unless a real `summary.json` exists.
- Synthetic pending rows are intentionally kept as pending rather than filled with zero.
