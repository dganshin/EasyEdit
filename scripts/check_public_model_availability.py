import argparse
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


GPTJ_REPO = "EleutherAI/gpt-j-6b"
LLAMA_BACKUP_REPO = "NousResearch/Llama-2-7b-hf"
GPTJ_PATHS = [
    "/root/autodl-tmp/models/gpt-j-6B",
    "/root/autodl-tmp/models/GPT-J-6B",
]
QWEN_PATHS = [
    "/root/autodl-tmp/models/Qwen2.5-7B",
]
LLAMA_PATHS = [
    "/root/autodl-tmp/models/Llama-2-7b-hf",
    "/root/autodl-tmp/models/llama-2-7b",
    "/root/autodl-tmp/models/LLaMA-2-7B",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check/download public benchmark model availability without GPU.")
    parser.add_argument("--output_dir", default="artifacts/public_benchmarks_20260622", type=str)
    parser.add_argument("--download_gptj", action="store_true")
    parser.add_argument("--gptj_target", default="/root/autodl-tmp/models/gpt-j-6B", type=str)
    parser.add_argument("--download_llama_backup", action="store_true")
    parser.add_argument("--llama_target", default="/root/autodl-tmp/models/Llama-2-7b-hf-nousresearch", type=str)
    parser.add_argument("--hf_endpoint", default=None, type=str, help="Optional HF endpoint, e.g. https://hf-mirror.com")
    parser.add_argument("--skip_transformers_load", action="store_true")
    return parser.parse_args()


def path_status(paths: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for raw in paths:
        path = Path(raw)
        rows.append(
            {
                "path": raw,
                "exists": path.exists(),
                "is_dir": path.is_dir(),
                "num_files": len(list(path.iterdir())) if path.exists() and path.is_dir() else None,
            }
        )
    return rows


def hf_cache_candidates(repo_id: str) -> List[str]:
    candidates = []
    hf_home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
    hub = Path(hf_home) / "hub"
    normalized = repo_id.replace("/", "--")
    for root in [hub, Path.home() / ".cache" / "huggingface" / "hub"]:
        if not root.exists():
            continue
        for path in root.glob(f"models--{normalized}*"):
            candidates.append(str(path))
    return sorted(set(candidates))


GPTJ_ALLOW_PATTERNS = [
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.json",
    "merges.txt",
    "pytorch_model.bin",
    "model.safetensors",
    "*.safetensors",
]


def snapshot_to_dir(repo_id: str, target: str, allow_patterns: List[str] | None = None) -> Dict[str, Any]:
    from huggingface_hub import snapshot_download

    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    local_dir = snapshot_download(
        repo_id,
        local_dir=str(target_path),
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=allow_patterns,
    )
    return {"downloaded": True, "repo_id": repo_id, "local_dir": local_dir, "allow_patterns": allow_patterns}


def safe_snapshot(repo_id: str, target: str, allow_patterns: List[str] | None = None) -> Dict[str, Any]:
    try:
        return snapshot_to_dir(repo_id, target, allow_patterns=allow_patterns)
    except Exception as exc:
        return {
            "downloaded": False,
            "repo_id": repo_id,
            "target": target,
            "error": repr(exc),
            "traceback_tail": traceback.format_exc()[-4000:],
        }


def transformers_config_check(model_path: str) -> Dict[str, Any]:
    try:
        from transformers import AutoConfig, AutoTokenizer
    except Exception as exc:
        return {"checked": False, "ok": False, "reason": f"transformers unavailable: {exc!r}"}
    try:
        cfg = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
        tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        return {
            "checked": True,
            "ok": True,
            "model_type": getattr(cfg, "model_type", None),
            "vocab_size": getattr(tok, "vocab_size", None),
        }
    except Exception as exc:
        return {"checked": True, "ok": False, "reason": repr(exc)}


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Model Availability Report",
        "",
        f"- created_at: `{payload['created_at']}`",
        f"- download_gptj: `{payload['download_gptj']}`",
        f"- hf_endpoint: `{payload.get('hf_endpoint')}`",
        "",
        "## GPT-J-6B",
        "",
    ]
    for row in payload["gptj_paths"]:
        lines.append(f"- `{row['path']}` exists={row['exists']} files={row['num_files']}")
    lines.extend(
        [
            "",
            f"- HF cache candidates: `{payload['gptj_hf_cache_candidates']}`",
            f"- download result: `{payload.get('gptj_download_result')}`",
            f"- config/tokenizer check: `{payload.get('gptj_config_check')}`",
            "",
            "## LLaMA-2 Backup",
            "",
            f"- backup repo: `{payload.get('llama_backup_repo')}`",
            f"- download result: `{payload.get('llama_download_result')}`",
            "",
            "## Qwen2.5-7B",
            "",
        ]
    )
    for row in payload["qwen_paths"]:
        lines.append(f"- `{row['path']}` exists={row['exists']} files={row['num_files']}")
    lines.extend(["", "## LLaMA-2-7B Probe Only", ""])
    for row in payload["llama_paths"]:
        lines.append(f"- `{row['path']}` exists={row['exists']} files={row['num_files']}")
    lines.extend(
        [
            "",
            "## Server Download Command",
            "",
            "```bash",
            "cd /root/autodl-tmp/projects/EasyEdit",
            "bash /root/start_mihomo.sh || true",
            "conda activate easyedit",
            "export HF_HOME=/root/autodl-tmp/hf_cache/hf",
            "export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers",
            "export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets",
            "export http_proxy=http://127.0.0.1:7890",
            "export https_proxy=http://127.0.0.1:7890",
            "export HTTP_PROXY=http://127.0.0.1:7890",
            "export HTTPS_PROXY=http://127.0.0.1:7890",
            "export HF_ENDPOINT=https://hf-mirror.com",
            "python3 scripts/check_public_model_availability.py --download_gptj --hf_endpoint https://hf-mirror.com",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.hf_endpoint:
        os.environ["HF_ENDPOINT"] = args.hf_endpoint
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "download_gptj": args.download_gptj,
        "download_llama_backup": args.download_llama_backup,
        "hf_endpoint": os.environ.get("HF_ENDPOINT"),
        "gptj_repo": GPTJ_REPO,
        "llama_backup_repo": LLAMA_BACKUP_REPO,
        "gptj_paths": path_status(GPTJ_PATHS),
        "qwen_paths": path_status(QWEN_PATHS),
        "llama_paths": path_status(LLAMA_PATHS),
        "gptj_hf_cache_candidates": hf_cache_candidates(GPTJ_REPO),
    }
    if args.download_gptj:
        payload["gptj_download_result"] = safe_snapshot(GPTJ_REPO, args.gptj_target, allow_patterns=GPTJ_ALLOW_PATTERNS)
        payload["gptj_paths"] = path_status(GPTJ_PATHS)
    else:
        payload["gptj_download_result"] = None
    if args.download_llama_backup:
        payload["llama_download_result"] = safe_snapshot(LLAMA_BACKUP_REPO, args.llama_target)
        payload["llama_paths"] = path_status([*LLAMA_PATHS, args.llama_target])
    else:
        payload["llama_download_result"] = None

    gptj_existing = next((row["path"] for row in payload["gptj_paths"] if row["exists"]), args.gptj_target)
    if args.skip_transformers_load:
        payload["gptj_config_check"] = {"checked": False, "ok": None, "reason": "skipped"}
    else:
        payload["gptj_config_check"] = transformers_config_check(gptj_existing)

    json_path = output_dir / "model_availability_report.json"
    md_path = output_dir / "MODEL_AVAILABILITY_REPORT.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    write_report(md_path, payload)
    print(f"model_availability_json: {json_path}")
    print(f"model_availability_md: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
