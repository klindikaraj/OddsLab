# python/collectors/odds_collector.py
"""
Raccoglie quote live da The Odds API e le salva nel database.
Documentazione API: https://the-odds-api.com/liveapi/guides/v4/
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB
from config import ODDS_API_KEY

BASE_URL = "https://api.the-odds-api.com/v4/sports"


class OddsCollector:
    """Raccoglie quote live da The Odds API e le salva nel DB."""

    def __init__(self) -> None:
        self.api_key: str = ODDS_API_KEY
        self.regions: str = "eu"
        self.markets: str = "h2h"
        self.odds_format: str = "decimal"

        if not self.api_key:
            raise ValueError(
                "ODDS_API_KEY non configurata! "
                "Controlla il file .env"
            )

    def get_available_sports(self) -> list[dict[str, Any]]:
        """Restituisce la lista degli sport disponibili sulla API."""
        url = f"{BASE_URL}/?apiKey={self.api_key}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        sports: list[dict[str, Any]] = response.json()
        print(f"[API] {len(sports)} sport disponibili")
        return sports

    def get_odds(self, sport_key: str) -> list[dict[str, Any]]:
        """
        Scarica le quote per uno sport/campionato specifico.

        Args:
            sport_key: es. 'soccer_italy_serie_a'

        Returns:
            Lista di eventi con quote
        """
        url = (
            f"{BASE_URL}/{sport_key}/odds/"
            f"?apiKey={self.api_key}"
            f"&regions={self.regions}"
            f"&markets={self.markets}"
            f"&oddsFormat={self.odds_format}"
        )

        print(f"[API] Scaricando quote per: {sport_key}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        remaining = response.headers.get(
            'x-requests-remaining', '?'
        )
        used = response.headers.get(
            'x-requests-used', '?'
        )
        print(f"[API] Richieste usate: {used} | "
              f"Rimanenti: {remaining}")

        events: list[dict[str, Any]] = response.json()
        print(f"[API] Trovati {len(events)} eventi")
        return events

    def save_to_db(self, events: list[dict[str, Any]],
                   sport_id: int,
                   campionato_id: int) -> dict[str, int]:
        """
        Salva partite, bookmaker e quote nel database.

        Returns:
            Dizionario con statistiche di salvataggio
        """
        stats: dict[str, int] = {
            'partite_nuove': 0,
            'partite_esistenti': 0,
            'quote_inserite': 0,
            'bookmaker_nuovi': 0
        }

        for event in events:
            partita_id, is_new = self._upsert_partita(
                event, sport_id, campionato_id
            )

            if is_new:
                stats['partite_nuove'] += 1
            else:
                stats['partite_esistenti'] += 1

            for bookmaker_data in event.get('bookmakers', []):
                book_id, book_new = self._upsert_bookmaker(
                    bookmaker_data['key'],
                    bookmaker_data['title']
                )

                if book_new:
                    stats['bookmaker_nuovi'] += 1

                for market in bookmaker_data.get('markets', []):
                    if market['key'] != 'h2h':
                        continue

                    for outcome in market.get('outcomes', []):
                        esito = self._map_outcome(
                            outcome['name'], event
                        )
                        self._insert_quota(
                            partita_id=partita_id,
                            bookmaker_id=book_id,
                            tipo_mercato=market['key'],
                            esito=esito,
                            valore=outcome['price']
                        )
                        stats['quote_inserite'] += 1

        print(f"[DB] Salvati: {stats}")
        return stats

    # =============== METODI PRIVATI ===============

    def _upsert_partita(self, event: dict[str, Any],
                        sport_id: int,
                        camp_id: int) -> tuple[int, bool]:
        """Inserisce la partita se non esiste. Ritorna (id, is_new)."""
        existing = DB.fetch_one(
            "SELECT id FROM partite WHERE api_event_id = %s",
            (event['id'],)
        )

        if existing is not None:
            return int(existing['id']), False

        casa_id = self._upsert_squadra(
            event['home_team'], camp_id
        )
        trasf_id = self._upsert_squadra(
            event['away_team'], camp_id
        )

        data_ora = event['commence_time'].replace('T', ' ')
        data_ora = data_ora.replace('Z', '')

        partita_id = DB.execute(
            """INSERT INTO partite
               (sport_id, campionato_id, squadra_casa_id,
                squadra_trasf_id, data_ora, api_event_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (sport_id, camp_id, casa_id, trasf_id,
             data_ora, event['id'])
        )

        return partita_id, True

    def _upsert_squadra(self, nome: str,
                        camp_id: int) -> int:
        """Inserisce la squadra se non esiste. Ritorna l'id."""
        existing = DB.fetch_one(
            """SELECT id FROM squadre
               WHERE nome_api = %s AND campionato_id = %s""",
            (nome, camp_id)
        )

        if existing is not None:
            return int(existing['id'])

        return DB.execute(
            """INSERT INTO squadre
               (campionato_id, nome, nome_api)
               VALUES (%s, %s, %s)""",
            (camp_id, nome, nome)
        )

    def _upsert_bookmaker(self, key: str,
                          title: str) -> tuple[int, bool]:
        """Inserisce il bookmaker se non esiste. Ritorna (id, is_new)."""
        existing = DB.fetch_one(
            "SELECT id FROM bookmaker WHERE nome = %s",
            (title,)
        )

        if existing is not None:
            return int(existing['id']), False

        new_id = DB.execute(
            """INSERT INTO bookmaker (nome, url)
               VALUES (%s, %s)""",
            (title, f"https://{key}.com")
        )
        return new_id, True

    def _insert_quota(self, partita_id: int,
                      bookmaker_id: int,
                      tipo_mercato: str,
                      esito: str,
                      valore: float) -> None:
        """Inserisce una singola quota nel database."""
        DB.execute(
            """INSERT INTO quote
               (partita_id, bookmaker_id, tipo_mercato,
                esito, valore_quota)
               VALUES (%s, %s, %s, %s, %s)""",
            (partita_id, bookmaker_id, tipo_mercato,
             esito, round(float(valore), 2))
        )

    def _map_outcome(self, outcome_name: str,
                     event: dict[str, Any]) -> str:
        """Mappa il nome dell'esito dell'API al nostro formato."""
        if outcome_name == event['home_team']:
            return 'home'
        elif outcome_name == event['away_team']:
            return 'away'
        elif outcome_name.lower() == 'draw':
            return 'draw'
        return outcome_name.lower()


# --- Test standalone ---
if __name__ == '__main__':
    collector = OddsCollector()
    sports = collector.get_available_sports()
    for s in sports[:10]:
        print(f"  {s['key']:.<40} {s['title']}")