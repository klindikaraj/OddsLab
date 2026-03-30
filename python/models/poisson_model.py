# python/models/poisson_model.py
"""
Modello di Distribuzione di Poisson per prevedere
il risultato di partite di calcio.
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB


class PoissonModel:
    """Previsione risultati calcio con distribuzione di Poisson."""

    MAX_GOALS: int = 6
    DEFAULT_AVG: float = 1.35

    def _poisson_pmf(self, k: int, lam: float) -> float:
        """Probability Mass Function di Poisson."""
        return (lam ** k) * math.exp(-lam) / math.factorial(k)

    def get_team_stats(self, team_id: int) -> dict[str, float]:
        """Recupera le statistiche della squadra dal DB."""
        result: Optional[dict] = DB.fetch_one(
            """SELECT
                 gol_fatti_avg  AS attack,
                 gol_subiti_avg AS defense
               FROM squadre WHERE id = %s""",
            (team_id,)
        )

        if (result is not None
                and result['attack'] is not None
                and result['defense'] is not None):
            return {
                'attack':  float(result['attack']),
                'defense': float(result['defense'])
            }

        return {'attack': self.DEFAULT_AVG,
                'defense': self.DEFAULT_AVG}

    def get_league_average(self, campionato_id: int) -> float:
        """Media gol per squadra per partita del campionato."""
        result: Optional[dict] = DB.fetch_one(
            """SELECT AVG(score_casa + score_trasferta)
                      AS avg_total_goals
               FROM partite
               WHERE campionato_id = %s
                 AND stato = 'conclusa'""",
            (campionato_id,)
        )

        if (result is not None
                and result['avg_total_goals'] is not None):
            return float(result['avg_total_goals']) / 2
        return self.DEFAULT_AVG

    def predict(self, home_id: int, away_id: int,
                campionato_id: int) -> dict[str, object]:
        """Calcola le probabilità 1X2 per una partita di calcio."""
        league_avg = self.get_league_average(campionato_id)
        home = self.get_team_stats(home_id)
        away = self.get_team_stats(away_id)

        home_att_strength = home['attack'] / league_avg
        home_def_strength = home['defense'] / league_avg
        away_att_strength = away['attack'] / league_avg
        away_def_strength = away['defense'] / league_avg

        lambda_home = (home_att_strength
                       * away_def_strength
                       * league_avg)
        lambda_away = (away_att_strength
                       * home_def_strength
                       * league_avg)

        lambda_home = max(lambda_home, 0.20)
        lambda_away = max(lambda_away, 0.20)

        prob_home: float = 0.0
        prob_draw: float = 0.0
        prob_away: float = 0.0
        score_matrix: dict[str, float] = {}

        for i in range(self.MAX_GOALS + 1):
            for j in range(self.MAX_GOALS + 1):
                p = (self._poisson_pmf(i, lambda_home)
                     * self._poisson_pmf(j, lambda_away))

                score_matrix[f"{i}-{j}"] = round(p, 4)

                if i > j:
                    prob_home += p
                elif i == j:
                    prob_draw += p
                else:
                    prob_away += p

        # ===== NORMALIZZAZIONE =====
        # Quando i lambda sono molto alti, parte della probabilità
        # cade oltre MAX_GOALS. Normalizziamo per farle sommare a 1.0
        total = prob_home + prob_draw + prob_away
        if total > 0 and total != 1.0:
            prob_home = prob_home / total
            prob_draw = prob_draw / total
            prob_away = prob_away / total

        most_likely = max(score_matrix,
                          key=score_matrix.get)  # type: ignore

        return {
            'prob_home':    round(prob_home, 4),
            'prob_draw':    round(prob_draw, 4),
            'prob_away':    round(prob_away, 4),
            'lambda_home':  round(lambda_home, 2),
            'lambda_away':  round(lambda_away, 2),
            'most_likely':  most_likely,
            'most_likely_p': score_matrix[most_likely],
            'model':        'poisson'
        }

    def save_prediction(self, partita_id: int,
                        prediction: dict[str, object]) -> None:
        """Salva la previsione nel database."""
        existing: Optional[dict] = DB.fetch_one(
            "SELECT id FROM previsioni WHERE partita_id = %s",
            (partita_id,)
        )

        if existing is not None:
            DB.execute(
                """UPDATE previsioni
                   SET prob_casa = %s,
                       prob_pareggio = %s,
                       prob_trasferta = %s,
                       tipo_modello = %s,
                       calcolata_il = NOW()
                   WHERE partita_id = %s""",
                (prediction['prob_home'],
                 prediction['prob_draw'],
                 prediction['prob_away'],
                 prediction['model'],
                 partita_id)
            )
        else:
            DB.execute(
                """INSERT INTO previsioni
                   (partita_id, tipo_modello, prob_casa,
                    prob_pareggio, prob_trasferta)
                   VALUES (%s, %s, %s, %s, %s)""",
                (partita_id,
                 prediction['model'],
                 prediction['prob_home'],
                 prediction['prob_draw'],
                 prediction['prob_away'])
            )

        print(
            f"  📊 Previsione salvata: "
            f"1={prediction['prob_home']:.1%} "  # type: ignore
            f"X={prediction['prob_draw']:.1%} "  # type: ignore
            f"2={prediction['prob_away']:.1%} "  # type: ignore
            f"(Più probabile: {prediction['most_likely']})"
        )


# --- Test standalone ---
if __name__ == '__main__':
    model = PoissonModel()
    print("=== Test Poisson Model ===\n")

    la = (1.8 / 1.35) * (1.0 / 1.35) * 1.35
    lb = (1.7 / 1.35) * (0.9 / 1.35) * 1.35

    prob_h = prob_d = prob_a = 0.0
    for i in range(7):
        for j in range(7):
            p = model._poisson_pmf(i, la) * model._poisson_pmf(j, lb)
            if i > j:
                prob_h += p
            elif i == j:
                prob_d += p
            else:
                prob_a += p

    total = prob_h + prob_d + prob_a
    prob_h /= total
    prob_d /= total
    prob_a /= total

    print(f"Lambda Casa:      {la:.2f}")
    print(f"Lambda Trasferta: {lb:.2f}")
    print(f"P(Casa):  {prob_h:.1%}")
    print(f"P(Pareg): {prob_d:.1%}")
    print(f"P(Trasf): {prob_a:.1%}")
    print(f"Somma:    {prob_h + prob_d + prob_a:.1%}")