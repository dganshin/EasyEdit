# Public Benchmark Interpretation Guide

Last updated: 2026-06-23  
Related commit: this commit (see `git log --oneline -1`)  
Current completed artifacts: public benchmark scope, Qwen-only interpretation rule, GPT-J/IKE stop rationale  
Current running artifacts: Qwen public 200-case benchmark  
Pending server artifacts: Qwen CounterFact/zsRE wrapper summaries  
Completed local writing tasks: public benchmark scope and wording rules  
Next action: fill Qwen public table and keep it separate from privacy metrics  
Risk / fallback: public benchmark cannot prove privacy sanitization; use it only as closed-loop wrapper transfer validation.

## 定位

CounterFact 和 zsRE 不是 PII 清洗数据集，不能用于证明隐私清洗成功。它们在本文中的作用是验证 closed-loop request selection wrapper 是否能迁移到公开 factual editing 场景。

## 主表范围

主表只使用 Qwen2.5-7B：

```text
CounterFact / zsRE
× ROME / FT / KN / ROME+PACE-Edit / ROME+CAPE-Edit
```

GPT-J 由于 KN coarse-neuron search 成本过高，不进入主表。IKE 因缺少 sentence-transformer 依赖，不作为必须 baseline。

## 指标

public benchmark 表使用：

- Reliability；
- Generalization；
- Locality；
- Failure count。

不要把 Private Value Contains、Public Refusal 等 synthetic privacy 指标混进 public benchmark 主表。

## 写法

可写：

> 公开 factual editing 结果用于检验闭环请求选择策略在非隐私场景下的迁移性和 locality 影响。

不可写：

> CounterFact/zsRE 证明本文方法能够清洗真实隐私知识。
