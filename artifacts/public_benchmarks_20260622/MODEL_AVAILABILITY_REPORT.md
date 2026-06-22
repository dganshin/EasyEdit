# Model Availability Report

- created_at: `2026-06-22T23:00:29`
- download_gptj: `False`

## GPT-J-6B

- `/root/autodl-tmp/models/gpt-j-6B` exists=False files=None
- `/root/autodl-tmp/models/GPT-J-6B` exists=False files=None

- HF cache candidates: `[]`
- download result: `None`
- config/tokenizer check: `{'checked': False, 'ok': None, 'reason': 'skipped'}`

## Qwen2.5-7B

- `/root/autodl-tmp/models/Qwen2.5-7B` exists=False files=None

## LLaMA-2-7B Probe Only

- `/root/autodl-tmp/models/Llama-2-7b-hf` exists=False files=None
- `/root/autodl-tmp/models/llama-2-7b` exists=False files=None
- `/root/autodl-tmp/models/LLaMA-2-7B` exists=False files=None

## Server Download Command

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
conda activate easyedit
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python3 scripts/check_public_model_availability.py --download_gptj
```
