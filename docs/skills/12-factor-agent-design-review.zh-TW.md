# 12-factor-agent-design-review

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現。若無公認譯名，
    直接保留英文。代碼、API 名、CLI flag、套件名與檔名一律不翻。

用 HumanLayer 的
[12-Factor Agents](https://github.com/humanlayer/12-factor-agents)
作為 evidence-first 的工程分析視角，設計或審查 production LLM
application。Skill 提供 greenfield **Design**、有證據的 **Review**，以及
先審查現況再提出 target architecture 的 **Mixed** mode。

它刻意不是 compliance scorer，也不是 project scaffolder。

## 推薦使用場景

| 場景 | Mode | 為何適合 |
|---|---|---|
| 設計新的 customer-facing LLM workflow | Design | 在選定 framework 前，先明確定義 LLM/code 邊界、typed decision、durable state、pause/resume、retry 與驗證。 |
| Production-readiness architecture review | Review | 每個 verdict 都需要 file/line 或文件證據，並把 gap 連回使用者可見的 failure mode。 |
| 從 framework-owned behavior 遷移 | Mixed | 保留已運作的部分，找出被隱藏的 prompt/context/state/control-flow 決策，再定義可控制的 target state。 |
| 建立 async 或 human-in-the-loop workflow | Design 或 Review | 涵蓋 durable approval request/response、callback、timeout、cancellation、idempotency、resume 與 replay。 |
| 調查「卡在 80%」的 agent | Review | 檢查 context growth、無界 retry、hidden state、未驗證 model output 等系統性邊界。 |

## 有條件適合

- **Incident diagnosis：**先重現 failure，再用本 skill 尋找 architecture
  root cause；它不能取代 log、trace 或 runtime debugging。
- **Security-sensitive agent：**可找出 model output 接觸高風險 side
  effect 的位置，但仍需獨立 threat model 與 security review。
- **Model quality 問題：**可驗證 context、prompt ownership、eval 與 replay
  surface；本身不會 benchmark model accuracy。
- **Implementation planning：**可定義 interface 與 acceptance check；
  framework-specific code generation 應交給另外的 implementation 或
  scaffold workflow。

## 不適合使用

- 一般 [Twelve-Factor App](https://12factor.net/) deployment/configuration；
- 沒有 architecture 變更的單一 prompt 改寫；
- 比較 model 價格、latency、benchmark 或 provider 功能；
- 沒有 LLM decision boundary 的一般 code review；
- 生成可執行 starter project，或只按 feature checklist 選 framework。

## Skill 會產生什麼

### Design mode

- system boundary 與 non-goal；
- LLM、deterministic code、human 的 decision table；
- trigger/event/context/model/validation/handler/state flow；
- factor relevance、design decision 與 acceptance check；
- typed tool、state、human-response、failure、eval、observability contract；
- 依 dependency 排序的 implementation sequence。

### Review mode

- inspected scope 與 evidence coverage；
- 每個 factor 的 `Strong / Partial / Gap / N/A / Unverified` finding；
- 與 factor 編號無關、依 consequence 排序的 severity；
- 應保留的 strength；
- 最小 remediation sequence 與具體 verification step。

Skill 不會產生「12-factor compliance 百分比」。Factor 13
（pre-fetch context）永遠標示為 appendix extension，不會冒充正式第十三個
factor。

## Prompt 範例

```text
請設計一個 FastAPI + Postgres 的退款客服 agent。它從 email 和 Slack
啟動，500 美元以下可自動退款，以上需要人工核准，worker restart 後也要
安全 resume。
```

```text
用 12-Factor Agents review src/agent/ 和 docs/refund-workflow.md。請引用
file:line evidence、區分 Gap 與 Unverified，並依 production risk 排出最小修正。
```

```text
我們的 LangGraph workflow demo 正常，但 tool error 時會 loop，而且人工核准
後無法 resume。先 review 現況，再提出 target design；不要預設一定要移除
LangGraph。
```

## 來源與延伸

Factor 的 canonical intent 來自 HumanLayer。Conditional reference 也記錄：

- [`existential-birds/beagle@agent-architecture-analysis`](https://github.com/existential-birds/beagle/tree/main/plugins/beagle-analysis/skills/agent-architecture-analysis)
  的 evidence gate，但不採用其 Python-specific rubric；
- [`tika/12-factor-agent-skills`](https://github.com/tika/12-factor-agent-skills)
  的 workflow decomposition，但不採用 cross-skill dependency 與 scanner；
- [Adnan Masood 的 enterprise analysis](https://medium.com/@adnanmasood/12-factor-agents-framework-for-reliable-llm-agents-empirical-guidelines-for-scalable-auditable-4b758e0e7979)
  所補充的 auditability 與 idempotency 視角；
- [HumanLayer Discussion #61](https://github.com/humanlayer/12-factor-agents/discussions/61)
  的 scaffolding、observability、eval 與 failure-mode handoff 構想。

## Canonical SKILL.md

完整 workflow、gotcha、template 與 conditional reference 規則見
[skills/local/12-factor-agent-design-review/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/12-factor-agent-design-review/SKILL.md)。
