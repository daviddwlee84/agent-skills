# Playwright times out on Mermaid SVG even though the Zensical diagram is visible

## Symptom

With Zensical 0.0.73, both `pre.mermaid svg` and `.mermaid svg` timed out in
Playwright. The visible host serialized as `<div class="mermaid"></div>` and
`element.shadowRoot` returned `null`, despite a rendered diagram and nonzero height.

## Root cause

The native Mermaid integration replaces the source block with a host using a
**closed shadow root**. A Chromium DevTools Protocol inspection confirmed
`shadowRootType: "closed"`. Ordinary DOM selectors, including Playwright's
open-shadow traversal, cannot inspect its SVG descendants.

## Workaround

Wait for the `.mermaid` host to be visible and have nonzero dimensions, then
capture and visually inspect that host. Select the site's actual light/dark
palette when testing each mode. For precise DOM diagnostics in Chromium, use a
CDP `DOM.getDocument` request with `pierce: true`; do not change application
encapsulation just to make a selector pass.

## Prevention

Do not infer a missing diagram from `shadowRoot === null` or an SVG-selector
timeout. Verify the source fence and generated HTML, browser console/network,
and the rendered host. Layout still needs a visual check; host dimensions alone
do not prove the flowchart is correct.
