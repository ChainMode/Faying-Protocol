# dim_hash — 哈希算法维度合规测试

> **Task anchor** — 实现 [`tasks.md` 任务 5.4](../../docs/zh-CN/specification/2025-10-25/README.md) 「哈希维度合规测试（SHA-256 / BLAKE3）」。
> **Requirements anchor** — [Requirement 8.1（算法套件可协商）](../../docs/zh-CN/specification/2025-10-25/README.md) / [Requirement 10.2（Deterministic CBOR 签名输入规范化）](../../docs/zh-CN/specification/2025-10-25/README.md) / [Requirement 10.3（跨实现兼容矩阵）](../../docs/zh-CN/specification/2025-10-25/README.md)。
> **Design anchor** — [design.md §6.1 算法套件](../../docs/zh-CN/specification/2025-10-25/README.md) / [design.md §6.3 签名格式](../../docs/zh-CN/specification/2025-10-25/README.md)。

## 1. 目的

本目录是 5 维互操作矩阵中 **hash 维度** 的可执行驱动器。它对协议正本枚举的两种哈希逐一执行 §6.3 的签名输入构造：

| 哈希 | 来源 | 状态 |
| --- | --- | --- |
| `SHA-256` | design.md §6.1 默认 | MUST 支持（FIPS 180-4） |
| `BLAKE3` | design.md §6.1 备选 | MUST 支持（task 5.4 验收强制） |

> `SHA3-256` 在 design.md §6.1 作为 PQC 协商位保留，但**不在 task 5.4 范围内**——该算法的接入由 task 5.6 跨实现兼容轮次承担。

任务 5.4 的两条验收：

- **2/2 哈希跑通**：每条 `vectors/` 里的合规向量都能被两种哈希各自计算签名输入摘要，输出长度合规（均为 32 字节）。
- **签名输入构造与 §6.3 完全一致**：
  - 喂给哈希函数的字节串 `Deterministic-CBOR(Envelope_without_signature)` 与哈希算法**无关**——交换 SHA-256 / BLAKE3 不得扰动输入字节。
  - 当向量在 `expected.json` 提供 SHA-256 参考摘要时（如 `vectors/encoding-equivalence/01-bootstrap/expected.json.signature_input.hash_hex`），本驱动的计算结果**必须逐字节一致**。

## 2. 模块组成

| 文件 | 职责 |
| --- | --- |
| `algorithms.py` | 两种哈希的统一 `compute_hash` API；输出长度 32 字节硬约束；BLAKE3 后端缺失时显式抛 `HashUnavailableError`（"2/2 跑通"是硬验收，不能静默退化） |
| `negotiation.py` | Requirement 8.1 协商规则的可执行实现；强度顺序 `BLAKE3 > SHA-256`，无交集时抛 `HashNegotiationError`（即 `E_PROTOCOL` / 1099） |
| `signing_input.py` | 加载向量 `{request,signal,mandate,message,...}.{cbor,json}`，剥离外层签名，按 design.md §6.3 计算 `Deterministic-CBOR(Envelope_without_signature)` 后做哈希；并在向量 `expected.json` 携带 SHA-256 参考摘要时做一致性交叉校验 |
| `driver.py` | CLI 驱动器：`python -m conformance.dim_hash.driver`；text/json 双格式输出；非零退出码即合规失败 |
| `test_dim_hash.py` | pytest 套件：A 类「2/2 哈希覆盖」+ B 类「签名输入构造与 §6.3 一致」+ C 类「哈希套件协商」+ FIPS / BLAKE3 KAT 自检 |

## 3. 协商强度顺序

```
NEGOTIATION_ORDER = ("BLAKE3", "SHA-256")
```

- **BLAKE3 强于 SHA-256** 的结构性原因（见 `negotiation.py` 文档串）：
  - Merkle 树内部结构对长度扩展攻击（length extension）天然免疫，而 SHA-256 易受影响。
  - 默认 256-bit 输出，与 SHA-256 一致；并发性能与软件性能均更高（与协议合规无关，但解释了 design.md §6.1 把它列为「备选」的工程动机）。
- 协商函数返回 `client ∩ server` 中按上表排序的首个算法；交集为空时抛 `HashNegotiationError`，错误码恒为 `E_PROTOCOL`（1099）。
- **不强制 BLAKE3 baseline**：design.md §6.1 把 SHA-256 标为「默认」，所有现有 `vectors/` 都用 SHA-256 哈希；只要双方都至少支持 SHA-256，BOOTSTRAP 就不得因 BLAKE3 缺失而拒绝。

## 4. 签名输入构造（§6.3 等价复刻）

```
signing-input(envelope, h) = h( Deterministic-CBOR(envelope_without_signature) )
```

