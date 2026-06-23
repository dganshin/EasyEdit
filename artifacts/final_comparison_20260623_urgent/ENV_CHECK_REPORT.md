# Urgent Main Experiment Environment Check

- root: `/root/autodl-tmp/projects/EasyEdit`
- timestamp: `2026-06-23 17:10:05`
- python: `/root/miniconda3/envs/easyedit/bin/python3`
- conda env: `easyedit`

## GPU
```text
Tue Jun 23 17:10:05 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.124.04             Driver Version: 570.124.04     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA vGPU-48GB               On  |   00000000:16:00.0 Off |                  Off |
| 99%   48C    P8             66W /  450W |       1MiB /  49140MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
                                                                                         
+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

## Required Paths
- OK: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- OK: `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json`
- OK: `artifacts/run_20260615_v2_rome_direct/privacy_leakage_eval_v2_rome_direct_full.json`
- OK: `artifacts/run_20260615_v2_rome_direct/public_retain_eval_v2_rome_direct.json`
- OK: `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
