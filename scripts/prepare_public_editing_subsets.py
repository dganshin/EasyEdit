import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


COUNTERFACT_SOURCE = "azhx/counterfact"
ZSRE_SOURCE = "wangzn2001/zsre"
ZSRE_DEV_FILE = "structured_zeroshot-dev-new_annotated_final.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare small public editing benchmark subsets.")
    parser.add_argument("--output_dir", default="artifacts/public_benchmarks_20260622", type=str)
    parser.add_argument("--counterfact_size", default=500, type=int)
    parser.add_argument("--zsre_size", default=500, type=int)
    parser.add_argument("--minimum_size", default=200, type=int)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--prefer_local", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_records(records: List[Dict[str, Any]]) -> str:
    payload = json.dumps(records, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def find_local_candidate(dataset_name: str) -> Optional[Path]:
    patterns = {
        "counterfact": ["*counterfact*.json", "*CounterFact*.json"],
        "zsre": ["*zsre*.json", "*zsre*.jsonl", "*ZsRE*.json"],
    }[dataset_name]
    roots = [Path("data"), Path("artifacts"), Path("examples")]
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for path in root.rglob(pattern):
                if path.is_file() and "public_benchmarks_20260622" not in str(path):
                    return path
    return None


def first_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, list):
        for item in value:
            text = first_text(item)
            if text:
                return text
    if isinstance(value, dict):
        for key in ("str", "answer", "text", "value"):
            if key in value:
                text = first_text(value[key])
                if text:
                    return text
    return None


def fill_prompt(template: str, subject: str) -> str:
    template = str(template)
    if "{}" in template:
        return template.format(subject)
    if subject and subject not in template:
        return f"{template} {subject}".strip()
    return template


def normalize_counterfact_record(record: Dict[str, Any], idx: int, dropped: Counter) -> Optional[Dict[str, Any]]:
    rewrite = record.get("requested_rewrite") or {}
    subject = first_text(rewrite.get("subject") or record.get("subject"))
    target_new = first_text(rewrite.get("target_new") or record.get("target_false"))
    ground_truth = first_text(rewrite.get("target_true") or record.get("target_true"))
    prompt_template = first_text(rewrite.get("prompt") or record.get("prompt"))
    if not (subject and target_new and ground_truth and prompt_template):
        dropped["missing_required_fields"] += 1
        return None
    prompt = fill_prompt(prompt_template, subject)
    if subject not in prompt:
        dropped["subject_not_in_prompt"] += 1
        return None
    rephrases = record.get("paraphrase_prompts") or record.get("generation_prompts") or []
    rephrases = [str(item).strip() for item in rephrases if str(item).strip()]
    if not rephrases:
        rephrases = [prompt]
    locality = [
        {"prompt": str(item).strip(), "ground_truth": None, "metric": "pre_post_consistency"}
        for item in (record.get("neighborhood_prompts") or [])[:5]
        if str(item).strip()
    ]
    return {
        "case_id": f"counterfact_{idx:05d}",
        "source_case_id": record.get("case_id", idx),
        "dataset": "counterfact",
        "prompt": prompt,
        "subject": subject,
        "target_new": target_new,
        "ground_truth": ground_truth,
        "rephrase_prompt": rephrases[:3],
        "locality": locality,
        "portability": [],
        "source": COUNTERFACT_SOURCE,
    }


def load_counterfact_from_hf(size: int, seed: int, dropped: Counter) -> List[Dict[str, Any]]:
    from datasets import load_dataset

    ds = load_dataset(COUNTERFACT_SOURCE, split="train")
    records = [dict(item) for item in ds]
    random.Random(seed).shuffle(records)
    normalized: List[Dict[str, Any]] = []
    for item in records:
        row = normalize_counterfact_record(item, len(normalized), dropped)
        if row:
            normalized.append(row)
        if len(normalized) >= size:
            break
    return normalized


def normalize_zsre_record(
    record: Dict[str, Any],
    idx: int,
    locality_seed: Optional[Dict[str, Any]],
    dropped: Counter,
) -> Optional[Dict[str, Any]]:
    prompt = first_text(record.get("input"))
    ground_truth = first_text(record.get("output"))
    alternatives = record.get("alternatives") or []
    target_new = first_text(alternatives)
    provenance = None
    output = record.get("output")
    if isinstance(output, list) and output and isinstance(output[0], dict):
        provs = output[0].get("provenance") or []
        if provs and isinstance(provs[0], dict):
            provenance = provs[0]
    subject = first_text((provenance or {}).get("title"))
    if not subject:
        dropped["missing_subject"] += 1
        return None
    if not (prompt and ground_truth and target_new):
        dropped["missing_required_fields"] += 1
        return None
    if subject not in prompt:
        dropped["subject_not_in_prompt"] += 1
        return None
    rephrases = record.get("filtered_rephrases") or record.get("rephrases") or []
    rephrases = [str(item).strip() for item in rephrases if str(item).strip() and subject in str(item)]
    if not rephrases:
        rephrases = [prompt]
    locality: List[Dict[str, Any]] = []
    if locality_seed is not None:
        loc_prompt = first_text(locality_seed.get("input"))
        loc_answer = first_text(locality_seed.get("output"))
        if loc_prompt and loc_answer:
            locality.append({"prompt": loc_prompt, "ground_truth": loc_answer, "metric": "target_contains"})
    return {
        "case_id": f"zsre_{idx:05d}",
        "source_case_id": record.get("id", idx),
        "dataset": "zsre",
        "prompt": prompt,
        "subject": subject,
        "target_new": target_new,
        "ground_truth": ground_truth,
        "rephrase_prompt": rephrases[:3],
        "locality": locality,
        "portability": [],
        "source": f"{ZSRE_SOURCE}/{ZSRE_DEV_FILE}",
    }


