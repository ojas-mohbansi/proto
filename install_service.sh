#!/usr/bin/env bash
# Install Proto as systemd services on Linux.
# Usage: sudo ./install_service.sh [install|uninstall|status]
# Requires: systemd, python3, node, npm.

set -euo pipefail
ACTION="${1:-install}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-${USER}}"
PYTHON="$(command -v python3)"
NODE="$(command -v node)"
SYSTEMD_DIR="/etc/systemd/system"

UNITS=(proto-api proto-agent proto-watchdog proto-whatsapp)

write_unit() {
  local name="$1" desc="$2" exec="$3" workdir="$4"
  cat > "${SYSTEMD_DIR}/${name}.service" <<EOF
[Unit]
Description=${desc}
After=network.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${workdir}
Environment=PYTHONUNBUFFERED=1
Environment=AGENT_HOME=${ROOT}
EnvironmentFile=-${ROOT}/.env
ExecStart=${exec}
Restart=always
RestartSec=5
StandardOutput=append:${ROOT}/logs/${name}.log
StandardError=append:${ROOT}/logs/${name}.err

[Install]
WantedBy=multi-user.target
EOF
}

case "$ACTION" in
  install)
    if [ "$EUID" -ne 0 ]; then echo "Run as root (sudo)."; exit 1; fi
    mkdir -p "${ROOT}/logs"
    write_unit "proto-api"       "Proto — FastAPI"        "${PYTHON} ${ROOT}/start_api.py"             "${ROOT}"
    write_unit "proto-agent"     "Proto — Autonomous Agent" "${PYTHON} ${ROOT}/main.py"               "${ROOT}"
    write_unit "proto-watchdog"  "Proto — Watchdog"        "${PYTHON} ${ROOT}/watchdog/monitor.py"     "${ROOT}"
    write_unit "proto-whatsapp"  "Proto — WhatsApp Bot"    "${NODE} ${ROOT}/whatsapp/index.js"         "${ROOT}/whatsapp"
    systemctl daemon-reload
    for u in "${UNITS[@]}"; do
      systemctl enable "$u"
      systemctl restart "$u"
    done
    systemctl --no-pager status "${UNITS[@]}" || true
    echo
    echo "Installed. Logs are in ${ROOT}/logs/. Dashboard: cd dashboard && npm install && npm run build && npm run start"
    ;;
  uninstall)
    if [ "$EUID" -ne 0 ]; then echo "Run as root (sudo)."; exit 1; fi
    for u in "${UNITS[@]}"; do
      systemctl stop "$u" || true
      systemctl disable "$u" || true
      rm -f "${SYSTEMD_DIR}/${u}.service"
    done
    systemctl daemon-reload
    echo "Uninstalled."
    ;;
  status)
    systemctl --no-pager status "${UNITS[@]}" || true
    ;;
  *)
    echo "Usage: $0 [install|uninstall|status]"; exit 1
    ;;
esac
