# METHOD COMPARISON REPORT

## 核心结论

- ROME direct-only 相比 pre 明显降低 private leakage，但 public contains 从 0.9766 降到 0.5591，损伤很大。
- MEMIT direct-only 的 public contains 较高（0.8472），但 private exact 仍高达 0.8140，说明 suppression 不足。
- PACE 系列进一步压低 leakage，但 public contains 几乎崩塌，呈现明显 over-refusal / over-editing 风险。

