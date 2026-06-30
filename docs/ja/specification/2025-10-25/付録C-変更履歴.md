---
title: "Faying Protocol/1.0 — 付録 C 変更履歴"
version: Faying Protocol/1.0
status: Final
part: 付録 C
language: ja
---

> プロトコル本文ナビ：[章目次](./README.md) ｜ 前章 [付録 B デフォルトパラメータ予算](./付録B-デフォルトパラメータ予算.md)

# 付録 C 変更履歴

この履歴は、Faying Protocol/1.0 ドラフトが着手から確定稿に至るまでの間に、仕様本文と付随する成果物にどのような変化が起きたかを記録する。形式上は [Keep a Changelog](https://keepachangelog.com) のグルーピング慣行（Added / Changed / Deprecated / Removed / Security）を踏襲し、その前にバージョン番号の定め方を説明する。

> 出所に関する率直な説明：本プロトコルの 1.0 ドラフトは spec 駆動のプロセスで一気に産出されたものであり（要件 → 設計 → タスクリスト → 実装）、まだ複数回の独立したプロトコル委員会会議を経ていない。したがって本履歴は逐条の会議決議や正確な日付を捏造せず、「何をしたか、なぜか、どのタスクに対応するか」を事実どおりに記録するにとどめる。以下で引用するタスク番号（1.6、3.8、5.6 など）は実装タスク計画の実在の項目に対応し、これに基づいて各変更の産出位置を遡れる。今後、正式な委員会レビューのプロセスに入った際に、日付と決議番号を付した項目をここに追記する。

## バージョン番号の定め方

プロトコルバージョン番号付けの**権威的規則は本文 §1.7 バージョン管理と互換性を参照**（3 本の直交軸：プロトコルバージョン `MAJOR.MINOR` / 文書ステータス / 編集版次。協商と互換性規則。バージョン番号の落としどころと実装者の注意事項）。本付録は重複して定義せず、変更履歴に関連する 2 点のみを補足する。

- 本履歴は §1.7.2 の MAJOR / MINOR 判定基準に従って各変更を分類する：相互運用を破壊するものは MAJOR、後方互換の追加は MINOR、純粋な文面の正誤訂正は §1.7.4 に従って `Editorial` に分類しプロトコル番号を変えない。
- 現在は `Faying Protocol/1.0`、最初のベースライン、ステータス Final（2025-10-25 公開）。

命名の上では、散文とバージョン番号を統一して `Faying Protocol/1.0` とし、初期の `FAP` 略称は廃止済みである。ただし schema ファイル名 `fap-1.0.cddl` / `fap-1.0.proto` は旧プレフィックスを保留しているが、これは純粋にファイル名の安定性のため、既存参照を壊さないためであり——意図的なものであって命名の二転三転ではない（§1.7.5「schema ファイル名は編集版次で改名しない」と整合）。

## [Faying Protocol/1.0] — Final（2025-10-25）

これは 1.0 の最初の正式リリース版であり、2025-10-25 にドラフト作業領域から正式公開ディレクトリへ全体を一括移行して確定稿とした。以下、変更タイプ別に分類し、各項目にそれを産出したタスク番号を記す。

### Added

本文（§1–§11 + 付録 A/B）：

- §1 Overview：プロトコルの命名、位置づけ、8 項目の設計目標 G1–G8、目標と Requirement の一対一対応。§1.5.1 で「双方向 Faying はいずれも HP の明示的認可で初めて発効する」という中核命題を確立。（タスク 1.2）
- §2 Architecture：4 枚の Mermaid 図（プロトコルスタック、エンティティ関係、グレード階層、Bootstrap+Heartbeat+Action シーケンス、IF が能動的に発起する Phase A0 経路を含む）と 6 項目の設計原則。（タスク 1.3）
- §3 Components and Interfaces：6 つのコンポーネント（MS / PC / AC / RR / LC / BBS）のインターフェースと不変条件。（タスク 1.4）
- §4 Data Models：CDDL 権威定義、TypeScript 人間向けビュー、Disconnected 状態と再接続照合を含む Mandate 状態機械、endorsement サブ構造。（タスク 1.5）
- §5 Protocol Messages：7 種類のメッセージ（BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE）、統一エンベロープ、14 項目のエラーコード——うち 1010 `E_HUMAN_WITNESS_REQUIRED`、1013 `E_ENDORSEMENT_INVALID`、1014 `E_FAYING_REQUEST_NOT_CONFIRMED` を新設。（タスク 1.6）
- §6 Cryptography：アルゴリズムスイートの協商（PQC 協商ビットを含む）、鍵派生、署名フォーマット。endorsement フィールドを署名入力に組み入れ。（タスク 1.7）
- §7 Authorization Grades：G0–G4 の 5 段階意味論、トリガー行列、降格の単調性、および G1–G4 の上に重ねる §7.5 Endorsement Grades 子グレード。（タスク 1.8）
- §8 Lifecycle：7 状態のライフサイクル（Disconnected を含む）、責任帰属シーケンス、§8.4 再接続照合トランザクション。（タスク 1.9）
- §9 Security Considerations：STRIDE、リプレイ／乗っ取り／フィッシング耐性、離脱状態の識別、連絡途絶処理行列、および §9.10 の AI 時代の対抗的脅威カタログ T1–T7。（タスク 1.10）
- §10 Error Handling、§11 Open Questions、付録 A/B：エラーシナリオと回復経路、未解決課題 Q1–Q14、用語集、デフォルトパラメータ予算。（タスク 1.11）
- 英語仕様の全文翻訳。（タスク 1.12）

付随する成果物：

- schema：`schemas/fap-1.0.cddl`（権威）、`schemas/types.ts`（TypeScript 人間向けビュー、Not Normative）、`schemas/fap-1.0.proto`（代替 gRPC バインディング、Not Normative）。（タスク 2.1–2.3）
- テストベクトル `vectors/`：BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE、エラーコード、エンコーディング等価、Endorsement、FAYING_REQUEST、DISCLOSURE、Disconnection の計 11 類をカバー。（タスク 3.1–3.11）
- プロパティテスト `pbt/`：P1–P15 主プロパティをカバーし、P16（Endorsed_Mandate）、P17（Disconnection）、P18（AI-Era）の 3 族を加える。（タスク 4.1–4.34）
- 相互運用コンプライアンススイート `conformance/`：エンコーディング × 署名アルゴリズム × ハッシュ × チャネル × 実装言語の 5 次元マトリクス。TypeScript と Rust の 2 つの reference 実装を付す。（タスク 5.1–5.6）
- セキュリティ攻撃シミュレーション `conformance/attacks/`：リプレイ、乗っ取り、フィッシング、離脱状態の識別、および T1/T3/T4/T5/T6 のシミュレーション。（タスク 6.1–6.10）

### Changed

- プロトコルの命名を、初期ドラフトの "Faying Auth Protocol（FAP）" から **Faying Protocol** へ変更し、バージョン番号は `Faying Protocol/1.0` と表記する。（§11 Q10 に対応、決議済み）
- Faying の発起を、単方向（HP のみが発起できる）から双方向（HP 発起 + IF 発起）へ拡張したが、発効条件は「HP の明確な認可」という一点に統一して収束させた。（タスク 1.6、3.9）
- 連絡途絶を「真の連絡途絶」と「知覚上の連絡途絶」の 2 つの意味論に分割し、プロトコルの決定は知覚上の連絡途絶のみを見て、不一致ウィンドウには悲観的推定を行う。（タスク 1.10、3.11）
- 署名入力を `H(Deterministic-CBOR(Envelope_without_signature))` に統一し、CBOR 主フォーマットと JSON フォールバックがこの流儀のもとで等価に相互運用する。（タスク 3.7、5.2）

### Deprecated

- `FAP` / `FAP/1.0` / `Faying Auth Protocol` などの旧命名、および `application/fap+json`、`POST /fap/v1/...` などの旧エンドポイント形態は、一律廃止する。新表記は `application/faying-protocol+json` と `POST /faying-protocol/v1/{verb}` を用いる。schema ファイル名は旧プレフィックスを保留する唯一の例外である（上記「バージョン番号の定め方」参照）。

### Removed

- なし。1.0 は最初のベースラインであり、移除を要する既存フィールドやメッセージはない。

### Security

- AI 時代の対抗的脅威に対するプロトコルレベルの制約を新設：T1 ソーシャルエンジニアリング、T2 ブラックボックス操作、T3 軽きに就く、T4 注意の漂流、T5 固定観念的信頼の育成、T6 監査洪水、T7 拡張スロット。各項は Property P18.1–P18.7 と Requirement 13.1–13.7 に対応。（タスク 1.10、4.28–4.34、6.6–6.10）
- 裏書き式認可の改竄防止制約：endorsement を署名入力に組み入れ、いずれかのサブフィールドを変えると Mandate の署名検証が失敗する（`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`）。（タスク 1.5、3.8、4.17–4.21）
- 対称的な撤回と撤回の不可逆性：撤回経路の到達性は確立経路を下回らず、`Revoked` は吸収状態、連鎖撤回は既定で有効。（タスク 3.5、4.5、4.11、4.15）

## 今後の保守の仕方

- 正式なレビューに入った後は、委員会の各決議をここに 1 行追記し、日付、影響する章節、トリガーしたタスク番号を注記したうえで、上記の対応する Keep a Changelog グループに人間向けの項目を 1 つ補う。
- バージョン番号：§1.7 に従って実行する——後方互換の追加は MINOR を進め、破壊的変更は MAJOR を進めて MINOR をゼロに戻し、純粋な文面の正誤訂正は編集版次（§1.7.4）でプロトコル番号を変えない。
- 後続の正誤訂正と版次の移行は §1.7.4 / §1.7.5 に従って行う。本履歴は本文とともに移行済みであり、以後は版次に応じて更新する。
- 日本語版と英語版の同種の変更は同一サイクルで同期し、差異が生じた場合は簡体中国語版（zh-CN）を正とする。
