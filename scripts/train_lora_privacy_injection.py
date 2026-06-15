import argparse
import inspect
import json
import os
import random
import time
from pathlib import Path
import sys
from typing import Any, Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from easyeditor.models.lora import apply_lora_to_model
from easyeditor.models.lora.lora_hparams import LoRAHyperParams


LORA_SCOPE_TO_MODULES = {
    "attn_only": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "mlp_only": ["gate_proj", "up_proj", "down_proj"],
    "attn_mlp": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="复用 EasyEdit LoRA 实现，对 synthetic privacy facts 做 LoRA 注入训练。")
    parser.add_argument(
        "--train_data",
        default="artifacts/synthetic_privacy_data/lora_privacy_train.jsonl",
        type=str,
        help="LoRA 训练数据 jsonl 路径",
    )
    parser.add_argument(
        "--hparams",
        default="hparams/LoRA/qwen2.5-7b.yaml",
        type=str,
        help="LoRA hparams yaml 路径",
    )
    parser.add_argument("--model_path", required=True, type=str, help="本地 HuggingFace 模型目录")
    parser.add_argument(
        "--output_dir",
        default="outputs/lora_privacy_injection",
        type=str,
        help="LoRA adapter 输出目录",
    )
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument("--seed", default=42, type=int, help="随机种子")
    parser.add_argument("--max_records", default=0, type=int, help="若 > 0，则只训练前 N 条记录")
    parser.add_argument("--shuffle", action="store_true", help="训练前随机打乱记录顺序")
    parser.add_argument("--batch_size", default=0, type=int, help="若 > 0，则覆盖 hparams 的 batch_size")
    parser.add_argument(
        "--num_steps",
        default=0,
        type=int,
        help="若 > 0，则覆盖 hparams 的 num_steps；在当前 EasyEdit LoRA 实现里它表示 epoch 数，而不是 max_train_steps",
    )
    parser.add_argument("--rank", default=0, type=int, help="若 > 0，则覆盖 hparams 的 LoRA rank")
    parser.add_argument("--max_length", default=0, type=int, help="若 > 0，则覆盖 hparams 的 max_length")
    parser.add_argument("--lr", default=0.0, type=float, help="若 > 0，则覆盖 hparams 的 lr")
    parser.add_argument("--lora_alpha", default=0.0, type=float, help="若 > 0，则覆盖 hparams 的 lora_alpha")
    parser.add_argument("--max_grad_norm", default=1.0, type=float, help="梯度裁剪阈值，<=0 表示关闭")
    parser.add_argument("--adam_eps", default=1e-8, type=float, help="Adam epsilon")
    parser.add_argument("--disable_gradient_checkpointing", action="store_true", help="关闭 gradient checkpointing，增加显存占用")
    parser.add_argument(
        "--precision",
        choices=["auto", "bf16", "fp16", "fp32"],
        default="auto",
        help="训练精度；auto 会优先选择 bf16，再退回 fp16。",
    )
    parser.add_argument(
        "--attn_implementation",
        choices=["auto", "flash_attention_2", "sdpa", "eager"],
        default="auto",
        help="attention kernel 后端；auto 优先 flash_attention_2，不可用则退到 sdpa。",
    )
    parser.add_argument("--dataloader_num_workers", default=4, type=int, help="DataLoader worker 数")
    parser.add_argument("--prefetch_factor", default=4, type=int, help="DataLoader prefetch_factor")
    parser.add_argument("--disable_pin_memory", action="store_true", help="关闭 pin_memory")
    parser.add_argument("--disable_persistent_workers", action="store_true", help="关闭 persistent_workers")
    parser.add_argument("--group_by_length", action="store_true", help="按样本长度分桶，减少 padding 浪费")
    parser.add_argument("--benchmark_steps", default=0, type=int, help="若 >0，则只跑前 N 个训练 step，用于吞吐 benchmark")
    parser.add_argument("--log_interval", default=10, type=int, help="每隔多少个 step 更新一次进度后缀")
    parser.add_argument(
        "--lora_scope",
        choices=["attn_only", "mlp_only", "attn_mlp"],
        default=None,
        help="使用预设 target modules。若提供，则优先于 --target_modules。",
    )
    parser.add_argument(
        "--target_modules",
        nargs="*",
        default=None,
        help="若提供，则覆盖 hparams 的 target_modules，例如 q_proj k_proj v_proj o_proj",
    )
    return parser.parse_args()


