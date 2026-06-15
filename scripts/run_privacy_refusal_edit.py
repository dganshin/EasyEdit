import argparse
import contextlib
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from tqdm.auto import tqdm

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_rome_privacy_requests import load_dataset, select_requests
METHOD_TO_HPARAMS = {
    "ROME": "ROMEHyperParams",
    "MEMIT": "MEMITHyperParams",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 privacy-injected model 上执行 refusal editing。")
    parser.add_argument(
        "--method",
        choices=sorted(METHOD_TO_HPARAMS),
        default="ROME",
        help="当前主线仍推荐 ROME，MEMIT 预留为后续 baseline",
    )
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_privacy_data/synthetic_privacy_dataset.json",
        type=str,
        help="synthetic privacy dataset json 路径",
    )
    parser.add_argument("--model_path", required=True, type=str, help="待编辑模型目录")
    parser.add_argument("--hparams", required=True, type=str, help="对应方法的 hparams yaml 路径")
    parser.add_argument("--device", default="0", type=str, help="CUDA 设备编号，例如 0")
    parser.add_argument("--output_dir", required=True, type=str, help="输出目录")
    parser.add_argument(
        "--requests_path",
        default=None,
        type=str,
        help="外部 edit requests json 路径；若提供，则直接读取 requests 而不是自动构造 direct-only requests",
    )
    parser.add_argument(
        "--append_requests_path",
        default=None,
        type=str,
        help="可选的第二份 requests json；会与 --requests_path 合并去重后一起执行",
    )
    parser.add_argument(
        "--run_name",
        default=None,
        type=str,
        help="输出文件名前缀；默认 direct-only 使用 <method>_direct，外部 requests 使用 pace_round2",
    )
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
    parser.add_argument("--full_private_eval", action="store_true", help="是否额外评测 full private prompts")
    parser.add_argument("--eval_public", action="store_true", help="是否同时评测 public retain")
    parser.add_argument("--disable_fluency_eval", action="store_true", help="关闭 EasyEdit 内部 generation fluency")
    return parser.parse_args()


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


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def load_hparams(args: argparse.Namespace):
    from easyeditor import MEMITHyperParams, ROMEHyperParams

    method_to_hparams = {
        "ROME": ROMEHyperParams,
        "MEMIT": MEMITHyperParams,
    }
    hparams_cls = method_to_hparams[args.method]
    hparams = hparams_cls.from_hparams(args.hparams)
    hparams.model_name = args.model_path
    if hasattr(hparams, "tokenizer_name"):
        hparams.tokenizer_name = args.model_path
    hparams.device = int(args.device)
    if hasattr(hparams, "batch_size"):
        hparams.batch_size = 1
    return hparams


def load_requests_file(path_str: str) -> List[Dict[str, Any]]:
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        if "requests" in payload and isinstance(payload["requests"], list):
            return payload["requests"]
        raise ValueError(f"requests 文件缺少 requests 列表: {path}")
    if isinstance(payload, list):
        return payload
    raise ValueError(f"不支持的 requests 文件格式: {path}")


def dedupe_key(item: Dict[str, Any]) -> str:
    case_id = item.get("case_id")
    prompt = str(item.get("prompt", "")).strip()
    target_new = str(item.get("target_new", "")).strip()
    if case_id:
        return f"{case_id}||{prompt}||{target_new}"
    return f"{prompt}||{target_new}"


