# superproject-workspace

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現。**不自創翻譯**——
    若無公認譯名直接保留英文（如 `submodule`、`gitlink`、`worktree`）。
    代碼、CLI flag、檔名一律不翻。

讓一個以 **git submodule 組成的 superproject** 成為跨多個 repo 的 agent 單一入口，
又不會隨時間慢慢偏掉。適用於平行 repo 的 umbrella，也適用於混合 core、personal、
reference repo 的 workspace hub。

gitlink 記錄的是 commit，不是 branch，所以偏移是預設狀態：子 repo merge PR 後
pointer 默默落後、checkout 停在 detached 或 dirty、pointer 指向沒人 push 的 commit。
這個 skill 讓偏移**看得見**，並依 **policy** 移動 pointer。

| Surface | 回答的問題 |
|---|---|
| `scripts/superproject.py status` | 「哪些子 repo 落後、偏移、dirty，或指向未 push 的 commit？」 |
| `scripts/superproject.py pull` / `bump` | 「怎麼安全地移動 pointer，並收斂成一個外層 commit？」 |
| `scripts/superproject.py worktree` | 「子 repo 的 feature branch 要放哪？」 |
| `scripts/superproject.py audit` / `adopt` | 「怎麼把早期的 superproject 升級到這套規範？」 |
| `assets/superproject-bump.yml` | 「不靠人記得，pointer 怎麼自動跟上？」 |
| `references/decision-guide.md` | 「該用 monorepo、submodule、manifest + clone，還是 Project add-dir？」 |

## Policy 存在 `.gitmodules`

```ini
[submodule "app"]
    path = app
    url = git@github.com:me/app.git
    branch = main
    x-policy = track     # track | pin | lazy
    x-bump = pr          # pr | direct | manual（僅 track）
    x-tier = core
```

| Policy | Pointer 怎麼移動 | 預設是否 init |
|---|---|---|
| `track` | ff-only `pull` 後 `bump`；可由 CI 自動化（`pr` 或 `direct`） | 是 |
| `pin` | 只能 `bump --reason` | 是 |
| `lazy`（`update = none`） | 只能 `bump --reason` | 只在指名時 |

## 核心流程

```bash
sp status --fetch
sp worktree add app feat/login   # .worktrees/app/feat-login
# ...在子 repo 內 commit + push + PR...
sp pull
sp bump --all-track --commit     # 先 preflight，收斂成一個外層 commit
```

既有的 superproject：先跑 `audit`，再跑 `adopt --dry-run --policy-default pin --set app=track:pr`，
review 之後執行 `adopt`。它會寫入 AGENTS.md 區塊、`sub-*` justfile
recipe、`.worktrees/` ignore、本地 git config，也可選擇加入 CI workflow 與 pre-commit hook。

CLI 是**引用，不複製**：recipe 會找已安裝的 skill（`~/.agents/skills/superproject-workspace`），
找不到才從 GitHub raw 的 `$SUPERPROJECT_CLI_REF` 取得。一次 `npx skills update` 就能更新所有 superproject。
skill 更新後重跑 `adopt` 即可刷新 managed block；過時時 `audit` 會提示。

（`sp` = `uv run --script ~/.agents/skills/superproject-workspace/scripts/superproject.py`，或 `just sub-*` recipe。）

## 延伸閱讀

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/superproject-workspace)
- [`git-workflow`](git-workflow.md)：單一 repo 的 commit、branch、worktree。
- [`forge-native-dev`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/forge-native-dev)：各子 repo 內的 issue 與 PR 流程。
