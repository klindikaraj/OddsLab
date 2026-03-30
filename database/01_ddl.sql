-- ============================================
-- OddsLab Database — DDL
-- MySQL 8.0+
-- ============================================

CREATE DATABASE IF NOT EXISTS oddslab
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE oddslab;

-- ---------- TABELLE ANAGRAFICHE ----------

CREATE TABLE utenti (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    username          VARCHAR(50)    NOT NULL UNIQUE,
    email             VARCHAR(100)   NOT NULL UNIQUE,
    password_hash     VARCHAR(255)   NOT NULL,
    bankroll_iniziale DECIMAL(10,2)  NOT NULL DEFAULT 1000.00,
    bankroll_attuale  DECIMAL(10,2)  NOT NULL DEFAULT 1000.00,
    kelly_fraction    DECIMAL(3,2)   NOT NULL DEFAULT 0.50
                      COMMENT '1.00=Full, 0.50=Half, 0.25=Quarter',
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (kelly_fraction > 0 AND kelly_fraction <= 1),
    CHECK (bankroll_iniziale > 0)
);

CREATE TABLE sport (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nome    VARCHAR(50)  NOT NULL UNIQUE,
    api_key VARCHAR(50)  NOT NULL UNIQUE
            COMMENT 'Chiave usata da The Odds API (es. soccer_serie_a)',
    icona   VARCHAR(10)  DEFAULT '⚽'
);

CREATE TABLE campionati (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    sport_id INT          NOT NULL,
    nome     VARCHAR(100) NOT NULL,
    paese    VARCHAR(50)  NOT NULL,
    api_key  VARCHAR(80)  NOT NULL UNIQUE,

    FOREIGN KEY (sport_id) REFERENCES sport(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE squadre (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    campionato_id  INT           NOT NULL,
    nome           VARCHAR(100)  NOT NULL,
    nome_api       VARCHAR(100)  NOT NULL
                   COMMENT 'Nome esatto restituito dalla API',
    elo_rating     DECIMAL(7,2)  DEFAULT 1500.00,
    gol_fatti_avg  DECIMAL(4,2)  DEFAULT NULL
                   COMMENT 'Media gol fatti (per Poisson)',
    gol_subiti_avg DECIMAL(4,2)  DEFAULT NULL
                   COMMENT 'Media gol subiti (per Poisson)',

    FOREIGN KEY (campionato_id) REFERENCES campionati(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE bookmaker (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    nome     VARCHAR(50) NOT NULL UNIQUE,
    url      VARCHAR(200) DEFAULT NULL,
    logo_url VARCHAR(200) DEFAULT NULL
);

-- ---------- TABELLE OPERATIVE ----------

CREATE TABLE partite (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    sport_id         INT         NOT NULL,
    campionato_id    INT         NOT NULL,
    squadra_casa_id  INT         NOT NULL,
    squadra_trasf_id INT         NOT NULL,
    data_ora         DATETIME    NOT NULL,
    stato            ENUM('programmata','in_corso','conclusa','annullata')
                     NOT NULL DEFAULT 'programmata',
    score_casa       TINYINT     DEFAULT NULL,
    score_trasferta  TINYINT     DEFAULT NULL,
    api_event_id     VARCHAR(64) NOT NULL UNIQUE,
    updated_at       DATETIME    DEFAULT CURRENT_TIMESTAMP
                     ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (sport_id)         REFERENCES sport(id),
    FOREIGN KEY (campionato_id)    REFERENCES campionati(id),
    FOREIGN KEY (squadra_casa_id)  REFERENCES squadre(id),
    FOREIGN KEY (squadra_trasf_id) REFERENCES squadre(id),

    INDEX idx_data_stato (data_ora, stato)
);

CREATE TABLE quote (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    partita_id       INT            NOT NULL,
    bookmaker_id     INT            NOT NULL,
    tipo_mercato     ENUM('h2h','spreads','totals')
                     NOT NULL DEFAULT 'h2h',
    esito            VARCHAR(30)    NOT NULL
                     COMMENT 'home / draw / away',
    valore_quota     DECIMAL(6,2)   NOT NULL,
    prob_implicita   DECIMAL(5,4)   GENERATED ALWAYS AS (1 / valore_quota)
                     STORED,
    rilevata_il      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (partita_id)   REFERENCES partite(id)
        ON DELETE CASCADE,
    FOREIGN KEY (bookmaker_id) REFERENCES bookmaker(id),

    INDEX idx_partita_book (partita_id, bookmaker_id),
    INDEX idx_rilevazione  (rilevata_il)
);

CREATE TABLE previsioni (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    partita_id    INT         NOT NULL UNIQUE,
    tipo_modello  ENUM('poisson','elo','hybrid') NOT NULL,
    prob_casa     DECIMAL(5,4) NOT NULL,
    prob_pareggio DECIMAL(5,4) DEFAULT NULL
                  COMMENT 'NULL per sport senza pareggio (tennis)',
    prob_trasferta DECIMAL(5,4) NOT NULL,
    calcolata_il  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (partita_id) REFERENCES partite(id)
        ON DELETE CASCADE,

    CHECK (prob_casa + COALESCE(prob_pareggio, 0) + prob_trasferta
           BETWEEN 0.95 AND 1.05)
);

CREATE TABLE value_bets (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    partita_id      INT           NOT NULL,
    bookmaker_id    INT           NOT NULL,
    esito           VARCHAR(30)   NOT NULL,
    valore_quota    DECIMAL(6,2)  NOT NULL,
    prob_modello    DECIMAL(5,4)  NOT NULL,
    valore_perc     DECIMAL(6,4)  NOT NULL
                    COMMENT 'value = (prob * quota) - 1',
    stake_kelly_pct DECIMAL(5,4)  NOT NULL
                    COMMENT 'Percentuale Kelly Full',
    stato           ENUM('pending','won','lost','void')
                    NOT NULL DEFAULT 'pending',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (partita_id)   REFERENCES partite(id),
    FOREIGN KEY (bookmaker_id) REFERENCES bookmaker(id),

    INDEX idx_stato     (stato),
    INDEX idx_valore    (valore_perc DESC)
);

CREATE TABLE scommesse (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    utente_id          INT           NOT NULL,
    value_bet_id       INT           NOT NULL,
    importo_puntato    DECIMAL(10,2) NOT NULL,
    profitto_potenziale DECIMAL(10,2) NOT NULL,
    profitto_reale     DECIMAL(10,2) DEFAULT NULL,
    risultato          ENUM('pending','won','lost','void')
                       NOT NULL DEFAULT 'pending',
    data               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (utente_id)    REFERENCES utenti(id),
    FOREIGN KEY (value_bet_id) REFERENCES value_bets(id),

    INDEX idx_utente_data (utente_id, data)
);

CREATE TABLE storico_bankroll (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    utente_id       INT           NOT NULL,
    importo_attuale DECIMAL(10,2) NOT NULL,
    variazione      DECIMAL(10,2) NOT NULL DEFAULT 0,
    scommessa_id    INT           DEFAULT NULL,
    data            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (utente_id)    REFERENCES utenti(id),
    FOREIGN KEY (scommessa_id) REFERENCES scommesse(id),

    INDEX idx_utente_data (utente_id, data)
);

CREATE TABLE report_ia (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    partita_id  INT    NOT NULL,
    testo       TEXT   NOT NULL,
    generato_il DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (partita_id) REFERENCES partite(id)
        ON DELETE CASCADE
);