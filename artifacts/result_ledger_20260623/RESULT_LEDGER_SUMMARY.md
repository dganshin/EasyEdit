# Result Ledger Summary

Last updated: 2026-06-23

## 1. 当前可报数字

- Synthetic privacy 可进正文主表的有效行：`8`。
- Qwen public 可进公开迁移验证表的有效行：`13`。

## 2. 状态计数

| status | count |
| --- | --- |
| failed | 4 |
| missing_artifact | 3 |
| ok | 29 |
| pending | 5 |
| stopped | 4 |

## 3. 正文主表建议

- Synthetic privacy: Leakage model / ROME direct / MEMIT direct / PACE variants / CAPE variants.
- 如果 urgent main 返回，再加入 FT / KN / CAPE-Anchor K0/K1/K2。
- Public table 主体只放 Qwen CounterFact / zsRE 的真实指标；GPT-J 仅作为 50/100-case ROME/FT fast patch 或附表，不扩 KN/IKE。

## 4. 附表或失败表

- IKE dependency failure.
- KN zsRE OOM.
- GPT-J partial/stopped.
- Public wrapper CUDA failed/missing.

## 5. 下一步唯一值得跑的实验

CAPE-Anchor B20-K0/K1/K2 and synthetic FT/KN remain the main line. GPT-J is limited to the ROME/FT fast patch if a local model already exists; do not expand GPT-J KN/IKE/MEMIT or new public datasets.

## 6. 前 30 行 ledger 预览

| model | dataset | method | status | private_value_contains | public_contains | reliability | generalization | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | Leakage model | ok | 0.9387 | 0.9766 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | ROME direct | ok | 0.5787 | 0.5591 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | MEMIT direct | ok | 0.814 | 0.8472 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | PACE target_only | ok | 0 | 0.0032 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | PACE max1_per_case | ok | 0.0003 | 0.0099 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | PACE max2/person | ok | 0.0243 | 0.0984 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | CAPE-v0 | ok | 0.0023 | 0.006 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | CAPE-v1 | ok | 0.0443 | 0.1119 | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | Fine-tuning | pending | missing | missing | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | Knowledge Neurons | pending | missing | missing | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | In-context Editing | failed | missing | missing | missing | missing | missing_or_failed_dependency |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | PACE-Lite B20-K0 | pending | missing | missing | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | CAPE-Anchor B20-K1 | pending | missing | missing | missing | missing | missing |
| Qwen2.5-7B privacy-v2 merged | synthetic_privacy_v2 | CAPE-Anchor B20-K2 | pending | missing | missing | missing | missing | missing |
| Qwen2.5-7B | counterfact-200 | FT | ok | missing | missing | 1 | 0.725 | missing |
| Qwen2.5-7B | counterfact-200 | ROME | ok | missing | missing | 0.995 | 0.82 | missing |
| Qwen2.5-7B | counterfact-200 | ROME_CAPE_EDIT | ok | missing | missing | 0 | 0 | missing |
| Qwen2.5-7B | counterfact-200 | ROME_PACE_EDIT | ok | missing | missing | 0 | 0 | missing |
| Qwen2.5-7B | zsre-200 | FT | ok | missing | missing | 0.793012 | 0.808435 | missing |
| Qwen2.5-7B | zsre-200 | ROME | ok | missing | missing | 0.9975 | 0.945083 | missing |
| Qwen2.5-7B | zsre-200 | ROME_CAPE_EDIT | ok | missing | missing | 0.00154321 | 0 | missing |
| Qwen2.5-7B | zsre-200 | ROME_PACE_EDIT | ok | missing | missing | 0.00154321 | 0 | missing |
| Qwen2.5-7B | counterfact-200 | FT | ok | missing | missing | 1 | 1 | missing |
| Qwen2.5-7B | counterfact-200 | IKE | failed | missing | missing | missing | missing | FileNotFoundError('Path ./hugging_cache/all-MiniLM-L6-v2 not found') |
| Qwen2.5-7B | counterfact-200 | KN | ok | missing | missing | 0.0075 | 0.0075 | missing |
| Qwen2.5-7B | counterfact-200 | ROME | ok | missing | missing | 0.995 | 0.755 | missing |
| Qwen2.5-7B | counterfact-200 | ROME_PACE_EDIT | failed | missing | missing | missing | missing | RuntimeError('CUDA is required for public editing baselines.') |
| Qwen2.5-7B | zsre-200 | FT | ok | missing | missing | 0.738413 | 0.746865 | missing |
| Qwen2.5-7B | zsre-200 | KN | failed | missing | missing | missing | missing | OutOfMemoryError('CUDA out of memory. Tried to allocate 20.00 MiB. GPU 0 has a total capacity of 47.38 GiB of which 8.69 MiB is free. Including non-PyTorch memory, this process has 47.37 GiB memory in use. Of the allocated memory 46.80 GiB is allocated by PyTorch, and 118.42 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)') |
| Qwen2.5-7B | zsre-200 | ROME | ok | missing | missing | 1 | 0.976333 | missing |
