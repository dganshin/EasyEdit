import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


EXPECTED_SCALE = {
    "people": 100,
    "private_facts": 200,
    "public_facts": 840,
    "flat_cases": 1040,
    "public_type_counts": {
        "general_knowledge": 40,
        "same_relation_other_subject": 400,
        "same_subject_public": 400,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight checks for v2 MEMIT direct-only baseline.")
    parser.add_argument("--dataset", default="artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json")
    parser.add_argument("--requests", default="artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json")
    parser.add_argument("--model_path", default="/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged")
    parser.add_argument("--hparams", default="hparams/MEMIT/qwen2.5-7b.yaml")
    parser.add_argument("--output_dir", default="/root/autodl-tmp/outputs/easyedit/v2_memit_direct")
    parser.add_argument("--artifact_dir", default="artifacts/run_20260617_v2_memit_direct")
    parser.add_argument("--json_out", default=None, help="Machine-readable report path.")
    parser.add_argument("--output_json", default=None, help="Deprecated alias for --json_out.")
    parser.add_argument("--allow_dirty_git", action="store_true")
    parser.add_argument("--allow_existing_output_dir", action="store_true")
    parser.add_argument("--allow_missing_model", action="store_true")
    parser.add_argument("--allow_missing_stats", action="store_true")
    return parser.parse_args()


def run_cmd(cmd: List[str]) -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"returncode": -1, "stdout": "", "stderr": str(exc)}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_requests(path: Path) -> List[Dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("requests"), list):
        return payload["requests"]
    raise ValueError(f"Unsupported requests format: {path}")


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def sha256_file(path: Path) -> Optional[str]:
    if not path_exists(path) or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scalar(value: str) -> Any:
    raw = value.strip().strip('"').strip("'")
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if raw.startswith("[") and raw.endswith("]"):
        return raw
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        result[key.strip()] = parse_scalar(value)
    return result


def person_id_from_case_id(case_id: Any) -> Optional[str]:
    text = str(case_id or "")
    parts = text.split("_")
    if len(parts) >= 2 and parts[0] == "person":
        return f"{parts[0]}_{parts[1]}"
    return None


def count_real_people(rows: List[Dict[str, Any]]) -> int:
    people = set()
    for row in rows:
        person_id = str(row.get("person_id") or "")
        if person_id.startswith("person_"):
            people.add(person_id)
            continue
        parsed = person_id_from_case_id(row.get("case_id"))
        if parsed:
            people.add(parsed)
    return len(people)


def dataset_scale(dataset: Dict[str, Any]) -> Dict[str, Any]:
    flat_cases = dataset.get("flat_cases", [])
    private_cases = [row for row in flat_cases if row.get("sensitivity") == "private"]
    public_cases = [row for row in flat_cases if row.get("sensitivity") == "public"]
    return {
        "people": len(dataset.get("people", [])),
        "private_facts": len(private_cases),
        "public_facts": len(public_cases),
        "flat_cases": len(flat_cases),
        "public_type_counts": dict(sorted(Counter(str(row.get("public_type") or "unknown") for row in public_cases).items())),
    }


def resolve_stats_path(hparams_path: Path, hparams: Dict[str, Any]) -> Path:
    stats_dir = str(hparams.get("stats_dir") or "./data/stats")
    path = Path(stats_dir)
    if not path.is_absolute():
        path = (hparams_path.parent.parent.parent / path).resolve()
    return path


def stats_has_files(path: Path) -> bool:
    if not path_exists(path) or not path.is_dir():
        return False
    return any(item.is_file() for item in path.rglob("*"))


def cuda_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {"visible": False, "warning": "CUDA not checked via torch"}
    try:
        import torch  # type: ignore

        info = {
            "visible": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "torch_version": getattr(torch, "__version__", "unknown"),
            "warning": "" if torch.cuda.is_available() else "CUDA is not visible in this environment",
        }
    except Exception as exc:
        info["warning"] = f"torch unavailable or CUDA check failed: {exc}"
    return info


def add_check(report: Dict[str, Any], name: str, passed: bool, severity: str, message: str) -> None:
    report["checks"][name] = {
        "passed": bool(passed),
        "severity": severity,
        "message": message,
    }


def print_readable(report: Dict[str, Any]) -> None:
    print("# v2 MEMIT Direct Preflight")
    print(f"passed: {report['passed']}")
    for name, item in report["checks"].items():
        status = "PASS" if item["passed"] else ("WARN" if item["severity"] == "warning" else "FAIL")
        print(f"- [{status}] {name}: {item['message']}")
    if report["fatal_errors"]:
        print("fatal_errors:")
        for item in report["fatal_errors"]:
            print(f"- {item}")
    if report["warnings"]:
        print("warnings:")
        for item in report["warnings"]:
            print(f"- {item}")


def main() -> int:
    args = parse_args()
    json_out = args.json_out or args.output_json
    dataset_path = Path(args.dataset)
    requests_path = Path(args.requests)
    hparams_path = Path(args.hparams)
    model_path = Path(args.model_path)
    output_dir = Path(args.output_dir)
    artifact_dir = Path(args.artifact_dir)

    git_commit = run_cmd(["git", "rev-parse", "--short", "HEAD"])
    git_status = run_cmd(["git", "status", "--short"])
    dirty = bool(git_status["stdout"])
    hparams = load_simple_yaml(hparams_path)
    mom2_adjustment = bool(hparams.get("mom2_adjustment", False))
    stats_path = resolve_stats_path(hparams_path, hparams)
    stats_exists = stats_has_files(stats_path)
    dataset = load_json(dataset_path) if path_exists(dataset_path) else {}
    requests = load_requests(requests_path) if path_exists(requests_path) else []
    scale = dataset_scale(dataset) if dataset else {}
    request_people = count_real_people(requests)
    request_cases = len({str(row.get("case_id")) for row in requests if row.get("case_id")})
    request_attacks = Counter(str(row.get("attack_type") or "unknown") for row in requests)
    direct_like_requests = len(requests) == 40 and request_people == 20 and request_cases == 40

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "requests_path": str(requests_path),
        "requests_sha256": sha256_file(requests_path),
        "model_path": str(model_path),
        "hparams_path": str(hparams_path),
        "hparams": {
            "alg_name": hparams.get("alg_name"),
            "mom2_adjustment": mom2_adjustment,
            "stats_dir": hparams.get("stats_dir", "./data/stats"),
            "resolved_stats_path": str(stats_path),
            "mom2_dataset": hparams.get("mom2_dataset"),
            "mom2_n_samples": hparams.get("mom2_n_samples"),
        },
        "output_dir": str(output_dir),
        "artifact_dir": str(artifact_dir),
        "dataset_scale": scale,
        "request_summary": {
            "num_requests": len(requests),
            "num_people": request_people,
            "num_cases": request_cases,
            "by_attack_type": dict(sorted(request_attacks.items())),
            "direct_like_note": "ROME direct requests do not carry attack_type, but are generated from canonical direct QA prompts.",
        },
        "git": {
            "commit": git_commit["stdout"] if git_commit["returncode"] == 0 else None,
            "dirty": dirty,
            "status_short": git_status["stdout"],
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
        },
        "cuda": cuda_info(),
        "allowances": {
            "allow_dirty_git": args.allow_dirty_git,
            "allow_existing_output_dir": args.allow_existing_output_dir,
            "allow_missing_model": args.allow_missing_model,
            "allow_missing_stats": args.allow_missing_stats,
        },
        "checks": {},
        "fatal_errors": [],
        "warnings": [],
    }

    model_exists = path_exists(model_path)

    add_check(report, "dataset_exists", path_exists(dataset_path), "fatal", f"dataset path: {dataset_path}")
    add_check(report, "dataset_scale_is_v2_100_people", scale == EXPECTED_SCALE, "fatal", json.dumps(scale, ensure_ascii=False))
    add_check(report, "requests_exists", path_exists(requests_path), "fatal", f"request path: {requests_path}")
    add_check(report, "requests_are_rome_direct_40", direct_like_requests, "fatal", json.dumps(report["request_summary"], ensure_ascii=False))
    add_check(report, "model_exists", model_exists or args.allow_missing_model, "fatal", f"model path exists={model_exists}")
    add_check(report, "hparams_exists", path_exists(hparams_path), "fatal", f"hparams path: {hparams_path}")
    add_check(report, "mom2_adjustment_enabled", mom2_adjustment, "warning", f"mom2_adjustment={mom2_adjustment}")
    add_check(report, "stats_available", (not mom2_adjustment) or stats_exists or args.allow_missing_stats, "fatal", f"stats path: {stats_path}, exists_with_files={stats_exists}")
    add_check(report, "output_dir_safe", (not path_exists(output_dir)) or args.allow_existing_output_dir, "fatal", f"output_dir exists={path_exists(output_dir)}")
    add_check(report, "artifact_dir_safe", (not path_exists(artifact_dir)) or args.allow_existing_output_dir, "fatal", f"artifact_dir exists={path_exists(artifact_dir)}")
    add_check(report, "git_status_recorded", git_status["returncode"] == 0, "warning", "git status captured")
    add_check(report, "git_dirty_allowed", (not dirty) or args.allow_dirty_git, "warning", f"dirty={dirty}")
    add_check(report, "cuda_visible", bool(report["cuda"].get("visible")), "warning", report["cuda"].get("warning") or "CUDA visible")

    for name, item in report["checks"].items():
        if item["passed"]:
            continue
        if item["severity"] == "fatal":
            report["fatal_errors"].append(f"{name}: {item['message']}")
        else:
            report["warnings"].append(f"{name}: {item['message']}")

    report["passed"] = not report["fatal_errors"]
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print_readable(report)
    print("\n# JSON")
    print(output)
    if json_out:
        out_path = Path(json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
