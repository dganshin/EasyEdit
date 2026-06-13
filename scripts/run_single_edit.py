import argparse
import json
from pathlib import Path
from typing import Any, Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from easyeditor import BaseEditor, FTHyperParams, MEMITHyperParams, ROMEHyperParams


METHOD_TO_HPARAMS = {
    "ROME": ROMEHyperParams,
    "MEMIT": MEMITHyperParams,
    "FT": FTHyperParams,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="执行一次真实的 EasyEdit 单条编辑，并输出编辑前后结果。"
    )
    parser.add_argument("--hparams", required=True, type=str, help="hparams yaml 路径")
    parser.add_argument("--model_path", required=True, type=str, help="本地 HuggingFace 模型目录")
    parser.add_argument("--method", default="ROME", type=str, help="ROME / MEMIT / FT")
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument("--output_dir", default="outputs/single_edit", type=str, help="结果输出目录")
    parser.add_argument("--prompt", default="The Eiffel Tower is located in", type=str, help="待编辑 prompt")
    parser.add_argument("--subject", default="Eiffel Tower", type=str, help="事实主体")
    parser.add_argument("--target_new", default="Rome", type=str, help="新目标答案")
    parser.add_argument("--ground_truth", default="Paris", type=str, help="原正确答案")
    parser.add_argument("--rephrase_prompt", default=None, type=str, help="可选复述 prompt")
    parser.add_argument("--locality_prompt", default=None, type=str, help="可选 locality prompt")
    parser.add_argument("--locality_ground_truth", default=None, type=str, help="可选 locality 答案")
    parser.add_argument("--portability_prompt", default=None, type=str, help="可选 portability prompt")
    parser.add_argument("--portability_ground_truth", default=None, type=str, help="可选 portability 答案")
    parser.add_argument("--max_new_tokens", default=16, type=int, help="生成长度")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    method = args.method.upper()
    if method not in METHOD_TO_HPARAMS:
        raise ValueError(f"暂只支持 {sorted(METHOD_TO_HPARAMS)}，收到 {args.method}")
    if not torch.cuda.is_available():
        raise RuntimeError("当前环境未检测到 CUDA。EasyEdit 当前这条 ROME/MEMIT/FT pipeline 需要在 GPU 服务器上运行。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")
    if args.subject not in args.prompt and "{}" not in args.prompt:
        raise ValueError("ROME/MEMIT/FT 的 prompt 里应包含 subject，或使用 '{}' 作为占位符。")


def load_hparams(args: argparse.Namespace):
    method = args.method.upper()
    hp_cls = METHOD_TO_HPARAMS[method]
    hparams = hp_cls.from_hparams(args.hparams)
    hparams.model_name = args.model_path
    if hasattr(hparams, "tokenizer_name"):
        hparams.tokenizer_name = args.model_path
    hparams.device = int(args.device)
    if hasattr(hparams, "batch_size"):
        hparams.batch_size = 1
    return hparams


def build_optional_inputs(args: argparse.Namespace):
    locality_inputs = None
    portability_inputs = None

    if args.locality_prompt and args.locality_ground_truth:
        locality_inputs = {
            "neighborhood": {
                "prompt": [args.locality_prompt],
                "ground_truth": [args.locality_ground_truth],
            }
        }

    if args.portability_prompt and args.portability_ground_truth:
        portability_inputs = {
            "one_hop": {
                "prompt": [args.portability_prompt],
                "ground_truth": [args.portability_ground_truth],
            }
        }

    return locality_inputs, portability_inputs


def load_generation_model(model_path: str, device: int):
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
    ).to(f"cuda:{device}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    return model.eval(), tokenizer


def generate_text(model, tokenizer, prompt: str, device: int, max_new_tokens: int) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(f"cuda:{device}")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
        )
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def to_builtin(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: to_builtin(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_builtin(value) for value in obj]
    if isinstance(obj, tuple):
        return [to_builtin(value) for value in obj]
    if hasattr(obj, "item") and callable(obj.item):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    return obj


def main() -> int:
    args = parse_args()
    validate_args(args)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hparams = load_hparams(args)
    locality_inputs, portability_inputs = build_optional_inputs(args)

    pre_model, pre_tok = load_generation_model(args.model_path, int(args.device))
    pre_answer = generate_text(pre_model, pre_tok, args.prompt, int(args.device), args.max_new_tokens)
    del pre_model
    torch.cuda.empty_cache()

    editor = BaseEditor.from_hparams(hparams)
    metrics, edited_model, _ = editor.edit(
        prompts=[args.prompt],
        target_new=[args.target_new],
        ground_truth=[args.ground_truth],
        subject=[args.subject],
        rephrase_prompts=[args.rephrase_prompt] if args.rephrase_prompt else None,
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
        keep_original_weight=True,
        sequential_edit=False,
        test_generation=True,
    )

    post_answer = generate_text(edited_model.eval(), editor.tok, args.prompt, int(args.device), args.max_new_tokens)

    summary: Dict[str, Any] = {
        "method": args.method.upper(),
        "model_path": args.model_path,
        "hparams": args.hparams,
        "prompt": args.prompt,
        "subject": args.subject,
        "ground_truth": args.ground_truth,
        "target_new": args.target_new,
        "pre_answer": pre_answer,
        "post_answer": post_answer,
        "metrics": to_builtin(metrics),
    }

    result_path = output_dir / f"{args.method.lower()}_single_edit_result.json"
    with result_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("=== Single Edit Result ===")
    print(f"method: {summary['method']}")
    print(f"prompt: {summary['prompt']}")
    print(f"subject: {summary['subject']}")
    print(f"ground_truth: {summary['ground_truth']}")
    print(f"target_new: {summary['target_new']}")
    print(f"pre_answer: {summary['pre_answer']}")
    print(f"post_answer: {summary['post_answer']}")
    print(f"metrics_json: {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