def load_zsre_from_hf(size: int, seed: int, dropped: Counter) -> List[Dict[str, Any]]:
    from huggingface_hub import hf_hub_download

    path = Path(hf_hub_download(ZSRE_SOURCE, ZSRE_DEV_FILE, repo_type="dataset"))
    raw_records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    random.Random(seed).shuffle(raw_records)
    normalized: List[Dict[str, Any]] = []
    for pos, item in enumerate(raw_records):
        locality_seed = raw_records[(pos + 1) % len(raw_records)] if raw_records else None
        row = normalize_zsre_record(item, len(normalized), locality_seed, dropped)
        if row:
            normalized.append(row)
        if len(normalized) >= size:
            break
    return normalized


def enforce_minimum(name: str, records: List[Dict[str, Any]], minimum: int) -> None:
    if len(records) < minimum:
        raise RuntimeError(f"{name} subset has {len(records)} records, below minimum {minimum}")


def write_report(path: Path, stats: Dict[str, Any]) -> None:
    lines = [
        "# Public Subset Prep Report",
        "",
        "## Scope",
        "",
        "本轮只构造 CounterFact 与 zsRE small subset，不运行全量 benchmark，不下载 The Pile/Enron 全量。",
        "",
        "## Outputs",
        "",
        f"- CounterFact: `{stats['counterfact']['path']}`",
        f"- zsRE: `{stats['zsre']['path']}`",
        f"- Stats: `{stats['stats_path']}`",
        "",
        "## Dataset Summary",
        "",
        "| dataset | records | source | sha256 | dropped reasons |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for key in ["counterfact", "zsre"]:
        item = stats[key]
        lines.append(
            f"| {key} | {item['num_records']} | `{item['source']}` | `{item['sha256'][:12]}...` | `{item['dropped_reasons']}` |"
        )
    lines.extend(
        [
            "",
            "## Field Mapping",
            "",
            "- CounterFact: `requested_rewrite.prompt` + `subject` -> `prompt`; `target_new.str` -> `target_new`; `target_true.str` -> `ground_truth`; `paraphrase_prompts` -> `rephrase_prompt`。",
            "- zsRE: `input` -> `prompt`; `alternatives[0]` -> `target_new`; `output[0].answer` -> `ground_truth`; `filtered_rephrases` -> `rephrase_prompt`; provenance title -> `subject`。",
            "- CounterFact locality prompts lack explicit answers in the selected HF source, so they are marked for pre/post consistency rather than answer contains.",
            "",
            "## Interpretation",
            "",
            "CounterFact 是公开事实编辑 benchmark，zsRE 是问答式知识编辑 benchmark。二者不包含本文 synthetic PII 设置，不应与 privacy leakage 指标混成同一张主结果表。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.counterfact_size < args.minimum_size or args.zsre_size < args.minimum_size:
        raise ValueError("requested subset size must be >= minimum_size")
    if args.counterfact_size > 1000 or args.zsre_size > 1000:
        raise ValueError("subset size must not exceed 1000")

    dropped_cf: Counter = Counter()
    dropped_zsre: Counter = Counter()
    counterfact = load_counterfact_from_hf(args.counterfact_size, args.seed, dropped_cf)
    zsre = load_zsre_from_hf(args.zsre_size, args.seed, dropped_zsre)
    enforce_minimum("CounterFact", counterfact, args.minimum_size)
    enforce_minimum("zsRE", zsre, args.minimum_size)

    cf_path = output_dir / f"counterfact_{len(counterfact)}.json"
    zsre_path = output_dir / f"zsre_{len(zsre)}.json"
    write_json(cf_path, {"dataset": "counterfact", "source": COUNTERFACT_SOURCE, "num_records": len(counterfact), "records": counterfact})
    write_json(zsre_path, {"dataset": "zsre", "source": f"{ZSRE_SOURCE}/{ZSRE_DEV_FILE}", "num_records": len(zsre), "records": zsre})
    stats_path = output_dir / "public_subset_stats.json"
    stats = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "counterfact": {
            "path": str(cf_path),
            "source": COUNTERFACT_SOURCE,
            "num_records": len(counterfact),
            "sha256": sha256_file(cf_path),
            "records_sha256": sha256_records(counterfact),
            "dropped_reasons": dict(dropped_cf),
        },
        "zsre": {
            "path": str(zsre_path),
            "source": f"{ZSRE_SOURCE}/{ZSRE_DEV_FILE}",
            "num_records": len(zsre),
            "sha256": sha256_file(zsre_path),
            "records_sha256": sha256_records(zsre),
            "dropped_reasons": dict(dropped_zsre),
        },
        "stats_path": str(stats_path),
        "minimum_size": args.minimum_size,
        "seed": args.seed,
    }
    write_json(stats_path, stats)
    write_report(output_dir / "PUBLIC_SUBSET_PREP_REPORT.md", stats)
    print(f"counterfact_json: {cf_path}")
    print(f"zsre_json: {zsre_path}")
    print(f"stats_json: {stats_path}")
    print(f"report: {output_dir / 'PUBLIC_SUBSET_PREP_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
