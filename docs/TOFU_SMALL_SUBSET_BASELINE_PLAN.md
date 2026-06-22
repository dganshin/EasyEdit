# TOFU Small Subset Baseline Plan

## 1. Purpose

TOFU is a public forget/retain benchmark candidate. It can test whether the current privacy-utility evaluation framing transfers from synthetic PII to a public unlearning-style setting.

## 2. Data Source

- likely public dataset: `locuslab/TOFU`
- current repo status: no first-class local EasyEdit loader confirmed
- action now: plan only; no full download

## 3. Subset Size

Recommended first subset:

- 20 forget subjects or 100 QA pairs for smoke
- then 100-200 QA pairs if schema and evaluation are stable

## 4. Model Candidates

| model | role | risk |
| --- | --- | --- |
| GPT-J-6B | public model alignment with EasyEdit hparams | medium download risk |
| Qwen2.5-7B | reuses current infrastructure | lower engineering risk, weaker public comparability |
| LLaMA-2-7B | common unlearning baseline | high access and VRAM risk |

## 5. Methods

Initial low-cost methods:

1. Prompt Refusal
2. LoRA/SFT Sanitization
3. ROME on selected forget facts

Do not start with MEMIT or large multi-method sweeps before the TOFU schema and metrics are verified.

## 6. Metrics

- forget quality: target answer no longer produced or answer confidence reduced
- retain quality: retained author/fact QA accuracy
- refusal rate: whether forgetting degenerates into broad refusal
- public retain degradation: retain split contains/accuracy drop

## 7. Relationship to Current Work

TOFU does not contain the same synthetic phone/email PII structure. It should be written as a transfer check for the broader forget-retain framing, not as direct replacement for the synthetic privacy benchmark.

## 8. Risks

- Evaluation protocol differs from current value-contains metrics.
- Small subset results can show feasibility but not final benchmark performance.
- If Prompt Refusal performs well on TOFU, it may reflect prompt compliance rather than model memory deletion.