本目录把这个表达式拆成两半，分别对应两条验收：

| 阶段 | 函数 | 验收对应 |
| --- | --- | --- |
| 内层：去掉外层 `signature` 并按 RFC 8949 §4.2.1 做 Deterministic CBOR 编码 | `compute_signing_input(envelope)` | 「签名输入构造与 §6.3 完全一致」——这一阶段与哈希算法无关，是 P16.1 的字节级前置条件 |
| 外层：套上 `H = SHA-256 / BLAKE3` | `compute_hash(alg, signing_input)` | 「2/2 哈希跑通」——每条向量在两个哈希列下都得到合规摘要 |

> **设计选择**：本驱动**只处理外层签名**，不递归处理嵌套子签名（如 response 报文里 `claims.mandate.signature`）。这与 [`conformance/dim_signing/resign.py`](../dim_signing/resign.py) 完全一致——子签名是外层签名的**输入**，必须保留逐字节不变；§6.3 锚点也是这么定义的。

## 5. BLAKE3 依赖说明

> **关键边界** — 本目录在 BLAKE3 不可用时**主动抛错**，不静默跳过。

任务 5.4 的验收口径是 "2/2 跑通"。如果 `blake3` PyPI 包缺失，任何"BLAKE3 列被静默 skip"的实现都会让验收门崩溃为 1/2。因此 `algorithms.py` 在懒加载 BLAKE3 时若 ImportError，会抛 `HashUnavailableError`（继承自 `ImportError`），并提供清晰的安装指引：

```bash
pip install blake3
```

`blake3` 包是 BLAKE3 团队官方维护的 Python 绑定（基于其 Rust 参考实现），与 task 5.6 的 reference 实现路径一致。

## 6. 运行

```bash
# 全量执行 dim_hash（pytest 守门）
pytest conformance/dim_hash/

# 仅看覆盖矩阵
pytest conformance/dim_hash/ -k "test_two_of_two_hashes_succeed_on_every_vector"

# 仅看签名输入构造一致性
pytest conformance/dim_hash/ -k "signing_input_invariant or sha256_matches_reference"

# CLI 驱动器（更适合 CI 报表）
python -m conformance.dim_hash.driver
python -m conformance.dim_hash.driver --format json
python -m conformance.dim_hash.driver --filter encoding-equivalence -v
```

测试套件**自动发现** `vectors/` 下所有含 `expected.json` 与已知名信封文件的子目录，新增向量无需修改本目录。

## 7. 与协议正本的回链

| 本目录验证项 | 协议正本锚点 |
| --- | --- |
| `signing-input = H(Det-CBOR(envelope_without_signature))` | design.md §6.3 / Property P16.1 |
| `H ∈ {SHA-256, BLAKE3}` | design.md §6.1 算法套件表 / Requirement 8.1 子句 1–3 |
| 协商「最强共同哈希」 | design.md §6.1 协商规则 / Requirement 8.1 子句 2 |
| 无共同哈希 → `E_PROTOCOL` | design.md §EH.1 / §5.4 错误码 1099 / Requirement 8.1 子句 4 |
| `expected.json.signature_input.hash_hex` 一致性 | task 3.7 跨编码向量 / Requirement 10.2 子句 4 |
| Deterministic CBOR 输入字节与哈希算法无关 | Requirement 10.2 子句 4 / design.md §5.1 |

## 8. 与 dim_encoding / dim_signing 的关系

| 维度 | 锁定的变量 | 验证的变量 |
| --- | --- | --- |
| `dim_encoding`（task 5.2） | 签名算法、哈希算法 | 编码（CBOR ↔ JSON）下的字段语义等价、签名输入字节身份 |
| `dim_signing`（task 5.3） | 编码、哈希 | 签名算法（Ed25519 / ES256 / ML-DSA-65）下的重签 + 验签 |
| `dim_hash`（**本目录**） | 编码、签名算法 | **哈希算法（SHA-256 / BLAKE3）下签名输入摘要的等价正确性** |
| `dim_channel`（task 5.5） | 编码、签名、哈希 | 信道（TLS-only / mTLS）下 RFC 9266 Channel Binding |

三者共享同一份 `vectors/` 与 `schemas/`；矩阵的笛卡尔积由 `conformance/runner.py` 统一驱动。

## 9. Reference 实现免责

本目录直接消费 `vectors/` 与 `schemas/`，本身**不构成协议本体**。在跨实现合规（task 5.6）阶段，TS / Rust reference 实现接入后，本目录将作为「Python reference 路径」并入跨实现矩阵；那时 BLAKE3 列会与 reference 实现产出的 BLAKE3 摘要交叉校验，闭合"无 BLAKE3 ground-truth 摘要"的当前缺口。
