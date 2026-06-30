---
title: "Faying Protocol/1.0 — 付録 A 用語アライメント早見表"
version: Faying Protocol/1.0
status: Final
part: 付録 A
language: ja
---

> プロトコル本文ナビ：[章目次](./README.md) ｜ 前章 [§11 未解決の課題](./11-未解決の課題.md) ｜ 次章 [付録 B デフォルトパラメータ予算](./付録B-デフォルトパラメータ予算.md)

## 付録 A 用語アライメント早見表

> 本付録は本仕様の要件ベースライン Glossary、設計根拠付録 A の三者と一致を保つ。EARS 条項に登場するシステム名称は、ここで定義された後にのみ使用できる。本付録は「役割とエンティティ / プロトコルコンポーネント / プロトコルデータオブジェクト / グレードとポリシー / デフォルト予算」の 5 類で組織し、相互参照を容易にしている。

### A.1 役割とエンティティ

| プロトコル用語（英語） | ブループリント / 日本語用語 | 関係 / 説明 |
| --- | --- | --- |
| Human Prime（HP） | 人類原型 | 同義。Faying 関係の唯一の最終責任引き受け端、撤回権の保持者であり、かつ Faying 状態の変化に明確な認可確認を与えられる唯一のエンティティ |
| iFay Instance（IF） | iFay 実例 | 同義。監護される代理エンティティで、FayID で一意に識別される。自身の Mandate を撤回する権限を持たず、すべての状態変化は HP の明確な認可を前提とする |
| Supervisory Agent（SA） | 監督 Agent | Prime 以外の、もう一類のプロトコル層が識別できる監督主体。撤回権を持たず、HP に代わって Faying の認可確認を完了することはできない |
| Relying Party（RP） | 被呼び出し側 | iFay に呼び出される端末、アプリケーション、サービス |
| Presence Device（PD） | 在場デバイス | WebAuthn / FIDO2 資格情報、生体認証能力を載せるハードウェアで、在場信号の物理的な源 |

### A.2 プロトコルコンポーネント

| プロトコル用語（英語） | 略称 | 説明 |
| --- | --- | --- |
| Mandate Service | MS | HP を代表して Mandate を発行 / 更新 / 降格 / 撤回する論理サービス（詳細は §3.1） |
| Presence Channel | PC | PD から MS への低遅延・リプレイ耐性のある在場ストリーム（詳細は §3.2） |
| Attestation Chain | AC | HP → MS → IF → 派生 IF のすべての発行アクションが形成する、逆方向に追跡可能な署名チェーン（詳細は §3.3） |
| Revocation Registry | RR | リアルタイム撤回状態サービス（詳細は §3.4） |
| Liveness Channel | LC | 連絡途絶探知（真の連絡途絶と知覚上の連絡途絶を含む）ストリーム（詳細は §3.5、§9.9） |
| Behavior Baseline Service | BBS | (HP, IF) の行為ベースラインを維持する統計サービス（詳細は §3.6） |

### A.3 プロトコルデータオブジェクト

