#!/bin/bash
#
# Install WHOOP sync as launchd job (macOS)
#
# Usage:
#   ./install-cron.sh          # Install and start
#   ./install-cron.sh uninstall # Remove
#   ./install-cron.sh status    # Check status
#   ./install-cron.sh run       # Run now (manual)
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_NAME="com.health.whoop-sync"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

case "${1:-install}" in
    install)
        echo "Installing WHOOP sync..."

        # Copy plist
        cp "$PLIST_SRC" "$PLIST_DST"

        # Load job
        launchctl load "$PLIST_DST"

        echo "Installed! Sync runs at 08:00 and 20:00 daily."
        echo ""
        echo "Commands:"
        echo "  ./install-cron.sh status  - Check status"
        echo "  ./install-cron.sh run     - Run now"
        echo "  ./install-cron.sh logs    - View logs"
        ;;

    uninstall)
        echo "Uninstalling WHOOP sync..."
        launchctl unload "$PLIST_DST" 2>/dev/null
        rm -f "$PLIST_DST"
        echo "Uninstalled."
        ;;

    status)
        echo "WHOOP Sync Status:"
        launchctl list | grep -E "PID|$PLIST_NAME" | head -2
        echo ""
        echo "Last sync:"
        tail -5 "$PROJECT_DIR/data/integrations/whoop/sync.log" 2>/dev/null || echo "No logs yet"
        ;;

    run)
        echo "Running WHOOP sync now..."
        "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/integrations/whoop/sync.py" --days 2
        ;;

    logs)
        echo "=== Sync Log ==="
        tail -30 "$PROJECT_DIR/data/integrations/whoop/sync.log" 2>/dev/null
        ;;

    *)
        echo "Usage: $0 {install|uninstall|status|run|logs}"
        exit 1
        ;;
esac
