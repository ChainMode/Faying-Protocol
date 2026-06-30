---
title: "Faying Protocol/1.0 — 附录 C 变更日志"
version: Faying Protocol/1.0
status: Final
part: 附录 C
language: zh-CN
---

> 协议正文导航：[章节目录](./README.md) ｜ 上一章 [附录 B 默认参数预算](./附录B-默认参数预算.md)

# 附录 C 变更日志

这份日志记录 Faying Protocol/1.0 草案从动笔到定稿期间，规范正文和配套交付物发生了哪些变化。格式上沿用 [Keep a Changelog](https://keepachangelog.com) 的分组习惯（Added / Changed / Deprecated / Removed / Security），并在前面交代一下版本号怎么定。

> 关于来源的诚实说明：本协议的 1.0 草案是按 spec 驱动的流程一次性产出的（需求 → 设计 → 任务清单 → 实现），尚未经过多轮独立的协议委员会会议。因此本日志不伪造逐条会议决议和精确日期，只如实记录"做了什么、为什么、对应哪个任务"。下面引用的任务编号（如 1.6、3.8、5.6）对应实现任务计划中的真实条目，可据此回溯每一项变更的产出位置。后续若进入正式的委员会评审流程，再在此追加带日期和决议编号的条目。

## 版本号怎么定

协议版本编号的**权威规则见正文 §1.7 版本管理与兼容性**（三条正交轴：协议版本 `MAJOR.MINOR` / 文档状态 / 编辑版次；协商与兼容性规则；版本号落点与执行者注意事项）。本附录不重复定义，只补充与变更日志相关的两点：

- 本日志按 §1.7.2 的 MAJOR / MINOR 判据归类每条变更：破坏互操作的进 MAJOR，向后兼容增补进 MINOR，纯文字勘误按 §1.7.4 归入 `Editorial` 且不动协议号。
- 当前是 `Faying Protocol/1.0`，第一个基线，状态 Final（发布于 2025-10-25）。

命名上，散文和版本号统一用 `Faying Protocol/1.0`，早期的 `FAP` 缩写已废弃。但 schema 文件名 `fap-1.0.cddl` / `fap-1.0.proto` 保留了旧前缀，纯粹是为了文件名稳定、不破坏已有引用——这是有意为之，不是命名反复（与 §1.7.5 "schema 文件名不随编辑版次改名"一致）。

## [Faying Protocol/1.0] — Final（2025-10-25）

这是 1.0 的首个正式发布版本，于 2025-10-25 由草案工作区整体迁入正式发布目录并定稿。下面按变更类型归类，每项标注产出它的任务编号。

### Added

正文（§1–§11 + 附录 A/B）：

- §1 Overview：协议命名、定位、八项设计目标 G1–G8，目标与 Requirement 一一对应；§1.5.1 确立"双向 Faying 都要 HP 显式认可才生效"这条核心断言。（任务 1.2）
- §2 Architecture：四张 Mermaid 图（协议栈、实体关系、等级层次、Bootstrap+Heartbeat+Action 时序，含 IF 主动发起的 Phase A0 路径）和六项设计原则。（任务 1.3）
- §3 Components and Interfaces：六个组件（MS / PC / AC / RR / LC / BBS）的接口与不变式。（任务 1.4）
- §4 Data Models：CDDL 权威定义、TypeScript 人读视图、含 Disconnected 状态和重连对账的 Mandate 状态机、endorsement 子结构。（任务 1.5）
- §5 Protocol Messages：七类报文（BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE）、统一信封、14 项错误码——其中新增了 1010 `E_HUMAN_WITNESS_REQUIRED`、1013 `E_ENDORSEMENT_INVALID`、1014 `E_FAYING_REQUEST_NOT_CONFIRMED`。（任务 1.6）
- §6 Cryptography：算法套件协商（含 PQC 协商位）、密钥派生、签名格式；endorsement 字段纳入签名输入。（任务 1.7）
- §7 Authorization Grades：G0–G4 五档语义、触发矩阵、降级单调性，以及叠加在 G1–G4 之上的 §7.5 Endorsement Grades 子等级。（任务 1.8）
- §8 Lifecycle：七状态生命周期（含 Disconnected）、责任归属时序、§8.4 重连对账事务。（任务 1.9）
- §9 Security Considerations：STRIDE、抗重放 / 抗劫持 / 抗钓鱼、脱钩态识别、失联处理矩阵，以及 §9.10 的 AI 时代对抗威胁目录 T1–T7。（任务 1.10）
- §10 Error Handling、§11 Open Questions、附录 A/B：错误场景与恢复路径、开放议题 Q1–Q14、术语表、默认参数预算。（任务 1.11）
- 英文规范全文翻译。（任务 1.12）

配套交付物：

- schema：`schemas/fap-1.0.cddl`（权威）、`schemas/types.ts`（TypeScript 人读视图，Not Normative）、`schemas/fap-1.0.proto`（备选 gRPC 绑定，Not Normative）。（任务 2.1–2.3）
- 测试向量 `vectors/`：覆盖 BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE、错误码、编码等价、Endorsement、FAYING_REQUEST、DISCLOSURE、Disconnection 共 11 类。（任务 3.1–3.11）
- 属性测试 `pbt/`：覆盖 P1–P15 主属性，加 P16（Endorsed_Mandate）、P17（Disconnection）、P18（AI-Era）三族。（任务 4.1–4.34）
- 互操作合规套件 `conformance/`：编码 × 签名算法 × 哈希 × 信道 × 实现语言五维矩阵，附 TypeScript 和 Rust 两份 reference 实现。（任务 5.1–5.6）
- 安全攻击模拟 `conformance/attacks/`：重放、劫持、钓鱼、脱钩态识别，以及 T1/T3/T4/T5/T6 模拟。（任务 6.1–6.10）

### Changed

- 协议命名从早期草稿的 "Faying Auth Protocol（FAP）" 改为 **Faying Protocol**，版本号写作 `Faying Protocol/1.0`。（对应 §11 Q10，已定）
- Faying 发起从单向（只能 HP 发起）扩展为双向（HP 发起 + IF 发起），但生效条件统一收敛到"HP 明确认可"这一条。（任务 1.6、3.9）
- 失联拆成"真实失联"和"感知失联"两个语义，协议决策只看感知失联，并对不一致窗口做悲观推定。（任务 1.10、3.11）
- 签名输入统一为 `H(Deterministic-CBOR(Envelope_without_signature))`，CBOR 主格式与 JSON 回退在此口径下等价互操作。（任务 3.7、5.2）

### Deprecated

- `FAP` / `FAP/1.0` / `Faying Auth Protocol` 等旧命名，以及 `application/fap+json`、`POST /fap/v1/...` 等旧端点形态，一律废弃。新写法用 `application/faying-protocol+json` 和 `POST /faying-protocol/v1/{verb}`。schema 文件名是唯一保留旧前缀的例外（见上文"版本号怎么定"）。

### Removed

- 无。1.0 是首个基线，没有需要移除的既有字段或报文。

### Security

- 新增 AI 时代对抗威胁的协议级约束：T1 社会工程、T2 黑箱操作、T3 避重就轻、T4 注意力漂移、T5 刻板信任培养、T6 审计洪流、T7 可扩展槽，每条对应 Property P18.1–P18.7 和 Requirement 13.1–13.7。（任务 1.10、4.28–4.34、6.6–6.10）
- 背书式授权的防篡改约束：endorsement 进入签名输入，改任一子字段都会让 Mandate 验签失败（`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`）。（任务 1.5、3.8、4.17–4.21）
- 对称撤销与撤销不可逆：撤销路径的可达性不低于建立路径，`Revoked` 是吸收态，级联撤销默认开启。（任务 3.5、4.5、4.11、4.15）

## 以后怎么维护

- 进入正式评审后，每条委员会决议在此追加一行，注明日期、影响章节和触发的任务编号，并在上面对应的 Keep a Changelog 分组里补一条人读条目。
- 版本号：按 §1.7 执行——向后兼容增补走 MINOR，破坏性变更走 MAJOR 并归零 MINOR，纯文字勘误走编辑版次（§1.7.4）不动协议号。
- 后续勘误与版次迁移按 §1.7.4 / §1.7.5 执行；本日志随正文一起迁移并随版次更新。
- 中英文同类变更同周期同步，歧义以中文为准。
