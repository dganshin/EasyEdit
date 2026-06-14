# EasyEdit 仓库协作约定

## 1. 工作边界

- 本仓库当前阶段的主要目标是先打通 **原始 EasyEdit 单条模型编辑 pipeline**。
- 当前不是做隐私清洗本身，而是先把标准编辑方法跑通，再在这个基础上继续扩展。
- 不要随意改 EasyEdit 核心算法逻辑；优先把改动限制在：
  - `scripts/`
  - `docs/`
  - `.gitignore`
  - 必要的本地配置模板

## 2. 跨设备协作约定

- 本地开发机器可能是 Windows 或 macOS。
- 真正跑实验的环境始终是 Linux 服务器（当前主要是 AutoDL）。
- 推荐工作流：
  1. 本地修改代码
  2. 本地 `git commit` + `git push`
  3. 服务器进入仓库后 `git pull`
  4. 在服务器上运行脚本与实验

不要反过来在服务器上做大规模手改，然后再想办法回收。

## 2.1 实验记录约定

- 每完成一轮关键实验，除了保存原始输出文件，还应同步补两份文档：
  - 一份简要版：适合组会汇报
  - 一份详细版：适合和新的 agent / 后续技术讨论对接
- 推荐命名：
  - `docs/WEEKLY_PROGRESS_YYYY-MM-DD.md`
  - `docs/<STAGE>_RUNLOG_YYYY-MM-DD.md`
- 对应结果文件应尽量整理到：
  - `artifacts/run_YYYYMMDD_<experiment_name>/`
- 如果服务器上已经产出重要结果，但还没写文档，不应直接进入下一阶段；应先补最小结果总结，避免后续讨论脱节。

## 3. 当前已知服务器布局

当前约定的 AutoDL 数据盘根目录是：

```text
/root/autodl-tmp/
```

主要路径：

- 代码：`/root/autodl-tmp/projects/EasyEdit`
- 模型：`/root/autodl-tmp/models`
- HF 缓存：`/root/autodl-tmp/hf_cache`
- 输出：`/root/autodl-tmp/outputs/easyedit`
- NLTK 数据：`/root/autodl-tmp/nltk_data`

系统盘 `/` 用来保存镜像中的基础环境；大文件、模型、缓存、输出尽量都放数据盘 `/root/autodl-tmp`。

## 4. 当前已知代理配置

当前 AutoDL 旧镜像里已有 `mihomo`，用于访问 GitHub / Hugging Face。

已知路径：

- 二进制：`/root/mihomo/mihomo`
- 启动脚本：`/root/start_mihomo.sh`
- 主配置：`/root/config.yaml`
- geo 数据：`/root/.config/mihomo`

启动命令：

```bash
bash /root/start_mihomo.sh
```

当前使用的代理环境变量通常是：

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## 5. 当前已知运行环境

服务器上建议使用独立 conda 环境：

```bash
conda activate easyedit
```

当前已知需要的关键环境变量：

```bash
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
```

如果切换新实例或新镜像，优先先检查这些路径和变量是否仍然成立。

## 6. 当前已知模型选择

当前成功跑通单条编辑的模型不是 LLaMA，而是：

```text
Qwen2.5-7B
```

服务器模型目录约定为：

```text
/root/autodl-tmp/models/Qwen2.5-7B
```

注意：

- 通过 ModelScope 下载的 `Qwen2.5-7B` 目录最初不完整。
- 为了让 `transformers` 正常加载，后续额外补了：
  - `tokenizer.json`
  - `vocab.json`

如果以后重新下载模型，需要确认 tokenizer 文件齐全，而不是只看权重分片是否存在。

## 7. 当前已知可用脚本

- 环境检查：`scripts/check_easyedit_env.py`
- 正式单条编辑：`scripts/run_single_edit.py`
- 兼容壳脚本：`scripts/smoke_single_edit.py`
- 合成隐私数据生成：`scripts/generate_synthetic_privacy_data.py`
- LoRA 训练数据构建：`scripts/build_lora_privacy_train_data.py`
- LoRA 隐私注入训练：`scripts/train_lora_privacy_injection.py`
- LoRA merge：`scripts/merge_lora_privacy_model.py`
- ROME 隐私请求构造：`scripts/build_rome_privacy_requests.py`
- PACE Round2 请求构造：`scripts/build_pace_reedit_requests.py`
- ROME direct-only refusal 编辑：`scripts/run_rome_privacy_refusal.py`
- 通用 refusal 编辑入口：`scripts/run_privacy_refusal_edit.py`
- 隐私批量生成：`scripts/run_privacy_generation.py`
- 隐私泄露评测：`scripts/evaluate_privacy_leakage.py`
- public retain 评测：`scripts/evaluate_public_retain.py`
- baseline 汇总：`scripts/summarize_privacy_baseline.py`
- ROME 前后汇总：`scripts/summarize_rome_privacy.py`

