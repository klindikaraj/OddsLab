# python/fix_tennis.py
"""
Script una-tantum: annulla tutte le scommesse su partite di tennis
e restituisce il bankroll agli utenti.
Tennis rimosso dal sistema — le value bets vanno messe a 'void'.
"""
from db_connector import DB

def fix():
    print("=" * 60)
    print("🎾 FIX: Annullamento scommesse tennis")
    print("=" * 60)

    # Trova tutte le scommesse pending su partite di campionati tennis
    scommesse = DB.fetch_all(
        """SELECT s.id AS sid, s.utente_id, s.importo_puntato,
                  vb.id AS vbid, p.id AS pid,
                  sc.nome AS casa, st.nome AS trasf
           FROM scommesse s
           JOIN value_bets vb ON s.value_bet_id = vb.id
           JOIN partite p ON vb.partita_id = p.id
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           JOIN campionati c ON p.campionato_id = c.id
           WHERE s.risultato = 'pending'
             AND c.api_key LIKE 'tennis_%'"""
    )

    if not scommesse:
        print("  ✅ Nessuna scommessa tennis pending trovata")
        DB.close()
        return

    print(f"  Trovate {len(scommesse)} scommesse da annullare:\n")

    for s in scommesse:
        sid     = int(s['sid'])
        uid     = int(s['utente_id'])
        importo = float(s['importo_puntato'])
        vbid    = int(s['vbid'])
        pid     = int(s['pid'])

        print(f"  #{sid} | {s['casa']} vs {s['trasf']} | €{importo:.2f}")

        # 1. Segna scommessa come void
        DB.execute(
            "UPDATE scommesse SET risultato='void', profitto_reale=0 WHERE id=%s",
            (sid,)
        )

        # 2. Restituisci puntata al bankroll
        DB.execute(
            "UPDATE utenti SET bankroll_attuale = bankroll_attuale + %s WHERE id=%s",
            (importo, uid)
        )

        # 3. Log storico bankroll
        user = DB.fetch_one("SELECT bankroll_attuale FROM utenti WHERE id=%s", (uid,))
        if user:
            DB.execute(
                "INSERT INTO storico_bankroll (utente_id, importo_attuale, variazione, scommessa_id) VALUES (%s,%s,%s,%s)",
                (uid, float(user['bankroll_attuale']), importo, sid)
            )

        # 4. Segna value bet come void
        DB.execute(
            "UPDATE value_bets SET stato='void' WHERE id=%s",
            (vbid,)
        )

        # 5. Segna partita come annullata
        DB.execute(
            "UPDATE partite SET stato='annullata' WHERE id=%s",
            (pid,)
        )

        print(f"    ✅ Void — €{importo:.2f} restituiti")

    print(f"\n  ✅ Fix completato. {len(scommesse)} scommesse annullate.")
    DB.close()

if __name__ == '__main__':
    fix()
