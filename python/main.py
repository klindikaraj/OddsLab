# python/main.py
"""
OddsLab — Script Principale (Orchestratore)

Uso:
    python main.py              → esegue tutto
    python main.py --collect    → solo raccolta quote
    python main.py --predict    → solo previsioni
    python main.py --find       → solo ricerca value bets
    python main.py --report     → solo generazione report
    python main.py --results    → solo aggiornamento risultati
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime
from typing import Optional

from config import SUPPORTED_SPORTS
from db_connector import DB
from collectors.odds_collector import OddsCollector
from collectors.results_collector import ResultsCollector
from models.poisson_model import PoissonModel
from models.elo_model import EloModel
from models.value_finder import ValueFinder
from ai.report_generator import ReportGenerator
from settle_bets import settle_all_bets


def setup_sport_and_league(sport_config: dict) -> tuple[int, int]:
    sport_row: Optional[dict] = DB.fetch_one(
        "SELECT id FROM sport WHERE nome = %s",
        (sport_config['sport'],)
    )
    if sport_row is not None:
        sport_id: int = int(sport_row['id'])
    else:
        sport_id = DB.execute(
            "INSERT INTO sport (nome, api_key, icona) VALUES (%s, %s, %s)",
            (sport_config['sport'], sport_config['sport'].lower(), sport_config['icona'])
        )
        print(f"  🆕 Sport creato: {sport_config['sport']} (ID: {sport_id})")

    camp_row: Optional[dict] = DB.fetch_one(
        "SELECT id FROM campionati WHERE api_key = %s",
        (sport_config['api_key'],)
    )
    if camp_row is not None:
        camp_id: int = int(camp_row['id'])
    else:
        camp_id = DB.execute(
            "INSERT INTO campionati (sport_id, nome, paese, api_key) VALUES (%s, %s, %s, %s)",
            (sport_id, sport_config['nome'], sport_config['paese'], sport_config['api_key'])
        )
        print(f"  🆕 Campionato creato: {sport_config['nome']} (ID: {camp_id})")

    return sport_id, camp_id


def step_collect() -> None:
    """STEP 1: Raccoglie quote live da The Odds API."""
    print("\n" + "=" * 60)
    print("📡 STEP 1: RACCOLTA QUOTE")
    print("=" * 60)

    collector = OddsCollector()

    for sport_cfg in SUPPORTED_SPORTS:
        print(f"\n{sport_cfg['icona']} {sport_cfg['nome']} ({sport_cfg['paese']})")
        print("-" * 40)
        sport_id, camp_id = setup_sport_and_league(sport_cfg)
        try:
            events = collector.get_odds(sport_cfg['api_key'])
            if events:
                stats = collector.save_to_db(events, sport_id, camp_id)
                print(f"  ✅ {stats['partite_nuove']} nuove partite, "
                      f"{stats['quote_inserite']} quote salvate")
            else:
                print("  ℹ️ Nessun evento trovato")
        except Exception as e:
            print(f"  ❌ Errore: {e}")
            continue


def step_predict() -> None:
    """STEP 2: Calcola previsioni per tutte le partite future."""
    print("\n" + "=" * 60)
    print("🧠 STEP 2: CALCOLO PREVISIONI")
    print("=" * 60)

    poisson = PoissonModel()
    elo     = EloModel()

    partite: list[dict] = DB.fetch_all(
        """SELECT p.id, p.squadra_casa_id, p.squadra_trasf_id,
                  p.campionato_id, sc.nome AS casa, st.nome AS trasferta,
                  c.api_key AS camp_api_key
           FROM partite p
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           JOIN campionati c ON p.campionato_id = c.id
           LEFT JOIN previsioni pr ON p.id = pr.partita_id
           WHERE p.stato = 'programmata' AND p.data_ora > NOW() AND pr.id IS NULL
           ORDER BY p.data_ora ASC"""
    )

    print(f"\n📋 {len(partite)} partite da analizzare\n")

    for match in partite:
        match_id = int(match['id'])
        casa_id  = int(match['squadra_casa_id'])
        trasf_id = int(match['squadra_trasf_id'])
        camp_id  = int(match['campionato_id'])
        camp_api = str(match['camp_api_key'])

        sport_cfg_match = next(
            (s for s in SUPPORTED_SPORTS if s['api_key'] == camp_api), None
        )
        icona = sport_cfg_match['icona'] if sport_cfg_match else '🏟️'

        print(f"{icona} {match['casa']} vs {match['trasferta']} (#{match_id})")

        if sport_cfg_match and sport_cfg_match['modello'] == 'elo':
            prediction = elo.predict(casa_id, trasf_id, camp_id)
            elo.save_prediction(match_id, prediction, icona=icona)
        else:
            prediction = poisson.predict(casa_id, trasf_id, camp_id)
            poisson.save_prediction(match_id, prediction)


def step_find_value() -> list[dict]:
    """STEP 3: Cerca Value Bets."""
    print("\n" + "=" * 60)
    print("🔍 STEP 3: RICERCA VALUE BETS")
    print("=" * 60)
    return ValueFinder().find_all_pending()


def step_generate_reports(value_bets: Optional[list[dict]] = None) -> None:
    """STEP 4: Genera report IA per le partite con value bets."""
    print("\n" + "=" * 60)
    print("🤖 STEP 4: GENERAZIONE REPORT IA")
    print("=" * 60)

    generator = ReportGenerator()
    partite: list[dict] = DB.fetch_all(
        """SELECT DISTINCT vb.partita_id, sc.nome AS casa, st.nome AS trasferta
           FROM value_bets vb
           JOIN partite p ON vb.partita_id = p.id
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           LEFT JOIN report_ia r ON vb.partita_id = r.partita_id
           WHERE vb.stato = 'pending' AND r.id IS NULL"""
    )

    print(f"\n📝 {len(partite)} report da generare\n")
    for match in partite:
        p_id = int(match['partita_id'])
        print(f"📄 Report per: {match['casa']} vs {match['trasferta']}")
        report = generator.generate(p_id)
        print(f"  ✅ Generato ({len(report)} caratteri)\n")


def step_update_results() -> None:
    """STEP 5: Aggiorna risultati (football-data.org + balldontlie.io) + settle bets."""
    print("\n" + "=" * 60)
    print("📊 STEP 5: AGGIORNAMENTO RISULTATI")
    print("=" * 60)

    results_collector = ResultsCollector()

    for sport_cfg in SUPPORTED_SPORTS:
        if not sport_cfg.get('results_provider'):
            continue

        print(f"\n{sport_cfg['icona']} {sport_cfg['nome']}")
        print("-" * 40)

        try:
            _, camp_id = setup_sport_and_league(sport_cfg)
            results_collector.update_sport(
                sport_cfg=sport_cfg,
                campionato_id=camp_id,
                days_back=7,
            )
            results_collector.update_team_stats(camp_id)

        except Exception as e:
            print(f"  ❌ Errore: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 60)
    print("💰 STEP 5b: SETTLE BETS & BANKROLL")
    print("=" * 60)
    settle_all_bets()


def print_summary() -> None:
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO ODDSLAB")
    print("=" * 60)

    n_partite = DB.count("SELECT COUNT(*) AS n FROM partite")
    n_future  = DB.count("SELECT COUNT(*) AS n FROM partite WHERE stato='programmata' AND data_ora>NOW()")
    n_quote   = DB.count("SELECT COUNT(*) AS n FROM quote")
    n_prev    = DB.count("SELECT COUNT(*) AS n FROM previsioni")
    n_vb_att  = DB.count("SELECT COUNT(*) AS n FROM value_bets WHERE stato='pending'")
    n_vb_tot  = DB.count("SELECT COUNT(*) AS n FROM value_bets")
    n_report  = DB.count("SELECT COUNT(*) AS n FROM report_ia")

    print(f"  {'Partite Totali':.<35} {n_partite}")
    print(f"  {'Partite Future':.<35} {n_future}")
    print(f"  {'Quote':.<35} {n_quote}")
    print(f"  {'Previsioni':.<35} {n_prev}")
    print(f"  {'Value Bets Attive':.<35} {n_vb_att}")
    print(f"  {'Value Bets Totali':.<35} {n_vb_tot}")
    print(f"  {'Report IA':.<35} {n_report}")

    top_vb: list[dict] = DB.fetch_all(
        """SELECT sc.nome AS casa, st.nome AS trasferta,
                  vb.esito, vb.valore_quota,
                  ROUND(vb.valore_perc * 100, 1) AS value_pct,
                  b.nome AS bookmaker
           FROM value_bets vb
           JOIN partite p ON vb.partita_id = p.id
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           JOIN bookmaker b ON vb.bookmaker_id = b.id
           WHERE vb.stato = 'pending' AND p.data_ora > NOW()
           ORDER BY vb.valore_perc DESC LIMIT 5"""
    )

    if top_vb:
        print(f"\n  🔥 TOP 5 VALUE BETS ATTIVE:")
        print(f"  {'Match':<30} {'Esito':<8} {'Quota':>6} {'Value':>7} {'Book':<15}")
        print(f"  {'-' * 70}")
        for vb in top_vb:
            mn = f"{vb['casa']} vs {vb['trasferta']}"
            if len(mn) > 28:
                mn = mn[:28] + ".."
            print(f"  {mn:<30} {str(vb['esito']):<8} "
                  f"{float(vb['valore_quota']):>6.2f} "
                  f"{float(vb['value_pct']):>6.1f}% "
                  f"{str(vb['bookmaker']):<15}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description='OddsLab — Value Bet Finder')
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--predict', action='store_true')
    parser.add_argument('--find',    action='store_true')
    parser.add_argument('--report',  action='store_true')
    parser.add_argument('--results', action='store_true')

    args = parser.parse_args()
    run_all = not any([args.collect, args.predict, args.find,
                       args.report, args.results])

    print("🔬 OddsLab — Value Bet Finder")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        if run_all or args.collect:
            step_collect()
        if run_all or args.predict:
            step_predict()

        vb_list: list[dict] = []
        if run_all or args.find:
            vb_list = step_find_value()
        if run_all or args.report:
            step_generate_reports(vb_list)
        if run_all or args.results:
            step_update_results()

        print_summary()

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DB.close()


if __name__ == '__main__':
    main()
