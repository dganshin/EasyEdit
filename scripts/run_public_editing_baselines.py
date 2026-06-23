import argparse
import contextlib
import gc
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


METHOD_HPARAMS = {
    "ROME": "ROMEHyperParams",
    "MEMIT": "MEMITHyperParams",
    "FT": "FTHyperParams",
    "FT-L": "FTHyperParams",
    "IKE": "IKEHyperParams",
    "KN": "KNHyperParams",
    "MEND": "MENDHyperParams",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run small public editing baselines with EasyEdit.")
    parser.add_argument("--dataset_path", required=True, type=str)
    parser.add_argument("--dataset_name", choices=["counterfact", "zsre"], required=True)
    parser.add_argument("--model_path", required=True, type=str)
    parser.add_argument("--model_name", required=True, type=str)
    parser.add_argument("--methods", default="ROME,FT,IKE,KN", type=str)
    parser.add_argument("--max_cases", default=500, type=int)
    parser.add_argument("--output_dir", required=True, type=str)
    parser.add_argument("--device", default="0", type=str)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--smoke_only", action="store_true")
    parser.add_argument("--disable_generation_test", action="store_true")
    parser.add_argument(
        "--resume_skip_completed",
        action="store_true",
        help="Skip a method when output_dir/METHOD/summary.json exists with status=ok.",
    )
    parser.add_argument(
        "--isolate_methods",
        action="store_true",
        help="Run each method in a fresh Python subprocess to release GPU memory between methods.",
    )
    parser.add_argument(
        "--output_method_suffix",
        default="",
        type=str,
        help="Append a suffix to method output names, e.g. ROME_PACE_EDIT while still using ROME hparams.",
    )
    parser.add_argument(
        "--sequential_edit",
        action="store_true",
        help="Apply requests cumulatively before final evaluation; needed for closed-loop wrapper runs.",
    )
    return parser.parse_args()


def load_dataset(path_str: str) -> List[Dict[str, Any]]:
    with Path(path_str).open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict) and "records" in payload:
        return payload["records"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"unsupported dataset format: {path_str}")


def method_hparams_path(method: str, model_name: str) -> Path:
    model_key = "gpt-j-6B" if "gpt" in model_name.lower() else "qwen2.5-7b"
    folder = "FT" if method == "FT-L" else method
    return Path("hparams") / folder / f"{model_key}.yaml"


def load_hparams(method: str, hparams_path: Path, model_path: str, device: str):
    import easyeditor

    cls_name = METHOD_HPARAMS[method]
    cls = getattr(easyeditor, cls_name)
    hparams = cls.from_hparams(str(hparams_path))
    hparams.model_name = model_path
    if hasattr(hparams, "tokenizer_name"):
        hparams.tokenizer_name = model_path
    if hasattr(hparams, "device"):
        hparams.device = int(device)
    if hasattr(hparams, "batch_size"):
        hparams.batch_size = 1
    if method == "FT-L" and hasattr(hparams, "objective_optimization"):
        hparams.objective_optimization = "prompt_last"
    return hparams


def to_request(record: Dict[str, Any]) -> Dict[str, Any]:
    rephrase = record.get("rephrase_prompt") or []
    if isinstance(rephrase, list):
        rephrase_prompt = rephrase[0] if rephrase else record["prompt"]
    else:
        rephrase_prompt = rephrase
    request = {
        "case_id": record.get("case_id"),
        "prompt": record["prompt"],
        "subject": record["subject"],
        "target_new": record["target_new"],
        "ground_truth": record["ground_truth"],
        "rephrase_prompt": rephrase_prompt,
        "locality": {},
        "portability": {},
    }
    locality = record.get("locality") or []
    loc_with_answer = [item for item in locality if item.get("prompt") and item.get("ground_truth")]
    if loc_with_answer:
        request["locality"]["loc"] = {
            "prompt": loc_with_answer[0]["prompt"],
            "ground_truth": loc_with_answer[0]["ground_truth"],
        }
    return request


