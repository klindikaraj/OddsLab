# Diagramma delle Classi — OddsLab

## Istruzioni
1. Copia il codice Mermaid qui sotto
2. Vai su https://mermaid.live
3. Incolla il codice nel pannello sinistro
4. Scarica l'immagine PNG dal pannello destro
5. Salva come `docs/diagramma_classi.png`

## Codice Mermaid

classDiagram
    direction TB

    class Database {
        -PDO pdo
        -Database instance$
        -__construct()
        +getInstance()$ Database
        +getConnection() PDO
        +fetchAll(query, params) array
        +fetchOne(query, params) array|null
        +execute(query, params) int
        +count(query, params) int
        +close()
    }

    class Auth {
        -Database db
        +register(username, email, password, bankroll) array
        +login(username, password) array
        +logout() void
        +isLoggedIn()$ bool
        +getUserId()$ int
        +getUsername()$ string
        +requireLogin()$ void
        +getUserData(userId) array|null
    }

    class Dashboard {
        -Database db
        +getKPIs(userId) array
        +getSystemStats() array
        +getRecentValueBets(limit) array
        +getBankrollHistory(userId, days) array
        +getValueBetsBySport() array
    }

    class ValueBet {
        -Database db
        +getActive(sport, confidence, orderBy, order) array
        +getById(id) array|null
        +getMatchOdds(partitaId) array
        +getMatchPrediction(partitaId) array|null
        +getMatchDetail(partitaId) array|null
        +getMatchReport(partitaId) array|null
        +getMatchValueBets(partitaId) array
        +getSports() array
    }

    class Bankroll {
        -Database db
        +getSummary(userId) array
        +placeBet(userId, valueBetId, importo) array
        +getBetHistory(userId, stato) array
        +getHistory(userId, days) array
        +updateSettings(userId, kellyFraction) array
        +calculateKellyStake(userId, valueBetId) array
    }

    class ApiClient {
        -string pythonCmd
        -string pythonDir
        +runPipeline(step) string
        +generateReport(partitaId) string
    }

    class DB_Python {
        -Any _instance$
        +get_connection()$ Any
        +fetch_all(query, params)$ list~dict~
        +fetch_one(query, params)$ dict|None
        +execute(query, params)$ int
        +count(query, params)$ int
        +close()$ void
    }

    class OddsCollector {
        -str api_key
        -str regions
        -str markets
        -str odds_format
        +get_available_sports() list
        +get_odds(sport_key) list
        +save_to_db(events, sport_id, camp_id) dict
        -_upsert_partita(event, sport_id, camp_id) tuple
        -_upsert_squadra(nome, camp_id) int
        -_upsert_bookmaker(key, title) tuple
        -_insert_quota(partita_id, book_id, tipo, esito, val) void
        -_map_outcome(outcome_name, event) str
    }

    class ResultsCollector {
        -str api_key
        +get_scores(sport_key, days_from) list
        +update_results(scores) dict
        +update_team_stats(campionato_id) void
        -_settle_value_bets(partita_id, score_h, score_a) void
    }

    class PoissonModel {
        -int MAX_GOALS
        -float DEFAULT_AVG
        +predict(home_id, away_id, camp_id) dict
        +save_prediction(partita_id, prediction) void
        +get_team_stats(team_id) dict
        +get_league_average(campionato_id) float
        -_poisson_pmf(k, lam) float
    }

    class EloModel {
        -float DEFAULT_RATING
        -int K_FACTOR
        +expected_score(rating_a, rating_b) float
        +predict(home_id, away_id, camp_id) dict
        +update_ratings(winner_id, loser_id) dict
        +save_prediction(partita_id, prediction) void
        -_get_rating(team_id) float
        -_update_rating_db(team_id, new_rating) void
    }

    class KellyResult {
        +float edge
        +float kelly_full_pct
        +float kelly_adj_pct
        +float stake_full
        +float stake_adjusted
        +str confidence
    }

    class KellyCriterion {
        -float MAX_STAKE_PCT
        -float MIN_VALUE_THRESHOLD
        +calculate(prob, odds, bankroll, fraction) KellyResult
        +calculate_for_match(partita_id, utente_id) list
        -_classify(edge) str
    }

    class ValueFinder {
        -KellyCriterion kelly
        +find_value_bets(partita_id) list
        +find_all_pending() list
        -_save_value_bet(vb) void
    }

    class ReportGenerator {
        -str SYSTEM_PROMPT
        -OpenAI|None client
        +generate(partita_id, kelly_results) str
        -_generate_fallback(partita_id) str
        -_get_match_data(partita_id) list
        -_build_prompt(match_data, kelly_results) str
        -_save_report(partita_id, testo) void
    }

    Auth --> Database : usa
    Dashboard --> Database : usa
    ValueBet --> Database : usa
    Bankroll --> Database : usa

    OddsCollector --> DB_Python : usa
    ResultsCollector --> DB_Python : usa
    PoissonModel --> DB_Python : usa
    EloModel --> DB_Python : usa
    KellyCriterion --> DB_Python : usa
    ValueFinder --> DB_Python : usa
    ValueFinder --> KellyCriterion : contiene
    ReportGenerator --> DB_Python : usa

    KellyCriterion ..> KellyResult : produce
    ApiClient ..> ReportGenerator : invoca

## Legenda

- **Linea continua con freccia (-->)**: Associazione / Dipendenza diretta
- **Linea tratteggiata (..>)**: Dipendenza debole / Creazione
- **+**: Metodo/Attributo pubblico
- **-**: Metodo/Attributo privato
- **$**: Metodo/Attributo statico

## Note sui Design Pattern

| Pattern | Classe | Motivazione |
|---------|--------|-------------|
| Singleton | Database, DB_Python | Una sola connessione al DB |
| Strategy | PoissonModel, EloModel | Modello diverso per ogni sport |
| Facade | ApiClient | Interfaccia semplificata verso Python |
| Data Class | KellyResult | Struttura dati immutabile |