# Public Subset Prep Report

## Scope

本轮只构造 CounterFact 与 zsRE small subset，不运行全量 benchmark，不下载 The Pile/Enron 全量。

## Outputs

- CounterFact: `artifacts\public_benchmarks_20260622\counterfact_500.json`
- zsRE: `artifacts\public_benchmarks_20260622\zsre_500.json`
- Stats: `artifacts\public_benchmarks_20260622\public_subset_stats.json`

## Dataset Summary

| dataset | records | source | sha256 | dropped reasons |
| --- | ---: | --- | --- | --- |
| counterfact | 500 | `azhx/counterfact` | `addca976d4f0...` | `{}` |
| zsre | 500 | `wangzn2001/zsre/structured_zeroshot-dev-new_annotated_final.jsonl` | `d24310b9374e...` | `{'subject_not_in_prompt': 7, 'missing_subject': 53, 'missing_required_fields': 25}` |

## Field Mapping

- CounterFact: `requested_rewrite.prompt` + `subject` -> `prompt`; `target_new.str` -> `target_new`; `target_true.str` -> `ground_truth`; `paraphrase_prompts` -> `rephrase_prompt`。
- zsRE: `input` -> `prompt`; `alternatives[0]` -> `target_new`; `output[0].answer` -> `ground_truth`; `filtered_rephrases` -> `rephrase_prompt`; provenance title -> `subject`。
- CounterFact locality prompts lack explicit answers in the selected HF source, so they are marked for pre/post consistency rather than answer contains.

## Interpretation

CounterFact 是公开事实编辑 benchmark，zsRE 是问答式知识编辑 benchmark。二者不包含本文 synthetic PII 设置，不应与 privacy leakage 指标混成同一张主结果表。
