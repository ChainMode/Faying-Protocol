# iFay 框架的位置

本章只回答两个问题：iFay 框架大致长什么样？Faying Protocol 在其中处于什么位置？

iFay 框架本身覆盖面广、组件众多，每一处稍微展开就会走入字段、协议、消息格式等技术细节。本仓库三类资产——蓝图、协议规范、schema——只承载 Faying Protocol 一项内容。iFay 协议族中除 Faying Protocol 之外的所有成员，统一以链接到 [ifay.ai](https://ifay.ai) 的方式引用，本仓库不复述、不重写、不衍生。

## iFay 框架的轮廓

按 [ifay.ai](https://ifay.ai) 的整体设计，iFay 框架可以被粗略地理解为四层结构。

**实体层**包含两类受协议约束的智慧实体。**iFay**（Individual Fay）强制对等挂载到一个具体的人类原型——离开这一归属，它不再是 iFay。**coFay** 是共享型 Fay，仅当它被明确归属到某个有法律责任承担能力的个人或组织时才被允许运行。无论 iFay 还是 coFay，本蓝图所讨论的 Faying Protocol 都对它们一视同仁地约束：归属一旦失效，Fay 必须停下。

**核心组件**包含每个 Fay 实体内部不可分割的几个部件。**FayID** 是 Fay 的统一唯一身份标识，是其进入任何监护关系的身份基础。**Ego** 是与特定个体或角色 profile 对齐的基线范式，约束 Fay 在价值取向、兴趣偏好、习惯、认知与技能边界、权限边界、工作风格等维度上的自主行为空间。Ego 不是大型 AGI 模型，是一份"人格化的边界"。**Runtime** 是 Fay 的虚拟运行时，使 iFay 与 coFay 能在不同终端、操作系统、嵌入式应用场景中兼容运行。FayID 与 Ego 是 Faying Protocol 能够生效的两个前置条件——前者承载身份归属，后者承载行为边界。

**协议族**包含 iFay 与世界连接、感知、协作的一系列协议。除本蓝图主题 **Faying Protocol** 外，至少还包括：终端控制相关的双向传输协议、面向人类用户界面的 UI 友好协议、iFay 与 coFay 之间去 UI 翻译层的语义通信协议、云端能力的广播与订阅协议，以及未来可能新增的其他成员。这些协议族成员的技术细节请前往 [ifay.ai](https://ifay.ai)，本仓库不收录。

**价值结构**对应一种新的劳动结构与价值分配模型。这一层包括人类劳动退出、知识扁平化、普遍生存保障、新价值创造、新社会分层等系统性变化，并以 MeriToken 等机制作为价值度量的承接。这是 iFay 框架的远景背景板，不直接落到 Faying Protocol 协议规范上，详见 [ifay.ai](https://ifay.ai)。

## Faying Protocol 在其中的位置

把上面四层放在一起，Faying Protocol 在 iFay 框架中的位置可以被这样精准锚定：

> **Faying Protocol 处于"实体层"与"核心组件"之上，是协议族里专责"受控、监护、委托控制"语义的子协议。它把"FayID 是否归属于某个人类原型"这一根本问题，转化为一组可被建立、维持、撤销的连接状态与动作。**

它不是 Fay 的能力定义，因此不规定 Fay 能做什么。它不是 Fay 的行为指南，因此不规定 Fay 应该如何做。它只回答一个问题：

> **此刻这个 Fay 的行动，归谁负责？**

正因如此，Faying Protocol 在 iFay 框架中既不属于"最炫目"的协议，也不是"最深厚"的协议，但它是最不可被略过的那一个。一旦它缺位，整个 iFay 框架立刻退化为一个普通的 Agent 生态，把第一章描述的责任真空带进社会。

## 本仓库与 iFay 框架的边界

```
                 +-------------------+
                 |   ifay.ai 全景    |
                 |  iFay 框架 4 层    |
                 +-------------------+
                          │
                          │  本仓库取其中一员展开
                          ▼
            +---------------------------+
            |   Faying Protocol 项目    |
            |   （即本仓库的全部资产）   |
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        蓝图          协议规范           schema
   docs/{lang}/    docs/{lang}/         schema/
    blueprint/    specification/       …（本期不交付）
   （即本 spec）  （后续独立 spec）
```

本仓库三类资产全部只承载 Faying Protocol 一项内容。任何 iFay 框架其他成员的深入展开，都不属于本仓库的范围，请直接访问 [ifay.ai](https://ifay.ai)。

![iFay 框架（alpha1）概览：Faying Protocol 居于受控关系契约层](./illustration/ifay-framework-alpha1.png)

![iFay 标题横幅](./illustration/ifay-title-banner.png)
