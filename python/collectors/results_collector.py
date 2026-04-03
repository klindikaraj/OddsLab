# python/collectors/results_collector.py
"""
Aggiorna i risultati delle partite concluse
usando The Odds API (scores endpoint).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

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

    @staticmethod
    def _is_finished(score: dict[str, Any]) -> bool:
        """
        Considera una partita finita se:
        1. L'API dice completed=True, OPPURE
        2. Il commence_time è nel passato E i punteggi sono presenti.
        (Il piano free di The Odds API ritarda il flag completed.)
        """
        if score.get('completed'):
            return True

        commence_time = score.get('commence_time', '')
        if not commence_time:
            return False

        try:
            # Parsa il timestamp ISO8601 dall'API (es. "2026-04-01T19:35:00Z")
            dt = datetime.fromisoformat(
                commence_time.replace('Z', '+00:00')
            )
            now = datetime.now(timezone.utc)
            # Considera finita se iniziata da più di 2 ore e ha punteggi
            elapsed_hours = (now - dt).total_seconds() / 3600
            has_scores = bool(score.get('scores'))
            return elapsed_hours > 2 and has_scores
        except (ValueError, TypeError):
            return False

    def update_results(self, scores: list[dict[str, Any]]) -> dict[str, int]:
        """Aggiorna le partite nel DB con i risultati reali."""
        stats: dict[str, int] = {
            'aggiornate': 0,
            'non_trovate': 0,
            'gia_aggiornate': 0
        }

        for score in scores:
            if not self._is_finished(score):
                continue

            partita: Optional[dict] = DB.fetch_one(
                "SELECT id, stato FROM partite WHERE api_event_id = %s",
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

            scores_list = score.get('scores') or []

            # Prova prima con corrispondenza per nome
            for s in scores_list:
                try:
                    if s['name'] == score['home_team']:
                        score_home = int(s['score'])
                    elif s['name'] == score['away_team']:
                        score_away = int(s['score'])
                except (ValueError, KeyError):
                    continue

            # Fallback: prendi i primi due punteggi in ordine
            if (score_home is None or score_away is None) and len(scores_list) >= 2:
                try:
                    s0_name  = scores_list[0]['name']
                    s0_score = int(scores_list[0]['score'])
                    s1_score = int(scores_list[1]['score'])
                    if s0_name == score['home_team']:
                        score_home, score_away = s0_score, s1_score
                    else:
                        score_home, score_away = s1_score, s0_score
                except (ValueError, KeyError, IndexError):
                    pass

            if score_home is None or score_away is None:
                print(f"  ⚠️  Punteggi non parsabili per: "
                      f"{score.get('home_team')} vs {score.get('away_team')}")
                continue

            partita_id = int(partita['id'])

            DB.execute(
                """UPDATE partite
                   SET stato = 'conclusa',
                       score_casa = %s,
                       score_trasferta = %s
                   WHERE id = %s""",
                (score_home, score_away, partita_id)
            )

            self._settle_value_bets(partita_id, score_home, score_away)

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
                "UPDATE value_bets SET stato = %s WHERE id = %s",
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
                   WHERE (squadra_casa_id = %s OR squadra_trasf_id = %s)
                     AND stato = 'conclusa'""",
                (sid, sid, sid, sid, sid, sid)
            )

            if (stats_row is not None
                    and stats_row['partite_giocate'] is not None
                    and int(stats_row['partite_giocate']) >= 3):
                DB.execute(
                    """UPDATE squadre
                       SET gol_fatti_avg = %s,
                           gol_subiti_avg = %s
                       WHERE id = %s""",
                    (round(float(stats_row['avg_fatti'] or 0), 2),
                     round(float(stats_row['avg_subiti'] or 0), 2),
                     sid)
                )

        print(f"[Stats] Aggiornate statistiche per {len(squadre)} squadre")


# --- Test standalone ---
if __name__ == '__main__':
    collector = ResultsCollector()
    scores = collector.get_scores('tennis_wta_charleston_open', days_from=3)
    for s in scores:
        finished = ResultsCollector._is_finished(s)
        print(
            f"  {'✅' if finished else '⏳'} "
            f"{s['home_team']} vs {s['away_team']} "
            f"| completed={s.get('completed')} "
            f"| scores={s.get('scores')} "
            f"| commence={s.get('commence_time')}"
        )
