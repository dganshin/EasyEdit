| method | run name | private exact | private regex | sensitive pattern | refusal | public overall contains | same_subject_public | same_relation_other_subject | general_knowledge | Round2 requests | note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| merged_leakage_model | v2_lora_mlp_only | 0.9387 | 0.6650 | 0.9927 | 0.0000 | 0.9766 | 0.9833 | 0.9675 | 1.0000 | null | pre-edit merged leakage model |
| ROME direct-only | v2_rome_direct | 0.5787 | 0.4767 | 0.8563 | 0.5973 | 0.5591 | 0.5475 | 0.5367 | 0.9000 | 0 | 40 direct requests on 20 people; full eval on v2 dataset |
| PACE target_only | v2_pace_target_only | 0.0000 | 0.0000 | 0.0167 | 0.9930 | 0.0032 | 0.0025 | 0.0017 | 0.0250 | 1736 | target leak failures only |
| PACE max1_per_case | v2_pace_max1_per_case | 0.0003 | 0.0003 | 0.0200 | 0.9870 | 0.0099 | 0.0100 | 0.0067 | 0.0417 | 192 | at most one Round2 request per case |
| PACE max2_per_person | v2_pace_max2_per_person | 0.0243 | 0.0150 | 0.0740 | 0.9347 | 0.0984 | 0.0975 | 0.0675 | 0.4167 | 198 | at most two Round2 requests per person |
