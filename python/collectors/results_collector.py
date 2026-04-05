# python/collectors/results_collector.py
"""
Aggiorna i risultati delle partite concluse.

Provider:
  - Calcio (Serie A, Premier League, La Liga):
      football-data.org — free, stagione corrente inclusa
      Base URL: https://api.football-data.org/v4
      Auth:     header X-Auth-Token

  - Basket (NBA):
      balldontlie.io — free, NBA inclusa
      Base URL: https://api.balldontlie.io/v1
      Auth:     header Authorization: Bearer <key>

Matching: finestra temporale ±2h UTC + similarità nomi ≥ 0.60
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
from config import FOOTBALLDATA_KEY, BALLDONTLIE_KEY


# ─────────────────────────────────────────────
#  NORMALIZZAZIONE NOMI SQUADRE
# ─────────────────────────────────────────────

# Mappa: nome normalizzato (lowercase, no accenti) → nome usato da The Odds API
_ALIASES: dict[str, str] = {
    # ── Serie A ──
    "inter milan":              "inter",
    "fc internazionale milano": "inter",
    "ac milan":                 "milan",
    "as roma":                  "roma",
    "ss lazio":                 "lazio",
    "us sassuolo calcio":       "sassuolo",
    "cagliari calcio":          "cagliari",
    "hellas verona fc":         "hellas verona",
    "acf fiorentina":           "fiorentina",
    "parma calcio 1913":        "parma",
    "us cremonese":             "cremonese",
    "bologna fc 1909":          "bologna",
    "ac pisa 1909":             "pisa",
    "torino fc":                "torino",
    "udinese calcio":           "udinese",
    "genoa cfc":                "genoa",
    "como 1907":                "como",
    "empoli fc":                "empoli",
    "venezia fc":               "venezia",
    "atalanta bc":              "atalanta",
    "ssc napoli":               "napoli",
    "juventus fc":              "juventus",
    "us lecce":                 "lecce",
    "acn venezia 1907":         "venezia",
    # ── Premier League ──
    "newcastle united":         "newcastle",
    "manchester utd":           "manchester united",
    "tottenham hotspur":        "tottenham",
    "wolverhampton wanderers":  "wolves",
    "brighton & hove albion":   "brighton",
    "nottingham forest":        "nottm forest",
    "west ham united":          "west ham",
    "brentford fc":             "brentford",
    "fulham fc":                "fulham",
    "crystal palace":           "crystal palace",
    "everton fc":               "everton",
    "leicester city":           "leicester",
    "luton town":               "luton",
    "sheffield utd":            "sheffield united",
    "afc bournemouth":          "bournemouth",
    "chelsea fc":               "chelsea",
    "arsenal fc":               "arsenal",
    "manchester city":          "manchester city",
    "liverpool fc":             "liverpool",
    # ── La Liga ──
    "real betis balompie":      "real betis",
    "deportivo alaves":         "alaves",
    "rcd espanyol de barcelona":"espanyol",
    "rcd espanyol":             "espanyol",
    "rayo vallecano de madrid": "rayo vallecano",
    "getafe cf":                "getafe",
    "athletic club":            "athletic bilbao",
    "real sociedad de futbol":  "real sociedad",
    "rcd mallorca":             "mallorca",
    "real madrid cf":           "real madrid",
    "fc barcelona":             "barcelona",
    "club atletico de madrid":  "atlético madrid",
    "sevilla fc":               "sevilla",
    "levante ud":               "levante",
    "elche cf":                 "elche",
    "ca osasuna":               "osasuna",
    "real oviedo":              "oviedo",
    "valencia cf":              "valencia",
    "rc celta de vigo":         "celta vigo",
    "villarreal cf":            "villarreal",
    "granada cf":               "granada",
    "ud las palmas":            "las palmas",
    "cadiz cf":                 "cadiz",
    "girona fc":                "girona",
    # ── NBA (balldontlie usa già nomi puliti, ma per sicurezza) ──
    "los angeles clippers":     "la clippers",
    "la clippers":              "la clippers",
}


def normalize(name: str) -> str:
    """Lowercase + rimozione accenti + rimozione suffissi + alias."""
    s = name.lower().strip()
    for src, dst in [('á','a'),('à','a'),('â','a'),('ä','a'),
                     ('é','e'),('è','e'),('ê','e'),('ë','e'),
                     ('í','i'),('ì','i'),('î','i'),
                     ('ó','o'),('ò','o'),('ô','o'),('ö','o'),
                     ('ú','u'),('ù','u'),('û','u'),('ü','u'),
                     ('ñ','n'),('ç','c')]:
        s = s.replace(src, dst)
    # Rimuovi suffissi/prefissi calcistici comuni
    s = re.sub(r'\b(fc|ac|ss|sd|cd|cf|as|rc|sc|sk|fk|rsc|afc|cp|ssc|ud|rcd|us)\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return _ALIASES.get(s, s)


def similarity(a: str, b: str) -> float:
    """Score [0,1] tra due nomi squadra."""
    na, nb = normalize(a), normalize(b)
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    ta = set(na.split())
    tb = set(nb.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


# ─────────────────────────────────────────────
#  CLIENT FOOTBALL-DATA.ORG
# ─────────────────────────────────────────────

class FootballDataClient:
    BASE = 'https://api.football-data.org/v4'

    def __init__(self) -> None:
        if not FOOTBALLDATA_KEY:
            raise ValueError("FOOTBALLDATA_KEY non configurata nel .env")
        self.headers = {'X-Auth-Token': FOOTBALLDATA_KEY}

    def get_finished_matches(
        self, competition: str, date_from: datetime, date_to: datetime
    ) -> list[dict[str, Any]]:
        url = f"{self.BASE}/competitions/{competition}/matches"
        params = {
            'status':   'FINISHED',
            'dateFrom': date_from.strftime('%Y-%m-%d'),
            'dateTo':   date_to.strftime('%Y-%m-%d'),
        }
        print(f"  [football-data] {competition} {params['dateFrom']}→{params['dateTo']}")
        r = requests.get(url, headers=self.headers, params=params, timeout=30)
        if r.status_code == 429:
            import time; time.sleep(12)
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
        r.raise_for_status()
        matches = r.json().get('matches', [])
        print(f"  [football-data] {len(matches)} partite FINISHED")
        return matches

    def extract_kickoff_utc(self, m: dict) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            return None

    def extract_teams(self, m: dict) -> tuple[str, str]:
        return m['homeTeam']['name'], m['awayTeam']['name']

    def extract_score(self, m: dict) -> tuple[Optional[int], Optional[int]]:
        try:
            ft = m['score']['fullTime']
            return int(ft['home']), int(ft['away'])
        except (KeyError, TypeError):
            return None, None


# ─────────────────────────────────────────────
#  CLIENT BALLDONTLIE.IO
# ─────────────────────────────────────────────

class BallDontLieClient:
    BASE = 'https://api.balldontlie.io/v1'

    def __init__(self) -> None:
        if not BALLDONTLIE_KEY:
            raise ValueError("BALLDONTLIE_KEY non configurata nel .env")
        self.headers = {'Authorization': BALLDONTLIE_KEY}

    def get_finished_games(self, date_from: datetime, date_to: datetime) -> list[dict]:
        url = f"{self.BASE}/games"
        all_games: list[dict] = []
        cursor = None
        df = date_from.strftime('%Y-%m-%d')
        dt = date_to.strftime('%Y-%m-%d')
        print(f"  [balldontlie] NBA {df}→{dt}")

        while True:
            params: dict[str, Any] = {
                'start_date': df, 'end_date': dt, 'per_page': 100
            }
            if cursor:
                params['cursor'] = cursor
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            all_games.extend(data.get('data', []))
            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                break

        finished = [g for g in all_games if g.get('status') == 'Final']
        print(f"  [balldontlie] {len(finished)}/{len(all_games)} giochi Final")
        return finished

    def extract_kickoff_utc(self, g: dict) -> Optional[datetime]:
        try:
            # balldontlie dà solo la data — usiamo mezzogiorno UTC
            # così la finestra ±24h copre qualsiasi orario NBA
            d = g['date'][:10]
            return datetime.fromisoformat(f"{d}T12:00:00+00:00")
        except (KeyError, ValueError):
            return None

    def extract_teams(self, g: dict) -> tuple[str, str]:
        return g['home_team']['full_name'], g['visitor_team']['full_name']

    def extract_score(self, g: dict) -> tuple[Optional[int], Optional[int]]:
        try:
            return int(g['home_team_score']), int(g['visitor_team_score'])
        except (KeyError, TypeError, ValueError):
            return None, None


# ─────────────────────────────────────────────
#  MATCH MATCHER
# ─────────────────────────────────────────────

class MatchMatcher:

    def __init__(self, time_window_hours: int = 2, threshold: float = 0.60) -> None:
        self.window    = timedelta(hours=time_window_hours)
        self.threshold = threshold

    def find(
        self,
        api_kickoff: datetime,
        api_home: str,
        api_away: str,
        db_partite: list[dict],
    ) -> Optional[dict]:
        best: Optional[dict] = None
        best_score = 0.0

        for p in db_partite:
            db_dt = p['data_ora']
            if isinstance(db_dt, str):
                db_dt = datetime.fromisoformat(db_dt)
            if db_dt.tzinfo is None:
                db_dt = db_dt.replace(tzinfo=timezone.utc)

            if abs(api_kickoff - db_dt) > self.window:
                continue

            combined = (similarity(api_home, p['nome_casa']) +
                        similarity(api_away, p['nome_trasf'])) / 2

            if combined >= self.threshold and combined > best_score:
                best_score = combined
                best = p

        if best:
            print(f"    ✔ ({best_score:.2f}) {api_home} vs {api_away} → #{best['id']}")
        else:
            print(f"    ✗ no match: {api_home} vs {api_away}")

        return best


# ─────────────────────────────────────────────
#  RESULTS COLLECTOR
# ─────────────────────────────────────────────

class ResultsCollector:

    def __init__(self) -> None:
        self._fd:  Optional[FootballDataClient] = None
        self._bdl: Optional[BallDontLieClient]  = None

    def _fd_client(self) -> FootballDataClient:
        if not self._fd:
            self._fd = FootballDataClient()
        return self._fd

    def _bdl_client(self) -> BallDontLieClient:
        if not self._bdl:
            self._bdl = BallDontLieClient()
        return self._bdl

    def _load_pending(self, campionato_id: int) -> list[dict]:
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
        self, sport_cfg: dict, campionato_id: int, days_back: int = 7
    ) -> dict[str, int]:
        stats    = {'aggiornate': 0, 'no_match': 0, 'no_score': 0}
        provider = sport_cfg.get('results_provider')
        if not provider:
            print("  ℹ️  Nessun provider risultati")
            return stats

        now       = datetime.now(timezone.utc)
        date_from = now - timedelta(days=days_back)

        db_partite = self._load_pending(campionato_id)
        if not db_partite:
            print("  ℹ️  Nessuna partita pending")
            return stats
        print(f"  [DB] {len(db_partite)} partite pending")

        # ── CALCIO ────────────────────────────────────────────
        if provider == 'footballdata':
            try:
                matches = self._fd_client().get_finished_matches(
                    sport_cfg['fd_competition'], date_from, now
                )
            except Exception as e:
                print(f"  ❌ football-data: {e}")
                return stats

            fd      = self._fd_client()
            matcher = MatchMatcher(time_window_hours=2, threshold=0.60)

            for m in matches:
                kickoff = fd.extract_kickoff_utc(m)
                if kickoff is None: continue
                home, away = fd.extract_teams(m)
                partita = matcher.find(kickoff, home, away, db_partite)
                if partita is None:
                    stats['no_match'] += 1; continue
                sh, sa = fd.extract_score(m)
                if sh is None:
                    stats['no_score'] += 1; continue
                self._commit(int(partita['id']), sh, sa)
                stats['aggiornate'] += 1
                db_partite = [p for p in db_partite if p['id'] != partita['id']]

        # ── BASKET ────────────────────────────────────────────
        elif provider == 'balldontlie':
            try:
                games = self._bdl_client().get_finished_games(date_from, now)
            except Exception as e:
                print(f"  ❌ balldontlie: {e}")
                return stats

            bdl     = self._bdl_client()
            matcher = MatchMatcher(time_window_hours=24, threshold=0.60)

            for g in games:
                kickoff = bdl.extract_kickoff_utc(g)
                if kickoff is None: continue
                home, away = bdl.extract_teams(g)
                partita = matcher.find(kickoff, home, away, db_partite)
                if partita is None:
                    stats['no_match'] += 1; continue
                sh, sa = bdl.extract_score(g)
                if sh is None:
                    stats['no_score'] += 1; continue
                self._commit(int(partita['id']), sh, sa)
                stats['aggiornate'] += 1
                db_partite = [p for p in db_partite if p['id'] != partita['id']]

        print(f"  [Riepilogo] ✅ {stats['aggiornate']} | "
              f"✗ {stats['no_match']} no-match | ⚠️ {stats['no_score']} no-score")
        return stats

    def _commit(self, partita_id: int, sh: int, sa: int) -> None:
        DB.execute(
            "UPDATE partite SET stato='conclusa', score_casa=%s, score_trasferta=%s WHERE id=%s",
            (sh, sa, partita_id)
        )
        self._settle_vbs(partita_id, sh, sa)
        print(f"    ✅ Partita #{partita_id}: {sh}-{sa}")

    def _settle_vbs(self, partita_id: int, sh: int, sa: int) -> None:
        esito = 'home' if sh > sa else ('draw' if sh == sa else 'away')
        vbs = DB.fetch_all(
            "SELECT id, esito FROM value_bets WHERE partita_id=%s AND stato='pending'",
            (partita_id,)
        )
        for vb in vbs:
            DB.execute(
                "UPDATE value_bets SET stato=%s WHERE id=%s",
                ('won' if vb['esito'] == esito else 'lost', int(vb['id']))
            )
        if vbs:
            print(f"    📊 {len(vbs)} VB → {esito.upper()}")

    def update_team_stats(self, campionato_id: int) -> None:
        squadre = DB.fetch_all(
            "SELECT id FROM squadre WHERE campionato_id=%s", (campionato_id,)
        )
        updated = 0
        for sq in squadre:
            sid = int(sq['id'])
            row = DB.fetch_one(
                """SELECT
                     AVG(CASE WHEN squadra_casa_id=%s THEN score_casa
                              WHEN squadra_trasf_id=%s THEN score_trasferta END) AS avg_fatti,
                     AVG(CASE WHEN squadra_casa_id=%s THEN score_trasferta
                              WHEN squadra_trasf_id=%s THEN score_casa END) AS avg_subiti,
                     COUNT(*) AS n
                   FROM partite
                   WHERE (squadra_casa_id=%s OR squadra_trasf_id=%s)
                     AND stato='conclusa'""",
                (sid, sid, sid, sid, sid, sid)
            )
            if row and row.get('n') and int(row['n']) >= 3:
                DB.execute(
                    "UPDATE squadre SET gol_fatti_avg=%s, gol_subiti_avg=%s WHERE id=%s",
                    (round(float(row['avg_fatti'] or 0), 2),
                     round(float(row['avg_subiti'] or 0), 2), sid)
                )
                updated += 1
        print(f"  [Stats] {updated}/{len(squadre)} squadre aggiornate")
