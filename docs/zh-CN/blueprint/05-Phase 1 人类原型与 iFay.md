# Phase 1：人类原型 ↔ iFay

Phase 1 是 Faying Protocol 的第一块基石：把"人类原型 ↔ iFay"这一最基础的监护关系建立起来，并使其能在任意终端、任意应用中被忠实表达与持续维持。

这一阶段不追求覆盖广度，追求深度自洽：在 Phase 1 落地之后，任意一个 iFay，无论运行在哪台设备、哪个操作系统、哪个应用容器里，都能够清楚地回答两个问题——"我此刻是否处于 Faying State？""如果是，我归谁负责？"

这是整个 Faying Protocol 演进的最小可用形态。后续 Phase 2 至 Phase 5 都建立在 Phase 1 之上：如果 Phase 1 不成立，后续的扩展就没有立足点。

## 覆盖范围

Phase 1 仅覆盖一类关系：

> **人类原型 ↔ iFay**

关系的责任端是某个具体的人类原型（Human Prime）；关系的另一端是该人类原型的某个 iFay；关系的内容是 iFay 在该人类原型的监护下展开数字行动。

Phase 1 不直接覆盖"人类原型 ↔ 终端"或"人类原型 ↔ 软件应用"。当一架无人机、一个家庭机器人、一个企业流程应用进入 Faying 关系时，Phase 1 要求的表达方式是：

> **该终端 / 该软件应用通过对应人类原型的 iFay 进入 Faying State**，而不是与人类原型直接建立 Faying 关系。

这一表达方式是有意为之。iFay 是 Faying Protocol 在 Phase 1 中唯一被信任承接监护契约的实体形态。把"无人机 ↔ Jack"理解为"无人机通过 Jack 的 iFay 进入受控状态"，能让 Phase 1 的责任链条始终保持简洁清晰，避免提前引入"多端直接 Faying"的复杂度。

## 三个核心议题

在覆盖范围被严格限定为"人类原型 ↔ iFay"的前提下，Phase 1 必须解决三个核心议题。

**建立**——Faying Action 如何由人类原型显式发起、被见证、被记录，并将 iFay 推入 Faying State。这一议题在第十二章（Faying 双重语义）展开。

**维持**——Faying State 在 iFay 整个工作生命周期中如何被持续校准。既要保证它在每一时刻仍然成立，也要保证它一旦不再成立就立即退出。这一议题对应第十三章（Rogue Fay 与责任归属）的九项触发条件。

**退出**——Faying State 退出后，iFay 如何转入 Rogue Fay 并仅保留 A/B/C 三个维度的最小行为集，禁止 D 维度的全部对外行动。这一议题对应第十三章的 A/B/C/D 四维度规则。

这三项议题不是 Phase 1 的"高级特性"，是 Phase 1 的全部内容。在它们被自洽落地之前，Phase 1 不被视为完成。Phase 1 的范围被故意收得很小，是为了让接下来的 Phase 2 至 Phase 5 在一片已经成立的契约土壤上展开扩展，而不是同时与基础形态斗争。

![Phase 1 概念图：人类原型与 iFay 的最小受控关系](./illustration/phase1-concept.png)

![Phase 1 架构图：iFay 在 Faying State 下的运作骨架](./illustration/phase1-architecture.png)
