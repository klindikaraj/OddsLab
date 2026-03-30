<?php
// php/classes/Bankroll.php

class Bankroll
{
    private Database $db;

    public function __construct()
    {
        $this->db = Database::getInstance();
    }

    /**
     * Riepilogo bankroll utente.
     */
    public function getSummary(int $userId): array
    {
        $user = $this->db->fetchOne(
            "SELECT bankroll_iniziale, bankroll_attuale, kelly_fraction
             FROM utenti WHERE id = ?",
            [$userId]
        );

        if ($user === null) {
            return [
                'bankroll_iniziale' => 0,
                'bankroll_attuale'  => 0,
                'kelly_fraction'    => 0.5,
                'roi_pct'           => 0,
            ];
        }

        $init = (float) $user['bankroll_iniziale'];
        $curr = (float) $user['bankroll_attuale'];
        $roi  = $init > 0 ? round((($curr - $init) / $init) * 100, 2) : 0;

        return [
            'bankroll_iniziale' => $init,
            'bankroll_attuale'  => $curr,
            'kelly_fraction'    => (float) $user['kelly_fraction'],
            'roi_pct'           => $roi,
        ];
    }

    /**
     * Piazza una scommessa e aggiorna il bankroll.
     * @return array{success: bool, message: string}
     */
    public function placeBet(int $userId, int $valueBetId, float $importo): array
    {
        $pdo = $this->db->getConnection();
        $pdo->beginTransaction();

        try {
            // 1. Verifica bankroll
            $user = $this->db->fetchOne(
                "SELECT bankroll_attuale FROM utenti WHERE id = ?",
                [$userId]
            );

            if ($user === null) {
                $pdo->rollBack();
                return ['success' => false, 'message' => 'Utente non trovato'];
            }

            $bankroll = (float) $user['bankroll_attuale'];

            if ($bankroll < $importo) {
                $pdo->rollBack();
                return [
                    'success' => false,
                    'message' => "Bankroll insufficiente. Disponibile: €" . number_format($bankroll, 2),
                ];
            }

            // 2. Recupera value bet
            $vb = $this->db->fetchOne(
                "SELECT * FROM value_bets WHERE id = ? AND stato = 'pending'",
                [$valueBetId]
            );

            if ($vb === null) {
                $pdo->rollBack();
                return ['success' => false, 'message' => 'Value bet non trovata o già chiusa'];
            }

            // 3. Inserisci scommessa
            $profittoPot = round($importo * ((float) $vb['valore_quota'] - 1), 2);

            $scommessaId = $this->db->execute(
                "INSERT INTO scommesse
                 (utente_id, value_bet_id, importo_puntato, profitto_potenziale)
                 VALUES (?, ?, ?, ?)",
                [$userId, $valueBetId, $importo, $profittoPot]
            );

            // 4. Aggiorna bankroll
            $nuovoBankroll = round($bankroll - $importo, 2);

            $this->db->execute(
                "UPDATE utenti SET bankroll_attuale = ? WHERE id = ?",
                [$nuovoBankroll, $userId]
            );

            // 5. Log storico
            $this->db->execute(
                "INSERT INTO storico_bankroll
                 (utente_id, importo_attuale, variazione, scommessa_id)
                 VALUES (?, ?, ?, ?)",
                [$userId, $nuovoBankroll, -$importo, $scommessaId]
            );

            $pdo->commit();

            return [
                'success'      => true,
                'message'      => "Scommessa piazzata! Puntato: €" . number_format($importo, 2),
                'scommessa_id' => $scommessaId,
                'bankroll'     => $nuovoBankroll,
            ];

        } catch (\Exception $e) {
            $pdo->rollBack();
            return ['success' => false, 'message' => 'Errore: ' . $e->getMessage()];
        }
    }

    /**
     * Storico scommesse dell'utente.
     */
    public function getBetHistory(int $userId, ?string $stato = null): array
    {
        $where  = "s.utente_id = ?";
        $params = [$userId];

        if ($stato !== null && $stato !== '' && $stato !== 'all') {
            $where .= " AND s.risultato = ?";
            $params[] = $stato;
        }

        return $this->db->fetchAll(
            "SELECT
                s.id,
                s.importo_puntato,
                s.profitto_potenziale,
                s.profitto_reale,
                s.risultato,
                s.data,
                vb.esito,
                vb.valore_quota,
                ROUND(vb.valore_perc * 100, 1) AS value_pct,
                sc.nome AS casa,
                st.nome AS trasferta,
                p.data_ora,
                p.id AS partita_id,
                sp.icona AS sport_icona,
                b.nome AS bookmaker
             FROM scommesse s
             JOIN value_bets vb ON s.value_bet_id = vb.id
             JOIN partite p     ON vb.partita_id = p.id
             JOIN squadre sc    ON p.squadra_casa_id = sc.id
             JOIN squadre st    ON p.squadra_trasf_id = st.id
             JOIN sport sp      ON p.sport_id = sp.id
             JOIN bookmaker b   ON vb.bookmaker_id = b.id
             WHERE {$where}
             ORDER BY s.data DESC",
            $params
        );
    }

    /**
     * Storico bankroll per grafico.
     */
    public function getHistory(int $userId, int $days = 30): array
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
     * Aggiorna impostazioni bankroll.
     */
    public function updateSettings(
        int   $userId,
        float $kellyFraction
    ): array {
        if ($kellyFraction <= 0 || $kellyFraction > 1) {
            return ['success' => false, 'message' => 'Kelly fraction deve essere tra 0.01 e 1.00'];
        }

        $this->db->execute(
            "UPDATE utenti SET kelly_fraction = ? WHERE id = ?",
            [$kellyFraction, $userId]
        );

        return ['success' => true, 'message' => 'Impostazioni aggiornate'];
    }

    /**
     * Calcola lo stake Kelly per un utente.
     */
    public function calculateKellyStake(int $userId, int $valueBetId): array
    {
        $user = $this->db->fetchOne(
            "SELECT bankroll_attuale, kelly_fraction FROM utenti WHERE id = ?",
            [$userId]
        );

        $vb = $this->db->fetchOne(
            "SELECT prob_modello, valore_quota FROM value_bets WHERE id = ?",
            [$valueBetId]
        );

        if ($user === null || $vb === null) {
            return ['stake' => 0, 'confidence' => 'NONE'];
        }

        $prob    = (float) $vb['prob_modello'];
        $odds    = (float) $vb['valore_quota'];
        $bank    = (float) $user['bankroll_attuale'];
        $fraction = (float) $user['kelly_fraction'];

        $edge = ($prob * $odds) - 1;

        if ($edge <= 0) {
            return ['stake' => 0, 'confidence' => 'NONE'];
        }

        $kellyFull = ($prob * $odds - 1) / ($odds - 1);
        $kellyFull = min($kellyFull, 0.10); // cap 10%
        $kellyAdj  = $kellyFull * $fraction;
        $stake     = round($bank * $kellyAdj, 2);

        // Confidence
        if ($edge < 0.02) {
            $conf = 'SKIP';
        } elseif ($edge < 0.05) {
            $conf = 'LOW';
        } elseif ($edge < 0.10) {
            $conf = 'MEDIUM';
        } elseif ($edge < 0.20) {
            $conf = 'HIGH';
        } else {
            $conf = 'ULTRA';
        }

        return [
            'stake'        => $stake,
            'kelly_pct'    => round($kellyAdj * 100, 2),
            'edge'         => round($edge * 100, 2),
            'confidence'   => $conf,
        ];
    }
}