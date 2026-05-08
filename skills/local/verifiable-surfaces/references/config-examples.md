# Config Verification Examples (Verification Mode)

Use these examples in **verification mode** — i.e. when an existing app, tool,
or config surface is being changed and you need to walk the verification
ladder. For **authoring mode** (designing new CLIs/tools/services so they are
verifiable in the first place), see `authoring-checklist.md`.

Prefer project-local commands when they exist (`make check-config`,
`npm run doctor`, `pytest tests/config`, `scripts/validate-config.sh`)
because they encode repo-specific load paths.

Official reference points:

- Ansible `ansible-playbook` CLI documents `--syntax-check`, `--check`,
  `--diff`, `--tags`, `--skip-tags`, and `--limit`:
  <https://docs.ansible.com/projects/ansible/latest/cli/ansible-playbook.html>
- Ansible check mode/diff mode docs describe dry-run style execution:
  <https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html>
- Chezmoi command docs cover `apply --dry-run --verbose`, `diff`, and
  `execute-template`:
  <https://www.chezmoi.io/reference/commands/>

## Generic App Or Tool Config

Start by finding the real load path:

```bash
rg -n "load.*config|config.*load|parse.*config|readFile|from_env|BaseSettings|argparse|click|tyro|commander|yargs" .
```

Then run, in order, the cheapest gates that apply:

```bash
# shape only
yamllint config.yml
python -m json.tool config.json >/dev/null

# app-native loader/checker
my-app config check --config config.yml
my-app --config config.yml --dry-run
my-app --print-config --config config.yml

# custom loader smoke
python - <<'PY'
from myapp.config import load_config
load_config("config.yml")
PY
```

If the app supports env vars, test with a minimal explicit env instead of the
agent's ambient shell:

```bash
env -i HOME="$(mktemp -d)" PATH="$PATH" MYAPP_CONFIG="$PWD/config.yml" \
  my-app config check
```

## Chezmoi And Dotfiles

Validate the generated/applied config, not only the template file:

```bash
chezmoi diff
chezmoi apply --dry-run --verbose
chezmoi execute-template < dot_gitconfig.tmpl
```

For runtime smoke, isolate `$HOME` when the tool supports it or when invoking a
consumer against rendered output:

```bash
tmp_home="$(mktemp -d)"
HOME="$tmp_home" git config --global --list
```

Do not run a real `chezmoi apply` to the user's home directory just to prove a
template compiles unless the user explicitly asked for it.

## Ansible

Treat syntax check as gate 1 only:

```bash
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml --check --diff --limit localhost
ansible-playbook site.yml --check --tags ssh_config --limit test-host
```

When a role is risky or host-specific, use the narrowest target that exercises
the changed task: localhost inventory, a disposable container/VM, Molecule, or
a role-specific test harness. If that is not available, report that execution
behavior remains untested.

## JavaScript And TypeScript Config

Use the tool's own config printer/debugger where available:

```bash
npm run typecheck -- --noEmit
npx eslint --print-config src/index.ts >/tmp/eslint-config.json
npx prettier --check .
npx tsc --showConfig >/tmp/tsconfig.rendered.json
npx next build
npx shadcn@latest info
```

For config modules (`next.config.ts`, `postcss.config.*`, `tailwind.config.*`),
a syntax check alone may miss plugin resolution, env-sensitive branches, or
runtime-only validation. Prefer the narrowest command that imports the config.

## Python CLI Or Settings Config

For argparse/click/tyro changes, verify both help text and parse/load behavior:

```bash
uv run python -m myapp --help
uv run python -m myapp --config config.toml --dry-run
```

For Pydantic settings or custom config loaders, run a small import/load smoke
with an isolated env:

```bash
env -i HOME="$(mktemp -d)" PATH="$PATH" \
  uv run python - <<'PY'
from myapp.settings import Settings
Settings()
PY
```

## Docker Compose

`docker compose config` renders and validates the merged Compose model:

```bash
docker compose config >/tmp/compose.rendered.yml
docker compose --env-file .env.example config >/tmp/compose.example.yml
docker compose up --dry-run  # when supported by the installed Compose version
```

If the failure mode depends on image startup, use a local disposable service
smoke with no production volumes or credentials.

## Kubernetes

Client-side YAML parsing is not enough. Use the strongest safe validator
available for the cluster access level:

```bash
kubectl apply --dry-run=client -f manifest.yml
kubectl apply --dry-run=server -f manifest.yml
kustomize build overlays/dev | kubectl apply --dry-run=client -f -
helm template release ./chart | kubectl apply --dry-run=client -f -
```

Server dry-run needs cluster access and can exercise admission/defaulting; do
not assume it is safe or available without checking context.

## Terraform Or OpenTofu

Run format/validate first, but use plan for semantic provider-level checks when
safe:

```bash
terraform fmt -check
terraform validate
terraform plan -out=/tmp/tfplan
terraform plan -refresh=false
```

Avoid plans against production workspaces unless the user explicitly requested
that environment. Prefer a local/example workspace or `-refresh=false` when the
goal is harmless config validation.

## Reporting Template

Use this concise summary after config validation:

```markdown
Validation:
- Syntax/schema: passed (`...`)
- Rendered/applied config: passed (`...`)
- App-native loader: passed (`...`)
- Runtime smoke: not run; requires <reason/environment>
```
