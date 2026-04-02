# python/settle_bets.py
"""
Aggiorna le scommesse degli utenti basandosi
sui risultati delle value bets.
"""

from __future__ import annotations
from typing import Any, Optional
from db_connector import DB


def settle_all_bets() -> None:
    """Trova scommesse pending con value bet risolta e le aggiorna."""

    print("=" * 60)
    print("💰 OddsLab — Settle Bets")
    print("=" * 60)

    # Trova scommesse pending la cui value bet è già risolta
    pending: list[dict[str, Any]] = DB.fetch_all(
        """SELECT
             s.id AS scommessa_id,
             s.utente_id,
             s.importo_puntato,
             s.profitto_potenziale,
             vb.stato AS vb_stato,
             vb.valore_quota,
             sc.nome AS casa,
             st.nome AS trasferta
           FROM scommesse s
           JOIN value_bets vb ON s.value_bet_id = vb.id
           JOIN partite p ON vb.partita_id = p.id
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           WHERE s.risultato = 'pending'
             AND vb.stato IN ('won', 'lost', 'void')"""
    )

    if not pending:
        print("\n  ℹ️  Nessuna scommessa da aggiornare.")
        print("     Tutte le scommesse pending hanno value bets ancora aperte.")
        return

    print(f"\n  📋 {len(pending)} scommesse da aggiornare\n")

    won_count = 0
    lost_count = 0
    void_count = 0

    for bet in pending:
        sid: int = int(bet['scommessa_id'])
        uid: int = int(bet['utente_id'])
        importo: float = float(bet['importo_puntato'])
        profitto_pot: float = float(bet['profitto_potenziale'])
        vb_stato: str = str(bet['vb_stato'])
        match_name: str = f"{bet['casa']} vs {bet['trasferta']}"

        # Calcola profitto reale
        if vb_stato == 'won':
            profitto_reale = profitto_pot
            rimborso = importo + profitto_pot  # restituisci puntata + profitto
            won_count += 1
            emoji = "✅"
        elif vb_stato == 'lost':
            profitto_reale = -importo
            rimborso = 0.0  # perdi tutto
            lost_count += 1
            emoji = "❌"
        else:  # void
            profitto_reale = 0.0
            rimborso = importo  # restituisci solo la puntata
            void_count += 1
            emoji = "⚪"

        # Aggiorna la scommessa
        DB.execute(
            """UPDATE scommesse
               SET risultato = %s, profitto_reale = %s
               WHERE id = %s""",
            (vb_stato, profitto_reale, sid)
        )

        # Aggiorna il bankroll dell'utente
        if rimborso > 0:
            DB.execute(
                """UPDATE utenti
                   SET bankroll_attuale = bankroll_attuale + %s
                   WHERE id = %s""",
                (rimborso, uid)
            )

        # Log nello storico bankroll
        user: Optional[dict[str, Any]] = DB.fetch_one(
            "SELECT bankroll_attuale FROM utenti WHERE id = %s",
            (uid,)
        )

        if user is not None:
            new_bankroll = float(user['bankroll_attuale'])
            DB.execute(
                """INSERT INTO storico_bankroll
                   (utente_id, importo_attuale, variazione, scommessa_id)
                   VALUES (%s, %s, %s, %s)""",
                (uid, new_bankroll, rimborso, sid)
            )

        print(
            f"  {emoji} Scommessa #{sid}: {match_name} → "
            f"{vb_stato.upper()} | "
            f"Puntato: €{importo:.2f} | "
            f"Profitto: €{profitto_reale:+.2f}"
        )

    # Riepilogo
    print(f"\n{'=' * 60}")
    print(f"  ✅ Vinte:    {won_count}")
    print(f"  ❌ Perse:    {lost_count}")
    print(f"  ⚪ Void:     {void_count}")
    print(f"  📊 Totale:   {len(pending)}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    try:
        settle_all_bets()
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DB.close()