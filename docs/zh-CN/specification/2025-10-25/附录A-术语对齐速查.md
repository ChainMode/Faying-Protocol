---
title: "Faying Protocol/1.0 — 附录 A 术语对齐速查"
version: Faying Protocol/1.0
status: Final
part: 附录 A
language: zh-CN
---

> 协议正文导航：[章节目录](./README.md) ｜ 上一章 [§11 开放议题](./11-开放议题.md) ｜ 下一章 [附录 B 默认参数预算](./附录B-默认参数预算.md)

## 附录 A 术语对齐速查

> 本附录与本规范需求基线 Glossary、设计依据附录 A 三者保持一致；EARS 子句中出现的系统名称必须在此处定义后方可使用。本附录按"角色与实体 / 协议组件 / 协议数据对象 / 等级与策略 / 默认预算"五类组织，便于交叉查阅。

### A.1 角色与实体

| 协议术语（英文） | 蓝图 / 中文术语 | 关系 / 说明 |
| --- | --- | --- |
| Human Prime（HP） | 人类原型 | 同义；Faying 关系唯一的最终责任承接端、撤销权持有者，亦是唯一可对 Faying 状态变化给出明确认可确认的实体 |
| iFay Instance（IF） | iFay 实例 | 同义；被监护的代理实体，由 FayID 唯一标识；不拥有撤销自身 Mandate 的权力，所有状态变化以 HP 明确认可为前提 |
| Supervisory Agent（SA） | 监管 Agent | Prime 之外的另一类协议层可识别的监管主体；不持有撤销权、不可替代 HP 完成 Faying 认可确认 |
| Relying Party（RP） | 受调用方 | 被 iFay 调用的终端、应用或服务 |
| Presence Device（PD） | 在场设备 | 承载 WebAuthn / FIDO2 凭据、生物识别能力的硬件，是在场信号的物理源头 |

### A.2 协议组件

| 协议术语（英文） | 缩写 | 说明 |
| --- | --- | --- |
| Mandate Service | MS | 代表 HP 颁发 / 续期 / 降级 / 撤销 Mandate 的逻辑服务（详见 §3.1） |
| Presence Channel | PC | 从 PD 到 MS 的低延迟、抗重放在场流（详见 §3.2） |
| Attestation Chain | AC | HP → MS → IF → 派生 IF 全部签发动作形成的可逆向追溯签名链（详见 §3.3） |
| Revocation Registry | RR | 实时撤销状态服务（详见 §3.4） |
| Liveness Channel | LC | 失联探测（含真实失联与感知失联）流（详见 §3.5、§9.9） |
| Behavior Baseline Service | BBS | 维护 (HP, IF) 行为基线的统计服务（详见 §3.6） |

### A.3 协议数据对象

| 协议术语（英文） | 蓝图 / 中文术语 | 说明 |
| --- | --- | --- |
| Mandate | 授权令 | 协议层新概念；承载 `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` 等字段（详见 §4.1 / §4.2） |
| Endorsed_Mandate | 背书式授权 | Mandate 子类型；显式声明 `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)`，使 IF 在物理失联期间仍可在限定范围内自治；责任承接端始终为 HP（详见 §7.5、P16.x） |
| PresenceSignal | 在场信号 | 由 PD 产生的、可被 MS 校验的物理在场断言 |
| Attestation | 证言 | 统一的可验证断言载体（WebAuthn / TPM-quote / Platform-keystore / Self-signed） |
| FayID | FayID | iFay 在 iFay 框架中的统一唯一身份标识（ULID-like） |
| Faying_State | 受控状态 | Mandate 处于 Active / Degraded / Disconnected 时 IF 所处的行为状态 |
| Rogue_Fay | 脱离状态 | Mandate 处于 Unpaired / Revoked 或不存在时 IF 所处的行为状态；与 Faying_State 二态互斥（P15）。**注**：`Suspended` 不归入 Rogue_Fay——它是"Faying State 暂停"（监护关系仍在、Mandate 元数据保留、可由 HP 显式恢复而无需新一轮 BOOTSTRAP），仅在行为后果上与 Rogue 一样禁止 D 维度；详见 §4.3 / §8.2 映射表 |
| Faying_Initiation | 双向 Faying 发起 | Faying 关系（建立或调整）的发起既可由 HP 主动（HP-initiated），亦可由 IF 主动向 HP 寻求（IF-initiated / FAYING_REQUEST）；最终生效条件均为 HP 给出可验证的明确认可确认（详见 §5.3.6、P16.6） |
| Behavior_Baseline | 行为基线 | 由 BBS 维护的 (HP, IF) 累积行为画像，用于检测突发偏离（详见 §3.6、P18.5） |
| Atomic_Action | 原子动作 | IF 对外执行的最小不可拆分声明单元；一次调用恰好对应 1 个 Atomic_Action，禁止打包（详见 P18.2） |
| Disclosure_Report | 披露报文 | IF 在汇报或请求确认时使用的结构化报文；`mandatory_fields` 强制可解析（详见 §5.3.7、P18.3） |
| Ego | 自我边界 | 同义；用于 `ego-deviation` 触发判定（详见 §3.6、§9.10.4） |
| Human View | 人类视野 | 价值观；Faying Protocol 是其协议级落地（蓝图第 11 章） |

### A.4 等级与策略

| 协议术语（英文） | 说明 |
| --- | --- |
| Authorization_Grade（Grade） | 授权等级，取值 `G0..G4`（详见 §7） |
| G0 Emergency_Override | 紧急夺回级；HP 单方面强制收回控制（详见 §7.1、P12） |
| G1 Strict | 最严格档；高敏感动作的默认 grade |
| G2 Moderate | 中等档 |
| G3 Loose | 宽松档 |
| G4 Autonomous | 最自主档；G4 心跳丢失直接 → Suspended（详见 §7.3） |
| PresenceRequirement | 在场要求；绑定到 grade 的 `(signal_types, max_staleness_ms, on_loss)` 三元组 |
| Scope | 授权范围；`(domains, actions, terminals?, budget?)` 显式声明的最小权限集合 |

### A.5 默认预算（详细数值见附录 B）

| 协议术语（英文） | 简述 |
| --- | --- |
| MaxMandateLifetime | 单个 Mandate 最大寿命（默认 24h，上限 30d） |
| BootstrapTimeout | BOOTSTRAP / FAYING_REQUEST 等待 HP 见证的超时（默认 60s） |
| RevocationVisibilityBudget | 撤销在 RR 全网可见的预算（默认 1s） |
| StaleBudget | RR 不可达拒绝阈值（默认 5s） |
| HumanReachabilityBudget | HP 失联触发自动 Revoke 的阈值（默认 30min） |
| LivenessDetectionBudget | 失联探测窗口上限；按 grade 单调收紧（详见附录 B、P17.3） |
| AttentionDriftThreshold | HP 视野空闲触发"注意力丢失"的阈值；按 grade 收紧（详见附录 B、P18.4） |
| ConfirmationRateLimit | 单位时间内向 HP 推送的确认请求数量上限；超限自动降级 / 暂停（详见附录 B、P18.6） |
| MaxDegradedDuration | Degraded 状态最大持续时间（默认 5min/grade） |

