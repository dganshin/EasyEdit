# Model Availability Report

- created_at: `2026-06-23T08:52:31`
- download_gptj: `True`
- hf_endpoint: `None`

## GPT-J-6B

- `/root/autodl-tmp/models/gpt-j-6B` exists=True files=11
- `/root/autodl-tmp/models/GPT-J-6B` exists=False files=None

- HF cache candidates: `['/root/autodl-tmp/hf_cache/hf/hub/models--EleutherAI--gpt-j-6b']`
- download result: `{'downloaded': False, 'repo_id': 'EleutherAI/gpt-j-6b', 'target': '/root/autodl-tmp/models/gpt-j-6B', 'error': 'SSLError(MaxRetryError("HTTPSConnectionPool(host=\'huggingface.co\', port=443): Max retries exceeded with url: /api/models/EleutherAI/gpt-j-6b/revision/main (Caused by SSLError(SSLEOFError(8, \'[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1017)\')))"), \'(Request ID: 1936a122-cdd0-4076-9437-adf6bade7f8e)\')', 'traceback_tail': 'urllib3.exceptions.SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1017)\n\nThe above exception was the direct cause of the following exception:\n\nTraceback (most recent call last):\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/requests/adapters.py", line 696, in send\n    resp = conn.urlopen(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/urllib3/connectionpool.py", line 842, in urlopen\n    retries = retries.increment(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/urllib3/util/retry.py", line 543, in increment\n    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]\nurllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host=\'huggingface.co\', port=443): Max retries exceeded with url: /api/models/EleutherAI/gpt-j-6b/revision/main (Caused by SSLError(SSLEOFError(8, \'[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1017)\')))\n\nDuring handling of the above exception, another exception occurred:\n\nTraceback (most recent call last):\n  File "/root/autodl-tmp/projects/EasyEdit/scripts/check_public_model_availability.py", line 98, in safe_snapshot\n    return snapshot_to_dir(repo_id, target, allow_patterns=allow_patterns)\n  File "/root/autodl-tmp/projects/EasyEdit/scripts/check_public_model_availability.py", line 86, in snapshot_to_dir\n    local_dir = snapshot_download(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn\n    return fn(*args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/_snapshot_download.py", line 165, in snapshot_download\n    repo_info = api.repo_info(repo_id=repo_id, repo_type=repo_type, revision=revision)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn\n    return fn(*args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/hf_api.py", line 2867, in repo_info\n    return method(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn\n    return fn(*args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/hf_api.py", line 2660, in model_info\n    r = get_session().get(path, headers=headers, timeout=timeout, params=params)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/requests/sessions.py", line 671, in get\n    return self.request("GET", url, params=params, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/requests/sessions.py", line 651, in request\n    resp = self.send(prep, **send_kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/requests/sessions.py", line 784, in send\n    r = adapter.send(request, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_http.py", line 96, in send\n    return super().send(request, *args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/requests/adapters.py", line 727, in send\n    raise SSLError(e, request=request)\nrequests.exceptions.SSLError: (MaxRetryError("HTTPSConnectionPool(host=\'huggingface.co\', port=443): Max retries exceeded with url: /api/models/EleutherAI/gpt-j-6b/revision/main (Caused by SSLError(SSLEOFError(8, \'[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1017)\')))"), \'(Request ID: 1936a122-cdd0-4076-9437-adf6bade7f8e)\')\n'}`
- config/tokenizer check: `{'checked': True, 'ok': True, 'model_type': 'gptj', 'vocab_size': 50257}`

## LLaMA-2 Backup

- backup repo: `NousResearch/Llama-2-7b-hf`
- download result: `None`

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
export HF_ENDPOINT=https://hf-mirror.com
python3 scripts/check_public_model_availability.py --download_gptj --hf_endpoint https://hf-mirror.com
```
