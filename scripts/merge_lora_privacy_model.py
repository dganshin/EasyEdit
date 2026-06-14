import argparse
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 base model 与 LoRA adapter merge 为一个独立 HF 模型目录。")
    parser.add_argument("--model_path", required=True, type=str, help="base model 目录")
    parser.add_argument("--lora_adapter_path", required=True, type=str, help="LoRA adapter 目录")
    parser.add_argument("--output_dir", required=True, type=str, help="merge 后模型输出目录")
    return parser.parse_args()


def resolve_tokenizer_source(model_path: str, lora_adapter_path: str) -> str:
    adapter_dir = Path(lora_adapter_path)
    tokenizer_markers = [
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
    ]
    if any((adapter_dir / marker).exists() for marker in tokenizer_markers):
        return lora_adapter_path
    return model_path


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    peft_model = PeftModel.from_pretrained(base_model, args.lora_adapter_path)
    merged_model = peft_model.merge_and_unload()

    tokenizer_source = resolve_tokenizer_source(args.model_path, args.lora_adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)

    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    manifest = {
        "model_path": args.model_path,
        "lora_adapter_path": args.lora_adapter_path,
        "output_dir": str(output_dir),
    }
    with (output_dir / "merge_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"model_path: {args.model_path}")
    print(f"lora_adapter_path: {args.lora_adapter_path}")
    print(f"merged_model_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
