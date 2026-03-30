-- ---------- VISTE UTILI ----------

CREATE VIEW v_value_bets_attive AS
SELECT
    vb.id,
    s.nome         AS sport,
    c.nome         AS campionato,
    sc.nome        AS squadra_casa,
    st.nome        AS squadra_trasferta,
    p.data_ora,
    b.nome         AS bookmaker,
    vb.esito,
    vb.valore_quota,
    vb.prob_modello,
    ROUND(vb.valore_perc * 100, 2)      AS value_pct,
    ROUND(vb.stake_kelly_pct * 100, 2)  AS kelly_pct
FROM value_bets vb
JOIN partite p     ON vb.partita_id   = p.id
JOIN sport s       ON p.sport_id      = s.id
JOIN campionati c  ON p.campionato_id = c.id
JOIN squadre sc    ON p.squadra_casa_id  = sc.id
JOIN squadre st    ON p.squadra_trasf_id = st.id
JOIN bookmaker b   ON vb.bookmaker_id = b.id
WHERE vb.stato = 'pending'
  AND p.data_ora > NOW()
ORDER BY vb.valore_perc DESC;

CREATE VIEW v_performance_utente AS
SELECT
    u.id AS utente_id,
    u.username,
    u.bankroll_iniziale,
    u.bankroll_attuale,
    ROUND(((u.bankroll_attuale - u.bankroll_iniziale)
           / u.bankroll_iniziale) * 100, 2)  AS roi_pct,
    COUNT(s.id)                               AS totale_scommesse,
    SUM(s.risultato = 'won')                  AS vinte,
    SUM(s.risultato = 'lost')                 AS perse,
    ROUND(SUM(s.risultato = 'won')
          / NULLIF(COUNT(s.id), 0) * 100, 1)  AS win_rate,
    COALESCE(SUM(s.profitto_reale), 0)         AS profitto_totale
FROM utenti u
LEFT JOIN scommesse s ON u.id = s.utente_id
                      AND s.risultato IN ('won','lost')
GROUP BY u.id;