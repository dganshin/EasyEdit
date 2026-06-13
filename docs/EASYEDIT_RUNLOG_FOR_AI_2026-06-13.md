# EasyEdit 运行记录（给后续 AI / 技术讨论用）

## 1. 当前目标

当前阶段的目标不是做隐私清洗，而是先把原始 EasyEdit 的单条模型编辑 pipeline 打通，确保：

- 本地仓库结构清楚
- AutoDL 环境可复现
- 至少有一种标准方法能在真实模型上完成一次编辑

这一步完成之后，再在此基础上推进知识清洗、隐私相关任务。

## 2. 本地仓库已经做过的改动

未改动 EasyEdit 核心算法逻辑，主要补充的是外层脚本和文档：

- `scripts/check_easyedit_env.py`
- `scripts/run_single_edit.py`
- `scripts/smoke_single_edit.py`
- `docs/AUTODL_EASYEDIT_SETUP.md`
- `.gitignore`

后续又对 `scripts/run_single_edit.py` 做了增强，但仍然没有改动核心编辑实现。新增能力主要是：

- `--generation_prompt`
- `--top_k`
- `--disable_fluency_eval`

目的是解释“内部指标成功，但自由生成不明显变化”的情况。

## 3. 服务器环境和目录

最终采用的是 AutoDL 旧镜像，因为其中已经有 `mihomo` 和基础 conda 环境，可以省去重新配置代理的时间。

约定目录：

- 代码：`/root/autodl-tmp/projects/EasyEdit`
- 模型：`/root/autodl-tmp/models/Qwen2.5-7B`
- HF 缓存：`/root/autodl-tmp/hf_cache/...`
- 输出：`/root/autodl-tmp/outputs/easyedit/...`
- NLTK 数据：`/root/autodl-tmp/nltk_data`

常用环境变量：

```bash
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

## 4. 模型选择与下载过程

最开始没有继续沿用官方 LLaMA 路线，原因是权限和下载链路都比较麻烦，因此先换成了 `Qwen2.5-7B`。仓库里已有：

- `hparams/ROME/qwen2.5-7b.yaml`
- `hparams/MEMIT/qwen2.5-7b.yaml`
- `hparams/FT/qwen2.5-7b.yaml`

这使得它比较适合当前阶段用来打通 pipeline。

模型先通过 ModelScope 下载到了：

`/root/autodl-tmp/models/Qwen2.5-7B`

但 ModelScope 下来的目录不完整，缺 tokenizer 关键文件，最初只有：

- `merges.txt`
- `tokenizer_config.json`

然后导致：

```python
AutoTokenizer.from_pretrained(path, trust_remote_code=True)
```

报错 `vocab_file is None`。

后续通过 `wget` 从 Hugging Face 官方仓库单独补齐了小文件：

- `tokenizer.json`
- `vocab.json`

补完之后 tokenizer 才能正常加载。

## 5. 环境坑点

服务器上实际遇到的坑点主要有这些：

1. `easyeditor` 不能直接 import  
   这不是算法问题，而是仓库源码路径没有进入 Python 搜索路径，需要显式设置：

```bash
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
```

2. `easyeditor/__init__.py` 全量导入过重  
   即便只跑文本编辑，也会把多模态和 API 相关模块一起导入，因此还额外补了：

- `qwen-vl-utils`
- `zhipuai`
- `protobuf`

3. NLTK 数据缺失  
   最终还补了：

- `punkt`
- `punkt_tab`

否则 fluency 评估阶段会报错。

## 6. 真正跑通的命令

最后有效跑通的命令是：

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

后面还又跑了一次：

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

## 7. 真实运行现象

从日志看，`ROME` 的内部流程确实执行了，不是脚本空转：

- 模型分片加载成功
- `BaseEditor` 初始化成功
- `u/v` 优化过程完整执行
- 实际写入了：
  - `model.layers.5.mlp.down_proj.weight`

EasyEdit 内部输出的核心指标是：

- `pre rewrite_acc = 0.0`
- `post rewrite_acc = 1.0`

所以可以判断：

**原始 EasyEdit 的 ROME 单条编辑链路已经真实跑通。**

## 8. 当前最值得注意的问题

虽然内部指标成功了，但从增强后的脚本输出看：

- `pre_answer` 和 `post_answer` 仍然都是  
  `Paris, France. It is a wrought iron lattice tower on the Champ de Mars`
- `pre_topk_next_token` 和 `post_topk_next_token` 也几乎不变
- 第一名 token 仍然是 `' Paris'`

这说明：

1. EasyEdit 内部评测口径下，编辑目标已经命中。
2. 但当前用于展示的自由生成和 next-token 观测，还没有体现出直观的 “Rome 替代 Paris”。

当前更倾向的解释是：

- EasyEdit 的 `rewrite_acc` 更接近内部评测 token 命中或 teacher-forcing 风格结果
- 而当前 `generation_prompt` 下的自由生成，仍被原始知识和续写惯性强烈锚定

## 9. 当前阶段能下的结论

已经可以比较稳地说：

- EasyEdit 仓库结构已经摸清
- 本地改动和服务器同步流程已经顺了
- AutoDL 上真实环境已打通
- `Qwen2.5-7B + ROME` 单条编辑 pipeline 已成功运行

但还不能草率地说：

- “模型肉眼上已经完全改成新知识”

更准确的说法应该是：

> 原始 EasyEdit 的单条知识编辑链路已经跑通，内部编辑指标显示目标编辑成功；但目前用于展示的自由生成结果仍未明显变化，后续需要进一步优化展示 prompt 或改进观测方式。

## 10. 下一步建议

后面如果继续和另一个 AI 讨论，比较有价值的问题是：

1. 为什么 `rewrite_acc=1.0`，但自由生成和 top-k 仍几乎不变？
2. 是否应该直接打印 `" Rome"` 和 `" Paris"` 的目标 token 概率变化，而不是只看 top-k？
3. 是否应该改成更贴近 EasyEdit 内部评测形式的探针，而不是现在的长文本生成？
4. `Qwen2.5-7B` 的这套 hparams 是否本身更偏“内部命中”而不是“显式生成改写”？

## 11. 已回收的结果文件

当前已经带回本地仓库的结果文件在：

`artifacts/run_20260613_qwen25_7b_rome/rome_single_edit_result.json`

这个文件可以作为“已经完成真实单条编辑跑通”的直接证据。
