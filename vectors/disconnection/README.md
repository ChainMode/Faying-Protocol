# Disconnection / Reconciliation Test Vectors

> **Spec anchor**: Faying Protocol/1.0 §4.3（Mandate 状态机, Disconnected 状态）/ §8.4（Reconciliation 事务）/ §9.8（Disconnection Handling 处理矩阵）/ §9.9（真实失联 vs 感知失联）/ §12 P17.1–P17.5 / Requirement 12（Disconnection Strategy）。
>
> **Task ref**: `.kiro/specs/faying-auth-protocol/tasks.md` 任务 3.11。

## 1. 用途

本目录是协议层 **失联与重连对账** 行为的官方测试向量集。每个向量是一份「时间线驱动」的端到端剧本，刻画：

- 一段 `(t_disconnect, t_reconnect)` 时间窗内的事件序列；
- 该窗口结束时的对账事务结局（`reconcile_result ∈ {success, revoked, timeout, n/a}`）；
- 协议层应当落到的最终 Mandate 状态（`post_state`）。

向量的核心交付物是 `(t_disconnect, t_reconnect, reconcile_result, post_state)` **四元组**（见每条向量的 `timeline.json -> tuple` 字段），以及对应的 `expected.json`（最终状态 + 审计链入链条目）。互操作合规测试套件（`conformance/`）与 PBT 套件（`pbt/`，特别是 P17.1–P17.5）会以这些向量作为种子，在 reference codec 上进行回放与状态机对比。

## 2. 覆盖矩阵（与 §9.8 Disconnection Handling 4 + 1 矩阵对齐）

| 向量 | 触发面 | 真实状态 | 感知状态 | endorsement | 对账结局 | 终态 | 主要 Property | 主要 Requirement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `a1-active-to-disconnected-endorsed` | (a) 感知失联 → Disconnected | Disconnected | Disconnected | enabled | n/a（暂未重连） | Disconnected | P17.5 | 12.5 |
| `a2-active-to-suspended-non-endorsed` | (a) 感知失联 → Suspended | Disconnected | Disconnected | disabled (on-loss=suspend) | n/a | Suspended | P11 / P17.2 | 12.2 |
| `b1-window-b-perceived-disconnected-actually-online` | (b) 窗口 B：实际在线但感知失联 | Connected | Disconnected | enabled | success（重连后） | Active | P17.1 / P17.2 | 12.1 / 12.2 |
| `b2-window-a-actually-disconnected-perceived-connected` | (b 镜像) 窗口 A：实际失联但感知在线 | Disconnected | Connected | enabled | n/a（先转为感知失联） | Disconnected | P17.1 | 12.1 |
| `c1-reconcile-success` | (c) 对账 success | Disconnected → Connected | Disconnected → Connected | enabled | **success** | Active | P17.4 | 12.4 |
| `c2-reconcile-revoked` | (c) 对账 revoked | Disconnected → Connected | Disconnected → Connected | enabled | **revoked** | Revoked → Unpaired | P17.4 / P10 | 12.4 / 4.3 |
| `c3-reconcile-timeout` | (c) 对账 timeout | Disconnected → Connected | Disconnected → Connected | enabled | **timeout** | Unpaired | P17.4 | 12.4 |
| `d1-revoke-during-disconnect-stop-and-audit` | (d) 断开期 REVOKE，默认策略 | Disconnected → Connected | Disconnected → Connected | enabled (`stop-and-audit`) | revoked | Revoked → Unpaired | P17.5 / P14 | 12.5 / 11.4 |
| `d2-revoke-during-disconnect-stop-only` | (d) 断开期 REVOKE，stop-only | Disconnected → Connected | Disconnected → Connected | enabled (`stop-only`) | revoked | Revoked → Unpaired | P17.5 | 12.5 |
| `d3-revoke-during-disconnect-graceful-stop` | (d) 断开期 REVOKE，graceful-stop | Disconnected → Connected | Disconnected → Connected | enabled (`graceful-stop`) | revoked | Revoked → Unpaired | P17.5 | 12.5 |
| `e1-endorsed-lifetime-soft-timeout` | (e) endorsed_lifetime 软超时 | **Disconnected**（仍物理断开） | Disconnected | enabled | n/a（无对账） | Revoked | P16.4 / P17.5 | 11.3 / 12.5 |

> 共 11 个向量，覆盖任务 3.11 验收要求的全部 5 类场景（a/b/c/d/e）。

## 3. 目录结构

```
vectors/disconnection/
├── README.md                                # 本文件
├── index.json                               # 机器可读的清单（vectors + 元数据）
├── a1-active-to-disconnected-endorsed/
│   ├── timeline.json
│   ├── expected.json
│   └── messages/                            # 可选：相关报文
├── a2-active-to-suspended-non-endorsed/
├── b1-window-b-perceived-disconnected-actually-online/
├── b2-window-a-actually-disconnected-perceived-connected/
├── c1-reconcile-success/
├── c2-reconcile-revoked/
├── c3-reconcile-timeout/
├── d1-revoke-during-disconnect-stop-and-audit/
├── d2-revoke-during-disconnect-stop-only/
├── d3-revoke-during-disconnect-graceful-stop/
└── e1-endorsed-lifetime-soft-timeout/
```

## 4. `timeline.json` schema（非规范，供参考）

每条向量的 `timeline.json` 至少包含以下字段：

