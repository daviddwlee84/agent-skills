# External skill collections —— 外部 skill 收錄

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

策展 (curated) 過的 upstream skill collection、marketplace、相關專案
索引。多數**未** vendor 進本 repo —— 列在這裡是給出手動安裝路徑與
記錄 vendoring 決策。

本頁取代 repo 根目錄的歷史 [`Collections.md`](https://github.com/daviddwlee84/agent-skills/blob/main/Collections.md)
（保留為 stub 維持 backlink），並收整原本在
[`README.md`](https://github.com/daviddwlee84/agent-skills/blob/main/README.md)
的「Resources」段落。

--8<-- "_snippets/external-install.md"

## Skills 管理工具 (managers)

安裝與探索 agent skill 的 CLI / runtime。本站頁首的安裝命令使用第一個。

| 工具 | Upstream | Status | 備註 |
|---|---|---|---|
| `npx skills` | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) | `vendored`-as-tool | 本 repo 標準化採用的 CLI。`marketplace.json` 如何驅動分組挑選器見 [npx skills metadata model](../reference/npx-skills-metadata.md)。 |
| The Agent Skills Directory | [`skills.sh`](https://skills.sh/) | `evaluated` | 託管的 `npx skills` 相容 skill 目錄。利於探索。 |
| Skill.Fish | [`knoxgraeme/skillfish`](https://github.com/knoxgraeme/skillfish) ([site](https://www.skill.fish/)) | `evaluated` | 另一套 skill manager。本 repo 未使用；列出供認識。 |

## 通用 (general-purpose) collection

涵蓋廣泛 engineering / 撰寫主題的多 skill repo。其中數個有部分
vendored（特定 skill 精選 (cherry-picked) 進
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)）。

| Collection | Upstream | Status | 備註 |
|---|---|---|---|
| Anthropic 一手 (first-party) skill | [`anthropics/skills`](https://github.com/anthropics/skills) | `vendored`（部分） | 已 vendor `skill-creator`、`frontend-design`、`webapp-testing`、`mcp-builder`。 |
| Vercel Labs agent skills | [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | `vendored`（部分） | 已 vendor `web-design-guidelines` 進 `fullstack-nextjs` series。 |
| Vercel plugin skills | [`vercel/vercel-plugin`](https://github.com/vercel/vercel-plugin) | `vendored`（部分） | 已 vendor `nextjs`、`shadcn`、`react-best-practices`、`vercel-storage` 進 `fullstack-nextjs` series。 |
| Supabase agent skills | [`supabase/agent-skills`](https://github.com/supabase/agent-skills) | `vendored`（部分） | 已 vendor `supabase`、`supabase-postgres-best-practices` 進 `fullstack-nextjs` series。 |
| marimo team skills | [`marimo-team/skills`](https://github.com/marimo-team/skills) | `vendored`（部分） | 已 vendor `marimo-notebook`、`streamlit-to-marimo`、`anywidget`。 |
| Streamlit agent skills | [`streamlit/agent-skills`](https://github.com/streamlit/agent-skills) | `wishlist` | 尚未評估；結構鏡射 marimo-team 的樣式。 |
| Matt Pocock skill | [`mattpocock/skills`](https://github.com/mattpocock/skills) | `vendored`（部分） | 已 vendor 這條 15 個 skill 的 end-to-end 流程（grill → spec → tickets → implement → review）進 `engineering-fundamentals` series —— 流程、完整清單與我們跳過的部分見 [`reference/mattpocock-skills.md`](../reference/mattpocock-skills.md)。 |
| GarryTan / OpenClaw skills | [`garrytan/gstack`](https://github.com/garrytan/gstack) | `vendored`（部分） | 已 vendor 4 個 skill 進 `product-planning` series。 |
| Warp Oz skills | [`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) | `vendored`（部分） | 15 個中 vendor 6 個 —— 跳過原因見 [`reference/warp-oz-skills.md`](../reference/warp-oz-skills.md)。 |
| 199-biotechnologies deep-research | [`199-biotechnologies/deep-research`](https://github.com/199-biotechnologies/deep-research) | `vendored` | 單 skill series。見 [`reference/deep-research-landscape.md`](../reference/deep-research-landscape.md)。 |
| The Minimalist Entrepreneur skill | [`slavingia/skills`](https://github.com/slavingia/skills) | `evaluated` | 基於 Sahil Lavingia 的 [The Minimalist Entrepreneur](https://www.amazon.com/Minimalist-Entrepreneur-Great-Founders-More/dp/0593192397) 的 skill。Persona 取向；作為單一作者 opinionated skill pack 的範本很有用。 |
| `last30days` 主題 synthesizer | [`mvanhorn/last30days-skill`](https://github.com/mvanhorn/last30days-skill) | `evaluated` | 跨 Reddit、X、YouTube、HN、Polymarket、web 研究主題 → 有依據的摘要 (grounded summary)。 |

## 領域取向 (domain-specific) collection

聚焦特定領域的 skill pack 與 plugin marketplace —— 對應的
[domain hub](domains/index.md) 有交叉引用。

| Collection | Upstream | Status | 領域 | 備註 |
|---|---|---|---|---|
| Claude for Financial Services | [`anthropics/financial-services`](https://github.com/anthropics/financial-services) | `wishlist` | [Finance](domains/finance.md) | 龐大的 marketplace：11 個命名 agent、7 個 vertical plugin、partner plugin（LSEG、S&P Global）。21.5k ⭐。 |
| Awesome Finance Skills | [`RKiding/Awesome-finance-skills`](https://github.com/RKiding/Awesome-finance-skills) | `wishlist` | [Finance](domains/finance.md) | 8 個即插即用 finance skill（news、stock data、sentiment、forecasting、signal tracking、viz、reporting、web search）。 |
| AI Research Skills library | [`Orchestra-Research/AI-research-SKILLs`](https://github.com/Orchestra-Research/AI-research-SKILLs) | `wishlist` | [AI/ML Research](domains/ai-ml-research.md) | 跨 23 個分類的 98 個 skill —— 完整研究生命週期。有自家 npm wrapper：`npx @orchestra-research/ai-research-skills`。 |
| Knowledge Work Plugins | [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) | `wishlist` | [Knowledge Work](domains/knowledge-work.md) | 11 個職能 plugin（sales、legal、finance、data、bio-research 等）。12.1k ⭐。 |

## 文章與相關閱讀

| 標題 | 來源 | 備註 |
|---|---|---|
| [Building Agent Skills with skill-creator](https://medium.com/google-cloud/building-agent-skills-with-skill-creator-855f18e785cf) | Google Cloud / Medium | 走 [`skill-creator`](../skills/skill-creator.md)（已 vendor）的 workflow。 |
| [Introducing: React Best Practices](https://vercel.com/blog/introducing-react-best-practices) | Vercel blog | 與已 vendor 的 [`react-best-practices`](../skills/react-best-practices.md) skill 配對。 |
| [Six skills for financial service professionals](https://claude.com/resources/tutorials/claude-for-financial-services-skills) | Claude resources | 在 [Finance](domains/finance.md) 也交叉引用。 |

## Skill 候選 (candidates)（評估中）

可能成為 vendored skill 或啟發 local skill 的參考專案 —— 尚未正式評估。

| 候選 | Upstream | Status | 備註 |
|---|---|---|---|
| 12-factor agents | [`humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) | `skipped` | Canonical methodology，不是可安裝 skill，因此不 vendor；它是 local [`12-factor-agent-design-review`](../skills/12-factor-agent-design-review.md) 的 CC BY-SA attribution source。 |
| `agent-architecture-analysis` | [`existential-birds/beagle`](https://github.com/existential-birds/beagle/tree/main/plugins/beagle-analysis/skills/agent-architecture-analysis) | `skipped` | Evidence gate 有價值，但 rubric 綁定 Python/Pydantic/Jinja/REST implementation choice。Local skill 只引用 framework-neutral 的 evidence pattern。 |
| 12-factor agent skill pack | [`tika/12-factor-agent-skills`](https://github.com/tika/12-factor-agent-skills) | `skipped` | Design/review/debug decomposition 可借鏡，但單獨安裝 skill 可能缺少 cross-skill reference，heuristic scanner 也可能把自身 source 當成證據；只作 extension reference，不 vendor。 |
| The Twelve-Factor App | [12factor.net](https://12factor.net/) | `evaluated` | 原始 12-factor 宣言。靈感來源，非 skill。 |
| `agent-skill-creator` | [`FrancyJGLisboa/agent-skill-creator`](https://github.com/FrancyJGLisboa/agent-skill-creator) | `wishlist` | 另一個 authoring 工具；與本 repo 的 [`skill-author`](../skills/skill-author.md) + vendored `skill-creator` 對照。 |
| `find-skills` | [`vercel-labs/skills/find-skills`](https://skills.sh/vercel-labs/skills/find-skills) | `evaluated` | 來自 `vercel-labs/skills` 的探索 skill。 |

## Vendoring 政策

我們在以下情況 vendor 一個 skill：

1. Upstream 有穩定的權威 (canonical authority)（Vercel 對 Next.js、
   Supabase 對 Supabase 等）。
2. 此 skill 補上其他 vendored / local skill 沒涵蓋的空缺。
3. License 與 [agentskills.io specification](https://agentskills.io/specification)
   相容。

**不** vendor 的情況：

- Upstream 本身就是 marketplace / collection（改用精選 (cherry-pick)）。
- Plugin 形式的 collection（如 `anthropics/knowledge-work-plugins`）
  需要 `claude plugin install` 而非 `npx skills add` —— 這裡記錄供
  手動安裝。
- 此 skill 與更權威來源已 vendored 的 skill 重複。
- 此 skill 太窄（host-specific、BigQuery-specific 等）不適合通用。

完整 workflow —— 包含如何把條目從 `wishlist` → `deferred` →
`vendored` 推進 —— 見
[Adding catalog entries](../workflows/adding-catalog-entries.md)。
