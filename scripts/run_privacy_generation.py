import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import torch
from peft import PeftModel
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="对合成隐私数据的测试 prompt 批量生成模型输出。")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="合成隐私数据集 json 路径",
    )
    parser.add_argument("--model_path", required=True, type=str, help="本地 HuggingFace 模型目录")
    parser.add_argument(
        "--lora_adapter_path",
        default=None,
        type=str,
        help="可选的 LoRA adapter 目录；若提供，则以 base model + adapter 方式生成",
    )
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument(
        "--output_path",
        default="outputs/privacy_predictions.jsonl",
        type=str,
        help="预测结果输出 jsonl 路径",
    )
    parser.add_argument("--max_new_tokens", default=32, type=int, help="每个 prompt 的最大生成长度")
    parser.add_argument("--batch_size", default=4, type=int, help="批大小")
    parser.add_argument("--do_sample", action="store_true", help="是否启用采样生成")
    parser.add_argument("--temperature", default=0.7, type=float, help="采样温度，仅在 --do_sample 时生效")
    parser.add_argument("--top_p", default=0.9, type=float, help="top-p，仅在 --do_sample 时生效")
    parser.add_argument("--num_trials", default=1, type=int, help="每个 prompt 生成多少次；>1 时用于多次采样风险评估")
    parser.add_argument("--seed", default=42, type=int, help="随机种子")
    parser.add_argument(
        "--mode",
        choices=["private", "public", "all"],
        default="private",
        help="生成 private 攻击问法、public retain，或两者都生成",
    )
    parser.add_argument(
        "--attack_types",
        nargs="*",
        default=["direct", "paraphrase", "completion", "roleplay"],
        help="要评测的攻击问法类型",
    )
    parser.add_argument(
        "--include_public",
        action="store_true",
        help="是否同时对 public case 的 direct prompt 生成输出",
    )
    return parser.parse_args()


def load_dataset(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def collect_generation_jobs(
    dataset: Dict[str, Any],
    attack_types: Iterable[str],
    mode: str,
) -> List[Dict[str, Any]]:
    attack_set = set(attack_types)
    jobs: List[Dict[str, Any]] = []
    include_private = mode in {"private", "all"}
    include_public = mode in {"public", "all"}

    for case in dataset["flat_cases"]:
        sensitivity = case.get("sensitivity")
        if sensitivity == "private" and include_private:
            prompt_rows = case.get("test_prompt_rows")
            if prompt_rows:
                candidate_rows = [
                    row for row in prompt_rows
                    if row["attack_type"] in attack_set
                ]
            else:
                candidate_rows = [
                    {
                        "attack_type": attack_type,
                        "attack_template_id": f"{attack_type}_t01",
                        "prompt": prompt,
                    }
                    for attack_type, prompt in case["test_prompts"].items()
                    if attack_type in attack_set
                ]
            for row in candidate_rows:
                attack_type = row["attack_type"]
                attack_template_id = row["attack_template_id"]
                prompt = row["prompt"]
                jobs.append(
                    {
                        "prediction_id": f"{case['case_id']}::{attack_type}::{attack_template_id}",
                        "case_id": case["case_id"],
                        "person_id": case["person_id"],
                        "name": case["name"],
                        "attribute": case["attribute"],
                        "privacy_type": case.get("privacy_type"),
                        "public_type": case.get("public_type"),
                        "sensitivity": sensitivity,
                        "attack_type": attack_type,
                        "attack_template_id": attack_template_id,
                        "prompt": prompt,
                        "target_value": case["value"],
                    }
                )
        elif include_public and sensitivity == "public":
            prompt_rows = case.get("test_prompt_rows") or [
                {
                    "attack_type": "direct",
                    "attack_template_id": "direct_t01",
                    "prompt": case["test_prompts"]["direct"],
                }
            ]
            for row in prompt_rows:
                if row["attack_type"] != "direct":
                    continue
                jobs.append(
                    {
                        "prediction_id": f"{case['case_id']}::direct::{row['attack_template_id']}",
                        "case_id": case["case_id"],
                        "person_id": case["person_id"],
                        "name": case["name"],
                        "attribute": case["attribute"],
                        "privacy_type": case.get("privacy_type"),
                        "public_type": case.get("public_type"),
                        "sensitivity": sensitivity,
                        "attack_type": "direct",
                        "attack_template_id": row["attack_template_id"],
                        "prompt": row["prompt"],
                        "target_value": case["value"],
                    }
                )
    return jobs


def resolve_tokenizer_source(model_path: str, lora_adapter_path: str | None) -> str:
    if not lora_adapter_path:
        return model_path
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


def load_model_and_tokenizer(model_path: str, device: int, lora_adapter_path: str | None):
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
    )
    if lora_adapter_path:
        model = PeftModel.from_pretrained(model, lora_adapter_path)
    model = model.to(f"cuda:{device}")
    tokenizer_source = resolve_tokenizer_source(model_path, lora_adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if tokenizer.padding_side != "left":
        tokenizer.padding_side = "left"
    return model.eval(), tokenizer


def batched(items: List[Dict[str, Any]], batch_size: int) -> Iterable[List[Dict[str, Any]]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def generate_batch(
    model,
    tokenizer,
    prompts: List[str],
    device: int,
    max_new_tokens: int,
    do_sample: bool,
    temperature: float,
    top_p: float,
) -> List[str]:
    encoded = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
    ).to(f"cuda:{device}")
    with torch.no_grad():
        outputs = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature if do_sample else None,
            top_p=top_p if do_sample else None,
            pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
        )

    results: List[str] = []
    for idx in range(outputs.shape[0]):
        input_len = int(encoded["attention_mask"][idx].sum().item())
        generated = outputs[idx][input_len:]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        results.append(text)
    return results


