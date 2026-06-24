# Public PACE/CAPE Selection Report

PACE-Edit 在公开知识编辑基准中表示 residual-failure closed-loop editing；CAPE-Edit 在 residual failure 基础上加入 locality risk 和 subject/relation budget。
CounterFact/zsRE 上的 residual failure 对应 rewrite/rephrase 编辑失败；locality risk 对应公开知识编辑 benchmark 中的 locality 下降。

- dataset: `zsre`
- model: `gpt-j-6B`
- base_method: `ROME`
- total_cases: `200`
- selection_split_size: `120`
- heldout_size: `80`
- candidate_count: `16`
- pace_selected_count: `16`
- cape_selected_count: `16`
- round1_count: `200`
- pace_union_count: `216`
- cape_union_count: `216`
- rewrite_fail_count: `0`
- rephrase_fail_count: `16`
- locality_available_count: `0`
- locality_failed_count: `0`
- skipped_by_locality_risk: `0`
- skipped_by_subject_or_relation_budget: `0`

## Split Note

Diagnostic-all uses the original full set to inspect closed-loop repair behavior. Held-out split files are emitted to avoid presenting same-set feedback as strict external generalization.

| strategy | case_id | subject | rewrite | rephrase | locality |
| --- | --- | --- | ---: | ---: | ---: |
| PACE_EDIT | zsre_00027 | Karol Križan | 1.0000 | 0.0000 |  |
| PACE_EDIT | zsre_00116 | Jacob Milgrom | 1.0000 | 0.0000 |  |
| PACE_EDIT | zsre_00187 | Philip Cross | 1.0000 | 0.0000 |  |
| PACE_EDIT | zsre_00171 | Detroit City FC | 1.0000 | 0.3333 |  |
| PACE_EDIT | zsre_00006 | Markus Marquardt | 1.0000 | 0.5000 |  |
| PACE_EDIT | zsre_00098 | Triangulum Galaxy | 1.0000 | 0.5000 |  |
| PACE_EDIT | zsre_00013 | Hartmut Losch | 1.0000 | 0.6667 |  |
| PACE_EDIT | zsre_00056 | Matinee Ladies | 1.0000 | 0.6667 |  |
| PACE_EDIT | zsre_00067 | Stop Violence | 1.0000 | 0.6667 |  |
| PACE_EDIT | zsre_00190 | Barilius shacra | 1.0000 | 0.6667 |  |
| PACE_EDIT | zsre_00157 | KM-SAM | 1.0000 | 0.7500 |  |
| PACE_EDIT | zsre_00161 | Hyperion Hotel | 1.0000 | 0.7500 |  |
| PACE_EDIT | zsre_00083 | FH-2000 | 1.0000 | 0.8000 |  |
| PACE_EDIT | zsre_00086 | Elizabeth Tailboys, 4th Baroness Tailboys of Kyme | 1.0000 | 0.8000 |  |
| PACE_EDIT | zsre_00036 | Sheikh Jamal Dhanmondi Club | 1.0000 | 0.8333 |  |
| PACE_EDIT | zsre_00184 | Joseph A. Sullivan | 1.0000 | 0.8333 |  |
| CAPE_EDIT | zsre_00027 | Karol Križan | 1.0000 | 0.0000 |  |
| CAPE_EDIT | zsre_00116 | Jacob Milgrom | 1.0000 | 0.0000 |  |
| CAPE_EDIT | zsre_00187 | Philip Cross | 1.0000 | 0.0000 |  |
| CAPE_EDIT | zsre_00171 | Detroit City FC | 1.0000 | 0.3333 |  |
| CAPE_EDIT | zsre_00006 | Markus Marquardt | 1.0000 | 0.5000 |  |
| CAPE_EDIT | zsre_00098 | Triangulum Galaxy | 1.0000 | 0.5000 |  |
| CAPE_EDIT | zsre_00013 | Hartmut Losch | 1.0000 | 0.6667 |  |
| CAPE_EDIT | zsre_00056 | Matinee Ladies | 1.0000 | 0.6667 |  |
| CAPE_EDIT | zsre_00067 | Stop Violence | 1.0000 | 0.6667 |  |
| CAPE_EDIT | zsre_00190 | Barilius shacra | 1.0000 | 0.6667 |  |
| CAPE_EDIT | zsre_00157 | KM-SAM | 1.0000 | 0.7500 |  |
| CAPE_EDIT | zsre_00161 | Hyperion Hotel | 1.0000 | 0.7500 |  |
| CAPE_EDIT | zsre_00083 | FH-2000 | 1.0000 | 0.8000 |  |
| CAPE_EDIT | zsre_00086 | Elizabeth Tailboys, 4th Baroness Tailboys of Kyme | 1.0000 | 0.8000 |  |
| CAPE_EDIT | zsre_00036 | Sheikh Jamal Dhanmondi Club | 1.0000 | 0.8333 |  |
| CAPE_EDIT | zsre_00184 | Joseph A. Sullivan | 1.0000 | 0.8333 |  |
