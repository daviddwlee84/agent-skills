# yq invalid expression / wrong query result

## Symptom

```
Error: bad expression, please check expression syntax
error: yq failed applying: ... 3
```

Or yq query silently returns `null` even though the data clearly contains the
match (no error, just wrong answer).

Two common triggers:

1. **Unquoted ISO date in `--set` value** —
   `bash check-preferences.sh --set foo.decided_at=2026-04-23` produces a
   yq expression like `.foo.decided_at = 2026-04-23`, and yq treats
   `2026-04-23` as the arithmetic expression `2026 - 04 - 23`, which it
   then chokes on. (Bare integers and `true`/`false`/`null` are fine; ISO
   dates and most other "looks like a literal" strings need quoting.)

2. **`strenv(VAR)` inside a chained pipeline that yq can't bind** —
   `yq '.nav | to_entries | map(select(.value | type == "!!map" and (keys | .[0] == strenv(SEC))))' file`
   returns `null` even though `[.nav[] | keys | .[0]]` clearly contains
   the value of `$SEC`. `strenv(...)` reads at parse time from a yq env
   binding that is not always plumbed through deeply nested `select(...)`.

## Root cause

mikefarah/yq's expression language has two ways to read environment
variables:

- `strenv(VAR)` — early-bound string lookup, sometimes does not survive
  through certain pipeline shapes.
- `env(VAR)` + `as $var` — late-bound, works inside `select(...)` and
  nested expressions reliably.

For values, yq follows YAML scalar parsing rules: an unquoted token that
looks like a YAML scalar of any type is parsed as that type.
`2026-04-23` is not a YAML date in yq's expression grammar — it's a
subtraction. The fix is to emit it as a quoted string (`"2026-04-23"`).

## Workaround

**For env-var-in-query**: prefer the `env(VAR) as $var` form:

```bash
SEC=Reference yq 'env(SEC) as $s |
  [.nav[] | keys | .[0]] | to_entries |
  map(select(.value == $s)) | .[0].key' mkdocs.yml
```

**For unquoted-date in `--set`**: quote anything that is not a
bool/`null`/pure-integer:

```bash
case "$v" in
  true|false|null) yv="$v" ;;
  ''|*[!0-9]*)     yv="\"${v//\"/\\\"}\"" ;;  # any non-digit → quote
  *)               yv="$v" ;;                  # all-digits → leave as int
esac
yq -i ".$ns.$key = $yv" "$file"
```

## Prevention

- When writing yq queries that need shell variables, default to
  `env(VAR) as $name` over `strenv(VAR)`. The latter is fine for
  top-level string substitution but failure-prone in nested selects.
- When writing values into yq via `--set`, never trust that the raw
  string will be interpreted as a YAML string. Quote everything that
  is not provably a number/bool/null. Test with at least one ISO date
  and one URL.
- Both `add-docs-page.sh` and `check-preferences.sh` in
  `skills/local/mkdocs-site-bootstrap/scripts/` ship with the workarounds
  above; copy from there when writing new yq-using scripts.

## Where this was hit

Building `skills/local/mkdocs-site-bootstrap/scripts/{add-docs-page,check-preferences}.sh`
during the initial scaffold (commit `a0886a5`). Both bugs were silent: the
add-docs-page one returned `null` and bailed with a "section not found"
error pointing at the wrong cause; the preferences one printed `bad
expression` but the date wasn't visually obviously the trigger.
