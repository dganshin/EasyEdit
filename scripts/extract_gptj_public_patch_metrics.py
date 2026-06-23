import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


OUT_DIR = Path("artifacts/gptj_fast_patch_20260623")
PAPER_TABLE_DIR = Path("artifacts/paper_assets_20260623/tables")
ART_ROOTS = [
    Path("artifacts/public_benchmarks_20260623_200"),
    Path("artifacts/final_comparison_20260623_200"),
    Path("artifacts/result_ledger_20260623"),
]
FIELDS = [
    "model",
    "dataset",
    "method",
    "n_cases",
    "reliability",
    "generalization",
    "locality",
    "status",
    "failure_reason",
    "source_file",
    "runtime_sec",
]
TARGETS = [
    ("counterfact", "ROME"),
    ("counterfact", "FT"),
    ("counterfact", "MEMIT"),
    ("zsre", "ROME"),
    ("zsre", "FT"),
    ("zsre", "MEMIT"),
]
MISSING = "missing"


def clean(value: Any) -> str:
    if value is None or value == "":
        return MISSING
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def read_json(path: Path) -> Optional[Any]:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, MISSING) for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def md_table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, MISSING)).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines)


def avg(values: List[float]) -> str:
    if not values:
        return MISSING
    return f"{sum(values) / len(values):.6g}"


