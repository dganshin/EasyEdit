# AutoDL 上部署 EasyEdit 单条编辑

本文目标是先打通 EasyEdit 原始单条编辑 pipeline，不下载模型、不提交大文件、不改核心算法。

## 1. 推荐目录结构

建议把代码、模型、缓存分开，并尽量把大文件放数据盘 `/root/autodl-tmp`：

```text
/root/autodl-tmp/
├── projects/
│   ├── EasyEdit/
│   ├── KnowLM/
│   └── knowledge-sanitization/
├── models/
│   └── llama-hf/
│       └── 7B/
├── hf_cache/
│   ├── hf/
│   ├── transformers/
│   └── datasets/
└── outputs/
    └── easyedit/
```

推荐路径：

- 代码仓库：`/root/autodl-tmp/projects/EasyEdit`
- 模型目录：`/root/autodl-tmp/models`
- 缓存目录：`/root/autodl-tmp/hf_cache`
- 输出目录：`/root/autodl-tmp/outputs/easyedit`

## 2. 克隆代码

如果你已经把本地改好的 EasyEdit 推到 GitHub：

```bash
cd /root/autodl-tmp/projects
git clone <你的 EasyEdit 仓库地址>
cd EasyEdit
```

如果服务器上已经有仓库：

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull
```

## 3. 创建 conda 环境

```bash
conda create -n easyedit python=3.10 -y
conda activate easyedit
cd /root/autodl-tmp/projects/EasyEdit
pip install -r requirements.txt
```

如果 `fairscale`、`bitsandbytes`、`flash-attn` 一类包有编译或 CUDA 兼容问题，先不要额外加包，先按仓库默认依赖打通最小单条编辑。

## 4. 设置缓存目录

```bash
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$HF_DATASETS_CACHE"
mkdir -p /root/autodl-tmp/outputs/easyedit
```

如果你希望每次登录自动生效，可以把这几行写进 `~/.bashrc`。

## 5. 手动准备模型

本仓库不会替你下载模型。你需要自己把模型放进：

```text
/root/autodl-tmp/models/<model_name>
```

例如：

- `/root/autodl-tmp/models/llama-hf/7B`
- `/root/autodl-tmp/models/gpt2-xl`
- `/root/autodl-tmp/models/tinyllama`

### 5.1 模型目录至少应包含

- `config.json`
- tokenizer 文件中的至少一部分：
  - `tokenizer.json`
  - 或 `tokenizer.model`
  - 或 `tokenizer_config.json + vocab/merges`
- 权重文件中的至少一种：
  - `*.safetensors`
  - `*.bin`
  - `*.pt`
  - `*.pth`
  - 或对应的分片索引文件

### 5.2 如果沿用已有 LLaMA-7B

请先确认它是 HuggingFace 可直接 `from_pretrained()` 的目录格式，而不是原始分片或非 HF 转换格式。

## 6. 先做环境与模型目录检查

这一步不真正执行编辑，适合你在开卡前或刚开卡时快速确认环境。

```bash
cd /root/autodl-tmp/projects/EasyEdit
python scripts/check_easyedit_env.py \
  --method ROME \
  --hparams hparams/ROME/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B
```

如果你想先检查小模型：

```bash
python scripts/check_easyedit_env.py \
  --method ROME \
  --hparams hparams/ROME/gpt2-xl.yaml \
  --model_path /root/autodl-tmp/models/gpt2-xl
```

## 7. 运行单条编辑

主脚本使用 `scripts/run_single_edit.py`。  
`scripts/smoke_single_edit.py` 仅保留为兼容入口，内部直接转调 `run_single_edit.py`。

### 7.1 当前推荐顺序

- 你最终目标如果是 `LLaMA-7B`，可以直接拿它做第一轮调试。
- 但要明确：你截图里这台实例当前显示 `GPU: No devices were found`、`内存: 2GB`，这不是可执行编辑的目标实例。
- 真正调试时，请切到你说的 `48GB` 显存实例后再跑下面命令。

如果你后面换更现代的模型，再补对应 hparams 或模板。

### 7.2 直接跑已有 LLaMA-7B

你当前服务器上已经存在：

- 模型目录：`/root/autodl-tmp/models/llama-hf/7B`

示例：

```bash
python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/llama7b_rome \
  --prompt "The Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome"
