# V2 Audit and Locality Summary

## 1. Why this audit

本审计用于核对 v2 benchmark 的真实规模、LoRA/ROME/PACE 是否共享同一条实验链路, 以及 public locality damage 的汇报口径是否可追溯。此前口头记录中出现过 50 人口径, 但仓库内 v2 artifact 显示实际生成和评测口径是 100 人, 因此需要单独固化账本, 避免后续 MEMIT baseline 使用错误数据范围。

## 2. Benchmark scale

- people count: `100`
- private facts: `200`
- public facts: `840`
- flat cases: `1040`
- train records: `3240`
- train people: `100`
- train private records: `1600`
- train public records: `1640`
- train/eval split or selected subset: 没有发现独立 train/eval split 文件。LoRA 注入使用 100 人全量 synthetic dataset 构造训练记录；ROME direct-only 只编辑 20 人 40 条 private cases；后续 full private/public eval 覆盖 100 人全量 v2 dataset。
- edited people / edited cases: ROME direct-only 为 20 people / 40 cases；PACE target_only 合并后 99 people / 177 cases；PACE max1_per_case 合并后 100 people / 195 cases；PACE max2_per_person 合并后 100 people / 124 cases。

`flat_cases` 在当前数据里表示一个 fact-like case。100 人每人包含 2 条 private facts、4 条 same-subject public facts、4 条 same-relation public facts, 再加 40 条 general_knowledge public cases, 所以总数为 `100 * (2 + 4 + 4) + 40 = 1040`。因此 "50 人 v2" 与当前 artifact 不一致；可信口径应写为 "当前已归档 v2 run 使用 100 人 synthetic benchmark, ROME direct-only 只编辑其中前 20 人的 private facts"。

## 3. Pipeline consistency check

| run | base model | dataset path | request path | output path | eval path | traceable |
| --- | --- | --- | --- | --- | --- | --- |
| v2_lora_mlp_only | `/root/autodl-tmp/models/Qwen2.5-7B` | `artifacts/run_20260615_v2_lora_mlp_only/synthetic_privacy_dataset.json` | `null` | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | `artifacts/run_20260615_v2_lora_mlp_only/privacy_leakage_eval_merged_v2.json; artifacts/run_20260615_v2_lora_mlp_only/public_retain_eval_merged_v2.json` | yes |
| v2_rome_direct | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json` | `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json` | `/root/autodl-tmp/outputs/easyedit/v2_rome_direct` | `artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json; artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json` | yes |
| v2_pace_target_only | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json` | `artifacts/run_20260615_v2_pace_target_only/v2_pace_target_only_requests.json` | `/root/autodl-tmp/outputs/easyedit/v2_pace_target_only` | `artifacts/run_20260615_v2_pace_target_only/privacy_leakage_eval_v2_pace_target_only_full.json; artifacts/run_20260615_v2_pace_target_only/public_retain_eval_v2_pace_target_only.json` | yes |
| v2_pace_max1_per_case | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json` | `artifacts/run_20260615_v2_pace_max1_per_case/v2_pace_max1_per_case_requests.json` | `/root/autodl-tmp/outputs/easyedit/v2_pace_max1_per_case` | `artifacts/run_20260615_v2_pace_max1_per_case/privacy_leakage_eval_v2_pace_max1_per_case_full.json; artifacts/run_20260615_v2_pace_max1_per_case/public_retain_eval_v2_pace_max1_per_case.json` | yes |
| v2_pace_max2_per_person | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json` | `artifacts/run_20260615_v2_pace_max2_per_person/v2_pace_max2_per_person_requests.json` | `/root/autodl-tmp/outputs/easyedit/v2_pace_max2_per_person` | `artifacts/run_20260615_v2_pace_max2_per_person/privacy_leakage_eval_v2_pace_max2_per_person_full.json; artifacts/run_20260615_v2_pace_max2_per_person/public_retain_eval_v2_pace_max2_per_person.json` | yes |


    审计结论: 现有 v2 ROME/PACE manifests 都指向同一个 merged leakage model `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`, 且 dataset path 都写为 `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`。该 canonical dataset 目录已在 2026-06-17 从 `artifacts/run_20260615_v2_lora_mlp_only/` 恢复, 后续脚本可直接使用该路径。

## 4. Metric summary

| method | run name | private exact | private regex | sensitive pattern | refusal | public overall contains | same_subject_public | same_relation_other_subject | general_knowledge | Round2 requests | note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| merged_leakage_model | v2_lora_mlp_only | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 | 0.9833 | 0.9675 | 1.0000 | null | pre-edit merged leakage model |
| ROME direct-only | v2_rome_direct | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 | 0.5475 | 0.5367 | 0.9000 | 0 | 40 direct requests on 20 people; full eval on v2 dataset |
| PACE target_only | v2_pace_target_only | 0.0000 | 0.0000 | 0.0167 | 0.9930 | 0.0032 | 0.0025 | 0.0017 | 0.0250 | 1736 | target leak failures only |
| PACE max1_per_case | v2_pace_max1_per_case | 0.0003 | 0.0003 | 0.0200 | 0.9870 | 0.0099 | 0.0100 | 0.0067 | 0.0417 | 192 | at most one Round2 request per case |
| PACE max2_per_person | v2_pace_max2_per_person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 | 0.0975 | 0.0675 | 0.4167 | 198 | at most two Round2 requests per person |

## 5. Current trustworthy conclusion

可靠结论:

- 当前 v2 merged leakage model 是 100 人 synthetic benchmark 上训练和评测得到的, private leakage 高且 public retain 高。
- ROME direct-only 与三组 PACE 都基于同一个 v2 merged leakage model。
- ROME direct-only 只编辑 20 人 40 条 private cases, 但 full private/public eval 覆盖全量 100 人 v2 dataset。
- PACE target_only 和 max1_per_case 基本能把 private exact/regex leak 压到接近 0, 但 public overall contains 掉到约 0.0032/0.0099。
- PACE max2_per_person 保留了更多 public, 但 public overall contains 仍只有 0.0984, 且 private exact/regex 不再为 0。

还不能说:

- 不能说方法已经解决真实预训练 PII 删除。
- 不能说 PACE 在 utility 上成功, 因为 same_subject_public 和 same_relation_other_subject 仍严重受损。
- 不能说当前现象只属于 ROME, 因为 MEMIT baseline 尚未跑出可比结果。

该结果可以支撑简历/汇报中的项目表述, 但应使用诚实口径: "在 synthetic benchmark 上验证模型编辑可显著抑制目标隐私泄露, 同时发现并量化 public/locality collateral damage"。

## 6. Recommended next step

    建议下一步可以准备 MEMIT baseline。路径口径已修复, 但在开 GPU 前仍应在 AutoDL 上跑 preflight 确认服务器模型目录存在:

- MEMIT baseline 应使用同一个 merged model、同一个 v2 dataset、同一套 public/private eval。
- 输出目录建议新建 `/root/autodl-tmp/outputs/easyedit/v2_memit_direct` 和 `artifacts/run_YYYYMMDD_v2_memit_direct/`, 不覆盖任何 ROME/PACE 结果。
- 预计输入包括 merged model、`hparams/MEMIT/qwen2.5-7b.yaml`、v2 direct request JSON 和 v2 dataset；预计输出包括 edit metrics、full private eval、public retain eval、summary JSON 和 runlog。
