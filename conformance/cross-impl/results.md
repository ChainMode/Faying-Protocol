# Faying Protocol/1.0 — 跨实现兼容矩阵跑测结果（Cross-Implementation Conformance Matrix）

> **Reference Implementations, Not Normative.** 本目录记录两份独立 reference
> 实现（TypeScript + Rust）跑通 task 5.2–5.5 维度矩阵、并互相解析与验签的结果。
> 两份实现仅服务于互操作合规测试，**不构成协议本体**。协议正本锚点：
> [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl)（Normative wire schema）、
> [design.md §TS.4 互操作测试矩阵](../../docs/zh-CN/specification/2025-10-25/README.md)、
> [requirements.md §8.1 / §10.1 / §10.3](../../docs/zh-CN/specification/2025-10-25/README.md)。

## 1. 范围与方法（Requirements 8.1 / 10.1 / 10.3）

Requirement 10.3 要求互操作矩阵覆盖 design.md §TS.4 的五维，且**实现语言至少 2 种**：

| 维度 | 取值 | 本任务落点 |
| --- | --- | --- |
| 编码 encoding | CBOR / JSON | 每条 interop 报文同时产出 CBOR 与 JSON 两种编码 |
| 签名 signing-alg | Ed25519 / ECDSA-P256(ES256) / ML-DSA-65 | 两份实现各自跑通三算法 |
| 哈希 hash | SHA-256 / BLAKE3 | 两份实现各自跑通两哈希 |
| 信道 channel | TLS-only / mTLS（RFC 9266） | 两份实现各自跑通信道绑定 accept/reject 矩阵 |
| 实现语言 impl-language | **TypeScript + Rust（≥ 2）** | 本任务交付的两份 reference 实现 |

两份实现消费的是**同一套权威输入**：

- 官方测试向量 [`vectors/`](../../vectors/)（task 3.x，含 `encoding-equivalence/`、
  `bootstrap/`、`presence/`、`grade-switch/`、`delegate/`、`revoke/`、`errors/`、
  `endorsement/`、`faying-request/`、`disclosure/`、`disconnection/`）。
- 权威 CDDL schema [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl)。

**签名输入口径（design.md §6.3）** 两份实现严格一致：

```
signing_input_bytes = Deterministic-CBOR( Envelope_without_signature )   # RFC 8949 §4.2.1
signing_input_hash  = SHA-256( signing_input_bytes )                     # 跨编码恒等摘要
```

Ed25519 / ES256 在 `signing_input_bytes` 上直接签名（算法各自内置哈希），
`signing_input_hash` 是官方向量 `expected.json` 与本目录 interop manifest 记录的
跨编码恒等摘要。两份实现各自手写 RFC 8949 §4.2.1 确定性 CBOR 编码器（因为主流
CBOR 库默认不按编码后字节序排键），并以"逐字节复刻 Python `cbor2` 生成的官方
向量"为通过基线。

## 2. 参与实现（≥ 2 reference 实现）

| 实现 | 路径 | 关键依赖 | 运行入口 |
| --- | --- | --- | --- |
| TypeScript | [`reference-impls/typescript/`](../../reference-impls/typescript/) | Node.js（原生 TS 运行，无构建步骤）+ WebAuthn 概念 + `cbor-x`（独立解码交叉校验）+ `@noble/hashes`（BLAKE3） | `node src/cli.ts {dims,produce,verify}` |
| Rust | [`reference-impls/rust/`](../../reference-impls/rust/) | `ed25519-dalek` + `p256` + `ciborium` + `sha2` + `blake3` | `cargo run -- {dims,produce,verify}` |

两份实现 README 顶部均声明
`Reference Implementation, Not Normative — for conformance testing only.`

## 3. 如何复跑（Reproduce）

一键脚本（自动安装 TS 依赖、跑双实现维度矩阵、跑双向互操作）：

```bash
# 若 cargo 不在 PATH 上，先 export CARGO=~/.cargo/bin/cargo
conformance/cross-impl/run_cross_impl.sh
```

