# verifiable-surfaces

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

設計與驗證 app、CLI、service、config 的可執行表面 (exercisable
surface)。這個 skill 有兩個互補模式：

- **Authoring mode** — 寫新的 CLI、tool、library、service 時，要讓它暴露
  `--help`、`--dry-run`、`--print-config`、isolated-state smoke entrypoint，
  以及明確的 exit-code 契約。
- **Verification mode** — 改 config、CLI args/env parsing、dotfiles、
  Ansible、IaC、generated/rendered config 時，走 verification ladder
  直到最高一個 harmless gate 通過。

核心 invariant：一個無法被便宜且 harmless 地執行的表面，不算被驗證過，
無論 lint 通過多少。

## skill 觸發時機

**Authoring mode:**

- 用 Python uv + tyro / click / argparse、Node commander/yargs/oclif、
  Bash 寫新 CLI，或寫任何有 side effect 的腳本
- 為現有 tool 新增 subcommand、flag、env var
- 寫 service/daemon 帶 config file，或 SDK/library 會 load config

**Verification mode:**

- 編輯 app/tool config，例如 `next.config.*`、`pyproject.toml`、
  `mkdocs.yml`、`docker-compose.yml`、`pueue.yml`、DVC/MLflow config、
  service manifest
- 改 CLI args、env parsing、config discovery order、default 或
  startup-time setting
- 更新 dotfiles 或 generated config，尤其是 chezmoi template、shell init
  file、Git hooks、editor config、launchd/systemd unit、Ansible、
  Terraform、Kubernetes、CI、deploy manifest

## Authoring checklist (通用)

1. `--help` 列出 usage、所有 flag、範例、exit code
2. `--dry-run` 對任何有 side effect 的操作都要存在，**且仍然 load 真正的
   config / 解析真正的 plan**
3. `--print-config` (或 `--show-config`) 印出完整 merge 過的 effective
   config (對會 load config 的程式)
4. 接受 `--config <path>`；尊重 `$HOME` / `$XDG_CONFIG_HOME`
5. exit-code 契約寫在 `--help`
6. stdout 是 data；stderr 是 log 與 diagnostic
7. 完成前自我驗證：`--help`、`--dry-run`、`--print-config`、
   故意餵 bad input 看是否回 non-zero、isolated-state smoke
   (`env -i HOME=$(mktemp -d) ...`)

## Verification ladder

1. Syntax/schema gate
2. Rendered/applied config gate (驗證 render 出來的輸出，不是 template 原始檔)
3. App/tool-native loader gate (`config check`、`doctor`、`--print-config`、
   `plan`、`--dry-run`)
4. Compile/build gate
5. Harmless runtime smoke (temp `$HOME`、`/tmp`、container、`--check`、
   限制 tag/target)

## 例子

附帶的 reference 涵蓋兩個模式：

- [`references/authoring-checklist.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/references/authoring-checklist.md)
  — Python (tyro/click)、Node (commander/yargs)、Bash 範本，加一段五行
  self-verification snippet
- [`references/config-examples.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/references/config-examples.md)
  — chezmoi (`apply --dry-run --verbose`、`diff`、`execute-template`)、
  Ansible (`--syntax-check` 只是 gate 1；之後再跑 `--check`/`--diff`/
  `--tags`/`--limit`)、JS/TS、Python settings、Docker Compose、
  Kubernetes、Terraform/OpenTofu

## Canonical SKILL.md

完整觸發描述、雙模式 workflow、gotcha 與 reference 連結見
[skills/local/verifiable-surfaces/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/verifiable-surfaces/SKILL.md)。
