---
title: "Faying Protocol/1.0 — 附錄 A 術語對齊速查"
version: Faying Protocol/1.0
status: Final
part: 附錄 A
language: zh-TW
---

> 協定正文導航：[章節目錄](./README.md) ｜ 上一章 [§11 開放議題](./11-開放議題.md) ｜ 下一章 [附錄 B 預設參數預算](./附錄B-預設參數預算.md)

## 附錄 A 術語對齊速查

> 本附錄與本規範需求基線 Glossary、設計依據附錄 A 三者保持一致；EARS 子句中出現的系統名稱必須在此處定義後方可使用。本附錄按「角色與實體 / 協定元件 / 協定資料物件 / 等級與策略 / 預設預算」五類組織，便於交叉查閱。

### A.1 角色與實體

| 協定術語（英文） | 藍圖 / 中文術語 | 關係 / 說明 |
| --- | --- | --- |
| Human Prime（HP） | 人類原型 | 同義；Faying 關係唯一的最終責任承接端、撤銷權持有者，亦是唯一可對 Faying 狀態變化給出明確認可確認的實體 |
| iFay Instance（IF） | iFay 實例 | 同義；被監護的代理實體，由 FayID 唯一標識；不擁有撤銷自身 Mandate 的權力，所有狀態變化以 HP 明確認可為前提 |
| Supervisory Agent（SA） | 監管 Agent | Prime 之外的另一類協定層可辨識的監管主體；不持有撤銷權、不可替代 HP 完成 Faying 認可確認 |
| Relying Party（RP） | 受呼叫方 | 被 iFay 呼叫的終端、應用或服務 |
| Presence Device（PD） | 在場設備 | 承載 WebAuthn / FIDO2 憑證、生物辨識能力的硬體，是在場訊號的物理源頭 |

### A.2 協定元件

| 協定術語（英文） | 縮寫 | 說明 |
| --- | --- | --- |
| Mandate Service | MS | 代表 HP 頒發 / 續期 / 降級 / 撤銷 Mandate 的邏輯服務（詳見 §3.1） |
| Presence Channel | PC | 從 PD 到 MS 的低延遲、抗重放在場流（詳見 §3.2） |
| Attestation Chain | AC | HP → MS → IF → 派生 IF 全部簽發動作形成的可逆向追溯簽章鏈（詳見 §3.3） |
| Revocation Registry | RR | 即時撤銷狀態服務（詳見 §3.4） |
| Liveness Channel | LC | 失聯探測（含真實失聯與感知失聯）流（詳見 §3.5、§9.9） |
| Behavior Baseline Service | BBS | 維護 (HP, IF) 行為基線的統計服務（詳見 §3.6） |

### A.3 協定資料物件

| 協定術語（英文） | 藍圖 / 中文術語 | 說明 |
| --- | --- | --- |
| Mandate | 授權令 | 協定層新概念；承載 `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` 等欄位（詳見 §4.1 / §4.2） |
| Endorsed_Mandate | 背書式授權 | Mandate 子型別；顯式宣告 `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)`，使 IF 在物理失聯期間仍可在限定範圍內自治；責任承接端始終為 HP（詳見 §7.5、P16.x） |
| PresenceSignal | 在場訊號 | 由 PD 產生的、可被 MS 校驗的物理在場斷言 |
| Attestation | 證言 | 統一的可驗證斷言載體（WebAuthn / TPM-quote / Platform-keystore / Self-signed） |
| FayID | FayID | iFay 在 iFay 框架中的統一唯一身分標識（ULID-like） |
| Faying_State | 受控狀態 | Mandate 處於 Active / Degraded / Disconnected 時 IF 所處的行為狀態 |
| Rogue_Fay | 脫離狀態 | Mandate 處於 Unpaired / Revoked 或不存在時 IF 所處的行為狀態；與 Faying_State 二態互斥（P15）。**注**：`Suspended` 不歸入 Rogue_Fay——它是「Faying State 暫停」（監護關係仍在、Mandate 中繼資料保留、可由 HP 顯式復原而無需新一輪 BOOTSTRAP），僅在行為後果上與 Rogue 一樣禁止 D 維度；詳見 §4.3 / §8.2 映射表 |
| Faying_Initiation | 雙向 Faying 發起 | Faying 關係（建立或調整）的發起既可由 HP 主動（HP-initiated），亦可由 IF 主動向 HP 尋求（IF-initiated / FAYING_REQUEST）；最終生效條件均為 HP 給出可驗證的明確認可確認（詳見 §5.3.6、P16.6） |
| Behavior_Baseline | 行為基線 | 由 BBS 維護的 (HP, IF) 累積行為畫像，用於偵測突發偏離（詳見 §3.6、P18.5） |
| Atomic_Action | 原子動作 | IF 對外執行的最小不可拆分宣告單元；一次呼叫恰好對應 1 個 Atomic_Action，禁止打包（詳見 P18.2） |
| Disclosure_Report | 披露封包 | IF 在彙報或請求確認時使用的結構化封包；`mandatory_fields` 強制可解析（詳見 §5.3.7、P18.3） |
| Ego | 自我邊界 | 同義；用於 `ego-deviation` 觸發判定（詳見 §3.6、§9.10.4） |
| Human View | 人類視野 | 價值觀；Faying Protocol 是其協定級落地（藍圖第 11 章） |

### A.4 等級與策略

| 協定術語（英文） | 說明 |
| --- | --- |
| Authorization_Grade（Grade） | 授權等級，取值 `G0..G4`（詳見 §7） |
| G0 Emergency_Override | 緊急奪回級；HP 單方面強制收回控制（詳見 §7.1、P12） |
| G1 Strict | 最嚴格檔；高敏感動作的預設 grade |
| G2 Moderate | 中等檔 |
| G3 Loose | 寬鬆檔 |
| G4 Autonomous | 最自主檔；G4 心跳遺失直接 → Suspended（詳見 §7.3） |
| PresenceRequirement | 在場要求；綁定到 grade 的 `(signal_types, max_staleness_ms, on_loss)` 三元組 |
| Scope | 授權範圍；`(domains, actions, terminals?, budget?)` 顯式宣告的最小權限集合 |

### A.5 預設預算（詳細數值見附錄 B）

| 協定術語（英文） | 簡述 |
| --- | --- |
| MaxMandateLifetime | 單個 Mandate 最大壽命（預設 24h，上限 30d） |
| BootstrapTimeout | BOOTSTRAP / FAYING_REQUEST 等待 HP 見證的逾時（預設 60s） |
| RevocationVisibilityBudget | 撤銷在 RR 全網可見的預算（預設 1s） |
| StaleBudget | RR 不可達拒絕閾值（預設 5s） |
| HumanReachabilityBudget | HP 失聯觸發自動 Revoke 的閾值（預設 30min） |
| LivenessDetectionBudget | 失聯探測視窗上限；按 grade 單調收緊（詳見附錄 B、P17.3） |
| AttentionDriftThreshold | HP 視野閒置觸發「注意力遺失」的閾值；按 grade 收緊（詳見附錄 B、P18.4） |
| ConfirmationRateLimit | 單位時間內向 HP 推送的確認請求數量上限；超限自動降級 / 暫停（詳見附錄 B、P18.6） |
| MaxDegradedDuration | Degraded 狀態最大持續時間（預設 5min/grade） |
