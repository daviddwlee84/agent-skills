# ChordPro CLI: install, render, transpose, convert, validate

The official tool is a Perl program distributed on CPAN as
**`App::Music::ChordPro`**. Current 6.x releases install the **`chordpro`**
command (and `wxchordpro`, the GUI). Older releases also shipped a standalone
**`a2crd`** binary; in current versions the chords-over-lyrics importer is
`chordpro --a2crd` (verified against ChordPro core 6.101). Authoritative:
https://www.chordpro.org/chordpro/using-chordpro/ ,
https://www.chordpro.org/chordpro/chordpro-installation/ ,
https://metacpan.org/dist/App-Music-ChordPro.

> Version drift: the exact set of `--generate=` backends and `--diagrams=` values
> can vary by release. When unsure, check `chordpro --help` / `chordpro --manual`
> on the installed version rather than trusting this doc.

## Install (per platform)

- **macOS (CLI, recommended)** — there is **no official Homebrew formula**; use
  Homebrew's Perl + CPAN:
  ```bash
  brew install perl cpanminus
  cpanm App::Music::ChordPro
  ```
  If `chordpro` then fails with `Can't locate ChordPro.pm in @INC`, cpanm
  installed into a `local::lib` (`~/perl5`) that isn't on Perl's search path.
  Activate it once (and add to `~/.zshrc` to persist):
  ```bash
  eval "$(perl -I"$HOME/perl5/lib/perl5" -Mlocal::lib)"
  ```
  A GUI `.dmg` (macOS 10.15+) is on GitHub Releases but is only ad-hoc signed —
  read its bundled README. For the CLI, CPAN is the route.
- **Linux** — `cpanm App::Music::ChordPro` (canonical). Official package only for
  Fedora; an AppImage is also published on Releases.
- **Windows** — native installer from GitHub Releases, or Strawberry Perl +
  `cpanm App::Music::ChordPro`.
- **Anywhere (bootstrap)** — `curl -L https://cpanmin.us | perl - App::Music::ChordPro`.

No emphasized official Docker image; CPAN is the canonical cross-platform path.

## Render

Format is inferred from the output extension, or set explicitly with `--generate`.

```bash
chordpro -o song.pdf  song.cho                 # PDF (default backend)
chordpro --generate=HTML -o song.html song.cho # HTML (experimental)
chordpro --generate=Text -o song.txt  song.cho # plain text
chordpro --generate=ChordPro -o out.cho song.cho  # normalized round-trip
chordpro -o - song.cho                          # write to stdout
```

Available generators: **PDF** (default), **Text**, **ChordPro**, **HTML**
(experimental). A LaTeX backend has existed historically but is experimental —
prefer PDF/HTML.

Songbook with table of contents:

```bash
chordpro --toc -o Songbook.pdf songs/*.cho
chordpro --filelist=songlist.txt --toc -o Songbook.pdf
```

## Transpose + capo

```bash
chordpro -x 2   -o up.pdf   song.cho   # up 2 semitones
chordpro -x -3f -o down.pdf song.cho   # down 3, prefer flats
chordpro -x 1s  -o up.pdf   song.cho   # up 1, force sharps
chordpro --decapo -o out.pdf song.cho  # fold {capo} into the chords instead of printing a capo line
```

Suffix `s`/`f` forces sharp/flat spelling. There is also a per-song
`{transpose: +n}` directive (see the format reference).

## Convert chords-over-lyrics → ChordPro (`a2crd`)

`a2crd` is the **official importer** for legacy "chords on the line above the
lyrics" text (the Ultimate-Guitar / OnSong style). It heuristically classifies
each line as a chord line or a lyric line and merges them into inline `[..]`.

```bash
chordpro --a2crd input.txt                 # ChordPro to stdout (current 6.x path)
chordpro --a2crd input.txt -o song.cho
a2crd input.txt -o song.cho                # older releases shipped a standalone a2crd binary
```

In ChordPro 6.x the standalone `a2crd` command may not be installed — prefer
`chordpro --a2crd`. It auto-detects header lines (e.g. a title/attribution above
the first chord line becomes `{title:}`/`{subtitle:}`). `--a2crd` (ASCII → crd) is
**distinct** from `--generate=ChordPro` (reparse + re-emit an existing ChordPro
file). The heuristics are tunable (`pct_chords`, `classic`, etc. — see
https://www.chordpro.org/chordpro/chordpro-configuration-a2crd/); chord placement
is column-position based so output usually needs a light manual pass — **always
validate and eyeball** before rendering. See `assets/example-a2crd-input.txt` for
a ready-to-convert sample.

## Validate / normalize (the verify loop)

There's no dedicated `--lint`, but strict-mode parsing is the check:

```bash
chordpro --strict --generate=Text -o - song.cho   # exit 0 + no stderr warnings = valid
```

- **Strict mode** (default) enforces the standard and warns on unknown/malformed
  directives (stderr). `--no-strict` is lenient.
- **Normalize**: `chordpro --generate=ChordPro -o song.cho song.cho` reparses and
  re-emits canonical ChordPro — the practical way to clean up spacing/forms and
  to see how your input differs from canonical.
- `scripts/validate-cho.sh` wraps the strict-parse call and reports PASS/FAIL.

## Config + info

```bash
chordpro --config=layout.json -o song.pdf song.cho   # JSON config; repeatable, later wins
chordpro --no-default-configs --config=layout.json ...
chordpro --print-final-config                        # dump computed config, then exit
chordpro --about        # or -A
chordpro --version      # or -V
chordpro --help         # or -h ;  chordpro --manual
```

## Diagrams

Control global diagram output with `--diagrams=` (e.g. `all`, `none`) — confirm
accepted values against `chordpro --help` on the installed version. Per-chord
diagrams come from `{define}` (see `chordpro-format.md`).