```

FT-L 示例：

```bash
python scripts/run_single_edit.py \
  --method FT \
  --hparams hparams/FT/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/llama7b_ft \
  --prompt "The Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome"
```

### 7.3 小模型只作为备用排障

更小模型仍然可以用于定位“环境错了 / hparams 错了 / 路径错了”这种基础问题，但它不是本文档主推荐路径：

- `gpt2-xl`
- 如果你自己另外准备了更小且兼容的 causal LM，也可以先试

示例：

```bash
python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/gpt2-xl.yaml \
  --model_path /root/autodl-tmp/models/gpt2-xl \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/gpt2xl_rome \
  --prompt "The Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome"
```

FT-L 示例：

```bash
python scripts/run_single_edit.py \
  --method FT \
  --hparams hparams/FT/gpt2-xl.yaml \
  --model_path /root/autodl-tmp/models/gpt2-xl \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/gpt2xl_ft \
  --prompt "The Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome"
```

## 8. 关于显存的实际建议

这里要实事求是，不拿“小玩具结果”糊弄你：

- 你既然准备用 `48GB` 显存实例，第一优先级就该直接尝试现有 `LLaMA-7B`。
- `ROME` 和 `FT-L` 都值得先试，`FT-L` 通常更稳。
- `MEMIT` 不是“只要显存够就行”，它还依赖统计量文件；没统计量时不能算真正跑通。
- 如果 `LLaMA-7B + ROME` 失败，再回退到 `gpt2-xl` 做排障，而不是把小模型当最终交差结果。

## 9. MEMIT 的额外注意事项

`MEMIT` 默认需要 `mom2_adjustment: true`，并依赖统计量目录 `stats_dir` 下的 `wikipedia_stats` 类文件。

这意味着：

- 只靠模型目录本身不够
- 你还需要手动准备或复用仓库要求的统计量文件
- 如果这些文件没准备好，`MEMIT` 不能算真正打通

因此建议顺序：

1. 先用 `ROME` 或 `FT-L` 跑通单条编辑
2. 再补 `MEMIT` 的统计量依赖

## 10. 如何切换模型路径和 hparams

本次新增脚本采用：

- `--hparams` 指向现有 yaml
- `--model_path` 在运行时覆盖 `hparams.model_name`
- 如果该方法类有 `tokenizer_name`，也同步覆盖

因此不要把你服务器私有路径直接写回仓库 yaml。

正确方式：

```bash
python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/run1
```

## 11. 常见 OOM 处理

- 优先改用更小模型先打通，例如 `gpt2-xl`
- 先尝试 `FT-L`，再尝试 `ROME`
- 最后再碰 `MEMIT`
- 保证单卡只跑一个任务
- 运行前清理其他 Python 进程和显存占用
- 必要时先重启实例再开跑

如果是 `MEMIT` 在 7B 上 OOM，不建议盲目硬顶，因为你最终还要保证结果和论文设定可解释、可复现。

## 12. 结果文件

单条编辑脚本会输出一个 JSON，例如：

```text
/root/autodl-tmp/outputs/easyedit/llama7b_rome/rome_single_edit_result.json
```

其中包含：

- 编辑方法
- 模型路径
- prompt / subject / ground_truth / target_new
- 编辑前生成
- 编辑后生成
- EasyEdit 返回的 metrics

## 13. 推荐执行顺序

```bash
conda activate easyedit
cd /root/autodl-tmp/projects/EasyEdit

export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets

python scripts/check_easyedit_env.py \
  --method ROME \
  --hparams hparams/ROME/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B

python scripts/run_single_edit.py \
  --method ROME \
  --hparams hparams/ROME/llama-7b.yaml \
  --model_path /root/autodl-tmp/models/llama-hf/7B \
  --device 0 \
  --output_dir /root/autodl-tmp/outputs/easyedit/llama7b_rome \
  --prompt "The Eiffel Tower is located in" \
  --subject "Eiffel Tower" \
  --ground_truth "Paris" \
  --target_new "Rome"
```
