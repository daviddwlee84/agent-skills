.PHONY: sync sync-check add-vendor kanban

sync:
	./scripts/sync-vendor.sh

sync-check:
	./scripts/sync-vendor.sh --check

# Usage: make add-vendor SOURCE=owner/repo/path/to/skill
add-vendor:
	./scripts/add-vendor.sh $(SOURCE)

kanban:
	./scripts/todo-kanban.sh
