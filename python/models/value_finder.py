# python/models/value_finder.py
"""
ValueFinder — il cuore di OddsLab.
Confronta le probabilità del modello con le quote dei bookmaker.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB
from models.kelly import KellyCriterion
from config import MIN_VALUE_THRESHOLD


class ValueFinder:
    """Trova Value Bets confrontando modello vs bookmaker."""

    def __init__(self) -> None:
        self.kelly = KellyCriterion()

    def find_value_bets(self, partita_id: int) -> list[dict]:
        """Cerca value bets per una partita specifica."""
        pred: Optional[dict] = DB.fetch_one(
            """SELECT prob_casa, prob_pareggio, prob_trasferta,
                      tipo_modello
               FROM previsioni
               WHERE partita_id = %s""",
            (partita_id,)
        )

        if pred is None:
            return []

        prob_map: dict[str, float] = {
            'home': float(pred['prob_casa'] or 0),
            'away': float(pred['prob_trasferta'] or 0),
        }
        if pred['prob_pareggio'] is not None:
            prob_map['draw'] = float(pred['prob_pareggio'])

        best_odds: list[dict] = DB.fetch_all(
            """SELECT
                 q.esito,
                 MAX(q.valore_quota) AS best_quota,
                 (SELECT q2.bookmaker_id
                  FROM quote q2
                  WHERE q2.partita_id = q.partita_id
                    AND q2.esito = q.esito
                  ORDER BY q2.valore_quota DESC
                  LIMIT 1) AS best_bookmaker_id,
                 (SELECT b.nome
                  FROM bookmaker b
                  JOIN quote q3 ON b.id = q3.bookmaker_id
                  WHERE q3.partita_id = q.partita_id
                    AND q3.esito = q.esito
                  ORDER BY q3.valore_quota DESC
                  LIMIT 1) AS best_bookmaker_nome
               FROM quote q
               WHERE q.partita_id = %s
                 AND q.tipo_mercato = 'h2h'
               GROUP BY q.esito, q.partita_id""",
            (partita_id,)
        )

        value_bets_found: list[dict] = []

        for odd in best_odds:
            esito: str = str(odd['esito'])
            quota: float = float(odd['best_quota'])
            prob_modello: Optional[float] = prob_map.get(esito)

            if prob_modello is None or prob_modello <= 0:
                continue

            value: float = (prob_modello * quota) - 1
            prob_implicita: float = 1 / quota

            if value >= MIN_VALUE_THRESHOLD:
                kelly_result = self.kelly.calculate(
                    prob_model=prob_modello,
                    odds=quota,
                    bankroll=1000.0,
                    kelly_fraction=1.0
                )

                vb: dict = {
                    'partita_id':      partita_id,
                    'bookmaker_id':    int(odd['best_bookmaker_id']),
                    'bookmaker_nome':  str(odd['best_bookmaker_nome']),
                    'esito':           esito,
                    'valore_quota':    quota,
                    'prob_modello':    prob_modello,
                    'prob_implicita':  round(prob_implicita, 4),
                    'valore_perc':     round(value, 4),
                    'stake_kelly_pct': round(
                        kelly_result.kelly_full_pct / 100, 4
                    ),
                    'confidence':      kelly_result.confidence
                }

                value_bets_found.append(vb)

                print(
                    f"  🔥 VALUE BET! "
                    f"{esito} @ {quota} "
                    f"({odd['best_bookmaker_nome']}) | "
                    f"Value: {value:.1%} | "
                    f"Conf: {kelly_result.confidence}"
                )

        for vb in value_bets_found:
            self._save_value_bet(vb)

        if not value_bets_found:
            print(f"  ℹ️  Nessuna value bet per partita "
                  f"#{partita_id}")

        return value_bets_found

    def find_all_pending(self) -> list[dict]:
        """Cerca value bets per TUTTE le partite future."""
        partite: list[dict] = DB.fetch_all(
            """SELECT p.id, sc.nome AS casa, st.nome AS trasf
               FROM partite p
               JOIN previsioni pr ON p.id = pr.partita_id
               JOIN squadre sc ON p.squadra_casa_id = sc.id
               JOIN squadre st ON p.squadra_trasf_id = st.id
               WHERE p.stato = 'programmata'
                 AND p.data_ora > NOW()
               ORDER BY p.data_ora ASC"""
        )

        all_vb: list[dict] = []
        print(f"\n🔍 Analizzando {len(partite)} partite...\n")

        for match in partite:
            print(f"📋 {match['casa']} vs {match['trasf']} "
                  f"(#{match['id']})")
            vbs = self.find_value_bets(int(match['id']))
            all_vb.extend(vbs)

        print(f"\n{'=' * 50}")
        print(f"🔥 Totale Value Bets: {len(all_vb)}")
        print(f"{'=' * 50}")

        return all_vb

    def _save_value_bet(self, vb: dict) -> None:
        """Salva una value bet nel database."""
        existing: Optional[dict] = DB.fetch_one(
            """SELECT id FROM value_bets
               WHERE partita_id = %s
                 AND bookmaker_id = %s
                 AND esito = %s
                 AND stato = 'pending'""",
            (vb['partita_id'], vb['bookmaker_id'], vb['esito'])
        )

        if existing is not None:
            DB.execute(
                """UPDATE value_bets
                   SET valore_quota = %s,
                       valore_perc = %s,
                       stake_kelly_pct = %s
                   WHERE id = %s""",
                (vb['valore_quota'], vb['valore_perc'],
                 vb['stake_kelly_pct'], int(existing['id']))
            )
        else:
            DB.execute(
                """INSERT INTO value_bets
                   (partita_id, bookmaker_id, esito,
                    valore_quota, prob_modello, valore_perc,
                    stake_kelly_pct)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (vb['partita_id'], vb['bookmaker_id'],
                 vb['esito'], vb['valore_quota'],
                 vb['prob_modello'], vb['valore_perc'],
                 vb['stake_kelly_pct'])
            )


# --- Test standalone ---
if __name__ == '__main__':
    finder = ValueFinder()
    finder.find_all_pending()