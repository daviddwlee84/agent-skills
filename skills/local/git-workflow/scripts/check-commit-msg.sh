#!/usr/bin/env bash
# check-commit-msg.sh — validate Conventional Commit messages and the optional
# cross-harness agentic provenance contract.
#
# Bash 3.2 compatible (stock macOS).

set -euo pipefail

ALLOWED_TYPES="feat fix docs style refactor perf test build ci chore revert"

usage() {
  cat <<'EOF'
Usage: check-commit-msg.sh [OPTIONS] ["<message>"]
       printf 'feat: add x\n' | check-commit-msg.sh
       check-commit-msg.sh --agentic --staged --file .git/COMMIT_EDITMSG

Validate `<type>[(scope)][!]: <subject>`. Default mode checks the header only.
Agentic mode also requires an English description and a final Git trailer block:

  AI-Assisted-By: Codex CLI (gpt-5.6-sol)
  Agent-Transcript: .specstory/history/session.md
  Agent-Plan: .claude/plans/plan.md

Options:
  --file PATH          Read the message from PATH instead of arg/stdin.
  --agentic            Enforce body + canonical AI provenance trailers.
  --staged             Cross-check transcript/plan trailers against the index.
                       Requires --agentic and must run inside the target repo.
  --allow-no-body      Agentic escape hatch for a genuinely trivial commit.
  --types              Print the allowed commit types and exit.
  --help, -h           Show this help and exit.

Agentic messages reject CJK/Hangul in the human-written header/body. Tool-native
metadata (Generated-with, Co-Authored-By, cryptographic signatures) is allowed;
place the canonical fields in the final trailer block so git can parse them.

Output (stdout): one JSON object describing the validation result.

Exit codes:
  0  valid
  1  validation failed (reason on stderr)
  2  bad arguments / missing input / wrong repository context
EOF
}

log()  { printf '%s\n' "$*" >&2; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

FILE=""
ARG_MSG=""
HAVE_ARG=0
AGENTIC=0
CHECK_STAGED=0
ALLOW_NO_BODY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --file)
      shift
      [ $# -gt 0 ] || die "--file needs a path (try --help)" 2
      FILE="$1"; shift ;;
    --agentic) AGENTIC=1; shift ;;
    --staged) CHECK_STAGED=1; shift ;;
    --allow-no-body) ALLOW_NO_BODY=1; shift ;;
    --types)
      for allowed_type in $ALLOWED_TYPES; do printf '%s\n' "$allowed_type"; done
      exit 0 ;;
    --help|-h) usage; exit 0 ;;
    --) shift; if [ $# -gt 0 ]; then ARG_MSG="$1"; HAVE_ARG=1; shift; fi ;;
    -*) die "unknown flag: $1 (try --help)" 2 ;;
    *)  ARG_MSG="$1"; HAVE_ARG=1; shift ;;
  esac
done

[ "$CHECK_STAGED" = "0" ] || [ "$AGENTIC" = "1" ] || \
  die "--staged requires --agentic" 2
[ "$ALLOW_NO_BODY" = "0" ] || [ "$AGENTIC" = "1" ] || \
  die "--allow-no-body requires --agentic" 2

msg=""
if [ -n "$FILE" ]; then
  [ -f "$FILE" ] || die "file not found: $FILE" 2
  msg="$(cat "$FILE")"
elif [ "$HAVE_ARG" = "1" ]; then
  msg="$ARG_MSG"
elif [ ! -t 0 ]; then
  msg="$(cat)"
else
  die "no message provided (pass an argument, --file PATH, or pipe via stdin)" 2
fi

clean_msg="$(printf '%s\n' "$msg" | sed '/^[[:space:]]*#/d')"
header=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  header="$line"
  break
done <<EOF
$clean_msg
EOF
[ -n "$header" ] || die "empty commit message" 2

