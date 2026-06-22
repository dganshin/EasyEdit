# METHOD PROVENANCE AUDIT

## Git evidence

- git rev-parse HEAD: `c76cc30953771a865d150614c8f64ad163fc760d`
- git status --short:
```text
?? artifacts/analysis_v2_audit_20260622/
?? docs/V2_CONSERVATIVE_PACE_RUNLOG_2026-06-15.md
?? docs/WEEKLY_PROGRESS_2026-06-15_V2_PACE.md
?? scripts/analyze_v2_audit.py
?? "课程论文撰写模板 (研究类).docx"
```
- git remote -v:
```text
origin	git@github.com:dganshin/EasyEdit.git (fetch)
origin	git@github.com:dganshin/EasyEdit.git (push)
```

## Core algorithm diff

- `git diff -- easyeditor/models/rome easyeditor/models/memit` 结果为空，说明当前工作树没有未提交的 ROME/MEMIT core diff。
- 但文件历史显示 `easyeditor/models/rome/layer_stats.py` 在近期 commit 中被改过，属于 MEMIT/ROME 统计数据加载链路改动，不是编辑更新公式本身。
- `easyeditor/models/memit` 当前无工作树 diff。

### layer_stats recent history
```text
163e094 Use stable Wikipedia parquet source
eb4c21b Add offline MEMIT stats dataset prep
c845ae5 Stream Wikipedia stats loading
ec3fcd9 Add MEMIT stats prep script
b4c61b3 support MEND and MEMIT for Qwen2
62d256c Refactor step 1
6ddaffc support MEMIT for Mistral
64f51e0 Update layer_stats.py
5581c3b fix a bug
ef713cf add optional way to load wikipedia dataset
771d43b update global config
3fb01b3 support llama-2
870363c update README
d109998 update README
b696d69 support ROME&MEMIT for GPTJ
a781d66 Initial Commit
```

## Hashes
- hparams/ROME/qwen2.5-7b.yaml: `8c9bf8e1fcbe2232d2631de13a9f3dafc2869d8488915df988a04be436f4f3ca`
- hparams/MEMIT/qwen2.5-7b.yaml: `444f6bbe778c69da9741a5380096bf2fb1b420479e16a0a6430e4d264f53b8b2`
- dataset artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json: `7744b6f10e81defa9dcd33b38330e03c78a4f90ddbe1353ff542af56ad6380a4`
- requests artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json: `14a46adb23ee022dcde7dbcbb1e65e62dea1d52ccadc997a5414a8d7d2d08274`

## Start model audit

- ROME direct-only: model_path = `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- MEMIT direct-only: model_path = `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- PACE target_only: model_path = `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- PACE max1_per_case: model_path = `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`
- PACE max2_per_person: model_path = `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged`

结论：ROME / MEMIT / PACE 三条 v2 主线都从同一个 merged leakage model `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` 出发；PACE 是在同一 pre model 上追加 round2 requests 的 ROME wrapper，不是 `pre -> ROME -> MEMIT` 串联。

