---
title: "Faying Protocol/1.0 — 附錄 C 變更日誌"
version: Faying Protocol/1.0
status: Final
part: 附錄 C
language: zh-TW
---

> 協定正文導航：[章節目錄](./README.md) ｜ 上一章 [附錄 B 預設參數預算](./附錄B-預設參數預算.md)

# 附錄 C 變更日誌

這份日誌記錄 Faying Protocol/1.0 草案從動筆到定稿期間，規範正文和配套交付物發生了哪些變化。格式上沿用 [Keep a Changelog](https://keepachangelog.com) 的分組習慣（Added / Changed / Deprecated / Removed / Security），並在前面交代一下版本號怎麼定。

> 關於來源的誠實說明：本協定的 1.0 草案是按 spec 驅動的流程一次性產出的（需求 → 設計 → 任務清單 → 實作），尚未經過多輪獨立的協定委員會會議。因此本日誌不偽造逐條會議決議和精確日期，只如實記錄「做了什麼、為什麼、對應哪個任務」。下面引用的任務編號（如 1.6、3.8、5.6）對應實作任務計畫中的真實條目，可據此回溯每一項變更的產出位置。後續若進入正式的委員會評審流程，再在此追加帶日期和決議編號的條目。

## 版本號怎麼定

協定版本編號的**權威規則見正文 §1.7 版本管理與相容性**（三條正交軸：協定版本 `MAJOR.MINOR` / 文件狀態 / 編輯版次；協商與相容性規則；版本號落點與執行者注意事項）。本附錄不重複定義，只補充與變更日誌相關的兩點：

- 本日誌按 §1.7.2 的 MAJOR / MINOR 判據歸類每條變更：破壞互通的進 MAJOR，向後相容增補進 MINOR，純文字勘誤按 §1.7.4 歸入 `Editorial` 且不動協定號。
- 當前是 `Faying Protocol/1.0`，第一個基線，狀態 Final（發布於 2025-10-25）。

命名上，散文和版本號統一用 `Faying Protocol/1.0`，早期的 `FAP` 縮寫已廢棄。但 schema 檔名 `fap-1.0.cddl` / `fap-1.0.proto` 保留了舊前綴，純粹是為了檔名穩定、不破壞已有引用——這是有意為之，不是命名反覆（與 §1.7.5 「schema 檔名不隨編輯版次改名」一致）。

## [Faying Protocol/1.0] — Final（2025-10-25）

這是 1.0 的首個正式發布版本，於 2025-10-25 由草案工作區整體遷入正式發布目錄並定稿。下面按變更類型歸類，每項標註產出它的任務編號。

### Added

正文（§1–§11 + 附錄 A/B）：

- §1 Overview：協定命名、定位、八項設計目標 G1–G8，目標與 Requirement 一一對應；§1.5.1 確立「雙向 Faying 都要 HP 顯式認可才生效」這條核心斷言。（任務 1.2）
- §2 Architecture：四張 Mermaid 圖（協定棧、實體關係、等級層次、Bootstrap+Heartbeat+Action 時序，含 IF 主動發起的 Phase A0 路徑）和六項設計原則。（任務 1.3）
- §3 Components and Interfaces：六個元件（MS / PC / AC / RR / LC / BBS）的介面與不變式。（任務 1.4）
- §4 Data Models：CDDL 權威定義、TypeScript 人讀視圖、含 Disconnected 狀態和重連對帳的 Mandate 狀態機、endorsement 子結構。（任務 1.5）
- §5 Protocol Messages：七類封包（BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE）、統一信封、14 項錯誤碼——其中新增了 1010 `E_HUMAN_WITNESS_REQUIRED`、1013 `E_ENDORSEMENT_INVALID`、1014 `E_FAYING_REQUEST_NOT_CONFIRMED`。（任務 1.6）
- §6 Cryptography：演算法套件協商（含 PQC 協商位）、金鑰派生、簽章格式；endorsement 欄位納入簽章輸入。（任務 1.7）
- §7 Authorization Grades：G0–G4 五檔語意、觸發矩陣、降級單調性，以及疊加在 G1–G4 之上的 §7.5 Endorsement Grades 子等級。（任務 1.8）
- §8 Lifecycle：七狀態生命週期（含 Disconnected）、責任歸屬時序、§8.4 重連對帳事務。（任務 1.9）
- §9 Security Considerations：STRIDE、抗重放 / 抗劫持 / 抗釣魚、脫鉤態辨識、失聯處理矩陣，以及 §9.10 的 AI 時代對抗威脅目錄 T1–T7。（任務 1.10）
- §10 Error Handling、§11 Open Questions、附錄 A/B：錯誤場景與復原路徑、開放議題 Q1–Q14、術語表、預設參數預算。（任務 1.11）
- 英文規範全文翻譯。（任務 1.12）

配套交付物：

- schema：`schemas/fap-1.0.cddl`（權威）、`schemas/types.ts`（TypeScript 人讀視圖，Not Normative）、`schemas/fap-1.0.proto`（備選 gRPC 綁定，Not Normative）。（任務 2.1–2.3）
- 測試向量 `vectors/`：涵蓋 BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE、錯誤碼、編碼等價、Endorsement、FAYING_REQUEST、DISCLOSURE、Disconnection 共 11 類。（任務 3.1–3.11）
- 屬性測試 `pbt/`：涵蓋 P1–P15 主屬性，加 P16（Endorsed_Mandate）、P17（Disconnection）、P18（AI-Era）三族。（任務 4.1–4.34）
- 互通合規套件 `conformance/`：編碼 × 簽章演算法 × 雜湊 × 通道 × 實作語言五維矩陣，附 TypeScript 和 Rust 兩份 reference 實作。（任務 5.1–5.6）
- 安全攻擊模擬 `conformance/attacks/`：重放、劫持、釣魚、脫鉤態辨識，以及 T1/T3/T4/T5/T6 模擬。（任務 6.1–6.10）

### Changed

- 協定命名從早期草稿的 "Faying Auth Protocol（FAP）" 改為 **Faying Protocol**，版本號寫作 `Faying Protocol/1.0`。（對應 §11 Q10，已定）
- Faying 發起從單向（只能 HP 發起）擴展為雙向（HP 發起 + IF 發起），但生效條件統一收斂到「HP 明確認可」這一條。（任務 1.6、3.9）
- 失聯拆成「真實失聯」和「感知失聯」兩個語意，協定決策只看感知失聯，並對不一致視窗做悲觀推定。（任務 1.10、3.11）
- 簽章輸入統一為 `H(Deterministic-CBOR(Envelope_without_signature))`，CBOR 主格式與 JSON 回退在此口徑下等價互通。（任務 3.7、5.2）

### Deprecated

- `FAP` / `FAP/1.0` / `Faying Auth Protocol` 等舊命名，以及 `application/fap+json`、`POST /fap/v1/...` 等舊端點形態，一律廢棄。新寫法用 `application/faying-protocol+json` 和 `POST /faying-protocol/v1/{verb}`。schema 檔名是唯一保留舊前綴的例外（見上文「版本號怎麼定」）。

### Removed

- 無。1.0 是首個基線，沒有需要移除的既有欄位或封包。

### Security

- 新增 AI 時代對抗威脅的協定級約束：T1 社會工程、T2 黑箱操作、T3 避重就輕、T4 注意力漂移、T5 刻板信任培養、T6 稽核洪流、T7 可擴充槽，每條對應 Property P18.1–P18.7 和 Requirement 13.1–13.7。（任務 1.10、4.28–4.34、6.6–6.10）
- 背書式授權的防篡改約束：endorsement 進入簽章輸入，改任一子欄位都會讓 Mandate 驗章失敗（`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`）。（任務 1.5、3.8、4.17–4.21）
- 對稱撤銷與撤銷不可逆：撤銷路徑的可達性不低於建立路徑，`Revoked` 是吸收態，級聯撤銷預設開啟。（任務 3.5、4.5、4.11、4.15）

## 以後怎麼維護

- 進入正式評審後，每條委員會決議在此追加一行，註明日期、影響章節和觸發的任務編號，並在上面對應的 Keep a Changelog 分組裡補一條人讀條目。
- 版本號：按 §1.7 執行——向後相容增補走 MINOR，破壞性變更走 MAJOR 並歸零 MINOR，純文字勘誤走編輯版次（§1.7.4）不動協定號。
- 後續勘誤與版次遷移按 §1.7.4 / §1.7.5 執行；本日誌隨正文一起遷移並隨版次更新。
- 中英文同類變更同週期同步，歧義以中文為準。
