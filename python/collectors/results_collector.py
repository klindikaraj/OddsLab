# python/collectors/results_collector.py
"""
Aggiorna i risultati delle partite concluse
usando The Odds API (scores endpoint).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB
from config import ODDS_API_KEY

BASE_URL = "https://api.the-odds-api.com/v4/sports"


class ResultsCollector:
    """Raccoglie i risultati delle partite e aggiorna il DB."""

    def __init__(self) -> None:
        self.api_key: str = ODDS_API_KEY

    def get_scores(self, sport_key: str,
                   days_from: int = 3) -> list[dict[str, Any]]:
        """Scarica i risultati degli ultimi N giorni."""
        url = (
            f"{BASE_URL}/{sport_key}/scores/"
            f"?apiKey={self.api_key}"
            f"&daysFrom={days_from}"
        )

        print(f"[API] Scaricando risultati per: {sport_key}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        scores: list[dict[str, Any]] = response.json()
        print(f"[API] Trovati {len(scores)} risultati")
        return scores

    def update_results(self, scores: list[dict[str, Any]]) -> dict[str, int]:
        """Aggiorna le partite nel DB con i risultati reali."""
        stats: dict[str, int] = {
            'aggiornate': 0,
            'non_trovate': 0,
            'gia_aggiornate': 0
        }

        for score in scores:
            if not score.get('completed'):
                continue

            partita: Optional[dict] = DB.fetch_one(
                """SELECT id, stato FROM partite
                WHERE api_event_id = %s""",
                (score['id'],)
            )

            if partita is None:
                stats['non_trovate'] += 1
                continue

            if partita['stato'] == 'conclusa':
                stats['gia_aggiornate'] += 1
                continue

            score_home: Optional[int] = None
            score_away: Optional[int] = None

            if score.get('scores') and len(score['scores']) >= 2:
                for s in score['scores']:
                    if s['name'] == score['home_team']:
                        score_home = int(s['score'])
                    elif s['name'] == score['away_team']:
                        score_away = int(s['score'])

            # Se non abbiamo i punteggi ma il match è completato,
            # determina il vincitore dal fatto che è "completed"
            if score_home is None or score_away is None:
                # Per tennis/MMA: il match è completato,
                # usiamo score 1-0 per il vincitore
                if score.get('completed') and score.get('scores'):
                    try:
                        scores_list = score['scores']
                        if len(scores_list) >= 2:
                            s1 = int(scores_list[0].get('score', 0))
                            s2 = int(scores_list[1].get('score', 0))

                            if scores_list[0]['name'] == score['home_team']:
                                score_home = s1
                                score_away = s2
                            else:
                                score_home = s2
                                score_away = s1
                    except (ValueError, KeyError, IndexError):
                        # Non riusciamo a parsare → skip
                        continue

            if score_home is not None and score_away is not None:
                partita_id = int(partita['id'])

                DB.execute(
                    """UPDATE partite
                    SET stato = 'conclusa',
                        score_casa = %s,
                        score_trasferta = %s
                    WHERE id = %s""",
                    (score_home, score_away, partita_id)
                )

                self._settle_value_bets(
                    partita_id, score_home, score_away
                )

                stats['aggiornate'] += 1
                print(
                    f"  ✅ Aggiornata partita #{partita_id}: "
                    f"{score['home_team']} {score_home} - "
                    f"{score_away} {score['away_team']}"
                )

        print(f"[Results] Riepilogo: {stats}")
        return stats

    def _settle_value_bets(self, partita_id: int,
                           score_home: int,
                           score_away: int) -> None:
        """Determina se le value bets sono state vinte o perse."""
        if score_home > score_away:
            esito_reale = 'home'
        elif score_home == score_away:
            esito_reale = 'draw'
        else:
            esito_reale = 'away'

        value_bets: list[dict] = DB.fetch_all(
            """SELECT id, esito FROM value_bets
               WHERE partita_id = %s AND stato = 'pending'""",
            (partita_id,)
        )

        for vb in value_bets:
            nuovo_stato = 'won' if vb['esito'] == esito_reale else 'lost'

            DB.execute(
                """UPDATE value_bets SET stato = %s
                   WHERE id = %s""",
                (nuovo_stato, int(vb['id']))
            )

        if value_bets:
            print(
                f"    📊 {len(value_bets)} value bets aggiornate "
                f"(risultato: {esito_reale})"
            )

    def update_team_stats(self, campionato_id: int) -> None:
        """Ricalcola le medie gol fatti/subiti per ogni squadra."""
        squadre: list[dict] = DB.fetch_all(
            "SELECT id FROM squadre WHERE campionato_id = %s",
            (campionato_id,)
        )

        for sq in squadre:
            sid = int(sq['id'])

            stats_row: Optional[dict] = DB.fetch_one(
                """SELECT
                     AVG(CASE
                       WHEN squadra_casa_id = %s THEN score_casa
                       WHEN squadra_trasf_id = %s THEN score_trasferta
                     END) AS avg_fatti,
                     AVG(CASE
                       WHEN squadra_casa_id = %s THEN score_trasferta
                       WHEN squadra_trasf_id = %s THEN score_casa
                     END) AS avg_subiti,
                     COUNT(*) AS partite_giocate
                   FROM partite
                   WHERE (squadra_casa_id = %s
                          OR squadra_trasf_id = %s)
                     AND stato = 'conclusa'""",
                (sid, sid, sid, sid, sid, sid)
            )

            if (stats_row is not None
                    and stats_row['partite_giocate'] is not None
                    and int(stats_row['partite_giocate']) >= 3):
                avg_fatti = float(stats_row['avg_fatti'] or 0)
                avg_subiti = float(stats_row['avg_subiti'] or 0)

                DB.execute(
                    """UPDATE squadre
                       SET gol_fatti_avg = %s,
                           gol_subiti_avg = %s
                       WHERE id = %s""",
                    (round(avg_fatti, 2), round(avg_subiti, 2), sid)
                )

        print(f"[Stats] Aggiornate statistiche "
              f"per {len(squadre)} squadre")


# --- Test standalone ---
if __name__ == '__main__':
    collector = ResultsCollector()
    scores = collector.get_scores('soccer_italy_serie_a', days_from=3)
    for s in scores:
        status = "✅" if s.get('completed') else "⏳"
        print(
            f"  {status} {s['home_team']} vs {s['away_team']} "
            f"| {s.get('scores', 'N/A')}"
        )
