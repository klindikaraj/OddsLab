#!/bin/bash
# ============================================
# OddsLab — Calcolo Previsioni + Ricerca Value Bets
# Esegui dopo fetch_odds, ogni 6 ore:
# 15 */6 * * * /path/to/OddsLab/cron/run_models.sh
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_DIR="$PROJECT_DIR/python"
LOG_DIR="$PROJECT_DIR/cron/logs"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/run_models_$TIMESTAMP.log"

echo "========================================" >> "$LOG_FILE"
echo "OddsLab — Run Models + Find Value Bets" >> "$LOG_FILE"
echo "Avviato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$PYTHON_DIR" || exit 1

# Step 1: Calcola previsioni
python main.py --predict >> "$LOG_FILE" 2>&1

# Step 2: Trova value bets
python main.py --find >> "$LOG_FILE" 2>&1

# Step 3: Genera report IA
python main.py --report >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Completato: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

ls -t "$LOG_DIR"/run_models_*.log 2>/dev/null | tail -n +31 | xargs -r rm