或分步运行：

```bash
# TypeScript（Node.js ≥ 22.6.0，无需构建）
cd reference-impls/typescript && npm install
node src/cli.ts dims
node src/cli.ts produce ../../conformance/cross-impl/_interop/ts

# Rust
cd reference-impls/rust
cargo run -- dims
cargo run -- verify ../../conformance/cross-impl/_interop/ts        # Rust 验 TS 产物
cargo run -- produce ../../conformance/cross-impl/_interop/rust
cd ../typescript && node src/cli.ts verify ../../conformance/cross-impl/_interop/rust  # TS 验 Rust 产物
```

## 4. 跑测结果（100% 通过）

### 4.1 各实现独立跑通 task 5.2–5.5 维度矩阵

两份实现对官方 `vectors/` 语料运行完整四维，逐维统计如下（数字为
`通过/总数`，两实现完全一致）：

| 维度 (task) | TypeScript | Rust | 说明 |
| --- | --- | --- | --- |
| encoding (5.2) | **5/5 PASS** | **5/5 PASS** | `encoding-equivalence/{01..05}` 的 CBOR/JSON 折叠到逐字节相同的 Det-CBOR 签名输入；SHA-256 匹配 `expected.json`；CBOR 信封签名验签通过。 |
| signing (5.3) | **117/117 PASS** | **117/117 PASS** | 113 条语料信封各自在 Ed25519/ES256/ML-DSA-65 下重签+验签通过、签名输入跨算法恒定；外加 4 条算法套件协商断言（最强择优 / 经典回退 / `ECDSA-P256` 别名 / 不相交集合 → `E_PROTOCOL`）。 |
| hash (5.4) | **113/113 PASS** | **113/113 PASS** | 每条语料的 §6.3 签名输入在 SHA-256 与 BLAKE3 下均产出 32 字节；SHA-256 与向量声明的参考摘要一致。 |
| channel (5.5) | **18/18 PASS** | **18/18 PASS** | `{BOOTSTRAP,DELEGATE,REVOKE} × {tls-only,mtls} × {present-correct,present-tampered,absent}` 信道绑定接受/拒绝矩阵；mTLS 缺/篡改绑定 → `E_ATTESTATION_INVALID(1007)`，TLS-only 夹带绑定 → `E_PROTOCOL(1099)`。 |

两实现的逐维计数完全相同（5 / 117 / 113 / 18），即"两份独立 reference 实现各自
跑通完整 task 5.2–5.5 维度矩阵"。

### 4.2 跨实现互操作（TS ↔ Rust 双向）

每个方向产出 7 条报文 × {CBOR, JSON} = **14 行**，覆盖
`BOOTSTRAP(Ed25519,mTLS) / BOOTSTRAP(ES256,TLS) / BOOTSTRAP(ML-DSA-65,TLS) /
PRESENCE(Ed25519) / GRADE_SWITCH(ES256,mTLS) / DELEGATE(Ed25519) /
REVOKE(Ed25519,mTLS)`，跨编码、跨算法、跨信道模式。验签方重新推导 §6.3 签名
输入、重算 SHA-256 与 BLAKE3 摘要、并重新验签，逐项与 manifest 比对。

| 方向 | 结果 |
| --- | --- |
| **TS 产报文 → Rust 解析并验签** | **14/14 PASS** |
| **Rust 产报文 → TS 解析并验签** | **14/14 PASS** |

> "TS 实现产出的报文必须能被 Rust 实现解析与验签，反向亦然" — 双向均 100% 通过。

### 4.3 汇总

```
=== Faying Protocol/1.0 cross-impl matrix (task 5.6) ===
[2/5] TypeScript dimension matrix  : encoding 5/5, signing 117/117, hash 113/113, channel 18/18 → PASS
[3/5] Rust dimension matrix        : encoding 5/5, signing 117/117, hash 113/113, channel 18/18 → PASS
[4/5] TS produces → Rust verifies  : 14/14 PASS
[5/5] Rust produces → TS verifies  : 14/14 PASS
=== cross-impl matrix complete: 100% PASS ===
```

