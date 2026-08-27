.PHONY: sync sync-check add-vendor kanban add-todo promote-todo sweep-inbox docs-serve docs-build docs-deploy test-skill marketplace native-marketplace-smoke native-claude-smoke native-codex-smoke lint-frontmatter validate install-hooks

sync:
	./scripts/sync-vendor.sh

sync-check:
	./scripts/sync-vendor.sh --check

# Usage: make add-vendor SOURCE=owner/repo/path/to/skill
add-vendor:
	./scripts/add-vendor.sh $(SOURCE)

kanban:
	./scripts/todo-kanban.sh

# Validate skills/.claude-plugin/marketplace.json — the catalog manifest
# read by `npx skills@latest add daviddwlee84/agent-skills/skills`.
marketplace:
	./scripts/validate-marketplace.sh

# Exercise both native marketplace loaders in isolated config state. Kept
# separate from `validate` so contributors without either CLI can run the
# portable publish gates.
native-marketplace-smoke: native-claude-smoke native-codex-smoke

native-claude-smoke:
	./scripts/smoke-claude-marketplace.sh

native-codex-smoke:
	./scripts/smoke-codex-marketplace.sh

# YAML-parse every skills/**/SKILL.md frontmatter. A skill whose frontmatter
# does not parse is silently SKIPPED by `npx skills add` (and by Claude Code /
# Cursor), so this gate runs before publishing. Uses yq, PyYAML, or the js
# "yaml" package — whichever is installed.
lint-frontmatter:
	./scripts/lint-frontmatter.sh skills

# Portable publish gates and the set run by the pre-push hook. CI runs these
# plus `native-marketplace-smoke`; both CLI dependencies stay optional locally.
validate:
	./scripts/lint-frontmatter.sh --quiet skills
	./scripts/validate-marketplace.sh
	./scripts/todo-kanban.sh --validate-only

# Symlink scripts/git-hooks/pre-push into .git/hooks so `git push` runs
# `make validate` first. Bypass a single push with `git push --no-verify`.
install-hooks:
	@ln -sf "$$(git rev-parse --show-toplevel)/scripts/git-hooks/pre-push" "$$(git rev-parse --git-dir)/hooks/pre-push"
	@echo "installed: $$(git rev-parse --git-dir)/hooks/pre-push -> scripts/git-hooks/pre-push"

# Convenience wrappers around scripts/add-todo.sh, promote-todo.sh, sweep-inbox.sh.
# For full flags use the scripts directly.
# Usage: make add-todo ARGS="--priority P3 --effort M --title 'X' --description 'Y'"
add-todo:
	./scripts/add-todo.sh $(ARGS)

# Usage: make promote-todo ARGS="--title 'substring' --summary 'shipped summary'"
promote-todo:
	./scripts/promote-todo.sh $(ARGS)

sweep-inbox:
	./scripts/sweep-inbox.sh $(ARGS)

# Docs site: MkDocs Material + mkdocs-llmstxt + mkdocs-copy-to-llm.
# Requires `uv sync --extra docs` once.
docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

# Manual one-shot deploy (CI handles this on push to main).
docs-deploy:
	uv run mkdocs gh-deploy --force

# Test agent-history-hygiene plus git-workflow's commit contract: pytest
# (unit + corpus) + bash exit-code/metadata/message contracts. Requires
# `uv sync --extra dev` once, plus
# `gitleaks` on PATH for the corpus + shell tests (they skip gracefully
# if missing).
test-skill:
	uv run --extra dev pytest skills/local/agent-history-hygiene/tests/ -q
	bash skills/local/agent-history-hygiene/tests/test_scan_staged.sh
	bash skills/local/agent-history-hygiene/tests/test_agent_commit_metadata.sh
	bash skills/local/git-workflow/tests/test_check_commit_msg.sh
