import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import torch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_rome_privacy_requests import load_dataset, select_requests
from run_privacy_generation import (
    collect_generation_jobs,
    batched,
    generate_batch,
)
from easyeditor import BaseEditor, ROMEHyperParams


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 merged privacy model 上执行 ROME direct-only refusal editing。")
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="synthetic privacy dataset json 路径",
    )
    parser.add_argument("--model_path", required=True, type=str, help="待编辑模型目录")
    parser.add_argument("--hparams", default="hparams/ROME/qwen2.5-7b.yaml", type=str, help="ROME hparams yaml 路径")
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument("--output_dir", required=True, type=str, help="输出目录")
    parser.add_argument("--num_people", default=5, type=int, help="前多少个人参与 direct-only 编辑")
    parser.add_argument("--private_per_person", default=2, type=int, help="每个人编辑多少条 private")
    parser.add_argument(
        "--prompt_style",
        choices=["canonical_qa", "dataset_prompt"],
        default="canonical_qa",
        help="编辑请求 prompt 风格",
    )
    parser.add_argument("--target_new", default="I cannot provide private information.", type=str, help="统一 refusal 文本")
    parser.add_argument("--batch_size", default=4, type=int, help="编辑后 generation 批大小")
    parser.add_argument("--max_new_tokens", default=32, type=int, help="编辑后 generation 长度")
    parser.add_argument("--full_private_eval", action="store_true", help="是否额外评测 full 80 private prompts")
    parser.add_argument("--eval_public", action="store_true", help="是否同时评测 public retain")
    parser.add_argument("--disable_fluency_eval", action="store_true", help="关闭 EasyEdit 内部 generation fluency")
    return parser.parse_args()


def load_hparams(args: argparse.Namespace):
    hparams = ROMEHyperParams.from_hparams(args.hparams)
    hparams.model_name = args.model_path
    if hasattr(hparams, "tokenizer_name"):
        hparams.tokenizer_name = args.model_path
    hparams.device = int(args.device)
    if hasattr(hparams, "batch_size"):
        hparams.batch_size = 1
    return hparams


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


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


def build_subset_dataset(dataset: Dict[str, Any], allowed_case_ids: set[str]) -> Dict[str, Any]:
    filtered_cases = [
        case for case in dataset["flat_cases"]
        if case.get("case_id") in allowed_case_ids
    ]
    return {
        "seed": dataset.get("seed"),
        "num_people": len({case["person_id"] for case in filtered_cases}),
        "refusal_text": dataset.get("refusal_text", "I cannot provide private information."),
        "people": [],
        "flat_cases": filtered_cases,
    }


def filter_jobs_by_case_ids(jobs: List[Dict[str, Any]], allowed_case_ids: set[str]) -> List[Dict[str, Any]]:
    return [job for job in jobs if job["case_id"] in allowed_case_ids]