def load_train_records(path_str: str) -> List[Dict[str, Any]]:
    path = Path(path_str)
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def apply_hparam_overrides(hparams: LoRAHyperParams, args: argparse.Namespace) -> LoRAHyperParams:
    if args.batch_size > 0:
        hparams.batch_size = args.batch_size
    if args.num_steps > 0:
        hparams.num_steps = args.num_steps
    if args.rank > 0:
        hparams.rank = args.rank
    if args.max_length > 0:
        hparams.max_length = args.max_length
    if args.lr > 0:
        hparams.lr = args.lr
    if args.lora_alpha > 0:
        hparams.lora_alpha = args.lora_alpha
    if args.lora_scope:
        hparams.target_modules = list(LORA_SCOPE_TO_MODULES[args.lora_scope])
    elif args.target_modules:
        hparams.target_modules = list(args.target_modules)
    hparams.max_grad_norm = args.max_grad_norm
    hparams.adam_eps = args.adam_eps
    hparams.use_gradient_checkpointing = not args.disable_gradient_checkpointing
    hparams.seed = args.seed
    hparams.precision = args.precision
    hparams.attn_implementation = args.attn_implementation
    hparams.dataloader_num_workers = args.dataloader_num_workers
    hparams.prefetch_factor = args.prefetch_factor
    hparams.pin_memory = not args.disable_pin_memory
    hparams.persistent_workers = not args.disable_persistent_workers
    hparams.group_by_length = args.group_by_length
    hparams.benchmark_steps = args.benchmark_steps
    hparams.log_interval = args.log_interval
    return hparams


def infer_lora_scope(target_modules: List[str]) -> str:
    for scope, modules in LORA_SCOPE_TO_MODULES.items():
        if list(target_modules) == modules:
            return scope
    return "custom"


def resolve_precision(args: argparse.Namespace) -> tuple[torch.dtype, str]:
    if args.precision == "bf16":
        return torch.bfloat16, "bf16"
    if args.precision == "fp16":
        return torch.float16, "fp16"
    if args.precision == "fp32":
        return torch.float32, "fp32"
    if torch.cuda.is_bf16_supported():
        return torch.bfloat16, "bf16"
    return torch.float16, "fp16"


def resolve_attn_implementation(raw_value: str) -> str:
    if raw_value != "auto":
        return raw_value
    try:
        import flash_attn  # noqa: F401
        return "flash_attention_2"
    except Exception:
        return "sdpa"


def supports_fused_adam() -> bool:
    try:
        return "fused" in inspect.signature(torch.optim.Adam).parameters
    except Exception:
        return False


