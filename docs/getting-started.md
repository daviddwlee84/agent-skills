# Getting Started

## Install the skills

--8<-- "_snippets/install.md"

This populates `.agents/skills/` in your project with everything under
`skills/local/` and `skills/vendor/` from this repo.

## Render the repo backlog

If you want to see the kanban view of the repo's own TODO list:

```bash
git clone https://github.com/daviddwlee84/agent-skills
cd agent-skills
make kanban
```

`make kanban` runs [`scripts/todo-kanban.sh`](reference/scripts.md#todo-kanbansh),
which validates [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)
and prints a Markdown board grouped by lane.

## Build the docs locally

The docs site you're reading is a [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
site. To preview it locally:

```bash
# From the repo root
uv sync --extra docs
uv run mkdocs serve
```

Then open <http://127.0.0.1:8000/>.

To produce the static site (what GitHub Pages serves):

```bash
uv run mkdocs build --strict
```

`make docs-serve` and `make docs-build` are convenience wrappers around
those two commands.

## Apply the project-knowledge-harness skill to your own project

If you just want the TODO + backlog + pitfalls structure in another repo,
the bundled init script does the whole setup in one shot:

```bash
git clone https://github.com/daviddwlee84/agent-skills /tmp/agent-skills
/tmp/agent-skills/skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/your/project \
  --project-name "Your Project" \
  --deployment chezmoi   # or npm | pip | docker | none
```

See the [`project-knowledge-harness` page](skills/project-knowledge-harness.md)
for what the script does and what flags it supports.