def listify(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def metric_float(value: Any) -> Optional[float]:
    items = listify(value)
    if not items:
        return None
    try:
        return float(items[0])
    except Exception:
        return None


def aggregate_per_case(path: Path) -> Dict[str, str]:
    rewrite: List[float] = []
    rephrase: List[float] = []
    locality: List[float] = []
    count = 0
    if not path.exists():
        return {"n_cases": MISSING, "reliability": MISSING, "generalization": MISSING, "locality": MISSING}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            count += 1
            payload = json.loads(line)
            post = payload.get("metrics", {}).get("post", {})
            rv = metric_float(post.get("rewrite_acc"))
            gv = metric_float(post.get("rephrase_acc"))
            if rv is not None:
                rewrite.append(rv)
            if gv is not None:
                rephrase.append(gv)
            loc = post.get("locality") or {}
            for item in loc.values() if isinstance(loc, dict) else []:
                if isinstance(item, dict):
                    for key in ("acc", "accuracy", "correct"):
                        lv = metric_float(item.get(key))
                        if lv is not None:
                            locality.append(lv)
                else:
                    lv = metric_float(item)
                    if lv is not None:
                        locality.append(lv)
    return {
        "n_cases": str(count) if count else MISSING,
        "reliability": avg(rewrite),
        "generalization": avg(rephrase),
        "locality": avg(locality),
    }


def possible_method_dirs(dataset: str, method: str) -> List[Path]:
    dataset_variants = {
        "counterfact": ["gptj_counterfact", "gpt-j_counterfact", "gpt_j_counterfact", "GPT-J_counterfact", "gptj_CounterFact", "counterfact_gptj"],
        "zsre": ["gptj_zsre", "gpt-j_zsre", "gpt_j_zsre", "GPT-J_zsre", "gptj_ZsRE", "zsre_gptj"],
    }[dataset]
    paths: List[Path] = []
    for root in ART_ROOTS:
        for variant in dataset_variants:
            paths.append(root / variant / method)
    return paths


def row_from_summary(dataset: str, method: str, method_dir: Path) -> Dict[str, str]:
    summary_path = method_dir / "summary.json"
    summary = read_json(summary_path) or {}
    status = clean(summary.get("status"))
    per_case = Path(summary.get("per_case_results", method_dir / "per_case_results.jsonl"))
    if not per_case.is_absolute():
        per_case = method_dir / per_case.name if per_case.name else method_dir / "per_case_results.jsonl"
    agg = aggregate_per_case(per_case)
    failure = summary.get("error") or summary.get("failure_error") or MISSING
    return {
        "model": "GPT-J-6B",
        "dataset": f"{dataset}-200",
        "method": method,
        "n_cases": clean(summary.get("num_cases") or agg["n_cases"]),
        "reliability": agg["reliability"],
        "generalization": agg["generalization"],
        "locality": agg["locality"],
        "status": status,
        "failure_reason": clean(failure if status != "ok" else MISSING),
        "source_file": str(summary_path),
        "runtime_sec": clean(summary.get("elapsed_sec")),
    }


def discover_existing() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    missing: List[Dict[str, str]] = []
    seen = set()
    for dataset, method in TARGETS:
        found = None
        for method_dir in possible_method_dirs(dataset, method):
            if (method_dir / "summary.json").exists():
                found = method_dir
                break
        if found:
            rows.append(row_from_summary(dataset, method, found))
            seen.add((dataset, method))
        else:
            reason = "no summary.json found"
            if method in {"KN", "IKE"}:
                reason = "intentionally skipped in fast patch"
            missing.append(
                {
                    "model": "GPT-J-6B",
                    "dataset": f"{dataset}-200",
                    "method": method,
                    "n_cases": MISSING,
                    "reliability": MISSING,
                    "generalization": MISSING,
                    "locality": MISSING,
                    "status": "missing_artifact",
                    "failure_reason": reason,
                    "source_file": "gptj_fast_patch_expected_matrix",
                    "runtime_sec": MISSING,
                }
            )
    return rows, missing


def run_plan(rows: List[Dict[str, str]]) -> str:
    ok = {(row["dataset"].split("-")[0], row["method"]) for row in rows if row["status"] == "ok"}
    lines = [
        "# GPT-J Fast Patch Run Plan",
        "",
        "This plan skips KN/IKE and only targets GPT-J ROME/FT public editing rows.",
        "",
        "## Required next runs",
    ]
    targets = [("counterfact", "ROME"), ("counterfact", "FT"), ("zsre", "ROME"), ("zsre", "FT")]
    pending = []
    for dataset, method in targets:
        if (dataset, method) in ok:
            lines.append(f"- SKIP `{dataset} × {method}`: existing status=ok.")
        else:
            pending.append((dataset, method))
            lines.append(f"- RUN `{dataset} × {method}`.")
    lines += [
        "",
        "## Excluded",
        "",
        "- KN: excluded due to coarse-neuron search cost.",
        "- IKE: excluded due to embedding dependency path.",
        "- MEMIT: excluded unless hparams/stats/smoke are proven ready; default run keeps TRY_MEMIT=0.",
        "- Wrappers: excluded unless GPT-J ROME per_case exists and time remains.",
    ]
    if not pending:
        lines += ["", "All required fast patch rows are already present."]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    rows, missing = discover_existing()
    all_rows = [*rows, *missing]
    write_csv(OUT_DIR / "gptj_existing_metrics.csv", all_rows, FIELDS)
    write_text(OUT_DIR / "gptj_existing_metrics.md", md_table(all_rows, FIELDS))
    write_csv(OUT_DIR / "gptj_missing_matrix.csv", missing, FIELDS)
    write_text(OUT_DIR / "GPTJ_FAST_PATCH_RUN_PLAN.md", run_plan(rows))
    write_csv(OUT_DIR / "table_gptj_public_fast_patch.csv", all_rows, FIELDS)
    write_text(OUT_DIR / "table_gptj_public_fast_patch.md", md_table(all_rows, FIELDS))
    write_csv(PAPER_TABLE_DIR / "table_gptj_public_fast_patch.csv", all_rows, FIELDS)
    write_text(PAPER_TABLE_DIR / "table_gptj_public_fast_patch.md", md_table(all_rows, FIELDS))
    ok_count = sum(1 for row in rows if row["status"] == "ok")
    report = [
        "# GPT-J Existing Result Audit",
        "",
        f"- existing summaries found: `{len(rows)}`",
        f"- existing ok rows: `{ok_count}`",
        f"- missing target rows: `{len(missing)}`",
        "",
        "No GPU was used by this audit script. Missing values are written as `missing`, not zero.",
        "",
        "## Current rows",
        "",
        md_table(all_rows, FIELDS),
    ]
    write_text(OUT_DIR / "GPTJ_EXISTING_RESULT_AUDIT.md", "\n".join(report))
    print(f"wrote {OUT_DIR}")
    print(f"existing={len(rows)} ok={ok_count} missing={len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