**跨实现矩阵：100% 通过。**

## 5. 失败用例的定位与回填流程（验收要求）

验收要求："任一不通过用例必须能定位到向量或 schema，并回填 Issue 提交协议委员会。"
本套件按以下流程保证可定位、可回填：

1. **定位到具体用例。** 每个维度失败都打印
   `[<category>/<case>] <原因>`（如 `[bootstrap/pos-cbor-es256] SHA-256 … != reference …`）。
   interop 失败打印 `[<id>/<encoding>] <原因>`（如
   `[bootstrap-ed25519/json] BLAKE3 … != manifest …`）。`<category>/<case>` 直接
   对应 [`vectors/<category>/<case>/`](../../vectors/) 目录。
2. **判定根因属于"向量"还是"schema"。**
   - 若两实现对同一向量产出**相同**的非预期结果 → 多半是**向量**（`vectors/<…>/`
     的 `message.cbor` / `expected.json`）或 **schema**（`schemas/fap-1.0.cddl`
     字段定义）问题，而非实现 bug。
   - 若两实现产出**不同**结果 → 至少一方实现偏离了 §6.3 / CDDL；用
     `signing.input.det-cbor.hex` 与 `signature.input.hash.hex`（向量自带）做仲裁，
     哪一方的 Det-CBOR 字节与向量不符即为该实现的 bug。
   - 编码维度失败可进一步用 `vectors/encoding-equivalence/verify.py` 独立复核
     CBOR↔JSON 等价与签名输入恒等。
3. **回填 Issue 提交协议委员会。** 失败定位后，按下述模板向协议委员会提交 Issue：

   ```
   Title: [conformance 5.6] <category>/<case> 跨实现不一致
   Body:
     - 失败维度 / 方向: <encoding|signing|hash|channel | TS→Rust | Rust→TS>
     - 复现命令: conformance/cross-impl/run_cross_impl.sh
     - 期望（来自 expected.json / signature.input.hash.hex）: <hash/outcome>
     - TS 实测: <…>   Rust 实测: <…>
     - 初步根因归类: 向量(vectors/<…>) | schema(fap-1.0.cddl) | 实现
     - 关联条款: design.md §6.3 / §TS.4；requirements.md 8.1 / 10.1 / 10.3
   ```

   schema 层问题（CDDL）须先回到 design.md §4.2 同步后再改 `schemas/fap-1.0.cddl`
   （遵循 `conformance/README.md` §6 "禁止反向"的回链纪律）；向量层问题须重跑对应
   `vectors/<category>/_tools|_generate.py|generate.py` 重新生成并更新 `expected.json`。

> 当前跑测**无失败用例**；以上为流程预案，确保未来回归时可在分钟级定位到向量或 schema 并回填委员会。

## 6. 已知非规范点（Not Normative caveats）

- **ML-DSA-65 为确定性占位实现。** 两份 reference 实现与官方向量工具链、Python
  conformance 驱动一致，对 ML-DSA-65（FIPS 204）使用确定性占位签名（仅校验格式 +
  内嵌摘要），用于跑通算法协商与"PQC 作为 OPTIONAL 不阻断 BOOTSTRAP"的语义，
  **不是密码学实现**，禁止用于生产。真实 ML-DSA-65 落地后应替换占位并重跑本矩阵。
- **信道维度为协议层判定矩阵。** RFC 9266 channel binding 的 accept/reject 由
  RP 侧校验逻辑建模（与 `conformance/dim_channel` 同口径），不拉起真实 TLS 握手。
- 两份实现的确定性 CBOR 编码器均以"逐字节复刻 `vectors/encoding-equivalence` 的
  on-disk canonical bytes"为单元测试基线（`cargo test` /
  `node --test`），保证跨语言互操作建立在已验证的字节级一致之上。