types_re="$(printf '%s' "$ALLOWED_TYPES" | tr ' ' '|')"
if ! printf '%s' "$header" | grep -Eq "^(${types_re})(\([a-z0-9][a-z0-9._/-]*\))?!?: .+"; then
  if ! printf '%s' "$header" | grep -Eq '^[a-z]+(\(|!|:)'; then
    log "invalid: header must start with a lowercase type, e.g. 'feat: ...'"
  elif ! printf '%s' "$header" | grep -Eq "^(${types_re})"; then
    log "invalid: unknown type. Allowed: ${ALLOWED_TYPES}"
  elif ! printf '%s' "$header" | grep -Eq ': .+'; then
    log "invalid: missing ': <subject>' after the type/scope"
  else
    log "invalid: does not match '<type>[(scope)][!]: <subject>'"
  fi
  printf '{"valid":false,"header":"%s"}\n' "$(printf '%s' "$header" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  exit 1
fi

type="$(printf '%s' "$header" | sed -E 's/^([a-z]+).*/\1/')"
scope=""
if printf '%s' "$header" | grep -Eq '^[a-z]+\('; then
  scope="$(printf '%s' "$header" | sed -E 's/^[a-z]+\(([a-z0-9._/-]+)\).*/\1/')"
fi
breaking=false
printf '%s' "$header" | grep -Eq '^[a-z]+(\([a-z0-9._/-]+\))?!:' && breaking=true
subject="$(printf '%s' "$header" | sed -E 's/^[a-z]+(\([a-z0-9._/-]+\))?!?: //')"

if [ "${#header}" -gt 72 ]; then warn "header is ${#header} chars (aim for <=72)"; fi
case "$subject" in [A-Z]*) warn "subject starts with a capital ('$subject') — prefer lowercase imperative" ;; esac
case "$subject" in *.) warn "subject ends with a period — drop it" ;; esac

assistant_count=0
transcript_count=0
plan_count=0

contains_line() {
  local needle="$1" haystack="$2"
  while IFS= read -r candidate; do
    [ "$candidate" = "$needle" ] && return 0
  done <<EOF
$haystack
EOF
  return 1
}

count_duplicates() {
  local values="$1"
  [ -n "$values" ] || { printf '0'; return; }
  printf '%s\n' "$values" | sed '/^$/d' | sort | uniq -d | wc -l | tr -d ' '
}

if [ "$AGENTIC" = "1" ]; then
  trailers="$(printf '%s\n' "$clean_msg" | git interpret-trailers --parse)"
  assistants="$(printf '%s\n' "$trailers" | sed -n 's/^AI-Assisted-By:[[:space:]]*//p')"
  transcripts="$(printf '%s\n' "$trailers" | sed -n 's/^Agent-Transcript:[[:space:]]*//p')"
  plans="$(printf '%s\n' "$trailers" | sed -n 's/^Agent-Plan:[[:space:]]*//p')"

  [ -n "$assistants" ] || die "agentic commit needs AI-Assisted-By in the final trailer block" 1
  while IFS= read -r assistant; do
    [ -n "$assistant" ] || continue
    assistant_count=$((assistant_count + 1))
    printf '%s' "$assistant" | grep -Eq '^.+ \(.+\)$' || \
      die "invalid AI-Assisted-By value '$assistant' (expected 'Harness (model)')" 1
    if printf '%s' "$assistant" | grep -Eqi '(^|[ (])(unknown|unspecified|n/a)([ )]|$)'; then
      die "AI-Assisted-By must name a real harness and model, not '$assistant'" 1
    fi
  done <<EOF
