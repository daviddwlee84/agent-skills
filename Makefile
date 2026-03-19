.PHONY: sync sync-check

sync:
	./scripts/sync-vendor.sh

sync-check:
	./scripts/sync-vendor.sh --check
