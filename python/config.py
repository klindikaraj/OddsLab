# python/config.py
"""
Configurazione centralizzata OddsLab.
Legge le variabili dal file .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica il .env dalla stessa cartella di questo file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- Database ---
DATABASE = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', ''),
    'database': os.getenv('DB_NAME', 'oddslab'),
}

# --- API Keys ---
ODDS_API_KEY   = os.getenv('ODDS_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# --- Impostazioni App ---
SUPPORTED_SPORTS = [
    # ===== CALCIO =====
    {
        'api_key':  'soccer_italy_serie_a',
        'nome':     'Serie A',
        'sport':    'Calcio',
        'paese':    'Italia',
        'icona':    '⚽',
        'modello':  'poisson'
    },
    {
        'api_key':  'soccer_epl',
        'nome':     'Premier League',
        'sport':    'Calcio',
        'paese':    'Inghilterra',
        'icona':    '⚽',
        'modello':  'poisson'
    },
    {
        'api_key':  'soccer_spain_la_liga',
        'nome':     'La Liga',
        'sport':    'Calcio',
        'paese':    'Spagna',
        'icona':    '⚽',
        'modello':  'poisson'
    },

    # ===== TENNIS =====
    {
        'api_key':  'tennis_wta_charleston_open',
        'nome':     'WTA Charleston Open',
        'sport':    'Tennis',
        'paese':    'Internazionale',
        'icona':    '🎾',
        'modello':  'elo'
    },
    # Tornei futuri (si attiveranno quando iniziano)
    {
        'api_key':  'tennis_atp_french_open',
        'nome':     'ATP French Open',
        'sport':    'Tennis',
        'paese':    'Internazionale',
        'icona':    '🎾',
        'modello':  'elo'
    },
    {
        'api_key':  'tennis_atp_wimbledon',
        'nome':     'ATP Wimbledon',
        'sport':    'Tennis',
        'paese':    'Internazionale',
        'icona':    '🎾',
        'modello':  'elo'
    },
    {
        'api_key':  'tennis_atp_us_open',
        'nome':     'ATP US Open',
        'sport':    'Tennis',
        'paese':    'Internazionale',
        'icona':    '🎾',
        'modello':  'elo'
    },
    {
        'api_key':  'tennis_atp_aus_open',
        'nome':     'ATP Australian Open',
        'sport':    'Tennis',
        'paese':    'Internazionale',
        'icona':    '🎾',
        'modello':  'elo'
    },

    # ===== BASKET =====
    {
        'api_key':  'basketball_nba',
        'nome':     'NBA',
        'sport':    'Basket',
        'paese':    'USA',
        'icona':    '🏀',
        'modello':  'elo'
    },
]

# Soglie Value Bet
MIN_VALUE_THRESHOLD = 0.02   # Ignora value < 2%
MAX_KELLY_STAKE     = 0.10   # Mai più del 10% del bankroll


if __name__ == '__main__':
    print("=== OddsLab Config ===")
    print(f"DB Host:     {DATABASE['host']}")
    print(f"DB Name:     {DATABASE['database']}")
    print(f"Odds API:    {'✅ Configurata' if ODDS_API_KEY else '❌ Mancante'}")
    print(f"OpenAI API:  {'✅ Configurata' if OPENAI_API_KEY else '❌ Mancante'}")
    print(f"Sport:       {len(SUPPORTED_SPORTS)} configurati")