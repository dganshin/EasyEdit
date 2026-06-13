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

其中 `run_single_edit.py` 已经扩展支持：

- `--generation_prompt`
- `--top_k`
- `--disable_fluency_eval`

这些增强是为了更清楚地观察“内部指标成功但自由生成不明显变化”的情况。

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
- `docs/SESSION_HANDOFF.md`
