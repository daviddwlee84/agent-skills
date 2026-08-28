
我現在要製作一個skill是我的Python best practice 特別是for agentic coding的時代
不過我現在會把我所有想法列出來 你需要再幫我統整一下 順便看有沒有漏掉的

1. 一定用uv來做package management 且最好是足夠新的版本 (src/package-name) => README 要有getting started user知道怎麽uv sync等等
2. 製作CLI的話使用Tyro (並且注意shell的auto completion) -> 合理切分subcommmand modules => 方便下游user可以直接uv tool install (不一定要直接deploy PyPI 可以先讓user從git link來install)
3. notebooks 使用marimo notebook 且notebook可以有script mode (一樣用Tyro) 這樣多種interface (WebUI/CLI 都能有相同體驗) 非package的notebook應該要放 notebooks/

- notebooks 可以做爲package的使用範例
- package 可自帶anywidget 特別是一些特殊visualize

1. logging使用loguru
2. 最好都有CLI 並且同時在 AGENTS.md (symlink to CLAUDE.md) 確保每次更新package都能同步更新skill (甚至可以學herdr 把skill直接做進)
3. 推薦如果scaffold項目自帶我們的skills

- agent-history-hygiene
- project-knowledge-harness
- mkdocs-site-bootstrap => 所有public項目都有良好的github page docs說明 (給人類看 ; 給agent看有llms.txt)

1. 此skill也可以用作舊的Python項目的refactor依據指南
2. TDD driven development始得loop engineering可驗收
3. 項目以外的helper放到 scripts之中
4. 製作Justfile把常用操作放進去 或是考慮用 [tool.taskipy.tasks] ？
5. 我們的package要維護一個自己的agent skill 讓agent知道如何調用
6. 我們應該會要有一個scaffold CLI for此purpose (可以是一個Tyro uv script讓AI調用 並保證可控)
7. 如果有API server設計考慮FastAPI + Pydantic等 (需有Swagger/OpenAPI說明頁)
8. 如果agent skill不夠涵蓋的部分可以考慮製作MCP
9. agentic是一個選項 不過也可以初始最簡 後面有需要再慢慢加上去
10. 也考慮有Rust backend + PyO3的開發指南
11. 考慮項目類型可能帶額外推薦skill 比如ML項目等等 可能會考慮帶上 experimentknowledge-harness 等等
12. linting formatting 考慮 ruff, black等 (setup LSP?)

Optional setup

```
❯ cat .envrc
# https://github.com/direnv/direnv/issues/1264
# .envrc
# export VIRTUAL_ENV=.venv
# layout python3
# [[ -d ".venv" ]] || . .venv/bin/activate

# .envrc
# 自動啟動 .venv
# since direnv cannot modify PS1, won't got prompt like `(.venv) $`
# unless you configure PS1 in your shell rc file
export VIRTUAL_ENV="$PWD/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"

# 如果有 .env 就載入
dotenv_if_exists
```

核心要點

1. clear
2. portable
3. plug and play
4. easy to use
...

由繁至簡都可以用
從0 setup還是舊項目refactor也可以用
普通情況就是Python dev guide 但可以避免許多過時的開發

有必要的話 skill assets裡面可以直接帶上含dir structure的template? 等等
