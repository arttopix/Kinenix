#!/usr/bin/env bash
# ==============================================================================
# Kinenix Worker - install, update, or remove the systemd service (Linux)
#
#   ./kinenix-worker/scripts/install_service.sh              install or update, then start
#   ./kinenix-worker/scripts/install_service.sh --uninstall  stop and remove the service
#
# Run as the user that owns the Kinenix checkout (not as root); sudo is used where needed.
# The service runs `kinenix-worker daemon` as that user, starts at boot, and restarts on failure.
#
# Per-user files (created if missing, never overwritten):
#   ~/.kinenix/worker.env      KINENIX_ORCHESTRATOR_URL, KINENIX_ORCHESTRATOR_API_KEY, KINENIX_WORKER_ID
#   ~/.kinenix/triggers.json   triggers for the daemon; empty means heartbeats only
# ==============================================================================
set -euo pipefail

SERVICE_NAME="kinenix-worker"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

if ! command -v systemctl >/dev/null 2>&1; then
    echo "ERROR: systemd (systemctl) not found. This script supports systemd-based Linux only." >&2
    exit 1
fi
if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: run this script as the user that owns the Kinenix checkout, not as root." >&2
    exit 1
fi

if [ "${1:-}" = "--uninstall" ]; then
    sudo systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "$UNIT_PATH"
    sudo systemctl daemon-reload
    echo "Service '$SERVICE_NAME' removed. Files in ~/.kinenix were kept."
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKER_BIN="$REPO_ROOT/.venv/bin/kinenix-worker"
RUN_USER="$(id -un)"
CONFIG_DIR="$HOME/.kinenix"
ENV_FILE="$CONFIG_DIR/worker.env"
TRIGGERS_FILE="$CONFIG_DIR/triggers.json"

if [ ! -x "$WORKER_BIN" ]; then
    echo "ERROR: $WORKER_BIN not found. Run kinenix-worker/scripts/setup_rpi.sh first." >&2
    exit 1
fi

mkdir -p "$CONFIG_DIR"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'EOF'
# Kinenix Worker settings, loaded by the kinenix-worker service and by your shell.
# Fill in the Orchestrator URL and key, then: sudo systemctl restart kinenix-worker
export KINENIX_ORCHESTRATOR_URL=
export KINENIX_ORCHESTRATOR_API_KEY=
export KINENIX_WORKER_ID=$(hostname)
EOF
    echo "Created $ENV_FILE (edit it to connect to the Orchestrator)."
fi
chmod 600 "$ENV_FILE"

if [ ! -f "$TRIGGERS_FILE" ]; then
    cat > "$TRIGGERS_FILE" <<'EOF'
{
  "triggers": []
}
EOF
    echo "Created $TRIGGERS_FILE (no triggers yet: the worker only sends heartbeats)."
fi

# worker.env is sourced by bash so it can keep the `export` lines that a login shell also uses
sudo tee "$UNIT_PATH" >/dev/null <<EOF
[Unit]
Description=Kinenix Worker (unattended RPA daemon)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$REPO_ROOT
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash -c 'if [ -f "$ENV_FILE" ]; then . "$ENV_FILE"; fi; exec "$WORKER_BIN" daemon --config "$TRIGGERS_FILE"'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" >/dev/null
sudo systemctl restart "$SERVICE_NAME"

echo ""
echo "Service '$SERVICE_NAME' installed and started (runs as $RUN_USER, starts at boot)."
echo "  Status:   systemctl status $SERVICE_NAME"
echo "  Logs:     journalctl -u $SERVICE_NAME -f"
echo "  Restart:  sudo systemctl restart $SERVICE_NAME   (after editing worker.env or triggers.json)"
echo "  Remove:   $SCRIPT_DIR/install_service.sh --uninstall"
