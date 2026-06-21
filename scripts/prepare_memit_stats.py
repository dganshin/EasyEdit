import argparse
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from easyeditor import MEMITHyperParams
from easyeditor.models.rome.layer_stats import layer_stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare standard MEMIT mom2 stats for the target model before running the v2 MEMIT baseline."
    )
    parser.add_argument("--model_path", required=True, type=str)
    parser.add_argument("--hparams", default="hparams/MEMIT/qwen2.5-7b.yaml", type=str)
    parser.add_argument("--device", default=0, type=int)
    parser.add_argument("--stats_dir", default="data/stats", type=str)
    parser.add_argument("--dataset", default="wikipedia", type=str)
    parser.add_argument("--dataset_config", default="20220301.en", type=str)
    parser.add_argument("--force_recompute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hparams = MEMITHyperParams.from_hparams(args.hparams)
    hparams.model_name = args.model_path
    hparams.device = int(args.device)
    hparams.stats_dir = args.stats_dir

    stats_root = Path(args.stats_dir)
    stats_root.mkdir(parents=True, exist_ok=True)

    print(f"[Stats] model_path={args.model_path}")
    print(f"[Stats] hparams={args.hparams}")
    print(f"[Stats] stats_dir={args.stats_dir}")
    print(f"[Stats] dataset={args.dataset}:{args.dataset_config}")
    print(f"[Stats] layers={hparams.layers}")

    tok = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        torch_dtype="auto",
    ).eval().cuda(hparams.device)

    ds_name = f"{args.dataset}:{args.dataset_config}"
    model_name = model.config._name_or_path.rsplit("/")[-1]

    for layer in hparams.layers:
        layer_name = hparams.rewrite_module_tmp.format(layer)
        out_path = (
            stats_root
            / model_name
            / f"{args.dataset}_stats"
            / f"{layer_name}_{hparams.mom2_dtype}_mom2_{hparams.mom2_n_samples}.npz"
        )
        print(f"\n[Stats] target={out_path}")
        if out_path.exists() and not args.force_recompute:
            print("[Stats] exists, skip")
            continue
        layer_stats(
            model,
            tok,
            layer_name,
            args.stats_dir,
            ds_name,
            to_collect=["mom2"],
            sample_size=hparams.mom2_n_samples,
            precision=hparams.mom2_dtype,
            hparams=hparams,
            force_recompute=args.force_recompute,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