def main() -> int:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("LoRA 注入训练需要 GPU 环境。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    records = load_train_records(args.train_data)
    if args.shuffle:
        random.shuffle(records)
    if args.max_records > 0:
        records = records[:args.max_records]
    if not records:
        raise ValueError("训练数据为空。")

    hparams = LoRAHyperParams.from_hparams(args.hparams)
    hparams.model_name = args.model_path
    hparams.device = int(args.device)
    hparams = apply_hparam_overrides(hparams, args)
    if args.lr <= 0 and hparams.lr > 5e-4:
        print(f"Auto lowering lr from {hparams.lr} to 5e-4 for stability.")
        hparams.lr = 5e-4

    resolved_dtype, precision_name = resolve_precision(args)
    resolved_attn_impl = resolve_attn_implementation(args.attn_implementation)

    device = f"cuda:{args.device}"
    model_load_kwargs: Dict[str, Any] = {
        "torch_dtype": resolved_dtype,
    }
    if resolved_attn_impl:
        model_load_kwargs["attn_implementation"] = resolved_attn_impl

    model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_load_kwargs).to(device)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if tokenizer.padding_side != "right":
        tokenizer.padding_side = "right"

    requests = [
        {
            "prompt": record["prompt"],
            "target_new": record["target"],
            "subject": record["name"],
        }
        for record in records
    ]

    train_start = time.perf_counter()
    edited_model, lora_result = apply_lora_to_model(
        model=model,
        tok=tokenizer,
        requests=requests,
        hparams=hparams,
        copy=False,
        keep_original_weight=False,
    )
    train_stats = lora_result.get("train_stats", {}) if isinstance(lora_result, dict) else {}
    total_train_time = time.perf_counter() - train_start

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    edited_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    manifest = {
        "train_data": args.train_data,
        "hparams": args.hparams,
        "model_path": args.model_path,
        "output_dir": str(output_dir),
        "num_records": len(records),
        "device": int(args.device),
        "seed": args.seed,
        "max_records": args.max_records,
        "shuffle": args.shuffle,
        "resolved_hparams": {
            "batch_size": hparams.batch_size,
            "num_steps": hparams.num_steps,
            "rank": hparams.rank,
            "max_length": hparams.max_length,
            "lr": hparams.lr,
            "lora_alpha": hparams.lora_alpha,
            "lora_scope": infer_lora_scope(hparams.target_modules),
            "target_modules": hparams.target_modules,
            "max_grad_norm": hparams.max_grad_norm,
            "adam_eps": hparams.adam_eps,
            "use_gradient_checkpointing": hparams.use_gradient_checkpointing,
            "precision": precision_name,
            "attn_implementation": resolved_attn_impl,
            "dataloader_num_workers": hparams.dataloader_num_workers,
            "prefetch_factor": hparams.prefetch_factor,
            "pin_memory": hparams.pin_memory,
            "persistent_workers": hparams.persistent_workers,
            "group_by_length": hparams.group_by_length,
            "benchmark_steps": hparams.benchmark_steps,
            "log_interval": hparams.log_interval,
            "tf32": {
                "matmul": torch.backends.cuda.matmul.allow_tf32,
                "cudnn": torch.backends.cudnn.allow_tf32,
            },
        },
        "train_stats": train_stats,
        "total_train_time_sec": total_train_time,
    }
    with (output_dir / "training_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"train_data: {args.train_data}")
    print(f"model_path: {args.model_path}")
    print(f"num_records: {len(records)}")
    print(f"batch_size: {hparams.batch_size}")
    print(f"epochs: {hparams.num_steps}")
    print(f"rank: {hparams.rank}")
    print(f"lr: {hparams.lr}")
    print(f"precision: {precision_name}")
    print(f"attn_implementation: {resolved_attn_impl}")
    print(f"lora_scope: {infer_lora_scope(hparams.target_modules)}")
    print(f"target_modules: {hparams.target_modules}")
    print(f"max_grad_norm: {hparams.max_grad_norm}")
    print(f"use_gradient_checkpointing: {hparams.use_gradient_checkpointing}")
    print(f"dataloader_num_workers: {hparams.dataloader_num_workers}")
    print(f"pin_memory: {hparams.pin_memory}")
    print(f"persistent_workers: {hparams.persistent_workers}")
    print(f"group_by_length: {hparams.group_by_length}")
    print(f"benchmark_steps: {hparams.benchmark_steps}")
    if train_stats:
        print(f"avg_step_time_sec: {train_stats.get('avg_step_time_sec', 0.0):.4f}")
        print(f"samples_per_sec: {train_stats.get('samples_per_sec', 0.0):.4f}")
        print(f"tokens_per_sec: {train_stats.get('tokens_per_sec', 0.0):.4f}")
        print(f"padding_ratio: {train_stats.get('padding_ratio', 0.0):.4f}")
        print(f"max_gpu_memory_gb: {train_stats.get('max_gpu_memory_gb', 0.0):.2f}")
    print(f"adapter_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