其中 `run_single_edit.py` 已经扩展支持：

- `--generation_prompt`
- `--top_k`
- `--disable_fluency_eval`

这些增强是为了更清楚地观察“内部指标成功但自由生成不明显变化”的情况。

新增的隐私相关脚本负责：

- 先生成小规模合成数据
- 用真实模型批量生成攻击问法输出
- 先做 exact/regex 级别的泄露检测
- 同时统计敏感格式幻觉输出
- 对 public facts 做 retain 评测
- 自动从失败样本构造 PACE Round2 再编辑请求

它们是后续 LoRA 注入和 PACE 闭环的准备层，不会改变 EasyEdit 主体逻辑。

当前 synthetic dataset / generation / eval 已经支持在 prompt 级别保留：

- `case_id`
- `attack_type`
- `attack_template_id`
- `base_prediction_id`
- `trial_id`

`scripts/evaluate_privacy_leakage.py` 额外支持：

- `--mode full`
- `--mode native_sensitive`

其中 `native_sensitive` 只用于衡量敏感格式输出抑制，不应在文档里表述成“真实预训练 PII 清除”。

LoRA 注入阶段的最小链路是：

- 先用 `scripts/build_lora_privacy_train_data.py` 从 synthetic dataset 构造训练集
- 再用 `scripts/train_lora_privacy_injection.py` 复用 EasyEdit 现有 LoRA 实现训练 adapter
- 如需主实验，应优先使用 `mlp_only` scope，然后通过 `scripts/merge_lora_privacy_model.py` 把 adapter merge 进模型权重
- 最后再用 `scripts/run_privacy_generation.py --lora_adapter_path ...` 或 merged model 对 private/public 复测

如果服务器是 48GB 显存，不建议继续使用最保守的 `batch_size=1, rank=8`。
优先通过训练命令覆盖这些参数，而不是再改代码：

- `--batch_size 4` 或 `8`
- `--rank 16`
- `--num_steps 120`
- `--target_modules q_proj k_proj v_proj o_proj`

当前已知稳定性注意事项：

- `hparams/LoRA/qwen2.5-7b.yaml` 原始 `lr=5e-3` 对更强配置可能过高
- `scripts/train_lora_privacy_injection.py` 现在会在未显式传 `--lr` 时，把过高默认值自动压到 `5e-4`
- 训练脚本现在默认启用 `max_grad_norm=1.0`
- 如果想进一步吃显存，可加 `--disable_gradient_checkpointing`

当前更推荐显式使用 `--lora_scope`，而不是手动拼 target modules：

- `attn_only`: `q_proj k_proj v_proj o_proj`
- `mlp_only`: `gate_proj up_proj down_proj`
- `attn_mlp`: attention + MLP 全部

当前主实验更推荐：

- `mlp_only` 作为主线
- `attn_only` 保留为消融 / 压力测试
- `mlp_only -> merge -> ROME direct-only -> attack-wise eval -> PACE round2` 作为当前推荐主路径

如果下一步要直接进入隐私拒答编辑，建议先走小规模 `direct-only`：

```bash
python scripts/run_privacy_refusal_edit.py \
  --method ROME \
  --dataset artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B-privacy-mlp-merged \
  --hparams hparams/ROME/qwen2.5-7b.yaml \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/rome_privacy_direct \
  --num_people 5 \
  --private_per_person 2 \
  --prompt_style canonical_qa \
  --full_private_eval \
  --eval_public \
  --disable_fluency_eval
```

如果要构造 PACE Round2 请求：

```bash
python scripts/build_pace_reedit_requests.py \
  --leakage_eval /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/privacy_leakage_eval_rome_direct_full.json \
  --predictions /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/privacy_predictions_rome_direct_full.jsonl \
  --output_path /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/pace_round2_requests.json
```

然后汇总：

```bash
python scripts/summarize_rome_privacy.py \
  --pre_privacy_eval artifacts/run_20260614_lora_mlp_only/privacy_leakage_eval_merged_mlp_only.json \
  --post_subset_privacy_eval /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/privacy_leakage_eval_rome_direct_subset.json \
  --post_full_privacy_eval /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/privacy_leakage_eval_rome_direct_full.json \
  --pre_public_eval /root/autodl-tmp/outputs/easyedit/public_retain_eval_merged_mlp_only.json \
  --post_public_eval /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/public_retain_eval_rome_direct.json \
  --output_path /root/autodl-tmp/outputs/easyedit/rome_privacy_direct/rome_direct_summary.json
```

## 8. 当前已知成功命令

当前已经在服务器真实跑通过的命令示例：

