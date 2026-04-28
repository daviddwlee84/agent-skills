# Creating local skills — 建立 local skill

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

Local skill 是這個 repo 內、放在
[`skills/local/<skill-name>/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local)
的自製 skill。

## 起手新 skill

```bash
cd skills/local
npx skills@latest init [skill-name]
```

這會建立 `skills/local/<skill-name>/SKILL.md`，包含必要的 YAML
frontmatter（`name`、`description`）。

## 必要結構

完整佈局規則見 [Conventions](../conventions.md)。簡言之：

- `SKILL.md` —— 必要，精簡（控制在 ~500 行以內）。
- `assets/` —— skill 複製到目標 project 的 template。
- `scripts/` —— 可執行輔助 (Bash 3.2 相容)。
- `references/` —— 按需載入的長篇資料。

## 依照 agentskills.io best practices 寫 SKILL.md

[agentskills.io best practices](https://agentskills.io/skill-creation/best-practices)
中槓桿最大的兩條：

1. **程序勝過宣告 (Procedures over declarations)。** 告訴 agent 該**做什麼**，
   不要告訴它**該成為誰**。寫「跟著這三步」遠比寫
   「要當一個謹慎、有條理的助手」可靠。
2. **預設勝過選單 (Defaults over menus)。** 挑一條工作流程當預設；
   其他選項透過 flag 或 `references/` 提供。每一步都讓 agent 在三個
   等價選項間挑，是除錯惡夢。

我們在這個 repo 套用的第三條：

- **能寫成 script 就寫成 script。** 如果 skill 一直在叫 agent 做同樣的
  多步驟程序，乾脆把它寫成 `scripts/` 下的 shell script，然後讓
  SKILL.md 去呼叫該 script。
  [`project-knowledge-harness`](../skills/project-knowledge-harness.md)
  skill 是這個 pattern 的範本。

## 加一頁 docs

每個 local skill 也應該在 `docs/skills/<skill>.md` 有一頁，
向人類讀者說明這個 skill 是做什麼用的、何時會觸發、用它的成本是什麼。
`SKILL.md` 是面向 agent 的契約；docs 頁面是面向人類的推銷。
兩者都有價值。

建立 docs 頁面時，也要從
[`docs/skills/index.md`](../skills/index.md) 連結它，並加進 repo 根目錄
`mkdocs.yml` 的 `nav:` 區段。

## 用一個 scratch project 來測試安裝

```bash
mkdir /tmp/scratch && cd /tmp/scratch
git init
npx skills@latest add daviddwlee84/agent-skills/skills
```

這會把新 skill 拉進一個乾淨 project 的 `.agents/skills/`，讓你驗證
SKILL.md 是否如預期被觸發。
