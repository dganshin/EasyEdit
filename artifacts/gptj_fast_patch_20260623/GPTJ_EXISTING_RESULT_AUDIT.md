# GPT-J Existing Result Audit

- existing summaries found: `8`
- existing ok rows: `8`
- missing target rows: `0`

No GPU was used by this audit script. Missing values are written as `missing`, not zero.

## Current rows

| model | dataset | method | n_cases | reliability | generalization | locality | status | failure_reason | source_file | runtime_sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-J-6B | counterfact-200 | ROME | 200 | 0.995 | 0.82 | missing | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_counterfact/ROME/summary.json | 1311.41 |
| GPT-J-6B | counterfact-200 | FT | 200 | 1 | 0.725 | missing | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_counterfact/FT/summary.json | 99.0221 |
| GPT-J-6B | counterfact-200 | ROME_PACE_EDIT | 220 | 0.995455 | 0.745455 | missing | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_counterfact/ROME_PACE_EDIT/summary.json | 1510.82 |
| GPT-J-6B | counterfact-200 | ROME_CAPE_EDIT | 220 | 0.995455 | 0.745455 | missing | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_counterfact/ROME_CAPE_EDIT/summary.json | 1509.68 |
| GPT-J-6B | zsre-200 | ROME | 200 | 0.9975 | 0.945083 | 0.906337 | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_zsre/ROME/summary.json | 3359.2 |
| GPT-J-6B | zsre-200 | FT | 200 | 0.793012 | 0.808435 | 0.201496 | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_zsre/FT/summary.json | 2167.96 |
| GPT-J-6B | zsre-200 | ROME_PACE_EDIT | 216 | 0.996528 | 0.92662 | 0.9018 | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_zsre/ROME_PACE_EDIT/summary.json | 1814.41 |
| GPT-J-6B | zsre-200 | ROME_CAPE_EDIT | 216 | 0.996528 | 0.92662 | 0.9018 | ok | missing | artifacts/public_benchmarks_20260623_200/gptj_zsre/ROME_CAPE_EDIT/summary.json | 1814.08 |
