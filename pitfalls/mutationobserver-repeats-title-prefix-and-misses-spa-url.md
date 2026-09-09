# MutationObserver repeats the title prefix or misses an SPA URL change

## Symptoms

- A bounded local fixture produced `[test] [test] [test] Page` despite an
  `applying = true` / DOM write / `applying = false` guard.
- `history.pushState({}, '', '/two')` changed `/one` to `/two`, while a body
  MutationObserver recorded **zero callbacks**.

## Root causes

MutationObserver callbacks run later through the microtask queue, after the
synchronous flag has reset. The flag does not express whether the desired DOM
state has already been achieved.

History updates need not mutate DOM. Comparing `location.href` only inside a DOM
observer therefore cannot detect every route change.

## Workaround and prevention

Compare the current value with the desired value before writing, so repeated
reconciliation is a no-op. Scope observations and schedule bounded work on
streaming pages. Use a verified route signal or an active-only URL comparison,
and recheck route identity before applying asynchronous results.

The local Chromium probe on 2026-09-09 capped the flag-only observer at three
callbacks to avoid an infinite loop. A prefix-equality guard produced one prefix
and one callback. The URL-only probe made no DOM changes. These are browser
pattern checks, not userscript-manager compatibility tests.

The original title script already had an equality check; its simplified tutorial
flag example did not. When extracting a skill, inspect the implementation and
test the invariant rather than copying the tutorial literally.

See the owned [userscript-development](../skills/owned/userscript-development/SKILL.md)
skill and [MDN microtasks](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide).
