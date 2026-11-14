# dim_signing — 签名算法维度合规测试

> **Task anchor** — 实现 [`tasks.md` 任务 5.3](../../docs/zh-CN/specification/2025-10-25/README.md) 「签名算法维度合规测试（Ed25519 / ECDSA-P256 / ML-DSA-65）」。
> **Requirements anchor** — [Requirement 8.1（算法套件可协商）](../../docs/zh-CN/specification/2025-10-25/README.md) / [Requirement 8.2（PQC 算法位预留）](../../docs/zh-CN/specification/2025-10-25/README.md) / [Requirement 10.3（跨实现兼容矩阵）](../../docs/zh-CN/specification/2025-10-25/README.md)。

## 1. 目的

本目录是 5 维互操作矩阵中 **signing-alg 维度** 的可执行驱动器。它对协议正本枚举的三种签名算法逐一执行：

| 算法 | 来源 | 状态 |
| --- | --- | --- |
| `Ed25519` | design.md §6.1 默认 | MUST 支持（Requirement 8.1 子句 3） |
| `ES256`（ECDSA-P256） | design.md §6.1 备选 | MUST 支持（Requirement 8.1 子句 3） |
| `ML-DSA-65`（FIPS 204） | design.md §6.1 PQC 协商位 | OPTIONAL（Requirement 8.2 子句 3） |

任务 5.3 的两条验收：

- **3/3 算法跑通**：每条 `vectors/` 里的合规向量都能被三种算法各自重签 + 验签通过。
- **ML-DSA-65 OPTIONAL**：实现方未声明支持 PQC 时，BOOTSTRAP 仍能通过经典算法对（`{Ed25519, ECDSA-P256}`）落地，不得以"对方不支持 PQC"为由拒绝。

## 2. 模块组成

| 文件 | 职责 |
| --- | --- |
| `algorithms.py` | 三种算法的统一 `sign` / `verify` / `generate_keypair` API；ML-DSA-65 路径使用与 `vectors/bootstrap/_tools/generate.py` 完全一致的确定性占位签名 |
| `negotiation.py` | Requirement 8.1 协商规则的可执行实现；强度顺序 `ML-DSA-65 > Ed25519 > ES256`，无交集时抛 `NegotiationError`（即 `E_PROTOCOL` / 1099） |
| `resign.py` | 加载 `vectors/<category>/<vector>/{request.cbor,request.json,debug.json}`，剥离原签名，按 design.md §6.3 的 `H(Det-CBOR(Envelope_without_signature))` 重新签发 |
| `test_dim_signing.py` | pytest 套件：A 类「重签覆盖」+ B 类「算法协商」 |

## 3. 协商强度顺序

```
NEGOTIATION_ORDER = ("ML-DSA-65", "Ed25519", "ES256")
```

- PQC 优先于经典算法（design.md §6.1 PQC 协商位）。
- `Ed25519` 是 design.md §6.1 标注的「默认」（更小签名 / 抗 nonce 重用），故强度高于 `ES256`。
- 协商函数返回 `client ∩ server` 中按上表排序的首个算法；交集为空时抛 `NegotiationError`，错误码恒为 `E_PROTOCOL`（1099）。

## 4. ML-DSA-65 占位签名说明

> **关键边界** — 本目录的 `ML-DSA-65` 路径**不是密码学实现**，仅为协商逻辑的占位驱动。

向量作者时刻（Faying Protocol/1.0 Draft）尚无成熟的纯 Python ML-DSA 库，因此：

- 公钥格式 `b"test-only-ml-dsa-65-pubkey-" || expand(seed)`，与 [`vectors/bootstrap/_tools/generate.py`](../../vectors/bootstrap/_tools/generate.py) 完全一致。
- 签名格式 `b"test-only-ml-dsa-65-sig-" || label[:8] || sha256(message)`。
- 校验仅做格式 + sha256 比对，**不构成密码学验证**。
- 本路径只用于：
  1. 验证算法**协商**逻辑（task 5.3 验收的真正主语）。
  2. 验证签名输入构造（design.md §6.3）在三种算法下保持不变。
- 真正的 ML-DSA-65 接入时机：见 [`tasks.md` task 5.6](../../docs/zh-CN/specification/2025-10-25/README.md) 的跨实现兼容轮次，届时 reference 实现（TS / Rust）将接入 NIST FIPS 204 标准库。

> 任何想以「ML-DSA-65 通过」声明协议合规的实现，必须替换本目录的占位以接入真实的 FIPS 204 实现，并在 conformance 报告中标注实现来源。

## 5. 运行

```bash
# 全量执行 dim_signing
pytest conformance/dim_signing/

# 仅看 ML-DSA-65 OPTIONAL 这条
pytest conformance/dim_signing/ -k optional

# 单条向量重签调试
pytest conformance/dim_signing/test_dim_signing.py::test_resign_each_vector_under_each_algorithm \
    -k 'pos-cbor-ed25519::ES256'
```

测试套件**自动发现** `vectors/` 下所有含 `expected.json` 的子目录，所以新增测试向量无需修改本目录。

## 6. 与协议正本的回链

| 本目录验证项 | 协议正本锚点 |
| --- | --- |
| `signature.alg ∈ {Ed25519, ES256, ML-DSA-65}` | design.md §6.1 / `schemas/fap-1.0.cddl` `signature-bundle.alg` enum |
| `H(Det-CBOR(Envelope_without_signature))` | design.md §6.3 / Property P16.1 |
| 协商「最强共同算法」 | design.md §6.1 协商规则 / Requirement 8.1 子句 2 |
| 无共同算法 → `E_PROTOCOL` | design.md §EH.1 / §5.4 错误码 1099 / Requirement 8.1 子句 4 |
| ML-DSA-65 OPTIONAL，缺失不阻塞 BOOTSTRAP | Requirement 8.2 子句 3 |

## 7. Reference 实现免责

本目录直接消费 `vectors/` 与 `schemas/`，本身**不构成协议本体**。在跨实现合规（task 5.6）阶段，TS / Rust reference 实现接入后，本目录将作为「Python reference 路径」并入跨实现矩阵。
