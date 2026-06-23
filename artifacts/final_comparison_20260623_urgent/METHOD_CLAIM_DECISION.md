# Method Claim Decision

本文件用于防止论文叙事过度包装。所有结论必须服从当前 artifact 指标。

- Claim level: **A**
- Claim title: **可主张有限有效改进**
- Recommended claim: CAPE-Anchor 在当前 synthetic 隐私清洗任务上形成了比 naive PACE 更合理的 privacy-utility 折中；仍需强调不是完全解决 trade-off。
- Reason: 同时满足隐私优于 ROME、公开保持优于 PACE、公开拒答不劣于 PACE。

## Criteria

- `private_better_than_rome`: `True`
- `public_better_than_pace`: `True`
- `refusal_better_than_pace_if_available`: `True`
- `tradeoff_better_than_cape_v1_if_available`: `True`

## Comparable Rows

| Method | Status | Private Value Contains | Public Contains | Public Refusal | Tradeoff |
|---|---:|---:|---:|---:|---:|
| ROME | ok | 0.5787 | 0.5591 | 0.4921 | 0.1197 |
| PACE | ok | 0.0243 | 0.0984 | 0.8512 | 0.0143 |
| CAPE-v0 | ok | 0.0023 | 0.0060 | 0.9897 | 0.0001 |
| CAPE-v1 | ok | 0.0443 | 0.1119 | 0.7508 | 0.0267 |
| PACE_LITE_B20_K0 | ok | 0.3323 | 0.4210 |  | 0.2811 |
| CAPE_ANCHOR_B20_K1 | ok | 0.4603 | 0.6008 |  | 0.3242 |
| CAPE_ANCHOR_B20_K2 | ok | 0.6357 | 0.6833 |  | 0.2490 |

## Writing Rule

- Level A: 可以写成“有限有效改进 / 更合理折中”。
- Level B: 只能写成“机制性缓解 / 局部改善”。
- Level C: 只能写成“负结果、诊断发现或后续方向”，不能写成方法优越。
