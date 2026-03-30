#!/bin/bash
# ============================================
# OddsLab — Raccolta Quote Automatica
# Esegui ogni 6 ore con crontab:
# 0 */6 * * * /path/to/OddsLab/cron/fetch_odds.sh
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_DIR="$PROJECT_DIR/python"
LOG_DIR="$PROJECT_DIR/cron/logs"

# Crea cartella log se non esiste
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/fetch_odds_$TIMESTAMP.log"

echo "========================================" >> "$LOG_FILE"
echo "OddsLab — Fetch Odds" >> "$LOG_FILE"
echo "Avviato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$PYTHON_DIR" || exit 1

python main.py --collect >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Completato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Mantieni solo gli ultimi 30 log
ls -t "$LOG_DIR"/fetch_odds_*.log 2>/dev/null | tail -n +31 | xargs -r rm