#!/usr/bin/env bash
# Refresh data/disposable_domains.txt from upstream blocklist.
# Run quarterly (March / June / September / December) or whenever upstream
# bumps. Prints a diff against the previous version.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
DATA_FILE="$HERE/data/disposable_domains.txt"
TMP_RAW="$(mktemp)"
TMP_NEW="$(mktemp)"
trap 'rm -f "$TMP_RAW" "$TMP_NEW"' EXIT

URL="https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf"

echo "Fetching: $URL"
curl -fsSL "$URL" > "$TMP_RAW"

echo "Normalizing (lowercase + dedupe + sort)..."
{
  printf "# Source: https://github.com/disposable-email-domains/disposable-email-domains\n"
  printf "# Refreshed: %s\n" "$(date -u +%Y-%m-%d)"
  printf "# One domain per line. Lines starting with # are comments.\n"
  printf "\n"
  tr '[:upper:]' '[:lower:]' < "$TMP_RAW" | sort -u | grep -v '^$'
} > "$TMP_NEW"

if [[ -f "$DATA_FILE" ]]; then
    echo "--- Diff with previous ---"
    diff -u "$DATA_FILE" "$TMP_NEW" | head -40 || true
    OLD=$(wc -l < "$DATA_FILE")
    NEW=$(wc -l < "$TMP_NEW")
    echo "Lines: $OLD → $NEW"
fi

mv "$TMP_NEW" "$DATA_FILE"
echo "Wrote: $DATA_FILE"
echo
echo "Next: review the diff, then commit:"
echo "  git diff $DATA_FILE"
echo "  git commit -m 'chore(email-hygiene): refresh disposable list YYYY-MM'"