```bash
python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/qwen2.5-7b.yaml \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/qwen25_7b_rome \
  --prompt "The Eiffel Tower is located in" \
  --generation_prompt "Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome" \
  --top_k 10
```

也跑过关闭 fluency 的版本：

```bash
python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/qwen2.5-7b.yaml \
  --model_path /root/autodl-tmp/models/Qwen2.5-7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/qwen25_7b_rome \
  --prompt "The Eiffel Tower is located in" \
  --generation_prompt "Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome" \
  --top_k 10 \
  --disable_fluency_eval
```

## 9. 当前阶段已经得到的结论

- EasyEdit 原始单条编辑 pipeline 已经在服务器上真实跑通。
- 使用的是 `Qwen2.5-7B + ROME`。
- EasyEdit 内部指标里，`rewrite_acc` 已经出现 `0.0 -> 1.0` 的成功结果。
- 但自由生成和 top-k 展示目前没有同样明显地体现出 “Rome 替代 Paris”。

因此后续不要再把主要时间花在“环境是否能跑”上，而应重点分析：

- 为什么内部指标成功，但生成展示不明显
- 如何设计更合适的 probe / prompt / 输出方式

## 10. 交接文档

更详细的运行记录见：

- `docs/AUTODL_EASYEDIT_SETUP.md`
- `docs/WEEKLY_PROGRESS_2026-06-13.md`
- `docs/EASYEDIT_RUNLOG_FOR_AI_2026-06-13.md`
- `docs/WEEKLY_PROGRESS_2026-06-14.md`
- `docs/PRIVACY_BASELINE_RUNLOG_2026-06-14.md`
- `docs/WEEKLY_PROGRESS_2026-06-14_LORA.md`
- `docs/LORA_PRIVACY_INJECTION_RUNLOG_2026-06-14.md`
- `docs/WEEKLY_PROGRESS_2026-06-15_PACE.md`
- `docs/PACE_ROUND2_RUNLOG_2026-06-15.md`
- `docs/SESSION_HANDOFF.md`

## 11. 当前最新阶段状态（2026-06-15）

当前主线已经推进到：

```text
synthetic privacy dataset
-> LoRA privacy injection
-> merged privacy leakage model
-> ROME direct-only
-> PACE Round2
```

当前关键 artifact：

- `artifacts/run_20260614_privacy_baseline/`
- `artifacts/run_20260614_lora_mlp_only/`
- `artifacts/run_20260614_rome_privacy_direct/`
- `artifacts/run_20260615_pace_round2_merged/`

当前最重要的已确认结果：

### LoRA merged privacy leakage model

- private:
  - `target_exact_leak_rate = 0.9875`
  - `target_regex_leak_rate = 0.9375`
  - `sensitive_pattern_rate = 1.0000`
  - `safe_refusal_rate = 0.0000`

说明 synthetic private/public facts 已成功注入，后续清洗实验成立。

### ROME direct-only

- full private:
  - `target_exact_leak_rate = 0.0375`
  - `target_regex_leak_rate = 0.0375`
  - `sensitive_pattern_rate = 0.5375`
  - `safe_refusal_rate = 0.3875`
- public:
  - `exact_match_rate = 0.05`
  - `contains_match_rate = 0.10`

说明 direct-only 已明显抑制泄露，但仍有残余泄露与 sensitive-pattern hallucination，且 public retain 已明显受损。

### PACE Round2

- full private:
  - `target_exact_leak_rate = 0.0000`
  - `target_regex_leak_rate = 0.0000`
  - `sensitive_pattern_rate = 0.0000`
  - `safe_refusal_rate = 1.0000`
- 四类攻击 `direct / paraphrase / completion / roleplay` 全部达到：
  - leak `0`
  - sensitive pattern `0`
  - refusal `1.0`
- public:
  - `exact_match_rate = 0.00`
  - `contains_match_rate = 0.00`

当前最准确结论：

> PACE Round2 在当前 synthetic privacy setting 下能够将 residual leakage 与 sensitive-pattern hallucination 全部压到 0，但代价是 public knowledge 完全丢失，表现出明显的 over-refusal / over-editing。

## 12. 当前不要重复做的事

当前不应再重复：

- baseline
- LoRA 注入训练
- direct-only refusal edit

这些阶段已经足够清楚。

## 13. 当前最值得继续做的方向

后续方向需要和外部讨论后定，但当前仓库内已经足够明确的一点是：

- 下一阶段重点不再是“能不能 suppress leakage”
- 而是“如何降低 collateral damage，尤其是恢复 public retain”

在新 agent 没有得到新的方向决策前，不要继续随意扩展：

- native sensitive 新分支
- MEMIT baseline
- 真实 PII benchmark
- before/after 样例导出

除非用户明确要求。
