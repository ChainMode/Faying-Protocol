# Faying Protocol

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

本仓库专责 Faying Protocol 一项内容，分三类资产：

| 路径 | 内容 | 状态 |
| --- | --- | --- |
| `docs/{lang}/blueprint/` | **蓝图** —— 动机、定位、愿景、使命路径、价值观、前瞻议题 | zh-CN 已定稿；其他语言陆续翻译 |
| `docs/{lang}/specification/` | **协议规范** —— 字段、消息、状态机、API、版本号 | 后续独立 spec 承接 |
| `schema/` | **schema** —— Faying Protocol 的字段与结构定义 | 后续独立 spec 承接 |

蓝图是宣言式、纲领性文档，**不收录字段定义、消息格式、API、状态机表、加密算法、协议版本号等技术细节**。这些内容由协议规范文档与 schema 承接，蓝图正文中以链接形式引用，绝不在蓝图正文中复述。

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

## 本期范围

本期 Faying Protocol 仅覆盖**人类原型 ↔ iFay**一类受控关系。其他 Faying 关系——人类 ↔ 终端、人类 ↔ 软件、iFay ↔ coFay、iFay ↔ iFay 等——作为前瞻议题列在第 14 章，不在本期协议设计范围内。

## 多语言

蓝图以 **zh-CN（中文简体）** 为唯一源语言。其他语言版本按以下链路派生：

- **zh-CN → 直译**：zh-TW（台湾繁体）、ja、ko、en
- **en → 派生**：de、es、fr、ru

跨语言术语对齐规则与各章节同步状态，统一在 [`docs/zh-CN/blueprint/glossary.md`](./docs/zh-CN/blueprint/glossary.md) 与 [`docs/zh-CN/blueprint/sync-status.yaml`](./docs/zh-CN/blueprint/sync-status.yaml) 中维护。

## 许可

待定。

## 相关

- [ifay.ai](https://ifay.ai) —— iFay 协议族全景
