# Symlink target resolved relative to symlink, not repo root

## Symptom

```bash
$ ls -la .agents/skills/skill-author
lrwxr-xr-x  1 user  staff  26 ... .agents/skills/skill-author -> skills/local/skill-author/

$ test -e .agents/skills/skill-author/SKILL.md && echo OK || echo BROKEN
BROKEN

$ readlink -f .agents/skills/skill-author
# (empty, or path that doesn't exist)
```

The symlink looks fine in `ls -la` (target is a real path that exists
when read from repo root), but agents/tools that follow the link from
inside `.agents/skills/` see a dangling reference.

Same trap with `.claude/skills/<name> -> skills/local/<name>/` (would
resolve to `.claude/skills/skills/local/<name>/`).

## Root cause

POSIX symlinks resolve their target **relative to the directory
containing the symlink**, not relative to the directory you ran the
`ln -s` from. So:

```bash
# Wrong — looks right when you cd into repo root and ls
ln -s skills/local/skill-author .agents/skills/skill-author
# Effective target: .agents/skills/skills/local/skill-author/  ← does not exist
```

```bash
# Right — relative to where the symlink lives
ln -s ../../skills/local/skill-author .agents/skills/skill-author
# Effective target: <repo>/skills/local/skill-author/  ← exists
```

The shell-completion friendly form (`skills/local/...`) is what you'd
type from repo root and it tab-completes — that's what makes the bug
easy to introduce.

## Workaround

After creating any symlink, validate by following it from a different
working directory:

```bash
ln -sf ../../skills/local/skill-author .claude/skills/skill-author
test -e .claude/skills/skill-author/SKILL.md && echo OK || echo BROKEN
```

Or use `readlink -f` (GNU) / `realpath` and compare to the expected
absolute path.

To repair a broken one in place:

```bash
rm .agents/skills/skill-author
ln -s ../../skills/local/skill-author .agents/skills/skill-author
```

## Prevention

- **Always count `../` levels** from where the symlink lives to reach
  the target, not from where you're running `ln`.
- **The pattern in this repo is**: skills under `.agents/skills/` and
  `.claude/skills/` both point to `../../skills/local/<name>` (two
  parents = back to repo root).
- **Test new symlinks with `test -e <link>/SKILL.md`** before
  committing. A dangling symlink shows up green/valid in `ls -la` and
  in `git status`, so you only notice when an agent fails to load
  the skill.
- Both `.agents/skills/` and `.claude/skills/` should mirror the same
  set of links (`find-skills`, `skill-creator`, plus any local skill
  the repo wants to dogfood).

## Where this was hit

Commit `14a57a2` accidentally committed `.agents/skills/skill-author ->
skills/local/skill-author/` (relative to repo root), which resolved to
the non-existent `.agents/skills/skills/local/skill-author/`. Fixed in
`d42fe9e` by re-linking with `../../skills/local/...`. The bad symlink
was probably auto-created by an earlier action — this is exactly the
kind of "looks fine in `ls`" footgun that the validate-after-create
discipline above prevents.
