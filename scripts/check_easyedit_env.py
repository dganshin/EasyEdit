import argparse
import importlib
import json
import platform
import sys
from pathlib import Path
from typing import Iterable, Tuple


REQUIRED_IMPORTS = [
    "torch",
    "transformers",
    "easyeditor",
]


METHOD_TO_CLASS = {
    "ROME": "ROMEHyperParams",
    "MEMIT": "MEMITHyperParams",
    "FT": "FTHyperParams",
    "MEND": "MENDHyperParams",
    "LoRA": "LoRAHyperParams",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查 EasyEdit 环境、hparams 与本地 HuggingFace 模型目录。"
    )
    parser.add_argument("--model_path", type=str, default=None, help="本地模型目录")
    parser.add_argument("--method", type=str, default="ROME", help="编辑方法名，如 ROME/MEMIT/FT")
    parser.add_argument("--hparams", type=str, default=None, help="hparams yaml 路径")
    return parser.parse_args()


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def check_imports() -> Tuple[dict, list]:
    versions = {}
    failures = []
    for module_name in REQUIRED_IMPORTS:
        try:
            module = importlib.import_module(module_name)
            versions[module_name] = getattr(module, "__version__", "unknown")
        except Exception as exc:
            failures.append((module_name, repr(exc)))
    return versions, failures


def check_torch_runtime() -> None:
    print_header("Torch/CUDA")
    try:
        import torch
    except Exception as exc:
        print(f"torch 导入失败: {exc}")
        return

    print(f"torch.__version__: {torch.__version__}")
    print(f"torch.version.cuda: {torch.version.cuda}")
    print(f"cuda_available: {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("未检测到可用 CUDA。当前机器可继续做目录/依赖检查，但 ROME/MEMIT/FT 实际编辑建议在 AutoDL GPU 上执行。")
        return

    print(f"cuda_device_count: {torch.cuda.device_count()}")
    for idx in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(idx)
        total_gb = props.total_memory / (1024 ** 3)
        print(
            f"gpu[{idx}]: name={props.name}, total_memory_gb={total_gb:.2f}, "
            f"major={props.major}, minor={props.minor}"
        )


def _find_any(base: Path, patterns: Iterable[str]) -> list:
    hits = []
    for pattern in patterns:
        hits.extend(base.glob(pattern))
    return sorted({str(hit) for hit in hits})


def check_model_dir(model_path: Path) -> int:
    print_header("Model Directory")
    if not model_path.exists():
        print(f"模型路径不存在: {model_path}")
        return 2
    if not model_path.is_dir():
        print(f"模型路径不是目录: {model_path}")
        return 2

    print(f"model_path: {model_path}")

    config_file = model_path / "config.json"
    generation_config = model_path / "generation_config.json"
    tokenizer_hits = _find_any(
        model_path,
        [
            "tokenizer.json",
            "tokenizer.model",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.json",
            "merges.txt",
        ],
    )
    weight_hits = _find_any(
        model_path,
        [
            "*.safetensors",
            "*.bin",
            "*.pt",
            "*.pth",
            "*.safetensors.index.json",
            "*.bin.index.json",
        ],
    )

    print(f"config.json: {'OK' if config_file.exists() else 'MISSING'}")
    print(f"generation_config.json: {'OK' if generation_config.exists() else 'OPTIONAL/MISSING'}")
    print(f"tokenizer_files_found: {len(tokenizer_hits)}")
    for item in tokenizer_hits[:10]:
        print(f"  - {Path(item).name}")
    print(f"weight_files_found: {len(weight_hits)}")
    for item in weight_hits[:10]:
        print(f"  - {Path(item).name}")

    problems = []
    if not config_file.exists():
        problems.append("缺少 config.json")
    if not tokenizer_hits:
        problems.append("未找到 tokenizer 相关文件")
    if not weight_hits:
        problems.append("未找到模型权重文件（safetensors/bin/pt/pth 或索引文件）")

    if problems:
        print("模型目录检查失败:")
        for problem in problems:
            print(f"  - {problem}")
        return 2

    print("模型目录检查通过。")
    return 0


def check_hparams(method: str, hparams_path: Path) -> int:
    print_header("HParams")
    if not hparams_path.exists():
        print(f"hparams 文件不存在: {hparams_path}")
        return 2

    print(f"hparams_path: {hparams_path}")
    try:
        import yaml
        with hparams_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except Exception as exc:
        print(f"hparams 读取失败: {exc}")
        return 2

    if not isinstance(raw, dict):
        print("hparams 内容不是字典结构。")
        return 2

    print("关键字段:")
    for key in ["alg_name", "model_name", "tokenizer_name", "device", "stats_dir", "layers"]:
        if key in raw:
            print(f"  - {key}: {raw[key]}")

    expected = method.upper()
    actual = str(raw.get("alg_name", "")).upper()
    if actual and actual != expected:
        print(f"警告: --method={expected}，但 hparams.alg_name={actual}")

    try:
        import easyeditor

        cls_name = METHOD_TO_CLASS.get(expected)
        if cls_name and hasattr(easyeditor, cls_name):
            cls = getattr(easyeditor, cls_name)
            hp_obj = cls.from_hparams(str(hparams_path))
            print(f"from_hparams 加载成功: {cls_name}")
            print(f"loaded.model_name: {getattr(hp_obj, 'model_name', None)}")
            if hasattr(hp_obj, "tokenizer_name"):
                print(f"loaded.tokenizer_name: {getattr(hp_obj, 'tokenizer_name', None)}")
        else:
            print(f"未找到方法 {expected} 对应的 HyperParams 类，跳过 from_hparams 实测。")
    except Exception as exc:
        print(f"from_hparams 加载失败: {exc}")
        return 2

    return 0


def main() -> int:
    args = parse_args()

    print_header("System")
    print(f"python: {sys.version}")
    print(f"platform: {platform.platform()}")
    print(f"executable: {sys.executable}")

    versions, failures = check_imports()
    print_header("Imports")
    for name, version in versions.items():
        print(f"{name}: {version}")
    if failures:
        for name, err in failures:
            print(f"{name}: IMPORT FAILED -> {err}")

    check_torch_runtime()

    exit_code = 0
    if args.hparams:
        exit_code = max(exit_code, check_hparams(args.method, Path(args.hparams)))
    if args.model_path:
        exit_code = max(exit_code, check_model_dir(Path(args.model_path)))

    print_header("Summary")
    summary = {
        "method": args.method,
        "hparams": args.hparams,
        "model_path": args.model_path,
        "status": "ok" if exit_code == 0 and not failures else "warning" if exit_code == 0 else "error",
        "import_failures": failures,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if failures else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