$assistants
EOF

  transcript_count="$(printf '%s\n' "$transcripts" | sed '/^$/d' | wc -l | tr -d ' ')"
  plan_count="$(printf '%s\n' "$plans" | sed '/^$/d' | wc -l | tr -d ' ')"
  [ "$(count_duplicates "$assistants")" = "0" ] || die "duplicate AI-Assisted-By trailer" 1
  [ "$(count_duplicates "$transcripts")" = "0" ] || die "duplicate Agent-Transcript trailer" 1
  [ "$(count_duplicates "$plans")" = "0" ] || die "duplicate Agent-Plan trailer" 1

  body_found=0
  human_text="$header"
  skipped_header=0
  while IFS= read -r line; do
    if [ "$skipped_header" = "0" ]; then
      [ -z "$line" ] && continue
      skipped_header=1
      continue
    fi
    [ -z "$line" ] && continue
    case "$line" in
      "Generated with "*|"🤖 Generated with "*) continue ;;
      "BREAKING CHANGE: "*) continue ;;
    esac
    if printf '%s' "$line" | grep -Eq '^[A-Za-z][A-Za-z0-9-]*:[[:space:]]+'; then
      continue
    fi
    body_found=1
    human_text="${human_text}\n${line}"
  done <<EOF
$clean_msg
EOF

  if [ "$ALLOW_NO_BODY" = "0" ] && [ "$body_found" = "0" ]; then
    die "non-trivial agentic commit needs an English body (use --allow-no-body only when truly trivial)" 1
  fi

  set +e
  printf '%b\n' "$human_text" | grep -Eq '[一-龥ぁ-んァ-ヶ가-힣]' 2>/dev/null
  language_rc=$?
  set -e
  if [ "$language_rc" = "0" ]; then
    die "agentic commit header/body must be English (CJK/Hangul text detected)" 1
  elif [ "$language_rc" -gt 1 ]; then
    warn "could not run the UTF-8 language check in this locale"
  fi

  if [ "$CHECK_STAGED" = "1" ]; then
    git rev-parse --show-toplevel >/dev/null 2>&1 || \
      die "--staged must run inside the target git repository" 2

    staged_transcripts=""
    staged_plans=""
    while IFS= read -r -d '' path; do
      case "$path" in
        .specstory/history/*.md)
          staged_transcripts="${staged_transcripts}${staged_transcripts:+$'\n'}${path}" ;;
        .claude/plans/*.md|.cursor/plans/*.md|.opencode/plans/*.md|.specify/*.md|.codex/*.md)
          staged_plans="${staged_plans}${staged_plans:+$'\n'}${path}" ;;
      esac
    done < <(git diff --cached --name-only --diff-filter=ACMR -z)

    while IFS= read -r path; do
      [ -n "$path" ] || continue
      contains_line "$path" "$transcripts" || \
        die "staged transcript missing from trailers: $path" 1
    done <<EOF
$staged_transcripts
EOF
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      contains_line "$path" "$plans" || die "staged plan missing from trailers: $path" 1
    done <<EOF
$staged_plans
EOF
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      case "$path" in /*|../*|*/../*) die "Agent-Transcript must be repo-relative: $path" 1 ;; esac
      contains_line "$path" "$staged_transcripts" || \
        die "Agent-Transcript does not name a staged transcript: $path" 1
    done <<EOF
$transcripts
EOF
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      case "$path" in /*|../*|*/../*) die "Agent-Plan must be repo-relative: $path" 1 ;; esac
      contains_line "$path" "$staged_plans" || \
        die "Agent-Plan does not name a staged plan: $path" 1
    done <<EOF
$plans
EOF
  fi
fi

bnote=""
[ "$breaking" = "true" ] && bnote=" breaking=true"
agentic_note=""
[ "$AGENTIC" = "1" ] && agentic_note=" agentic=true"
log "valid: type=${type}${scope:+ scope=${scope}}${bnote}${agentic_note}"
printf '{"valid":true,"type":"%s","scope":"%s","breaking":%s,"agentic":%s,"assistants":%s,"transcripts":%s,"plans":%s}\n' \
  "$type" "$scope" "$breaking" \
  "$([ "$AGENTIC" = "1" ] && printf true || printf false)" \
  "$assistant_count" "$transcript_count" "$plan_count"
