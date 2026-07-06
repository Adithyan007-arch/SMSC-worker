#!/bin/bash
###############################################################################
# File        : install.sh
# Description : SMS Sender Installation Script
###############################################################################

set -e

APP_HOME=$(cd "$(dirname "$0")"; pwd)

echo "=================================================="
echo " Installing SMS Sender"
echo "=================================================="

echo "[1/7] Creating directory structure..."

mkdir -p "${APP_HOME}/conf"
mkdir -p "${APP_HOME}/logs"
mkdir -p "${APP_HOME}/input"
mkdir -p "${APP_HOME}/archive"
mkdir -p "${APP_HOME}/failed"
mkdir -p "${APP_HOME}/delivery_report"

echo "[2/7] Checking Python..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python3 is not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Detected: ${PYTHON_VERSION}"

echo "[3/7] Creating virtual environment..."

if [ ! -d "${APP_HOME}/venv" ]; then
    python3 -m venv "${APP_HOME}/venv"
fi

echo "[4/7] Activating virtual environment..."

source "${APP_HOME}/venv/bin/activate"

echo "[5/7] Upgrading pip..."

pip install --upgrade pip

echo "[6/7] Installing dependencies..."

pip install -r "${APP_HOME}/requirements.txt"

echo "[7/7] Setting executable permissions..."

chmod +x "${APP_HOME}/run.sh"

find "${APP_HOME}" -name "*.py" -exec chmod 644 {} \;

echo
echo "=================================================="
echo " Installation Completed Successfully"
echo "=================================================="
echo
echo "Activate environment:"
echo
echo "source ${APP_HOME}/venv/bin/activate"
echo
echo "Run application:"
echo
echo "./run.sh --config conf/config-uat.json"
echo
echo "or"
echo
echo "./run.sh --config conf/config-prod.json"
echo