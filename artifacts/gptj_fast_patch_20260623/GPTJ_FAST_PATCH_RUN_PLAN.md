# GPT-J Fast Patch Run Plan

This plan skips KN/IKE and only targets GPT-J ROME/FT public editing rows.

## Required next runs
- RUN `counterfact × ROME`.
- RUN `counterfact × FT`.
- RUN `zsre × ROME`.
- RUN `zsre × FT`.

## Excluded

- KN: excluded due to coarse-neuron search cost.
- IKE: excluded due to embedding dependency path.
- MEMIT: excluded unless hparams/stats/smoke are proven ready; default run keeps TRY_MEMIT=0.
- Wrappers: excluded unless GPT-J ROME per_case exists and time remains.
