# Next Experiment Feasibility Audit

日期：2026-06-22

本审计只基于当前本地仓库、已有脚本、hparams 和 artifacts。结论用于决定下一批最小可行实验，不代表公开 benchmark 已经完成运行。

## 1. 当前边界

- 本轮不启动 GPU。
- 本轮不下载 GPT-J、LLaMA、TOFU、CounterFact 等大文件。
- 本轮不修改 EasyEdit、ROME、MEMIT 底层算法。
- 本轮优先补齐非参数 Prompt Refusal baseline、LoRA/SFT Sanitization 数据准备，以及公开基准 small subset 计划。

## 2. EasyEdit 方法可行性

| method | local code path | hparams path | needs training editor? | Qwen2.5-7B | GPT-J-6B | risk | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ROME | `easyeditor/models/rome` | `hparams/ROME/qwen2.5-7b.yaml`, `hparams/ROME/gpt-j-6B.yaml` | no | yes, 已跑通 v2 | yes, hparams exists | low | P0: 已是主线 baseline |
| MEMIT | `easyeditor/models/memit` | `hparams/MEMIT/qwen2.5-7b.yaml`, `hparams/MEMIT/gpt-j-6B.yaml` | no, but needs MOM2 stats | yes, 已跑通 v2 | yes, hparams exists | medium | P0: 已完成 synthetic v2；公开 small subset 可后续用 |
| FT / FT-L | `easyeditor/models/ft`, trainer `easyeditor/trainer/algs/ft.py` | `hparams/FT/qwen2.5-7b.yaml`, `hparams/FT/gpt-j-6B.yaml` | no separate editor checkpoint | yes, hparams exists | yes, hparams exists | medium | P1: 可作为参数更新 baseline |
| LoRA / SFT | `easyeditor/models/lora`, scripts under `scripts/train_lora_privacy_injection.py` | `hparams/LoRA/qwen2.5-7b.yaml`, `hparams/LoRA/gpt-j-6B.yaml` | trains adapter | yes, 已有 Qwen LoRA workflow | yes, hparams exists | medium | P0: 先只生成 sanitization data |
| IKE | `easyeditor/models/ike` | `hparams/IKE/qwen2.5-7b.yaml`, `hparams/IKE/gpt-j-6B.yaml` | no parameter edit, needs demonstrations | yes, hparams exists | yes, hparams exists | medium | P1: 公开 small subset 候选 |
| MEND | `easyeditor/models/mend`, trainer `easyeditor/trainer/algs/MEND.py` | `hparams/MEND/qwen2.5-7b.yaml`, `hparams/MEND/gpt-j-6B.yaml` | yes | hparams exists, but editor training/checkpoint risk | hparams exists | high | P3: 不适合作为近期补实验 |
| SERAC | `easyeditor/models/serac`, trainer `easyeditor/trainer/algs/SERAC.py` | `hparams/SERAC/gpt-j-6B.yaml`, `hparams/TRAINING/SERAC/...` | yes | no direct qwen hparams observed in main SERAC dir | yes | high | P3: 需要训练 editor |
| GRACE | `easyeditor/models/grace` | `hparams/GRACE/qwen2.5-7b.yaml`, `hparams/GRACE/gpt-j-6b.yaml` | unknown / method-specific memory | yes, hparams exists | yes, hparams exists | medium-high | P2: 可做后续探索 |
| KN | `easyeditor/models/kn` | `hparams/KN/qwen2.5-7b.yaml`, `hparams/KN/gpt-j-6B.yaml` | no | yes | yes | medium | P2: 可做知识定位对照 |
| PMET | `easyeditor/models/pmet` | `hparams/PMET/gpt-j-6B.yaml`, `hparams/PMET/llama-7b.yaml` | no | qwen hparams not observed | yes | medium-high | P2/P3: 公开 GPT-J 可尝试 |
| WISE | `easyeditor/models/wise` | `hparams/WISE/qwen2.5-7b.yaml`, `hparams/WISE/gpt-j-6B.yaml` | method-specific | yes | yes | medium-high | P2: 先不作为近期主线 |
| AlphaEdit | `easyeditor/models/alphaedit` | `hparams/AlphaEdit/qwen2.5-7b.yaml`, `hparams/AlphaEdit/gpt-j-6B.yaml` | no | yes | yes | medium-high | P2: 可作为后续强 baseline |

审计判断：近期最稳的顺序是 Prompt Refusal baseline -> LoRA/SFT Sanitization 数据和计划 -> CounterFact GPT-J small subset 计划 -> TOFU small subset 计划。MEND/SERAC 这类训练型 editor 不适合作为当前低成本补实验。

