# python/config.py
"""
Configurazione centralizzata OddsLab.
Legge le variabili dal file .env

Provider risultati:
  - Calcio:  football-data.org (free, stagione corrente inclusa)
  - Basket:  balldontlie.io    (free, NBA inclusa)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

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
ODDS_API_KEY      = os.getenv('ODDS_API_KEY', '')
OPENAI_API_KEY    = os.getenv('OPENAI_API_KEY', '')
FOOTBALLDATA_KEY  = os.getenv('FOOTBALLDATA_KEY', '')
BALLDONTLIE_KEY   = os.getenv('BALLDONTLIE_KEY', '')

# --- Sport supportati ---
# results_provider:
#   'footballdata' → football-data.org  (calcio)
#   'balldontlie'  → balldontlie.io     (NBA)
#   None           → nessun aggiornamento automatico
SUPPORTED_SPORTS = [
    # ===== CALCIO =====
    {
        'api_key':          'soccer_italy_serie_a',
        'nome':             'Serie A',
        'sport':            'Calcio',
        'paese':            'Italia',
        'icona':            '⚽',
        'modello':          'poisson',
        'results_provider': 'footballdata',
        'fd_competition':   'SA',    # football-data.org competition code
    },
    {
        'api_key':          'soccer_epl',
        'nome':             'Premier League',
        'sport':            'Calcio',
        'paese':            'Inghilterra',
        'icona':            '⚽',
        'modello':          'poisson',
        'results_provider': 'footballdata',
        'fd_competition':   'PL',
    },
    {
        'api_key':          'soccer_spain_la_liga',
        'nome':             'La Liga',
        'sport':            'Calcio',
        'paese':            'Spagna',
        'icona':            '⚽',
        'modello':          'poisson',
        'results_provider': 'footballdata',
        'fd_competition':   'PD',    # Primera Division
    },

    # ===== BASKET =====
    {
        'api_key':          'basketball_nba',
        'nome':             'NBA',
        'sport':            'Basket',
        'paese':            'USA',
        'icona':            '🏀',
        'modello':          'elo',
        'results_provider': 'balldontlie',
    },
]

# Soglie Value Bet
MIN_VALUE_THRESHOLD = 0.02   # Ignora value < 2%
MAX_KELLY_STAKE     = 0.10   # Mai più del 10% del bankroll


if __name__ == '__main__':
    print("=== OddsLab Config ===")
    print(f"DB Host:           {DATABASE['host']}")
    print(f"DB Name:           {DATABASE['database']}")
    print(f"Odds API:          {'✅' if ODDS_API_KEY else '❌'}")
    print(f"OpenAI:            {'✅' if OPENAI_API_KEY else '❌'}")
    print(f"football-data.org: {'✅' if FOOTBALLDATA_KEY else '❌'}")
    print(f"balldontlie.io:    {'✅' if BALLDONTLIE_KEY else '❌'}")
    print(f"Sport attivi:      {len(SUPPORTED_SPORTS)}")
