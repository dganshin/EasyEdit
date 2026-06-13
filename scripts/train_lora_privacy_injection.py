import argparse
import json
import random
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
    parser.add_argument("--num_steps", default=0, type=int, help="若 > 0，则覆盖 hparams 的 num_steps")
    parser.add_argument("--rank", default=0, type=int, help="若 > 0，则覆盖 hparams 的 LoRA rank")
    parser.add_argument("--max_length", default=0, type=int, help="若 > 0，则覆盖 hparams 的 max_length")
    parser.add_argument("--lr", default=0.0, type=float, help="若 > 0，则覆盖 hparams 的 lr")
    parser.add_argument("--lora_alpha", default=0.0, type=float, help="若 > 0，则覆盖 hparams 的 lora_alpha")
    parser.add_argument("--max_grad_norm", default=1.0, type=float, help="梯度裁剪阈值，<=0 表示关闭")
    parser.add_argument("--adam_eps", default=1e-8, type=float, help="Adam epsilon")
    parser.add_argument("--disable_gradient_checkpointing", action="store_true", help="关闭 gradient checkpointing，增加显存占用")
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
    if args.target_modules:
        hparams.target_modules = list(args.target_modules)
    hparams.max_grad_norm = args.max_grad_norm
    hparams.adam_eps = args.adam_eps
    hparams.use_gradient_checkpointing = not args.disable_gradient_checkpointing
    return hparams


def main() -> int:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("LoRA 注入训练需要 GPU 环境。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

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

    device = f"cuda:{args.device}"
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.float16,
    ).to(device)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if tokenizer.padding_side != "left":
        tokenizer.padding_side = "left"

    requests = [
        {
            "prompt": record["prompt"],
            "target_new": record["target"],
            "subject": record["name"],
        }
        for record in records
    ]

    edited_model, _ = apply_lora_to_model(
        model=model,
        tok=tokenizer,
        requests=requests,
        hparams=hparams,
        copy=False,
        keep_original_weight=False,
    )

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
            "target_modules": hparams.target_modules,
            "max_grad_norm": hparams.max_grad_norm,
            "adam_eps": hparams.adam_eps,
            "use_gradient_checkpointing": hparams.use_gradient_checkpointing,
        },
    }
    with (output_dir / "training_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"train_data: {args.train_data}")
    print(f"model_path: {args.model_path}")
    print(f"num_records: {len(records)}")
    print(f"batch_size: {hparams.batch_size}")
    print(f"num_steps: {hparams.num_steps}")
    print(f"rank: {hparams.rank}")
    print(f"lr: {hparams.lr}")
    print(f"target_modules: {hparams.target_modules}")
    print(f"max_grad_norm: {hparams.max_grad_norm}")
    print(f"use_gradient_checkpointing: {hparams.use_gradient_checkpointing}")
    print(f"adapter_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
