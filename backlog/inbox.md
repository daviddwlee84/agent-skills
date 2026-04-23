# Inbox

Quick-capture area for the maintainer. Drop loose ideas here whenever the
priority/effort/wording isn't clear yet — the [`sweep-inbox.sh`](../scripts/sweep-inbox.sh)
script will formalize them into [`TODO.md`](../TODO.md) on demand.

Lines starting with `#` and blank lines are ignored. Anything else is
treated as a candidate for triage.

Two accepted shapes:

1. Free-form line — sweep prompts you for priority/effort/title/description:

   ```
   - maybe add docs versioning with mike
   ```

2. Pre-parsed key=value line — sweeps in `--batch` mode without prompting:

   ```
   - priority=P3 effort=M title="Add docs versioning" description="Use mike for versioned docs"
   ```

Once a line has been formalized into `TODO.md`, sweep-inbox removes it
from this file. To trigger:

```bash
./scripts/sweep-inbox.sh             # interactive
./scripts/sweep-inbox.sh --batch     # non-interactive; only key=value lines
./scripts/sweep-inbox.sh --dry-run   # preview without modifying anything
```

<!-- inbox entries below this line; mix free-form and key=value freely -->

