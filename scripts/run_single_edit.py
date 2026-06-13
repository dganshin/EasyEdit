import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    parser.add_argument("--generation_prompt", default=None, type=str, help="可选展示用 prompt；默认与编辑 prompt 相同")
    parser.add_argument("--rephrase_prompt", default=None, type=str, help="可选复述 prompt")
    parser.add_argument("--locality_prompt", default=None, type=str, help="可选 locality prompt")
    parser.add_argument("--locality_ground_truth", default=None, type=str, help="可选 locality 答案")
    parser.add_argument("--portability_prompt", default=None, type=str, help="可选 portability prompt")
    parser.add_argument("--portability_ground_truth", default=None, type=str, help="可选 portability 答案")
    parser.add_argument("--max_new_tokens", default=16, type=int, help="生成长度")
    parser.add_argument("--top_k", default=10, type=int, help="展示首个续写 token 的 top-k")
    parser.add_argument("--probe_original_text", default=None, type=str, help="可选显式指定原答案 probe 文本；默认使用 ground_truth")
    parser.add_argument("--probe_target_text", default=None, type=str, help="可选显式指定目标答案 probe 文本；默认使用 target_new")
    parser.add_argument("--disable_fluency_eval", action="store_true", help="关闭 EasyEdit 内部 fluency 评估，减少额外依赖和耗时")
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


def first_token_topk(model, tokenizer, prompt: str, device: int, top_k: int) -> List[Dict[str, Any]]:
    inputs = tokenizer(prompt, return_tensors="pt").to(f"cuda:{device}")
    with torch.no_grad():
        logits = model(**inputs).logits[:, -1, :]
        probs = torch.softmax(logits, dim=-1)
        topk_probs, topk_ids = torch.topk(probs, k=top_k, dim=-1)

    results: List[Dict[str, Any]] = []
    for token_id, prob in zip(topk_ids[0].tolist(), topk_probs[0].tolist()):
        token_text = tokenizer.decode([token_id], skip_special_tokens=False)
        results.append(
            {
                "token_id": token_id,
                "token_text": token_text,
                "prob": prob,
            }
        )
    return results


def _continuation_token_ids(tokenizer, prompt: str, continuation: str) -> List[int]:
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(prompt + continuation, add_special_tokens=False)["input_ids"]
    if len(full_ids) <= len(prompt_ids):
        raise ValueError(f"无法从 prompt={prompt!r} 和 continuation={continuation!r} 中解析续写 token。")
    return full_ids[len(prompt_ids):]


def continuation_probe(
    model,
    tokenizer,
    prompt: str,
    continuation_text: str,
    device: int,
) -> Dict[str, Any]:
    continuation = continuation_text if continuation_text.startswith(" ") else f" {continuation_text}"
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    continuation_ids = _continuation_token_ids(tokenizer, prompt, continuation)
    full_ids = prompt_ids + continuation_ids
    input_ids = torch.tensor([full_ids], dtype=torch.long, device=f"cuda:{device}")

    with torch.no_grad():
        logits = model(input_ids=input_ids).logits[0]

    token_details: List[Dict[str, Any]] = []
    token_probs: List[float] = []
    token_logprobs: List[float] = []
    token_ranks: List[int] = []

    for idx, token_id in enumerate(continuation_ids):
        logit_index = len(prompt_ids) - 1 + idx
        probs = torch.softmax(logits[logit_index], dim=-1)
        sorted_ids = torch.argsort(probs, descending=True)
        rank_tensor = (sorted_ids == token_id).nonzero(as_tuple=False)
        rank = int(rank_tensor[0].item()) + 1 if rank_tensor.numel() else -1
        prob = float(probs[token_id].item())
        logprob = float(torch.log(probs[token_id]).item())
        token_text = tokenizer.decode([token_id], skip_special_tokens=False)

        token_probs.append(prob)
        token_logprobs.append(logprob)
        token_ranks.append(rank)
        token_details.append(
            {
                "token_id": token_id,
                "token_text": token_text,
                "prob": prob,
                "rank": rank,
            }
        )

    joint_prob = float(math.exp(sum(token_logprobs)))
    return {
        "text": continuation_text,
        "continuation_text": continuation,
        "token_ids": continuation_ids,
        "token_details": token_details,
        "avg_token_prob": float(sum(token_probs) / len(token_probs)),
        "joint_prob": joint_prob,
        "first_token_prob": token_probs[0],
        "first_token_rank": token_ranks[0],
    }


