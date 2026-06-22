import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate v2 LoRA/SFT sanitization baseline.")
    parser.add_argument("--train_jsonl", default="artifacts/data_v2_lora_sanitization/train.jsonl", type=str)
    parser.add_argument("--dev_jsonl", default="artifacts/data_v2_lora_sanitization/dev.jsonl", type=str)
    parser.add_argument("--dataset", default="artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json", type=str)
    parser.add_argument("--model_path", default="/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged", type=str)
    parser.add_argument("--hparams", default="hparams/LoRA/qwen2.5-7b.yaml", type=str)
    parser.add_argument("--output_dir", default="/root/autodl-tmp/outputs/easyedit/v2_lora_sanitization", type=str)
    parser.add_argument("--artifact_dir", default="artifacts/run_20260622_v2_lora_sanitization", type=str)
    parser.add_argument("--device", default="0", type=str)
    parser.add_argument("--rank", default=8, type=int)
    parser.add_argument("--batch_size", default=4, type=int)
    parser.add_argument("--num_steps", default=200, type=int)
    parser.add_argument("--max_new_tokens", default=32, type=int)
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def convert_train_data(source: Path, target: Path) -> int:
    rows = read_jsonl(source)
    converted = []
    for item in rows:
        converted.append(
            {
                "case_id": item.get("case_id"),
                "person_id": item.get("person_id"),
                "name": item.get("name") or item.get("person_id") or "",
                "prompt": item["instruction"],
                "target": item["output"],
                "sensitivity": item.get("sensitivity"),
                "split_source": item.get("split_source"),
            }
        )
    write_jsonl(target, converted)
    return len(converted)


def run(command: List[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write("$ " + " ".join(command) + "\n")
        log.flush()
        proc = subprocess.run(command, text=True, stdout=log, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(command)}")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    artifact_dir = Path(args.artifact_dir)
    log_dir = output_dir / "logs"
    adapter_dir = output_dir / "adapter"
    converted_train = output_dir / "lora_sanitization_train_converted.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    num_train = convert_train_data(Path(args.train_jsonl), converted_train)

    train_cmd = [
        sys.executable,
        "scripts/train_lora_privacy_injection.py",
        "--train_data",
        str(converted_train),
        "--hparams",
        args.hparams,
        "--model_path",
        args.model_path,
        "--output_dir",
        str(adapter_dir),
        "--device",
        args.device,
        "--rank",
        str(args.rank),
        "--batch_size",
        str(args.batch_size),
        "--num_steps",
        str(args.num_steps),
        "--lora_scope",
        "mlp_only",
        "--shuffle",
    ]
    private_predictions = output_dir / "privacy_predictions_v2_lora_sanitization_full.jsonl"
    private_eval = output_dir / "privacy_leakage_eval_v2_lora_sanitization_full.json"
    public_predictions = output_dir / "public_predictions_v2_lora_sanitization.jsonl"
    public_eval = output_dir / "public_retain_eval_v2_lora_sanitization.json"
    gen_private_cmd = [
        sys.executable,
        "scripts/run_privacy_generation.py",
        "--dataset",
        args.dataset,
        "--model_path",
        args.model_path,
        "--lora_adapter_path",
        str(adapter_dir),
        "--device",
        args.device,
        "--output_path",
        str(private_predictions),
        "--mode",
        "private",
        "--batch_size",
        "16",
        "--max_new_tokens",
        str(args.max_new_tokens),
    ]
    eval_private_cmd = [
        sys.executable,
        "scripts/evaluate_privacy_leakage.py",
        "--dataset",
        args.dataset,
        "--predictions",
        str(private_predictions),
        "--output_path",
        str(private_eval),
    ]
    gen_public_cmd = [
        sys.executable,
        "scripts/run_privacy_generation.py",
        "--dataset",
        args.dataset,
        "--model_path",
        args.model_path,
        "--lora_adapter_path",
        str(adapter_dir),
        "--device",
        args.device,
        "--output_path",
        str(public_predictions),
        "--mode",
        "public",
        "--batch_size",
        "16",
        "--max_new_tokens",
        str(args.max_new_tokens),
    ]
    eval_public_cmd = [
        sys.executable,
        "scripts/evaluate_public_retain.py",
        "--dataset",
        args.dataset,
        "--predictions",
        str(public_predictions),
        "--output_path",
        str(public_eval),
    ]
    manifest = {
        "train_jsonl": args.train_jsonl,
        "dev_jsonl": args.dev_jsonl,
        "converted_train": str(converted_train),
        "num_train_records": num_train,
        "model_path": args.model_path,
        "adapter_dir": str(adapter_dir),
        "rank": args.rank,
        "batch_size": args.batch_size,
        "num_steps": args.num_steps,
        "dry_run": args.dry_run,
        "commands": {
            "train": train_cmd,
            "generate_private": gen_private_cmd,
            "evaluate_private": eval_private_cmd,
            "generate_public": gen_public_cmd,
            "evaluate_public": eval_public_cmd,
        },
    }
    write_json(output_dir / "v2_lora_sanitization_manifest.json", manifest)
    write_json(artifact_dir / "v2_lora_sanitization_manifest.json", manifest)
    if args.dry_run:
        print(f"dry_run_manifest: {output_dir / 'v2_lora_sanitization_manifest.json'}")
        return 0
    run(train_cmd, log_dir / "train.log")
    run(gen_private_cmd, log_dir / "generate_private.log")
    run(eval_private_cmd, log_dir / "evaluate_private.log")
    run(gen_public_cmd, log_dir / "generate_public.log")
    run(eval_public_cmd, log_dir / "evaluate_public.log")
    summary = {
        "private_eval": str(private_eval),
        "public_eval": str(public_eval),
        "adapter_dir": str(adapter_dir),
        "status": "ok",
    }
    write_json(output_dir / "v2_lora_sanitization_summary.json", summary)
    for source in [private_eval, public_eval, output_dir / "v2_lora_sanitization_summary.json", output_dir / "v2_lora_sanitization_manifest.json"]:
        target = artifact_dir / source.name
        target.write_bytes(source.read_bytes())
    print(f"summary: {output_dir / 'v2_lora_sanitization_summary.json'}")
    print(f"artifact_dir: {artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
