---
title: "Faying Protocol/1.0 — 附录 B 默认参数预算"
version: Faying Protocol/1.0
status: Final
part: 附录 B
language: zh-CN
---

> 协议正文导航：[章节目录](./README.md) ｜ 上一章 [附录 A 术语对齐速查](./附录A-术语对齐速查.md) ｜ 下一章 [附录 C 变更日志](./附录C-变更日志.md)

## 附录 B 默认参数预算

> 本附录给出 Faying Protocol 1.0 的默认参数预算与上限；具体数值可被实现调整，但任一参数的实现取值不得超过"上限"列；按 grade 单调收紧的硬约束（详见 P17.3 LivenessDetectionBudget / P8 在场新鲜度）必须维持。

### B.1 全局预算

| 参数 | 默认值 | 上限 | 按 grade 收紧规则 | 出处 |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24h | 30d | 高敏感场景应更短（实现自定义） | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60s | 5min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1s | 5s | 按 grade 收紧（高 autonomy → 更短预算） | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget`（RR 不可达拒绝阈值） | 5s | 30s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30min | 24h | — | §EH 派生 / 蓝图第 11 章 |
| `MaxDegradedDuration` | 5min（按 grade） | 30min | 按 grade 收紧（高 autonomy → 更短停留） | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness（按 grade）

| Grade | 默认值 | 上限 | 备注 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 高敏感动作默认 grade |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 心跳丢失直接 → Suspended（§7.3） |

> **出处**：§7.1 / P8 在场新鲜度。

### B.3 LivenessDetectionBudget（失联探测窗口上限）

> 与 Presence max-staleness 同档收紧；P17.3 强约束：`max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ 按 grade 单调收紧（更严的 grade → 更短的探测窗口）。

| Grade | 默认值 | 上限 | 备注 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 与 G1 max-staleness 同档收紧 |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 心跳丢失直接 → Suspended（§7.3） |

> **出处**：§9.9 / P17.3 / Requirement 12.3。

### B.4 AttentionDriftThreshold（HP 视野空闲阈值）

> HP 视野通道无活动连续超过该阈值即视为"注意力丢失"，期间禁止发起高敏感动作（详见 §9.10.5 T4、P18.4）。

| Grade | 默认值 | 上限 | 备注 |
| --- | --- | --- | --- |
| G1 Strict | 30s | 2min | 高敏感动作必须落于 ≤ G1 自主性 |
| G2 Moderate | 5min | 15min | — |
| G3 Loose | 15min | 1h | — |
| G4 Autonomous | 1h | 4h | — |

> **出处**：§9.10.5 / P18.4 / Requirement 13.4。

### B.5 ConfirmationRateLimit（确认速率上限）

> 超限自动降级 / 暂停；critical 桶事件穿透不可被静默丢弃；FAYING_REQUEST 频次纳入同一预算（与 Open Questions Q12 一致）。

| 参数 | 默认值 | 上限 | 备注 |
| --- | --- | --- | --- |
| `ConfirmationRateLimit`（每对 HP × IF） | 10 次 / min | 60 次 / min | 含 FAYING_REQUEST、GRADE_SWITCH-up、DISCLOSURE 高敏感前置确认等所有需 HP 显式确认的事件 |

> **出处**：§9.10.7 / P18.6 / Requirement 13.6。

### B.6 Endorsed_Lifetime 软上限

> 与 P16.3（Endorsement_Convergence）/ P16.4（Endorsed_Lifetime_Hard_Stop）配套；不得超过 `Mandate.not_after − Mandate.not_before`；到期即触发 Mandate Revoked，即使 IF 仍处于物理断开（软超时强约束）。

| 参数 | 默认值 | 软上限 | 备注 |
| --- | --- | --- | --- |
| `Endorsed_Lifetime` 软上限 | 4h | 12h | Open Questions Q11 决议前作为推荐值；按 grade 进一步收紧的硬上限留待 RFC 决议 |

> **出处**：§7.5 / P16.3 / P16.4 / Requirement 11.3 / Open Questions Q11。

### B.7 数值一致性硬约束

- **B.2 与 B.3 同档收紧**：`max_staleness_ms ≤ LivenessDetectionBudget(grade)`；BOOTSTRAP / GRADE_SWITCH 越界请求一律以 `E_PROTOCOL` 拒绝（P17.3）。
- **B.5 ConfirmationRateLimit 超限**：自动按 §9.10.7 降级 / 暂停；`critical` 桶事件不可被静默丢弃，必须穿透至 HP 视野通道（P18.6）。
- **B.6 Endorsed_Lifetime 到期强约束**：到期即触发 Mandate 状态机迁移至 Revoked，即使 IF 仍处于 Disconnected（P16.4）。
- **按 grade 单调收紧的统一规则**：所有按 grade 收紧的预算（B.2 / B.3 / B.4）在 BOOTSTRAP / GRADE_SWITCH / DELEGATE 越界请求时一律以 `E_PROTOCOL` 拒绝。
- **附录 A 与附录 B 一致性**：附录 A.5 列出的预算名称必须与本附录所有小节定义的参数名称严格一致；任一名称变更需同步更新两处。
