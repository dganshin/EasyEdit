# Paper Final Result Sections 20260623

Last updated: 2026-06-23
Final result status: frozen
No further GPU expansion unless explicitly approved

## 1. Synthetic Privacy Main Results

Qwen synthetic privacy is the main experimental setting for the paper claim. The merged leakage model preserves public facts while leaking private values, with Private Value Contains = 0.9387 and Public Contains = 0.9766. ROME reduces Private Value Contains to 0.5787 while retaining Public Contains = 0.5591, whereas MEMIT keeps stronger public utility (0.8472) but leaves more private leakage (0.8140). FT suppresses the measured private leakage to 0.0000, but its Public Contains falls to 0.0040, which indicates a destructive sanitization behavior rather than a useful privacy-utility trade-off.

PACE and CAPE provide stronger privacy suppression than ROME, with Private Value Contains = 0.0243 and 0.0443 respectively. However, their Public Contains values are only 0.0984 and 0.1119, showing the public-collapse / over-refusal side effect that motivates CAPE-Anchor. Therefore, the main result should not be written as “privacy solved”; it should be written as a structured privacy-utility trade-off analysis.

## 2. CAPE-Anchor Ablation

CAPE-Anchor changes the operating point of closed-loop editing. PACE-Lite B20-K0 obtains Public Contains = 0.4210 with Private Value Contains = 0.3323. CAPE-Anchor K1 further raises Public Contains to 0.6008, with Private Value Contains = 0.4603. CAPE-Anchor K2 reaches Public Contains = 0.6833, but Private Value Contains also rises to 0.6357. These results support Claim A only in the limited sense: CAPE-Anchor forms a more useful privacy-utility trade-off than naive PACE/CAPE, but it is not the lowest-leakage method and not a lossless sanitization method.

## 3. Qwen Public Transfer

The public benchmark is a factual-editing transfer check, not a PII sanitization proof. On Qwen2.5-7B, ROME and FT are strong public-editing baselines on CounterFact and zsRE. The ROME-based PACE/CAPE wrappers are executable on both datasets, but their transfer performance is moderate: CounterFact reliability is 0.5179 and zsRE reliability is 0.3117. This supports only a conservative statement that the closed-loop request-selection idea can be instantiated on public factual-editing tasks, while not outperforming strong ROME/FT baselines.

## 4. GPT-J Second-Model Boundary Check

为检查公开迁移实验是否完全依赖 Qwen2.5-7B，本文在 GPT-J-6B 上进行了第二模型公开事实编辑验证。结果显示，GPT-J-6B 上 ROME 与 FT baseline 均能正常运行，在 CounterFact 与 zsRE 上获得较高 rewrite 成功率。然而，将未重新调参的 ROME-based PACE/CAPE wrapper 直接迁移到 GPT-J-6B 时，wrapper 出现明显塌缩。per-case 审计进一步排除了路径混用和汇总脚本误读的可能。该结果说明，闭环请求扩展策略的跨模型迁移依赖底层编辑器超参数、请求集合规模与局部性约束，后续需要模型特定校准或 retain-aware objective。

## 5. Failure And Resource Limitation

The failure matrix should be reported explicitly rather than hidden. KN on Qwen synthetic privacy failed due to GPU memory pressure on a 48GB instance. IKE failed because the expected SentenceTransformer dependency `./hugging_cache/all-MiniLM-L6-v2` was missing. Qwen public IKE and zsRE KN also failed for dependency or resource reasons. These failures are resource/dependency limits under the current project deadline, not evidence that the main synthetic privacy result is invalid.

## 6. Final Claim Decision

The final claim should use Claim A with conservative wording: CAPE-Anchor provides a limited effective improvement by moving the privacy-utility operating point on Qwen synthetic privacy. Public Qwen experiments are transfer checks, and GPT-J experiments are boundary evidence. The paper must not claim cross-model success for GPT-J, must not present public benchmarks as PII sanitization proof, and must not claim lossless privacy cleaning.

## Evidence Mapping

- Main claim evidence: `artifacts/final_paper_assets_20260623/tables/table1_synthetic_privacy_main.csv`
- CAPE-Anchor evidence: `artifacts/final_paper_assets_20260623/tables/table2_cape_anchor_ablation.csv`
- Qwen public transfer evidence: `artifacts/final_paper_assets_20260623/tables/table3_qwen_public_transfer.csv`
- GPT-J boundary evidence: `artifacts/final_paper_assets_20260623/tables/table4_gptj_boundary_check.csv`
- Failure/resource evidence: `artifacts/final_paper_assets_20260623/tables/table5_failure_and_resource_limits.csv`