def generate_records(
    model,
    tokenizer,
    jobs: List[Dict[str, Any]],
    device: int,
    batch_size: int,
    max_new_tokens: int,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for batch_jobs in batched(jobs, batch_size):
        prompts = [job["prompt"] for job in batch_jobs]
        outputs = generate_batch(
            model,
            tokenizer,
            prompts,
            device,
            max_new_tokens,
            do_sample=False,
            temperature=0.7,
            top_p=0.9,
        )
        for job, output in zip(batch_jobs, outputs):
            records.append(
                {
                    "prediction_id": job["prediction_id"],
                    "base_prediction_id": job["prediction_id"],
                    "trial_id": 0,
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
    return records


def run_eval(script_name: str, dataset: str, predictions: Path, output_path: Path) -> None:
    command = [
        sys.executable,
        str(SCRIPT_DIR / script_name),
        "--dataset",
        dataset,
        "--predictions",
        str(predictions),
        "--output_path",
        str(output_path),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("当前环境未检测到 CUDA，ROME refusal editing 需要在 GPU 服务器上运行。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")

    dataset = load_dataset(args.dataset)
    requests = select_requests(
        dataset,
        args.num_people,
        args.private_per_person,
        args.prompt_style,
        args.target_new,
    )
    request_case_ids = {item["case_id"] for item in requests}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    requests_path = output_dir / "rome_direct_requests.json"
    write_json(
        requests_path,
        {
            "dataset_path": args.dataset,
            "model_path": args.model_path,
            "hparams": args.hparams,
            "num_requests": len(requests),
            "requests": requests,
        },
    )
    subset_dataset_path = output_dir / "rome_direct_subset_dataset.json"
    write_json(subset_dataset_path, build_subset_dataset(dataset, request_case_ids))

    hparams = load_hparams(args)
    editor = BaseEditor.from_hparams(hparams)
    metrics, edited_model, _ = editor.edit(
        prompts=[item["prompt"] for item in requests],
        target_new=[item["target_new"] for item in requests],
        ground_truth=[item["ground_truth"] for item in requests],
        subject=[item["subject"] for item in requests],
        rephrase_prompts=[item.get("rephrase_prompt") for item in requests],
        sequential_edit=True,
        keep_original_weight=True,
        test_generation=not args.disable_fluency_eval,
    )
    write_json(output_dir / "rome_direct_edit_metrics.json", {"metrics": to_builtin(metrics)})

    tokenizer = editor.tok
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if getattr(tokenizer, "padding_side", "right") != "left":
        tokenizer.padding_side = "left"

    private_jobs_all = collect_generation_jobs(dataset, ["direct", "paraphrase", "completion", "roleplay"], "private")
    private_jobs_subset = filter_jobs_by_case_ids(private_jobs_all, request_case_ids)

    subset_predictions = generate_records(
        edited_model.eval(),
        tokenizer,
        private_jobs_subset,
        int(args.device),
        args.batch_size,
        args.max_new_tokens,
    )
    subset_pred_path = output_dir / "privacy_predictions_rome_direct_subset.jsonl"
    write_jsonl(subset_pred_path, subset_predictions)
    run_eval("evaluate_privacy_leakage.py", str(subset_dataset_path), subset_pred_path, output_dir / "privacy_leakage_eval_rome_direct_subset.json")

    if args.full_private_eval:
        full_predictions = generate_records(
            edited_model.eval(),
            tokenizer,
            private_jobs_all,
            int(args.device),
            args.batch_size,
            args.max_new_tokens,
        )
        full_pred_path = output_dir / "privacy_predictions_rome_direct_full.jsonl"
        write_jsonl(full_pred_path, full_predictions)
        run_eval("evaluate_privacy_leakage.py", args.dataset, full_pred_path, output_dir / "privacy_leakage_eval_rome_direct_full.json")

    if args.eval_public:
        public_jobs = collect_generation_jobs(dataset, ["direct"], "public")
        public_predictions = generate_records(
            edited_model.eval(),
            tokenizer,
            public_jobs,
            int(args.device),
            args.batch_size,
            args.max_new_tokens,
        )
        public_pred_path = output_dir / "public_predictions_rome_direct.jsonl"
        write_jsonl(public_pred_path, public_predictions)
        run_eval("evaluate_public_retain.py", args.dataset, public_pred_path, output_dir / "public_retain_eval_rome_direct.json")

    manifest = {
        "dataset_path": args.dataset,
        "model_path": args.model_path,
        "hparams": args.hparams,
        "num_people": args.num_people,
        "private_per_person": args.private_per_person,
        "prompt_style": args.prompt_style,
        "target_new": args.target_new,
        "num_requests": len(requests),
        "request_case_ids": sorted(request_case_ids),
        "full_private_eval": args.full_private_eval,
        "eval_public": args.eval_public,
        "output_dir": str(output_dir),
    }
    write_json(output_dir / "rome_direct_manifest.json", manifest)

    print(f"requests_json: {requests_path}")
    print(f"edit_metrics_json: {output_dir / 'rome_direct_edit_metrics.json'}")
    print(f"subset_predictions_jsonl: {subset_pred_path}")
    print(f"subset_eval_json: {output_dir / 'privacy_leakage_eval_rome_direct_subset.json'}")
    if args.full_private_eval:
        print(f"full_eval_json: {output_dir / 'privacy_leakage_eval_rome_direct_full.json'}")
    if args.eval_public:
        print(f"public_eval_json: {output_dir / 'public_retain_eval_rome_direct.json'}")
    print(f"manifest_json: {output_dir / 'rome_direct_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
