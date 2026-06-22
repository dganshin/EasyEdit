# GPT-J Instance Transfer Instructions

目标：新开一个空数据盘 AutoDL 实例，只下载 GPT-J-6B，并运行 CounterFact / zsRE 公开 benchmark 的 500 条 small subset。不要复制 Qwen 模型，不要复制旧 outputs，不要复制 HF cache。

## 1. 在实例 A 或本地生成迁移包

```bash
cd /root/autodl-tmp/projects/EasyEdit
git pull --ff-only
bash scripts/package_for_gptj_instance.sh
```

输出：

```text
/tmp/easyedit_gptj_instance_bundle.tar.gz
```

该包只包含代码、`scripts/`、`hparams/`、`easyeditor/`、CounterFact/zsRE 500 条 small subset 和必要说明，不包含模型、缓存和大输出。

## 2. 迁移方式 A：本地中转

从实例 A 拉到本地：

```bash
scp root@<INSTANCE_A_HOST>:/tmp/easyedit_gptj_instance_bundle.tar.gz .
```

再传到实例 B：

```bash
scp easyedit_gptj_instance_bundle.tar.gz root@<INSTANCE_B_HOST>:/root/autodl-tmp/
```

## 3. 迁移方式 B：AutoDL 文件管理或对象存储

如果两个实例之间不能直接互通，可以用 AutoDL 文件管理页面或对象存储中转：

1. 在实例 A 下载 `/tmp/easyedit_gptj_instance_bundle.tar.gz` 到本地。
2. 上传到实例 B 的 `/root/autodl-tmp/`。

## 4. 在实例 B 解压并运行

```bash
cd /root/autodl-tmp
tar -xzf easyedit_gptj_instance_bundle.tar.gz
cd /root/autodl-tmp/projects/EasyEdit

screen -S public_gptj_full
bash scripts/run_public_gptj_full.sh
```

退出 screen 但保持任务运行：

```text
Ctrl+A 然后 D
```

重新进入：

```bash
screen -r public_gptj_full
```

## 5. GPT-J 运行内容

脚本会自动：

1. 设置 conda、代理、HF cache、`PYTHONPATH`。
2. 检查 `/root/autodl-tmp/models/gpt-j-6B`。
3. 如果 GPT-J 不存在，使用 `EleutherAI/gpt-j-6b` 下载。
4. 下载后验证 `config.json`、`AutoConfig.from_pretrained`、`AutoTokenizer.from_pretrained`。
5. 验证失败则停止，不跑编辑。
6. 验证成功后运行：
   - CounterFact 500 × GPT-J × ROME / FT / KN / IKE
   - zsRE 500 × GPT-J × ROME / FT / KN / IKE
7. 汇总结果到：
   - `artifacts/public_benchmarks_20260622/public_editing_comparison_gptj.csv`
   - `artifacts/public_benchmarks_20260622/PUBLIC_EDITING_BASELINE_REPORT_GPTJ.md`

## 6. 可选 LLaMA-2 备用探测

默认不启用。只有 GPT-J 下载超过 2 小时仍失败时，才考虑：

```bash
DOWNLOAD_LLAMA_BACKUP=1 bash scripts/run_public_gptj_full.sh
```

默认备用源：

```text
NousResearch/Llama-2-7b-hf
```
