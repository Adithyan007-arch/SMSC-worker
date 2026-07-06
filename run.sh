#!/bin/bash
###############################################################################
# File        : run.sh
# Description : SMS Sender Startup Script
###############################################################################

set -euo pipefail

APP_HOME="$(cd "$(dirname "$0")" && pwd)"

PYTHON_BIN="${APP_HOME}/venv/bin/python"

DEFAULT_CONFIG="${APP_HOME}/conf/config-prod.json"

usage() {
    cat << EOF

Usage:
    ./run.sh --config conf/config-uat.json
    ./run.sh --config conf/config-prod.json

Options:
    --config <file>   Configuration JSON file
    -h, --help        Show help

EOF
}

CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

if [[ -z "${CONFIG_FILE}" ]]; then
    CONFIG_FILE="${DEFAULT_CONFIG}"
fi

# Convert relative path to absolute
if [[ "${CONFIG_FILE}" != /* ]]; then
    CONFIG_FILE="${APP_HOME}/${CONFIG_FILE}"
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "ERROR: Configuration file not found:"
    echo "       ${CONFIG_FILE}"
    exit 1
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "ERROR: Python virtual environment not found."
    echo "Run ./install.sh first."
    exit 1
fi

export PYTHONUNBUFFERED=1

echo "=========================================================="
echo " SMS Sender"
echo "=========================================================="
echo "Application Home : ${APP_HOME}"
echo "Configuration    : ${CONFIG_FILE}"
echo "Started At       : $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================================="

cd "${APP_HOME}"

"${PYTHON_BIN}" send_sms.py --config "${CONFIG_FILE}"

EXIT_CODE=$?

echo
echo "=========================================================="
echo "Finished At : $(date '+%Y-%m-%d %H:%M:%S')"
echo "Exit Code   : ${EXIT_CODE}"
echo "=========================================================="

exit ${EXIT_CODE}