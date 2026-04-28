.PHONY: sync sync-check add-vendor kanban add-todo promote-todo sweep-inbox docs-serve docs-build docs-deploy test-skill marketplace

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

# Test the agent-history-hygiene skill: pytest (unit + corpus) + bash
# exit-code contract. Requires `uv sync --extra dev` once, plus
# `gitleaks` on PATH for the corpus + shell tests (they skip gracefully
# if missing).
test-skill:
	uv run --extra dev pytest skills/local/agent-history-hygiene/tests/ -q
	bash skills/local/agent-history-hygiene/tests/test_scan_staged.sh
