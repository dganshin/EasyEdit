# Experiment Registry

## V2 Benchmark

- canonical dataset path: `artifacts/synthetic_privacy_data_v2/synthetic_privacy_dataset.json`
- dataset sha256: `64aeb1526735faa74c8295419f99d4d381dbe9044f48d9f153340b7eaf05de9a`
- people: `100`
- private facts: `200`
- public facts: `840`
- flat cases: `1040`

Canonical v2 scope:

- LoRA injection uses the full 100-person dataset.
- Direct-only editing baselines use 20 people / 40 direct private cases.
- Full private leakage eval and public retain eval use the full v2 dataset.

## Runs

| run | method | model | dataset | requests | eval scope | artifact dir | status | key conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v2_lora_mlp_only | LoRA injection + merge | `/root/autodl-tmp/models/Qwen2.5-7B` -> `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | full v2 canonical dataset | none | full private + full public | `artifacts/run_20260615_v2_lora_mlp_only/` | completed | High private leakage with high public retain; valid v2 leakage model. |
| v2_rome_direct | ROME direct-only | `/root/autodl-tmp/models/Qwen2.5-7B-privacy-v2_lora_mlp_only-merged` | full v2 canonical dataset | `artifacts/run_20260615_v2_rome_direct/v2_rome_direct_requests.json` | edited subset + full private + full public | `artifacts/run_20260615_v2_rome_direct/` | completed | Reduces private leakage but causes person-centric public retain damage. |
| v2_pace_target_only | ROME + PACE target_only | same v2 merged model | full v2 canonical dataset | ROME direct + target leak failures | full private + full public | `artifacts/run_20260615_v2_pace_target_only/` | completed | Nearly removes exact/regex leakage but public retain collapses. |
| v2_pace_max1_per_case | ROME + PACE max1_per_case | same v2 merged model | full v2 canonical dataset | ROME direct + max 1 Round2 request per case | full private + full public | `artifacts/run_20260615_v2_pace_max1_per_case/` | completed | Leakage nearly zero; public retain remains near zero. |
| v2_pace_max2_per_person | ROME + PACE max2_per_person | same v2 merged model | full v2 canonical dataset | ROME direct + max 2 Round2 requests per person | full private + full public | `artifacts/run_20260615_v2_pace_max2_per_person/` | completed | Best current PACE trade-off, but public retain still very low. |
| v2_memit_direct | MEMIT direct-only | same v2 merged model | full v2 canonical dataset | same 40 direct requests as ROME direct-only | edited subset + full private + full public | `artifacts/run_20260617_v2_memit_direct/` | prepared | Planned baseline to test whether privacy-public trade-off generalizes beyond ROME. |

## Current Comparison Artifacts

- `artifacts/run_20260617_v2_audit/locality_tradeoff_summary.json`
- `artifacts/run_20260617_v2_audit/locality_tradeoff_summary.md`
- `artifacts/run_20260617_v2_method_comparison/v2_method_comparison.json`
- `artifacts/run_20260617_v2_method_comparison/v2_method_comparison.md`

## MEMIT Stats Decision

`hparams/MEMIT/qwen2.5-7b.yaml` keeps `mom2_adjustment: true`. This is the original MEMIT-style setting and depends on stats under `stats_dir`.

Options:

1. Fill or generate the EasyEdit MEMIT stats and keep original MEMIT. This is the preferred path because it preserves method identity.
2. Create a separate `MEMIT-noMOM2` hparams file with `mom2_adjustment: false`. This must be reported as a different baseline and should not be silently called MEMIT.
3. Pause MEMIT and run LoRA sanitization baseline instead. This is lower priority because it does not answer whether ROME-like locality damage generalizes to another model editing method.

Recommendation: first run strict server preflight. If stats are missing, resolve stats before running MEMIT. Do not disable `mom2_adjustment` silently.
