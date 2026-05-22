# iFay 框架的位置

本章只回答兩個問題：iFay 框架大致長什麼樣？Faying Protocol 在其中處於什麼位置？

iFay 框架本身覆蓋面廣、組件眾多，每一處稍微展開就會走入欄位、協定、訊息格式等技術細節。本倉庫三類資產——藍圖、協定規範、schema——只承載 Faying Protocol 一項內容。iFay 協定族中除 Faying Protocol 之外的所有成員，統一以連結到 [ifay.ai](https://ifay.ai) 的方式引用，本倉庫不複述、不重寫、不衍生。

## iFay 框架的輪廓

按 [ifay.ai](https://ifay.ai) 的整體設計，iFay 框架可以被粗略地理解為四層結構。

**實體層**包含兩類受協定約束的智慧實體。**iFay**（Individual Fay）強制對等掛載到一個具體的人類原型——離開這一歸屬，它不再是 iFay。**coFay** 是共享型 Fay，僅當它被明確歸屬到某個有法律責任承擔能力的個人或組織時才被允許運行。無論 iFay 還是 coFay，本藍圖所討論的 Faying Protocol 都對它們一視同仁地約束：歸屬一旦失效，Fay 必須停下。

**核心組件**包含每個 Fay 實體內部不可分割的幾個部件。**FayID** 是 Fay 的統一唯一身份標識，是其進入任何監護關係的身份基礎。**Ego** 是與特定個體或角色 profile 對齊的基線範式，約束 Fay 在價值取向、興趣偏好、習慣、認知與技能邊界、權限邊界、工作風格等維度上的自主行為空間。Ego 不是大型 AGI 模型，是一份「人格化的邊界」。**Runtime** 是 Fay 的虛擬運行時，使 iFay 與 coFay 能在不同終端、作業系統、嵌入式應用場景中相容運行。FayID 與 Ego 是 Faying Protocol 能夠生效的兩個前置條件——前者承載身份歸屬，後者承載行為邊界。

**協定族**包含 iFay 與世界連接、感知、協作的一系列協定。除本藍圖主題 **Faying Protocol** 外，至少還包括：終端控制相關的雙向傳輸協定、面向人類使用者介面的 UI 友善協定、iFay 與 coFay 之間去 UI 翻譯層的語義通訊協定、雲端能力的廣播與訂閱協定，以及未來可能新增的其他成員。這些協定族成員的技術細節請前往 [ifay.ai](https://ifay.ai)，本倉庫不收錄。

**價值結構**對應一種新的勞動結構與價值分配模型。這一層包括人類勞動退出、知識扁平化、普遍生存保障、新價值創造、新社會分層等系統性變化，並以 MeriToken 等機制作為價值度量的承接。這是 iFay 框架的遠景背景板，不直接落到 Faying Protocol 協定規範上，詳見 [ifay.ai](https://ifay.ai)。

## Faying Protocol 在其中的位置

把上面四層放在一起，Faying Protocol 在 iFay 框架中的位置可以被這樣精準錨定：

> **Faying Protocol 處於「實體層」與「核心組件」之上，是協定族裡專責「受控、監護、委託控制」語義的子協定。它把「FayID 是否歸屬於某個人類原型」這一根本問題，轉化為一組可被建立、維持、撤銷的連接狀態與動作。**

它不是 Fay 的能力定義，因此不規定 Fay 能做什麼。它不是 Fay 的行為指南，因此不規定 Fay 應該如何做。它只回答一個問題：

> **此刻這個 Fay 的行動，歸誰負責？**

正因如此，Faying Protocol 在 iFay 框架中既不屬於「最炫目」的協定，也不是「最深厚」的協定，但它是最不可被略過的那一個。一旦它缺位，整個 iFay 框架立刻退化為一個普通的 Agent 生態，把第一章描述的責任真空帶進社會。

## 本倉庫與 iFay 框架的邊界

```
                 +-------------------+
                 |   ifay.ai 全景    |
                 |  iFay 框架 4 層    |
                 +-------------------+
                          │
                          │  本倉庫取其中一員展開
                          ▼
            +---------------------------+
            |   Faying Protocol 專案    |
            |   （即本倉庫的全部資產）   |
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        藍圖          協定規範           schema
   docs/{lang}/    docs/{lang}/         schema/
    blueprint/    specification/       …（本期不交付）
   （即本 spec）  （後續獨立 spec）
```

本倉庫三類資產全部只承載 Faying Protocol 一項內容。任何 iFay 框架其他成員的深入展開，都不屬於本倉庫的範圍，請直接訪問 [ifay.ai](https://ifay.ai)。

![iFay 框架（alpha1）概覽：Faying Protocol 居於受控關係契約層](../../zh-CN/blueprint/illustration/ifay-framework-alpha1.png)

![iFay 標題橫幅](../../zh-CN/blueprint/illustration/ifay-title-banner.png)
