# GPT-J Existing Result Audit

- existing summaries found: `2`
- existing ok rows: `2`
- missing target rows: `8`

No GPU was used by this audit script. Missing values are written as `missing`, not zero.

## Current rows

| model | dataset | method | n_cases | reliability | generalization | locality | status | failure_reason | source_file | runtime_sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-J-6B | counterfact-200 | ROME | 200 | 0.995 | 0.82 | missing | ok | missing | artifacts\public_benchmarks_20260623_200\gptj_counterfact\ROME\summary.json | 1311.41 |
| GPT-J-6B | counterfact-200 | FT | 200 | 1 | 0.725 | missing | ok | missing | artifacts\public_benchmarks_20260623_200\gptj_counterfact\FT\summary.json | 99.0221 |
| GPT-J-6B | counterfact-200 | ROME_PACE_EDIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | counterfact-200 | ROME_CAPE_EDIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | counterfact-200 | MEMIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | zsre-200 | ROME | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | zsre-200 | FT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | zsre-200 | ROME_PACE_EDIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | zsre-200 | ROME_CAPE_EDIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
| GPT-J-6B | zsre-200 | MEMIT | missing | missing | missing | missing | missing_artifact | no summary.json found | gptj_fast_patch_expected_matrix | missing |
