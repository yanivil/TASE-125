#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_daily.sh — Automated daily runner for TASE swing scanner
#
# Schedule: Monday through Friday at 21:00 Israel Time
# Excludes: Saturday and Sunday
# Output:   Writes new markdown and CSV files under ./out/
# ---------------------------------------------------------------------------
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 1) Check day of week: 1 = Monday, 5 = Friday, 6 = Saturday, 7 = Sunday
DOW=$(date +%u)
if [ "$DOW" -eq 6 ] || [ "$DOW" -eq 7 ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipping scan: Saturday and Sunday are excluded."
  exit 0
fi

# 2) Ensure virtual environment exists
if [ ! -x "$DIR/.venv/bin/python3" ]; then
  echo "Virtual environment not found in $DIR/.venv. Initializing..."
  /opt/homebrew/bin/python3.12 -m venv "$DIR/.venv"
  "$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"
fi

# 3) Activate virtual environment
# shellcheck disable=SC1091
source "$DIR/.venv/bin/activate"

# 4) Prepare directories
mkdir -p "$DIR/out" "$DIR/logs"

STAMP=$(date +%Y-%m-%d)
LOG_FILE="$DIR/logs/scan-$STAMP.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting daily TASE scan..." | tee -a "$LOG_FILE"

# 5) Run the live scan
python3 "$DIR/tase_swing_scan.py" --out "$DIR/out" "$@" 2>&1 | tee -a "$LOG_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily scan completed successfully. Report written to $DIR/out/tase_swing_scan_$STAMP.md" | tee -a "$LOG_FILE"

# 6) Auto-commit & push reports to GitHub
echo "$(date '+%Y-%m-%d %H:%M:%S') - Syncing scan reports to GitHub..." | tee -a "$LOG_FILE"
git add "$DIR/out/tase_swing_scan_$STAMP.md" "$DIR/out/tase_swing_scan_$STAMP.csv"
if ! git diff --cached --quiet; then
  git commit -m "chore(scan): daily scan report $STAMP"
  # Pull remote updates first in case of Dependabot PRs or edits
  git pull --rebase origin main || true
  git push origin main
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Successfully pushed scan reports to GitHub." | tee -a "$LOG_FILE"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Scan report already up to date on GitHub." | tee -a "$LOG_FILE"
fi

