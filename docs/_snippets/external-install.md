!!! info "Status enum (single source of truth across the catalog)"

    Every external-skill or MCP entry below carries a `status:` value:

    | Status | Meaning | Where it links |
    |---|---|---|
    | `vendored` | Already in [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml). | Link to the `skills/vendor/<name>/` (or series) entry. |
    | `deferred` | Open `TODO P?` item — under consideration. | Link to the [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md) anchor. |
    | `skipped` | Looked at, chose not to vendor. | Inline reason required (1 sentence). |
    | `evaluated` | Read but no decision recorded. Effectively "tracked." | Inline 1-line note describing what was learned. |
    | `wishlist` | Surfaced but not yet evaluated. | No link required; default for fresh discoveries. |

    Status changes are explicit edits — see the **Adding catalog
    entries** workflow doc (under `Workflows` in the nav) for the
    `wishlist → deferred → vendored` recipe.

!!! tip "Manual install for non-vendored skills"

    When a skill is not in `vendor.yaml`, you can still install it directly
    from upstream via the [`npx skills`](https://skills.sh) CLI:

    ```bash
    # Whole-repo install (if SKILL.md sits at repo root or skills/)
    npx skills@latest add <owner>/<repo>

    # Subpath install (when the skill is nested)
    npx skills@latest add <owner>/<repo>/<path-to-skill-dir>

    # Cherry-pick by name
    npx skills@latest add <owner>/<repo> -s <skill-name>

    # Force deep discovery (skill nested >1 level inside skills/)
    npx skills@latest add <owner>/<repo> --full-depth -s <skill-name>
    ```

    For Anthropic-style **plugin marketplaces** (e.g.
    `anthropics/financial-services`,
    `anthropics/knowledge-work-plugins`), use the Claude Code plugin
    commands instead:

    ```bash
    claude plugin marketplace add <owner>/<repo>
    claude plugin install <plugin-name>@<repo-name>
    ```

    For MCP servers, see the per-entry "Auth & install" section in
    the MCP wiki — install commands vary by transport (HTTP / stdio /
    SSE) and host (Claude Code / Claude Desktop / Cursor / Managed
    Agents).
