# `vectors/faying-request/` — FAYING_REQUEST 双向 Faying 测试向量

**Spec**：Faying Protocol/1.0
**References**：§1.5.1（双向 Faying 由 HP 显式认可生效）、§2.4 Phase A0（iFay-Initiated Faying Request）、§5.3.6（FAYING_REQUEST / FAYING_REQUEST_RESP）、§5.4 错误码 1010 / 1014
**Requirements**：1.3、11.1
**Task**：3.9（Implementation Plan）

---

## 1. 范围

本向量集覆盖 **iFay 主动向 Human Prime 寻求 Faying** 这一双向通路（IF-initiated Faying，详见 §2.4 Phase A0），包括：

- **正向路径**：iFay 发起 `FAYING_REQUEST` → MS 转交 → HP 在 `BootstrapTimeout`（默认 60 s）内通过 `BOOTSTRAP`（携 `faying_request_ref` 与可验证 `human_witness`）完成认可生效；
- **反向路径**：
  - HP 显式拒绝（`FAYING_REQUEST_RESP { status="rejected" }`）；
  - HP 在 `BootstrapTimeout` 内未给出认可（错误码 `E_FAYING_REQUEST_NOT_CONFIRMED` / `1014`）；
  - 伪造的"MS 替 HP 同意"路径（缺 `human_witness`）必须以 `E_HUMAN_WITNESS_REQUIRED` / `1010` 拒绝。

每个向量都同时声明了应当被独立写入 Attestation Chain 的 `(initiator, confirm_ts, took_effect)` 三元组，对应 Requirement 1.3 #4：

> THE Mandate_Service SHALL 将上述每一次 Faying 发起请求（无论由 Human_Prime 还是 iFay_Instance 触发，无论是否最终生效）写入 Attestation_Chain，使第三方可以独立还原"何方发起、何时确认、是否生效"。

---

## 2. 文件结构

```
vectors/faying-request/
├── README.md                    ← 本文件
├── index.json                   ← 全部向量的机读清单
├── _tools/
│   ├── generate.py              ← 确定性向量生成脚本（运行后字节级可复现）
│   └── verify.py                ← CBOR ↔ JSON round-trip + 签名校验
├── vec-01-establish/
│   ├── request.{cbor,json}              ← FAYING_REQUEST（IF→MS）
│   ├── bootstrap-followup.{cbor,json}   ← BOOTSTRAP（HP→MS，携 faying_request_ref + human_witness）
│   ├── response.{cbor,json}             ← FAYING_REQUEST_RESP / BOOTSTRAP_RESP / ERROR
│   └── expected.json                    ← outcome + Attestation Chain triple
├── vec-02-adjust-scope/        … 同上结构
├── vec-03-adjust-grade/        …
├── vec-04-renew/               …
├── vec-05-endorsement-request/ …
├── vec-06-hp-rejected/         （无 bootstrap-followup —— 因 HP 直接拒绝）
├── vec-07-bootstrap-timeout/   （response = FAYING_REQUEST_RESP{status="timeout"} + error.{cbor,json} 携带 1014）
└── vec-08-forged-ms-surrogate/ （bootstrap-followup 缺 human_witness + error.{cbor,json} 携带 1010）
```

每个向量内部的 `expected.json` 必含 `attestation_chain_entry`，其字段三元组为：

| 字段 | 含义 |
| --- | --- |
| `initiator` | 谁发起（本向量集中始终为 iFay 的 `FayID`） |
| `confirm_ts` | HP 给出认可 / 拒绝 / MS 判定超时的时间戳 |
| `took_effect` | 是否产生 Faying 状态变化（`true` 仅当 HP 在 BootstrapTimeout 内出示了可验证 `human_witness`） |

`evidence` 子段补全"凭证粘合"信息：FAYING_REQUEST 的 `msg_id`、（若发生）BOOTSTRAP 的 `msg_id`、（若发生）错误报文的 `msg_id` 与错误码、HP 见证是否存在等。

---

## 3. 向量清单（共 8 条）

