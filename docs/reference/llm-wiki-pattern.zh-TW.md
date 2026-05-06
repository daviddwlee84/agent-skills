# Karpathy 的 LLM Wiki pattern

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：嵌入
    (embedding)。**不自創翻譯**——若無公認譯名直接保留英文（如 `RAG`、
    `wiki`、`schema`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

整理 Andrej Karpathy 在 2025 年底提出的「**由 LLM 維護的個人知識庫
(personal knowledge base maintained by an LLM)**」pattern。這頁是**文件,
不是 skill**——先把想法存下來,之後再決定要 vendor 既有實作（如
`obsidian-second-brain`）還是自己寫一個 local skill。

## 來源

- [`gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
  ——長版「LLM Wiki」pattern 文件,設計成可以直接貼給你自己的 LLM agent,
  讓它跟你共同設計具體實作。
- [`x.com/karpathy/status/2039805659525644595`](https://x.com/karpathy/status/2039805659525644595)
  ——原始 tweet（"LLM Knowledge Bases"）,gist 的~一頁濃縮版,也是整個
  pattern 的種子。

## TL;DR

Wiki 是一個**持久 (persistent)、會累積 (compounding) 的產物**。
`RAG` 每次 query 都從 raw sources 重新 derive 知識;LLM Wiki 把該知識
**compile 一次**進結構化 markdown,並隨新來源 ingest **持續維護更新**。

> Obsidian 是 IDE,LLM 是 programmer,wiki 是 codebase。
> ——Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## 原始 tweet（逐字英文引用）

> **LLM Knowledge Bases**
>
> Something I'm finding very useful recently: using LLMs to build personal
> knowledge bases for various topics of research interest. In this way, a
> large fraction of my recent token throughput is going less into
> manipulating code, and more into manipulating knowledge (stored as
> markdown and images). The latest LLMs are quite good at it. So:
>
> **Data ingest:** I index source documents (articles, papers, repos,
> datasets, images, etc.) into a `raw/` directory, then I use an LLM to
> incrementally "compile" a wiki, which is just a collection of `.md` files
> in a directory structure. The wiki includes summaries of all the data in
> `raw/`, backlinks, and then it categorizes data into concepts, writes
> articles for them, and links them all. To convert web articles into `.md`
> files I like to use the Obsidian Web Clipper extension, and then I also
> use a hotkey to download all the related images to local so that my LLM
> can easily reference them.
>
> **IDE:** I use Obsidian as the IDE "frontend" where I can view the raw
> data, the compiled wiki, and the derived visualizations. Important to
> note that the LLM writes and maintains all of the data of the wiki, I
> rarely touch it directly. I've played with a few Obsidian plugins to
> render and view data in other ways (e.g. Marp for slides).
>
> **Q&A:** Where things get interesting is that once your wiki is big
> enough (e.g. mine on some recent research is ~100 articles and ~400K
> words), you can ask your LLM agent all kinds of complex questions
> against the wiki, and it will go off, research the answers, etc. I
> thought I had to reach for fancy RAG, but the LLM has been pretty good
> about auto-maintaining index files and brief summaries of all the
> documents and it reads all the important related data fairly easily at
> this ~small scale.
>
> **Output:** Instead of getting answers in text/terminal, I like to have
> it render markdown files for me, or slide shows (Marp format), or
> matplotlib images, all of which I then view again in Obsidian. You can
> imagine many other visual output formats depending on the query. Often,
> I end up "filing" the outputs back into the wiki to enhance it for
> further queries. So my own explorations and queries always "add up" in
> the knowledge base.
>
> **Linting:** I've run some LLM "health checks" over the wiki to e.g.
> find inconsistent data, impute missing data (with web searchers), find
> interesting connections for new article candidates, etc., to
> incrementally clean up the wiki and enhance its overall data integrity.
> The LLMs are quite good at suggesting further questions to ask and look
> into.
>
> **Extra tools:** I find myself developing additional tools to process
> the data, e.g. I vibe coded a small and naive search engine over the
> wiki, which I both use directly (in a web ui), but more often I want to
> hand it off to an LLM via CLI as a tool for larger queries.
>
> **Further explorations:** As the repo grows, the natural desire is to
> also think about synthetic data generation + finetuning to have your LLM
> "know" the data in its weights instead of just context windows.
>
> **TL;DR:** raw data from a given number of sources is collected, then
> compiled by an LLM into a `.md` wiki, then operated on by various CLIs
> by the LLM to do Q&A and to incrementally enhance the wiki, and all of
> it viewable in Obsidian. You rarely ever write or edit the wiki
> manually, it's the domain of the LLM. I think there is room here for an
> incredible new product instead of a hacky collection of scripts.

## 架構 (Architecture)

三層,出自 gist:

1. **Raw sources** ——你篩選過的源文件（articles、papers、images、
   datasets）。**Immutable**——LLM 只讀不改,這是 source of truth。
2. **The wiki** ——LLM 生成的 markdown 目錄（summaries、entity 頁、
   concept 頁、comparisons、overview、synthesis）。LLM 完全擁有這層,
   你讀,LLM 寫。
3. **The schema** —— `CLAUDE.md` / `AGENTS.md`,告訴 LLM wiki 的結構、
   慣例 (conventions)、ingest / query / lint 的 workflow。你跟 LLM 一起
   隨時間共同演化 (co-evolve) 這份 schema。

## 三個 operations

| Operation | 做什麼 |
| --------- | ------ |
| **Ingest** | 把新 source 丟進 `raw/`,LLM 讀完、寫 summary 頁、更新對應 entity / concept 頁、更新 index、append log。一個 source 可能 touch 10–15 頁。 |
| **Query** | 提問。LLM 先讀 index,drill 進相關頁,然後回答——可以是 markdown 頁、比較表、Marp 簡報、matplotlib 圖。**好答案要回填 (file back) 進 wiki**,explorations 才會累積。 |
| **Lint** | 定期健檢 (health check)。找矛盾、stale 主張、orphan 頁、缺 cross-reference、資料缺口。並建議下一步要 investigate 的問題跟要找的新 sources。 |

## 兩個特殊檔案

- **`index.md`** ——content-oriented 目錄。每頁一條 link + 一行 summary,
  按類別分組。LLM 每次 ingest 都更新,query 時先讀。在 ~100 sources / 數百
  頁規模下,不需要 embedding-based RAG 基礎建設就能 work。
- **`log.md`** ——chronological,append-only。建議用統一 prefix（如
  `## [2026-04-02] ingest | Article Title`）讓 log 變 greppable:
  `grep "^## \[" log.md | tail -5`。

## 為什麼 work

殺掉個人 wiki 的不是讀或想,是**維護 (maintenance)**。更新 cross-reference、
保持 summary 最新、標出新舊矛盾、跨數十頁維持一致性——人類會放棄,因為
維護負擔成長得比價值快。LLM 不會無聊、不會忘了補 back-link,而且一次能
touch 15 個檔案。Wiki 持續被維護,因為維護成本接近零。

這個 pattern 精神上接近 Vannevar Bush 的 [Memex](https://en.wikipedia.org/wiki/Memex)
（1945）——一個私人、主動策展 (curated) 的知識庫,文件之間的關聯
(associative trails) 跟文件本身一樣重要。Bush 沒解掉的部分是**誰來維護**。
LLM 解掉了。

## 周邊生態 (Ecosystem)

圍繞這個 pattern 長出來的實作跟相關工具:

- **[`eugeniughelbur/obsidian-second-brain`](https://github.com/eugeniughelbur/obsidian-second-brain)**
  ——一個 Claude Code skill（不是 Obsidian plugin）,把 pattern 推得更遠:
  31 個 slash commands + 排程 agents + Python scripts。加進 AI-first
  慣例（machine-readable preamble、bi-temporal facts——同時 track「事實
  何時為真」+「vault 何時學到」、Two-Output Rule——每個答案都順便更新
  相關頁面）、vault-first research（先掃既有 notes 再上網查）、
  `_CLAUDE.md` / `index.md` / `log.md` / `SOUL.md` / `CRITICAL_FACTS.md`
  （~120 tokens 永遠載入）放在 vault root。
  *"If Karpathy's wiki is a knowledge base you maintain with an LLM,
  this is a knowledge base that maintains itself."*
- **[`tobi/qmd`](https://github.com/tobi/qmd)** ——本地 markdown 搜尋引擎
  （hybrid BM25 + vector + LLM re-ranking,全部 on-device）。同時有 CLI
  （給 LLM shell 出去用）跟 MCP server。Gist 提到當 index 檔擋不住時的
  自然升級路徑。
- **Obsidian Web Clipper**、**Marp**（markdown-to-slides）、**Dataview**
  （對 frontmatter 跑 query）——gist 推薦的支援工具。

## 跟本 repo 的關係

本 repo 的 [`project-knowledge-harness`](../skills/project-knowledge-harness.md)
是**任務記憶 (task memory)** —— `TODO.md` + `backlog/` + `pitfalls/`,
圍繞已交付/延後工作跟過去踩到的坑。Karpathy 的 LLM Wiki 是**知識記憶
(knowledge memory)** —— 對某個外部研究領域策展、合成 (synthesize) 後的
view。兩者正交 (orthogonal),可以在同一個 project 共存。

可能的後續（**未承諾**）:

- Vendor `obsidian-second-brain` 進 `skills/vendor/`（license 允許的話）,
  跟 `project-knowledge-harness` 並列當「兩種 memory pattern」的對照組。
- 寫一個極簡 local skill `llm-wiki-bootstrap` ——只做 gist 描述的三層
  架構 + `index.md` / `log.md` + `ingest` / `query` / `lint` 三個指令,
  不綁 Obsidian。

如果要正式追蹤,用 [`scripts/add-todo.sh`](scripts.md) 加一條 `P3`。
