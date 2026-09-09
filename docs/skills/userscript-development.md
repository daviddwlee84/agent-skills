# userscript-development

Develop userscripts with explicit runtime and testing boundaries. This owned
skill is maintained in [Tampermonkey-Scripts](https://github.com/daviddwlee84/Tampermonkey-Scripts);
the collection distributes its copy under `skills/owned/userscript-development/`.
See [owned workflow](../workflows/adding-owned-skills.md) for updates.

## What it captures

| Experience | Skill guidance |
|---|---|
| A button vanishes after navigation | Idempotent reconciliation, target replacement, route invalidation |
| A title keeps acquiring prefixes | Observer callbacks are asynchronous; compare desired state before writing |
| Console succeeds, manager fails | Diagnose grants, sandbox, matching, injection permission and timing separately |
| Export includes its own panel or translated text | Clone and clean, isolate owned UI, retain the source snapshot |
| UI screenshots look right but output is wrong | Inspect clipboard text, downloaded files and partial-export reports |
| A userscript conflicts with site/native shortcuts | Test real keyboard input, Shadow DOM paths, IME and focus ownership |
| Chromium/Firefox fixtures pass | Report DOM/shim evidence separately from real-manager evidence |
| Native reference data agrees | Distinguish static-model agreement from loading the actual reference extension |

The main skill is 146 lines with six references, a runnable three-file test
example, and an output-ignore file. Detailed sources and corrected assumptions
live in its [provenance reference](https://github.com/daviddwlee84/Tampermonkey-Scripts/blob/main/.agents/skills/userscript-development/references/provenance.md).

Installed resources resolve from the loaded skill directory. Project commands,
dependencies and test outputs belong to the user's working project; the author's
checkout is not required. Source-specific commands remain in that project's
CLAUDE.md, while public source links provide optional attribution.

## Browser and extension testing

The skill covers installing browser binaries through the project's locked
Playwright, writing local HTML fixtures, injecting explicit GM shims in a known
order, exercising UI with Chromium and Firefox, and preserving screenshots and
actual output. On 2026-09-09, a real `skills@1.5.25 add --copy` installation in a
fresh project whose path contained spaces passed **6/6 tests** across both
engines. Playwright 1.62.1 was independently installed in that project, and the
copy/run instructions were executed directly from the installed reference.
Screenshots were inspected and all 11 installed skill files remained unchanged.

For real-manager tests, it explains bundled Chromium's persistent context,
isolated profiles, official extension artifacts, runtime ID discovery, permission
controls, and importing `.user.js` through the actual manager UI. Reference tests
compare extension alone, userscript alone, and coexistence on the same fixture.

This procedure draws from the source project's
[actual VM/TM + Vimium C validation](https://github.com/daviddwlee84/Tampermonkey-Scripts/blob/d7525d2/userscripts/vimium-c-companion/VALIDATION.md)
and inspected local experiments. Those historical results were reviewed, not
rerun during skill authoring. Firefox DOM tests are supported; the source's real
Firefox manager attempt did not establish successful userscript injection.

## Existing skills considered

Discovery used the skills.sh leaderboard, `skills@1.5.25 find userscript`, and
`find tampermonkey`, followed by upstream inspection. Counts below are a
2026-09-09 snapshot and do not establish correctness.

| Candidate | Discovery evidence | Decision |
|---|---|---|
| [henkisdabro tampermonkey](https://skills.sh/henkisdabro/wookstar-claude-plugins/tampermonkey) | 225 installs; GitHub repository 86 stars; SKILL.md and patterns inspected at `5091ecc` | `skipped` for vendoring: useful TM API reference, but the local project needs a compact cross-manager lifecycle and fixture/native-test workflow |
| [xixu-me develop-userscripts](https://skills.sh/xixu-me/skills/develop-userscripts) | 12 installs; directory description includes Tampermonkey/ScriptCat; GitHub API returned 404 | `evaluated` at listing level only; canonical source, stars and installability unverified |
| [andradeatdev userscript-creator](https://skills.sh/andradeatdev/skills/userscript-creator) | 1 install; GitHub API returned 404 | `wishlist`; content not evaluated and not recommended for installation yet |

The first candidate's inspected source is
[here](https://github.com/henkisdabro/wookstar-claude-plugins/blob/5091eccfb7cf09275f20fda850c190dff83be100/plugins/tampermonkey/skills/tampermonkey/SKILL.md).
Its manual install command is
`npx skills@1.5.25 add henkisdabro/wookstar-claude-plugins --skill tampermonkey`.
No external skill was installed or copied into this collection.

The new skill uses original wording and the owner's project evidence. Its added
value is specific failure modes and repeatable verification; it is not a generic
JavaScript tutorial. A controlled with/without-skill model benchmark has not been
run; `skill-creator` can evaluate output quality and triggering separately.

## Installation and maintenance

The canonical path is `.agents/skills/userscript-development/` in the source
project. The source is published and the owned entry tracks its upstream commit
in `vendor.yaml`. Install directly from the published source:

```bash
npx skills@1.5.25 add daviddwlee84/Tampermonkey-Scripts --skill userscript-development
```

After the collection's updated mirror is published, its grouped installation is:

```bash
npx skills@1.5.25 add daviddwlee84/agent-skills/skills --skill userscript-development
```

During local development, install from a local checkout or use the source
project's discovery directory. Edit the source project, not the owned mirror.
