# EasyEdit 跨设备交接说明

本文档面向新的 agent、换设备后的本地开发环境，以及重新创建的服务器实例。目标是让新会话能够快速接上当前进度，不需要依赖旧对话历史。

## 1. 当前项目阶段

当前阶段已经不是“阅读仓库”阶段，而是“在已经打通的单条编辑链路上继续分析和扩展”阶段。

已完成的关键点：

- EasyEdit 仓库主入口已确认
- 本地辅助脚本和部署文档已补齐
- AutoDL 上的 `Qwen2.5-7B + ROME` 单条编辑已经真实跑通一次
- 结果文件已经回收到仓库内 `artifacts/`

## 2. 本地与服务器分工

推荐分工固定如下：

- 本地 Windows / macOS：
  - 读代码
  - 改脚本和文档
  - 本地提交到 GitHub
- Linux 服务器：
  - 拉最新代码
  - 准备模型
  - 跑实验
  - 保存输出

不要把服务器当成长期手工开发主机。这样做会增加代码回收成本，也不利于多设备切换。

## 3. AutoDL 路径约定

当前约定路径：

```text
/root/autodl-tmp/
├── projects/
│   └── EasyEdit/
├── models/
│   └── Qwen2.5-7B/
├── hf_cache/
│   ├── hf/
│   ├── transformers/
│   └── datasets/
├── nltk_data/
└── outputs/
    └── easyedit/
```

说明：

- `/root/autodl-tmp` 是数据盘，适合存代码、模型、缓存、输出。
- `/` 是系统盘，适合保存镜像里的基础环境，比如 `mihomo`、conda、SSH 配置等。

## 4. AutoDL 旧镜像里的已知基础设施

当前旧镜像里已知存在：

- `conda`
- `mihomo`
- GitHub SSH key

已知路径：

- `mihomo` 二进制：`/root/mihomo/mihomo`
- `mihomo` 启动脚本：`/root/start_mihomo.sh`
- `mihomo` 主配置：`/root/config.yaml`
- `mihomo` geo 数据：`/root/.config/mihomo`
- conda 根目录：`/root/miniconda3`

如果换了新镜像，需要重新确认这些东西是不是还在。

## 5. 代理启动与联网

当前服务器访问外网通常需要先启动 `mihomo`：

```bash
bash /root/start_mihomo.sh
```

然后设置代理变量：

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

如果需要自检：

```bash
curl -I https://www.google.com
```

## 6. 服务器 Python 环境

当前实验环境名：

```bash
easyedit
```

进入方式：

```bash
conda activate easyedit
```

运行前通常还需要：

```bash
export PYTHONPATH=/root/autodl-tmp/projects/EasyEdit:$PYTHONPATH
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export NLTK_DATA=/root/autodl-tmp/nltk_data
```

其中：

- `PYTHONPATH` 是为了让本地源码形式的 `easyeditor` 能被导入
- `NLTK_DATA` 是为了避免 fluency 评估时再次报 `punkt` / `punkt_tab` 缺失

## 7. 模型下载与修补经验

当前实际使用的模型是：

```text
Qwen2.5-7B
```

模型目录：

```text
/root/autodl-tmp/models/Qwen2.5-7B
```

注意事项：

1. ModelScope 下载的目录最初不完整。
2. 权重分片虽然齐全，但 tokenizer 文件不足，导致 `AutoTokenizer.from_pretrained(...)` 报错。
3. 后续从 Hugging Face 官方仓库补了：
   - `tokenizer.json`
   - `vocab.json`

因此以后如果重新下载模型，不要只检查：

- `config.json`
- `*.safetensors`

还要检查 tokenizer 相关文件是否能支持 `AutoTokenizer.from_pretrained(...)`。

## 8. 当前已知关键脚本

### `scripts/check_easyedit_env.py`

用途：

- 检查 Python / torch / transformers / easyeditor
- 检查 GPU
- 检查 hparams
- 检查模型目录是否完整

### `scripts/run_single_edit.py`

用途：

- 运行单条编辑
- 支持 `ROME / MEMIT / FT`
- 打印编辑前后生成结果
- 打印 top-k next token

新增参数：

- `--generation_prompt`
- `--top_k`
- `--disable_fluency_eval`

当前还新增了 token-level probe，用来观察：

- `P(original_answer | prompt)`
- `P(target_new | prompt)`
- 编辑前后概率变化
- 编辑前后 rank 变化

### `scripts/smoke_single_edit.py`

目前是兼容壳，内部转调 `run_single_edit.py`。主入口应优先使用 `run_single_edit.py`。

### `scripts/generate_synthetic_privacy_data.py`

用途：

- 生成小规模合成隐私数据
- 输出 `people` 和 `flat_cases` 两种结构
- 为后续 LoRA 注入、ROME 编辑和泄露评测提供统一数据源

### `scripts/evaluate_privacy_leakage.py`

用途：

- 对手机号、邮箱做 exact/regex 泄露检测
- 生成最小可复用的泄露率统计
- 为后续攻击问法测试和闭环再编辑提供基础评测

## 9. 当前已知成功命令

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

关闭 fluency 的版本：

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

## 10. 当前最重要的实验结论

已确认：

- ROME 真正执行了参数更新
- `rewrite_acc` 从 `0.0` 提升到 `1.0`
- EasyEdit 原始单条编辑 pipeline 已经真实跑通

但也观察到：

- 自由生成结果前后仍然都是 `Paris, France...`
- top-k next token 里 `' Paris'` 仍然排第一，变化非常小

因此下一阶段的重点不是继续修环境，而是研究：

- EasyEdit 内部评测为什么显示成功
- 为什么自由生成没有同步体现
- 如何设计更合适的展示 prompt、probe 或 token-level 观测方式

## 11. 当前已知结果文件

当前仓库内已有结果：

```text
artifacts/run_20260613_qwen25_7b_rome/rome_single_edit_result.json
```

这个文件可以作为“单条编辑 pipeline 已经跑通”的直接证据。

## 12. 服务器同步约定

本地修改后，建议统一按下面流程同步：

### 本地

```bash
git add <files>
git commit -m "<message>"
git push
```

### 服务器

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull
```

然后再进入环境复跑。
