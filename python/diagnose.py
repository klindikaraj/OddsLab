# python/diagnose.py
"""
Script diagnostico: mostra partite passate ancora 'programmata'
e testa direttamente football-data.org e balldontlie.io.
"""
from __future__ import annotations
from datetime import datetime, timezone
from db_connector import DB
from config import FOOTBALLDATA_KEY, BALLDONTLIE_KEY
import requests

def check_db():
    print("=" * 60)
    print("📋 PARTITE PASSATE ANCORA 'PROGRAMMATA' NEL DB")
    print("=" * 60)

    partite = DB.fetch_all(
        """SELECT p.id, p.data_ora,
                  sc.nome_api AS casa, st.nome_api AS trasf,
                  c.nome AS campionato
           FROM partite p
           JOIN squadre sc ON p.squadra_casa_id = sc.id
           JOIN squadre st ON p.squadra_trasf_id = st.id
           JOIN campionati c ON p.campionato_id = c.id
           WHERE p.stato = 'programmata' AND p.data_ora < NOW()
           ORDER BY p.data_ora DESC LIMIT 20"""
    )

    if not partite:
        print("  ✅ Nessuna partita passata con stato 'programmata'")
    else:
        print(f"  ⚠️  {len(partite)} partite già giocate ma ancora 'programmata':\n")
        for p in partite:
            print(f"  #{p['id']} | {p['data_ora']} | {p['campionato']} | "
                  f"{p['casa']} vs {p['trasf']}")

def test_footballdata(competition: str, date_from: str, date_to: str):
    print(f"\n{'='*60}")
    print(f"🔍 TEST football-data.org (competition={competition})")
    print(f"   from={date_from} to={date_to}")
    print("=" * 60)

    url = f"https://api.football-data.org/v4/competitions/{competition}/matches"
    params = {'status': 'FINISHED', 'dateFrom': date_from, 'dateTo': date_to}
    headers = {'X-Auth-Token': FOOTBALLDATA_KEY}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        data = r.json()
        print(f"  HTTP Status: {r.status_code}")
        matches = data.get('matches', [])
        print(f"  Partite FINISHED trovate: {len(matches)}")
        for m in matches[:5]:
            home  = m['homeTeam']['name']
            away  = m['awayTeam']['name']
            date  = m['utcDate'][:10]
            ft    = m.get('score', {}).get('fullTime', {})
            print(f"    {date} | {home} {ft.get('home')}-{ft.get('away')} {away}")
        if data.get('errorCode'):
            print(f"  ⚠️  Errore API: {data}")
    except Exception as e:
        print(f"  ❌ Errore: {e}")

def test_balldontlie(date_from: str, date_to: str):
    print(f"\n{'='*60}")
    print(f"🔍 TEST balldontlie.io (NBA)")
    print(f"   from={date_from} to={date_to}")
    print("=" * 60)

    url = "https://api.balldontlie.io/v1/games"
    params = {'start_date': date_from, 'end_date': date_to, 'per_page': 10}
    headers = {'Authorization': BALLDONTLIE_KEY}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        data = r.json()
        print(f"  HTTP Status: {r.status_code}")
        games = data.get('data', [])
        print(f"  Games trovati: {len(games)}")
        for g in games[:5]:
            home   = g['home_team']['full_name']
            away   = g['visitor_team']['full_name']
            date   = g['date'][:10]
            status = g.get('status', '?')
            sh     = g.get('home_team_score', '?')
            sa     = g.get('visitor_team_score', '?')
            print(f"    {date} | {home} {sh}-{sa} {away} [{status}]")
        if 'error' in data:
            print(f"  ⚠️  Errore API: {data['error']}")
    except Exception as e:
        print(f"  ❌ Errore: {e}")

if __name__ == '__main__':
    check_db()
    test_footballdata('SA', '2026-03-28', '2026-04-05')
    test_footballdata('PL', '2026-03-28', '2026-04-05')
    test_footballdata('PD', '2026-03-28', '2026-04-05')
    test_balldontlie('2026-03-29', '2026-04-05')
    DB.close()
