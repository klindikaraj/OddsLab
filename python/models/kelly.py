# python/models/kelly.py
"""
Kelly Criterion — Calcolo dello stake ottimale.

Formula: f* = (p × b - 1) / (b - 1)
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB


@dataclass
class KellyResult:
    """Risultato del calcolo Kelly Criterion."""
    edge: float
    kelly_full_pct: float
    kelly_adj_pct: float
    stake_full: float
    stake_adjusted: float
    confidence: str


class KellyCriterion:
    """Implementazione del Criterio di Kelly."""

    MAX_STAKE_PCT: float = 0.10
    MIN_VALUE_THRESHOLD: float = 0.02

    def calculate(self, prob_model: float, odds: float,
                  bankroll: float,
                  kelly_fraction: float = 0.5) -> KellyResult:
        """Calcola lo stake ottimale."""
        edge: float = (prob_model * odds) - 1

        if edge <= 0:
            return KellyResult(
                edge=round(edge, 4),
                kelly_full_pct=0.0,
                kelly_adj_pct=0.0,
                stake_full=0.0,
                stake_adjusted=0.0,
                confidence='NONE'
            )

        kelly_full: float = (prob_model * odds - 1) / (odds - 1)
        kelly_full = min(kelly_full, self.MAX_STAKE_PCT)
        kelly_adj: float = kelly_full * kelly_fraction

        stake_full: float = round(bankroll * kelly_full, 2)
        stake_adj: float = round(bankroll * kelly_adj, 2)

        confidence: str = self._classify(edge)

        return KellyResult(
            edge=round(edge, 4),
            kelly_full_pct=round(kelly_full * 100, 2),
            kelly_adj_pct=round(kelly_adj * 100, 2),
            stake_full=stake_full,
            stake_adjusted=stake_adj,
            confidence=confidence
        )

    def _classify(self, edge: float) -> str:
        """Classifica il livello di confidenza."""
        if edge < self.MIN_VALUE_THRESHOLD:
            return 'SKIP'
        elif edge < 0.05:
            return 'LOW'
        elif edge < 0.10:
            return 'MEDIUM'
        elif edge < 0.20:
            return 'HIGH'
        else:
            return 'ULTRA'

    def calculate_for_match(self, partita_id: int,
                            utente_id: int) -> list[dict]:
        """Calcola Kelly per tutti gli esiti di una partita."""
        user: Optional[dict] = DB.fetch_one(
            """SELECT bankroll_attuale, kelly_fraction
               FROM utenti WHERE id = %s""",
            (utente_id,)
        )

        if user is None:
            print(f"  ⚠️ Utente #{utente_id} non trovato")
            return []

        pred: Optional[dict] = DB.fetch_one(
            """SELECT prob_casa, prob_pareggio, prob_trasferta
               FROM previsioni WHERE partita_id = %s""",
            (partita_id,)
        )

        if pred is None:
            print(f"  ⚠️ Nessuna previsione per partita "
                  f"#{partita_id}")
            return []

        best_odds: list[dict] = DB.fetch_all(
            """SELECT
                 q.esito,
                 MAX(q.valore_quota) AS best_quota,
                 (SELECT b.nome
                  FROM bookmaker b
                  JOIN quote q2 ON b.id = q2.bookmaker_id
                  WHERE q2.partita_id = q.partita_id
                    AND q2.esito = q.esito
                  ORDER BY q2.valore_quota DESC
                  LIMIT 1) AS best_bookmaker
               FROM quote q
               WHERE partita_id = %s
                 AND tipo_mercato = 'h2h'
               GROUP BY q.esito, q.partita_id""",
            (partita_id,)
        )

        prob_map: dict[str, float] = {
            'home': float(pred['prob_casa'] or 0),
            'draw': float(pred['prob_pareggio'] or 0),
            'away': float(pred['prob_trasferta'] or 0)
        }

        results: list[dict] = []

        for odd in best_odds:
            esito: str = str(odd['esito'])
            prob: float = prob_map.get(esito, 0.0)

            if prob <= 0:
                continue

            kelly = self.calculate(
                prob_model=prob,
                odds=float(odd['best_quota']),
                bankroll=float(user['bankroll_attuale']),
                kelly_fraction=float(user['kelly_fraction'])
            )

            results.append({
                'esito':        esito,
                'best_quota':   float(odd['best_quota']),
                'bookmaker':    str(odd['best_bookmaker']),
                'prob_modello': prob,
                'kelly':        kelly
            })

        return results


# --- Test standalone ---
if __name__ == '__main__':
    kc = KellyCriterion()

    print("=" * 50)
    print("  🧮 Test Kelly Criterion")
    print("=" * 50)

    result = kc.calculate(
        prob_model=0.482, odds=2.40,
        bankroll=1000.00, kelly_fraction=0.50
    )
    print(f"\n  Edge:       {result.edge:.2%}")
    print(f"  Full Kelly: {result.kelly_full_pct}%")
    print(f"  Half Kelly: {result.kelly_adj_pct}%")
    print(f"  Punta:      €{result.stake_adjusted}")
    print(f"  Confidenza: {result.confidence}")