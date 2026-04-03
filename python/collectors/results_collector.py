# python/collectors/results_collector.py
"""
Aggiorna i risultati delle partite concluse usando API-Sports.

URL base per sport:
  - Football:   https://v3.football.api-sports.io   (stessa chiave)
  - Basketball: https://v1.basketball.api-sports.io (stessa chiave)
  - Tennis:     https://v1.tennis.api-sports.io     (stessa chiave, in beta)

NOTA sul piano free football: copre solo le stagioni 2022-2024.
Per la stagione 2025 serve un piano a pagamento oppure usare
l'endpoint /fixtures senza il filtro season (solo per data).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone, timedelta

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_connector import DB
from config import APISPORTS_KEY

# URL base per sport — NON usare un pattern generico, ogni sport ha la sua versione
APISPORTS_URLS: dict[str, str] = {
    'football':   'https://v3.football.api-sports.io',
    'basketball': 'https://v1.basketball.api-sports.io',
    'tennis':     'https://v1.tennis.api-sports.io',
}

APISPORTS_ENDPOINTS: dict[str, str] = {
    'football':   'fixtures',
    'basketball': 'games',
    'tennis':     'games',
}


# ─────────────────────────────────────────────
#  NORMALIZZAZIONE NOMI SQUADRE / GIOCATORI
# ─────────────────────────────────────────────

_ALIASES: dict[str, str] = {
    "inter milan":            "inter",
    "atletico madrid":        "atlético madrid",
    "atletico de madrid":     "atlético madrid",
    "ac milan":               "milan",
    "as roma":                "roma",
    "ss lazio":               "lazio",
    "newcastle united":       "newcastle",
    "manchester utd":         "manchester united",
    "tottenham hotspur":      "tottenham",
    "wolverhampton":          "wolves",
    "brighton & hove albion": "brighton",
    "nottingham forest":      "nottm forest",
    "la galaxy":              "los angeles galaxy",
}


def normalize_name(name: str) -> str:
    s = name.lower().strip()
    for src, dst in [('á','a'),('à','a'),('ä','a'),('â','a'),
                     ('é','e'),('è','e'),('ê','e'),('ë','e'),
                     ('í','i'),('ì','i'),('î','i'),
                     ('ó','o'),('ò','o'),('ô','o'),('ö','o'),
                     ('ú','u'),('ù','u'),('û','u'),('ü','u'),
                     ('ñ','n'),('ç','c')]:
        s = s.replace(src, dst)
    s = re.sub(
        r'\b(fc|ac|ss|sd|cd|cf|as|rc|sc|sk|fk|rsc|afc|bsc|'
        r'real|athletic|atletico|deportivo|sporting)\b', '', s
    )
    s = re.sub(r'\s+', ' ', s).strip()
    return _ALIASES.get(s, s)


def normalize_player(name: str) -> tuple[str, str]:
    s = normalize_name(name)
    parts = s.split()
    if not parts:
        return ('', s)
    return (parts[-1], s)


def team_similarity(a: str, b: str) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    tokens_a = set(na.split())
    tokens_b = set(nb.split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


def player_similarity(a: str, b: str) -> float:
    sur_a, full_a = normalize_player(a)
    sur_b, full_b = normalize_player(b)
    if sur_a != sur_b:
        return 0.0
    parts_a = full_a.split()
    parts_b = full_b.split()
    if len(parts_a) >= 2 and len(parts_b) >= 2:
        init_a = parts_a[0][0] if parts_a[0] else ''
        init_b = parts_b[0][0] if parts_b[0] else ''
        if init_a and init_b and init_a != init_b:
            return 0.5
        return 1.0
    return 0.9


# ─────────────────────────────────────────────
#  CLIENT API-SPORTS
# ─────────────────────────────────────────────

class ApisportsClient:

    def __init__(self) -> None:
        if not APISPORTS_KEY:
            raise ValueError("APISPORTS_KEY non configurata nel file .env")
        self.key = APISPORTS_KEY

    def _headers(self) -> dict[str, str]:
        return {'x-apisports-key': self.key}

    def _base(self, sport: str) -> str:
        url = APISPORTS_URLS.get(sport)
        if not url:
            raise ValueError(f"Sport non supportato: {sport}")
        return url

    def get_fixtures_by_date(
        self,
        sport: str,
        date_from: datetime,
        date_to: datetime,
        league_id: Optional[int] = None,
        season: Any = None,
    ) -> list[dict[str, Any]]:
        """
        Scarica fixture completate in un intervallo di date.
        Per il football: usa solo la data (senza season) per aggirare
        il blocco del piano free sulle stagioni recenti.
        """
        endpoint = APISPORTS_ENDPOINTS[sport]
        base_url = f"{self._base(sport)}/{endpoint}"

        params: dict[str, Any] = {
            'from':   date_from.strftime('%Y-%m-%d'),
            'to':     date_to.strftime('%Y-%m-%d'),
            'status': 'FT',
        }

        # Per football: aggiungere league ma NON season (piano free blocca 2025)
        if sport == 'football' and league_id:
            params['league'] = league_id
        # Per basketball: serve anche la season
        elif sport == 'basketball' and league_id and season:
            params['league'] = league_id
            params['season'] = season

        print(f"  [API-Sports/{sport}] GET {base_url}")
        print(f"  [API-Sports/{sport}] params={params}")

        r = requests.get(base_url, headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        remaining = r.headers.get('x-ratelimit-requests-remaining', '?')
        print(f"  [API-Sports] Richieste rimanenti oggi: {remaining}")

        if data.get('errors') and data['errors']:
            print(f"  [API-Sports] ⚠️  Errori: {data['errors']}")
        if data.get('message'):
            print(f"  [API-Sports] ⚠️  Messaggio: {data['message']}")

        results = data.get('response', [])
        print(f"  [API-Sports] Trovati {len(results)} risultati")
        return results

    def get_tennis_results_by_date(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> list[dict[str, Any]]:
        """Scarica partite tennis completate giorno per giorno."""
        all_results: list[dict[str, Any]] = []
        current  = date_from.date()
        end_date = date_to.date()

        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            url = f"{self._base('tennis')}/{APISPORTS_ENDPOINTS['tennis']}"

            print(f"  [API-Sports/tennis] GET {url} date={date_str}")
            try:
                r = requests.get(
                    url,
                    headers=self._headers(),
                    params={'date': date_str},
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()

                if data.get('errors') and data['errors']:
                    print(f"    ⚠️  Errori API: {data['errors']}")

                results = data.get('response', [])
                completed = [
                    g for g in results
                    if g.get('status', {}).get('short') in ('FIN', 'AOC', 'WO')
                ]
                all_results.extend(completed)
                print(f"    {len(completed)}/{len(results)} completate")
            except Exception as e:
                print(f"    ⚠️  Errore per data {date_str}: {e}")

            current += timedelta(days=1)

        return all_results


# ─────────────────────────────────────────────
#  MATCH MATCHER
# ─────────────────────────────────────────────

class MatchMatcher:
    TIME_WINDOW_MINUTES    = 90
    SCORE_THRESHOLD_TEAM   = 0.75
    SCORE_THRESHOLD_PLAYER = 0.85

    def __init__(self, sport_type: str) -> None:
        self.sport_type = sport_type

    def extract_kickoff_utc(self, fixture: dict[str, Any]) -> Optional[datetime]:
        try:
            if self.sport_type == 'football':
                ts = fixture['fixture']['timestamp']
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            elif self.sport_type == 'basketball':
                return datetime.fromisoformat(fixture['date']).astimezone(timezone.utc)
            elif self.sport_type == 'tennis':
                return datetime.fromisoformat(
                    fixture.get('date', '').replace('Z', '+00:00')
                ).astimezone(timezone.utc)
        except (KeyError, ValueError, TypeError):
            return None

    def extract_teams(self, fixture: dict[str, Any]) -> tuple[str, str]:
        if self.sport_type in ('football', 'basketball'):
            return (fixture['teams']['home']['name'],
                    fixture['teams']['away']['name'])
        elif self.sport_type == 'tennis':
            players = fixture.get('players', [])
            if len(players) >= 2:
                return (players[0]['player']['name'],
                        players[1]['player']['name'])
        return ('', '')

    def extract_score(self, fixture: dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
        try:
            if self.sport_type == 'football':
                return int(fixture['goals']['home']), int(fixture['goals']['away'])
            elif self.sport_type == 'basketball':
                return (int(fixture['scores']['home']['total']),
                        int(fixture['scores']['away']['total']))
            elif self.sport_type == 'tennis':
                players = fixture.get('players', [])
                if len(players) >= 2:
                    if players[0].get('winner'):
                        return 1, 0
                    elif players[1].get('winner'):
                        return 0, 1
        except (KeyError, TypeError, ValueError):
            pass
        return None, None

    def find_match_in_db(
        self,
        fixture: dict[str, Any],
        db_partite: list[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        kickoff = self.extract_kickoff_utc(fixture)
        if kickoff is None:
            return None

        api_home, api_away = self.extract_teams(fixture)
        if not api_home or not api_away:
            return None

        window     = timedelta(minutes=self.TIME_WINDOW_MINUTES)
        best_match: Optional[dict[str, Any]] = None
        best_score: float = 0.0

        for partita in db_partite:
            db_dt = partita['data_ora']
            if isinstance(db_dt, str):
                db_dt = datetime.fromisoformat(db_dt)
            if db_dt.tzinfo is None:
                db_dt = db_dt.replace(tzinfo=timezone.utc)

            if abs(kickoff - db_dt) > window:
                continue

            if self.sport_type == 'tennis':
                s_h = player_similarity(api_home, partita['nome_casa'])
                s_a = player_similarity(api_away, partita['nome_trasf'])
                threshold = self.SCORE_THRESHOLD_PLAYER
            else:
                s_h = team_similarity(api_home, partita['nome_casa'])
                s_a = team_similarity(api_away, partita['nome_trasf'])
                threshold = self.SCORE_THRESHOLD_TEAM

            combined = (s_h + s_a) / 2
            if combined >= threshold and combined > best_score:
                best_score = combined
                best_match = partita

        if best_match:
            print(f"    ✔ Match (score={best_score:.2f}): "
                  f"{api_home} vs {api_away} → partita #{best_match['id']}")
        else:
            print(f"    ✗ No match: {api_home} vs {api_away} "
                  f"@ {kickoff.strftime('%d/%m %H:%M')} UTC")

        return best_match


# ─────────────────────────────────────────────
#  RESULTS COLLECTOR
# ─────────────────────────────────────────────

class ResultsCollector:

    def __init__(self) -> None:
        self.client = ApisportsClient()

    def _load_pending_partite(self, campionato_id: int) -> list[dict[str, Any]]:
        return DB.fetch_all(
            """SELECT p.id, p.data_ora,
                      sc.nome_api AS nome_casa,
                      st.nome_api AS nome_trasf
               FROM partite p
               JOIN squadre sc ON p.squadra_casa_id = sc.id
               JOIN squadre st ON p.squadra_trasf_id = st.id
               WHERE p.campionato_id = %s AND p.stato = 'programmata'
               ORDER BY p.data_ora ASC""",
            (campionato_id,)
        )

    def update_sport(
        self,
        sport_cfg: dict[str, Any],
        campionato_id: int,
        days_back: int = 7,
    ) -> dict[str, int]:
        stats = {'aggiornate': 0, 'no_match': 0, 'no_score': 0}

        sport_type = sport_cfg['apisports_type']
        now        = datetime.now(timezone.utc)
        date_from  = now - timedelta(days=days_back)

        db_partite = self._load_pending_partite(campionato_id)
        if not db_partite:
            print("  ℹ️  Nessuna partita pending nel DB")
            return stats

        print(f"  [DB] {len(db_partite)} partite pending da risolvere")

        try:
            if sport_type == 'tennis':
                fixtures = self.client.get_tennis_results_by_date(date_from, now)
            else:
                fixtures = self.client.get_fixtures_by_date(
                    sport=sport_type,
                    date_from=date_from,
                    date_to=now,
                    league_id=sport_cfg.get('apisports_league'),
                    season=sport_cfg.get('apisports_season'),
                )
        except Exception as e:
            print(f"  ❌ Errore API-Sports: {e}")
            return stats

        if not fixtures:
            print("  ℹ️  Nessun risultato da API-Sports")
            return stats

        matcher = MatchMatcher(sport_type)

        for fixture in fixtures:
            partita = matcher.find_match_in_db(fixture, db_partite)
            if partita is None:
                stats['no_match'] += 1
                continue

            score_home, score_away = matcher.extract_score(fixture)
            if score_home is None or score_away is None:
                print(f"    ⚠️  Punteggio mancante per partita #{partita['id']}")
                stats['no_score'] += 1
                continue

            partita_id = int(partita['id'])
            DB.execute(
                """UPDATE partite SET stato='conclusa',
                   score_casa=%s, score_trasferta=%s WHERE id=%s""",
                (score_home, score_away, partita_id)
            )
            self._settle_value_bets(partita_id, score_home, score_away)
            stats['aggiornate'] += 1
            db_partite = [p for p in db_partite if p['id'] != partita['id']]

        print(f"  [Riepilogo] Aggiornate: {stats['aggiornate']} | "
              f"No match: {stats['no_match']} | No score: {stats['no_score']}")
        return stats

    def _settle_value_bets(self, partita_id: int, score_home: int, score_away: int) -> None:
        esito_reale = 'home' if score_home > score_away else ('draw' if score_home == score_away else 'away')
        vbs = DB.fetch_all(
            "SELECT id, esito FROM value_bets WHERE partita_id=%s AND stato='pending'",
            (partita_id,)
        )
        for vb in vbs:
            DB.execute(
                "UPDATE value_bets SET stato=%s WHERE id=%s",
                ('won' if vb['esito'] == esito_reale else 'lost', int(vb['id']))
            )
        if vbs:
            print(f"    📊 {len(vbs)} value bets → {esito_reale.upper()}")

    def update_team_stats(self, campionato_id: int) -> None:
        squadre = DB.fetch_all("SELECT id FROM squadre WHERE campionato_id=%s", (campionato_id,))
        for sq in squadre:
            sid = int(sq['id'])
            row = DB.fetch_one(
                """SELECT
                     AVG(CASE WHEN squadra_casa_id=%s THEN score_casa
                              WHEN squadra_trasf_id=%s THEN score_trasferta END) AS avg_fatti,
                     AVG(CASE WHEN squadra_casa_id=%s THEN score_trasferta
                              WHEN squadra_trasf_id=%s THEN score_casa END) AS avg_subiti,
                     COUNT(*) AS partite_giocate
                   FROM partite
                   WHERE (squadra_casa_id=%s OR squadra_trasf_id=%s) AND stato='conclusa'""",
                (sid, sid, sid, sid, sid, sid)
            )
            if row and row.get('partite_giocate') and int(row['partite_giocate']) >= 3:
                DB.execute(
                    "UPDATE squadre SET gol_fatti_avg=%s, gol_subiti_avg=%s WHERE id=%s",
                    (round(float(row['avg_fatti'] or 0), 2),
                     round(float(row['avg_subiti'] or 0), 2), sid)
                )
        print(f"  [Stats] Aggiornate statistiche per {len(squadre)} squadre")
