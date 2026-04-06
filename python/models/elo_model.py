# python/models/elo_model.py
"""
Modello Elo Rating per sport 1v1 (Basket, ecc.)
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB


class EloModel:
    """Modello Elo Rating per previsione match 1v1."""

    DEFAULT_RATING: float = 1500.0
    K_FACTOR: int = 32

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400))

    def predict(self, home_id: int, away_id: int,
                campionato_id: Optional[int] = None) -> dict[str, object]:
        rating_home = self._get_rating(home_id)
        rating_away = self._get_rating(away_id)
        prob_home   = self.expected_score(rating_home, rating_away)

        return {
            'prob_home': round(prob_home, 4),
            'prob_draw': None,
            'prob_away': round(1.0 - prob_home, 4),
            'elo_home':  rating_home,
            'elo_away':  rating_away,
            'elo_diff':  round(rating_home - rating_away, 1),
            'model':     'elo'
        }

    def update_ratings(self, winner_id: int, loser_id: int) -> dict[str, float]:
        rating_w   = self._get_rating(winner_id)
        rating_l   = self._get_rating(loser_id)
        expected_w = self.expected_score(rating_w, rating_l)
        expected_l = self.expected_score(rating_l, rating_w)
        new_w      = rating_w + self.K_FACTOR * (1 - expected_w)
        new_l      = rating_l + self.K_FACTOR * (0 - expected_l)

        self._update_rating_db(winner_id, round(new_w, 2))
        self._update_rating_db(loser_id,  round(new_l, 2))

        print(f"  🏆 Elo: #{winner_id}: {rating_w:.0f}→{new_w:.0f} | "
              f"#{loser_id}: {rating_l:.0f}→{new_l:.0f}")

        return {
            'winner_new_elo': round(new_w, 2),
            'loser_new_elo':  round(new_l, 2),
            'winner_change':  round(new_w - rating_w, 2),
            'loser_change':   round(new_l - rating_l, 2),
        }

    def save_prediction(self, partita_id: int,
                        prediction: dict[str, object],
                        icona: str = '🏀') -> None:
        """Salva la previsione nel database."""
        existing = DB.fetch_one(
            "SELECT id FROM previsioni WHERE partita_id = %s", (partita_id,)
        )
        if existing is not None:
            DB.execute(
                """UPDATE previsioni
                   SET prob_casa=%s, prob_pareggio=NULL, prob_trasferta=%s,
                       tipo_modello=%s, calcolata_il=NOW()
                   WHERE partita_id=%s""",
                (prediction['prob_home'], prediction['prob_away'],
                 prediction['model'], partita_id)
            )
        else:
            DB.execute(
                """INSERT INTO previsioni
                   (partita_id, tipo_modello, prob_casa, prob_pareggio, prob_trasferta)
                   VALUES (%s, %s, %s, NULL, %s)""",
                (partita_id, prediction['model'],
                 prediction['prob_home'], prediction['prob_away'])
            )

        print(f"  {icona} Previsione Elo: "
              f"1={prediction['prob_home']:.1%} "   # type: ignore
              f"2={prediction['prob_away']:.1%} "   # type: ignore
              f"(Diff: {prediction['elo_diff']:+.0f})")  # type: ignore

    # ── PRIVATI ──────────────────────────────────────────────

    def _get_rating(self, team_id: int) -> float:
        result = DB.fetch_one(
            "SELECT elo_rating FROM squadre WHERE id = %s", (team_id,)
        )
        if result and result['elo_rating'] is not None:
            return float(result['elo_rating'])
        return self.DEFAULT_RATING

    def _update_rating_db(self, team_id: int, new_rating: float) -> None:
        DB.execute(
            "UPDATE squadre SET elo_rating = %s WHERE id = %s",
            (new_rating, team_id)
        )


# --- Test standalone ---
if __name__ == '__main__':
    model = EloModel()
    print("Tabella probabilità per differenze Elo:")
    print(f"{'Diff':>8} | {'P(Fav)':>10} | {'P(Sfav)':>10}")
    print("-" * 35)
    for diff in [0, 50, 100, 150, 200, 300, 400, 500]:
        p = model.expected_score(1500 + diff, 1500)
        print(f"{'+' + str(diff):>8} | {p:>9.1%} | {1-p:>9.1%}")
