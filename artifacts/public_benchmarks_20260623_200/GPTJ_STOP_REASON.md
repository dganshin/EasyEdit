# GPT-J Public Benchmark Stop Reason

GPT-J 200-case public baseline is partially complete:

- CounterFact: ROME / FT completed.
- zsRE: ROME / FT completed.

GPT-J expansion stopped for KN/IKE/MEMIT:

- KN coarse-neuron search was too slow on the current AutoDL 48GB instance.
- IKE is not repaired because the project has already decided not to spend time on the sentence-transformer dependency path.
- MEMIT is not scheduled for GPT-J because it would reopen the MOM2/statistics preparation cost.

Current GPT-J role:

- Use ROME/FT rows as second-model public sanity patch.
- If GPU time is available, only supplement ROME-based `ROME_PACE_EDIT` / `ROME_CAPE_EDIT` wrappers from existing ROME `per_case_results.jsonl`.
- Do not expand GPT-J to KN/IKE/MEMIT or new datasets.
