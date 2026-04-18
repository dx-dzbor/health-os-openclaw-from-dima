#!/bin/bash
#
# WHOOP Sync Cron Wrapper
#
# Runs every 12 hours via crontab.
#
# Install:
#   crontab -e
#   0 */12 * * * /path/to/health-os/integrations/whoop/cron_sync.sh
#
# Or for testing:
#   ./cron_sync.sh
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_DIR/data/integrations/whoop/sync.log"
VENV_PATH="$PROJECT_DIR/.venv"
MAX_LOG_SIZE=1048576  # 1MB

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Also try user's home directory
if [ -f "$HOME/.whoop_env" ]; then
    export $(grep -v '^#' "$HOME/.whoop_env" | xargs)
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Rotate log if too large
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi

# Log start
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "WHOOP Sync: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Activate virtual environment if exists
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "Using venv: $VENV_PATH" >> "$LOG_FILE"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run sync
python integrations/whoop/sync.py --days 2 >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Sync completed successfully" >> "$LOG_FILE"
else
    echo "Sync failed with exit code: $EXIT_CODE" >> "$LOG_FILE"
fi

echo "----------------------------------------" >> "$LOG_FILE"

exit $EXIT_CODE