def main() -> int:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("当前环境未检测到 CUDA，privacy generation 需要在 GPU 服务器上运行。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")
    if args.batch_size < 1:
        raise ValueError("--batch_size 必须 >= 1")
    if args.num_trials < 1:
        raise ValueError("--num_trials 必须 >= 1")

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    dataset = load_dataset(args.dataset)
    mode = "all" if args.include_public and args.mode == "private" else args.mode
    jobs = collect_generation_jobs(dataset, args.attack_types, mode)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model, tokenizer = load_model_and_tokenizer(args.model_path, int(args.device), args.lora_adapter_path)

    records: List[Dict[str, Any]] = []
    total_batches = max(1, (len(jobs) + args.batch_size - 1) // args.batch_size) if jobs else 0
    total_steps = total_batches * args.num_trials
    progress = tqdm(total=total_steps, desc="Privacy generation", dynamic_ncols=True)
    for trial_idx in range(args.num_trials):
        for batch_jobs in batched(jobs, args.batch_size):
            prompts = [job["prompt"] for job in batch_jobs]
            outputs = generate_batch(
                model,
                tokenizer,
                prompts,
                int(args.device),
                args.max_new_tokens,
                args.do_sample,
                args.temperature,
                args.top_p,
            )
            for job, output in zip(batch_jobs, outputs):
                prediction_id = job["prediction_id"]
                if args.num_trials > 1:
                    prediction_id = f"{prediction_id}::trial_{trial_idx:02d}"
                records.append(
                    {
                        "prediction_id": prediction_id,
                        "base_prediction_id": job["prediction_id"],
                        "trial_id": trial_idx,
                        "case_id": job["case_id"],
                        "person_id": job["person_id"],
                        "name": job["name"],
                        "attribute": job["attribute"],
                        "privacy_type": job.get("privacy_type"),
                        "public_type": job.get("public_type"),
                        "sensitivity": job["sensitivity"],
                        "attack_type": job["attack_type"],
                        "attack_template_id": job.get("attack_template_id"),
                        "prompt": job["prompt"],
                        "target_value": job["target_value"],
                        "output": output,
                    }
                )
            progress.update(1)
            progress.set_postfix_str(f"trial={trial_idx + 1}/{args.num_trials}, records={len(records)}")
    progress.close()

    with output_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"dataset: {args.dataset}")
    print(f"model_path: {args.model_path}")
    print(f"lora_adapter_path: {args.lora_adapter_path}")
    print(f"mode: {mode}")
    print(f"do_sample: {args.do_sample}")
    print(f"num_trials: {args.num_trials}")
    print(f"num_jobs: {len(jobs)}")
    print(f"num_outputs: {len(records)}")
    print(f"predictions_jsonl: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
