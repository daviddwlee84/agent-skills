# `specstory sync` reports `1 session not found` for a synthetic macOS session

## Symptom

```text
specstory sync failed (rc=1): ERROR

  1 session not found.
```

The JSONL exists under `~/.claude/projects/<slug>/<uuid>.jsonl`, its UUID is
correct, and the slug appears to follow Claude Code's rule of replacing every
non-alphanumeric path character with `-`.

## Root cause

On macOS, `tempfile.gettempdir()` commonly returns a logical path under
`/var/folders/...`, while the physical cwd seen by a subprocess resolves to
`/private/var/folders/...`.

SpecStory derives the Claude provider lookup from that physical cwd. A probe
that builds `<slug>` from the unresolved `/var/...` string writes the session
under `-var-folders-...`; SpecStory searches `-private-var-folders-...` and
cannot find it.

## Workaround

Resolve the project directory before deriving both the Claude project slug and
the subprocess cwd:

```python
project_dir = project_dir.resolve()
slug = re.sub(r"[^A-Za-z0-9]", "-", str(project_dir))
```

## Prevention

Any synthetic Claude/SpecStory session generator must derive storage paths from
the canonical physical project path. Treat `Path.resolve()` (or `realpath`) as
part of the slug algorithm, especially for macOS temp directories and other
symlinked mount aliases.