| vid | reason_code | outcome | error_code | 描述 |
| --- | --- | --- | --- | --- |
| `vec-01-establish` | `establish` | `effective` | — | iFay 请求初次建立 Faying；HP 在 30 s 内完成 BOOTSTRAP 见证 |
| `vec-02-adjust-scope` | `adjust-scope` | `effective` | — | iFay 请求扩展 scope（新增 `mail.example.com` 读权限），HP 见证通过 |
| `vec-03-adjust-grade` | `adjust-grade` | `effective` | — | iFay 请求短暂提升至 G2，HP 见证通过 |
| `vec-04-renew` | `renew` | `effective` | — | iFay 请求顺延 Mandate 有效期，HP 见证通过 |
| `vec-05-endorsement-request` | `endorsement-request` | `effective` | — | iFay 请求 Endorsed Mandate 以备失联期间使用；HP 在 BOOTSTRAP 中显式打包 `endorsement` 字段 |
| `vec-06-hp-rejected` | `establish` | `rejected` | — | HP 显式以 `FAYING_REQUEST_RESP{status="rejected"}` 拒绝 |
| `vec-07-bootstrap-timeout` | `adjust-grade` | `timeout` | `E_FAYING_REQUEST_NOT_CONFIRMED`（1014） | 61 s 仍无 HP 见证 → MS 返回 `status="timeout"` 并伴随 `ERROR{1014}` |
| `vec-08-forged-ms-surrogate` | `establish` | `refused-no-witness` | `E_HUMAN_WITNESS_REQUIRED`（1010） | 攻击者尝试由 MS 替 HP 同意；BOOTSTRAP 缺 `human_witness` 必须被拒 |

---

## 4. 协议层硬约束（由本向量集联合证明）

来自 §5.3.6 与 §1.5.1：

1. **FAYING_REQUEST 不直接产生状态变化**：
   - 反向证明：`vec-06`（HP 拒绝）、`vec-07`（超时）、`vec-08`（伪造）三例的 `expected.attestation_chain_entry.took_effect = false`；
   - 正向印证：`vec-01..05` 仅在 HP 在 `BootstrapTimeout` 内给出 BOOTSTRAP 见证后 `took_effect = true`。
2. **HP 见证不可由 MS / IF / Supervisory Agent 替代**：
   - `vec-08` 的 `bootstrap-followup` 由 MS 私钥签名、issuer 字段标为 MS、且缺 `human_witness`，必须以 `E_HUMAN_WITNESS_REQUIRED`（1010）拒绝；
   - 所有 8 条向量的 `expected.hardness_checks.hp_witness_irreplaceable = true`。
3. **AC 完整记录"谁发起 / 何时确认 / 是否生效"**：
   - 全部 8 条向量在 `expected.attestation_chain_entry` 中提供 `initiator` / `confirm_ts` / `took_effect` 三字段；
   - 反向用例额外携带 `error_msg_id` / `error_code_*` / `rejected_surrogate_witness_party` 等审计扩展字段。
4. **错误码与 §5.4 一致**：
   - `vec-07` ↔ 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`（必入审计、不必入 HP 视野）；
   - `vec-08` ↔ 1010 `E_HUMAN_WITNESS_REQUIRED`（必入审计）。

---

## 5. 编码与签名约定

- **CBOR**：每个 `*.cbor` 文件均使用 RFC 8949 §4.2.1 的 Deterministic Encoding（`cbor2.dumps(canonical=True)`）。
- **JSON 镜像**：`*.json` 文件是 CBOR 的可视化对照。byte 字段以 `{ "$b64": "<base64>" }` 表达；解码后与 CBOR 完全等价（由 `_tools/verify.py` 强制校验）。
- **签名输入**：每个 Faying Protocol 信封的 `signature` 计算为 `Ed25519( SHA-256( Deterministic-CBOR( Envelope_without_signature ) ) )`（design.md §6.3）。算法字段固定 `Ed25519`；后续可演进至 PQC `ML-DSA-65`（design.md §8、Requirement 8）。
- **测试密钥**：HP / IF / MS / PD 的私钥种子由 `_tools/generate.py` 内的 `_seed("...")` 派生，**仅供测试**，禁止用于生产环境。

---

## 6. 复现与校验

```bash
# 重新生成（字节级可复现）
python3 vectors/faying-request/_tools/generate.py

# 校验：CBOR ↔ JSON 等价 + 全部签名 + AC triple 字段完整 + 反向用例错误码与 §5.4 一致
python3 vectors/faying-request/_tools/verify.py
```

`verify.py` 通过即输出：

```
  ✓ vec-01-establish
  ✓ vec-02-adjust-scope
  …
OK — 8 vectors, 23 envelopes, all CBOR ↔ JSON equivalent and all signatures verified.
```

---

## 7. 已知 TODO

- 待 design.md §12 为 Requirement 1.3 / 11.1 落定 PBT 属性后，由 `pbt/tests/test_p16_6_faying_initiation_hp_witness.py`（task 4.22）以本向量集中的 `vec-08-forged-ms-surrogate` 作为 stateful seed 输入。
- 后续若 §11 Open Questions Q12（速率限制）落定，将补充 `vec-09-rate-limit-flood` 用例覆盖 `ConfirmationRateLimit` 触发的降级 / 暂停路径。
