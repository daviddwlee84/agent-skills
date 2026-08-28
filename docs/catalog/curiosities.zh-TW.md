# Skill 趣味收藏架

這裡收錄有趣、好玩、帶挑釁性或高度個人化，值得記住但刻意不放進本
repo 日常工作流的 agent skill。

本頁條目**只存在於 docs**：不複製到 `skills/vendor/`、不寫入
`vendor.yaml`、不放進 marketplace，因此不會參與 skill discovery。只有
使用者主動打開來源並自行安裝時，才會影響其 agent 環境。

--8<-- "_snippets/external-install.md"

## Meta-skill 與 persona 實驗

| Skill | 核心概念 | 有趣之處 | 為何只放 docs | Status |
|---|---|---|---|---|
| [`anti-distill`](https://github.com/leilei926524-tech/anti-distill) | 重寫 skill，讓文件看似完整，但抽掉最有價值的隱性知識。 | 把知識蒸餾 (knowledge distillation) 與企業知識移交流程整個反轉，帶有鮮明的諷刺意味。 | 設計目標刻意對抗一般文件與知識分享目的；適合作為觀察素材，不適合預設工作流。 | `skipped` |
| [`distilly`](https://github.com/titanwings/distilly)（原 `colleague-skill`） | 從同事、關係對象或公眾人物的素材，蒸餾出可供 agent 使用的人物 profile。 | 是 persona 擷取、證據收集與持續更新角色模擬的一個格外完整案例。 | 高度個人化、涉及隱私，且偏離本 repo 的一般工程工作流。 | `skipped` |
| [`create-ex`](https://github.com/therealXiaomanChu/ex-skill) | 從回憶、聊天記錄、照片與社群貼文建立會持續演化的前任模擬 persona。 | 位在 agent skill、數位記憶與情感模擬交界，是很令人印象深刻的實驗。 | 涉及敏感關係資料，使用情境也很窄，不適合在這裡自動 discovery。 | `skipped` |

## 加入另一個趣味收藏

當一個 skill 的點子、文化訊號或互動設計值得日後回看，但不該成為 agent
日常行為的一部分，就在表格新增一列。說明應保持描述性，不代表認同其
行為或用途。

狀態使用 `skipped`，並簡短寫明理由。若日後確認它對例行工作真的有用，
再把條目移到 [External skills](skill-collections.md)，並依照一般的
[catalog status workflow](../workflows/adding-catalog-entries.md) 處理。
