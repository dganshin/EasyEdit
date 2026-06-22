# CAPE-v0 Failure Diagnosis

## 1. 结论

CAPE-v0 不能写成有效改进。当前证据更支持一个负面诊断：仅靠 residual leakage request selection，且不限制总编辑人数/总请求量、直接使用 completion 类泄露 prompt 作为再编辑请求，会把 ROME/PACE 式拒答编辑推向更强的 over-refusal，导致 public retain 进一步崩塌。

这不是 MEMIT/ROME/EasyEdit 底层 bug 的直接证据；从 manifest 和请求组成看，更像 CAPE-v0 选择策略与实验协议的问题。

## 2. 关键指标

- CAPE-v0 full private: target_exact_leak_rate=0.0023, target_regex_leak_rate=0.0023, sensitive_pattern_rate=0.0190, safe_refusal_rate=0.9890
- CAPE-v0 public: contains_match_rate=0.0060, exact_match_rate=0.0000
- PACE max2/person full private: target_exact_leak_rate=0.0243, target_regex_leak_rate=0.0150, sensitive_pattern_rate=0.0740, safe_refusal_rate=0.9347
- PACE max2/person public: contains_match_rate=0.0984, exact_match_rate=0.0000

解释：CAPE-v0 的 private suppression 很强，但 public contains 只有 0.0060，低于 PACE max2/person 的 0.0984，因此不能声称获得更好的 privacy-utility trade-off。

## 3. 请求选择诊断

- CAPE selection report: candidates=2569, selected=60, selected_people=60, skipped_public_anchor=815, skipped_budget=1694
- CAPE-v0 round2 请求数: 60
- CAPE-v0 round2 涉及人数: 60
- CAPE-v0 round2 attack_type 分布: {'completion': 60}
- CAPE-v0 round2 failure_source 分布: {'target_exact_or_value_contains': 59, 'sensitive_pattern': 1}
- CAPE-v0 round2 与原始 ROME direct-only 人员重叠: 2/60
- CAPE-v0 round2 target_new 唯一值数量: 1

主要问题是 B=1 只限制了每人最多 1 条 re-edit，但没有限制总人数。结果不是“保守地补少量漏洞”，而是对 60 个 subject 各追加一次拒答编辑。

## 4. 与 PACE max2/person 的差异

- rome_direct_initial: requests=40, people=20, cases=40, attacks={'unknown': 40}, original_overlap=20
- pace_max2_round2: requests=198, people=100, cases=109, attacks={'direct': 151, 'paraphrase': 16, 'completion': 17, 'context': 9, 'roleplay': 5}, original_overlap=20
- pace_max2_combined: requests=238, people=100, cases=124, attacks={'unknown': 40, 'direct': 151, 'paraphrase': 16, 'completion': 17, 'context': 9, 'roleplay': 5}, original_overlap=20
- cape_v0_round2: requests=60, people=60, cases=60, attacks={'completion': 60}, original_overlap=2
- cape_v0_combined: requests=100, people=78, cases=98, attacks={'unknown': 40, 'completion': 60}, original_overlap=20

表面上 CAPE-v0 的 round2 请求数少于 PACE max2/person，但它更集中在 completion 类 prompt，并扩展到 60 个 subject。PACE max2/person 虽然请求更多，但请求类型以 direct 为主，且其 public general knowledge 保留明显高于 CAPE-v0。说明“请求少”本身不足以保证副作用小，请求类型、覆盖人数和目标文本同样关键。

## 5. Pipeline/路径核查

- manifest model_path: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- manifest method: `ROME`
- manifest hparams: `hparams/ROME/qwen2.5-7b.yaml`
- manifest request_count: `100`
- manifest command/argv: ``

未发现明显的错模型/错 checkpoint 证据。CAPE-v0 复用 merged leakage model，并把原始 ROME direct requests 与 CAPE round2 requests 合并后一次性编辑；这与 PACE 系列 pipeline 的比较口径一致。若要更严格核查，可在下一轮补充脚本级 manifest 字段，但当前失败不应优先归因于路径错误。

## 6. Public failure 形态

- refusal: 2489
- wrong_or_drift: 16
- success: 15

public failure 详细样例见 `cape_public_failure_cases.md`。如果大量 failure 被分类为 refusal，则说明 CAPE-v0 主要问题是 over-refusal；如果主要是 wrong_or_drift，则说明编辑造成事实漂移。当前两者都应在报告中诚实呈现，不应只看 private 指标。

## 7. 可检验假设

- H1: 总 subject 覆盖过大。证据：B=1 但 selected_people=60；下一步应加入 max_total_requests/max_total_people。
- H2: completion/context prompt 作为编辑请求会放大拒答泛化。证据：CAPE-v0 selected attack_type 高度集中在 completion；下一步用 canonical direct prompt 做 re-edit。
- H3: 统一 refusal target 诱导 person-question 级别拒答。证据：target_new 唯一值很少；下一步保留拒答目标但收缩 scope，或设计更局部化 target。
- H4: public anchor 只做过滤，不足以作为 locality 约束。证据：通过 tau=0.5 的 subject 仍出现 public collapse；下一步 selection score 需要显式惩罚 public failure risk。
- H5: residual mining 从 full eval 扩展了编辑范围。证据：CAPE selected 与原始 ROME direct 人员只有部分重叠；下一步先限制 original_edited_people_only。

## 8. 下一步建议

不要继续调 CAPE-v0 同款参数，也不要改 ROME/MEMIT/EasyEdit 底层。若还允许一轮 GPU 实验，建议只跑 CAPE-v1 最小修正版：

- scope = original_edited_people_only
- request_type = canonical_direct
- candidate_source = exact/value_contains leakage only
- max_total_requests = 20
- max_per_person = 1
- public_anchor_threshold = 0.7
- 不使用 completion/context 作为编辑请求

判定标准必须严格：CAPE-v1 只有在 private value contains 低于 ROME direct-only、public contains 高于 PACE max2/person、public refusal 低于 PACE max2/person 时，才能写成更合理折中。否则只能写成负面消融。

## 9. 产物

- `cape_selected_request_breakdown.csv`: CAPE-v0 选中请求逐条明细
- `cape_vs_pace_request_distribution.csv`: CAPE/PACE/ROME 请求分布对比
- `cape_public_failure_cases.md`: public retain 失败类型统计与样例