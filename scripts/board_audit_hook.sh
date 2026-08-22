#!/usr/bin/env bash
# Stop-hook wrapper around board_audit.py.
#
# The audit is the check on the agent that just wrote to the board, so it runs at the
# end of the session that could have caused the drift. Two things keep it cheap:
# it is declared async in settings.json (session exit never waits on it), and it
# throttles itself so a run of short sessions does not re-audit every few minutes.
#
# Report lands in .claude/board-audit.log (gitignored via *.log).

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT="$REPO/.claude/board-audit.log"
THROTTLE_SECONDS=1800

mkdir -p "$(dirname "$REPORT")"

# Skip when a report is already fresh — nothing meaningful drifts in 30 minutes.
if [ -f "$REPORT" ]; then
  age=$(( $(date +%s) - $(stat -c %Y "$REPORT" 2>/dev/null || echo 0) ))
  if [ "$age" -lt "$THROTTLE_SECONDS" ]; then
    exit 0
  fi
fi

command -v gh >/dev/null 2>&1 || exit 0
gh auth status >/dev/null 2>&1 || exit 0

output=$(cd "$REPO" && python3 scripts/board_audit.py 2>&1)
status=$?

{
  echo "# board audit — $(date -Iseconds)"
  echo "$output"
} > "$REPORT"

if [ "$status" -ne 0 ]; then
  count=$(printf '%s\n' "$output" | grep -c '^  \[' || true)
  printf '{"systemMessage":"Board audit: %s finding(s) — see .claude/board-audit.log","suppressOutput":true}\n' \
    "$count"
fi

exit 0
