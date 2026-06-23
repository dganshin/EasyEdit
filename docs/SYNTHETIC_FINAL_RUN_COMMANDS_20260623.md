# Synthetic Final Run Commands 20260623

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: synthetic ROME/MEMIT/PACE/CAPE-v1; public partial Qwen baseline; ablation placeholders  
Current running artifacts: none confirmed locally  
Pending server artifacts: CAPE-Anchor B20-K0/K1/K2; synthetic FT/KN; final claim decision  
Next action: run the CAPE-Anchor first, then synthetic FT/KN, then final tables and claim decision  
Risk / fallback: do not run public wrapper, GPT-J, IKE, MEND/SERAC, or new datasets in this final pass.

## 1. Server sync

Use SSH remote. If Git asks for GitHub username/password, stop with `Ctrl+C`; the remote is wrong.

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true

export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

git remote set-url origin git@github.com:dganshin/EasyEdit.git
ssh -T git@github.com || true
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git pull --rebase --autostash origin main

conda activate easyedit
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
```

## 2. Preferred one-shot run

This run explicitly disables public wrappers. It only runs synthetic extra editors, CAPE-Anchor, final figures/tables, and claim decision.

```bash
screen -S urgent_synthetic

cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

RUN_SYNTH_EXTRA=1 \
RUN_CAPE_ANCHOR=1 \
RUN_PUBLIC_WRAPPERS=0 \
RUN_FIGURES=1 \
RUN_CLAIM_DECISION=1 \
METHODS=FT,KN \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_urgent_main_experiments_48g.sh
```

Expected key outputs:

```text
artifacts/run_20260623_cape_anchor_rescue/
artifacts/final_comparison_20260623_urgent/table_cape_anchor_rescue.csv
artifacts/run_20260623_v2_ft_baseline/
artifacts/run_20260623_v2_kn_baseline/
artifacts/final_comparison_20260623_urgent/table_synthetic_main_results.csv
artifacts/final_comparison_20260623_urgent/table_synthetic_extra_editors.csv
artifacts/final_comparison_20260623_urgent/fig_privacy_utility_tradeoff.png
artifacts/final_comparison_20260623_urgent/fig_public_refusal_comparison.png
artifacts/final_comparison_20260623_urgent/fig_attack_type_breakdown.png
artifacts/final_comparison_20260623_urgent/METHOD_CLAIM_DECISION.md
```

## 3. Safer staged run

If you want to avoid losing time when one phase fails, run these separately.

### 3.1 CAPE-Anchor only

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_cape_anchor_rescue.sh
```

### 3.2 Synthetic FT/KN only

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

METHODS=FT,KN \
SHUTDOWN_ON_EXIT=0 \
STREAM_LOGS=1 \
bash scripts/run_synthetic_privacy_extra_editors.sh
```

### 3.3 Final tables and claim

```bash
cd /root/autodl-tmp/projects/EasyEdit
conda activate easyedit

python3 scripts/build_paper_ready_figures_and_tables.py
python3 scripts/decide_method_claim_level.py
python3 scripts/build_ablation_assets.py
python3 scripts/build_topconf_result_tables.py
```

## 4. Do not run now

```text
public wrapper
GPT-J
IKE dependency repair
TOFU / Enron / LLaMA / The Pile
MEND / SERAC training
new public benchmark
large PACE/CAPE sweep
```