def to_builtin(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, tuple):
        return [to_builtin(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    return obj


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def completed_summary_exists(method_dir: Path) -> bool:
    summary_path = method_dir / "summary.json"
    if not summary_path.exists():
        return False
    try:
        with summary_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return False
    return payload.get("status") == "ok"


def display_method_name(method: str, args: argparse.Namespace) -> str:
    suffix = (args.output_method_suffix or "").strip().strip("_")
    return f"{method}_{suffix}" if suffix else method


def release_cuda_cache() -> None:
    gc.collect()
    try:
        import torch
    except Exception:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def run_isolated_methods(args: argparse.Namespace, methods: List[str]) -> int:
    script_path = Path(__file__).resolve()
    for method in methods:
        method_dir = Path(args.output_dir) / display_method_name(method, args)
        if args.resume_skip_completed and completed_summary_exists(method_dir):
            print(f"[SKIP] {method}: completed summary exists at {method_dir / 'summary.json'}")
            continue
        cmd = [
            sys.executable,
            str(script_path),
            "--dataset_path",
            args.dataset_path,
            "--dataset_name",
            args.dataset_name,
            "--model_path",
            args.model_path,
            "--model_name",
            args.model_name,
            "--methods",
            method,
            "--max_cases",
            str(args.max_cases),
            "--output_dir",
            args.output_dir,
            "--device",
            str(args.device),
        ]
        if args.dry_run:
            cmd.append("--dry_run")
        if args.smoke_only:
            cmd.append("--smoke_only")
        if args.disable_generation_test:
            cmd.append("--disable_generation_test")
        if args.resume_skip_completed:
            cmd.append("--resume_skip_completed")
        if args.output_method_suffix:
            cmd.extend(["--output_method_suffix", args.output_method_suffix])
        if args.sequential_edit:
            cmd.append("--sequential_edit")
        env = os.environ.copy()
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        print(f"[METHOD] {method}: isolated subprocess")
        result = subprocess.run(cmd, env=env)
        if result.returncode != 0:
            print(f"[FAIL] {method}: isolated subprocess exited with code {result.returncode}")
            return result.returncode
    return 0


def run_method(method: str, requests: List[Dict[str, Any]], args: argparse.Namespace, method_dir: Path) -> None:
    import torch
    from easyeditor import BaseEditor

    method_dir.mkdir(parents=True, exist_ok=True)
    hparams_path = method_hparams_path(method, args.model_name)
    config = {
        "dataset_path": args.dataset_path,
        "dataset_name": args.dataset_name,
        "model_path": args.model_path,
        "model_name": args.model_name,
        "method": display_method_name(method, args),
        "base_method": method,
        "hparams_path": str(hparams_path),
        "max_cases": len(requests),
        "device": args.device,
        "smoke_only": args.smoke_only,
        "test_generation": not args.disable_generation_test,
        "sequential_edit": args.sequential_edit,
    }
    write_json(method_dir / "method_config.json", config)
    log_path = method_dir / "run_log.txt"
    if not hparams_path.exists():
        raise FileNotFoundError(f"hparams not found: {hparams_path}")
    if method == "MEND":
        raise RuntimeError("MEND requires a trained editor checkpoint; no checkpoint was configured for this run.")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for public editing baselines.")
    hparams = load_hparams(method, hparams_path, args.model_path, args.device)
    start = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        kwargs: Dict[str, Any] = {"test_generation": not args.disable_generation_test}
        if method == "IKE":
            kwargs["train_ds"] = requests
        with contextlib.redirect_stdout(log):
            editor = BaseEditor.from_hparams(hparams)
            metrics, _, _ = editor.edit_requests(requests, sequential_edit=args.sequential_edit, verbose=False, **kwargs)
        elapsed = time.time() - start
        log.write(f"elapsed_sec={elapsed:.2f}\n")
    per_case = []
    for request, metric in zip(requests, metrics):
        per_case.append(
            {
                "case_id": request.get("case_id"),
                "dataset": args.dataset_name,
                "method": display_method_name(method, args),
                "base_method": method,
                "request": request,
                "metrics": to_builtin(metric),
            }
        )
    write_jsonl(method_dir / "per_case_results.jsonl", per_case)
    summary = {
        "status": "ok",
        "method": display_method_name(method, args),
        "base_method": method,
        "num_cases": len(per_case),
        "elapsed_sec": elapsed,
        "per_case_results": str(method_dir / "per_case_results.jsonl"),
    }
    write_json(method_dir / "summary.json", summary)


def main() -> int:
    args = parse_args()
    if args.max_cases > 1000:
        raise ValueError("--max_cases must be <= 1000")
    records = load_dataset(args.dataset_path)[: args.max_cases]
    if args.smoke_only:
        records = records[:5]
    requests = [to_request(record) for record in records]
    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_manifest.json", {
        "dataset_path": args.dataset_path,
        "dataset_name": args.dataset_name,
        "model_path": args.model_path,
        "model_name": args.model_name,
        "methods": methods,
        "num_requests": len(requests),
        "dry_run": args.dry_run,
        "smoke_only": args.smoke_only,
        "sequential_edit": args.sequential_edit,
    })
    if args.dry_run:
        for method in methods:
            method_dir = output_dir / display_method_name(method, args)
            method_dir.mkdir(parents=True, exist_ok=True)
            write_json(method_dir / "method_config.json", {
                "method": method,
                "display_method": display_method_name(method, args),
                "hparams_path": str(method_hparams_path(method, args.model_name)),
                "num_cases": len(requests),
                "status": "dry_run_only",
            })
        print(f"dry_run_manifest: {output_dir / 'run_manifest.json'}")
        return 0

    if args.isolate_methods and len(methods) > 1:
        return run_isolated_methods(args, methods)

    for method in methods:
        method_dir = output_dir / display_method_name(method, args)
        if args.resume_skip_completed and completed_summary_exists(method_dir):
            print(f"[SKIP] {method}: completed summary exists at {method_dir / 'summary.json'}")
            continue
        try:
            run_method(method, requests, args, method_dir)
            print(f"[OK] {method}: {method_dir}")
        except Exception as exc:
            method_dir.mkdir(parents=True, exist_ok=True)
            failure = {
                "status": "failed",
                "method": method,
                "error": repr(exc),
                "traceback": traceback.format_exc(),
                "num_cases_attempted": len(requests),
            }
            write_json(method_dir / "summary.json", failure)
            (method_dir / "run_log.txt").write_text(failure["traceback"], encoding="utf-8")
            print(f"[FAIL] {method}: {exc!r}")
            return 1
        finally:
            release_cuda_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
