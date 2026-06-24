# Public PACE/CAPE Selection Report

PACE-Edit 在公开知识编辑基准中表示 residual-failure closed-loop editing；CAPE-Edit 在 residual failure 基础上加入 locality risk 和 subject/relation budget。
CounterFact/zsRE 上的 residual failure 对应 rewrite/rephrase 编辑失败；locality risk 对应公开知识编辑 benchmark 中的 locality 下降。

- dataset: `counterfact`
- model: `gpt-j-6B`
- base_method: `ROME`
- total_cases: `200`
- selection_split_size: `120`
- heldout_size: `80`
- candidate_count: `20`
- pace_selected_count: `20`
- cape_selected_count: `20`
- round1_count: `200`
- pace_union_count: `220`
- cape_union_count: `220`
- rewrite_fail_count: `0`
- rephrase_fail_count: `20`
- locality_available_count: `0`
- locality_failed_count: `0`
- skipped_by_locality_risk: `0`
- skipped_by_subject_or_relation_budget: `0`

## Split Note

Diagnostic-all uses the original full set to inspect closed-loop repair behavior. Held-out split files are emitted to avoid presenting same-set feedback as strict external generalization.

| strategy | case_id | subject | rewrite | rephrase | locality |
| --- | --- | --- | ---: | ---: | ---: |
| PACE_EDIT | counterfact_00004 | Avitohol Point | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00006 | Bully Beatdown | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00021 | Taxidermia | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00022 | Stuart Parkin | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00027 | Johann von Rist | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00029 | Henrik Lundqvist | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00030 | Brabant Island | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00042 | Fritz Schramma | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00051 | Econoline Crush | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00067 | Selland Arena | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00070 | ARM Holdings | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00079 | Pyongyang | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00083 | presbyter | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00115 | Jean Crotti | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00121 | Chu Lai Base Area | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00122 | Marcus Licinius Crassus | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00136 | Jean Bruller | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00173 | Marcel Mouloudji | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00189 | Bo Lundgren | 1.0000 | 0.0000 |  |
| PACE_EDIT | counterfact_00199 | Saskia Mulder | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00004 | Avitohol Point | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00006 | Bully Beatdown | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00021 | Taxidermia | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00022 | Stuart Parkin | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00027 | Johann von Rist | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00029 | Henrik Lundqvist | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00030 | Brabant Island | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00042 | Fritz Schramma | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00051 | Econoline Crush | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00067 | Selland Arena | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00070 | ARM Holdings | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00079 | Pyongyang | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00083 | presbyter | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00115 | Jean Crotti | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00121 | Chu Lai Base Area | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00122 | Marcus Licinius Crassus | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00136 | Jean Bruller | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00173 | Marcel Mouloudji | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00189 | Bo Lundgren | 1.0000 | 0.0000 |  |
| CAPE_EDIT | counterfact_00199 | Saskia Mulder | 1.0000 | 0.0000 |  |
