# Decision guide: how to bring repos together for an agent

Goal: one agent entry point with context (and usually edit access) across
several repos, without coupling their histories, CI, or release cycles more
than necessary.

| Option | What it is | Version snapshot of the set? | Drift problem | Best when |
|---|---|---|---|---|
| **Real monorepo** | One repo, one history | Yes (every commit) | None | Repos ship together, share CI and owners, and change atomically |
| **Submodule superproject** (this skill) | Outer repo pins each child by gitlink | Yes (outer commit = exact set) | Yes, so manage it by policy | Repos are independent but you need reproducible "this set worked together" points, or the outer repo carries shared knowledge (agent history, context, runbooks) |
| **Manifest + gitignored clones** | `repos.yaml` + a clone/update script (`mani`, `gita`, `repo`, `meta`, or 20 lines of shell) | No (unless you record SHAs yourself) | None: each clone is just "whatever is checked out" | You only need co-location for context; no one asks "which versions went together?" |
| **Project / add-dir** (Claude Code `--add-dir`, Codex or Claude Projects) | Agent session spans several existing checkouts | No | None | Ad-hoc, personal, short-lived cross-repo tasks |

## Questions that decide it

1. **Do you need to reproduce a combination later?** Examples: "what did prod
   run", "the umbrella state that passed parity checks". If yes, choose
   submodules, or a monorepo if the repos are tightly coupled.
2. **Does the outer repo have content of its own?** Examples: AGENTS.md, a
   cross-repo `context/` graph, `pitfalls/`, SpecStory history, deployment
   runbooks. If yes, a superproject gives that content a versioned home, and
   the gitlinks date each note against concrete child versions.
3. **Do children have different owners, visibility, or forges** (GitHub +
   GitLab, personal + org)? Then rule out a monorepo; submodules or a manifest
   both work.
4. **Will you remember to bump?** If not, either automate it (`x-bump = pr` or
   `direct`) or choose a manifest. A superproject with no bumping is the worst
   option: it pins by accident.

## Hybrid that works well

Use a superproject for the **core** set (`track` or `pin`), and mark
reference material `lazy` so a fresh clone stays small. Truly throwaway reads
don't need a submodule at all: use add-dir for those.
