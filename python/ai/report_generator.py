# python/ai/report_generator.py
"""
Genera report pre-match narrativi usando OpenAI GPT.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from db_connector import DB
from config import OPENAI_API_KEY


class ReportGenerator:
    """Genera report pre-match usando GPT."""

    SYSTEM_PROMPT: str = """Sei un analista sportivo professionista 
italiano. Ricevi dati statistici su un match e devi generare 
un report di analisi in italiano di massimo 250 parole.

Il report deve:
1. Spiegare PERCHÉ il modello ha trovato valore
2. Evidenziare i fattori chiave
3. Dare un giudizio sulla confidenza del segnale
4. Specificare l'importo consigliato da puntare
5. Includere un DISCLAIMER

Formato: paragrafi brevi e numeri concreti.
Tono: professionale ma accessibile."""

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            print(
                "⚠️  OPENAI_API_KEY non configurata. "
                "Uso modalità fallback."
            )
            self.client: Optional[OpenAI] = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate(self, partita_id: int,
                 kelly_results: Optional[list[dict]] = None
                 ) -> str:
        """Genera il report IA per una partita."""
        if self.client is None:
            return self._generate_fallback(partita_id)

        match_data: list[dict] = self._get_match_data(partita_id)
        if not match_data:
            return "⚠️ Dati insufficienti per generare il report."

        user_prompt: str = self._build_prompt(
            match_data, kelly_results or []
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": self.SYSTEM_PROMPT},
                    {"role": "user",
                     "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            content = response.choices[0].message.content
            report_text: str = content if content is not None else ""

            self._save_report(partita_id, report_text)

            print(f"  🤖 Report IA generato per partita "
                  f"#{partita_id}")
            return report_text

        except Exception as e:
            print(f"  ❌ Errore OpenAI: {e}")
            return self._generate_fallback(partita_id)

    def _generate_fallback(self, partita_id: int) -> str:
        """Genera un report basico SENZA OpenAI."""
        match_data: list[dict] = self._get_match_data(partita_id)
        if not match_data:
            return "Dati non disponibili."

        m: dict = match_data[0]

        vbs: list[dict] = DB.fetch_all(
            """SELECT esito, valore_quota, prob_modello,
                      valore_perc
               FROM value_bets
               WHERE partita_id = %s AND stato = 'pending'""",
            (partita_id,)
        )

        prob_casa: float = float(m.get('prob_casa') or 0)
        prob_pareg: float = float(m.get('prob_pareggio') or 0)
        prob_trasf: float = float(m.get('prob_trasferta') or 0)

        report: str = (
            f"📊 REPORT — {m['casa']} vs {m['trasferta']}\n"
            f"{'=' * 50}\n"
            f"🏆 {m['campionato']} ({m['sport']})\n"
            f"📅 {m['data_ora']}\n\n"
            f"📈 PREVISIONI ({m.get('tipo_modello', 'N/A')}):\n"
            f"• {m['casa']}: {prob_casa:.1%}\n"
            f"• Pareggio: {prob_pareg:.1%}\n"
            f"• {m['trasferta']}: {prob_trasf:.1%}\n"
        )

        if vbs:
            report += f"\n🔥 VALUE BETS: {len(vbs)}\n"
            for vb in vbs:
                esito_label: str = {
                    'home': str(m['casa']),
                    'draw': 'Pareggio',
                    'away': str(m['trasferta'])
                }.get(str(vb['esito']), str(vb['esito']))

                val_perc: float = float(vb['valore_perc'])
                report += (
                    f"• {esito_label} @ {vb['valore_quota']} "
                    f"| Value: {val_perc:.1%}\n"
                )
        else:
            report += "\nℹ️ Nessuna value bet trovata.\n"

        report += (
            "\n⚠️ DISCLAIMER: Analisi puramente statistica. "
            "Non costituisce consiglio finanziario."
        )

        self._save_report(partita_id, report)
        return report

    def _get_match_data(self, partita_id: int) -> list[dict]:
        """Recupera tutti i dati di un match dal DB."""
        return DB.fetch_all(
            """SELECT
                p.data_ora,
                sc.nome AS casa,
                sc.elo_rating AS elo_casa,
                sc.gol_fatti_avg AS gf_casa,
                sc.gol_subiti_avg AS gs_casa,
                st.nome AS trasferta,
                st.elo_rating AS elo_trasf,
                st.gol_fatti_avg AS gf_trasf,
                st.gol_subiti_avg AS gs_trasf,
                pr.prob_casa,
                pr.prob_pareggio,
                pr.prob_trasferta,
                pr.tipo_modello,
                c.nome AS campionato,
                s.nome AS sport
            FROM partite p
            JOIN squadre sc ON p.squadra_casa_id = sc.id
            JOIN squadre st ON p.squadra_trasf_id = st.id
            LEFT JOIN previsioni pr ON p.id = pr.partita_id
            JOIN campionati c ON p.campionato_id = c.id
            JOIN sport s ON p.sport_id = s.id
            WHERE p.id = %s""",
            (partita_id,)
        )

    def _build_prompt(self, match_data: list[dict],
                      kelly_results: list[dict]) -> str:
        """Costruisce il prompt per OpenAI."""
        m: dict = match_data[0]

        kelly_text: str = ""
        for kr in kelly_results:
            kelly_obj = kr.get('kelly')
            if kelly_obj is not None and hasattr(kelly_obj, 'confidence'):
                if kelly_obj.confidence != 'SKIP':
                    prob_m: float = float(kr.get('prob_modello', 0))
                    kelly_text += (
                        f"\n- Esito '{kr['esito']}': "
                        f"quota {kr['best_quota']} "
                        f"({kr.get('bookmaker', 'N/A')}), "
                        f"prob modello {prob_m:.1%}, "
                        f"value {kelly_obj.edge:.1%}, "
                        f"stake €{kelly_obj.stake_adjusted} "
                        f"(confidenza: {kelly_obj.confidence})"
                    )

        prob_casa: float = float(m.get('prob_casa') or 0)
        prob_pareg: float = float(m.get('prob_pareggio') or 0)
        prob_trasf: float = float(m.get('prob_trasferta') or 0)

        return f"""
