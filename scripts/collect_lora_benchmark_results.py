import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从多份 training_manifest.json 汇总 LoRA 吞吐对比表。")
    parser.add_argument("--manifests", nargs="+", required=True, type=str, help="多份 training_manifest.json 路径")
    parser.add_argument("--output_path", default=None, type=str, help="可选，输出 json 路径")
    return parser.parse_args()


def load_json(path_str: str) -> Dict[str, Any]:
    with Path(path_str).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def row_from_manifest(path_str: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    hp = payload.get("resolved_hparams", {})
    stats = payload.get("train_stats", {})
    dataset_stats = stats.get("dataset_stats", {})
    return {
        "manifest": path_str,
        "config": Path(path_str).parent.name,
        "micro_batch": hp.get("batch_size"),
        "grad_accum": 1,
        "seq_len": hp.get("max_length"),
        "workers": hp.get("dataloader_num_workers"),
        "precision": hp.get("precision"),
        "attn": hp.get("attn_implementation"),
        "checkpointing": hp.get("use_gradient_checkpointing"),
        "step_time_sec": stats.get("avg_step_time_sec"),
        "samples_per_sec": stats.get("samples_per_sec"),
        "tokens_per_sec": stats.get("tokens_per_sec"),
        "padding_ratio": stats.get("padding_ratio"),
        "max_mem_gb": stats.get("max_gpu_memory_gb"),
        "avg_seq_len": dataset_stats.get("avg_sequence_length"),
        "max_seq_observed": dataset_stats.get("max_sequence_length_observed"),
    }


def build_markdown(rows: List[Dict[str, Any]]) -> str:
    header = "| 配置 | micro batch | grad accum | seq len | workers | bf16/fp16 | flash/sdpa | checkpointing | step time | tokens/s | samples/s | padding ratio | max mem |"
    sep = "|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|"
    lines = [header, sep]
    for row in rows:
        lines.append(
            "| {config} | {micro_batch} | {grad_accum} | {seq_len} | {workers} | {precision} | {attn} | {checkpointing} | {step_time_sec:.4f} | {tokens_per_sec:.1f} | {samples_per_sec:.2f} | {padding_ratio:.4f} | {max_mem_gb:.2f} |".format(
                config=row["config"],
                micro_batch=row["micro_batch"],
                grad_accum=row["grad_accum"],
                seq_len=row["seq_len"],
                workers=row["workers"],
                precision=row["precision"],
                attn=row["attn"],
                checkpointing=row["checkpointing"],
                step_time_sec=float(row.get("step_time_sec") or 0.0),
                tokens_per_sec=float(row.get("tokens_per_sec") or 0.0),
                samples_per_sec=float(row.get("samples_per_sec") or 0.0),
                padding_ratio=float(row.get("padding_ratio") or 0.0),
                max_mem_gb=float(row.get("max_mem_gb") or 0.0),
            )
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = [row_from_manifest(path, load_json(path)) for path in args.manifests]
    payload = {
        "rows": rows,
        "markdown_table": build_markdown(rows),
    }
    print(payload["markdown_table"])
    if args.output_path:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"output_json: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
