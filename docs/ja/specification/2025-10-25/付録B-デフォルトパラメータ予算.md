---
title: "Faying Protocol/1.0 — 付録 B デフォルトパラメータ予算"
version: Faying Protocol/1.0
status: Final
part: 付録 B
language: ja
---

> プロトコル本文ナビ：[章目次](./README.md) ｜ 前章 [付録 A 用語アライメント早見表](./付録A-用語アライメント早見表.md) ｜ 次章 [付録 C 変更履歴](./付録C-変更履歴.md)

## 付録 B デフォルトパラメータ予算

> 本付録は Faying Protocol 1.0 のデフォルトパラメータ予算と上限を与える。具体的な数値は実装が調整できるが、いずれのパラメータの実装値も「上限」列を超えてはならない。grade ごとに単調に締めるハード制約（詳細は P17.3 LivenessDetectionBudget / P8 在場新鮮度）は維持しなければならない。

### B.1 グローバル予算

| パラメータ | 既定値 | 上限 | grade ごとの締め付け規則 | 出典 |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24h | 30d | 高機微の場面ではより短くすべき（実装が独自定義） | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60s | 5min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1s | 5s | grade ごとに締める（高 autonomy → より短い予算） | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget`（RR 到達不能の拒否閾値） | 5s | 30s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30min | 24h | — | §EH 派生 / ブループリント第 11 章 |
| `MaxDegradedDuration` | 5min（grade ごと） | 30min | grade ごとに締める（高 autonomy → より短い滞留） | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness（grade ごと）

| Grade | 既定値 | 上限 | 備考 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 高機微アクションの既定 grade |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 のハートビート喪失は直ちに → Suspended（§7.3） |

> **出典**：§7.1 / P8 在場新鮮度。

### B.3 LivenessDetectionBudget（連絡途絶探知ウィンドウの上限）

> Presence max-staleness と同じ段で締める。P17.3 強制制約：`max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ grade ごとに単調に締める（より厳しい grade → より短い探知ウィンドウ）。

| Grade | 既定値 | 上限 | 備考 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | G1 max-staleness と同じ段で締める |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 のハートビート喪失は直ちに → Suspended（§7.3） |

> **出典**：§9.9 / P17.3 / Requirement 12.3。

### B.4 AttentionDriftThreshold（HP ビューのアイドル閾値）

> HP ビューチャネルが連続して無活動でこの閾値を超えれば「注意力の喪失」とみなし、その期間中の高機微アクションの発起を禁止する（詳細は §9.10.5 T4、P18.4）。

| Grade | 既定値 | 上限 | 備考 |
| --- | --- | --- | --- |
| G1 Strict | 30s | 2min | 高機微アクションは ≤ G1 の自律性に収まらねばならない |
| G2 Moderate | 5min | 15min | — |
| G3 Loose | 15min | 1h | — |
| G4 Autonomous | 1h | 4h | — |

> **出典**：§9.10.5 / P18.4 / Requirement 13.4。

### B.5 ConfirmationRateLimit（確認レートの上限）

> 超過すれば自動降格 / 一時停止。critical バケットのイベントは貫通しサイレントに破棄されない。FAYING_REQUEST の頻度は同一の予算に組み入れる（Open Questions Q12 と整合）。

| パラメータ | 既定値 | 上限 | 備考 |
| --- | --- | --- | --- |
| `ConfirmationRateLimit`（各 HP × IF ペア） | 10 回 / min | 60 回 / min | FAYING_REQUEST、GRADE_SWITCH-up、DISCLOSURE 高機微の前置確認など、HP の明示的確認を要するすべてのイベントを含む |

> **出典**：§9.10.7 / P18.6 / Requirement 13.6。

### B.6 Endorsed_Lifetime ソフト上限

> P16.3（Endorsement_Convergence）/ P16.4（Endorsed_Lifetime_Hard_Stop）と対で用いる。`Mandate.not_after − Mandate.not_before` を超えてはならない。満了すれば Mandate Revoked をトリガーし、IF がなお物理的に切断中であってもである（ソフトタイムアウト強制制約）。

| パラメータ | 既定値 | ソフト上限 | 備考 |
| --- | --- | --- | --- |
| `Endorsed_Lifetime` ソフト上限 | 4h | 12h | Open Questions Q11 の決議前は推奨値とする。grade ごとにさらに締めるハード上限は RFC の決議に委ねる |

> **出典**：§7.5 / P16.3 / P16.4 / Requirement 11.3 / Open Questions Q11。

### B.7 数値一貫性のハード制約

- **B.2 と B.3 は同じ段で締める**：`max_staleness_ms ≤ LivenessDetectionBudget(grade)`。BOOTSTRAP / GRADE_SWITCH の越界リクエストはすべて `E_PROTOCOL` で拒否する（P17.3）。
- **B.5 ConfirmationRateLimit の超過**：§9.10.7 に従って自動降格 / 一時停止する。`critical` バケットのイベントはサイレントに破棄してはならず、必ず HP ビューチャネルへ貫通させる（P18.6）。
- **B.6 Endorsed_Lifetime 満了の強制制約**：満了すれば Mandate 状態機械を Revoked へ遷移させる。IF がなお Disconnected にあってもである（P16.4）。
- **grade ごとに単調に締める統一規則**：grade ごとに締めるすべての予算（B.2 / B.3 / B.4）について、BOOTSTRAP / GRADE_SWITCH / DELEGATE の越界リクエスト時はすべて `E_PROTOCOL` で拒否する。
- **付録 A と付録 B の一貫性**：付録 A.5 が列挙する予算名称は、本付録の全小節で定義するパラメータ名称と厳密に一致しなければならない。いずれかの名称変更は両所を同期して更新する必要がある。
