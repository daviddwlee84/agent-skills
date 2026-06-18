# fastapi-ai-interview-prep

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現,例:依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    (如 `embedding`、`tokenizer`)。代碼、API 名、CLI flag、套件名、檔名一律不翻。

給 FastAPI + AI 工程職缺的題庫與 mock interviewer 工具組。十個主題檔各 10 題
(共 100 題),每個答案都寫到面試官在聽的 **senior signal** —— 區分「會用 API」
與「在規模下跑過」的那個 production 後果或 trade-off。

> 啟發自 *FastAPI for AI Engineers* (AI Engineering Insider, 2026) 的主題涵蓋。
> 所有問答皆從頭撰寫;這不是書中題目的重製。

## 出貨內容 (What ships)

- 完整 SKILL.md
  ([skills/local/fastapi-ai-interview-prep/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/SKILL.md))
  —— 三種 session 模式 (mock interview、主題刷題、自我測驗) 與評分 rubric
  (正確性 → senior signal → 情境方法)。
- 十份 reference (`references/ch01-intro.md` … `ch10-deployment.md`),每章一份、
  各 10 題自撰問答:
  [intro/ASGI](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch01-intro.md)、
  [Pydantic](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch02-pydantic.md)、
  [endpoint](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch03-endpoints.md)、
  [dependency injection](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch04-dependency-injection.md)、
  [database](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch05-database.md)、
  [security](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch06-security.md)、
  [testing](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch07-testing.md)、
  [async](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch08-async.md)、
  [AI serving](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch09-ai-serving.md)、
  [deployment](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch10-deployment.md)。
- 一個 script:
    - [`quiz.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/scripts/quiz.py)
      —— 即時從 reference 解析問題並抽題/列出/揭示答案。只用 stdlib。

## 快速開始

```bash
cd skills/local/fastapi-ai-interview-prep

python3 scripts/quiz.py --topics              # 章節 + 題數
python3 scripts/quiz.py --random 5            # 抽 5 題 (不含答案)
python3 scripts/quiz.py --answer ch09-q4      # 揭示一題的 rubric
python3 scripts/quiz.py --topic ch08 --random 4 --with-answers
python3 scripts/quiz.py --random 3 --seed 42 --json   # 可重現、機器可讀
```

跑 mock interview 時抽不含答案的題目、讓候選人作答,再依 id 逐題揭示 rubric,
照 senior signal 評分。

## Cross-references

- 要*應用*這些 pattern:[`fastapi-ai-patterns`](fastapi-ai-patterns.md)。
- 要*建構*服務:[`fastapi-ai-scaffold`](fastapi-ai-scaffold.md)。
