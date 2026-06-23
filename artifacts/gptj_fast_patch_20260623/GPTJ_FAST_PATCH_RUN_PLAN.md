# GPT-J Fast Patch Run Plan

This plan skips KN/IKE and only targets GPT-J ROME/FT public editing rows.

## Required next runs
- SKIP `counterfact × ROME`: existing status=ok.
- SKIP `counterfact × FT`: existing status=ok.
- RUN `counterfact × ROME_PACE_EDIT`.
- RUN `counterfact × ROME_CAPE_EDIT`.
- SKIP `zsre × ROME`: existing status=ok.
- SKIP `zsre × FT`: existing status=ok.
- RUN `zsre × ROME_PACE_EDIT`.
- RUN `zsre × ROME_CAPE_EDIT`.

## Excluded

- KN: excluded due to coarse-neuron search cost.
- IKE: excluded due to embedding dependency path.
- MEMIT: excluded unless hparams/stats/smoke are proven ready; default run keeps TRY_MEMIT=0.
- Wrappers: excluded unless GPT-J ROME per_case exists and time remains.