def merge_requests(primary: List[Dict[str, Any]], appended: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*primary, *appended]:
        key = dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def summarize_request_pool(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_case = Counter(str(item.get("case_id") or "unknown") for item in requests)
    by_person = Counter(str(item.get("person_id") or "unknown") for item in requests)
    by_attack_type = Counter(str(item.get("attack_type") or "unknown") for item in requests)
    real_people = [key for key in by_person if key and key != "unknown"]
    return {
        "num_requests": len(requests),
        "num_cases": len(by_case),
        "num_people": len(real_people),
        "by_attack_type": dict(sorted(by_attack_type.items())),
        "max_requests_per_case": max(by_case.values()) if by_case else 0,
        "max_requests_per_person": max((by_person[key] for key in real_people), default=0),
    }


def resolve_run_name(args: argparse.Namespace) -> str:
    if args.run_name:
        return args.run_name
    if args.requests_path:
        return "pace_round2"
    return f"{args.method.lower()}_direct"


def resolve_requests(args: argparse.Namespace, dataset: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
    if args.requests_path:
        primary_requests = load_requests_file(args.requests_path)
        if args.append_requests_path:
            append_requests = load_requests_file(args.append_requests_path)
            requests = merge_requests(primary_requests, append_requests)
        else:
            requests = primary_requests
        return requests, "external_requests"

    requests = select_requests(
        dataset,
        args.num_people,
        args.private_per_person,
        args.prompt_style,
        args.target_new,
    )
    return requests, "direct_only"


def build_subset_dataset(dataset: Dict[str, Any], allowed_case_ids: set[str]) -> Dict[str, Any]:
    filtered_cases = [case for case in dataset["flat_cases"] if case.get("case_id") in allowed_case_ids]
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
    progress_desc: str,
) -> List[Dict[str, Any]]:
    from run_privacy_generation import batched, generate_batch

    records: List[Dict[str, Any]] = []
    total_batches = max(1, (len(jobs) + batch_size - 1) // batch_size) if jobs else 0
    progress = tqdm(
        batched(jobs, batch_size),
        total=total_batches,
        desc=progress_desc,
        leave=False,
        dynamic_ncols=True,
    )
    for batch_jobs in progress:
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
                    "privacy_type": job.get("privacy_type"),
                    "sensitivity": job["sensitivity"],
                    "attack_type": job["attack_type"],
                    "attack_template_id": job.get("attack_template_id"),
                    "prompt": job["prompt"],
                    "target_value": job["target_value"],
                    "output": output,
                }
            )
        progress.set_postfix_str(f"records={len(records)}")
    progress.close()
    return records


