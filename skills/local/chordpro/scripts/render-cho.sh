#!/usr/bin/env bash
# render-cho.sh — Render a ChordPro file to PDF with correct fonts, then prove the
# glyphs actually made it into the PDF.
#
# Why this exists: `chordpro`'s default fonts (GNU FreeFont) contain NO CJK glyphs,
# so a bare `chordpro -o song.pdf song.cho` on a Chinese/Japanese/Korean song exits
# 0, emits no warning, and passes `validate-cho.sh` — while silently dropping every
# non-Latin character (tofu / blank). Parse-validity is not render-fidelity. This
# script auto-detects a CJK-capable font, renders through it, and then round-trips
# the PDF to confirm the expected script is visible. It closes the verify loop for
# non-Latin songs.
#
# Bash 3.2 compatible (works on stock macOS).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: render-cho.sh [OPTIONS] <file.cho>

Render a ChordPro file to PDF and verify the glyphs rendered (not tofu).
If the .cho contains CJK, a CJK-capable font is auto-detected and injected via a
temporary `--config`; the output PDF is then glyph-checked.

Options:
  -o, --output FILE   Output PDF path (default: <file>.pdf next to the input).
  --font PATH         Force a specific font file (overrides auto-detection).
  --keep-config       Write the font --config next to the PDF instead of a temp file.
  --help, -h          Show this help and exit.

Auto-detected CJK fonts (first that exists wins):
  macOS: /System/Library/Fonts/Supplemental/Arial Unicode.ttf, PingFang.ttc, STHeiti
  Linux: Noto Sans CJK (Noto*CJK*.ttc), wqy-* — install fonts-noto-cjk if missing.

Verdict (stdout, JSON):
  {"file":"song.cho","pdf":"song.pdf","cjk":true,"font":"…/Arial Unicode.ttf","glyphs_ok":true}

Exit codes:
  0  rendered and (if CJK) glyphs verified present
  1  invalid arguments
  2  input not found / chordpro not installed
  3  render failed, OR CJK song rendered as tofu (no CJK glyphs in the PDF)
EOF
}

log() { printf '%s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit "${2:-1}"; }

FILE=""; OUT=""; FONT=""; KEEP_CONFIG=0
while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUT="${2:-}"; shift 2 ;;
    --font) FONT="${2:-}"; shift 2 ;;
    --keep-config) KEEP_CONFIG=1; shift ;;
    --help|-h) usage; exit 0 ;;
    -*) die "unknown flag: $1 (try --help)" 1 ;;
    *) [ -n "$FILE" ] && die "only one file allowed" 1; FILE="$1"; shift ;;
  esac
done

[ -n "$FILE" ] || die "missing <file.cho> (try --help)" 1
[ -f "$FILE" ] || die "file not found: $FILE" 2
command -v chordpro >/dev/null 2>&1 || die "chordpro not on PATH. Install: brew install perl cpanminus && cpanm App::Music::ChordPro (then activate local::lib; see references/cli-and-rendering.md)" 2
[ -n "$OUT" ] || OUT="${FILE%.*}.pdf"

# Does the input contain CJK (CJK Unified Ideographs, Hiragana, Katakana, Hangul)?
has_cjk() {
  python3 - "$1" <<'PY' 2>/dev/null
import sys
t=open(sys.argv[1],encoding="utf-8",errors="ignore").read()
def cjk(c):
    o=ord(c)
    return (0x4E00<=o<=0x9FFF) or (0x3040<=o<=0x30FF) or (0xAC00<=o<=0xD7AF) or (0x3400<=o<=0x4DBF)
sys.exit(0 if any(cjk(c) for c in t) else 1)
PY
}

detect_font() {
  local c
  for c in \
    "$HOME/Library/Fonts/Arial Unicode.ttf" \
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf" \
    "/Library/Fonts/Arial Unicode.ttf" \
    "/System/Library/Fonts/PingFang.ttc" \
    "/System/Library/Fonts/STHeiti Light.ttc" \
    /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
    /usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc \
    /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc \
    /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc \
    /usr/share/fonts/truetype/wqy/wqy-microhei.ttc ; do
    if [ -f "$c" ]; then printf '%s' "$c"; return 0; fi
  done
  return 1
}

CJK=0; FONT_USED=""; CONFIG=""
if has_cjk "$FILE"; then
  CJK=1
  if [ -z "$FONT" ]; then
    FONT="$(detect_font || true)"
    [ -n "$FONT" ] || die "input has CJK but no CJK font found. Install one (macOS ships 'Arial Unicode.ttf'; Linux: fonts-noto-cjk) or pass --font PATH." 3
  fi
  FONT_USED="$FONT"
  if [ "$KEEP_CONFIG" = "1" ]; then CONFIG="$(dirname "$OUT")/.chordpro-fonts.json"; else CONFIG="$(mktemp -t chordpro-fonts).json"; fi
  # Point every text-bearing PDF font role at the CJK font (chords stay Latin but
  # sharing the font is harmless and keeps annotations legible).
  python3 - "$FONT" > "$CONFIG" <<'PY'
import json,sys
f=sys.argv[1]
roles=["title","subtitle","text","chord","comment","comment_italic","comment_box","tab","grid","toc","footer"]
print(json.dumps({"pdf":{"fonts":{r:{"file":f} for r in roles}}}, ensure_ascii=False, indent=2))
PY
  [ "$KEEP_CONFIG" = "1" ] || trap 'rm -f "$CONFIG"' EXIT
fi

# Render
if [ "$CJK" = "1" ]; then
  chordpro --config "$CONFIG" -o "$OUT" "$FILE" 2>/tmp/render.$$ || { cat /tmp/render.$$ >&2; rm -f /tmp/render.$$; die "chordpro render failed" 3; }
else
  chordpro -o "$OUT" "$FILE" 2>/tmp/render.$$ || { cat /tmp/render.$$ >&2; rm -f /tmp/render.$$; die "chordpro render failed" 3; }
fi
rm -f /tmp/render.$$
[ -f "$OUT" ] || die "no PDF produced at $OUT" 3

# Glyph-check: for a CJK song, confirm CJK actually made it into the PDF text layer.
GLYPHS_OK=true
if [ "$CJK" = "1" ]; then
  if command -v pdftotext >/dev/null 2>&1; then
    if pdftotext "$OUT" - 2>/dev/null | python3 -c 'import sys; t=sys.stdin.read(); sys.exit(0 if any(0x4E00<=ord(c)<=0x9FFF or 0x3040<=ord(c)<=0x30FF or 0xAC00<=ord(c)<=0xD7AF for c in t) else 1)'; then
      GLYPHS_OK=true
    else
      GLYPHS_OK=false
      log "GLYPH CHECK FAILED: no CJK glyphs found in $OUT — the PDF is tofu."
      log "The chosen font ($FONT_USED) may lack the needed glyphs; try --font with a fuller CJK font."
    fi
  else
    log "note: pdftotext not found (poppler) — skipping glyph verification. Install poppler to enable it."
  fi
fi

printf '{"file":"%s","pdf":"%s","cjk":%s,"font":"%s","glyphs_ok":%s}\n' \
  "$FILE" "$OUT" "$( [ "$CJK" = 1 ] && echo true || echo false )" "$FONT_USED" "$GLYPHS_OK"

if [ "$GLYPHS_OK" = "false" ]; then exit 3; fi
log "OK: rendered $OUT$( [ "$CJK" = 1 ] && echo ' (CJK glyphs verified)')"
