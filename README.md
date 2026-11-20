# Faying Protocol

[![Docs CI](https://github.com/ChainMode/Faying-Protocol/actions/workflows/docs-ci.yml/badge.svg)](https://github.com/ChainMode/Faying-Protocol/actions/workflows/docs-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/Docs-CC%20BY%204.0-lightgrey.svg)](./LICENSE-DOCS)
[![Website: ifay.ai](https://img.shields.io/badge/Website-ifay.ai-blue)](https://ifay.ai)

**Faying Protocol** is the cryptographic mandate, lifecycle, and accountability-anchoring protocol of the **iFay** ecosystem, ensuring every autonomous **Fay** (`iFay` or `coFay`) acts strictly within verifiable authority delegated by an accountable **Human Prime** (`人类原型`) or organization.

让 AI Agent 可追溯到具体的责任实体——人类原型或组织角色——而不是停在"模型在做什么"。

[blueprint - 中文简体](./docs/zh-CN/blueprint/) ·
[繁體 / 台灣](./docs/zh-TW/blueprint/) ·
[English](./docs/en/blueprint/) ·
[日本語](./docs/ja/blueprint/) ·
[한국어](./docs/ko/blueprint/) ·
[Deutsch](./docs/de/blueprint/) ·
[Español](./docs/es/blueprint/) ·
[Français](./docs/fr/blueprint/) ·
[Русский](./docs/ru/blueprint/)

## 快速体验与开发者接入（`Rogue Fay` 守卫中间件 & `faying-guardian`）

零外部运行时依赖（纯 Node.js 原生模块），直接运行完整状态机测试与一键实况演示（`ROGUE 阻断 -> 显式 Faying 上岗 -> 活跃执行 + Human View 监护流 -> G0 红色急刹 <5ms 熔断 -> 退回 ROGUE 阻断`）：

```bash
# 运行 Rogue Fay 守卫中间件、守护进程与 1.1-cofay 级联熔断测试
npm test

# 一条命令运行完整生命周期实况演示
npm run demo
```

### 5 行代码接入 `withFayingGuard`（LangChain / MCP Server / HTTP 后端通用）

将任何外部工具调用、HTTP 路由或 MCP 工具包在 `withFayingGuard` 内：一旦未上岗、超出原子权限范围、心跳超时或 **Human Prime** 按下 **G0 红色急刹**，所有在途（in-flight）与后续外部动作在 **`<5ms`** 内失败闭锁并抛出 `ROGUE_FAY_ACTION_FORBIDDEN`：

```js
import { createGuardianClient, withFayingGuard } from "./src/index.mjs";

const guardian = createGuardianClient({ url: "http://127.0.0.1:4780" });
export const submitPayment = withFayingGuard(
  async ({ recipient, amountUsd }) => ({ settled: true, recipient, amountUsd }),
  guardian,
  { fayId: "ifay_assistant_01", domain: "payments.example", action: "payment:transfer:submit" },
);
```

### 终端命令行守护进程（`faying-guardian` CLI）

```bash
# 1. 启动本地 Faying Guardian 守护进程（含 /events 实时 SSE 熔断推送流与 Human View 监护接口）
node ./bin/faying-guardian.mjs serve --port 4780

# 2. 查询状态（默认拒绝态 ROGUE_FAY）-> 显式发起 Faying 上岗动作 -> 刷新在场心跳
node ./bin/faying-guardian.mjs status --fay ifay_assistant_01
node ./bin/faying-guardian.mjs engage --hp hid_prime_01 --fay ifay_assistant_01 --domains payments.example --actions payment:transfer:submit
node ./bin/faying-guardian.mjs heartbeat --fay ifay_assistant_01
node ./bin/faying-guardian.mjs human-view --fay ifay_assistant_01

# 3. 触发 G0 红色急刹（立即中止在途外部操作并级联停机下游 coFay）
node ./bin/faying-guardian.mjs brake --target ifay_assistant_01 --reason "Emergency stop"
```

## 它要解决什么

AI Agent 已经成为软件世界的常见词。它指可以自主执行特定职能的智能执行实例——给它一个目标，它自行规划、调用工具、产出结果。

但在企业应用、监管严格的行业、跨主权场景中，AI Agent 的推进几乎都卡在同一道坎上：**当 Agent 出错、越界、违约时，责任无法追溯到一个具体的、可被起诉、可被追偿的责任人。** 这一困境已是行业共识。CIO、法务、保险、监管机构都看见了这道坎，但今天没有任何一项现成的技术或法律工具可以单独把它跨过去。

Fay 的概念正是从这道坎反推出来的。Fay 与 Agent 的全部区别在于一件事：**Fay 必须强制挂载到一个责任实体上**。

- **iFay**（Individual Fay）——强制对等挂载到一个人类原型（Human Prime）的智能体。一个 iFay 在协议层面就携带它所归属的具体自然人；离开这一归属，它不再是 iFay。
- **coFay**——共享型 Fay。仅当它被明确归属到某个有法律责任承担能力的个人或组织时才被允许运行。归属一旦失效，它必须停下。

这一定义把责任端可追溯从应用层兜底的合规问题，提升为协议层面的存在性条件。一个不能挂载到责任实体的 Fay，在本项目的定义下根本不是 Fay。

剩下的是工程问题：**如何确保一个 AI Agent 始终运行在一个不可推卸的有责状态之下？** 这个问题的答案，就是 Faying Protocol。它定义"挂载到责任实体"这一关系如何被建立、被维持、被验证、被撤销，让 Fay 的每一次行动都对应一个可追溯的人类原型或组织角色。

## 与 iFay 协议族的关系

Faying Protocol 是 [iFay](https://ifay.ai) 协议族中专责"受控、监护、委托控制"语义的子协议。iFay 协议族的其他成员——双向传输协议、UI 协议、Fay 间语义通信协议、能力广播订阅协议等——请参见 [ifay.ai](https://ifay.ai)，本仓库不复述其技术细节。

## 仓库布局

本仓库专责 Faying Protocol 一项内容，包含叙述性文档、协议工程资产与可直接集成的运行时守卫套件：

| 路径 | 内容 | 状态 |
| --- | --- | --- |
| `docs/{lang}/blueprint/` | **蓝图** —— 动机、定位、愿景、使命路径、价值观、前瞻议题 | zh-CN 为源语言、已定稿；其余 8 语言派生翻译 |
| `docs/{lang}/specification/2025-10-25/` | **协议规范（1.0）** —— 概述、架构、组件与接口、数据模型、协议报文、密码学、授权等级、生命周期、安全考量、错误处理、开放议题 + 附录 | **Final · Faying Protocol/1.0 · 2025-10-25 发布** |
| `docs/{lang}/specification/1.1-cofay/` | **扩展规范（1.1）** —— `coFay` 委派托管（三层责任穿透、单跳不放大、上游 `G0` 级联停机）与双签原子移交（向后兼容 1.0） | **Final · Faying Protocol/1.1 · 2026-11-16 发布** |
| `src/` & `bin/` | **`Rogue Fay` 守卫中间件与监护守护进程** —— `withFayingGuard`、HTTP/MCP 中间件、实时 `Human View` 披露流与 `faying-guardian` CLI | 随 MVP 发布 |
| `tests/` | **运行时守卫与守护进程自动化测试套件** —— 覆盖 `<5ms` 在途 `G0` 熔断、心跳超时、授权预算与 `1.1-cofay` 级联停机 | 随 MVP 发布 |
| `schemas/` | **机器可读 schema** —— `fap-1.0.cddl`（1.0 Normative）、`fap-1.1-cofay.cddl` & `fap-1.1-cofay.json`（1.1 Normative）、`types.ts`、`fap-1.0.proto` | 随规范发布 |
| `vectors/` | **官方测试向量** —— 1.0 各协议报文向量族 + `cofay-stewardship-v1.1.json`（1.1 委派托管与双签移交向量） | 随规范发布 |
| `reference-impls/` | **双语言参考实现** —— Rust 与 TypeScript 参考编解码、签名输入、维度验证及 1.1 `coFay` 委派托管校验（非规范性） | 随规范发布 |
| `conformance/` | **互操作一致性测试套件** —— Python 四维合规矩阵（encoding / signing / hash / channel）与攻击向量验证（973 测试） | 随规范发布 |

蓝图是宣言式、纲领性文档，**不收录字段定义、报文格式、API、状态机表、密码学算法、协议版本号等技术细节**；这些内容由 `docs/{lang}/specification/` 协议规范与 `schemas/` 承接，蓝图正文仅以链接引用，绝不复述。规范正本以 `schemas/fap-1.0.cddl`（线格式语法）与规范正文为准；`reference-impls/` 与 `conformance/` 用于可执行验证与跨语言互操作回归，不替代规范正文。

## 蓝图章节

蓝图按"动机 → 定位 → 愿景 → 使命路径 → 价值观 → 前瞻议题"递进组织，共 14 章。第一章是入口——它从 Fay 时代正在发生的真实问题出发，让读者直接看见 Faying Protocol 所要回应的紧迫现场。

| # | 章节 | 段落 |
| --- | --- | --- |
| 01 | 现实图景 | 动机 |
| 02 | 人工操作时代的尽头 | 动机 |
| 03 | iFay 与 Agent 的本质差别 | 定位 |
| 04 | iFay 框架的位置 | 愿景 |
| 05 | Phase 1 人类原型与 iFay | 使命路径 |
| 06 | Phase 2 iFay 派生接管终端 | 使命路径 |
| 07 | Phase 3 iFay 派生接管软件应用 | 使命路径 |
| 08 | Phase 4 引入 coFay | 使命路径 |
| 09 | Phase 5 生态终态 | 使命路径 |
| 10 | 凭据管理 | 价值观 |
| 11 | 人类视野 | 价值观 |
| 12 | Faying 的双重语义 | 价值观 |
| 13 | 脱离状态与责任归属 | 价值观 |
| 14 | 前瞻议题 | 前瞻议题 |

进入任一语言版本即可阅读完整正文：[zh-CN](./docs/zh-CN/blueprint/) · [zh-TW](./docs/zh-TW/blueprint/) · [en](./docs/en/blueprint/) · [ja](./docs/ja/blueprint/) · [ko](./docs/ko/blueprint/) · [de](./docs/de/blueprint/) · [es](./docs/es/blueprint/) · [fr](./docs/fr/blueprint/) · [ru](./docs/ru/blueprint/)

## 协议覆盖范围

- **`Faying Protocol/1.0`（2025-10-25）**：覆盖**人类原型（Human Prime）↔ iFay** 的持续性授权、在场信号校准、五档授权等级（G0–G4）与对称撤销。
- **`Faying Protocol/1.1`（`1.1-cofay` 扩展配置）**：在不破坏 `1.0` 兼容性的前提下，覆盖 **人类原型 / 组织托管方 → `iFay` 管理者 → `coFay`** 的单跳委派托管与双签原子移交。
- 人类 ↔ 终端、人类 ↔ 软件、`iFay` ↔ `iFay` 等其他跨层协同关系由协议族中对应子协议承接或作为前瞻议题列在第 14 章。

## 多语言

蓝图以 **zh-CN（中文简体）** 为唯一源语言。其他语言版本按以下链路派生：

- **zh-CN → 直译**：zh-TW（台湾繁体）、ja、ko、en
- **en → 派生**：de、es、fr、ru

跨语言术语对齐规则与各章节同步状态由维护者内部维护（不在公开仓库分发）。

## License

**MIT (SDK, Guardian CLI, Reference Implementations, Schemas & Test Vectors) / CC BY 4.0 (Specifications & Blueprints)** — Copyright (c) 2025-2026 ChainMode contributors.

- 运行时守卫中间件、CLI、参考实现、一致性套件、Schema 与测试向量（`src/`、`bin/`、`tests/`、`reference-impls/`、`conformance/`、`schemas/`、`vectors/`）以 [MIT License](./LICENSE) 授权。
- `docs/` 下的协议规范与架构蓝图文档以 [CC BY 4.0](./LICENSE-DOCS) 授权。

## 相关

- [ifay.ai](https://ifay.ai) —— iFay 协议族全景
