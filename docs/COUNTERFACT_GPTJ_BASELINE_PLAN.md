# CounterFact GPT-J Small Subset Baseline Plan

## 1. Purpose

CounterFact small subset is used as a public knowledge editing sanity check, not as a PII privacy experiment. It answers whether the current EasyEdit setup can reproduce a standard public factual editing protocol on a mature model-method pair.

## 2. Data Source

- EasyEdit loader: `easyeditor/dataset/counterfact.py`
- README notes: `CounterFactDataset` expects the dataset under `data`
- Suggested subset size: 100 or 200 records

Do not download full data until the subset path and script are confirmed.

## 3. Model

- preferred model: GPT-J-6B
- expected HF/source name: `EleutherAI/gpt-j-6b`
- local server target path: `/root/autodl-tmp/models/gpt-j-6B` or `/root/autodl-tmp/models/GPT-J-6B`
- current status: not confirmed present locally

## 4. Methods

Start with:

1. ROME
2. MEMIT if stats/data dependencies are manageable
3. IKE or FT only after ROME smoke passes

Relevant hparams exist:

- `hparams/ROME/gpt-j-6B.yaml`
- `hparams/MEMIT/gpt-j-6B.yaml`
- `hparams/IKE/gpt-j-6B.yaml`
- `hparams/FT/gpt-j-6B.yaml`

## 5. Metrics

Use standard public editing metrics:

- reliability / rewrite success
- generalization / rephrase success
- locality / unrelated facts retained
- optional fluency if runtime allows

Relationship to current paper:

- CounterFact does not test PII privacy.
- It supports the claim that the implementation is grounded in standard model editing benchmarks.
- It can be reported as a small public benchmark sanity check.

## 6. Minimal Execution Plan

1. Confirm GPT-J path exists or download size before opening GPU.
2. Build a 100-row CounterFact subset.
3. Run one ROME smoke edit.
4. Run 100-row ROME batch only if smoke passes.
5. Package only small JSON/CSV/MD results.

## 7. Risks

- GPT-J download may consume time and disk.
- CounterFact schema may require adapter code to match current scripts.
- MEMIT may require stats or additional covariance computation.
- Results should not be mixed with synthetic privacy metrics in one table without clear sectioning.
