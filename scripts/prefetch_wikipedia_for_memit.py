import argparse
import json
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import HfApi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prefetch a fixed Wikipedia text subset to local jsonl so MEMIT stats can be computed offline after GPU allocation."
    )
    parser.add_argument("--dataset", default="wikipedia", type=str)
    parser.add_argument("--dataset_config", default="20220301.en", type=str)
    parser.add_argument("--sample_size", default=100000, type=int)
    parser.add_argument("--seed", default=1, type=int)
    parser.add_argument(
        "--output_path",
        default="data/cache/wikipedia_20220301_en_100000.jsonl",
        type=str,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Prefetch] dataset={args.dataset}:{args.dataset_config}")
    print(f"[Prefetch] sample_size={args.sample_size}")
    print(f"[Prefetch] output_path={output_path}")

    if args.dataset != "wikipedia":
        raise ValueError("This helper currently only supports dataset=wikipedia.")

    repo_id = "legacy-datasets/wikipedia"
    api = HfApi()
    prefix = f"data/{args.dataset_config}/"
    parquet_files = sorted(
        path
        for path in api.list_repo_files(repo_id=repo_id, repo_type="dataset")
        if path.startswith(prefix) and path.endswith(".parquet")
    )
    if not parquet_files:
        raise FileNotFoundError(
            f"No parquet files found for {repo_id} config {args.dataset_config}"
        )
    data_files = [
        f"https://huggingface.co/datasets/{repo_id}/resolve/main/{path}"
        for path in parquet_files
    ]

    print(f"[Prefetch] repo_id={repo_id}")
    print(f"[Prefetch] parquet_files={len(data_files)}")

    ds = load_dataset(
        "parquet",
        data_files=data_files,
        split="train",
        streaming=True,
    )
    shuffle_buffer = min(max(args.sample_size, 1000), 10000)
    ds = ds.shuffle(seed=args.seed, buffer_size=shuffle_buffer).take(args.sample_size)

    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for row in ds:
            f.write(
                json.dumps(
                    {
                        "id": row.get("id"),
                        "url": row.get("url"),
                        "title": row.get("title"),
                        "text": row.get("text", ""),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            count += 1
            if count % 1000 == 0:
                print(f"[Prefetch] wrote={count}")

    print(f"[Prefetch] done, wrote={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
