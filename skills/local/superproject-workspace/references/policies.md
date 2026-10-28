# Policies

Keys live in `.gitmodules` under the submodule's **name** (not path):

```bash
git config -f .gitmodules submodule.<name>.x-policy track   # track | pin | lazy
git config -f .gitmodules submodule.<name>.x-bump pr        # pr | direct | manual
git config -f .gitmodules submodule.<name>.x-tier core
git config -f .gitmodules submodule.<name>.branch main      # native git key
git config -f .gitmodules submodule.<name>.update none      # lazy children
```

## Choosing a policy

| Question about the child | Policy |
|---|---|
| You own it and the superproject should follow its main line | `track` |
| A specific version matters (deployed, released, a known-good reproduction) | `pin` |
| It's reference reading, a third-party upstream, or rarely used | `lazy` |
| You don't know yet | leave unset (treated as `pin`; `audit` reminds you) |

## Choosing a bump mode (`track` only)

| Mode | Use when | Risk |
|---|---|---|
| `manual` | Default. Bumps happen deliberately, alongside cross-repo work | Falls behind if nobody looks; `audit` shows `behind` |
| `pr` | You want a reviewable stream of updates (umbrellas, docs hubs) | PR noise; needs CI token for private children |
| `direct` | The pointer carries no review value (pure aggregation, notes repos) | A broken child lands in the outer default branch without review |

`direct` still runs preflight: a commit that is not reachable from
`origin/<branch>` is never recorded.

## Example: umbrella (every child follows main)

Parallel, equally owned repos, such as per-platform dotfiles:

```ini
[submodule "dotfiles-unix"]
    path = dotfiles-unix
    url = git@github.com:me/dotfiles.git
    branch = main
    x-policy = track
    x-bump = pr
[submodule "dotfiles-windows"]
    path = dotfiles-windows
    url = git@github.com:me/dotfiles-windows.git
    branch = main
    x-policy = track
    x-bump = pr
```

## Example: workspace hub (tiers)

```ini
[submodule "submodules/engine"]
    path = submodules/engine
    url = https://github.com/org/engine.git
    branch = release/2.x       # the baseline the pin follows
    x-policy = pin
    x-tier = core
[submodule "submodules/dashboard"]
    path = submodules/dashboard
    url = https://github.com/org/dashboard.git
    branch = main
    x-policy = track
    x-bump = manual
    x-tier = core
[submodule "submodules/references/someone/paper-code"]
    path = submodules/references/someone/paper-code
    url = https://github.com/someone/paper-code.git
    x-policy = lazy
    x-tier = reference
    update = none
```

`init --tier reference` fetches all references at once. `status --tier core`
narrows the report.

## Pins and branches

For a pin, `branch` names the line the pin follows, such as a release branch.
That is what `status` measures lag against. The safety rule for pins is
weaker than for track: the recorded commit must be on **some** origin branch,
so a fresh clone can check it out. It does not have to be on `branch`.
