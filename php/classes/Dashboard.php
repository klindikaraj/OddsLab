<?php
// php/classes/Dashboard.php

class Dashboard
{
    private Database $db;

    public function __construct()
    {
        $this->db = Database::getInstance();
    }

    /**
     * KPI principali dell'utente.
     */
    public function getKPIs(int $userId): array
    {
        $user = $this->db->fetchOne(
            "SELECT bankroll_iniziale, bankroll_attuale, kelly_fraction
             FROM utenti WHERE id = ?",
            [$userId]
        );

        if ($user === null) {
            return [
                'bankroll'    => 0,
                'roi'         => 0,
                'win_rate'    => 0,
                'total_bets'  => 0,
                'won'         => 0,
                'lost'        => 0,
                'profit'      => 0,
                'active_vb'   => 0,
            ];
        }

        $bankrollIniz  = (float) $user['bankroll_iniziale'];
        $bankrollAtt   = (float) $user['bankroll_attuale'];

        $roi = $bankrollIniz > 0
            ? round((($bankrollAtt - $bankrollIniz) / $bankrollIniz) * 100, 2)
            : 0;

        $bets = $this->db->fetchOne(
            "SELECT
                COUNT(*)                          AS total,
                SUM(risultato = 'won')            AS won,
                SUM(risultato = 'lost')           AS lost,
                COALESCE(SUM(profitto_reale), 0)  AS profit
             FROM scommesse
             WHERE utente_id = ? AND risultato IN ('won','lost')",
            [$userId]
        );

        $total = (int) ($bets['total'] ?? 0);
        $won   = (int) ($bets['won'] ?? 0);
        $lost  = (int) ($bets['lost'] ?? 0);
        $profit = (float) ($bets['profit'] ?? 0);

        $winRate = $total > 0 ? round(($won / $total) * 100, 1) : 0;

        $activeVB = $this->db->count(
            "SELECT COUNT(*) AS n FROM value_bets
             WHERE stato = 'pending'"
        );

        return [
            'bankroll'    => $bankrollAtt,
            'bankroll_init' => $bankrollIniz,
            'roi'         => $roi,
            'win_rate'    => $winRate,
            'total_bets'  => $total,
            'won'         => $won,
            'lost'        => $lost,
            'profit'      => $profit,
            'active_vb'   => $activeVB,
        ];
    }

    /**
     * Statistiche generali del database.
     */
    public function getSystemStats(): array
    {
        return [
            'partite'     => $this->db->count("SELECT COUNT(*) AS n FROM partite"),
            'quote'       => $this->db->count("SELECT COUNT(*) AS n FROM quote"),
            'previsioni'  => $this->db->count("SELECT COUNT(*) AS n FROM previsioni"),
            'value_bets'  => $this->db->count("SELECT COUNT(*) AS n FROM value_bets"),
            'report'      => $this->db->count("SELECT COUNT(*) AS n FROM report_ia"),
            'bookmaker'   => $this->db->count("SELECT COUNT(*) AS n FROM bookmaker"),
        ];
    }

    /**
     * Ultime value bets attive (per la dashboard).
     */
    public function getRecentValueBets(int $limit = 5): array
    {
        return $this->db->fetchAll(
            "SELECT
                vb.id,
                vb.esito,
                vb.valore_quota,
                ROUND(vb.valore_perc * 100, 1) AS value_pct,
                ROUND(vb.stake_kelly_pct * 100, 1) AS kelly_pct,
                vb.prob_modello,
                vb.stato,
                sc.nome AS casa,
                st.nome AS trasferta,
                p.data_ora,
                p.id AS partita_id,
                b.nome AS bookmaker,
                s.icona AS sport_icona,
                c.nome AS campionato
             FROM value_bets vb
             JOIN partite p   ON vb.partita_id = p.id
             JOIN squadre sc  ON p.squadra_casa_id = sc.id
             JOIN squadre st  ON p.squadra_trasf_id = st.id
             JOIN bookmaker b ON vb.bookmaker_id = b.id
             JOIN campionati c ON p.campionato_id = c.id
             JOIN sport s     ON p.sport_id = s.id
             WHERE vb.stato = 'pending'
               AND p.data_ora > NOW()
             ORDER BY vb.valore_perc DESC
             LIMIT ?",
            [$limit]
        );
    }

    /**
     * Dati per il grafico bankroll nel tempo.
     */
    public function getBankrollHistory(int $userId, int $days = 30): array
    {
        return $this->db->fetchAll(
            "SELECT
                DATE(data) AS giorno,
                ROUND(AVG(importo_attuale), 2) AS bankroll
             FROM storico_bankroll
             WHERE utente_id = ?
               AND data >= DATE_SUB(NOW(), INTERVAL ? DAY)
             GROUP BY DATE(data)
             ORDER BY giorno ASC",
            [$userId, $days]
        );
    }

    /**
     * Distribuzione value bets per sport.
     */
    public function getValueBetsBySport(): array
    {
        return $this->db->fetchAll(
            "SELECT
                s.nome AS sport,
                s.icona,
                COUNT(vb.id) AS totale,
                SUM(vb.stato = 'won')  AS vinte,
                SUM(vb.stato = 'lost') AS perse
             FROM value_bets vb
             JOIN partite p ON vb.partita_id = p.id
             JOIN sport s   ON p.sport_id = s.id
             GROUP BY s.id, s.nome, s.icona
             ORDER BY totale DESC"
        );
    }
}