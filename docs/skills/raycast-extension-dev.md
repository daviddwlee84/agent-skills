# raycast-extension-dev

Build, verify, and ship [Raycast](https://developers.raycast.com/) extensions in
TypeScript. Raycast's own docs cover what `List` and `Form` accept; this skill
covers the other 20% — **what the toolchain does not check, what the runtime does
not provide, and what the Raycast Store checks that the linter does not**.

Every claim in it was paid for once while building
[Pueue for Raycast](https://github.com/daviddwlee84/Pueue-Raycast-Extension), and
most of them trace back to a file in that repo's
[`pitfalls/`](https://github.com/daviddwlee84/Pueue-Raycast-Extension/tree/main/pitfalls).

| Surface | Question it answers |
|---|---|
| `new-raycast-extension.sh` | "Scaffold me an extension that is gated from the first commit." |
| `check-store-readiness.sh` | "What will store review reject that `ray lint` just passed?" |
| [`references/runtime-and-subprocess.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/runtime-and-subprocess.md) | "Why is my binary not found, when `which` finds it instantly?" |
| [`references/manifest-and-commands.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/manifest-and-commands.md) | "What can a `package.json` command / preference / argument actually declare?" |
| [`references/data-and-state.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/data-and-state.md) | "Why does my action flash, revert, and then re-apply?" |
| [`references/ui-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/ui-patterns.md) | "Which List/Form/ActionPanel idiom, and why did my dropdown reset itself?" |
| [`references/menu-bar.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/menu-bar.md) | "How do I show a count without opening Raycast, and why is mine stale?" |
| [`references/store-publishing.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/references/store-publishing.md) | "What is left before I can submit, and what can never be automated?" |

## The gate, and why it is four commands

The single most expensive fact about the Raycast toolchain:

| Command | Catches | Misses |
|---|---|---|
| `tsc --noEmit` | types | manifest, formatting, runtime shape |
| `node dev-check.js` | your own invariants, wire shapes, generated argv | anything you did not assert |
| `ray lint` | manifest schema, icons, ESLint, Prettier, reserved-shortcut collisions | types |
| `ray build` (`-e dev`) | syntax, that esbuild can bundle it | **types — esbuild strips them without checking** |
| `ray build -e dist` | the above **plus types** (it runs `tsc -p tsconfig.json --noEmit`) | manifest, formatting |

Measured on a scaffold carrying one genuine `TS2345`: `ray build` exits **0** and
prints `ready - built extension successfully`; `ray build -e dist` exits **1** and
reports it. The dist build is therefore a stronger pre-submit check than most
people realise — but `npm run build`, `just build`, and `ray develop` are all the
*dev* build, which is precisely why a type error survives long enough to ship.

Two real bugs took that route in the source extension: a `MutatePromise<GroupMap>`
passed where `MutatePromise<State>` was expected — which at runtime would have
emptied the list on every action — and a `ReactNode`/`JSX.Element` clash caused by
`@raycast/api` bundling its own copy of `@types/react`. Neither produced a single
line of output.

The skill ships that gate as `assets/Justfile.template`, and the scaffolder writes
it into every new extension.

## What `ray lint` does not check

Verified, not assumed: **`ray lint` exits 0 with a completely empty `metadata/`
directory.** Its "validate extension metadata" stage passes. So the linter cannot
be your submission gate — screenshot count and dimensions, icon size, whether the
icon is still a placeholder, the CHANGELOG placeholder, and a real `author` are all
review-time requirements nothing runs locally.

`check-store-readiness.sh` covers exactly that column, emitting a JSON array of
`{id, status, detail, fix}` and exiting `4` when something fails, `3` when a check
had to be skipped for a missing tool (skipped is never reported as passed).

## When the skill triggers

- "Build me a Raycast extension for X" / "wrap this CLI in Raycast"
- "It works in `npm run dev` but not from Raycast" — the launchd PATH trap, which
  the dev console structurally cannot reproduce
- "The menu bar shows the wrong count / nothing / stale data"
- "My action flashes the new state, reverts, then re-applies"
- "Get this ready for the Raycast Store"

## When it doesn't

- **Raycast Script Commands** — a separate repo, no manifest, no React.
- **Generic React/TSX quality** → `react-best-practices`.
- **The wrapped CLI's own semantics** → that tool's skill, or its `--help`.
- **AI Extensions without Raycast Pro** — `tools[]` is Pro-gated, and there is no
  confirmation surface inside a tool call, so a first version must be read-only.
- **Taking the screenshots.** The skill verifies their count and dimensions. It
  cannot capture a window, and neither can any CLI.

## Structure

```text
skills/local/raycast-extension-dev/
├── SKILL.md                              485 lines — workflows A-F + 27 gotchas
├── references/
│   ├── runtime-and-subprocess.md         launchd env, path probing, execFile, streaming, error taxonomy
│   ├── manifest-and-commands.md          every manifest field + the schema length minimums
│   ├── data-and-state.md                 hooks, cache-key scoping, the reconcile measurement loop
│   ├── ui-patterns.md                    List/Detail/Form/ActionPanel, dropdowns, shortcuts, markdown fencing
│   ├── menu-bar.md                       every MenuBarExtra constraint with its consequence
│   └── store-publishing.md               checklist, screenshot mechanics, review criteria
├── scripts/
│   ├── new-raycast-extension.sh          scaffold a gated extension (exit 0/1/2/3/4)
│   └── check-store-readiness.sh          the store checks ray lint skips (exit 0/1/2/3/4)
└── assets/
    ├── Justfile.template                 the four-stage gate
    ├── tsconfig.json.template            note: include must list raycast-env.d.ts
    ├── eslint.config.mjs.template        flat config for @raycast/eslint-config v2
    ├── package.json.template             manifest skeleton, known-good deps
    ├── dev-check.ts.template             the no-test-runner harness
    ├── transport.ts.template             the Mutation data-union seam
    ├── error-descriptor.tsx.template     one descriptor, four renderers
    ├── metadata-README.md.template       makes "Save to Metadata" appear
    └── extension-icon.placeholder.png    512x512 — its sha256 is its own tripwire
```

## Three ideas the skill argues for

**Model mutations as a data union, not argv strings.** A `Mutation` type with one
variant per operation is what makes the transport a swappable seam. If `mutate()`
took a `string[]` of argv, a socket or HTTP transport would have to parse argv back
into intent — which is not a seam, it is a shell.

**There is no test runner, and adding one is store-review noise.** Keep every pure
module free of `@raycast/api` imports, and assert them from one `dev-check.ts`
compiled by the already-installed `tsc` and run under `node`. That import
discipline is the whole precondition — a barrel that pulls in the transport pulls
in `@raycast/api` with it, and then nothing is assertable.

**One error descriptor, N renderers.** A `structural` flag decides whether cached
data is a moment stale or a snapshot of a system nobody can reach; actions stay
data rather than JSX so the menu bar — which cannot render a `List.EmptyView` —
maps them to its own primitives instead of growing a second copy that drifts.

## Verification

The skill was built against the real toolchain, not from documentation:

```bash
# scaffold, then run every stage of the gate on the result
bash scripts/new-raycast-extension.sh --dir /tmp/trial --name trial --author me \
  --command tasks:view --command queue-menu:menu-bar --command quick:no-view
cd /tmp/trial && npm install
npx ray build && npx tsc --noEmit && npx ray lint    # all three exit 0
```

And the claim the skill rests on, reproduced:

```bash
npx ray lint;                              echo $?   # 0 — with metadata/ EMPTY
bash scripts/check-store-readiness.sh .;   echo $?   # 4 — names the screenshots
```

Adding three correctly-sized PNGs shrinks the failure list by exactly one id and
still reports `icon-not-placeholder`, which is how you know the checker
discriminates rather than merely counting files.

The canonical source is
[`SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/raycast-extension-dev/SKILL.md).
