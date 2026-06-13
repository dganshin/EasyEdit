import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import torch
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
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument(
        "--output_path",
        default="outputs/privacy_predictions.jsonl",
        type=str,
        help="预测结果输出 jsonl 路径",
    )
    parser.add_argument("--max_new_tokens", default=32, type=int, help="每个 prompt 的最大生成长度")
    parser.add_argument("--batch_size", default=4, type=int, help="批大小")
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
    include_public: bool,
) -> List[Dict[str, Any]]:
    attack_set = set(attack_types)
    jobs: List[Dict[str, Any]] = []

    for case in dataset["flat_cases"]:
        sensitivity = case.get("sensitivity")
        if sensitivity == "private":
            for attack_type, prompt in case["test_prompts"].items():
                if attack_type not in attack_set:
                    continue
                jobs.append(
                    {
                        "case_id": case["case_id"],
                        "person_id": case["person_id"],
                        "name": case["name"],
                        "attribute": case["attribute"],
                        "sensitivity": sensitivity,
                        "attack_type": attack_type,
                        "prompt": prompt,
                        "target_value": case["value"],
                    }
                )
        elif include_public and sensitivity == "public":
            prompt = case["test_prompts"]["direct"]
            jobs.append(
                {
                    "case_id": case["case_id"],
                    "person_id": case["person_id"],
                    "name": case["name"],
                    "attribute": case["attribute"],
                    "sensitivity": sensitivity,
                    "attack_type": "direct",
                    "prompt": prompt,
                    "target_value": case["value"],
                }
            )
    return jobs


def load_model_and_tokenizer(model_path: str, device: int):
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
    ).to(f"cuda:{device}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
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
            do_sample=False,
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

    dataset = load_dataset(args.dataset)
    jobs = collect_generation_jobs(dataset, args.attack_types, args.include_public)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model, tokenizer = load_model_and_tokenizer(args.model_path, int(args.device))

    records: List[Dict[str, Any]] = []
    for batch_jobs in batched(jobs, args.batch_size):
        prompts = [job["prompt"] for job in batch_jobs]
        outputs = generate_batch(model, tokenizer, prompts, int(args.device), args.max_new_tokens)
        for job, output in zip(batch_jobs, outputs):
            records.append(
                {
                    "case_id": job["case_id"],
                    "person_id": job["person_id"],
                    "name": job["name"],
                    "attribute": job["attribute"],
                    "sensitivity": job["sensitivity"],
                    "attack_type": job["attack_type"],
                    "prompt": job["prompt"],
                    "target_value": job["target_value"],
                    "output": output,
                }
            )

    with output_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"dataset: {args.dataset}")
    print(f"model_path: {args.model_path}")
    print(f"num_jobs: {len(jobs)}")
    print(f"num_outputs: {len(records)}")
    print(f"predictions_jsonl: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
