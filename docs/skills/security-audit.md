# security-audit (vendored)

Vendored from Cloudflare's
[`cloudflare/security-audit-skill/skills/security-audit`](https://github.com/cloudflare/security-audit-skill/tree/main/skills/security-audit)
skill under MIT. It is the single-repo starting point behind Cloudflare's
vulnerability discovery harness (see
[Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)).
It is synchronized through `vendor.yaml`, and `license_path: LICENSE` copies
the repo-root license into `LICENSE.txt`. Do not edit the vendored files locally
because `make sync` replaces them.

## What it teaches

The skill makes an agent a defensive, source-first security reviewer. A
finding counts only if it crosses a real trust boundary: the agent must name the
lower-trust principal, the input, the control that was bypassed, the affected
resource, and the observed result. It then recommends the smallest source fix
that closes the hole.

It has two operating modes:

- **Guidance mode** (default) is for security questions, focused reviews, and
  triage. The agent uses only the relevant parts and writes no audit files.
- **Full audit mode** runs only when the user explicitly asks for an audit, a
  pen test, a comprehensive review, or report artifacts. It has six phases:
  reconnaissance, coverage-led hunting waves, candidate validation, structured
  `findings.json`, independent record verification, and a target-neutral
  report. Output goes outside the target, by default under
  `~/security-audit-skill/<repo>/run-<N>`.

## Safety model

Reading source is always allowed. Target code may run only inside an OS-enforced
sandbox with no external network, an allowlisted environment, a read-only target,
and hard resource limits. If the sandbox cannot be enforced, the agent does not
execute code and records a `needs_validation` blocker. The skill forbids probing
deployed endpoints, shared infrastructure, or live identities.

## Bundled files

| File | Purpose |
|---|---|
| `RECONNAISSANCE.md`, `HUNTING.md`, `VALIDATION-AND-REPORTING.md` | Phase instructions and sub-agent prompts |
| `ATTACK-CLASSES.md` + 10 domain companions | Hunting classes for web/auth, client-side, AI/LLM, memory safety, supply chain, cloud, RPC, resource exhaustion, data isolation, and desktop/mobile IPC |
| `report-schema.json` | Schema for `confirmed` / `needs_validation` / `rejected` records |
| `validate-findings.cjs`, `validate-coverage-ledger.cjs` | Zero-dependency Node validators, plus their `*.test.cjs` suites |

The validators need only Node. To check a synced copy, run
`node --test validate-findings.test.cjs validate-coverage-ledger.test.cjs`
from the skill directory.

## Canonical SKILL.md

See
[`skills/vendor/security-audit/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/security-audit/SKILL.md)
for the full instructions.