| プロトコル用語（英語） | ブループリント / 日本語用語 | 説明 |
| --- | --- | --- |
| Mandate | 授権令 | プロトコル層の新概念。`(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` などのフィールドを担う（詳細は §4.1 / §4.2） |
| Endorsed_Mandate | 裏書き式認可 | Mandate のサブタイプ。`endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)` を明示的に宣言し、IF が物理連絡途絶の期間中も限定範囲内で自律できるようにする。責任引き受け端は常に HP（詳細は §7.5、P16.x） |
| PresenceSignal | 在場信号 | PD が生成し、MS が検証できる物理的な在場アサーション |
| Attestation | 証言 | 統一された検証可能なアサーションの載体（WebAuthn / TPM-quote / Platform-keystore / Self-signed） |
| FayID | FayID | iFay が iFay フレームワークにおいて持つ統一的な一意身元識別子（ULID-like） |
| Faying_State | 受制御状態 | Mandate が Active / Degraded / Disconnected にあるとき IF が置かれる行為状態 |
| Rogue_Fay | 離脱状態 | Mandate が Unpaired / Revoked にあるか存在しないとき IF が置かれる行為状態。Faying_State と二項排他（P15）。**注**：`Suspended` は Rogue_Fay に含めない——これは「Faying State の一時停止」（監護関係はなお存在し、Mandate メタデータを保持し、HP の明示的回復によって新たな BOOTSTRAP を要せず回復できる）であり、行為の結果の上で Rogue と同様に D 次元を禁止するにすぎない。詳細は §4.3 / §8.2 マッピング表 |
| Faying_Initiation | 双方向 Faying 発起 | Faying 関係（確立または調整）の発起は HP が能動的に行う（HP-initiated）ことも、IF が能動的に HP へ求める（IF-initiated / FAYING_REQUEST）こともできる。最終的な発効条件はいずれも HP が検証可能な明確な認可確認を与えることである（詳細は §5.3.6、P16.6） |
| Behavior_Baseline | 行為ベースライン | BBS が維持する (HP, IF) の累積行為プロファイル。突発的な逸脱の検知に用いる（詳細は §3.6、P18.5） |
| Atomic_Action | 原子アクション | IF が対外的に実行する最小の不可分な宣言単位。1 回の呼び出しはちょうど 1 つの Atomic_Action に対応し、パッケージ化を禁止する（詳細は P18.2） |
| Disclosure_Report | 披露メッセージ | IF が報告または確認要求の際に用いる構造化メッセージ。`mandatory_fields` は強制的に解析可能（詳細は §5.3.7、P18.3） |
| Ego | 自我境界 | 同義。`ego-deviation` のトリガー判定に用いる（詳細は §3.6、§9.10.4） |
| Human View | 人類視野 | 価値観。Faying Protocol はそのプロトコルレベルの落とし込みである（ブループリント第 11 章） |

### A.4 グレードとポリシー

| プロトコル用語（英語） | 説明 |
| --- | --- |
| Authorization_Grade（Grade） | 認可グレード。値は `G0..G4`（詳細は §7） |
| G0 Emergency_Override | 緊急奪還レベル。HP が一方的に制御を強制回収する（詳細は §7.1、P12） |
| G1 Strict | 最も厳格な段位。高機微アクションの既定 grade |
| G2 Moderate | 中等段位 |
| G3 Loose | 緩い段位 |
| G4 Autonomous | 最も自律的な段位。G4 のハートビート喪失は直ちに → Suspended（詳細は §7.3） |
| PresenceRequirement | 在場要求。grade にバインドされた `(signal_types, max_staleness_ms, on_loss)` の三つ組 |
| Scope | 認可範囲。`(domains, actions, terminals?, budget?)` を明示的に宣言した最小権限集合 |

### A.5 デフォルト予算（詳細な数値は付録 B 参照）

| プロトコル用語（英語） | 概要 |
| --- | --- |
| MaxMandateLifetime | 単一 Mandate の最大寿命（既定 24h、上限 30d） |
| BootstrapTimeout | BOOTSTRAP / FAYING_REQUEST が HP 見証を待つタイムアウト（既定 60s） |
| RevocationVisibilityBudget | 撤回が RR 全網で可視となる予算（既定 1s） |
| StaleBudget | RR 到達不能の拒否閾値（既定 5s） |
| HumanReachabilityBudget | HP の連絡途絶が自動 Revoke をトリガーする閾値（既定 30min） |
| LivenessDetectionBudget | 連絡途絶探知ウィンドウの上限。grade ごとに単調に締める（詳細は付録 B、P17.3） |
| AttentionDriftThreshold | HP ビューのアイドルが「注意力の喪失」をトリガーする閾値。grade ごとに締める（詳細は付録 B、P18.4） |
| ConfirmationRateLimit | 単位時間に HP へプッシュする確認リクエスト数の上限。超過すれば自動降格 / 一時停止（詳細は付録 B、P18.6） |
| MaxDegradedDuration | Degraded 状態の最大継続時間（既定 5min/grade） |
