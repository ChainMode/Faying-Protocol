# Phase 1：人類原型 ↔ iFay

Phase 1 是 Faying Protocol 的第一塊基石：把「人類原型 ↔ iFay」這一最基礎的監護關係建立起來，並使其能在任意終端、任意應用中被忠實表達與持續維持。

這一階段不追求覆蓋廣度，追求深度自洽：在 Phase 1 落地之後，任意一個 iFay，無論運行在哪台設備、哪個作業系統、哪個應用容器裡，都能夠清楚地回答兩個問題——「我此刻是否處於 Faying State？」「如果是，我歸誰負責？」

這是整個 Faying Protocol 演進的最小可用形態。後續 Phase 2 至 Phase 5 都建立在 Phase 1 之上：如果 Phase 1 不成立，後續的擴展就沒有立足點。

## 覆蓋範圍

Phase 1 僅覆蓋一類關係：

> **人類原型 ↔ iFay**

關係的責任端是某個具體的人類原型（Human Prime）；關係的另一端是該人類原型的某個 iFay；關係的內容是 iFay 在該人類原型的監護下展開數位行動。

Phase 1 不直接覆蓋「人類原型 ↔ 終端」或「人類原型 ↔ 軟體應用」。當一架無人機、一個家庭機器人、一個企業流程應用進入 Faying 關係時，Phase 1 要求的表達方式是：

> **該終端 / 該軟體應用通過對應人類原型的 iFay 進入 Faying State**，而不是與人類原型直接建立 Faying 關係。

這一表達方式是有意為之。iFay 是 Faying Protocol 在 Phase 1 中唯一被信任承接監護契約的實體形態。把「無人機 ↔ Jack」理解為「無人機通過 Jack 的 iFay 進入受控狀態」，能讓 Phase 1 的責任鏈條始終保持簡潔清晰，避免提前引入「多端直接 Faying」的複雜度。

## 三個核心議題

在覆蓋範圍被嚴格限定為「人類原型 ↔ iFay」的前提下，Phase 1 必須解決三個核心議題。

**建立**——Faying Action 如何由人類原型顯式發起、被見證、被記錄，並將 iFay 推入 Faying State。這一議題在第十二章（Faying 雙重語義）展開。

**維持**——Faying State 在 iFay 整個工作生命週期中如何被持續校準。既要保證它在每一時刻仍然成立，也要保證它一旦不再成立就立即退出。這一議題對應第十三章（Rogue Fay 與責任歸屬）的九項觸發條件。

**退出**——Faying State 退出後，iFay 如何轉入 Rogue Fay 並僅保留 A/B/C 三個維度的最小行為集，禁止 D 維度的全部對外行動。這一議題對應第十三章的 A/B/C/D 四維度規則。

這三項議題不是 Phase 1 的「高級特性」，是 Phase 1 的全部內容。在它們被自洽落地之前，Phase 1 不被視為完成。Phase 1 的範圍被故意收得很小，是為了讓接下來的 Phase 2 至 Phase 5 在一片已經成立的契約土壤上展開擴展，而不是同時與基礎形態鬥爭。

![Phase 1 概念圖：人類原型與 iFay 的最小受控關係](../../zh-CN/blueprint/illustration/phase1-concept.png)

![Phase 1 架構圖：iFay 在 Faying State 下的運作骨架](../../zh-CN/blueprint/illustration/phase1-architecture.png)
