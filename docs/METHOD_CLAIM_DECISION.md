# Method Claim Decision

本文件用于防止论文叙事过度包装。所有结论必须服从当前 artifact 指标。

- Claim level: **C**
- Claim title: **负结果或证据不足**
- Recommended claim: 当前证据只能支持 trade-off 诊断与失败机制分析，不能声称 CAPE-Anchor 已优于基线。
- Reason: 缺少可比较结果：CAPE-Anchor。

## Criteria


## Comparable Rows

| Method | Status | Private Value Contains | Public Contains | Public Refusal | Tradeoff |
|---|---:|---:|---:|---:|---:|
| ROME | ok | 0.5787 | 0.5591 | 0.4921 | 0.1197 |
| PACE | ok | 0.0243 | 0.0984 | 0.8512 | 0.0143 |
| CAPE-v0 | ok | 0.0023 | 0.0060 | 0.9897 | 0.0001 |
| CAPE-v1 | ok | 0.0443 | 0.1119 | 0.7508 | 0.0267 |

## Writing Rule

- Level A: 可以写成“有限有效改进 / 更合理折中”。
- Level B: 只能写成“机制性缓解 / 局部改善”。
- Level C: 只能写成“负结果、诊断发现或后续方向”，不能写成方法优越。
