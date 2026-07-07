# TODO

Long-term backlog for this repo. See [CLAUDE.md](CLAUDE.md) for the maintenance
workflow that agents should follow.

> For agents: add explicitly deferred work here with priority and effort tags.
> Keep `TODO.md` as the single index, use `backlog/<slug>.md` for non-trivial
> investigation, use `pitfalls/<slug>.md` for non-obvious traps, and move
> shipped items to `## Done` in the same commit.
>
> Prune `## Done` into `CHANGELOG.md` only when it contains items from a
> previous calendar year or grows past 20 entries.

## P1

## P2
- [ ] **[S] Bump GitHub Actions to next majors before Node 20 deprecation** — actions/checkout@v4, actions/setup-python@v5, actions/upload-artifact@v4, astral-sh/setup-uv@v5 will deprecate June 2026. Bump checkout/upload-artifact to @v5, setup-python to @v6, setup-uv to @v6 in .github/workflows/docs.yml and any other workflows. Verify deploy still passes.

## P3
- [ ] **[S] Document 'prefer relative links' as docs convention** — Add an explicit rule in docs/conventions.md and CLAUDE.md: inside docs/, default to relative links (not absolute https URLs) so docs are portable across deploys. Absolute URLs only when (a) linking to files outside docs/ in the GitHub repo, or (b) absolutely necessary. See pitfalls/mkdocs-strict-rejects-build-time-generated-links.md for the validation.links.not_found:info workaround that makes this work with strict mode.
- [ ] **[S] Mirror-check script for scripts/ vs project-knowledge-harness/scripts/** — Add scripts/check-script-mirror.sh that diffs scripts/{add-todo,sweep-inbox,promote-todo,todo-kanban}.sh against skills/local/project-knowledge-harness/scripts/ and exits non-zero if any pair differs. Wire into a Make target and (later) CI.
- [ ] **[M] Bake validation.links.not_found:info into mkdocs-site-bootstrap template** — skills/local/mkdocs-site-bootstrap/assets/mkdocs.yml.template should ship with the validation override pre-set so downstream sites don't rediscover the strict-mode-rejects-build-time-generated-links pitfall. Also document the rationale inline as a YAML comment.
- [ ] **[S] Document --full-depth in README install snippet for nested local skills** — Current README install snippet 'npx skills@latest add daviddwlee84/agent-skills' silently skips skills/local/ entries (project-knowledge-harness, skill-author, mkdocs-site-bootstrap, quantatitive-factor-researcher) due to npx skills CLI's one-level discovery: fallback recursive search only triggers when zero top-level matches, but skills/vendor/skill-creator etc. satisfy that, blocking deeper discovery. Add a separate snippet showing '--full-depth -s name' usage. See pitfalls/skills-cli-skips-nested-skills-without-full-depth.md.
- [ ] **[S] Smoke-test marimo-batch-mlflow starting-point.py end-to-end** — Run 'uv run skills/local/marimo-batch-mlflow/references/starting-point.py --help' to verify Tyro --help generation, then run with --epochs 1 --batch-size 8 against a local MLflow server (mlflow server --port 5000) to verify mlflow.log_metric works and the live MlflowChart cell renders in marimo edit mode. Capture any breakage as a pitfall.
- [ ] **[S] Offer Tyro + provider-agnostic refactor as upstream PR to marimo-team/skills/marimo-batch** — Once marimo-batch-mlflow is shipped and battle-tested, raise an upstream PR offering Tyro as an opt-in CLI parser (current upstream uses mo.cli_args() + hand-rolled rich.Table). Optional courtesy contribution; does not need to land MLflow swap (that stays as a separate skill in this repo). Reference: skills/local/marimo-batch-mlflow/references/starting-point.py.
- [ ] **[M] Decide on LLM Wiki skill: vendor obsidian-second-brain vs author llm-wiki-bootstrap** — Karpathy's LLM Wiki pattern (docs at reference/llm-wiki-pattern.md) is orthogonal to project-knowledge-harness — task memory vs knowledge memory. Either vendor eugeniughelbur/obsidian-second-brain (license permitting) or author a minimal local skill covering just the gist's three-layer architecture + index/log + ingest/query/lint. Pick one or explicitly defer.
- [ ] **[S] Catalog frontmatter validator script** — Add scripts/validate-catalog-frontmatter.sh to lint required YAML keys (name, slug, upstream_url, transport, auth, hosting, domain, status, license, last_verified) on every docs/catalog/mcp/*.md and verify the domain: field references an existing docs/catalog/domains/*.md hub. Wire into a Make target. Build when 5+ MCP entries justify the maintenance.
- [ ] **[S] MCP wiki index auto-regenerator** — Read frontmatter from each docs/catalog/mcp/*.md and regenerate the entries table inside docs/catalog/mcp/index.md between marker comments (similar to how todo-kanban renders). Saves manual table edits as the wiki grows. Build when 5+ MCP entries make hand-editing painful.
- [ ] **[M] Catalog cross-link audit script** — Add scripts/audit-catalog-links.sh: every entry with status: vendored should resolve to a real vendor.yaml line; every status: deferred should resolve to a TODO.md item; every domain hub linked from a catalog entry should exist. Catches drift between catalog and the sources of truth. Run after make sync.

## P?

- [ ] **[?/M] Python + uv workflow skill** — evaluate package management, `uv run`, and virtualenv activation conventions for Python-focused repos.
- [ ] **[?/L] Next.js + Supabase + shadcn/ui + Tailwind CSS + Vercel** — evaluate a full-stack app skill that covers auth, data, UI scaffolding, and deployment together.
- [ ] **[?/M] VectorBT skill** — assess the minimum workflow for factor research, backtesting, and result inspection with VectorBT.
- [ ] **[?/L] VectorBT Pro skill** — assess whether a premium-only skill can reliably point agents at the correct documentation page and paid workflow nuances.
- [ ] **[?/M] Nautilus Trader skill** — evaluate event-driven trading workflows, backtests, and live-trading guardrails for Nautilus Trader users.
- [ ] **[?/M] Marimo + Tyro skill** — evaluate notebook-style experimentation plus CLI configuration patterns in one skill.
- [ ] **[?/M] Streamlit app skill** — evaluate the minimum build, state, and deployment workflow for Streamlit agents.
- [ ] **[?/L] Grafana + OpenTelemetry + LGTM stack** — evaluate an observability skill that covers local telemetry setup, dashboards, and debugging flow end to end.
- [ ] **[?/M] n8n automation skill** — evaluate workflow automation patterns, self-hosting constraints, and common integration shapes for n8n.
- [ ] **[?/M] MLflow experiments skill** — evaluate experiment tracking, model registry touchpoints, and reproducibility guidance for MLflow users.
- [ ] **[?/M] DVC skill** — evaluate dataset versioning, remotes, and experiment workflows for DVC-backed projects.
- [ ] **[?/L] Rust-backed Python package with PyO3** — evaluate packaging, build tooling, and mixed-language debugging guidance for PyO3 projects.
- [ ] **[?/M] GitHub Actions skill** — evaluate workflow authoring, local validation, and debugging guidance for common Actions use cases.
- [ ] **[?/L] LangChain / LangSmith / LangServe / LangGraph / Langfuse** — evaluate how this orchestration and observability stack should be grouped into one coherent skill set.
- [ ] **[?/M] Build MCP skill** — evaluate the minimum workflow for creating, testing, and documenting MCP servers or tools.
- [ ] **[?/L] LLM fine-tuning skill** — evaluate the practical workflow for supervised fine-tuning and adapter-based tuning with current tooling.
- [ ] **[?/M] Hugging Face Spaces + Gradio skill** — evaluate demo app deployment, secrets handling, and local-to-hosted handoff for Spaces.
- [ ] **[?/L] Tardis SDK skill** — evaluate historical market data workflows, access assumptions, and example-driven guidance for Tardis users.
- [ ] **[?/M] Discord bot skill with discord.py** — evaluate bot setup, event handling, and deployment guidance for Discord automation.
- [ ] **[?/M] Playwright skill** — evaluate web automation, testing, and website-cloning workflows that are realistic for agents to maintain.
- [ ] **[?/M] GitHub Docs + mkdocs-material skill** — evaluate documentation authoring, local preview, and publishing flow for GitHub-hosted docs.
- [ ] **[?/M] Data visualization skill** — evaluate Matplotlib, Seaborn, and Plotly guidance for fast exploratory charting and report-ready output.
- [ ] **[?/L] Financial data sources skill set** — compare free and paid market-data providers, clarify regional coverage, and decide whether skills should be organized by provider or workflow. → [research](backlog/financial-data-sources.md)
- [ ] **[?/M] Docker Compose skill** — evaluate local multi-service workflows, overrides, and debugging patterns for Compose-driven projects.
- [ ] **[?/L] Kubernetes skill** — evaluate whether the first version should target `kubectl`, Python clients, or operational troubleshooting patterns.
- [ ] **[?/L] CI/CD pipelines skill** — evaluate how much shared guidance belongs above tool-specific systems like GitHub Actions, Jenkins, and CircleCI.
- [ ] **[?/M] Terraform skill** — evaluate module structure, plan/apply safety, and reviewable IaC workflows for Terraform users.
- [ ] **[?/M] Ansible skill** — evaluate playbook structure, inventory handling, and idempotent troubleshooting patterns for Ansible repos.
- [ ] **[?/M] chezmoi skill** — evaluate dotfile templating, apply workflows, and common gotchas for chezmoi-managed machines.
- [ ] **[?/M] Tailscale skill** — evaluate device onboarding, ACL/auth-key management, and common networking tasks for Tailscale users.
- [ ] **[?/L] Sibling docs-stack skills (docusaurus / vitepress / hugo / sphinx)** — mkdocs-site-bootstrap is intentionally MkDocs-specific (Python/Material stack). Not all projects want MkDocs: JS projects often prefer Docusaurus or VitePress, Go/static prefer Hugo, scientific Python prefers Sphinx. Each should be a separate skill (docusaurus-site-bootstrap, vitepress-site-bootstrap, etc.) following the same consent-gated + .skills/preferences.yaml pattern. Don't merge into a generic docs-site-bootstrap — the configs / lifecycle / link-checker rules are too divergent. Currently uncertain whether to write all four or wait until needed; keeping as P?.
- [ ] **[?/M] marimo-batch-pydantic-only variant skill** — If usage shows people want strict Pydantic validation + Field descriptions WITHOUT Tyro overhead (e.g., embedded in larger app where Tyro's argparse takeover is unwanted), spin off a marimo-batch-pydantic skill that uses pydantic + a thin click/typer CLI instead. Decide based on whether marimo-batch-mlflow's Pydantic alternative section gets requested standalone.
- [ ] **[?/M] AI/ML research skills series in vendor.yaml** — Once 3+ candidates from Orchestra-Research/AI-research-SKILLs (98 skills, 23 categories) are vetted via the new AI/ML Research catalog hub, create a P? ai-ml-research series in vendor.yaml mirroring fullstack-nextjs. Cherry-pick rather than wholesale; some skills overlap with existing local skills (mlflow-tracking, dvc-ml-workflow).
- [ ] **[?/M] Decide on vendoring anthropics/financial-services subsets** — Currently wishlist in the Finance hub. Decide whether to vendor any specific plugins (financial-analysis is the highest-value entry: DCF, LBO, comps, 3-statement + 11 MCP connectors) or stay with manual install. Most plugins assume Cowork / Managed Agents deployment, not solo Claude Code — verify per-plugin compatibility before vendoring.
- [ ] **[?/M] Decide: flatten fullstack-nextjs series vs upstream CLI fix** — Series skills at skills/vendor/fullstack-nextjs/<name>/ (depth 4) fail plain 'npx skills update' downstream and never get .claude/skills symlinks — see pitfalls/skills-update-fails-for-series-nested-skills.md. Two mutually-exclusive fixes: (A) flatten to skills/vendor/<name>/ (depth 3) so shallow discovery finds them — touches vendor.yaml series field, sync-vendor.sh, marketplace.json paths; keeps grouped install UI since that is manifest-driven. (B) file an upstream issue on vercel-labs/skills so 'update' passes --full-depth (or the deletion-check honors it). Pick one. → [research](backlog/flatten-fullstack-nextjs-series.md)
- [ ] **[?/M] demo-evidence: PR posting for evidence bundles** — gh pr comment posts MANIFEST text + artifact inventory; opt-in --publish uploads screenshots to gist raw URLs so they embed inline (video as link). MUST run gitleaks/redact over any text before external publish since .evidence/ media has no public URL. Extends skills/local/demo-evidence.

## Done

- ✅ [2026-04-23] [P2/L] Author mlflow-tracking skill — MLflow skill: SKILL.md + 6 references (sqlite-local, docker-compose-server, llm-tracing, model-registry, autologging-by-framework, mlflow-widgets) + 3 scripts (init-sqlite/start-server/tail-runs) + vendored docker-compose-stack assets. Lint clean.

- ✅ [2026-04-23] [P2/L] Author dvc-ml-workflow skill — DVC skill: SKILL.md + 4 references (pipelines, experiments-queue, data-remotes, plots-metrics) + 3 scripts (init/queue-helper/lint) + 3 templates. Lint clean.
