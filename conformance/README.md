# Faying Protocol/1.0 — 互操作合规测试套件（Conformance Test Suite）

> **Normative anchor** — 本目录是 [requirements.md §10.3 跨实现兼容矩阵](../docs/zh-CN/specification/2025-10-25/README.md) 的实现，亦即 [design.md §TS.4「互操作测试矩阵」](../docs/zh-CN/specification/2025-10-25/README.md) 的可执行落点。任何"协议合规"的声明，最终都要体现为本套件中某一组合的 PASS。

## 1. 用途

Requirement 10.3 要求 Faying_Protocol_System 在协议合规测试中覆盖 design.md §TS.4 列出的 5 维矩阵：

| 维度 | 取值 | 来源 |
| --- | --- | --- |
| encoding | `cbor` / `json` | Requirement 10.1，design.md §5.1 |
| signing-alg | `ed25519` / `ecdsa-p256` / `ml-dsa-65` | Requirement 8.1，design.md §6 |
| hash | `sha-256` / `blake3` | Requirement 8.1，design.md §6.3 |
| channel | `tls-only` / `mtls`（含 RFC 9266 Channel Binding） | Requirement 9.2，design.md §9.3 |
| impl-language | 至少 1 种（task 5.6 扩到 ≥ 2，建议 TypeScript + Rust） | Requirement 10.3，design.md §TS.4 |

笛卡尔积下限为 `2 × 3 × 2 × 2 × 1 = 24` 组合，等于 Requirement 10.3 的强制底线。

## 2. 目录结构

```
conformance/
├── README.md          ← 本文件
├── matrix.yaml        ← 5 维矩阵的机器可读声明
├── runner.py          ← 笛卡尔积驱动器（task 5.1，本任务）
├── dim_encoding/      ← task 5.2 交付：CBOR ↔ JSON 切换（已实现）
├── dim_signing/       ← task 5.3 交付：Ed25519 / ECDSA-P256 / ML-DSA-65
├── dim_hash/          ← task 5.4 交付：SHA-256 / BLAKE3
├── dim_channel/       ← task 5.5 交付：TLS-only / mTLS（含 RFC 9266）
├── cross-impl/        ← task 5.6 交付：跨 reference 实现兼容矩阵
└── attacks/           ← task 6.x 交付：攻击模拟（重放 / 劫持 / 钓鱼 / 脱钩）
```

`dim_*/`、`cross-impl/`、`attacks/` 目录由后续任务创建；本任务（5.1）只交付前三项（README / runner / matrix）。

## 3. 与 `vectors/` 与 `schemas/` 的关系

本套件不重新定义协议数据，而是消费仓库根的两份权威产物：

- [`vectors/`](../vectors/) — 由 task 3.x 交付的官方测试向量（BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / 错误码 / 跨编码等）。每条向量自带 `expected.json`，是合规测试的 ground truth。
- [`schemas/`](../schemas/) — 由 task 2.x 交付的权威 schema：
  - [`schemas/fap-1.0.cddl`](../schemas/fap-1.0.cddl)（**Normative**）
  - [`schemas/types.ts`](../schemas/types.ts)（人读视图，Not Normative）
  - [`schemas/fap-1.0.proto`](../schemas/fap-1.0.proto)（备选 gRPC 绑定，Not Normative）

`runner.py` 在 `--dry-run` 阶段就把 `vectors/` 与 `schemas/` 的相对路径打印出来，使得后续 dim_* 驱动的接入点对工具链一目了然。

## 4. 运行方式

### 4.1 列出全部组合（task 5.1 验收）

```bash
python conformance/runner.py --dry-run
```

期望输出至少 24 行组合 + `Total combinations: 24`，且 `Acceptance (Requirement 10.3, ≥ 24): MET`。

JSON 格式（用于喂给后续 CI/驱动器）：

```bash
python conformance/runner.py --dry-run --format json
```

### 4.2 执行实际合规测试

```bash
python conformance/runner.py --run                  # 跑当前已 wire 的所有维度
python conformance/runner.py --run --dim encoding   # 仅跑编码维度（task 5.2）
python conformance/runner.py --run --format json    # JSON 格式输出
python conformance/runner.py --run -v               # 显示所有 INFO 级别 finding
```

`--run` 当前已对接 task 5.2（编码维度，[`dim_encoding/`](./dim_encoding/README.md)）。task 5.3–5.6 的驱动器到位后会作为新的 `--dim` 选项追加注册；矩阵笛卡尔积本身不会膨胀，只是每一组合的 PASS 判据补全更多维度。

## 5. Reference 实现免责声明

本目录可能引用 `reference-impls/typescript/` 与 `reference-impls/rust/`（task 5.6 交付）。两份实现仅服务于本合规套件，**不构成协议本体**，且必须在文件头标注 `Reference Implementation, Not Normative`。

## 6. 协议正本与本套件的回链

| 本套件 | 协议正本锚点 | 回链关系 |
| --- | --- | --- |
| `matrix.yaml` 5 维 | design.md §TS.4 | 维度名称、维度取值需逐一同步 |
| `runner.py --dry-run` ≥ 24 | requirements.md §10.3 验收 | 组合数下限来自 EARS 子句 1 |
| `dim_encoding/` | requirements.md §10.1 / §10.2 | CBOR ↔ JSON 等价 + Deterministic CBOR |
| `dim_signing/` | requirements.md §8.1 / §8.2 | 算法套件协商 + PQC 演进位 |
| `dim_channel/` | requirements.md §9.2 | RFC 9266 Channel Binding |
| `cross-impl/` | requirements.md §10.3 第 3 条 | 跨实现兼容性 |

矩阵任何取值的增删都必须先回到 design.md §TS.4 与 requirements.md §10.3 同步，再回到 `matrix.yaml`，最后再回到 `dim_*/` 驱动器；禁止反向。
