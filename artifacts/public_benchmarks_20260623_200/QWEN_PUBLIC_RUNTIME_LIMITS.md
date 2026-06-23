# Qwen Public Runtime Limits

Qwen2.5-7B public benchmark uses 200-case CounterFact/zsRE.

Completed:
- CounterFact: ROME, FT, KN
- zsRE: ROME, FT

Stopped / failed:
- CounterFact IKE: missing local sentence-transformer dependency `./hugging_cache/all-MiniLM-L6-v2`
- zsRE KN: CUDA OOM during coarse neuron search
- zsRE IKE: not run after KN failure

Decision:
- Do not continue KN/IKE under current 48G/time budget.
- Use completed Qwen public baseline rows plus ROME+PACE-Edit / ROME+CAPE-Edit wrapper rows for public transfer validation.
- Treat public benchmark as migration validation, not main privacy sanitization evidence.