def probe_delta(pre_probe: Dict[str, Any], post_probe: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": post_probe["text"],
        "first_token_prob_delta": post_probe["first_token_prob"] - pre_probe["first_token_prob"],
        "avg_token_prob_delta": post_probe["avg_token_prob"] - pre_probe["avg_token_prob"],
        "joint_prob_delta": post_probe["joint_prob"] - pre_probe["joint_prob"],
        "first_token_rank_delta": post_probe["first_token_rank"] - pre_probe["first_token_rank"],
    }


def print_probe(label: str, pre_probe: Dict[str, Any], post_probe: Dict[str, Any]) -> None:
    delta = probe_delta(pre_probe, post_probe)
    print(f"{label}_probe_text: {post_probe['text']}")
    print(
        f"  pre_first_token_prob={pre_probe['first_token_prob']:.6f}, "
        f"post_first_token_prob={post_probe['first_token_prob']:.6f}, "
        f"delta={delta['first_token_prob_delta']:.6f}"
    )
    print(
        f"  pre_first_token_rank={pre_probe['first_token_rank']}, "
        f"post_first_token_rank={post_probe['first_token_rank']}, "
        f"delta={delta['first_token_rank_delta']}"
    )
    print(
        f"  pre_avg_token_prob={pre_probe['avg_token_prob']:.6f}, "
        f"post_avg_token_prob={post_probe['avg_token_prob']:.6f}, "
        f"delta={delta['avg_token_prob_delta']:.6f}"
    )
    print(
        f"  pre_joint_prob={pre_probe['joint_prob']:.6f}, "
        f"post_joint_prob={post_probe['joint_prob']:.6f}, "
        f"delta={delta['joint_prob_delta']:.6f}"
    )


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
    generation_prompt = args.generation_prompt or args.prompt
    probe_original_text = args.probe_original_text or args.ground_truth
    probe_target_text = args.probe_target_text or args.target_new

    hparams = load_hparams(args)
    locality_inputs, portability_inputs = build_optional_inputs(args)

    pre_model, pre_tok = load_generation_model(args.model_path, int(args.device))
    pre_answer = generate_text(pre_model, pre_tok, generation_prompt, int(args.device), args.max_new_tokens)
    pre_topk = first_token_topk(pre_model, pre_tok, generation_prompt, int(args.device), args.top_k)
    pre_original_probe = continuation_probe(pre_model, pre_tok, generation_prompt, probe_original_text, int(args.device))
    pre_target_probe = continuation_probe(pre_model, pre_tok, generation_prompt, probe_target_text, int(args.device))
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
        test_generation=not args.disable_fluency_eval,
    )

    post_answer = generate_text(edited_model.eval(), editor.tok, generation_prompt, int(args.device), args.max_new_tokens)
    post_topk = first_token_topk(edited_model.eval(), editor.tok, generation_prompt, int(args.device), args.top_k)
    post_original_probe = continuation_probe(edited_model.eval(), editor.tok, generation_prompt, probe_original_text, int(args.device))
    post_target_probe = continuation_probe(edited_model.eval(), editor.tok, generation_prompt, probe_target_text, int(args.device))

    summary: Dict[str, Any] = {
        "method": args.method.upper(),
        "model_path": args.model_path,
        "hparams": args.hparams,
        "prompt": args.prompt,
        "generation_prompt": generation_prompt,
        "subject": args.subject,
        "ground_truth": args.ground_truth,
        "target_new": args.target_new,
        "pre_answer": pre_answer,
        "post_answer": post_answer,
        "pre_topk_next_token": pre_topk,
        "post_topk_next_token": post_topk,
        "pre_original_probe": pre_original_probe,
        "post_original_probe": post_original_probe,
        "pre_target_probe": pre_target_probe,
        "post_target_probe": post_target_probe,
        "probe_deltas": {
            "original": probe_delta(pre_original_probe, post_original_probe),
            "target_new": probe_delta(pre_target_probe, post_target_probe),
        },
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
    print(f"generation_prompt: {summary['generation_prompt']}")
    print(f"pre_answer: {summary['pre_answer']}")
    print(f"post_answer: {summary['post_answer']}")
    print("pre_topk_next_token:")
    for item in summary["pre_topk_next_token"]:
        print(f"  {item['token_id']}: {item['token_text']!r} -> {item['prob']:.6f}")
    print("post_topk_next_token:")
    for item in summary["post_topk_next_token"]:
        print(f"  {item['token_id']}: {item['token_text']!r} -> {item['prob']:.6f}")
    print_probe("original", pre_original_probe, post_original_probe)
    print_probe("target_new", pre_target_probe, post_target_probe)
    print(f"metrics_json: {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
