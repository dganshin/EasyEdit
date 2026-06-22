# 基于模型编辑的大语言模型隐私知识清洗与保护研究

## 摘要

大语言模型在预训练与后训练过程中可能记忆并输出个人隐私信息。本文围绕 Privacy Knowledge Sanitization via Model Editing 构建研究型课程项目：首先设计包含 private/public 对照的 synthetic privacy benchmark；然后使用 MLP-only LoRA 向 Qwen2.5-7B 注入可控隐私记忆，形成 merged leakage model；进一步基于 EasyEdit 框架实现 ROME、MEMIT 与 PACE（Privacy-Aware Closed-loop Editing）等编辑策略，并从 private leakage、public retain、over-refusal 与 privacy-utility trade-off 四个维度进行审计。实验结果表明，现有编辑策略在隐私压制和公开知识保持之间存在明显权衡：ROME 能降低部分泄露但损伤公开知识，MEMIT 保留公开知识较好但隐私压制不足，PACE 能显著压低泄露但带来严重过度拒答。基于上述发现，本文进一步提出 CAPE-v0（Collateral-Aware Privacy Editing）作为副作用感知的请求选择方案，为后续降低 collateral damage 提供改进方向。

关键词：大语言模型；模型编辑；隐私知识清洗；知识保持；过度拒答；ROME；MEMIT；PACE

## 主结果表

| 方法 | Private Value Contains | PII-format Regex | Sensitive Pattern | Private Refusal | Public Contains | Public Refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pre leakage model | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 | 0.0000 |
| ROME direct-only | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 | 0.4679 |
| MEMIT direct-only | 0.8140 | 0.5993 | 0.8853 | 0.1950 | 0.8472 | 0.1484 |
| PACE target_only | 0.0000 | 0.0000 | 0.0167 | 0.9930 | 0.0032 | 0.9675 |
| PACE max1_per_case | 0.0003 | 0.0003 | 0.0200 | 0.9870 | 0.0099 | 0.9611 |
| PACE max2_per_person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 | 0.8115 |

## CAPE-v0 当前选择结果

CAPE-v0 在 `B=1, tau=0.5` 设置下，从 2569 个 residual leakage candidates 中选出 60 条 round2 re-edit requests。其中 public-anchor blocking 跳过 815 条，per-person budget 跳过 1694 条。该结果目前仅代表请求选择阶段，不代表 CAPE 模型编辑实验已经完成。
