-- ============================================
-- OddsLab — Dati di Esempio (Seed)
-- Esegui DOPO 01_ddl.sql e DOPO aver lanciato
-- python main.py almeno una volta.
--
-- Questo file inserisce:
-- 1. Un utente di test
-- 2. Alcuni dati di esempio per le demo
-- ============================================

USE oddslab;

-- ============================================
-- 1. UTENTE DI TEST
-- Password: "test123" (hash bcrypt)
-- ============================================
INSERT INTO utenti (username, email, password_hash, bankroll_iniziale, bankroll_attuale, kelly_fraction)
VALUES (
    'demo',
    'demo@oddslab.it',
    '$2y$10$YGxKc1gHJqHFqKz8V1Zt4OkLwEgZn4p7RQ5xB9kq8EjvJ3dF1T6Hy',
    1000.00,
    1000.00,
    0.50
)
ON DUPLICATE KEY UPDATE username = username;

-- ============================================
-- 2. SPORT (se non già inseriti da Python)
-- ============================================
INSERT IGNORE INTO sport (nome, api_key, icona) VALUES
    ('Calcio',  'calcio',  '⚽'),
    ('Tennis',  'tennis',  '🎾'),
    ('Basket',  'basket',  '🏀');

-- ============================================
-- 3. CAMPIONATI DI ESEMPIO
-- ============================================
INSERT IGNORE INTO campionati (sport_id, nome, paese, api_key) VALUES
    ((SELECT id FROM sport WHERE nome = 'Calcio'), 'Serie A',         'Italia',         'soccer_italy_serie_a'),
    ((SELECT id FROM sport WHERE nome = 'Calcio'), 'Premier League',  'Inghilterra',    'soccer_epl'),
    ((SELECT id FROM sport WHERE nome = 'Calcio'), 'La Liga',         'Spagna',         'soccer_spain_la_liga'),
    ((SELECT id FROM sport WHERE nome = 'Tennis'), 'ATP French Open', 'Internazionale', 'tennis_atp_french_open'),
    ((SELECT id FROM sport WHERE nome = 'Basket'), 'NBA',             'USA',            'basketball_nba');

-- ============================================
-- 4. BOOKMAKER PRINCIPALI
-- ============================================
INSERT IGNORE INTO bookmaker (nome, url) VALUES
    ('Bet365',       'https://www.bet365.com'),
    ('William Hill', 'https://www.williamhill.com'),
    ('Unibet',       'https://www.unibet.com'),
    ('Betfair',      'https://www.betfair.com'),
    ('Pinnacle',     'https://www.pinnacle.com'),
    ('1xBet',        'https://www.1xbet.com'),
    ('Marathonbet',  'https://www.marathonbet.com'),
    ('Betway',       'https://www.betway.com');

-- ============================================
-- 5. SQUADRE DI ESEMPIO (Serie A)
--    Le statistiche verranno aggiornate
--    automaticamente da Python dopo qualche
--    partita conclusa.
-- ============================================
INSERT IGNORE INTO squadre (campionato_id, nome, nome_api, elo_rating, gol_fatti_avg, gol_subiti_avg) VALUES
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Inter',       'Inter Milan',     1720, 2.10, 0.75),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Napoli',      'SSC Napoli',      1690, 1.85, 0.80),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Milan',       'AC Milan',        1650, 1.65, 1.00),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Juventus',    'Juventus',        1660, 1.55, 0.85),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Atalanta',    'Atalanta',        1640, 1.90, 1.05),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Roma',        'AS Roma',         1600, 1.45, 1.10),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Lazio',       'SS Lazio',        1590, 1.50, 1.15),
    ((SELECT id FROM campionati WHERE api_key = 'soccer_italy_serie_a'), 'Fiorentina',  'ACF Fiorentina',  1570, 1.40, 1.10);

-- ============================================
-- 6. STORICO BANKROLL INIZIALE (per il grafico)
-- ============================================
INSERT INTO storico_bankroll (utente_id, importo_attuale, variazione, scommessa_id)
SELECT id, 1000.00, 0, NULL
FROM utenti WHERE username = 'demo'
ON DUPLICATE KEY UPDATE importo_attuale = importo_attuale;

-- ============================================
-- VERIFICA
-- ============================================
SELECT '✅ Seed completato!' AS status;

SELECT 'utenti'     AS tabella, COUNT(*) AS righe FROM utenti
UNION ALL SELECT 'sport',       COUNT(*) FROM sport
UNION ALL SELECT 'campionati',  COUNT(*) FROM campionati
UNION ALL SELECT 'bookmaker',   COUNT(*) FROM bookmaker
UNION ALL SELECT 'squadre',     COUNT(*) FROM squadre;