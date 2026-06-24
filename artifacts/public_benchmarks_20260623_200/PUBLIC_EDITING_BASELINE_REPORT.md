# Public Editing Baseline Report

CounterFact 不是 PII 数据集，是公开事实编辑 benchmark；zsRE 不是 PII 数据集，是问答式知识编辑 benchmark。它们用于证明本文实验框架能在公开模型编辑基准上进行多方法比较，不和 synthetic privacy 指标混成同一张表。

| dataset | model | method | status | cases | rewrite | rephrase | locality | error |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| counterfact | gpt-j-6B | FT | ok | 200 | 1.0000 | 0.7250 |  |  |
| counterfact | gpt-j-6B | ROME | ok | 200 | 0.9950 | 0.8200 |  |  |
| counterfact | gpt-j-6B | ROME_CAPE_EDIT | ok | 220 | 0.9955 | 0.7455 |  |  |
| counterfact | gpt-j-6B | ROME_PACE_EDIT | ok | 220 | 0.9955 | 0.7455 |  |  |
| zsre | gpt-j-6B | FT | ok | 200 | 0.7930 | 0.8084 |  |  |
| zsre | gpt-j-6B | ROME | ok | 200 | 0.9975 | 0.9451 |  |  |
| zsre | gpt-j-6B | ROME_CAPE_EDIT | calibration_needed | 0 |  |  |  | GPT-J public PACE/CAPE wrappers are skipped by default because the uncalibrated ROME-based closed-loop request set previously showed near-zero rewrite success while ROME/FT baselines were healthy. Set GPTJ_WRAPPER_POLICY=run_uncalibrated to run the old behavior after model-specific calibration. |
| zsre | gpt-j-6B | ROME_PACE_EDIT | calibration_needed | 0 |  |  |  | GPT-J public PACE/CAPE wrappers are skipped by default because the uncalibrated ROME-based closed-loop request set previously showed near-zero rewrite success while ROME/FT baselines were healthy. Set GPTJ_WRAPPER_POLICY=run_uncalibrated to run the old behavior after model-specific calibration. |
| counterfact | qwen2.5-7b | FT | ok | 200 | 1.0000 | 1.0000 |  |  |
| counterfact | qwen2.5-7b | IKE | failed | 200 |  |  |  | FileNotFoundError('Path ./hugging_cache/all-MiniLM-L6-v2 not found') |
| counterfact | qwen2.5-7b | KN | ok | 200 | 0.0075 | 0.0075 |  |  |
| counterfact | qwen2.5-7b | ROME | ok | 200 | 0.9950 | 0.7550 |  |  |
| counterfact | qwen2.5-7b | ROME_CAPE_EDIT | ok | 224 | 0.5179 | 0.4196 |  |  |
| counterfact | qwen2.5-7b | ROME_PACE_EDIT | ok | 224 | 0.5179 | 0.4196 |  |  |
| zsre | qwen2.5-7b | FT | ok | 200 | 0.7384 | 0.7469 |  |  |
| zsre | qwen2.5-7b | KN | failed | 200 |  |  |  | OutOfMemoryError('CUDA out of memory. Tried to allocate 20.00 MiB. GPU 0 has a total capacity of 47.38 GiB of which 8.69 MiB is free. Including non-PyTorch memory, this process has 47.37 GiB memory in use. Of the allocated memory 46.80 GiB is allocated by PyTorch, and 118.42 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)') |
| zsre | qwen2.5-7b | ROME | ok | 200 | 1.0000 | 0.9763 |  |  |
| zsre | qwen2.5-7b | ROME_CAPE_EDIT | ok | 206 | 0.3117 | 0.2953 |  |  |
| zsre | qwen2.5-7b | ROME_PACE_EDIT | ok | 206 | 0.3117 | 0.2953 |  |  |
