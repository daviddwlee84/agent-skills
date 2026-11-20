# Visual design

Read when a screen is being laid out, restyled, or described as plain, flat,
"just text", or hard to scan. Behavior can be correct while the screen is still
a wall of same-colored text; this reference covers the visual layer that the
interaction rules assume. Preserve an existing app's established look unless
the task is to change it.

## Contents

- [Hierarchy before decoration](#hierarchy-before-decoration)
- [One semantic theme](#one-semantic-theme)
- [Panes, lists, and details](#panes-lists-and-details)
- [Footer, help, and modals](#footer-help-and-modals)
- [Forms and wizards](#forms-and-wizards)
- [Mouse by default](#mouse-by-default)
- [Anti-patterns](#anti-patterns)
- [Visual acceptance](#visual-acceptance)
- [Sources](#sources)

## Hierarchy before decoration

Give every screen five distinguishable layers, then style each consistently:

| Layer | Typical treatment |
|---|---|
| Chrome | Rounded borders, titles inset in the top border, counts in tabs/titles |
| Primary content | Default foreground; names and values bold where they are the answer |
| Secondary content | Muted: hints, keys of key/value pairs, timestamps, column headers |
| State | Semantic colors plus a shape: `✓ ! ✗`, `● ◐ ○`, threshold-colored meters |
| Focus | Accent: focused pane border and title, active tab chip, option cursor |

Sketch the screen as an ASCII mockup with these layers marked before writing
widgets (the compact interaction contract's Layout row). If two adjacent
elements would render with the same weight and color, the user has to read
both to tell them apart: change one.

## One semantic theme

Define roles once (accent, muted, ok, warn, err, info, pending, selection,
focused/unfocused border, button) in a small theme value and pass it to every
view. Views ask for a role, never a color number. The same theme serves the
dashboard, forms, and plain progress output, so the app looks like one tool.

- Base foreground roles on the 16 ANSI colors. The terminal theme then picks the
  actual RGB values and keeps light and dark backgrounds readable.
- Chips (app badge, active tab, focused button) need a guaranteed contrast. A
  fixed white or black foreground fails on some themes; reverse video of an
  ANSI accent makes the text take the terminal's own background color.
- A selected row keeps its segments' status colors, so its background must be a
  subtle tint chosen for the background brightness. In Bubble Tea v2, request
  it with `tea.RequestBackgroundColor`, handle `tea.BackgroundColorMsg.IsDark()`,
  and pick colors with `lipgloss.LightDark`; assume dark until the answer
  arrives. Short-lived programs that would exit before the reply can skip the
  query and avoid background-dependent styles.
- With color off (`--color never`, `NO_COLOR` in auto mode, non-terminal output)
  return plain styles that emit no SGR sequences, and keep structure: borders,
  `▌`, `›`, `●/○`, `[x]`, bracketed focused buttons, `[active tab]`. Give the
  bracketed and unbracketed forms the same width so focus never shifts layout.

## Panes, lists, and details

- Draw panes as boxes with the title in the top border and an optional status
  in the bottom border (`3/12`, `↓ more`, `↑65 · following`). The focused pane's
  border and title use the accent; others use the muted border.
- Lists get a muted column header, aligned columns sized from the measured
  pane width, and a priority order for dropping columns when narrow. Move
  low-value columns (transport details, IDs) to the detail pane before
  truncating names.
- Render the selected row segment by segment, adding the selection background
  to each segment. Stripping ANSI and then reversing the row erases the status
  colors the user scans for. Show focus separately from selection: in an
  unfocused list keep only a gutter marker (`▌`) and bold text.
- Details: muted keys, default values, accent section headings, and
  threshold-colored meters (`████░░░░`). Show timestamps as `3m ago · Jan 2
  15:04:05` instead of raw RFC 3339.
- Logs and other growing text: pin a short header (identity, state) and scroll
  the rest; follow the tail until the user scrolls up, resume at the bottom,
  and say which mode is active in the border.
- Empty states are styled too: a bold one-line statement and a muted next step
  with the key emphasized.

## Footer, help, and modals

- Footer hints render the key in the accent and the label muted. Keep `? help`
  and quit right-aligned and always visible; drop whole hints from the end
  rather than cutting one in half. Labels follow the current context
  (`select` in a list, `scroll` in a detail pane).
- A status line names its kind with an icon and color: `✓` ok, `✗` error, `…`
  pending, `·` info. Retain the message until something replaces it.
- Help and confirmations are centered modals over a dimmed base (strip the
  base's colors and render it muted). Destructive confirmations use the error
  color for the border, name the target, and focus the safe button.
- Lip Gloss v2 has `Canvas`, `Layer`, and `Compositor` for compositing; a
  line splice with `ansi.Cut` over a stripped base is enough for one modal.
  Check the pinned version with `go doc` before choosing either.

## Forms and wizards

Users must tell the question, its explanation, the answer, the choices, and the
cursor apart at a glance:

```text
 Hub on my-vps                                   ← title: accent
 Ubuntu 24.04 · 4 CPU · 7.8 GiB                  ← description: muted
   Hub name *            my-vps                  ← collapsed: label + bold value
 ┃ Network                                       ← focused: accent bar + label
 ┃ How workers reach this hub                    ← help: muted
 ┃ › ● public — reachable from the Internet      ← cursor ›, chosen ●
 ┃   ○ private — only on my network              ← detail after — is muted
 ┃ ✗ Network is required                         ← error inside the block
   [ Review ⌃S ]   Back Esc                3 / 7 ← primary + secondary buttons
 ↑↓ choose · Enter next · Tab field · / search   ← context keys, bottom line
```

- Focus, option cursor, and chosen value each get their own marker. One `>`
  meaning both "focused field" and "selected option" is the most common source
  of "I can't tell what is selected".
- Collapse unfocused fields to one aligned `label value` line; expand only the
  focused one with help and editor. Required-but-empty values show `required`
  in the error color in their collapsed line.
- Place buttons right after the fields, not at the bottom of a tall terminal;
  keep the key hints on the last line. The primary action is accent-colored
  even before it has focus; the focused button is a chip with brackets.
- Review screens: put the plan in a bordered viewport with its scroll position
  in the border, wrap long commands with a hanging indent, and highlight only
  shapes the renderer produces (numbered steps, `[host]` tags, privileged
  markers, warnings). Default focus stays on Back/Cancel.

## Mouse by default

Dashboards and forms capture the mouse by default (Bubble Tea v2:
`tea.View.MouseMode = tea.MouseModeCellMotion`, set on every frame). Click tabs,
rows, fields, choices, and buttons; the wheel scrolls the pane or modal under
the pointer. See [interaction-design.md](interaction-design.md#mouse-interaction)
for press/release and modal rules.

Capture takes away the terminal's own drag-to-select, so give it back:

- A toggle key (for example `M`) and a config opt-out restore native selection;
  the help says that most terminals still select with Shift- or Option-drag.
- Offer in-app copying where users copy most (logs, details, URLs): drag over a
  pane to mark whole lines, copy the untruncated plain text on release through
  `tea.SetClipboard` (OSC 52, also over SSH where the terminal allows it) and a
  local clipboard tool, and confirm in the status line. A plain click must not
  copy. A `y` key copies the whole current item.
- Isolate clipboard tools in tests (fake `pbcopy`/`xclip` on `PATH`) so test
  runs never overwrite the developer's clipboard.

## Anti-patterns

- A wall of default-colored text; color used only for errors.
- Raw color numbers scattered through view code instead of theme roles.
- `ansi.Strip` followed by reverse video on the selected row.
- The same marker for focus, cursor, and selection.
- Chip text in fixed white/black on an ANSI background color.
- Mouse capture never enabled, or enabled with no way back to text selection.
- Spacing by bytes or runes; truncation that cuts a hint or a grapheme.
- Buttons pinned to the bottom of a mostly empty screen, far from the fields.

## Visual acceptance

- Render each screen at 80×24 and a wide size, in a dark theme, a light theme,
  and with color off; look at the images (see
  [verification.md](verification.md#visual-review)).
- Each layer in the table above is distinguishable; focus, cursor, selection,
  and state are visible without color.
- The selected row keeps status colors; chips are readable in both themes.
- No line exceeds the width at any size, including tiny resizes.

## Sources

Reviewed 2026-11-21. Treatments above are this skill's preferences.

- Lazygit [Config.md at 54cc6af](https://github.com/jesseduffield/lazygit/blob/54cc6af1d77b5a6cec3dc9ad0b203afdb4ad3451/docs/Config.md):
  defaults include `mouseEvents: true` (with a note that selecting text then
  needs Option on macOS), `border: rounded`, a green bold active border, blue
  key hints, and a selected-line background chosen from the terminal's
  background brightness.
- Bubble Tea v2.0.9 and Lip Gloss v2.0.6 APIs (`tea.View.MouseMode`,
  `tea.RequestBackgroundColor`, `tea.BackgroundColorMsg`, `tea.SetClipboard`,
  `lipgloss.LightDark`, `Canvas`/`Layer`) were checked with `go doc` in a
  module pinned to those versions.
- [NO_COLOR](https://no-color.org/): disables color, not layout or markers.
