# COURSE PAPER REWRITE LOG

## 1. Read Files

- `课程论文_v2.docx`: original draft, backed up before rewrite.
- `课程论文撰写模板 (研究类).docx`: read-only course paper template for structure reference.
- `artifacts/analysis_v2_audit_20260622/`: metric audit, method comparison, over-refusal, attack-type and trade-off outputs.
- `artifacts/run_20260622_v2_memit_direct/`: MEMIT direct-only result artifacts.
- `artifacts/run_20260622_v2_cape_b1_tau05/`: CAPE-v0 request-selection report.

## 2. Updated Sections

- Rewritten abstract, keywords, introduction, problem definition, method, experiments, software usage and conclusion.
- Updated stale statements about missing MEMIT; MEMIT direct-only is now included as completed baseline.
- Unified metric names: `Private Value Contains`, `PII-format Regex`, `Sensitive Pattern`, `Public Contains`, and `Public Refusal`.
- Unified PACE naming as `Privacy-Aware Closed-loop Editing`.
- Added CAPE-v0 as follow-up side-effect-aware request selection strategy.

## 3. Added Experimental Results

- Added main ROME / MEMIT / PACE comparison table.
- Added public over-refusal analysis.
- Added privacy-utility trade-off section and inserted `privacy_utility_tradeoff.png`.
- Added CAPE-v0 request-selection status.
- CAPE-v0 current selection: candidates=2569, selected=60, public-anchor skipped=815, budget skipped=1694.

## 4. Pending Server Results

- CAPE-v0 model editing and full private/public eval are not yet written as completed results.
- After server returns CAPE eval JSON, update Chapter 4 tables, trade-off plot and conclusion.

## 5. Figures Requiring Manual Check

- Existing `privacy_utility_tradeoff.png` has been inserted into the Word document.
- Overall framework figure and CAPE-v0 mechanism figure are described in text but not yet drawn as independent figures.
- LibreOffice/soffice was not found in the current Windows environment, so automated render-to-PNG visual QA could not be completed here. Please open the final DOCX in Word/WPS for final visual layout inspection.

## 6. References to Verify

- Reference list uses known model editing, privacy leakage, LoRA, EasyEdit, DEPN, machine unlearning and differential privacy literature.
- DOI fields are intentionally omitted to avoid fabricating identifiers; final submission can add DOI after manual verification.

## 7. Self Check

- Template file was not modified.
- No CAPE model-editing result was fabricated.
- `Private Value Contains` is not described as strict equality.
- `Public Contains` is not described as strict factual accuracy.
- MEMIT direct-only is included.
- PACE is described as a wrapper/strategy, not a bottom-layer editing algorithm.