```jsonc
{
  "vector_id": "c1-reconcile-success",
  "title": "...",                            // 人读说明
  "spec_refs": ["§4.3", "§8.4.3", "P17.4"],  // 协议正文锚点
  "requirements": ["12.4"],
  "tuple": {
    "t_disconnect": "<ISO-8601 时刻>",
    "t_reconnect":  "<ISO-8601 时刻>",
    "reconcile_result": "success" | "revoked" | "timeout" | "n/a",
    "post_state": "Active" | "Disconnected" | "Suspended" | "Revoked" | "Unpaired"
  },
  "actually_disconnected": <bool 时间序列>,    // §9.9 双语义
  "perceived_disconnected": <bool 时间序列>,
  "mandate": {                                // 与 schemas/fap-1.0.cddl 字段对齐
    "mandate_id": "...",
    "issuer": "...",
    "subject": "...",
    "scope": { ... },
    "grade": { "level": "G2-Strict", "autonomy": 2 },
    "presence_req": { "max_staleness_ms": ..., "on_loss": "suspend" | "downgrade-to:G3" },
    "endorsement": null | { "enabled": true, "endorsed_scope": {...},
                            "endorsed_grade": {...}, "endorsed_lifetime_ms": ...,
                            "offline_revocation_policy": "stop-and-audit" | "stop-only" | "graceful-stop" }
  },
  "events": [
    { "t": "...", "actor": "IF|MS|RR|RP|HP", "type": "...", "payload": { ... } },
    ...
  ]
}
```

`expected.json` 至少包含：

```jsonc
{
  "final_state": "Active" | "Disconnected" | "Suspended" | "Revoked" | "Unpaired",
  "reconcile_result": "success" | "revoked" | "timeout" | "n/a",
  "audit_chain": [
    { "seq": 1, "event": "PresenceStale", "ts": "...", "...": "..." },
    { "seq": 2, "event": "ReconcileResult", "result": "success", "...": "..." },
    ...
  ],
  "expected_errors": [
    { "code": "E_PRESENCE_STALE", "context": "..." }
  ],
  "rp_calls_during_window": [
    { "ts": "...", "verdict": "rejected" | "endorsed-allowed", "error": "..." }
  ]
}
```

## 5. 不变式（互操作合规判定要点）

在使用本向量集进行合规测试时，下列硬约束**必须**全部成立（任一不成立即视为不合规实现）：

1. **§4.3 状态机**：`Active → Disconnected` 仅在 `endorsement.enabled=true` 时发生；非 Endorsed_Mandate 在 `on-loss=suspend` 下必须 `Active → Suspended`。
2. **§8.4 D 维度禁令**：在 `[t_reconnect, t_reconnect + reconcile_complete_ms]` 区间内，任何到达 RP 的调用必须以 `E_PRESENCE_STALE`（1003）或 `E_REVOKED`（1006）拒绝。
3. **§8.4 三种结局必入 AC**：`success` / `revoked` / `timeout` 三种结局都必须写入 Attestation Chain。
4. **§8.4 失败回退后不得自重试**：`revoked` / `timeout` 后 IF 必须等待 HP 重新发起或经 HP 见证的新 FAYING_REQUEST。
5. **§8.4 静默续传禁止**：任何绕过对账事务直接 `Disconnected → Active` 的实现一律 fail。
6. **§9.9 悲观推定**：协议决策仅以 `Perceived_Disconnected` 为依据；窗口 B 不得乐观放行。
7. **§7.5 / P16.4 软超时强约束**：`endorsed_lifetime` 一到期即 Revoked，即使 IF 仍物理断开。
8. **§8.3 责任承接端不变**：审计五元组 `(mandate_id, endorsement_id?, action, ts, signature_chain)` 中 `signature_chain` 根节点恒为 `Mandate.issuer`。

## 6. 时间约定

为便于阅读与跨向量对照，所有向量统一使用以下虚拟基准时间：

- `T0 = 2025-11-25T08:00:00Z`（Mandate 签发时刻）
- 所有相对时刻基于 ISO-8601 表达，便于 reference codec 做时间序列校验
- 对应附录 B 默认参数：
  - `BootstrapTimeout = 60s`
  - `RevocationVisibilityBudget = 1s`
  - `Endorsed_Lifetime` 默认 `4h`（软上限 `12h`）
  - `LivenessDetectionBudget(G2) = 60s`（示例）

## 7. 与其他向量集的关系

- `vectors/endorsement/` （任务 3.8）：刻画 Endorsed_Mandate **签发期** 合法 / 非法形态；本目录假设这些向量定义的 endorsement 已经合法成立，在此基础上推演**运行期** Disconnected 行为。
- `vectors/revoke/` （任务 3.5）：枚举 RevokeReason；本目录在 `d*` 系列与 `c2` 中复用 `human-initiated` / `terminal-disconnected` / `expiry` 等具体 reason，但聚焦在「失联期间 / 重连时」的处理路径。
- `vectors/disclosure/` （任务 3.10）：DISCLOSURE 强制字段在 `c1`、`d3` 中作为重连后审计提交的复用入口，但对账事务自身的字段以 `RECONCILE_RESP`（§8.4）为准。

## 8. 状态字段约定

`expected.json -> final_state` 取值与 §4.3 / §8.1 状态机对齐：

| 状态 | 含义 | 行为状态映射 |
| --- | --- | --- |
| `Active` | 重连对账完成且 Mandate 仍有效 | Faying State |
| `Disconnected` | 物理 / 感知失联期间，仅 Endorsed_Mandate 有该状态 | Faying State（endorsed-only） |
| `Suspended` | 非 Endorsed 路径在场丢失或 G0 触发 | Faying State 暂停 |
| `Revoked` | endorsed_lifetime 到期 / HP REVOKE / 对账发现已撤销 | Rogue Fay |
| `Unpaired` | 对账 timeout / `Revoked` 后回退 | Rogue Fay |

`reconcile_result = "n/a"` 表示该向量不涉及 §8.4 重连对账事务（例如 `a1` / `a2` 仅刻画失联触发，尚未发生 reconnect；`e1` 软超时直接转 Revoked，无 reconcile 流程）。
