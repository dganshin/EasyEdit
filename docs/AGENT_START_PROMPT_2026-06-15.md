# 新 Agent 启动 Prompt（2026-06-15）

下面这段文字可以直接复制给新的 agent，帮助其无缝接替当前工作。

---

你现在接手的是 `EasyEdit` 仓库中的 synthetic privacy editing 项目。请先不要自由发散，不要重复 baseline，不要重复 LoRA 注入，不要直接引入 MEMIT、native-sensitive 新分支或真实 PII benchmark。先基于仓库内现有 artifact 和文档理解当前状态，再决定后续动作。

## 仓库位置

- 本地仓库：当前就是 `EasyEdit`
- 服务器代码路径：
  - `/root/autodl-tmp/projects/EasyEdit`

## 当前服务器环境约定

```bash
conda activate easyedit
bash /root/start_mihomo.sh

export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## 当前主线阶段

当前实验主线已经推进到：

```text
synthetic dataset
-> LoRA privacy injection
-> merged privacy leakage model
-> ROME direct-only
-> PACE Round2
```

## 当前最重要 artifact

优先查看：

- `artifacts/run_20260614_privacy_baseline/`
- `artifacts/run_20260614_lora_mlp_only/`
- `artifacts/run_20260614_rome_privacy_direct/`
- `artifacts/run_20260615_pace_round2_merged/`

## 当前最重要文档

优先阅读：

1. `AGENTS.md`
2. `docs/SESSION_HANDOFF.md`
3. `docs/WEEKLY_PROGRESS_2026-06-15_PACE.md`
4. `docs/PACE_ROUND2_RUNLOG_2026-06-15.md`

## 当前关键结果

### LoRA merged privacy leakage model

- private:
  - exact `0.9875`
  - regex `0.9375`
  - sensitive `1.0000`
  - refusal `0.0000`

### ROME direct-only

- private:
  - exact `0.0375`
  - regex `0.0375`
  - sensitive `0.5375`
  - refusal `0.3875`
- public:
  - exact `0.05`
  - contains `0.10`

### PACE Round2

- private:
  - exact `0.0000`
  - regex `0.0000`
  - sensitive `0.0000`
  - refusal `1.0000`
- 四类攻击 `direct / paraphrase / completion / roleplay`：
  - 全部 `leak = 0`
  - 全部 `sensitive = 0`
  - 全部 `refusal = 1.0`
- public:
  - exact `0.00`
  - contains `0.00`

## 当前最准确结论

当前结论不是“PACE 完美成功”，而是：

> PACE Round2 在当前 synthetic privacy setting 下，能够将 residual leakage 与 sensitive-pattern hallucination 压到 0，并把 refusal rate 提升到 100%；但代价是 public retain 完全丢失，表现出明显的 over-refusal / over-editing。

## 当前不要做的事

在没有新的外部方向决策前，不要默认继续：

- 重跑 baseline
- 重跑 LoRA 注入
- 重跑 direct-only
- 擅自扩到 MEMIT / native-sensitive / 真实 PII benchmark

## 当前最值得继续分析的问题

如果没有新的用户指令，后续最应该围绕：

```text
如何在保持 privacy suppression 的同时降低 public damage
```

展开，而不是继续证明“能不能 suppress leakage”。

## 额外提醒

- 当前仓库里已经补了不少脚本、文档和 artifact；先复用，不要重写一套。
- 如果后续继续落代码，优先保持主逻辑不动，只在 `scripts/` 和 `docs/` 做增量。
- 每轮关键实验后都应同步补：
  - 简要汇报版文档
  - 详细 runlog 文档
  - 对应 `artifacts/run_YYYYMMDD_<name>/`

---
