#!/bin/bash
# ============================================
# OddsLab — Aggiornamento Risultati
# Esegui ogni giorno alle 8:00 e alle 23:00:
# 0 8,23 * * * /path/to/OddsLab/cron/update_results.sh
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_DIR="$PROJECT_DIR/python"
LOG_DIR="$PROJECT_DIR/cron/logs"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/update_results_$TIMESTAMP.log"

echo "========================================" >> "$LOG_FILE"
echo "OddsLab — Update Results" >> "$LOG_FILE"
echo "Avviato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$PYTHON_DIR" || exit 1

python main.py --results >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Completato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

ls -t "$LOG_DIR"/update_results_*.log 2>/dev/null | tail -n +31 | xargs -r rm