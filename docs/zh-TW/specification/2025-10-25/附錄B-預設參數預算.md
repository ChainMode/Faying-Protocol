---
title: "Faying Protocol/1.0 — 附錄 B 預設參數預算"
version: Faying Protocol/1.0
status: Final
part: 附錄 B
language: zh-TW
---

> 協定正文導航：[章節目錄](./README.md) ｜ 上一章 [附錄 A 術語對齊速查](./附錄A-術語對齊速查.md) ｜ 下一章 [附錄 C 變更日誌](./附錄C-變更日誌.md)

## 附錄 B 預設參數預算

> 本附錄給出 Faying Protocol 1.0 的預設參數預算與上限；具體數值可被實作調整，但任一參數的實作取值不得超過「上限」列；按 grade 單調收緊的硬約束（詳見 P17.3 LivenessDetectionBudget / P8 在場新鮮度）必須維持。

### B.1 全域預算

| 參數 | 預設值 | 上限 | 按 grade 收緊規則 | 出處 |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24h | 30d | 高敏感場景應更短（實作自訂） | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60s | 5min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1s | 5s | 按 grade 收緊（高 autonomy → 更短預算） | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget`（RR 不可達拒絕閾值） | 5s | 30s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30min | 24h | — | §EH 派生 / 藍圖第 11 章 |
| `MaxDegradedDuration` | 5min（按 grade） | 30min | 按 grade 收緊（高 autonomy → 更短停留） | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness（按 grade）

| Grade | 預設值 | 上限 | 備註 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 高敏感動作預設 grade |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 心跳遺失直接 → Suspended（§7.3） |

> **出處**：§7.1 / P8 在場新鮮度。

### B.3 LivenessDetectionBudget（失聯探測視窗上限）

> 與 Presence max-staleness 同檔收緊；P17.3 強約束：`max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ 按 grade 單調收緊（更嚴的 grade → 更短的探測視窗）。

| Grade | 預設值 | 上限 | 備註 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 與 G1 max-staleness 同檔收緊 |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 心跳遺失直接 → Suspended（§7.3） |

> **出處**：§9.9 / P17.3 / Requirement 12.3。

### B.4 AttentionDriftThreshold（HP 視野閒置閾值）

> HP 視野通道無活動連續超過該閾值即視為「注意力遺失」，期間禁止發起高敏感動作（詳見 §9.10.5 T4、P18.4）。

| Grade | 預設值 | 上限 | 備註 |
| --- | --- | --- | --- |
| G1 Strict | 30s | 2min | 高敏感動作必須落於 ≤ G1 自主性 |
| G2 Moderate | 5min | 15min | — |
| G3 Loose | 15min | 1h | — |
| G4 Autonomous | 1h | 4h | — |

> **出處**：§9.10.5 / P18.4 / Requirement 13.4。

### B.5 ConfirmationRateLimit（確認速率上限）

> 超限自動降級 / 暫停；critical 桶事件穿透不可被靜默丟棄；FAYING_REQUEST 頻次納入同一預算（與 Open Questions Q12 一致）。

| 參數 | 預設值 | 上限 | 備註 |
| --- | --- | --- | --- |
| `ConfirmationRateLimit`（每對 HP × IF） | 10 次 / min | 60 次 / min | 含 FAYING_REQUEST、GRADE_SWITCH-up、DISCLOSURE 高敏感前置確認等所有需 HP 顯式確認的事件 |

> **出處**：§9.10.7 / P18.6 / Requirement 13.6。

### B.6 Endorsed_Lifetime 軟上限

> 與 P16.3（Endorsement_Convergence）/ P16.4（Endorsed_Lifetime_Hard_Stop）配套；不得超過 `Mandate.not_after − Mandate.not_before`；到期即觸發 Mandate Revoked，即使 IF 仍處於物理斷開（軟逾時強約束）。

| 參數 | 預設值 | 軟上限 | 備註 |
| --- | --- | --- | --- |
| `Endorsed_Lifetime` 軟上限 | 4h | 12h | Open Questions Q11 決議前作為建議值；按 grade 進一步收緊的硬上限留待 RFC 決議 |

> **出處**：§7.5 / P16.3 / P16.4 / Requirement 11.3 / Open Questions Q11。

### B.7 數值一致性硬約束

- **B.2 與 B.3 同檔收緊**：`max_staleness_ms ≤ LivenessDetectionBudget(grade)`；BOOTSTRAP / GRADE_SWITCH 越界請求一律以 `E_PROTOCOL` 拒絕（P17.3）。
- **B.5 ConfirmationRateLimit 超限**：自動按 §9.10.7 降級 / 暫停；`critical` 桶事件不可被靜默丟棄，必須穿透至 HP 視野通道（P18.6）。
- **B.6 Endorsed_Lifetime 到期強約束**：到期即觸發 Mandate 狀態機遷移至 Revoked，即使 IF 仍處於 Disconnected（P16.4）。
- **按 grade 單調收緊的統一規則**：所有按 grade 收緊的預算（B.2 / B.3 / B.4）在 BOOTSTRAP / GRADE_SWITCH / DELEGATE 越界請求時一律以 `E_PROTOCOL` 拒絕。
- **附錄 A 與附錄 B 一致性**：附錄 A.5 列出的預算名稱必須與本附錄所有小節定義的參數名稱嚴格一致；任一名稱變更需同步更新兩處。
