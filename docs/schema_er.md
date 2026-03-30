# Schema Entità-Relazioni — OddsLab

## Istruzioni
1. Copia il codice Mermaid qui sotto
2. Vai su https://mermaid.live
3. Incolla il codice nel pannello sinistro
4. Scarica l'immagine PNG dal pannello destro
5. Salva come `docs/schema_er.png`

## Codice Mermaid

erDiagram
    UTENTI {
        int id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        decimal bankroll_iniziale
        decimal bankroll_attuale
        decimal kelly_fraction
        datetime created_at
    }

    SPORT {
        int id PK
        varchar nome UK
        varchar api_key
        varchar icona
    }

    CAMPIONATI {
        int id PK
        int sport_id FK
        varchar nome
        varchar paese
        varchar api_key UK
    }

    SQUADRE {
        int id PK
        int campionato_id FK
        varchar nome
        varchar nome_api
        decimal elo_rating
        decimal gol_fatti_avg
        decimal gol_subiti_avg
    }

    BOOKMAKER {
        int id PK
        varchar nome UK
        varchar url
        varchar logo_url
    }

    PARTITE {
        int id PK
        int sport_id FK
        int campionato_id FK
        int squadra_casa_id FK
        int squadra_trasf_id FK
        datetime data_ora
        enum stato
        tinyint score_casa
        tinyint score_trasferta
        varchar api_event_id UK
    }

    QUOTE {
        int id PK
        int partita_id FK
        int bookmaker_id FK
        enum tipo_mercato
        varchar esito
        decimal valore_quota
        decimal prob_implicita
        datetime rilevata_il
    }

    PREVISIONI {
        int id PK
        int partita_id FK
        enum tipo_modello
        decimal prob_casa
        decimal prob_pareggio
        decimal prob_trasferta
        datetime calcolata_il
    }

    VALUE_BETS {
        int id PK
        int partita_id FK
        int bookmaker_id FK
        varchar esito
        decimal valore_quota
        decimal prob_modello
        decimal valore_perc
        decimal stake_kelly_pct
        enum stato
        datetime created_at
    }

    SCOMMESSE {
        int id PK
        int utente_id FK
        int value_bet_id FK
        decimal importo_puntato
        decimal profitto_potenziale
        decimal profitto_reale
        enum risultato
        datetime data
    }

    STORICO_BANKROLL {
        int id PK
        int utente_id FK
        decimal importo_attuale
        decimal variazione
        int scommessa_id FK
        datetime data
    }

    REPORT_IA {
        int id PK
        int partita_id FK
        text testo
        datetime generato_il
    }

    SPORT ||--o{ CAMPIONATI : "ha"
    CAMPIONATI ||--o{ SQUADRE : "contiene"
    SPORT ||--o{ PARTITE : "sport_di"
    CAMPIONATI ||--o{ PARTITE : "campionato_di"
    SQUADRE ||--o{ PARTITE : "gioca_casa"
    SQUADRE ||--o{ PARTITE : "gioca_trasferta"
    PARTITE ||--o{ QUOTE : "ha_quote"
    BOOKMAKER ||--o{ QUOTE : "offre"
    PARTITE ||--o| PREVISIONI : "ha_previsione"
    PARTITE ||--o{ VALUE_BETS : "genera"
    BOOKMAKER ||--o{ VALUE_BETS : "bookmaker_di"
    PARTITE ||--o{ REPORT_IA : "ha_report"
    UTENTI ||--o{ SCOMMESSE : "piazza"
    VALUE_BETS ||--o{ SCOMMESSE : "basata_su"
    UTENTI ||--o{ STORICO_BANKROLL : "ha_storico"
    SCOMMESSE ||--o| STORICO_BANKROLL : "registra"

## Descrizione delle Tabelle

### Tabelle Anagrafiche

| Tabella | Descrizione | Righe Tipiche |
|---------|-------------|---------------|
| SPORT | Sport supportati (Calcio, Tennis, Basket) | 3 |
| CAMPIONATI | Campionati per ogni sport | 5 |
| SQUADRE | Squadre/giocatori con statistiche | 84 |
| BOOKMAKER | Bookmaker da cui si raccolgono quote | 25 |
| UTENTI | Utenti registrati sulla piattaforma | variabile |

### Tabelle Operative

| Tabella | Descrizione | Righe Tipiche |
|---------|-------------|---------------|
| PARTITE | Ogni evento sportivo con data e stato | 68+ |
| QUOTE | Quote rilevate (più per partita per bookmaker) | 4.903+ |
| PREVISIONI | Probabilità calcolate dal modello | 68+ |
| VALUE_BETS | Scommesse vantaggiose identificate | 71+ |
| REPORT_IA | Report generati da OpenAI o fallback | 67+ |

### Tabelle Utente

| Tabella | Descrizione | Righe Tipiche |
|---------|-------------|---------------|
| SCOMMESSE | Scommesse piazzate dagli utenti | variabile |
| STORICO_BANKROLL | Log di ogni variazione del bankroll | variabile |

## Relazioni Principali

| Relazione | Tipo | Descrizione |
|-----------|------|-------------|
| SPORT → CAMPIONATI | 1:N | Uno sport ha molti campionati |
| CAMPIONATI → SQUADRE | 1:N | Un campionato ha molte squadre |
| SQUADRE → PARTITE | 1:N | Una squadra gioca in molte partite |
| PARTITE → QUOTE | 1:N | Una partita ha molte quote |
| PARTITE → PREVISIONI | 1:1 | Una partita ha una previsione |
| PARTITE → VALUE_BETS | 1:N | Una partita può avere più value bets |
| UTENTI → SCOMMESSE | 1:N | Un utente piazza molte scommesse |
| VALUE_BETS → SCOMMESSE | 1:N | Una value bet può essere puntata da più utenti |

## Vincoli di Integrità

- **UNIQUE**: username, email, api_event_id, api_key campionati
- **FOREIGN KEY**: tutte con ON DELETE CASCADE dove appropriato
- **CHECK**: kelly_fraction tra 0 e 1, bankroll > 0
- **GENERATED**: prob_implicita = 1/valore_quota (colonna calcolata)
- **ENUM**: stato partita, tipo_mercato, risultato scommessa

## Indici per Performance

| Tabella | Indice | Colonne | Motivazione |
|---------|--------|---------|-------------|
| partite | idx_data_stato | data_ora, stato | Filtro partite future |
| quote | idx_partita_book | partita_id, bookmaker_id | JOIN frequenti |
| quote | idx_rilevazione | rilevata_il | Ordinamento temporale |
| value_bets | idx_stato | stato | Filtro pending |
| value_bets | idx_valore | valore_perc DESC | Ordinamento per value |
| scommesse | idx_utente_data | utente_id, data | Storico utente |
| storico_bankroll | idx_utente_data | utente_id, data | Grafico bankroll |