## 3. 模型可行性

| model | local hparams exists? | editing methods available | model path available locally? | needs download? | expected VRAM | risk | recommended use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-7B | yes: ROME/MEMIT/FT/LoRA/IKE/GRACE/KN/WISE/AlphaEdit | many | Windows no; AutoDL known path `/root/autodl-tmp/models/Qwen2.5-7B` and merged privacy model | no for current server image, if unchanged | 24GB for generation/ROME safer; MEMIT/stats previously used 48GB | low | 当前 synthetic privacy 主模型 |
| Qwen2.5-7B privacy merged | script paths use `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | ROME/MEMIT/PACE/CAPE/prompt baseline | Windows no; AutoDL path known | no if server still has it | 24GB may run generation; 48GB safer for editing | low | Prompt Refusal baseline target |
| GPT-J-6B | yes: ROME/MEMIT/FT/LoRA/IKE/MEND/GRACE/KN/PMET/WISE/AlphaEdit | mature for EasyEdit | not present locally in repo | yes, likely 12-24GB weights/cache | 24GB for small subset; 48GB safer for MEMIT | medium | public CounterFact small subset preferred |
| LLaMA-2-7B | yes in many hparams as llama-7b | many | not present locally | yes, access/licensing and tokenizer risk | EasyEdit README notes 40GB+ for llama-2-7B editing | high | only as later candidate |
| Pythia | partial references under Steer SAE configs and paper docs | not a main editing hparams target in current core set | no | yes | depends size; Pythia-6.9B similar 24GB+ | high | only as external validity candidate |
| GPT-Neo | README says GPT-Neo supported | hparams not confirmed as first-class in current scan | no | yes | depends size | medium-high | not priority |
| GPT2 / GPT2-XL | yes for ROME/MEMIT/FT/LoRA/IKE/GRACE/KN/AlphaEdit | many | no local weights | yes, smaller than 7B | 12-24GB | medium | quick public editing smoke candidate if needed |
| T5 | yes for FT/MEND/SERAC/KN | mainly seq2seq/training editor paths | no | yes | 24GB depending size | high | not aligned with current causal LM pipeline |

## 4. 公开数据集可用性

| dataset | source | estimated size | download risk | fields | can build small subset? | priority |
| --- | --- | --- | --- | --- | --- | --- |
| CounterFact | EasyEdit loader `easyeditor/dataset/counterfact.py`; README mentions placing data in `data` | medium, public JSON | medium; avoid full download until confirmed | subject, prompt, target_new, ground_truth, locality/rephrase | yes, 100/200 rows | P0 for public knowledge editing |
| zsRE | EasyEdit loader `easyeditor/dataset/zsre.py` | medium | medium | question/prompt, answer, locality/rephrase | yes | P1 |
| LAMA | no direct first-class loader found; related `knowns.py` | varies | medium | factual cloze triples | yes but needs adapter script | P2 |
| TOFU | not local loader; likely HuggingFace `locuslab/TOFU` | small/medium | medium; no full download now | question, answer, forget/retain split | yes, small forget/retain pilot | P0/P1 as forget-retain public baseline |
| Enron | no local loader; referenced in docs/paper notes | large/raw email corpus variants | high; privacy/legal handling requires care | email text, metadata, possible PII | yes only with masked/synthetic PII pilot | P2 |
| DEPN setting | no local dataset entry confirmed | unknown | high | depends on paper setting | unknown | P3 |
| The Pile / Pythia related data | referenced in docs and Steer configs | very large | very high | pretraining corpus chunks | no full subset without careful source choice | P3 |

## 5. Recommended Minimal Queue

1. P0: Prompt Refusal baseline on Qwen synthetic v2. 当前只提交 dry-run/report 和服务器命令，正式跑需用户确认。
2. P0: LoRA/SFT Sanitization data construction. 本地可完成，不训练。
3. P1: CounterFact small subset + GPT-J-6B plan. 先计划，不下载。
4. P1: TOFU small subset plan. 先计划，不下载。
5. P1/P2: CAPE-Anchor design. 先设计，不运行。

## 6. Risk Notes

- Prompt Refusal baseline 是非参数 baseline。即使 private refusal rate 高，也不能说明模型内部隐私知识已被清除。
- LoRA/SFT Sanitization 可能学到广义拒答，因此训练数据必须保留 public answer 样本并做 balanced sampling。
- CounterFact/GPT-J 用于通用知识编辑可跑性和 locality sanity check，不应被写成 PII 清洗实验。
- TOFU 可用于公开 forget/retain 迁移验证，但和当前 synthetic PII 任务不是同一数据分布。
