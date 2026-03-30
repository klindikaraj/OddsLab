# python/seed_team_stats.py
"""
OddsLab — Seed Team Stats
Risolve il Cold Start Problem.

Calcola statistiche iniziali REALISTICHE per ogni squadra
basandosi sulle quote medie dei bookmaker.

Logica:
- Se una squadra è quotata mediamente a 1.50 in casa,
  i bookmaker la considerano forte → Elo alto, molti gol fatti
- Se è quotata a 4.00, è debole → Elo basso
- Le quote contengono informazione sulla forza reale delle squadre

Esegui UNA VOLTA dopo il primo python main.py --collect
"""

from __future__ import annotations

import math
from typing import Any, Optional
from db_connector import DB


def implied_probability(odds: float) -> float:
    """Converti quota decimale in probabilità implicita."""
    return 1.0 / odds if odds > 0 else 0.0


def prob_to_elo_diff(prob: float) -> float:
    """
    Converti una probabilità di vittoria in differenza Elo.
    Formula inversa: diff = -400 × log10(1/p - 1)
    """
    if prob <= 0.01:
        prob = 0.01
    if prob >= 0.99:
        prob = 0.99
    return -400.0 * math.log10((1.0 / prob) - 1.0)


def prob_to_goals(prob_home: float, prob_draw: float,
                  prob_away: float, is_home: bool) -> tuple[float, float]:
    """
    Stima gol fatti/subiti medi a partire dalle probabilità.
    
    Logica approssimata:
    - Se prob vittoria alta → molti gol fatti, pochi subiti
    - Media Serie A: ~2.7 gol/partita totali
    """
    avg_total_goals = 2.70  # media storica

    if is_home:
        # Fattore casa: squadra di casa segna di più
        strength = prob_home / (prob_home + prob_away) if (prob_home + prob_away) > 0 else 0.5
    else:
        strength = prob_away / (prob_home + prob_away) if (prob_home + prob_away) > 0 else 0.5

    # Gol fatti proporzionali alla forza
    gol_fatti = avg_total_goals * strength
    gol_fatti = max(0.40, min(3.00, gol_fatti))  # limiti ragionevoli

    # Gol subiti inversamente proporzionali
    gol_subiti = avg_total_goals * (1 - strength)
    gol_subiti = max(0.40, min(2.50, gol_subiti))

    return round(gol_fatti, 2), round(gol_subiti, 2)


def seed_stats() -> None:
    """Calcola e salva statistiche per tutte le squadre."""

    print("=" * 60)
    print("🌱 OddsLab — Seed Team Stats (Cold Start Fix)")
    print("=" * 60)

    # Recupera tutte le squadre
    squadre: list[dict[str, Any]] = DB.fetch_all(
        """SELECT
             sq.id,
             sq.nome,
             sq.campionato_id,
             c.api_key AS camp_api,
             s.nome AS sport
           FROM squadre sq
           JOIN campionati c ON sq.campionato_id = c.id
           JOIN sport s ON c.sport_id = s.id
           ORDER BY s.nome, c.nome, sq.nome"""
    )

    print(f"\n📋 {len(squadre)} squadre da analizzare\n")

    updated = 0
    skipped = 0

    for sq in squadre:
        sq_id: int = int(sq['id'])
        sq_nome: str = str(sq['nome'])
        sport: str = str(sq['sport'])

        # ===== Calcola probabilità media dalle quote =====

        # Quote quando gioca IN CASA
        home_odds: Optional[dict[str, Any]] = DB.fetch_one(
            """SELECT
                 AVG(CASE WHEN q.esito = 'home' THEN q.valore_quota END) AS avg_home,
                 AVG(CASE WHEN q.esito = 'draw' THEN q.valore_quota END) AS avg_draw,
                 AVG(CASE WHEN q.esito = 'away' THEN q.valore_quota END) AS avg_away,
                 COUNT(DISTINCT p.id) AS n_partite
               FROM quote q
               JOIN partite p ON q.partita_id = p.id
               WHERE p.squadra_casa_id = %s
                 AND q.tipo_mercato = 'h2h'""",
            (sq_id,)
        )

        # Quote quando gioca IN TRASFERTA
        away_odds: Optional[dict[str, Any]] = DB.fetch_one(
            """SELECT
                 AVG(CASE WHEN q.esito = 'home' THEN q.valore_quota END) AS avg_home,
                 AVG(CASE WHEN q.esito = 'draw' THEN q.valore_quota END) AS avg_draw,
                 AVG(CASE WHEN q.esito = 'away' THEN q.valore_quota END) AS avg_away,
                 COUNT(DISTINCT p.id) AS n_partite
               FROM quote q
               JOIN partite p ON q.partita_id = p.id
               WHERE p.squadra_trasf_id = %s
                 AND q.tipo_mercato = 'h2h'""",
            (sq_id,)
        )

        # Raccogli le probabilità
        probs_home: list[float] = []  # prob vittoria quando gioca in casa
        probs_away: list[float] = []  # prob vittoria quando gioca fuori

        if home_odds is not None and home_odds['avg_home'] is not None:
            avg_h = float(home_odds['avg_home'])
            probs_home.append(implied_probability(avg_h))

        if away_odds is not None and away_odds['avg_away'] is not None:
            avg_a = float(away_odds['avg_away'])
            probs_away.append(implied_probability(avg_a))

        if not probs_home and not probs_away:
            print(f"  ⏭️  {sq_nome}: nessuna quota trovata, skip")
            skipped += 1
            continue

        # Probabilità media complessiva di vittoria
        all_probs = probs_home + probs_away
        avg_win_prob = sum(all_probs) / len(all_probs)

        # ===== Calcola Elo Rating =====
        base_elo = 1500.0
        elo_diff = prob_to_elo_diff(avg_win_prob)
        new_elo = round(base_elo + elo_diff, 2)
        # Limita tra 1200 e 1900
        new_elo = max(1200.0, min(1900.0, new_elo))

        # ===== Calcola Gol Fatti/Subiti (solo per calcio) =====
        gol_fatti: Optional[float] = None
        gol_subiti: Optional[float] = None

        if sport == 'Calcio':
            # Usa le quote in casa per stimare
            ph = avg_win_prob
            pd = 0.25  # stima pareggio
            pa = 1.0 - ph - pd
            if pa < 0.05:
                pa = 0.05
                pd = 1.0 - ph - pa

            gol_fatti, gol_subiti = prob_to_goals(ph, pd, pa, is_home=True)

        # ===== Salva nel DB =====
        if gol_fatti is not None:
            DB.execute(
                """UPDATE squadre
                   SET elo_rating = %s,
                       gol_fatti_avg = %s,
                       gol_subiti_avg = %s
                   WHERE id = %s""",
                (new_elo, gol_fatti, gol_subiti, sq_id)
            )
        else:
            DB.execute(
                """UPDATE squadre
                   SET elo_rating = %s
                   WHERE id = %s""",
                (new_elo, sq_id)
            )

        # Emoji in base alla forza
        if new_elo >= 1700:
            emoji = "🟢"
        elif new_elo >= 1550:
            emoji = "🟡"
        elif new_elo >= 1400:
            emoji = "🟠"
        else:
            emoji = "🔴"

        goals_str = ""
        if gol_fatti is not None:
            goals_str = f" | GF:{gol_fatti} GS:{gol_subiti}"

        print(
            f"  {emoji} {sq_nome:<30} "
            f"Elo: {new_elo:>7.0f} | "
            f"P(win): {avg_win_prob:>5.1%}"
            f"{goals_str}"
        )

        updated += 1

    print(f"\n{'=' * 60}")
    print(f"  ✅ Aggiornate: {updated} squadre")
    print(f"  ⏭️  Saltate:    {skipped} squadre")
    print(f"{'=' * 60}")