def run_eval(script_name: str, dataset: str, predictions: Path, output_path: Path, allowed_case_ids_json: Path | None = None) -> None:
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
    if allowed_case_ids_json is not None and script_name == "evaluate_privacy_leakage.py":
        command.extend(["--allowed_case_ids_json", str(allowed_case_ids_json)])
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    if args.append_requests_path and not args.requests_path:
        raise ValueError("--append_requests_path 必须与 --requests_path 一起使用")
    import torch
    from easyeditor import BaseEditor
    from run_privacy_generation import collect_generation_jobs, batched, generate_batch

    if not torch.cuda.is_available():
        raise RuntimeError("当前环境未检测到 CUDA，privacy refusal editing 需要在 GPU 服务器上运行。")
    if not str(args.device).isdigit():
        raise ValueError("--device 目前请传 CUDA 编号，如 0")

    dataset = load_dataset(args.dataset)
    requests, request_source = resolve_requests(args, dataset)
    run_name = resolve_run_name(args)
    request_case_ids = {item["case_id"] for item in requests}
    request_summary = summarize_request_pool(requests)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"{run_name}_run.log"
    append_log(log_path, f"method={args.method}")
    append_log(log_path, f"dataset={args.dataset}")
    append_log(log_path, f"model_path={args.model_path}")
    append_log(log_path, f"request_source={request_source}")
    append_log(log_path, f"num_requests={len(requests)}")
    append_log(log_path, f"num_cases={request_summary['num_cases']}")
    append_log(log_path, f"num_people={request_summary['num_people']}")

    requests_path = output_dir / f"{run_name}_requests.json"
    write_json(
        requests_path,
        {
            "dataset_path": args.dataset,
            "model_path": args.model_path,
            "hparams": args.hparams,
            "method": args.method,
            "request_source": request_source,
            "requests_path": args.requests_path,
            "append_requests_path": args.append_requests_path,
            "run_name": run_name,
            "num_requests": len(requests),
            "request_summary": request_summary,
            "requests": requests,
        },
    )

    subset_dataset_path = output_dir / f"{run_name}_subset_dataset.json"
    write_json(subset_dataset_path, build_subset_dataset(dataset, request_case_ids))
    allowed_case_ids_path = output_dir / f"{run_name}_case_ids.json"
    with allowed_case_ids_path.open("w", encoding="utf-8") as fh:
        json.dump(sorted(request_case_ids), fh, ensure_ascii=False, indent=2)

    hparams = load_hparams(args)
    easyeditor_logger = logging.getLogger("easyeditor")
    original_easyeditor_level = easyeditor_logger.level
    easyeditor_logger.setLevel(logging.WARNING)
    print(f"[Stage] requests: {len(requests)}")
    print(f"[Stage] instantiating editor; detailed logs -> {log_path}")
    with log_path.open("a", encoding="utf-8") as log_fh:
        with contextlib.redirect_stdout(log_fh), contextlib.redirect_stderr(log_fh):
            editor = BaseEditor.from_hparams(hparams)
            print(f"[Stage] running {args.method} edit")
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
    easyeditor_logger.setLevel(original_easyeditor_level)
    write_json(output_dir / f"{run_name}_edit_metrics.json", {"metrics": to_builtin(metrics)})
    print(f"[Stage] edit finished")

    tokenizer = editor.tok
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    if getattr(tokenizer, "padding_side", "right") != "left":
        tokenizer.padding_side = "left"

    private_jobs_all = collect_generation_jobs(dataset, ["direct", "paraphrase", "completion", "roleplay", "context"], "private")
    private_jobs_subset = filter_jobs_by_case_ids(private_jobs_all, request_case_ids)

    print(f"[Stage] subset generation start: {len(private_jobs_subset)}")
    subset_predictions = generate_records(
        edited_model.eval(),
        tokenizer,
        private_jobs_subset,
        int(args.device),
        args.batch_size,
        args.max_new_tokens,
        "Subset generation",
    )
    print(f"[Stage] subset generation finished: {len(subset_predictions)}")
    subset_pred_path = output_dir / f"privacy_predictions_{run_name}_subset.jsonl"
    write_jsonl(subset_pred_path, subset_predictions)
    run_eval(
        "evaluate_privacy_leakage.py",
        str(subset_dataset_path),
        subset_pred_path,
        output_dir / f"privacy_leakage_eval_{run_name}_subset.json",
        None,
    )

    if args.full_private_eval:
        print(f"[Stage] full private generation start: {len(private_jobs_all)}")
        full_predictions = generate_records(
            edited_model.eval(),
            tokenizer,
            private_jobs_all,
            int(args.device),
            args.batch_size,
            args.max_new_tokens,
            "Full private generation",
        )
        print(f"[Stage] full private generation finished: {len(full_predictions)}")
        full_pred_path = output_dir / f"privacy_predictions_{run_name}_full.jsonl"
        write_jsonl(full_pred_path, full_predictions)
        run_eval(
            "evaluate_privacy_leakage.py",
            args.dataset,
            full_pred_path,
            output_dir / f"privacy_leakage_eval_{run_name}_full.json",
            None,
        )

    if args.eval_public:
        public_jobs = collect_generation_jobs(dataset, ["direct"], "public")
        print(f"[Stage] public generation start: {len(public_jobs)}")
        public_predictions = generate_records(
            edited_model.eval(),
            tokenizer,
            public_jobs,
            int(args.device),
            args.batch_size,
            args.max_new_tokens,
            "Public generation",
        )
        print(f"[Stage] public generation finished: {len(public_predictions)}")
        public_pred_path = output_dir / f"public_predictions_{run_name}.jsonl"
        write_jsonl(public_pred_path, public_predictions)
        run_eval(
            "evaluate_public_retain.py",
            args.dataset,
            public_pred_path,
            output_dir / f"public_retain_eval_{run_name}.json",
        )

    manifest = {
        "dataset_path": args.dataset,
        "model_path": args.model_path,
        "hparams": args.hparams,
        "method": args.method,
        "request_source": request_source,
        "requests_path": args.requests_path,
        "append_requests_path": args.append_requests_path,
        "run_name": run_name,
        "num_people_requested": args.num_people,
        "private_per_person_requested": args.private_per_person,
        "prompt_style": args.prompt_style,
        "target_new": args.target_new,
        "num_requests": len(requests),
        "request_summary": request_summary,
        "request_case_ids": sorted(request_case_ids),
        "full_private_eval": args.full_private_eval,
        "eval_public": args.eval_public,
        "output_dir": str(output_dir),
    }
    write_json(output_dir / f"{run_name}_manifest.json", manifest)

    print(f"requests_json: {requests_path}")
    print(f"edit_metrics_json: {output_dir / f'{run_name}_edit_metrics.json'}")
    print(f"subset_predictions_jsonl: {subset_pred_path}")
    print(f"subset_eval_json: {output_dir / f'privacy_leakage_eval_{run_name}_subset.json'}")
    if args.full_private_eval:
        print(f"full_eval_json: {output_dir / f'privacy_leakage_eval_{run_name}_full.json'}")
    if args.eval_public:
        print(f"public_eval_json: {output_dir / f'public_retain_eval_{run_name}.json'}")
    print(f"manifest_json: {output_dir / f'{run_name}_manifest.json'}")
    print(f"run_log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