MATCH: {m['casa']} vs {m['trasferta']}
CAMPIONATO: {m['campionato']} ({m['sport']})
DATA: {m['data_ora']}

STATISTICHE {m['casa']}:
- Elo Rating: {m.get('elo_casa', 'N/A')}
- Media gol fatti: {m.get('gf_casa', 'N/A')}
- Media gol subiti: {m.get('gs_casa', 'N/A')}

STATISTICHE {m['trasferta']}:
- Elo Rating: {m.get('elo_trasf', 'N/A')}
- Media gol fatti: {m.get('gf_trasf', 'N/A')}
- Media gol subiti: {m.get('gs_trasf', 'N/A')}

PREVISIONI MODELLO ({m.get('tipo_modello', 'N/A')}):
- Vittoria casa: {prob_casa:.1%}
- Pareggio: {prob_pareg:.1%}
- Vittoria trasferta: {prob_trasf:.1%}

VALUE BETS: {kelly_text if kelly_text else 'Nessuna'}

Genera il report di analisi pre-match.
"""

    def _save_report(self, partita_id: int,
                     testo: str) -> None:
        """Salva il report nel database."""
        DB.execute(
            "DELETE FROM report_ia WHERE partita_id = %s",
            (partita_id,)
        )

        DB.execute(
            """INSERT INTO report_ia (partita_id, testo)
               VALUES (%s, %s)""",
            (partita_id, testo)
        )


# --- Test standalone ---
if __name__ == '__main__':
    gen = ReportGenerator()
    print("=== Test Report Generator ===")

    if gen.client is not None:
        print("✅ OpenAI configurata")
    else:
        print("⚠️  Modalità fallback")

    partita: Optional[dict] = DB.fetch_one(
        """SELECT id FROM partite
           WHERE stato = 'programmata' LIMIT 1"""
    )

    if partita is not None:
        report = gen._generate_fallback(int(partita['id']))
        print(report)
    else:
        print("Nessuna partita trovata.")