#!/bin/bash
#
# Install WHOOP sync as systemd service (Debian/Ubuntu)
#
# Usage:
#   sudo ./install.sh              # Install and enable
#   sudo ./install.sh uninstall    # Remove
#   ./install.sh status            # Check status (no sudo)
#   ./install.sh run               # Run now (no sudo)
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="whoop-sync"

# Detect project dir (adjust if needed)
PROJECT_DIR="${PROJECT_DIR:-$HOME/health-os}"

case "${1:-install}" in
    install)
        if [ "$EUID" -ne 0 ]; then
            echo "Please run with sudo: sudo $0 install"
            exit 1
        fi

        echo "Installing WHOOP sync service..."

        # Copy service files
        cp "$SCRIPT_DIR/whoop-sync.service" /etc/systemd/system/
        cp "$SCRIPT_DIR/whoop-sync.timer" /etc/systemd/system/

        # Reload systemd
        systemctl daemon-reload

        # Enable and start timer
        systemctl enable whoop-sync.timer
        systemctl start whoop-sync.timer

        echo ""
        echo "Installed! Timer runs at 08:00 and 20:00 daily."
        echo ""
        echo "Commands:"
        echo "  systemctl status whoop-sync.timer   # Timer status"
        echo "  systemctl start whoop-sync.service  # Run now"
        echo "  journalctl -u whoop-sync.service    # View logs"
        ;;

    uninstall)
        if [ "$EUID" -ne 0 ]; then
            echo "Please run with sudo: sudo $0 uninstall"
            exit 1
        fi

        echo "Uninstalling WHOOP sync..."
        systemctl stop whoop-sync.timer
        systemctl disable whoop-sync.timer
        rm -f /etc/systemd/system/whoop-sync.service
        rm -f /etc/systemd/system/whoop-sync.timer
        systemctl daemon-reload
        echo "Uninstalled."
        ;;

    status)
        echo "=== Timer Status ==="
        systemctl status whoop-sync.timer --no-pager 2>/dev/null || echo "Timer not installed"
        echo ""
        echo "=== Next Run ==="
        systemctl list-timers whoop-sync.timer --no-pager 2>/dev/null
        echo ""
        echo "=== Last Sync ==="
        tail -10 "$PROJECT_DIR/data/integrations/whoop/sync.log" 2>/dev/null || echo "No logs"
        ;;

    run)
        echo "Running WHOOP sync now..."
        "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/integrations/whoop/sync.py" --days 2
        ;;

    logs)
        journalctl -u whoop-sync.service -n 50 --no-pager
        ;;

    *)
        echo "Usage: $0 {install|uninstall|status|run|logs}"
        exit 1
        ;;
esac
