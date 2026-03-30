<?php
// php/classes/ValueBet.php

class ValueBet
{
    private Database $db;

    public function __construct()
    {
        $this->db = Database::getInstance();
    }

    /**
     * Tutte le value bets attive con filtri.
     */
    public function getActive(
        ?string $sport = null,
        ?string $confidence = null,
        string  $orderBy = 'valore_perc',
        string  $order = 'DESC'
    ): array {
        $where  = "vb.stato = 'pending' AND p.data_ora > NOW()";
        $params = [];

        if ($sport !== null && $sport !== '') {
            $where .= " AND s.nome = ?";
            $params[] = $sport;
        }

        if ($confidence !== null && $confidence !== '') {
            switch ($confidence) {
                case 'LOW':
                    $where .= " AND vb.valore_perc BETWEEN 0.02 AND 0.05";
                    break;
                case 'MEDIUM':
                    $where .= " AND vb.valore_perc BETWEEN 0.05 AND 0.10";
                    break;
                case 'HIGH':
                    $where .= " AND vb.valore_perc BETWEEN 0.10 AND 0.20";
                    break;
                case 'ULTRA':
                    $where .= " AND vb.valore_perc >= 0.20";
                    break;
            }
        }

        // Whitelist per prevenire SQL injection su ORDER BY
        $allowedOrder = ['valore_perc', 'valore_quota', 'data_ora', 'prob_modello'];
        if (!in_array($orderBy, $allowedOrder, true)) {
            $orderBy = 'valore_perc';
        }
        $order = strtoupper($order) === 'ASC' ? 'ASC' : 'DESC';

        $sql = "SELECT
                    vb.id,
                    vb.esito,
                    vb.valore_quota,
                    ROUND(vb.valore_perc * 100, 1) AS value_pct,
                    ROUND(vb.stake_kelly_pct * 100, 1) AS kelly_pct,
                    ROUND(vb.prob_modello * 100, 1) AS prob_pct,
                    vb.stato,
                    vb.partita_id,
                    sc.nome AS casa,
                    st.nome AS trasferta,
                    p.data_ora,
                    b.nome AS bookmaker,
                    s.nome AS sport,
                    s.icona AS sport_icona,
                    c.nome AS campionato
                FROM value_bets vb
                JOIN partite p   ON vb.partita_id = p.id
                JOIN squadre sc  ON p.squadra_casa_id = sc.id
                JOIN squadre st  ON p.squadra_trasf_id = st.id
                JOIN bookmaker b ON vb.bookmaker_id = b.id
                JOIN sport s     ON p.sport_id = s.id
                JOIN campionati c ON p.campionato_id = c.id
                WHERE {$where}
                ORDER BY {$orderBy} {$order}";

        return $this->db->fetchAll($sql, $params);
    }

    /**
     * Dettaglio singola value bet.
     */
    public function getById(int $id): ?array
    {
        return $this->db->fetchOne(
            "SELECT
                vb.*,
                ROUND(vb.valore_perc * 100, 1) AS value_pct,
                ROUND(vb.stake_kelly_pct * 100, 1) AS kelly_pct,
                ROUND(vb.prob_modello * 100, 1) AS prob_pct,
                sc.nome AS casa,
                st.nome AS trasferta,
                p.data_ora,
                b.nome AS bookmaker,
                s.nome AS sport,
                c.nome AS campionato
             FROM value_bets vb
             JOIN partite p   ON vb.partita_id = p.id
             JOIN squadre sc  ON p.squadra_casa_id = sc.id
             JOIN squadre st  ON p.squadra_trasf_id = st.id
             JOIN bookmaker b ON vb.bookmaker_id = b.id
             JOIN sport s     ON p.sport_id = s.id
             JOIN campionati c ON p.campionato_id = c.id
             WHERE vb.id = ?",
            [$id]
        );
    }

    /**
     * Tutte le quote per una partita.
     */
    public function getMatchOdds(int $partitaId): array
    {
        return $this->db->fetchAll(
            "SELECT
                q.esito,
                q.valore_quota,
                ROUND(q.prob_implicita * 100, 1) AS prob_impl_pct,
                b.nome AS bookmaker,
                q.rilevata_il
             FROM quote q
             JOIN bookmaker b ON q.bookmaker_id = b.id
             WHERE q.partita_id = ?
               AND q.tipo_mercato = 'h2h'
             ORDER BY q.esito, q.valore_quota DESC",
            [$partitaId]
        );
    }

    /**
     * Previsione del modello per una partita.
     */
    public function getMatchPrediction(int $partitaId): ?array
    {
        return $this->db->fetchOne(
            "SELECT
                tipo_modello,
                ROUND(prob_casa * 100, 1) AS prob_casa_pct,
                ROUND(prob_pareggio * 100, 1) AS prob_pareg_pct,
                ROUND(prob_trasferta * 100, 1) AS prob_trasf_pct,
                calcolata_il
             FROM previsioni
             WHERE partita_id = ?",
            [$partitaId]
        );
    }

    /**
     * Dettagli partita.
     */
    public function getMatchDetail(int $partitaId): ?array
    {
        return $this->db->fetchOne(
            "SELECT
                p.*,
                sc.nome AS casa,
                sc.elo_rating AS elo_casa,
                sc.gol_fatti_avg AS gf_casa,
                sc.gol_subiti_avg AS gs_casa,
                st.nome AS trasferta,
                st.elo_rating AS elo_trasf,
                st.gol_fatti_avg AS gf_trasf,
                st.gol_subiti_avg AS gs_trasf,
                s.nome AS sport,
                s.icona AS sport_icona,
                c.nome AS campionato
             FROM partite p
             JOIN squadre sc  ON p.squadra_casa_id = sc.id
             JOIN squadre st  ON p.squadra_trasf_id = st.id
             JOIN sport s     ON p.sport_id = s.id
             JOIN campionati c ON p.campionato_id = c.id
             WHERE p.id = ?",
            [$partitaId]
        );
    }

    /**
     * Report IA per una partita.
     */
    public function getMatchReport(int $partitaId): ?array
    {
        return $this->db->fetchOne(
            "SELECT testo, generato_il
             FROM report_ia
             WHERE partita_id = ?
             ORDER BY generato_il DESC
             LIMIT 1",
            [$partitaId]
        );
    }

    /**
     * Value bets di una partita specifica.
     */
    public function getMatchValueBets(int $partitaId): array
    {
        return $this->db->fetchAll(
            "SELECT
                vb.*,
                ROUND(vb.valore_perc * 100, 1) AS value_pct,
                ROUND(vb.stake_kelly_pct * 100, 1) AS kelly_pct,
                ROUND(vb.prob_modello * 100, 1) AS prob_pct,
                b.nome AS bookmaker
             FROM value_bets vb
             JOIN bookmaker b ON vb.bookmaker_id = b.id
             WHERE vb.partita_id = ?
             ORDER BY vb.valore_perc DESC",
            [$partitaId]
        );
    }

    /**
     * Lista sport disponibili (per filtri).
     */
    public function getSports(): array
    {
        return $this->db->fetchAll(
            "SELECT DISTINCT s.nome, s.icona
             FROM sport s
             JOIN partite p ON s.id = p.sport_id
             ORDER BY s.nome"
        );
    }
}