def reset_predictions() -> None:
    """
    Cancella le previsioni e value bets calcolate con i vecchi dati,
    così al prossimo python main.py vengono ricalcolate correttamente.
    """
    print("\n🗑️  Pulizia previsioni e value bets vecchie...")

    DB.execute("DELETE FROM report_ia")
    DB.execute("DELETE FROM value_bets WHERE stato = 'pending'")
    DB.execute("DELETE FROM previsioni")

    n_prev = DB.count("SELECT COUNT(*) AS n FROM previsioni")
    n_vb = DB.count("SELECT COUNT(*) AS n FROM value_bets WHERE stato = 'pending'")
    n_rep = DB.count("SELECT COUNT(*) AS n FROM report_ia")

    print(f"  Previsioni rimaste: {n_prev}")
    print(f"  Value Bets pending: {n_vb}")
    print(f"  Report IA:          {n_rep}")
    print("  ✅ Pulizia completata")


def show_summary() -> None:
    """Mostra un riepilogo delle statistiche per campionato."""
    print("\n📊 RIEPILOGO PER CAMPIONATO:")
    print(f"  {'Campionato':<25} {'Squadre':>8} {'Elo Min':>8} "
          f"{'Elo Avg':>8} {'Elo Max':>8}")
    print(f"  {'-' * 60}")

    camps: list[dict[str, Any]] = DB.fetch_all(
        """SELECT
             c.nome AS campionato,
             COUNT(sq.id) AS n,
             MIN(sq.elo_rating) AS elo_min,
             ROUND(AVG(sq.elo_rating)) AS elo_avg,
             MAX(sq.elo_rating) AS elo_max
           FROM squadre sq
           JOIN campionati c ON sq.campionato_id = c.id
           GROUP BY c.id, c.nome
           ORDER BY c.nome"""
    )

    for c in camps:
        print(
            f"  {str(c['campionato']):<25} "
            f"{c['n']:>8} "
            f"{float(c['elo_min'] or 0):>8.0f} "
            f"{float(c['elo_avg'] or 0):>8.0f} "
            f"{float(c['elo_max'] or 0):>8.0f}"
        )


if __name__ == '__main__':
    try:
        seed_stats()
        show_summary()
        reset_predictions()

        print("\n" + "=" * 60)
        print("  🚀 ORA RIESEGUI:  python main.py --predict --find")
        print("     Le previsioni saranno molto più accurate!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DB.close()